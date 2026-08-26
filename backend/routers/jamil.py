"""
jamil — JAMIL — Director-class AI persona (digest, knowledge, chat, speak, transcribe, status).

Extracted verbatim from backend/server.py (monolith refactor, slice 13).
Shared state is bound by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['jamil'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None


def bind(_db, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user
    
    db = _db
    current_user = _current_user


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
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


# ── JAMIL — Director-class AI persona ────────────────────────────────────────
import os as _os_jamil
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

def _jamil_system_prompt() -> str:
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    try:
        import sys as _sys
        _sys.path.insert(0, "/app")
        from ai.jamil_persona import JAMIL_SYSTEM_PROMPT as _JP
        return _JP.replace("{today}", today)
    except Exception:
        return f"You are Jamil. The Director. Supervisor. Director. PRT. You run this operation. Today is {today}. Named after a son. Built to carry it. Cape and all."

# Start the 12-hour knowledge digest scheduler at import time (server startup)
try:
    from ai.knowledge_digest import start_digest_scheduler as _start_digest
    import asyncio as _asyncio_kd
    async def _schedule_digest_on_startup():
        _start_digest(db)
    _asyncio_kd.get_event_loop().run_until_complete(_schedule_digest_on_startup()) if False else None
    # Actual start happens via the startup event below
    _DIGEST_READY = True
except Exception as _de:
    logger.warning("Knowledge digest scheduler unavailable: %s", _de)
    _DIGEST_READY = False

@router.post("/jamil/digest")
async def jamil_digest_trigger(user: User = Depends(_require_rank("admin"))):
    """Manually trigger a knowledge digest immediately — admin only."""
    try:
        from ai.knowledge_digest import run_digest as _run_digest
        result = await _run_digest(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jamil/knowledge")
async def jamil_knowledge_list(user: User = Depends(_require_rank("admin"))):
    """List all knowledge base entries — admin only."""
    try:
        entries = await db.jamil_knowledge.find(
            {}, {"_id": 0},
            sort=[("created_at", -1)],
        ).to_list(length=50)
        return {"entries": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jamil/ping")
async def jamil_ping():
    return {"status": "ok", "route": "jamil"}

@router.post("/jamil/chat")
async def jamil_chat_server(
    message: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    user: User = Depends(_dep_current_user),
):
    if not message.strip() and not files:
        raise HTTPException(status_code=400, detail="Send a message or attach a file.")

    system = _jamil_system_prompt()

    # Inject knowledge base context (last 12 digested knowledge entries)
    try:
        from ai.knowledge_digest import get_knowledge_context as _get_kb
        kb_context = await _get_kb(db)
        if kb_context:
            system += kb_context
    except Exception:
        pass

    # Inject active project context
    try:
        docs = await db.projects.find(
            {"status": {"$ne": "archived"}, "archived": {"$ne": True}},
            {"_id": 0, "title": 1, "status": 1, "priority": 1, "owner": 1, "milestones": 1}
        ).sort("updated_at", -1).to_list(length=20)
        if docs:
            lines = ["\n--- ACTIVE PROJECTS ---"]
            for d in docs:
                ms = d.get("milestones", [])
                done = sum(1 for m in ms if m.get("complete"))
                lines.append(f"• {d['title']} [{d['status']}] owner:{d.get('owner','-')} milestones:{done}/{len(ms)}")
            lines.append("--- END PROJECTS ---\n")
            system += "\n".join(lines)
    except Exception:
        pass

    parts = [message.strip()] if message.strip() else []
    for upload in files[:10]:
        content = await upload.read()
        if len(content) > 50 * 1024 * 1024:
            parts.append(f"[{upload.filename} skipped — exceeds 50 MB]")
            continue
        try:
            from ai.jamil_extractor import extract as _extract
            extracted = await _extract(upload.filename or "file", content, upload.content_type or "")
            parts.append(f"\n---\nFile: {upload.filename}\n{extracted}\n---")
        except Exception as _fe:
            try:
                parts.append(f"\n---\nFile: {upload.filename}\n{content.decode('utf-8', errors='replace')[:4000]}\n---")
            except Exception:
                parts.append(f"[{upload.filename} — could not be read]")

    user_message = "\n\n".join(parts)

    # Route through the full 9-tier free gateway — Groq → Cerebras → SambaNova →
    # Gemini → Grok → Cohere → Mistral → Together → OpenRouter → HuggingFace → KB
    from ai.llm_gateway import call_llm as _gateway_call
    result = await _gateway_call(
        system=system,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=4096,
        persona_label="jamil",
    )
    reply = result.get("text", "").strip()

    if not reply or result.get("provider") == "kb_fallback":
        if not reply:
            raise HTTPException(
                status_code=503,
                detail="No AI provider available. Add at least one free API key in Railway Variables: GROQ_API_KEY, CEREBRAS_API_KEY, SAMBANOVA_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, or TOGETHER_API_KEY.",
            )
        # KB fallback returned something — pass it through rather than 503
        logger.warning("Jamil routed to KB fallback — all AI providers unavailable")

    try:
        await db.jamil_history.insert_one({
            "user_id": str(getattr(user, "id", "") or getattr(user, "_id", "")),
            "message": message.strip(),
            "files": [f.filename for f in files],
            "reply": reply,
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        })
    except Exception:
        pass

    return {"reply": reply}

@router.get("/jamil/history")
async def jamil_history(user: User = Depends(_dep_current_user), limit: int = 60):
    """Jamil's conversation history for the current operator — so the chat
    syncs across sessions/devices instead of living only in localStorage.

    Admin/exec-only surface like the rest of /jamil/*; the FCC middleware
    enforces the registry classification.
    """
    limit = max(1, min(int(limit), 200))
    try:
        records = await db.jamil_history.find(
            {"user_id": str(getattr(user, "id", "") or getattr(user, "_id", ""))},
            {"_id": 0, "message": 1, "files": 1, "reply": 1, "timestamp": 1},
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        records.reverse()  # chronological order for the chat UI
        return {"history": records}
    except Exception:
        return {"history": []}


@router.post("/jamil/speak")
async def jamil_speak_server(body: dict, user: User = Depends(_dep_current_user)):
    """Server-side TTS disabled. Returns text for browser TTS (free, zero cost)."""
    text = (body.get("text") or "").strip()[:5000]
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")
    return {"text": text, "voice": "browser", "note": "Use browser speechSynthesis for free TTS"}

@router.post("/jamil/transcribe")
async def jamil_transcribe_server(audio: UploadFile = File(...), user: User = Depends(_dep_current_user)):
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio must be under 25 MB.")
    key = _os_jamil.environ.get("GROQ_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Transcription not configured — GROQ_API_KEY missing.")
    import io as _io, httpx as _hx2
    async with _hx2.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {key}"},
            files={"file": (audio.filename or "recording.webm", _io.BytesIO(content), audio.content_type or "audio/webm")},
            data={"model": "whisper-large-v3", "response_format": "text"},
        )
        if r.status_code == 200:
            return {"text": r.text.strip()}
        raise HTTPException(status_code=502, detail=f"Transcription error: {r.status_code}")

@router.get("/jamil/status")
async def jamil_status_server():
    from ai.llm_gateway import gateway_status as _gw_status
    gw = _gw_status()
    active = [k for k, v in gw["providers"].items() if v.get("available") and k != "kb_fallback"]
    return {
        "name": "Jamil",
        "status": "active" if active else "degraded",
        "active_providers": active,
        "provider_count": len(active),
        "voice": "browser_tts",
        "transcription": "groq-whisper" if _os_jamil.environ.get("GROQ_API_KEY") else "unavailable",
        "gateway": gw,
    }

# ── END JAMIL ─────────────────────────────────────────────────────────────────
