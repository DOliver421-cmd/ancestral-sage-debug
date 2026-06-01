"""app/routes/partnership.py — Partnership points, puzzle game, and Sovereign chat.

Ported from backend/server.py lines 10018–10100.
"""
import logging
import secrets as _secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

logger = logging.getLogger("lcewai")
router = APIRouter()


# ── Partnership Points & Tiers ────────────────────────────────────────────────

@router.get("/partnership/status")
async def partnership_status(user: User = Depends(current_user)):
    from app.services.partnership.points import get_status
    return await get_status(db, user.id)


@router.get("/partnership/ledger")
async def partnership_ledger(limit: int = 20, user: User = Depends(current_user)):
    from app.services.partnership.points import LEDGER_COLLECTION
    try:
        docs = await db[LEDGER_COLLECTION].find(
            {"user_id": user.id}, {"_id": 0, "user_id": 0}
        ).sort("ts", -1).limit(min(limit, 50)).to_list(50)
        for d in docs:
            if hasattr(d.get("ts"), "isoformat"):
                d["ts"] = d["ts"].isoformat()
        return docs
    except Exception:
        return []


# ── Puzzle Game ───────────────────────────────────────────────────────────────

async def _optional_user_id(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    try:
        from app.security.auth import decode_token
        token = authorization.replace("Bearer ", "").strip()
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        return None


class _PuzzleAnswerBody(BaseModel):
    puzzle_id: str
    answer: str


@router.get("/puzzles/next")
async def puzzles_next(authorization: Optional[str] = Header(None)):
    from app.services.puzzles.engine import next_puzzle
    uid = await _optional_user_id(authorization)
    return await next_puzzle(db, uid)


@router.post("/puzzles/answer")
async def puzzles_answer(body: _PuzzleAnswerBody, authorization: Optional[str] = Header(None)):
    from app.services.puzzles.engine import submit_answer
    uid = await _optional_user_id(authorization)
    return await submit_answer(db, uid, body.puzzle_id, body.answer)


# ── Sovereign Chat (executive only) ──────────────────────────────────────────

class _SovereignChatBody(BaseModel):
    message: str

class _SovereignMemoryBody(BaseModel):
    content: str
    kind: Optional[str] = "fact"


async def _build_sovereign_prompt(db, user_id: str) -> str:
    try:
        from app.services.sovereign.sovereign_memory import load_memory_block
        memory = await load_memory_block(db, user_id)
    except Exception:
        memory = ""
    return (
        "You are The Sovereign — the executive intelligence of the WAI Institute. "
        "You have access to platform memory and speak with full authority on strategy, "
        "governance, and operations. Memory context:\n" + (memory or "No memory yet.")
    )


@router.post("/sovereign/chat")
async def sovereign_chat(body: _SovereignChatBody, user: User = Depends(require_role("executive_admin"))):
    system = await _build_sovereign_prompt(db, user.id)
    try:
        import os, httpx
        key = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
        if not key:
            raise HTTPException(503, "No AI key configured")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 2048,
                      "system": system, "messages": [{"role": "user", "content": body.message}]},
            )
            r.raise_for_status()
            reply = r.json()["content"][0]["text"]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Sovereign AI error")
        raise HTTPException(502, f"Sovereign AI error: {e}")
    try:
        from app.services.sovereign.sovereign_memory import save_memory
        await save_memory(db, user.id, f"Asked: {body.message[:200]}", kind="note")
    except Exception:
        pass
    return {"reply": reply}


@router.get("/sovereign/memory")
async def sovereign_memory_list(user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import load_memory_block
    return {"memory": await load_memory_block(db, user.id)}


@router.post("/sovereign/memory")
async def sovereign_memory_add(body: _SovereignMemoryBody, user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import save_memory
    return {"saved": await save_memory(db, user.id, body.content, kind=body.kind or "fact")}


@router.delete("/sovereign/memory")
async def sovereign_memory_clear(user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import clear_memory
    return {"cleared": await clear_memory(db, user.id)}
