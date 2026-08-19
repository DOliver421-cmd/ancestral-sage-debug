"""
creator_lounge — Creator Lounge — collaboration projects, collabs.

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
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['creator-lounge'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
notify = None


def bind(_db, _current_user, _audit, _notify):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, notify
    
    db = _db
    current_user = _current_user
    audit = _audit
    notify = _notify


# Mirrors server.py's role hierarchy for runtime require_role checks.
# ROLE_RANK imported from roles.py
# Role imported from roles.py


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


# ═══════════════════════════════════════════════════════════════════════════════
#  CREATOR LOUNGE  —  /api/creator-lounge/*
#  Collaboration space for creators: projects, collabs, resource sharing.
# ═══════════════════════════════════════════════════════════════════════════════

class _CLProjectReq(BaseModel):
    title:       str   = Field(..., min_length=1, max_length=200)
    description: str   = Field("", max_length=2000)
    genre:       str   = Field("", max_length=100)
    looking_for: List[str] = []  # e.g. ["vocalist", "mixing engineer"]
    open:        bool  = True

class _CLCollab(BaseModel):
    project_id: str
    message:    str = Field("", max_length=500)

@router.get("/creator-lounge/projects")
async def cl_list_projects(
    genre: Optional[str] = None, open_only: bool = True,
    limit: int = 30, offset: int = 0,
    user: User = Depends(_dep_current_user)
):
    q: dict = {}
    if open_only: q["open"] = True
    if genre:     q["genre"] = {"$regex": genre, "$options": "i"}
    total  = await db.cl_projects.count_documents(q)
    cursor = db.cl_projects.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(min(limit, 50))
    items  = await cursor.to_list(min(limit, 50))
    return {"total": total, "projects": items}

@router.post("/creator-lounge/projects")
async def cl_create_project(body: _CLProjectReq, user: User = Depends(_dep_current_user)):
    doc = {
        "id":          str(uuid.uuid4()),
        "owner_id":    user.id,
        "owner_name":  getattr(user, "full_name", None) or getattr(user, "email", ""),
        "title":       body.title,
        "description": body.description,
        "genre":       body.genre,
        "looking_for": body.looking_for,
        "open":        body.open,
        "collabs":     [],
        "created_at":  datetime.now(timezone.utc).isoformat(),
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }
    await db.cl_projects.insert_one({**doc, "_id": doc["id"]})
    await audit(user.id, "creator_lounge.project.created", target=doc["id"])
    return doc

@router.patch("/creator-lounge/projects/{project_id}")
async def cl_update_project(project_id: str, body: _CLProjectReq, user: User = Depends(_dep_current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if proj["owner_id"] != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Not your project")
    await db.cl_projects.update_one({"id": project_id}, {"$set": {
        **body.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    return {"ok": True}

@router.delete("/creator-lounge/projects/{project_id}")
async def cl_delete_project(project_id: str, user: User = Depends(_dep_current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if proj["owner_id"] != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Not your project")
    await db.cl_projects.delete_one({"id": project_id})
    return {"ok": True}

@router.post("/creator-lounge/projects/{project_id}/collab")
async def cl_request_collab(project_id: str, body: _CLCollab, user: User = Depends(_dep_current_user)):
    proj = await db.cl_projects.find_one({"id": project_id}, {"_id": 0, "owner_id": 1, "open": 1})
    if not proj: raise HTTPException(404, "Project not found")
    if not proj.get("open"): raise HTTPException(400, "This project is not accepting collaborators")
    entry = {"user_id": user.id, "user_name": getattr(user, "full_name", None) or getattr(user, "email", ""),
             "message": body.message, "status": "pending", "requested_at": datetime.now(timezone.utc).isoformat()}
    await db.cl_projects.update_one({"id": project_id}, {"$push": {"collabs": entry}})
    await notify(proj["owner_id"], "New Collaboration Request",
        f"{entry['user_name']} wants to collaborate on your project.", link="/creator-lounge", kind="info")
    return {"ok": True}

@router.get("/creator-lounge/my-projects")
async def cl_my_projects(user: User = Depends(_dep_current_user)):
    cursor = db.cl_projects.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(50)
    return {"projects": await cursor.to_list(50)}
