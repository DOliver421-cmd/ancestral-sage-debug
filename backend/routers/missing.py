"""
missing — Missing Kameron — case photos, tips, file serving.

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
router = APIRouter(tags=['missing'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None


def bind(_db, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user
    
    db = _db
    current_user = _current_user


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "priority_member": 2, "instructor": 2, "creative_partner": 2, "site_support": 3, "admin": 3, "executive_admin": 4}
Role = Literal["student", "priority_member", "instructor", "creative_partner", "site_support", "admin", "executive_admin"]


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


# ── MISSING KAMERON (/missing/*) ─────────────────────────────────────────────

_KAMERON_CASE_ID = "kameron-mcmullen"

@router.get("/missing/photos/{case_id}")
async def get_missing_photos(case_id: str):
    photos = await db.missing_photos.find({"case_id": case_id}, {"_id": 0}).sort("uploaded_at", -1).to_list(100)
    return {"photos": photos, "case_id": case_id}

@router.post("/missing/photo")
async def upload_missing_photo(
    file: UploadFile = File(...),
    case_id: str = Form(default=_KAMERON_CASE_ID),
    user: User = Depends(_dep_current_user),
):
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20MB)")
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    import uuid
    bucket = AsyncIOMotorGridFSBucket(db)
    gfs_id = await bucket.upload_from_stream(file.filename, contents, metadata={"content_type": file.content_type, "case_id": case_id})
    photo_url = f"/api/missing/file/{gfs_id}"
    doc = {
        "id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "photo_url": photo_url,
        "filename": file.filename,
        "uploaded_by": user.id,
        "uploaded_at": _now(),
    }
    await db.missing_photos.insert_one(doc)
    doc.pop("_id", None)
    return doc

@router.post("/missing/tip")
async def submit_missing_tip(body: dict):
    name = (body.get("name") or "").strip()
    tip_text = (body.get("tip") or "").strip()
    contact = (body.get("contact") or "").strip()
    case_id = body.get("case_id", _KAMERON_CASE_ID)
    if not tip_text:
        raise HTTPException(400, "Tip content is required")
    import uuid
    doc = {
        "id": str(uuid.uuid4())[:8],
        "case_id": case_id,
        "case_name": name,
        "tip": tip_text,
        "contact": contact,
        "submitted_at": _now(),
        "reviewed": False,
    }
    await db.missing_tips.insert_one(doc)
    doc.pop("_id", None)
    logger.info("MISSING TIP submitted for case %s", case_id)
    return {"submitted": True, "id": doc["id"], "message": "Thank you. Your tip has been submitted anonymously and will be reviewed."}

@router.get("/missing/file/{file_id}")
async def get_missing_file(file_id: str):
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    from fastapi.responses import StreamingResponse
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        stream = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")
    async def iter_file():
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            yield chunk
    return StreamingResponse(iter_file(), media_type=stream.metadata.get("content_type", "image/jpeg"))
