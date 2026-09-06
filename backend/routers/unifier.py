"""
backend/routers/unifier.py — The Unifier
=========================================

Rebrand of The Arena into a real editorial/creative production room:

  Two personas take opposite passes on the user's prompt, then Hybrid NAM
  (the unified model) judges the two answers, synthesizes the best version,
  and returns the improved output. The user can swap either competitor
  persona out at any time. Results can be saved as Unifier plans, and a
  plan can be handed off into a real member project (My Projects).

Access (owner policy — enforced here and mirrored in the UI):
  - staff role OR higher (support_staff, oversight, admin, executive_admin)
  - patron feature tier OR higher (patron, platinum, executive)

Persistence (existing MongoDB):
  - unifier_sessions — chat session state, selected personas, exchanges
  - unifier_plans    — saved synthesis plans the user oversees
  - unifier_uploads  — attached files/images (served back via /unifier/media)
  - member_projects  — plan→project handoff target (same collection My
                       Projects reads; document shape matches
                       routers/member_projects.py exactly)

All external behavior is real:
  - chat goes through the existing AI gateway (call_llm, 6-tier fallback,
    BYOK routing, Source root protocol composition)
  - judge audio goes through the existing persona TTS chain
  - projects created through the handoff appear in My Projects
"""

from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.params import Header, Path
from pydantic import BaseModel, ConfigDict

from security.unifier_access import user_can_use_unifier

