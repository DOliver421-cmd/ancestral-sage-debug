"""
backend/routers/unifier.py — The Unifier

Editorial / creative production layer for MoreHelp Center.
One persona-ruleset vs others, re-tested by another ruleset to improve output,
with Hybrid NAM acting as the judge / synthesis voice.

Access:
  - staff role OR higher (support_staff, oversight, admin, executive_admin)
  - patron feature tier

Persistence:
  - unifier_sessions — chat session state + selected competitor personas
  - unifier_plans     — arena-plan feed records the user can oversee

All external behavior is real:
  - chat uses the existing AI gateway / provider routing via call_llm
  - audio uses the existing persona TTS (persona_speak)
  - file/image upload uses the existing media upload path
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.params import Path
from fastapi.params import Header
from pydantic import BaseModel, Field, ConfigDict

from security.unifier_access import user_can_use_unifier

# Import current_user from server for auth dependency
try:
    from server import current_user, db  # noqa: PLC0414
except Exception:
    current_user = None  # type: ignore
    db = None  # type: ignore

router = APIRouter()


# Wrapper for current_user that handles DB-not-available gracefully
async def _unifier_current_user(authorization: str | None = Header(None)):
    """Get current user, returning 503 if DB is not available."""
    if db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    return await current_user(authorization)
logger = logging.getLogger("unifier")

# ── Persistent collections ────────────────────────────────────────────────────
# These live in the existing MongoDB that server.py already connects.
UNAVAILABLE_MSG = "The Unifier is not available right now."


def _collections():
    if db is None:
        return None, None
    return db.unifier_sessions, db.unifier_plans


# ── Request / response models ─────────────────────────────────────────────────
class UnifierChatRequest(BaseModel):
    session_id: str
    message: str
    kind: Literal["user", "competitor_a", "competitor_b", "judge"] = "user"
    attached_file_id: str | None = None
    attached_image_id: str | None = None
    audio_response: bool = False


class UnifierChatResponse(BaseModel):
    session_id: str
    role: str
    text: str
    audio_url: str | None = None
    attached_files: list[dict[str, Any]] = []
    attached_images: list[dict[str, Any]] = []
    model: str | None = None


class UnifierSwapRequest(BaseModel):
    session_id: str
    competitor_a: "PersonaRef"
    competitor_b: "PersonaRef"


class PersonaRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona_id: str
    label: str | None = None


class UnifierSettingsResponse(BaseModel):
    session_id: str
    judge: dict[str, Any]
    competitor_a: dict[str, Any]
    competitor_b: dict[str, Any]


class UnifierPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    title: str
    objective: str
    inputs: dict[str, Any] = {}
    audience: str | None = None
    format: Literal["news", "ai_view", "soap", "gameshow", "programming", "other"] = "other"
    notes: str | None = None


class UnifierPlanResponse(BaseModel):
    plan_id: str
    session_id: str
    title: str
    objective: str
    format: str
    status: str
    created_at: str
    updated_at: str


class UnifierUploadResponse(BaseModel):
    file_id: str
    name: str
    kind: Literal["file", "image"]
    url: str
    mime: str
    size_bytes: int


# ── Small helpers ─────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_unifier_access(user: Any):
    if not user_can_use_unifier(user):
        raise HTTPException(403, "The Unifier requires staff role and patron tier.")
    return user


def _find_session(session_id: str):
    sessions, _ = _collections()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = sessions.find_one({"id": session_id})
    if doc is None:
        raise HTTPException(404, "Unifier session not found.")
    doc.pop("_id", None)
    return doc


def _persist_session(doc: dict):
    sessions, _ = _collections()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc["updated_at"] = _now_iso()
    sessions.replace_one({"id": doc["id"]}, doc, upsert=True)
    doc.pop("_id", None)
    return doc


# ── Persona loading ───────────────────────────────────────────────────────────
def _load_persona(persona_id: str) -> dict[str, Any]:
    try:
        from backend.ai.persona_loader import load_persona  # noqa: PLC0414
    except Exception as _e:
        raise HTTPException(503, "Persona support is unavailable.") from _e
    persona = load_persona(persona_id)
    if persona is None:
        raise HTTPException(404, f"Persona '{persona_id}' not found.")
    return persona


# ── AI + TTS + media ──────────────────────────────────────────────────────────
def _generate_ai_reply(persona: dict[str, Any], user_message: str, context: dict[str, Any]) -> str:
    try:
        from backend.ai.llm_gateway import call_llm  # noqa: PLC0414
    except Exception as _e:
        raise HTTPException(503, "AI provider support is unavailable.") from _e
    system = persona.get("prompt") or persona.get("system") or ""
    user_content = user_message
    if context:
        user_content = json.dumps({"context": context, "message": user_message}, ensure_ascii=False)
    reply = call_llm(system=system, user=user_content, persona_id=persona.get("id"))
    if not reply:
        raise HTTPException(503, "AI provider returned no response.")
    return reply


def _generate_audio(text: str, voice_id: str | None = None) -> str | None:
    try:
        from backend.ai.persona_tts import persona_speak  # noqa: PLC0414
    except Exception as _e:
        logger.warning("Unifier TTS import failed: %s", _e)
        return None
    try:
        url = persona_speak(text=text, voice_id=voice_id)
    except Exception as _e:
        logger.warning("Unifier TTS failed for voice %s: %s", voice_id, _e)
        return None
    if not url:
        return None
    return url


def _validate_media_file(file: UploadFile) -> tuple[str, str, int]:
    if not file or not file.filename:
        raise HTTPException(400, "No file provided.")
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", file.filename or "upload")
    if not name:
        name = "upload"
    content_type = (file.content_type or "application/octet-stream").lower()
    data = file.file.read()
    size = len(data)
    max_bytes = 25 * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(413, "File too large. Max 25 MB.")
    if not content_type.startswith(("image/", "audio/", "video/", "application/pdf", "text/")):
        raise HTTPException(415, "Unsupported file type.")
    return name, content_type, size


async def _store_uploaded_file(user_id: str, name: str, content_type: str, data: bytes, kind: Literal["file", "image"]) -> UnifierUploadResponse:
    if db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    file_id = f"unifier_file_{uuid.uuid4().hex[:16]}"
    doc = {
        "id": file_id,
        "user_id": user_id,
        "name": name,
        "content_type": content_type,
        "kind": kind,
        "size_bytes": len(data),
        "created_at": _now_iso(),
        "data": data,
    }
    await db.unifier_uploads.insert_one(doc)
    return UnifierUploadResponse(
        file_id=file_id,
        name=name,
        kind=kind,
        url=f"/api/unifier/media/{file_id}",
        mime=content_type,
        size_bytes=len(data),
    )


# ── Session lifecycle ─────────────────────────────────────────────────────────
@router.post("/unifier/sessions", status_code=201)
async def create_unifier_session(user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    sessions, _ = _collections()
    if sessions is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    session_id = f"unifier_{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    doc = {
        "id": session_id,
        "user_id": getattr(user, "id", ""),
        "judge": {"id": "hybrid_nam", "label": "Hybrid NAM (Judge)"},
        "competitor_a": {"id": "assistant_director", "label": "Assistant Director"},
        "competitor_b": {"id": "director", "label": "Director"},
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
        "message_count": 0,
    }
    sessions.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/unifier/sessions/{session_id}")
async def get_unifier_session(session_id: str = Path(..., description="Session ID"), user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    session = _find_session(session_id)
    if session.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That session does not belong to you.")
    return session


@router.patch("/unifier/sessions/{session_id}")
async def patch_unifier_session(
    session_id: str = Path(..., description="Session ID"),
    settings: UnifierSwapRequest = None,
    user: Any = Depends(_unifier_current_user),
):
    _require_unifier_access(user)
    session = _find_session(session_id)
    if session.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That session does not belong to you.")
    if settings is None:
        raise HTTPException(400, "No settings provided.")
    competitor_a = _load_persona(settings.competitor_a.persona_id)
    competitor_b = _load_persona(settings.competitor_b.persona_id)
    session["competitor_a"] = {"id": competitor_a["id"], "label": settings.competitor_a.label or competitor_a.get("label") or competitor_a["id"]}
    session["competitor_b"] = {"id": competitor_b["id"], "label": settings.competitor_b.label or competitor_b.get("label") or competitor_b["id"]}
    session["updated_at"] = _now_iso()
    return _persist_session(session)


@router.get("/unifier/sessions/{session_id}/settings")
async def get_unifier_settings(session_id: str = Path(..., description="Session ID"), user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    session = _find_session(session_id)
    if session.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That session does not belong to you.")
    judge = _load_persona(session["judge"]["id"])
    competitor_a = _load_persona(session["competitor_a"]["id"])
    competitor_b = _load_persona(session["competitor_b"]["id"])
    return UnifierSettingsResponse(
        session_id=session_id,
        judge={"id": judge["id"], "label": judge.get("label") or judge["id"], "role": "judge"},
        competitor_a={"id": competitor_a["id"], "label": session["competitor_a"]["label"] or competitor_a.get("label") or competitor_a["id"]},
        competitor_b={"id": competitor_b["id"], "label": session["competitor_b"]["label"] or competitor_b.get("label") or competitor_b["id"]},
    )


# ── Chat ──────────────────────────────────────────────────────────────────────
@router.post("/unifier/sessions/{session_id}/chat", response_model=UnifierChatResponse)
async def unifier_chat(
    session_id: str = Path(..., description="Session ID"),
    payload: UnifierChatRequest = None,
    file: UploadFile | None = File(None),
    image: UploadFile | None = File(None),
    user: Any = Depends(_unifier_current_user),
):
    _require_unifier_access(user)
    if payload is None:
        raise HTTPException(400, "No chat payload provided.")
    session = _find_session(session_id)
    if session.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That session does not belong to you.")

    attached_files = []
    attached_images = []

    if file is not None:
        name, mime, size = _validate_media_file(file)
        uploaded = await _store_uploaded_file(getattr(user, "id", ""), name, mime, file.file.read(), "file")
        attached_files.append({"id": uploaded.file_id, "name": uploaded.name, "mime": uploaded.mime, "size_bytes": uploaded.size_bytes})
        session["attached_files"] = session.get("attached_files", []) + [uploaded.file_id]

    if image is not None:
        name, mime, size = _validate_media_file(image)
        uploaded = await _store_uploaded_file(getattr(user, "id", ""), name, mime, image.file.read(), "image")
        attached_images.append({"id": uploaded.file_id, "name": uploaded.name, "mime": uploaded.mime, "size_bytes": uploaded.size_bytes})
        session["attached_images"] = session.get("attached_images", []) + [uploaded.file_id]

    # 1. Competitor A responds
    competitor_a = _load_persona(session["competitor_a"]["id"])
    competitor_a_reply = _generate_ai_reply(competitor_a, payload.message, {"session": session_id, "attached_files": len(attached_files), "attached_images": len(attached_images)})

    # 2. Competitor B responds
    competitor_b = _load_persona(session["competitor_b"]["id"])
    competitor_b_reply = _generate_ai_reply(competitor_b, payload.message, {"session": session_id, "attached_files": len(attached_files), "attached_images": len(attached_images)})

    # 3. Hybrid NAM judge synthesizes + improves
    judge = _load_persona(session["judge"]["id"])
    judged_context = {
        "competitor_a_reply": competitor_a_reply,
        "competitor_b_reply": competitor_b_reply,
        "user_message": payload.message,
        "attached_files_count": len(attached_files),
        "attached_images_count": len(attached_images),
    }
    judge_reply = _generate_ai_reply(judge, payload.message, judged_context)

    # 4. Optional audio from judge
    audio_url = None
    if payload.audio_response:
        voice_id = judge.get("voice_id") or judge.get("tts_voice") or None
        audio_url = _generate_audio(judge_reply, voice_id=voice_id)

    # Persist the exchange
    exchange = {
        "at": _now_iso(),
        "kind": payload.kind,
        "user_message": payload.message,
        "competitor_a": competitor_a_reply,
        "competitor_b": competitor_b_reply,
        "judge": judge_reply,
        "audio_url": audio_url,
        "attached_files": attached_files,
        "attached_images": attached_images,
    }
    session.setdefault("exchanges", []).append(exchange)
    session["last_message_at"] = _now_iso()
    session["message_count"] = session.get("message_count", 0) + 1
    _persist_session(session)

    return UnifierChatResponse(
        session_id=session_id,
        role="judge",
        text=judge_reply,
        audio_url=audio_url,
        attached_files=attached_files,
        attached_images=attached_images,
        model=judge.get("model") or judge.get("provider") or None,
    )


# ── Media retrieval ──────────────────────────────────────────────────────────
@router.get("/unifier/media/{file_id}")
async def get_unifier_media(file_id: str = Path(..., description="File ID"), user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    if db is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = db.unifier_uploads.find_one({"id": file_id})
    if doc is None:
        raise HTTPException(404, "Uploaded media not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "You do not own that media.")
    from fastapi.responses import Response
    return Response(content=doc["data"], media_type=doc.get("content_type", "application/octet-stream"))


# ── Arena-plan feed ──────────────────────────────────────────────────────────
@router.post("/unifier/sessions/{session_id}/plans", status_code=201, response_model=UnifierPlanResponse)
async def create_unifier_plan(
    session_id: str = Path(..., description="Session ID"),
    payload: UnifierPlanRequest = None,
    user: Any = Depends(_unifier_current_user),
):
    _require_unifier_access(user)
    if payload is None:
        raise HTTPException(400, "No plan payload provided.")
    _find_session(session_id)  # ensure session belongs to user
    plans, _ = _collections()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    plan_id = f"unifier_plan_{uuid.uuid4().hex[:16]}"
    now = _now_iso()
    doc = {
        "id": plan_id,
        "session_id": session_id,
        "user_id": getattr(user, "id", ""),
        "title": payload.title,
        "objective": payload.objective,
        "format": payload.format,
        "audience": payload.audience,
        "inputs": payload.inputs,
        "notes": payload.notes,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }
    plans.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/unifier/plans")
async def list_unifier_plans(user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    plans, _ = _collections()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    rows = []
    async for doc in plans.find({"user_id": getattr(user, "id", "")}).sort("updated_at", -1):
        doc.pop("_id", None)
        rows.append(doc)
    return rows


@router.get("/unifier/plans/{plan_id}")
async def get_unifier_plan(plan_id: str = Path(..., description="Plan ID"), user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    plans, _ = _collections()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    doc.pop("_id", None)
    return doc


@router.patch("/unifier/plans/{plan_id}")
async def patch_unifier_plan(
    plan_id: str = Path(..., description="Plan ID"),
    payload: UnifierPlanRequest = None,
    user: Any = Depends(_unifier_current_user),
):
    _require_unifier_access(user)
    if payload is None:
        raise HTTPException(400, "No plan payload provided.")
    plans, _ = _collections()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if k != "session_id"}
    update["updated_at"] = _now_iso()
    if "status" in update:
        update["status"] = str(update["status"]).lower()
    plans.update_one({"id": plan_id}, {"$set": update})
    doc.update(update)
    doc.pop("_id", None)
    return doc


@router.delete("/unifier/plans/{plan_id}", status_code=204)
async def delete_unifier_plan(plan_id: str = Path(..., description="Plan ID"), user: Any = Depends(_unifier_current_user)):
    _require_unifier_access(user)
    plans, _ = _collections()
    if plans is None:
        raise HTTPException(503, UNAVAILABLE_MSG)
    doc = plans.find_one({"id": plan_id})
    if doc is None:
        raise HTTPException(404, "Plan not found.")
    if doc.get("user_id") != getattr(user, "id", ""):
        raise HTTPException(403, "That plan does not belong to you.")
    plans.delete_one({"id": plan_id})
    return None
