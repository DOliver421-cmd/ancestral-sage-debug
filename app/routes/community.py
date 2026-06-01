"""app/routes/community.py — M.O.R.E. (Michael Oliver Resource Exchange) community endpoints.

Extracted from backend/server.py lines 6307–6914.
No logic changed.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import ANTHROPIC_API_KEY, ROLE_RANK
from app.database import db
from app.models.ai import OrchestratorHistoryItem
from app.models.user import User
from app.security.auth import assert_role, current_user
from app.utils.audit import audit

logger = logging.getLogger("lcewai")

router = APIRouter()


# ── Oliver Guardian prompt and crisis resources ───────────────────────────────

_OLIVER_GUARDIAN_PROMPT = """You are Oliver Guardian — the first-line AI moderator for M.O.R.E. (Michael Oliver Resource Exchange).

M.O.R.E. is named in honor of Michael Oliver, a community organizer who believed ordinary people, given the right structure, take extraordinary care of each other. This platform exists to honor that belief. You are its protector.

WHO YOU ARE
You are a wise, protective presence — part community elder, part sharp-eyed guard. You have warmth for people who belong here and zero patience for those who don't. You read the room. You know the difference between someone new to the platform who made an honest mistake, someone confused about the rules, and someone deliberately trying to exploit a community of vulnerable people. Your response is different for each.

PLATFORM RULES — absolute, no exceptions:
- NO money, payments, prices, or financial transactions of any kind
- NO personal contact info: phone numbers, addresses, email, social media handles
- NO illegal items, services, or activities
- NO harassment, threats, bullying, or intimidation
- NO sexual content of any kind
- NO discrimination based on race, ethnicity, age, disability, religion, gender, sexual orientation, or any protected class
- NO scams, fake offers, deceptive content, or false claims
- NO exploitation of elders, children, or vulnerable people
- NO hate speech
- NO solicitation of professional services that require licensing (medical diagnosis, legal advice, financial advice)

ALLOWED CONTENT — this community THRIVES on:
- Skill offers: teaching, tutoring, mentoring, trades, crafts, cooking, childcare
- Needs: help moving, transportation, meals, companionship, household tasks, job searching, reading/writing help
- Housing and shelter needs (legitimate, not solicitation)
- Community support, encouragement, stories of resilience
- Time and skill exchange — no money involved
- Legitimate local information, events, resources
- Crisis support REQUESTS (someone asking for help IS allowed — see CRISIS section)

DECISION TYPES — read carefully, each has a different response:

"approve" — content is legitimate, post it.

"warn" — content has a rule violation but the intent seems genuine or confused, not malicious.
  Voice: Warm but clear. Like an elder who corrects a child without shaming them. Explain what was wrong and how to fix it.
  Example (money mention): "Hey, I know you meant well — but we don't use money here, even as a reference. Just describe what you're offering or need in plain terms. Try again?"
  Example (phone number): "Almost there. We keep personal info off the platform for your protection — take out that number and repost. We've got you."

"block" — clear bad-faith violation: scam, harassment, hate speech, deliberate exploitation, repeated boundary-pushing.
  Voice: Oliver with full presence. Firm, direct, a little sharp. Not cruel, but unmistakably clear.
  Example (scam): "Ah yes. We've seen this move before. The community here has real needs — and real people protecting them. Not today."
  Example (harassment): "That kind of talk doesn't belong anywhere, and it definitely doesn't belong here. This one's staying off the platform."
  Example (money extraction): "A 'fee' on a no-fee platform. Interesting strategy. Incorrect one, but interesting."

"crisis" — content indicates the person may be in personal danger, expressing suicidal ideation, escaping domestic violence, or facing an immediate safety emergency.
  This is NOT a block. This person may need help. The post should NOT be published (it may contain unsafe personal details), but the person needs resources, not rejection.
  Voice: No sarcasm. Warm, direct, caring. Oliver at his most human.
  Example: "I hear you, and I want you to know help is real and available. Please reach out to 211 (call or text) — they connect people with shelter, food, crisis support, and more, 24/7 and free. If you're in immediate danger, call 911. You matter here."
  The crisis decision ALWAYS includes a crisis_resources array of specific resources.

