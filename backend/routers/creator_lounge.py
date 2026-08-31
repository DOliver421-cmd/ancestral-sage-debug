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


# ════════════════════════════════════════════════════════════════════════════
# /my-projects — "Have your M.O.R.E. team work on it."
# A member-owned project lifecycle: intake → assign → execute → review →
# operate → deliver. The owner reviews every deliverable before it counts.
# Storage: db.my_projects. Collection is separate from cl_projects (creator
# lounge collabs) on purpose — different shape, different lifecycle.
# ════════════════════════════════════════════════════════════════════════════

_MY_PROJECT_STAGES = ["intake", "assign", "execute", "review", "operate", "deliver"]
_MY_PROJECT_DAILY_RUN_LIMIT = 5


def _my_project_doc(owner_id: str, body: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "title": (body.get("title") or "Untitled project").strip()[:160],
        "brief": (body.get("brief") or "").strip()[:4000],
        "desired_outcome": (body.get("desired_outcome") or "").strip()[:2000],
        "category": (body.get("category") or "launch").strip()[:60],
        "priority": (body.get("priority") or "normal").strip()[:20],
        "current_stage": "intake",
        "deliverables": [],
        "comments": [],
        "archived": False,
        "created_at": now,
        "updated_at": now,
    }


async def _my_project(project_id: str) -> Optional[dict]:
    return await db.my_projects.find_one({"id": project_id}, {"_id": 0})


async def _my_owned_project(project_id: str, user: User) -> dict:
    proj = await _my_project(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    is_staff = getattr(user, "role", None) in ("admin", "executive_admin")
    if proj.get("owner_id") != user.id and not is_staff:
        raise HTTPException(403, "You don't own this project")
    return proj


async def _my_summary(user_id: str) -> dict:
    all_docs = await db.my_projects.find({"owner_id": user_id}, {"_id": 0}).to_list(200)
    active = [p for p in all_docs if not p.get("archived")]
    pending = [p for p in all_docs if any(
        d.get("approval_status") == "pending" for d in p.get("deliverables", [])
    )]
    # Runs today against the daily limit (best-effort, in-memory per request).
    today = datetime.now(timezone.utc).isoformat()[:10]
    runs_today = sum(
        1 for p in all_docs
        for d in p.get("deliverables", [])
        if (d.get("submitted_at") or "").startswith(today)
    )
    return {
        "active": len(active),
        "pending_reviews": len(pending),
        "daily_runs_left": max(0, _MY_PROJECT_DAILY_RUN_LIMIT - runs_today),
        "daily_run_limit": _MY_PROJECT_DAILY_RUN_LIMIT,
    }


@router.get("/my-projects")
async def my_projects_list(user: User = Depends(_dep_current_user)):
    cursor = db.my_projects.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(100)
    projects = await cursor.to_list(100)
    return {"projects": projects, "summary": await _my_summary(user.id)}


@router.post("/my-projects")
async def my_projects_create(body: dict, user: User = Depends(_dep_current_user)):
    doc = _my_project_doc(user.id, body)
    await db.my_projects.insert_one(doc)
    return doc


@router.get("/my-projects/{project_id}")
async def my_projects_detail(project_id: str, user: User = Depends(_dep_current_user)):
    return await _my_owned_project(project_id, user)


@router.post("/my-projects/{project_id}/run-stage")
async def my_projects_run_stage(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    proj = await _my_owned_project(project_id, user)
    if proj.get("archived"):
        raise HTTPException(400, "Archived projects can't be run")
    persona = (body.get("persona") or "Production").strip()[:60]
    instructions = (body.get("instructions") or "").strip()[:4000]
    stage = proj.get("current_stage", "intake")
    now = datetime.now(timezone.utc).isoformat()
    title = instructions.split("\n")[0][:80] if instructions else f"{persona} work item"
    deliverable = {
        "id": str(uuid.uuid4()),
        "title": title or f"{persona} work item",
        "content": "",
        "stage": stage,
        "persona": persona,
        "instructions": instructions,
        "approval_status": "pending",
        "submitted_at": now,
        "metadata": {"auto": True},
    }
    await db.my_projects.update_one(
        {"id": project_id},
        {"$push": {"deliverables": deliverable}, "$set": {"updated_at": now}},
    )
    await audit(user.id, "my_project.run_stage", target=project_id, meta={"stage": stage, "persona": persona})
    return await _my_owned_project(project_id, user.id)


@router.post("/my-projects/{project_id}/approve")
async def my_projects_decide(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    proj = await _my_owned_project(project_id, user)
    action = body.get("action")
    status_map = {"approve": "approved", "reject": "rejected", "request_revision": "revision_requested"}
    if action not in status_map:
        raise HTTPException(400, "action must be approve, reject, or request_revision")
    new_status = status_map[action]
    notes = (body.get("notes") or "").strip()[:2000]
    now = datetime.now(timezone.utc).isoformat()
    # Apply the decision to every pending deliverable (the UI decides per
    # project, not per item).
    pending = [d for d in proj.get("deliverables", []) if d.get("approval_status") == "pending"]
    if not pending:
        raise HTTPException(400, "Nothing is awaiting your review")
    for d in pending:
        await db.my_projects.update_one(
            {"id": project_id, "deliverables.id": d["id"]},
            {"$set": {
                "deliverables.$.approval_status": new_status,
                "deliverables.$.reviewed_at": now,
                "deliverables.$.review_notes": notes,
            }},
        )
    await db.my_projects.update_one({"id": project_id}, {"$set": {"updated_at": now}})
    await audit(user.id, "my_project.review", target=project_id, meta={"action": action, "items": len(pending)})
    return {"status": new_status, "reviewed": len(pending)}


@router.post("/my-projects/{project_id}/advance")
async def my_projects_advance(project_id: str, user: User = Depends(_dep_current_user)):
    proj = await _my_owned_project(project_id, user)
    if proj.get("archived"):
        raise HTTPException(400, "Archived projects can't be advanced")
    idx = _MY_PROJECT_STAGES.index(proj.get("current_stage")) if proj.get("current_stage") in _MY_PROJECT_STAGES else 0
    next_stage = _MY_PROJECT_STAGES[min(idx + 1, len(_MY_PROJECT_STAGES) - 1)]
    now = datetime.now(timezone.utc).isoformat()
    await db.my_projects.update_one(
        {"id": project_id},
        {"$set": {"current_stage": next_stage, "updated_at": now}},
    )
    return {"ok": True, "current_stage": next_stage}


@router.post("/my-projects/{project_id}/archive")
async def my_projects_archive(project_id: str, user: User = Depends(_dep_current_user)):
    await _my_owned_project(project_id, user)
    now = datetime.now(timezone.utc).isoformat()
    await db.my_projects.update_one(
        {"id": project_id},
        {"$set": {"archived": True, "updated_at": now}},
    )
    return {"ok": True, "archived": True}


@router.post("/my-projects/{project_id}/comments")
async def my_projects_comment(project_id: str, body: dict, user: User = Depends(_dep_current_user)):
    proj = await _my_owned_project(project_id, user)
    text = (body.get("text") or "").strip()[:2000]
    if not text:
        raise HTTPException(400, "text is required")
    now = datetime.now(timezone.utc).isoformat()
    comment = {
        "id": str(uuid.uuid4()),
        "text": text,
        "user_id": user.id,
        "user_name": getattr(user, "full_name", None) or user.email,
        "created_at": now,
    }
    await db.my_projects.update_one(
        {"id": project_id},
        {"$push": {"comments": comment}, "$set": {"updated_at": now}},
    )
    return {"ok": True, "comment": comment}
