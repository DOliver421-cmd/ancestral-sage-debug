"""app/routes/jamil.py — Jamil: unified Supervisor-Class AI persona.

Endpoints:
  POST /jamil/chat    — any logged-in user; multipart: message + optional files
  POST /jamil/speak   — TTS via ElevenLabs; returns audio/mpeg
  POST /jamil/transcribe — STT via Groq Whisper; returns { text }
  GET  /jamil/status  — public
"""
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.database import db
from app.models.user import User
from app.security.auth import current_user
from app.services.jamil.persona import JAMIL_DOMAINS, JAMIL_SYSTEM_PROMPT
from app.services.llm import chat as _llm_chat

logger = logging.getLogger("lcewai")
router = APIRouter()

_ELEVENLABS_VOICE_ID = os.environ.get("JAMIL_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # default: Adam
_MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB per file
_MAX_FILES = 10


@router.get("/jamil/ping")
async def jamil_ping():
    """No-auth smoke test — confirms Jamil route is registered."""
    return {"status": "ok", "route": "jamil"}


def _build_system_prompt() -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    return JAMIL_SYSTEM_PROMPT.replace("{today}", today)


async def _get_project_context() -> str:
    """Pull active projects from DB and format for Jamil's LLM context."""
    if db is None:
        return ""
    try:
        docs = await db.projects.find(
            {"status": {"$ne": "archived"}, "archived": {"$ne": True}},
            {"_id": 0, "project_id": 1, "title": 1, "status": 1, "priority": 1,
             "owner": 1, "due_date": 1, "notes": 1, "milestones": 1, "description": 1}
        ).sort("updated_at", -1).to_list(length=30)

        if not docs:
            return "\n[No active projects in the dashboard at this time.]\n"

        lines = ["\n--- ACTIVE PROJECT DASHBOARD ---"]
        for d in docs:
            lines.append(f"\nPROJECT: {d['title']} | Status: {d['status']} | Priority: {d.get('priority','normal')}")
            lines.append(f"  ID: {d['project_id']}")
            if d.get("owner"):
                lines.append(f"  Owner: {d['owner']}")
            if d.get("due_date"):
                lines.append(f"  Due: {d['due_date']}")
            if d.get("description"):
                lines.append(f"  {d['description']}")
            if d.get("notes"):
                lines.append(f"  Notes: {d['notes']}")
            milestones = d.get("milestones", [])
            if milestones:
                done = sum(1 for m in milestones if m.get("complete"))
                lines.append(f"  Milestones: {done}/{len(milestones)} done")
                for m in milestones:
                    mark = "✓" if m.get("complete") else "○"
                    assigned = f" [{m['assigned_to']}]" if m.get("assigned_to") else ""
                    lines.append(f"    {mark} {m['title']}{assigned}")
        lines.append("--- END PROJECT DASHBOARD ---\n")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("Could not load project context: %s", e)
        return ""


# ── Chat (text + optional files) ─────────────────────────────────────────────

@router.post("/jamil/chat")
async def jamil_chat(
    message: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    user: User = Depends(current_user),
):
    """Send a message and/or files to Jamil. Returns { reply: str }."""
    if not message.strip() and not files:
        raise HTTPException(status_code=400, detail="Send a message or attach a file.")

    system_prompt = _build_system_prompt()

    # Inject live project dashboard into system prompt
    project_context = await _get_project_context()
    if project_context:
        system_prompt = system_prompt + project_context

    # Build user context — message + extracted file contents
    parts = []
    if message.strip():
        parts.append(message.strip())

    for upload in files[:_MAX_FILES]:
        content = await upload.read()
        if len(content) > _MAX_FILE_BYTES:
            parts.append(f"[File {upload.filename} skipped — exceeds 50 MB limit]")
            continue
        try:
            from app.services.jamil.extractor import extract as extract_file
            extracted = await extract_file(
                upload.filename or "file",
                content,
                upload.content_type or "",
            )
            parts.append(f"\n---\nAttached file: {upload.filename}\n{extracted}\n---")
        except Exception as e:
            logger.warning("File extraction failed for %s: %s", upload.filename, e)
            parts.append(f"[File {upload.filename} — could not be read: {e}]")

    user_message = "\n\n".join(parts)

    try:
        reply = await _llm_chat(system=system_prompt, user=user_message, max_tokens=4096)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Jamil chat error: %s", exc)
        raise HTTPException(status_code=503, detail="Jamil is temporarily unavailable.")

    # Persist conversation history
    if db is not None:
        try:
            await db.jamil_history.insert_one({
                "user_id": str(getattr(user, "id", "") or getattr(user, "_id", "")),
                "message": message.strip(),
                "files": [f.filename for f in files],
                "reply": reply,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as exc:
            logger.warning("Jamil history save failed: %s", exc)

    return {"reply": reply}


# ── TTS — Jamil speaks via ElevenLabs ────────────────────────────────────────

@router.post("/jamil/speak")
async def jamil_speak(
    body: dict,
    user: User = Depends(current_user),
):
    """Convert Jamil's reply to speech via ElevenLabs. Returns audio/mpeg."""
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")
    if len(text) > 5000:
        text = text[:5000]

    el_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not el_key:
        raise HTTPException(status_code=503, detail="ElevenLabs not configured.")

    voice_id = body.get("voice_id") or _ELEVENLABS_VOICE_ID

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": el_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )
            if r.status_code == 200:
                return Response(content=r.content, media_type="audio/mpeg")
            logger.warning("ElevenLabs TTS returned %s: %s", r.status_code, r.text[:200])
            raise HTTPException(status_code=502, detail=f"ElevenLabs error: {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Jamil TTS failed: %s", e)
        raise HTTPException(status_code=503, detail="Voice synthesis unavailable.")


# ── STT — transcribe voice input via Groq Whisper ────────────────────────────

@router.post("/jamil/transcribe")
async def jamil_transcribe(
    audio: UploadFile = File(...),
    user: User = Depends(current_user),
):
    """Transcribe voice input. Returns { text: str }."""
    content = await audio.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file must be under 25 MB.")

    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Transcription not configured.")

    import io
    filename = audio.filename or "recording.webm"
    ct = audio.content_type or "audio/webm"
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (filename, io.BytesIO(content), ct)},
                data={"model": "whisper-large-v3", "response_format": "text"},
            )
            if r.status_code == 200:
                return {"text": r.text.strip()}
            raise HTTPException(status_code=502, detail=f"Transcription error: {r.status_code}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Jamil transcribe failed: %s", e)
        raise HTTPException(status_code=503, detail="Transcription unavailable.")


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/jamil/status")
async def jamil_status():
    el_configured = bool(os.environ.get("ELEVENLABS_API_KEY", ""))
    groq_configured = bool(os.environ.get("GROQ_API_KEY", ""))
    return {
        "name": "Jamil",
        "status": "active",
        "voice": "elevenlabs" if el_configured else "unavailable",
        "transcription": "groq-whisper" if groq_configured else "unavailable",
        "file_types": ["pdf", "docx", "xlsx", "csv", "images", "audio", "video", "code", "text"],
        "domains": JAMIL_DOMAINS,
    }
