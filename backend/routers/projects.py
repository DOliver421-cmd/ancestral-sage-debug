"""
projects — Projects — CRUD, milestones.

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
router = APIRouter(tags=['projects'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit
    
    db = _db
    current_user = _current_user
    audit = _audit


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
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


# ── PROJECTS (/projects*) ─────────────────────────────────────────────────────

def _new_project_id():
    import uuid
    return "proj_" + str(uuid.uuid4())[:8]

@router.get("/projects")
async def list_projects(user: User = Depends(_dep_current_user)):
    docs = await db.projects.find(
        {"$or": [{"owner_id": user.id}, {"collaborators": user.id}, {"visibility": "public"}]},
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    return docs

@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("visibility") != "public" and doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    return doc

@router.post("/projects")
async def create_project(body: dict, user: User = Depends(_dep_current_user)):
    pid = _new_project_id()
    doc = {
        "project_id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": (body.get("title") or "Untitled Project").strip(),
        "description": (body.get("description") or "").strip(),
        "status": body.get("status", "active"),
        "visibility": body.get("visibility", "private"),
        "tags": body.get("tags", []),
        "collaborators": [],
        "milestones": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    await audit(db, user.id, "project_created", {"project_id": pid, "title": doc["title"]})
    return doc

@router.patch("/projects/{project_id}")
async def update_project(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "status", "visibility", "tags", "milestones"}
    updates = {k: v for k, v in body.items() if k in allowed}
    updates["updated_at"] = _now()
    await db.projects.update_one({"project_id": project_id}, {"$set": updates})
    doc.update(updates)
    doc.pop("_id", None)
    return doc

@router.post("/projects/{project_id}/milestone")
async def add_milestone(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    import uuid
    milestone = {
        "milestone_id": str(uuid.uuid4())[:8],
        "title": (body.get("title") or "").strip(),
        "due_date": body.get("due_date"),
        "completed": False,
        "created_at": _now(),
    }
    await db.projects.update_one({"project_id": project_id}, {"$push": {"milestones": milestone}, "$set": {"updated_at": _now()}})
    return milestone

@router.patch("/projects/{project_id}/milestone/{milestone_id}")
async def update_milestone(project_id: str, milestone_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and user.id not in doc.get("collaborators", []):
        raise HTTPException(403, "Access denied")
    milestones = doc.get("milestones", [])
    for m in milestones:
        if m.get("milestone_id") == milestone_id:
            m.update({k: v for k, v in body.items() if k in {"title", "due_date", "completed"}})
    await db.projects.update_one({"project_id": project_id}, {"$set": {"milestones": milestones, "updated_at": _now()}})
    return {"updated": True}

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can delete")
    await db.projects.delete_one({"project_id": project_id})
    await audit(db, user.id, "project_deleted", {"project_id": project_id})
    return {"deleted": True}