logger = logging.getLogger("unifier")
router = APIRouter(tags=["unifier"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit=None):
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


UNAVAILABLE_MSG = "The Unifier is not available right now."

# The judge is the unified model — the single mind that already carries every
# persona capability (Hybrid NAM / The 9). Real persona key from the registry.
JUDGE_PERSONA_ID = "unified"
JUDGE_LABEL = "Hybrid NAM (Judge)"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_context_doc(context_id: str, owner_id: str) -> dict | None:
    if db is None:
        return None
    return db.arena_work_context.find_one({"id": context_id, "owner_id": owner_id}, {"_id": 0})


async def _ensure_context_for_session(user_id: str, work_context_id: str | None, title_hint: str = "") -> str:
    if work_context_id:
        ctx = _get_context_doc(work_context_id, user_id)
        if ctx:
            return work_context_id
    now = _now_iso()
    ctx_doc = {
        "id": str(uuid.uuid4()),
        "owner_id": user_id,
        "title": title_hint or "Unifier Session",
        "status": "exploring",
        "source_capability": "unifier",
        "activity_history": [
            {
                "action_type": "context_created",
                "description": f"Work context created via Unifier: {title_hint or 'Unifier Session'}",
                "capability": "unifier",
                "at": now,
            }
        ],
        "created_at": now,
        "updated_at": now,
        "created_by": user_id,
    }
    if db is not None:
        await db.arena_work_context.insert_one(ctx_doc)
    return ctx_doc["id"]


async def _append_context_event(context_id: str, owner_id: str, action_type: str, description: str, capability: str = "unifier", metadata: dict | None = None):
    if db is None:
        return
    now = _now_iso()
    await db.arena_work_context.update_one(
        {"id": context_id, "owner_id": owner_id},
        {
            "$push": {"activity_history": {"action_type": action_type, "description": description, "capability": capability, "metadata": metadata or {}, "at": now}},
            "$set": {"updated_at": now, "source_capability": capability},
        },
    )


def _sessions():
    return db.unifier_sessions if db is not None else None


def _plans():
    return db.unifier_plans if db is not None else None


# ── Auth dependency ───────────────────────────────────────────────────────────
async def _unifier_user(authorization: Optional[str] = Header(None)):
    if current_user is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    return await current_user(authorization)


def _require_unifier_access(user: Any):
    if not user_can_use_unifier(user):
        raise HTTPException(
            403,
            "The Unifier requires a staff role and the Patron tier. "
            "Upgrade to Patron or contact an administrator.",
        )
    return user


# ── Persona registry access ───────────────────────────────────────────────────
def _persona_prompt(persona_id: str) -> str:
    """Return the composed system prompt for a registry persona key."""
    try:
        from ai.persona_loader import get_persona_sync
    except Exception as _e:  # pragma: no cover
        raise HTTPException(503, "Persona support is unavailable.") from _e
    try:
        return get_persona_sync(persona_id)
    except KeyError:
        raise HTTPException(404, f"Persona '{persona_id}' not found.")


def _persona_label(persona_id: str) -> str:
    return persona_id.replace("_", " ").title()


def _list_personas() -> list[dict[str, str]]:
    try:
        from ai.persona_loader import load_personas
    except Exception as _e:  # pragma: no cover
        raise HTTPException(503, "Persona support is unavailable.") from _e
    keys = sorted(k for k in load_personas().keys() if k != "unified")
    return [
        {"id": JUDGE_PERSONA_ID, "label": JUDGE_LABEL, "role": "judge", "locked": True},
        *[
            {"id": k, "label": _persona_label(k), "role": "competitor", "locked": False}
            for k in keys
        ],
    ]


# ── AI / TTS ─────────────────────────────────────────────────────────────────
async def _persona_reply(persona_id: str, user_message: str, user_id: str,
                         context: dict[str, Any] | None = None) -> str:
    """Real LLM call through the existing gateway (BYOK + fallback included)."""
    from ai.llm_gateway import call_llm

    system = _persona_prompt(persona_id)
    content = user_message
    if context:
        content = (
            "Context from the Unifier session:\n"
            + _dump(context)
            + "\n\nUser message:\n"
            + user_message
        )
    result = await call_llm(
        system=system,
        messages=[{"role": "user", "content": content}],
        persona_label=f"unifier:{persona_id}",
        user_id=user_id or None,
        max_tokens=1200,
    )
    text = (result or {}).get("text") or ""
    if not text.strip():
        raise HTTPException(503, "The AI provider returned no response. Try again.")
    return text.strip()


def _dump(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)


async def _judge_audio(text: str) -> Optional[str]:
    """Real TTS through the persona chain; returns a data URI or None."""
    try:
        from ai.persona_tts import persona_speak
        result = await persona_speak(JUDGE_PERSONA_ID, text, db=db)
        audio = (result or {}).get("audio")
        if audio:
            return "data:audio/mpeg;base64," + base64.b64encode(audio).decode("ascii")
    except Exception as _e:
        logger.warning("Unifier TTS unavailable: %s", _e)
    return None


# ── Session helpers ───────────────────────────────────────────────────────────
async def _find_session(session_id: str) -> dict:
    sessions = _sessions()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = await sessions.find_one({"id": session_id})
    if doc is None:
        raise HTTPException(404, "Unifier session not found.")
    doc.pop("_id", None)
    return doc


async def _own_session(session_id: str, user: Any) -> dict:
    doc = await _find_session(session_id)
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That session does not belong to you.")
    return doc


async def _persist_session(doc: dict) -> dict:
    sessions = _sessions()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc["updated_at"] = _now_iso()
    await sessions.replace_one({"id": doc["id"]}, doc, upsert=True)
    doc.pop("_id", None)
    return doc


# ── Request / response models ────────────────────────────────────────────────
class PersonaRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_id: str
    label: str | None = None


class UnifierSwapRequest(BaseModel):
    competitor_a: PersonaRef
    competitor_b: PersonaRef


class UnifierSessionCreate(BaseModel):
    work_context_id: str | None = None


class UnifierChatRequest(BaseModel):
    message: str
    audio_response: bool = False


class UnifierPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    objective: str
    audience: str | None = None
    format: Literal["news", "ai_view", "soap", "gameshow", "programming", "other"] = "other"
    notes: str | None = None
    work_context_id: str | None = None


class UnifierPlanToProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Literal["launch", "create", "organize", "grow", "learn"] = "launch"
    priority: Literal["low", "normal", "high"] = "normal"
    desired_outcome: str = ""
    work_context_id: str | None = None


# ── Persona catalog ───────────────────────────────────────────────────────────
@router.get("/unifier/personas")
async def list_unifier_personas(user: Any = Depends(_unifier_user)):
    _require_unifier_access(user)
    return {"personas": _list_personas(), "judge": {"id": JUDGE_PERSONA_ID, "label": JUDGE_LABEL}}


# ── Session lifecycle ────────────────────────────────────────────────────────
@router.post("/unifier/sessions", status_code=201)
async def create_unifier_session(user: Any = Depends(_unifier_user), body: UnifierSessionCreate | None = None):
    _require_unifier_access(user)
    sessions = _sessions()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    session_id = f"unifier_{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    user_id = getattr(user, "id", "")
    work_context_id = None
    if body and getattr(body, "work_context_id", None):
        work_context_id = body.work_context_id
        ctx = _get_context_doc(work_context_id, user_id)
        if ctx:
            await _append_context_event(work_context_id, user_id, "unifier_session_started", "Unifier session started", capability="unifier")
    if not work_context_id:
        work_context_id = await _ensure_context_for_session(user_id, None, title_hint="Unifier Session")
    doc = {
        "id": session_id,
        "user_id": user_id,
        "work_context_id": work_context_id,
        "judge": {"id": JUDGE_PERSONA_ID, "label": JUDGE_LABEL},
        "competitor_a": {"id": "director", "label": "Director"},
        "competitor_b": {"id": "ancestral_sage", "label": "Ancestral Sage"},
        "exchanges": [],
        "message_count": 0,
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
    }
    await sessions.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/unifier/sessions/{session_id}")
async def get_unifier_session(
    session_id: str = Path(..., description="Session ID"),
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    return await _own_session(session_id, user)


@router.patch("/unifier/sessions/{session_id}")
async def patch_unifier_session(
    session_id: str = Path(..., description="Session ID"),
    body: UnifierSwapRequest = None,
    user: Any = Depends(_unifier_user),
):
    """Swap either competitor persona. The judge (Hybrid NAM) stays fixed."""
    _require_unifier_access(user)
    if body is None:
        raise HTTPException(400, "No persona swap provided.")
    session = await _own_session(session_id, user)
    a, b = body.competitor_a.persona_id, body.competitor_b.persona_id
    # Validate both against the real registry (404 if unknown).
    _persona_prompt(a)
    _persona_prompt(b)
    session["competitor_a"] = {
        "id": a,
        "label": body.competitor_a.label or _persona_label(a),
    }
    session["competitor_b"] = {
        "id": b,
        "label": body.competitor_b.label or _persona_label(b),
    }
    return await _persist_session(session)


# ── Chat: A pass, B pass, then Hybrid NAM judges and synthesizes ─────────────
@router.post("/unifier/sessions/{session_id}/chat")
async def unifier_chat(
    session_id: str = Path(..., description="Session ID"),
    body: UnifierChatRequest = None,
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    if body is None or not (body.message or "").strip():
        raise HTTPException(400, "Type a message first.")
    if len(body.message) > 4000:
        raise HTTPException(400, "Message is too long (4000 characters max).")
    session = await _own_session(session_id, user)
    user_id = getattr(user, "id", "")
    message = body.message.strip()

    competitor_a_id = session["competitor_a"]["id"]
    competitor_b_id = session["competitor_b"]["id"]

    # 1. Competitor A takes its pass
    a_reply = await _persona_reply(competitor_a_id, message, user_id, {
        "role": "competitor_a", "session": session_id,
    })
    # 2. Competitor B takes its pass
    b_reply = await _persona_reply(competitor_b_id, message, user_id, {
        "role": "competitor_b", "session": session_id,
    })
    # 3. Hybrid NAM judges both and synthesizes the improved answer
    judge_reply = await _persona_reply(JUDGE_PERSONA_ID, message, user_id, {
        "role": "judge",
        "competitor_a_label": session["competitor_a"]["label"],
        "competitor_a_reply": a_reply,
        "competitor_b_label": session["competitor_b"]["label"],
        "competitor_b_reply": b_reply,
        "instruction": (
            "You are the judge in the Unifier. Two personas answered the user "
            "independently. Identify what each got right and wrong, then produce "
            "ONE improved answer that beats both. End with a concrete next step."
        ),
    })

    audio_url = None
    if body.audio_response:
        audio_url = await _judge_audio(judge_reply)

    exchange = {
        "at": _now_iso(),
        "user_message": message,
        "competitor_a_id": competitor_a_id,
        "competitor_a_label": session["competitor_a"]["label"],
        "competitor_a": a_reply,
        "competitor_b_id": competitor_b_id,
        "competitor_b_label": session["competitor_b"]["label"],
        "competitor_b": b_reply,
        "judge": judge_reply,
        "audio_url": audio_url,
    }
    session.setdefault("exchanges", []).append(exchange)
    session["message_count"] = session.get("message_count", 0) + 1
    session["last_message_at"] = _now_iso()
    await _persist_session(session)

    return exchange


# ── Media upload / retrieval (session attachments) ───────────────────────────
@router.post("/unifier/sessions/{session_id}/upload")
async def upload_unifier_media(
    session_id: str = Path(..., description="Session ID"),
    file: UploadFile | None = File(None),
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    await _own_session(session_id, user)
    if file is None or not file.filename:
        raise HTTPException(400, "No file provided.")
    if db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    content_type = (file.content_type or "application/octet-stream").lower()
    if not content_type.startswith(("image/", "audio/", "video/", "application/pdf", "text/")):
        raise HTTPException(415, "Unsupported file type.")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "File too large. Max 25 MB.")
    file_id = f"unifier_file_{uuid.uuid4().hex[:16]}"
    await db.unifier_uploads.insert_one({
        "id": file_id,
        "user_id": getattr(user, "id", ""),
        "name": file.filename,
        "content_type": content_type,
        "size_bytes": len(data),
        "data": data,
        "created_at": _now_iso(),
    })
    return {"file_id": file_id, "name": file.filename, "url": f"/api/unifier/media/{file_id}"}


@router.get("/unifier/media/{file_id}")
async def get_unifier_media(
    file_id: str = Path(..., description="File ID"),
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    if db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = await db.unifier_uploads.find_one({"id": file_id})
    if doc is None:
        raise HTTPException(404, "Uploaded media not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "You do not own that media.")
    from fastapi.responses import Response
    return Response(content=doc["data"], media_type=doc.get("content_type", "application/octet-stream"))


# ── Plans: saved syntheses the user oversees ─────────────────────────────────
@router.post("/unifier/sessions/{session_id}/plans", status_code=201)
async def create_unifier_plan(
    session_id: str = Path(..., description="Session ID"),
    body: UnifierPlanRequest = None,
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    if body is None or not body.title.strip() or not body.objective.strip():
        raise HTTPException(400, "A plan needs a title and an objective.")
    session = await _own_session(session_id, user)
    plans = _plans()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    now = _now_iso()
    user_id = getattr(user, "id", "")
    doc = {
        "id": f"unifier_plan_{uuid.uuid4().hex[:16]}",
        "session_id": session_id,
        "user_id": user_id,
        "title": body.title.strip()[:200],
        "objective": body.objective.strip()[:2000],
        "audience": (body.audience or "").strip()[:300] or None,
        "format": body.format,
        "notes": (body.notes or "").strip()[:2000] or None,
        "status": "draft",
        "project_id": None,
        "work_context_id": getattr(body, "work_context_id", None) or session.get("work_context_id"),
        "created_at": now,
        "updated_at": now,
    }
    await plans.insert_one(doc)
    doc.pop("_id", None)
    work_context_id = doc.get("work_context_id")
    if work_context_id:
        await _append_context_event(
            work_context_id, user_id, "plan_created",
            f"Plan created: {body.title.strip()[:200]}",
            capability="unifier",
            metadata={"plan_id": doc["id"], "session_id": session_id},
        )
        await db.arena_work_context.update_one(
            {"id": work_context_id, "owner_id": user_id},
            {"$set": {"updated_at": now, "source_capability": "unifier"}},
        )
    return doc


@router.get("/unifier/plans")
async def list_unifier_plans(user: Any = Depends(_unifier_user)):
    _require_unifier_access(user)
    plans = _plans()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    rows = []
    async for doc in plans.find({"user_id": getattr(user, "id", "")}).sort("updated_at", -1).limit(100):
        doc.pop("_id", None)
        rows.append(doc)
    return rows


@router.get("/unifier/plans/{plan_id}")
async def get_unifier_plan(
    plan_id: str = Path(..., description="Plan ID"),
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    plans = _plans()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = await plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    doc.pop("_id", None)
    return doc


@router.patch("/unifier/plans/{plan_id}")
async def patch_unifier_plan(
    plan_id: str = Path(..., description="Plan ID"),
    body: UnifierPlanRequest = None,
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    if body is None:
        raise HTTPException(400, "No plan update provided.")
    plans = _plans()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = await plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    update = {
        "title": body.title.strip()[:200] or doc["title"],
        "objective": body.objective.strip()[:2000] or doc["objective"],
        "audience": (body.audience or "").strip()[:300] or None,
        "format": body.format,
        "notes": (body.notes or "").strip()[:2000] or None,
        "updated_at": _now_iso(),
    }
    await plans.update_one({"id": plan_id}, {"$set": update})
    doc.update(update)
    doc.pop("_id", None)
    return doc


@router.delete("/unifier/plans/{plan_id}", status_code=204)
async def delete_unifier_plan(
    plan_id: str = Path(..., description="Plan ID"),
    user: Any = Depends(_unifier_user),
):
    _require_unifier_access(user)
    plans = _plans()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = await plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    await plans.delete_one({"id": plan_id})
    return None


# ── Plan → member project handoff (Hybrid NAM results become real work) ──────
@router.post("/unifier/plans/{plan_id}/to-project", status_code=201)
async def unifier_plan_to_project(
    plan_id: str = Path(..., description="Plan ID"),
    body: UnifierPlanToProjectRequest = None,
    user: Any = Depends(_unifier_user),
):
    """Turn a saved Unifier plan into a real member project (My Projects)."""
    _require_unifier_access(user)
    if body is None:
        body = UnifierPlanToProjectRequest()
    plans = _plans()
    if plans is None or db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    plan = await plans.find_one({"id": plan_id})
    if plan is None:
        raise HTTPException(404, "Plan not found.")
    if plan.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    if plan.get("project_id"):
        raise HTTPException(409, "That plan is already a project.")

    # Document shape matches routers/member_projects.py so My Projects reads it.
    now = _now_iso()
    brief = (
        f"{plan['objective']}"
        + (f"\n\nAudience: {plan['audience']}" if plan.get("audience") else "")
        + (f"\n\nNotes: {plan['notes']}" if plan.get("notes") else "")
    )
    project = {
        "title": plan["title"],
        "brief": brief,
        "category": body.category,
        "priority": body.priority,
        "desired_outcome": body.desired_outcome.strip() or plan["objective"][:500],
        "status": "active",
        "current_stage": "intake",
        "stage_history": [{"stage": "intake", "entered_at": now}],
        "context": {"brief": brief, "category": body.category, "source": "unifier", "unifier_plan_id": plan_id},
        "deliverables": [],
        "approvals": [],
        "comments": [],
        "packet": {
            "objective": body.desired_outcome.strip() or plan["objective"][:500],
            "owner": getattr(user, "full_name", "") or getattr(user, "id", ""),
            "ai_team": ["Production", "Marketing", "Operations"],
            "authority": "approval_required",
            "approval_points": ["Approve every deliverable before it counts as done"],
        },
        "owner_id": getattr(user, "id", ""),
        "owner_name": getattr(user, "full_name", "") or getattr(user, "id", ""),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.member_projects.insert_one(project)
    project_id = str(result.inserted_id)
    await plans.update_one(
        {"id": plan_id},
        {"$set": {"status": "in_project", "project_id": project_id, "updated_at": now}},
    )
    if audit is not None:
        try:
            await audit(getattr(user, "id", ""), "unifier.plan_to_project",
                        meta={"plan_id": plan_id, "project_id": project_id})
        except Exception:
            pass
    plan_work_context_id = getattr(body, "work_context_id", None) or plan.get("work_context_id")
    if plan_work_context_id and db is not None:
        try:
            await db.arena_work_context.update_one(
                {"id": plan_work_context_id, "owner_id": getattr(user, "id", "")},
                {"$set": {"status": "planned", "updated_at": now, "source_capability": "unifier"}},
            )
            await db.arena_work_context.update_one(
                {"id": plan_work_context_id, "owner_id": getattr(user, "id", "")},
                {"$push": {"activity_history": {
                    "action_type": "project_handed_off",
                    "description": f"Plan handed off to member project: {project_id}",
                    "capability": "unifier",
                    "metadata": {"plan_id": plan_id, "project_id": project_id},
                    "at": now,
                }}},
            )
        except Exception:
            pass
    return {"project_id": project_id, "plan_id": plan_id, "status": "in_project"}
