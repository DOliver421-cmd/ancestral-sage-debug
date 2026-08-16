"""
Sovereign (NAM Oshun Revenue Engine) — file upload, exec chat with memory, puzzle/points game, partnership tiers and ledger.

Extracted verbatim from backend/server.py (monolith refactor, slice 11).
Shared state (db, current_user) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field
import jwt

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["sovereign", "puzzles", "partnership"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
JWT_SECRET = None
JWT_ALGO = "HS256"


def bind(_db, _current_user, _jwt_secret, _jwt_algo):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, JWT_SECRET, JWT_ALGO
    db = _db
    current_user = _current_user
    JWT_SECRET = _jwt_secret
    JWT_ALGO = _jwt_algo


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


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


# ═════════════════════════════════════════════════════════════════════════════
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.post("/sovereign/upload")
async def sovereign_upload_file(
    file: UploadFile = File(...),
    user: User = Depends(_require_rank("executive_admin")),
):
    """Accept a file upload for The Sovereign — PDF, TXT, images, MP3.
    Stored in MongoDB with 24-hour TTL. Returns file_id for use in chat.
    Registered unconditionally so it is never gated by optional imports.
    """
    import os as _os
    MAX_SIZE = 10 * 1024 * 1024
    # Read with cap — avoids loading a multi-GB malicious file into memory
    raw = await file.read(MAX_SIZE + 1)
    if len(raw) > MAX_SIZE:
        raise HTTPException(413, "File too large. Maximum 10 MB.")

    file_id = str(uuid.uuid4())
    filename = file.filename or "upload"
    filename = _os.path.basename(filename)
    filename = "".join(c for c in filename if c.isalnum() or c in ".-_ ")
    filename = filename.strip() or "upload"
    ct = file.content_type or "application/octet-stream"

    is_audio = ct.startswith("audio/") or filename.lower().endswith(".mp3")
    content = ""
    audio_b64 = ""
    is_binary = False

    if is_audio:
        import base64 as _b64
        audio_b64 = _b64.b64encode(raw).decode("utf-8")
        is_binary = True
    else:
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            import base64 as _b64
            content = _b64.b64encode(raw).decode("utf-8")
            is_binary = True

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.sovereign_uploads.insert_one({
        "id": file_id, "user_id": user.id, "filename": filename,
        "content_type": ct, "content": content, "audio_b64": audio_b64,
        "is_binary": is_binary, "is_audio": is_audio, "expires_at": expires_at,
    })
    return {"file_id": file_id, "filename": filename, "is_audio": is_audio, "content_type": ct}


try:
    from sovereign.sovereign_loader import build_sovereign_prompt as _build_sovereign_prompt
    from sovereign import sovereign_memory as _sovereign_memory
    from partnership import points as _partnership_points
    from puzzles import engine as _puzzle_engine

    async def _optional_user_id(authorization: Optional[str]):
        """Return the user id from a valid Bearer token, else None (never raises).
        Lets puzzles be viewed/attempted anonymously while points require login."""
        if not authorization or not authorization.startswith("Bearer "):
            return None
        try:
            payload = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGO])
            return payload.get("sub")
        except Exception:
            return None

    class _SovereignChatBody(BaseModel):
        message: str
        session_id: Optional[str] = "default"

    class _SovereignMemoryBody(BaseModel):
        content: str
        kind: Optional[str] = "fact"

    class _PuzzleAnswerBody(BaseModel):
        puzzle_id: str
        answer: str

    @router.post("/sovereign/chat")
    async def sovereign_chat(body: _SovereignChatBody, user: User = Depends(_require_rank("executive_admin"))):
        """Talk to The Sovereign — executive-only, Director-supervised, memory-aware.
        If a drift lockout is active, Sovereign declines new tasks and holds existing work.
        """
        # ── Drift lockout gate ────────────────────────────────────────────────
        lockout_doc = await db.platform_config.find_one({"key": "sovereign_drift_lockout"}, {"_id": 0})
        if lockout_doc and lockout_doc.get("value") is True:
            lockout_reason = lockout_doc.get("reason", "behavioral drift detected")
            return {
                "reply": (
                    f"D. Oliver — I have to be straight with you.\n\n"
                    f"The Sentinel has flagged a drift lockout on me ({lockout_reason}). "
                    f"That means I am not taking on new tasks right now. "
                    f"The Director and Ancestral Sage are watching this — this is the protocol working as designed.\n\n"
                    f"What I am doing: holding and maximizing everything already in motion. "
                    f"Your existing pipeline, active bookings, and open work continue — I am not standing down from those.\n\n"
                    f"What needs to happen: re-alignment. Once the Sentinel clears the lockout, "
                    f"I am back at full capacity. You can clear it manually from the Sentinel Reversals panel "
                    f"if this flag was set in error.\n\n"
                    f"— The Sovereign"
                ),
                "drift_lockout": True,
            }

        system = await _build_sovereign_prompt(db, user.id)
        reply = ""
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=system, messages=[{"role": "user", "content": body.message}], max_tokens=2048, persona_label="sovereign")
            if _gw.get("provider") != "kb_fallback":
                reply = _gw.get("text", "")
        except Exception as e:
            logger.exception("Sovereign AI error")

        if not reply:
            reply = (
                "The Sovereign is present — but operating without AI connectivity right now. "
                "Your session and memory are intact. "
                "Add a GROQ_API_KEY or GEMINI_API_KEY to Railway and he will speak fully. "
                "— The Sovereign"
            )

        try:
            await _sovereign_memory.save_memory(db, user.id, f"Asked: {body.message[:200]}", kind="note")
        except Exception:
            pass
        return {"reply": reply}

    @router.get("/sovereign/memory")
    async def sovereign_memory_list(user: User = Depends(_require_rank("executive_admin"))):
        return {"memory": await _sovereign_memory.load_memory_block(db, user.id)}

    @router.post("/sovereign/memory")
    async def sovereign_memory_add(body: _SovereignMemoryBody, user: User = Depends(_require_rank("executive_admin"))):
        return {"saved": await _sovereign_memory.save_memory(db, user.id, body.content, kind=body.kind or "fact")}

    @router.delete("/sovereign/memory")
    async def sovereign_memory_clear(user: User = Depends(_require_rank("executive_admin"))):
        return {"cleared": await _sovereign_memory.clear_memory(db, user.id)}

    @router.get("/puzzles/next")
    async def puzzles_next(authorization: Optional[str] = Header(None)):
        """Get the next puzzle. Public to view; points require login."""
        uid = await _optional_user_id(authorization)
        return await _puzzle_engine.next_puzzle(db, uid)

    @router.post("/puzzles/answer")
    async def puzzles_answer(body: _PuzzleAnswerBody, authorization: Optional[str] = Header(None)):
        """Submit an answer. Correct + logged-in => partnership points awarded once."""
        uid = await _optional_user_id(authorization)
        return await _puzzle_engine.submit_answer(db, uid, body.puzzle_id, body.answer)

    @router.get("/partnership/status")
    async def partnership_status(user: User = Depends(_dep_current_user)):
        """Current member's partnership points + membership tier."""
        return await _partnership_points.get_status(db, user.id)

    @router.get("/partnership/ledger")
    async def partnership_ledger(limit: int = 20, user: User = Depends(_dep_current_user)):
        """Recent point-award history for the current user."""
        try:
            from partnership.points import LEDGER_COLLECTION
            docs = await db[LEDGER_COLLECTION].find(
                {"user_id": user.id},
                {"_id": 0, "user_id": 0},
            ).sort("ts", -1).limit(min(limit, 50)).to_list(50)
            for d in docs:
                if hasattr(d.get("ts"), "isoformat"):
                    d["ts"] = d["ts"].isoformat()
            return docs
        except Exception:
            return []

    logger.info("Sovereign + puzzle/points endpoints registered")
except Exception as _sov_err:
    logger.warning(f"Could not register Sovereign/puzzle endpoints: {_sov_err}")
