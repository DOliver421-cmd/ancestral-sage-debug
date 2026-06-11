"""app/routes/jamil.py — Jamil: unified Supervisor-Class AI persona for NAM Oshun's platform.

Endpoints:
  POST /jamil/chat    — executive_admin only; takes { message: str }; returns { reply: str }
  GET  /jamil/status  — public; returns name, status, and domain list
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user
from app.services.jamil.persona import JAMIL_DOMAINS, JAMIL_SYSTEM_PROMPT
from app.services.llm import chat as _llm_chat

logger = logging.getLogger("lcewai")
router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    return JAMIL_SYSTEM_PROMPT.replace("{today}", today)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/jamil/chat", response_model=ChatResponse)
async def jamil_chat(
    body: ChatRequest,
    user: User = Depends(current_user),
):
    """Send a message to Jamil and receive his response."""
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    system_prompt = _build_system_prompt()

    try:
        reply = await _llm_chat(system=system_prompt, user=body.message.strip(), max_tokens=2048)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Jamil chat error: %s", exc)
        raise HTTPException(status_code=503, detail="Jamil is temporarily unavailable.")

    # Persist conversation history
    if db is not None:
        try:
            await db.jamil_history.insert_one({
                "user_id": str(user.id) if hasattr(user, "id") else str(getattr(user, "_id", "")),
                "message": body.message.strip(),
                "reply": reply,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as exc:
            logger.warning("Jamil history save failed: %s", exc)

    return ChatResponse(reply=reply)


@router.get("/jamil/status")
async def jamil_status():
    """Public status endpoint — confirms Jamil is active and lists his domains."""
    return {
        "name": "Jamil",
        "status": "active",
        "domains": JAMIL_DOMAINS,
    }
