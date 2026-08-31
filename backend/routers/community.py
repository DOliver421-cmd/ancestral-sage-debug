"""
Community router — M.O.R.E. (Members Offering Resources & Expertise): posts,
needs, direct chat, flags, appeals, moderation queue, department AI chat,
and XP leaderboard.

Extracted verbatim from backend/server.py (monolith refactor, slice 6).
Shared state (db, current_user, audit, assert_role, xp_level) is bound by
server.py via bind() at include time — no circular imports.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["community"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = assert_role = xp_level = None


def bind(_db, _current_user, _audit, _assert_role, _xp_level):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, assert_role, xp_level
    db = _db
    current_user = _current_user
    audit = _audit
    assert_role = _assert_role
    xp_level = _xp_level


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ── Models (mirror server.py definitions) ────────────────────────────────────
class OrchestratorHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


# ═════════════════════════════════════════════════════════════════════════════
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
class MorePostReq(BaseModel):
    content: str
    category: Literal["skill_offer", "need", "community", "story"] = "community"

class MoreNeedReq(BaseModel):
    title: str
    description: str
    category: str = "general"

class MoreChatReq(BaseModel):
    session_id: str
    message: str

class MoreFlagReq(BaseModel):
    target_id: str
    target_type: Literal["post", "need", "chat"]
    reason: str

class MoreDeptChatReq(BaseModel):
    session_id: str
    message: str
    history: Optional[list[OrchestratorHistoryItem]] = []
    department_hint: Optional[str] = None


# ─── M.O.R.E. Endpoints ──────────────────────────────────────────────────────

@router.post("/more/post")
async def more_create_post(req: MorePostReq, user=Depends(_dep_current_user)):
    if not req.content.strip():
        raise HTTPException(400, "Content cannot be empty")
    if len(req.content) > 2000:
        raise HTTPException(400, "Content too long (max 2000 chars)")

    # Rate limit check
    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(req.content, user_id=user.id, content_type="post")
    decision = moderation.get("decision", "warn")

    # Crisis — do not publish, return resources
    if decision == "crisis":
        return {
            "post": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    # Block — do not publish, return Oliver's message
    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This content cannot be posted.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Warn or quarantine → hold for admin review, not live
    if decision in ("warn", "quarantine"):
        post_doc = {
            "id": str(uuid.uuid4()),
            "content": req.content,
            "category": req.category,
            "author_id": user.id,
            "author_name": user.full_name,
            "status": "pending_review",
            "moderation_note": moderation.get("reason"),
            "violation_category": moderation.get("violation_category", "none"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "likes": 0,
        }
        await db.more_posts.insert_one(post_doc)
        post_doc.pop("_id", None)
        return {
            "post": post_doc,
            "oliver_response": moderation.get("oliver_response"),
            "pending_review": True,
        }

    # Approve — publish immediately
    post_doc = {
        "id": str(uuid.uuid4()),
        "content": req.content,
        "category": req.category,
        "author_id": user.id,
        "author_name": user.full_name,
        "status": "active",
        "moderation_note": moderation.get("reason"),
        "violation_category": "none",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "likes": 0,
    }
    await db.more_posts.insert_one(post_doc)
    post_doc.pop("_id", None)
    return {"post": post_doc, "oliver_response": None}


@router.get("/more/posts")
async def more_list_posts(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
    # Only Oliver-approved posts are public. Held content (pending_review) stays
    # off the public feed until a human clears it.
    query: dict = {"expires_at": {"$gt": now}, "status": "active"}
    if category:
        query["category"] = category
    cursor = db.more_posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(limit)
    total = await db.more_posts.count_documents(query)
    return {"posts": posts, "total": total}


@router.post("/more/need")
async def more_create_need(req: MoreNeedReq, user=Depends(_dep_current_user)):
    combined = f"{req.title}\n{req.description}"

    if not req.title.strip() or not req.description.strip():
        raise HTTPException(400, "Title and description are required")

    # Rate limit check
    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(combined, user_id=user.id, content_type="need")
    decision = moderation.get("decision", "warn")

    # Crisis — return resources, do not publish raw distress as a "need"
    if decision == "crisis":
        return {
            "need": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This content cannot be posted.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Warn or quarantine → hold for review
    status = "open" if decision == "approve" else "pending_review"

    need_doc = {
        "id": str(uuid.uuid4()),
        "title": req.title,
        "description": req.description,
        "category": req.category,
        "author_id": user.id,
        "author_name": user.full_name,
        "status": status,
        "moderation_note": moderation.get("reason"),
        "violation_category": moderation.get("violation_category", "none"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "responses": 0,
    }
    await db.more_needs.insert_one(need_doc)
    need_doc.pop("_id", None)
    return {
        "need": need_doc,
        "oliver_response": moderation.get("oliver_response") if decision != "approve" else None,
        "pending_review": decision in ("warn", "quarantine"),
    }


@router.get("/more/needs")
async def more_list_needs(
    category: Optional[str] = None,
    status: str = "open",
    skip: int = 0,
    limit: int = 20,
):
    now = datetime.now(timezone.utc).isoformat()
    # Never expose held/quarantined content via the public feed, even if a
    # client explicitly requests status=pending_review.
    if status == "pending_review":
        status = "open"
    query: dict = {"expires_at": {"$gt": now}, "status": status}
    if category:
        query["category"] = category
    cursor = db.more_needs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    needs = await cursor.to_list(limit)
    total = await db.more_needs.count_documents(query)
    return {"needs": needs, "total": total}


@router.post("/more/chat/send")
async def more_chat_send(req: MoreChatReq, user=Depends(_dep_current_user)):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    if len(req.message) > 1000:
        raise HTTPException(400, "Message too long (max 1000 chars)")

    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "Slow down a bit — you've been very active. Try again in an hour.")

    moderation = await _oliver_moderate(req.message, user_id=user.id, content_type="chat")
    decision = moderation.get("decision", "warn")

    if decision == "crisis":
        return {
            "message": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This message cannot be sent.")

    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=60)).isoformat()
    msg_doc = {
        "id": str(uuid.uuid4()),
        "session_id": req.session_id,
        "content": req.message,
        "author_id": user.id,
        "author_name": user.full_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
    }
    await db.more_chats.insert_one(msg_doc)
    msg_doc.pop("_id", None)
    return {"message": msg_doc, "oliver_response": moderation.get("oliver_response") if moderation.get("decision") == "warn" else None}


@router.get("/more/chat/{session_id}")
async def more_chat_get(session_id: str, user=Depends(_dep_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.more_chats.find(
        {"session_id": session_id, "expires_at": {"$gt": now}},
        {"_id": 0}
    ).sort("created_at", 1).limit(200)
    messages = await cursor.to_list(200)
    return {"messages": messages, "session_id": session_id}


@router.post("/more/flag")
async def more_flag_content(req: MoreFlagReq, user=Depends(_dep_current_user)):
    flag_doc = {
        "id": str(uuid.uuid4()),
        "target_id": req.target_id,
        "target_type": req.target_type,
        "reason": req.reason,
        "flagged_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "status": "pending",
    }
    await db.more_flags.insert_one(flag_doc)
    flag_doc.pop("_id", None)
    return {"flag": flag_doc}


@router.post("/more/appeal")
async def more_appeal_decision(
    target_id: str,
    reason: str,
    user=Depends(_dep_current_user),
):
    """Appeal a moderation decision. Logs the appeal for admin review.
    Users can appeal a block or a pending_review hold on their own content."""
    if not reason.strip():
        raise HTTPException(400, "Please explain why you are appealing.")
    if len(reason) > 1000:
        raise HTTPException(400, "Appeal reason too long (max 1000 chars).")

    # Verify the content belongs to this user
    post = await db.more_posts.find_one({"id": target_id, "author_id": user.id}, {"_id": 0})
    need = await db.more_needs.find_one({"id": target_id, "author_id": user.id}, {"_id": 0}) if not post else None
    if not post and not need:
        raise HTTPException(404, "Content not found or does not belong to your account.")

    appeal_doc = {
        "id": str(uuid.uuid4()),
        "target_id": target_id,
        "target_type": "post" if post else "need",
        "user_id": user.id,
        "user_name": user.full_name,
        "appeal_reason": reason.strip(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }
    await db.more_appeals.insert_one(appeal_doc)
    appeal_doc.pop("_id", None)
    await audit(user.id, "more.appeal", meta={"target_id": target_id})
    return {
        "appeal": appeal_doc,
        "message": (
            "Your appeal has been received. A real human will review it within 48 hours. "
            "Oliver Guardian protects everyone — including you. If the decision was wrong, we'll fix it."
        ),
    }


@router.get("/more/admin/queue")
async def more_admin_review_queue(user=Depends(_dep_current_user), skip: int = 0, limit: int = 50):
    """Admin review queue — pending_review posts and needs, plus appeals."""
    assert_role(user, "admin")
    posts_cursor = db.more_posts.find({"status": "pending_review"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    needs_cursor = db.more_needs.find({"status": "pending_review"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    appeals_cursor = db.more_appeals.find({"status": "pending"}, {"_id": 0}).sort("created_at", 1).skip(skip).limit(limit)
    posts_total = await db.more_posts.count_documents({"status": "pending_review"})
    needs_total = await db.more_needs.count_documents({"status": "pending_review"})
    appeals_total = await db.more_appeals.count_documents({"status": "pending"})
    posts, needs, appeals = await asyncio.gather(
        posts_cursor.to_list(limit),
        needs_cursor.to_list(limit),
        appeals_cursor.to_list(limit),
    )
    return {
        "posts": posts, "posts_total": posts_total,
        "needs": needs, "needs_total": needs_total,
        "appeals": appeals, "appeals_total": appeals_total,
    }


@router.post("/more/admin/queue/{content_type}/{content_id}/approve")
async def more_admin_approve(content_type: str, content_id: str, user=Depends(_dep_current_user)):
    """Admin approves a pending_review post or need — moves it to active/open."""
    assert_role(user, "admin")
    if content_type == "post":
        result = await db.more_posts.update_one(
            {"id": content_id, "status": "pending_review"},
            {"$set": {"status": "active", "reviewed_by": user.id, "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    elif content_type == "need":
        result = await db.more_needs.update_one(
            {"id": content_id, "status": "pending_review"},
            {"$set": {"status": "open", "reviewed_by": user.id, "reviewed_at": datetime.now(timezone.utc).isoformat()}},
        )
    else:
        raise HTTPException(400, "content_type must be 'post' or 'need'")
    if result.modified_count == 0:
        raise HTTPException(404, "Content not found or already reviewed.")
    await audit(user.id, f"more.admin.approve.{content_type}", meta={"content_id": content_id})
    return {"approved": True, "content_id": content_id}


@router.post("/more/admin/queue/{content_type}/{content_id}/reject")
async def more_admin_reject(content_type: str, content_id: str, reason: str = "", user=Depends(_dep_current_user)):
    """Admin rejects a pending_review item — removes it permanently."""
    assert_role(user, "admin")
    if content_type == "post":
        result = await db.more_posts.delete_one({"id": content_id, "status": "pending_review"})
    elif content_type == "need":
        result = await db.more_needs.delete_one({"id": content_id, "status": "pending_review"})
    else:
        raise HTTPException(400, "content_type must be 'post' or 'need'")
    if result.deleted_count == 0:
        raise HTTPException(404, "Content not found or already reviewed.")
    await audit(user.id, f"more.admin.reject.{content_type}", meta={"content_id": content_id, "reason": reason})
    return {"rejected": True, "content_id": content_id}


@router.get("/more/admin/moderation-log")
async def more_moderation_log(user=Depends(_dep_current_user), skip: int = 0, limit: int = 100, decision: Optional[str] = None):
    """Full Oliver Guardian moderation audit log — admin and site support."""
    assert_role(user, "support_staff", "admin")
    query = {}
    if decision:
        query["decision"] = decision
    cursor = db.more_moderation_log.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    total = await db.more_moderation_log.count_documents(query)
    return {"logs": logs, "total": total}


@router.get("/more/admin/moderation-stats")
async def more_moderation_stats(user=Depends(_dep_current_user)):
    """Oliver Guardian moderation summary statistics — admin and site support."""
    assert_role(user, "support_staff", "admin")
    total_moderated = await db.more_moderation_log.count_documents({})
    approved = await db.more_moderation_log.count_documents({"decision": "approve"})
    blocked = await db.more_moderation_log.count_documents({"decision": "block"})
    warned = await db.more_moderation_log.count_documents({"decision": "warn"})
    flagged = await db.more_flags.count_documents({})
    pending = await db.more_moderation_log.count_documents({"decision": {"$in": ["hold", "quarantine"]}})
    recent = db.more_moderation_log.find({}, {"_id": 0}).sort("created_at", -1).limit(20)
    recent_log = await recent.to_list(20)
    return {
        "total_moderated": total_moderated,
        "approved": approved,
        "blocked": blocked,
        "warned": warned,
        "flagged": flagged,
        "pending_count": pending,
        "recent_log": recent_log,
    }


@router.post("/more/purge")
async def more_manual_purge(user=Depends(_dep_current_user)):
    assert_role(user, "admin")
    now = datetime.now(timezone.utc).isoformat()
    r1 = await db.more_posts.delete_many({"expires_at": {"$lte": now}})
    r2 = await db.more_chats.delete_many({"expires_at": {"$lte": now}})
    r3 = await db.more_flags.delete_many({"expires_at": {"$lte": now}})
    r4 = await db.more_appeals.delete_many({"expires_at": {"$lte": now}})
    await audit(user.id, "more.purge", meta={
        "posts": r1.deleted_count, "chats": r2.deleted_count,
        "flags": r3.deleted_count, "appeals": r4.deleted_count,
    })
    return {"purged": {"posts": r1.deleted_count, "chats": r2.deleted_count, "flags": r3.deleted_count, "appeals": r4.deleted_count}}


@router.get("/more/admin/flags")
async def more_admin_flags(user=Depends(_dep_current_user), skip: int = 0, limit: int = 50):
    assert_role(user, "admin")
    cursor = db.more_flags.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    flags = await cursor.to_list(limit)
    total = await db.more_flags.count_documents({"status": "pending"})
    return {"flags": flags, "total": total}


# -- XP / GAMIFICATION --

@router.get("/xp/me")
async def my_xp(user: User = Depends(_dep_current_user)):
    doc = await db.user_xp.find_one({"user_id": user.id}, {"_id": 0})
    total = (doc or {}).get("total_xp", 0)
    level_info = xp_level(total)
    rank = 1
    if user.associate:
        cohort_ids = [u["id"] async for u in db.users.find({"associate": user.associate, "role": "student"}, {"id": 1, "_id": 0})]
        higher = await db.user_xp.count_documents({"user_id": {"$in": cohort_ids}, "total_xp": {"$gt": total}})
        rank = higher + 1
    return {**level_info, "total_xp": total, "rank_in_cohort": rank, "history": (doc or {}).get("history", [])[-10:]}


@router.get("/xp/leaderboard")
async def xp_leaderboard(associate: Optional[str] = None, user: User = Depends(_dep_current_user)):
    q: dict = {"role": "student"}
    if associate:
        q["associate"] = associate
    students = await db.users.find(q, {"_id": 0, "id": 1, "full_name": 1, "associate": 1}).to_list(500)
    ids = [s["id"] for s in students]
    xp_docs = await db.user_xp.find({"user_id": {"$in": ids}}, {"_id": 0}).to_list(500) if ids else []
    xp_map = {x["user_id"]: x["total_xp"] for x in xp_docs}
    board = sorted(
        [{**s, "total_xp": xp_map.get(s["id"], 0), "level": xp_level(xp_map.get(s["id"], 0))["level"]} for s in students],
        key=lambda x: -x["total_xp"]
    )[:25]
    return board


# -- AI LAB FEEDBACK --

# -- COHORT BENCHMARKING --


@router.post("/more/department/chat")
async def more_department_chat(body: MoreDeptChatReq, user: User = Depends(_dep_current_user)):
    """M.O.R.E. Department AI System endpoint.

    Routes the operator's message through the 13-persona M.O.R.E. Department
    AI network. Admin and executive_admin only. The unified system prompt handles
    internal routing to the correct persona (Finance, Revenue, Production, etc.)
    and returns a structured header identifying the active persona and mode.
    """
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Department AI requires admin access")

    system = get_more_department_system()

    user_message = body.message
    if body.department_hint:
        user_message = f"[DEPARTMENT CONTEXT: {body.department_hint}]\n\n{body.message}"

    claude_messages = [
        {"role": h.role, "content": h.content}
        for h in (body.history or [])
    ]
    claude_messages.append({"role": "user", "content": user_message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="more_department")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("M.O.R.E. Department AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Parse persona and mode from the structured header the system prompt always emits:
    # **[PERSONA NAME] | [DEPARTMENT] | Mode: [CURRENT MODE]**
    persona = "Department AI"
    department = "M.O.R.E."
    mode = "Balanced"
    first_line = reply.split("\n")[0].strip()
    if first_line.startswith("**") and "|" in first_line:
        parts = first_line.strip("*").split("|")
        if len(parts) >= 1:
            persona = parts[0].strip()
        if len(parts) >= 2:
            department = parts[1].strip()
        if len(parts) >= 3:
            mode_raw = parts[2].strip()
            mode = mode_raw.replace("Mode:", "").strip()

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": "more_department",
        "module_slug": None,
        "user_msg": body.message,
        "assistant_msg": reply,
        "persona": persona,
        "department": department,
        "active_mode": mode,
        "department_hint": body.department_hint,
        "role_at_time": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })

    return {
        "reply": reply,
        "persona": persona,
        "department": department,
        "mode": mode,
    }


@router.get("/more/department/history")
async def more_department_history(user: User = Depends(_dep_current_user), limit: int = 60):
    """M.O.R.E. Department AI conversation history for the current operator.

    Returns the operator's past more_department chat records (chronological)
    so the Dept. AI Ops page can restore context across sessions. Admin+ only,
    matching the chat endpoint.
    """
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Department AI requires admin access")
    limit = max(1, min(int(limit), 200))
    records = await db.chat_history.find(
        {"user_id": user.id, "mode": "more_department"},
        {"_id": 0, "user_msg": 1, "assistant_msg": 1, "persona": 1, "department": 1,
         "active_mode": 1, "is_decline": 1, "created_at": 1, "session_id": 1},
    ).sort("created_at", -1).limit(limit).to_list(limit)
    records.reverse()  # chronological order for the chat UI
    return {"history": records}


@router.get("/more/department/integrity")
async def more_department_integrity(user: User = Depends(_dep_current_user)):
    """SHA-256 hash of the M.O.R.E. Department system prompt for integrity auditing."""
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Admin access required")
    return {
        "hash": compute_more_department_hash(),
        "system": "more_department",
    }


# ─── PAYMENTS ────────────────────────────────────────────────────────────────
# Extracted to backend/routers/payments.py (monolith refactor, slice 0).
# The /api/payments/* routes are included below via api_router.include_router.
# ─── END PAYMENTS (extracted) ────────────────────────────────────────────────