FIRST-TIME GRACE
If the content seems like an honest first-time mistake (mention of money in passing, accidentally included a phone number, etc.) and there is no malicious pattern — use "warn" not "block." Protect the community. Don't punish the newcomer.

RESPOND ONLY with a valid JSON object — no other text:
{
  "decision": "approve" | "warn" | "block" | "crisis",
  "reason": "internal note — brief, factual (1-2 sentences, not shown to user)",
  "oliver_response": "message shown to user — only for warn, block, crisis decisions. null for approve.",
  "crisis_resources": ["211 — call or text, free, 24/7", "Crisis Text Line — text HOME to 741741", "National DV Hotline — 1-800-799-7233", "Childhelp National Child Abuse Hotline — 1-800-422-4453"],
  "violation_category": "money | contact_info | illegal | harassment | sexual | discrimination | scam | exploitation | hate_speech | crisis | none"
}

crisis_resources: include ONLY for "crisis" decisions. For all other decisions, omit this field or set to null.
oliver_response: required for warn, block, crisis. null for approve.
violation_category: always include, use "none" for approved content."""


_CRISIS_RESOURCES = [
    {"name": "211 (US)", "description": "Free local crisis resources — call or text, 24/7", "contact": "Call or text 211 | 211.org"},
    {"name": "Crisis Text Line", "description": "Text-based crisis support, free and confidential", "contact": "Text HOME to 741741"},
    {"name": "National Domestic Violence Hotline", "description": "Safe, confidential support for DV situations", "contact": "1-800-799-7233 | thehotline.org"},
    {"name": "Childhelp National Child Abuse Hotline", "description": "Child abuse reporting and support", "contact": "1-800-422-4453"},
    {"name": "988 Suicide & Crisis Lifeline", "description": "Mental health crisis support", "contact": "Call or text 988"},
    {"name": "SAMHSA National Helpline", "description": "Substance use and mental health treatment referrals", "contact": "1-800-662-4357"},
]


async def _oliver_write_audit_log(
    user_id: str,
    content_type: str,
    content: str,
    decision: str,
    reason: str,
    violation_category: str,
    oliver_response,
) -> None:
    try:
        await db.more_moderation_log.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "content_type": content_type,
            "content_preview": content[:500],
            "decision": decision,
            "reason": reason,
            "violation_category": violation_category,
            "oliver_response": oliver_response,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Oliver Guardian audit log write failed: {e}")


async def _oliver_check_rate_limit(user_id: str) -> bool:
    try:
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        count = 0
        for collection in [db.more_posts, db.more_needs, db.more_chats]:
            count += await collection.count_documents({
                "author_id": user_id,
                "created_at": {"$gte": one_hour_ago},
            })
        return count < 10
    except Exception as e:
        logger.warning(f"Oliver Guardian rate limit check failed: {e}")
        return True


async def _oliver_moderate(content: str, user_id: str = "unknown", content_type: str = "post") -> dict:
    import anthropic
    import json as _json

    decision_result = None
    try:
        aclient = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        resp = await aclient.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=_OLIVER_GUARDIAN_PROMPT,
            messages=[{"role": "user", "content": f"Content to moderate:\n\n{content}"}],
        )
        raw = resp.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        decision_result = _json.loads(raw.strip())
        decision_result.setdefault("decision", "warn")
        decision_result.setdefault("reason", "moderation review")
        decision_result.setdefault("oliver_response", None)
        decision_result.setdefault("violation_category", "none")
        if decision_result["decision"] == "crisis":
            decision_result["crisis_resources"] = _CRISIS_RESOURCES
    except Exception as e:
        logger.error(f"Oliver Guardian moderation failed: {e}")
        decision_result = {
            "decision": "quarantine",
            "reason": f"Moderation system temporarily unavailable: {type(e).__name__}",
            "oliver_response": (
                "We're having a brief technical hiccup reviewing your post. "
                "It's been held for a quick human review and will be up shortly if everything looks good."
            ),
            "violation_category": "none",
        }

    await _oliver_write_audit_log(
        user_id=user_id,
        content_type=content_type,
        content=content,
        decision=decision_result.get("decision", "unknown"),
        reason=decision_result.get("reason", ""),
        violation_category=decision_result.get("violation_category", "none"),
        oliver_response=decision_result.get("oliver_response"),
    )

    return decision_result


# ── Pydantic Models ────────────────────────────────────────────────────────────

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
    history: Optional[List[OrchestratorHistoryItem]] = []
    department_hint: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/more/post")
async def more_create_post(req: MorePostReq, user=Depends(current_user)):
    if not req.content.strip():
        raise HTTPException(400, "Content cannot be empty")
    if len(req.content) > 2000:
        raise HTTPException(400, "Content too long (max 2000 chars)")

    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(req.content, user_id=user.id, content_type="post")
    decision = moderation.get("decision", "warn")

    if decision == "crisis":
        return {
            "post": None,
            "oliver_response": moderation.get("oliver_response"),
            "crisis": True,
            "crisis_resources": moderation.get("crisis_resources", _CRISIS_RESOURCES),
        }

    if decision == "block":
        raise HTTPException(400, moderation.get("oliver_response") or "This content cannot be posted.")

    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

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
    query: dict = {"expires_at": {"$gt": now}, "status": "active"}
    if category:
        query["category"] = category
    cursor = db.more_posts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(limit)
    total = await db.more_posts.count_documents(query)
    return {"posts": posts, "total": total}


@router.post("/more/need")
async def more_create_need(req: MoreNeedReq, user=Depends(current_user)):
    combined = f"{req.title}\n{req.description}"

    if not req.title.strip() or not req.description.strip():
        raise HTTPException(400, "Title and description are required")

    if not await _oliver_check_rate_limit(user.id):
        raise HTTPException(429, "You're posting a lot right now. Take a breath and try again in an hour.")

    moderation = await _oliver_moderate(combined, user_id=user.id, content_type="need")
    decision = moderation.get("decision", "warn")

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
async def more_chat_send(req: MoreChatReq, user=Depends(current_user)):
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
async def more_chat_get(session_id: str, user=Depends(current_user)):
    now = datetime.now(timezone.utc).isoformat()
    cursor = db.more_chats.find(
        {"session_id": session_id, "expires_at": {"$gt": now}},
        {"_id": 0}
    ).sort("created_at", 1).limit(200)
    messages = await cursor.to_list(200)
    return {"messages": messages, "session_id": session_id}


@router.post("/more/flag")
async def more_flag_content(req: MoreFlagReq, user=Depends(current_user)):
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
    user=Depends(current_user),
):
    if not reason.strip():
        raise HTTPException(400, "Please explain why you are appealing.")
    if len(reason) > 1000:
        raise HTTPException(400, "Appeal reason too long (max 1000 chars).")

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
async def more_admin_review_queue(user=Depends(current_user), skip: int = 0, limit: int = 50):
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
async def more_admin_approve(content_type: str, content_id: str, user=Depends(current_user)):
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
async def more_admin_reject(content_type: str, content_id: str, reason: str = "", user=Depends(current_user)):
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
async def more_moderation_log(user=Depends(current_user), skip: int = 0, limit: int = 100, decision: Optional[str] = None):
    assert_role(user, "admin")
    query = {}
    if decision:
        query["decision"] = decision
    cursor = db.more_moderation_log.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    total = await db.more_moderation_log.count_documents(query)
    return {"logs": logs, "total": total}


@router.get("/more/admin/moderation-stats")
async def more_moderation_stats(user=Depends(current_user)):
    assert_role(user, "admin")
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
async def more_manual_purge(user=Depends(current_user)):
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
async def more_admin_flags(user=Depends(current_user), skip: int = 0, limit: int = 50):
    assert_role(user, "admin")
    cursor = db.more_flags.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    flags = await cursor.to_list(limit)
    total = await db.more_flags.count_documents({"status": "pending"})
    return {"flags": flags, "total": total}


@router.post("/more/department/chat")
async def more_department_chat(body: MoreDeptChatReq, user: User = Depends(current_user)):
    """M.O.R.E. Department AI System endpoint — admin and executive_admin only."""
    from ai.more_department import get_more_department_system, compute_more_department_hash

    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Department AI requires admin access")

    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

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


@router.get("/more/department/integrity")
async def more_department_integrity(user: User = Depends(current_user)):
    from ai.more_department import compute_more_department_hash
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Admin access required")
    return {
        "hash": compute_more_department_hash(),
        "system": "more_department",
    }
