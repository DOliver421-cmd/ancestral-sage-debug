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
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

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


# ── PROJECTS (/projects*) ─────────────────────────────────────────────────────

def _now() -> str:
    """ISO timestamp for project records and agenda items."""
    return datetime.now(timezone.utc).isoformat()


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
    now = _now()
    doc = {
        "project_id": pid,
        "owner_id": user.id,
        "owner_name": (body.get("owner") or user.full_name or "").strip(),
        "owner": (body.get("owner") or user.full_name or "").strip(),
        "title": (body.get("title") or "Untitled Project").strip(),
        "description": (body.get("description") or "").strip(),
        "status": body.get("status", "active"),
        "priority": body.get("priority", "normal"),
        "due_date": body.get("due_date"),
        "visibility": body.get("visibility", "private"),
        "tags": body.get("tags", []),
        "collaborators": [],
        "milestones": [],
        "created_at": now,
        "updated_at": now,
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "project_created", target=pid, meta={"title": doc["title"]})

    # ── Auto-agenda: every new project becomes a pending Business Agenda item ──
    # so it is guaranteed a place on the office's agenda — no manual step.
    try:
        await db.business_agenda.insert_one({
            "item_id": "agenda_" + uuid.uuid4().hex[:10],
            "source": "project",
            "project_id": pid,
            "title": doc["title"],
            "owner": doc["owner"],
            "priority": doc["priority"],
            "due_date": doc.get("due_date"),
            "status": "pending",
            "created_at": now,
        })
        await audit(user.id, "project_auto_agenda", target=pid, meta={"item": "pending", "title": doc["title"]})
    except Exception as _ae:
        logger.warning("projects: agenda auto-item failed for %s: %s", pid, _ae)

    return doc

@router.patch("/projects/{project_id}")
async def update_project(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.projects.find_one({"project_id": project_id})
    if not doc:
        raise HTTPException(404, "Project not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "status", "visibility", "tags", "milestones", "priority", "due_date", "owner"}
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
    await audit(user.id, "project_deleted", target=project_id)
    # Clean up any pending agenda item tied to the deleted project.
    try:
        await db.business_agenda.delete_many({"project_id": project_id})
    except Exception:
        pass
    return {"deleted": True}
