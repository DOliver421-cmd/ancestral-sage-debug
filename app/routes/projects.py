"""app/routes/projects.py — Project dashboard management.

All five leads (Jamil + AXIOM/CIPHER/MAVEN/SAGE) can read and update projects.
Jamil acts as assistant project manager — context-injected on every chat.

Collections:
  projects         — master project registry (metadata, milestones, status)
  competition_rounds — Arena task results (already exists)

Endpoints:
  GET    /projects                     — list all projects
  POST   /projects                     — create project
  GET    /projects/{project_id}        — get single project with full history
  PATCH  /projects/{project_id}        — update metadata / status / notes
  POST   /projects/{project_id}/milestone     — add milestone
  PATCH  /projects/{project_id}/milestone/{i} — update milestone
  DELETE /projects/{project_id}        — archive project
  GET    /projects/context/jamil       — projects formatted for Jamil's LLM context
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user

logger = logging.getLogger("lcewai")
router = APIRouter()

_STATUS_OPTIONS = {"active", "in_review", "blocked", "complete", "archived"}


# ── Pydantic models ───────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    owner: Optional[str] = ""         # team member name responsible
    priority: Optional[str] = "normal"  # low / normal / high / critical
    tags: Optional[List[str]] = []
    due_date: Optional[str] = None    # ISO date string


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None       # freeform PM notes


class MilestoneCreate(BaseModel):
    title: str
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None  # persona name or "Jamil"


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    complete: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_project(project_id: str) -> dict:
    doc = await db.projects.find_one({"project_id": project_id, "archived": {"$ne": True}})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found.")
    return doc


async def _enrich(doc: dict) -> dict:
    """Attach Arena round summary to a project doc."""
    pid = doc["project_id"]
    rounds = await db.competition_rounds.find(
        {"project_id": pid},
        {"_id": 0, "round_number": 1, "persona": 1, "task": 1,
         "commissioner_score": 1, "average_score": 1, "commissioner_verdict": 1, "timestamp": 1}
    ).sort("round_number", 1).to_list(length=200)

    # Group by round
    round_map: dict = {}
    for r in rounds:
        rn = r["round_number"]
        round_map.setdefault(rn, {"round": rn, "task": r.get("task", ""), "results": []})
        round_map[rn]["results"].append({
            "persona": r["persona"],
            "score": r.get("average_score") or r.get("commissioner_score", 0),
            "verdict": r.get("commissioner_verdict", ""),
        })

    doc["arena_rounds"] = list(round_map.values())
    doc["total_arena_rounds"] = len(round_map)
    doc.pop("_id", None)
    return doc


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects(user: User = Depends(current_user)):
    docs = await db.projects.find(
        {"archived": {"$ne": True}},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(length=200)
    return {"projects": docs}


@router.post("/projects", status_code=201)
async def create_project(body: ProjectCreate, user: User = Depends(current_user)):
    project_id = str(uuid.uuid4())
    now = _now()
    doc = {
        "project_id": project_id,
        "title": body.title.strip(),
        "description": body.description or "",
        "status": "active",
        "priority": body.priority or "normal",
        "owner": body.owner or "",
        "tags": body.tags or [],
        "due_date": body.due_date,
        "notes": "",
        "milestones": [],
        "created_by": str(getattr(user, "id", "") or getattr(user, "_id", "")),
        "created_at": now,
        "updated_at": now,
        "archived": False,
    }
    await db.projects.insert_one(doc)
    doc.pop("_id", None)
    logger.info("Project created: %s — %s", project_id, body.title)
    return doc


@router.get("/projects/context/jamil")
async def jamil_project_context(user: User = Depends(current_user)):
    """Returns active projects formatted as a plain-text context block for Jamil."""
    docs = await db.projects.find(
        {"status": {"$ne": "archived"}, "archived": {"$ne": True}},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(length=50)

    if not docs:
        return {"context": "No active projects at this time."}

    lines = ["ACTIVE PROJECTS — " + _now()[:10], ""]
    for d in docs:
        lines.append(f"PROJECT: {d['title']} [{d['status'].upper()}] priority={d['priority']}")
        lines.append(f"  ID: {d['project_id']}")
        if d.get("owner"):
            lines.append(f"  Owner: {d['owner']}")
        if d.get("due_date"):
            lines.append(f"  Due: {d['due_date']}")
        if d.get("description"):
            lines.append(f"  Description: {d['description']}")
        if d.get("notes"):
            lines.append(f"  PM Notes: {d['notes']}")
        milestones = d.get("milestones", [])
        if milestones:
            done = sum(1 for m in milestones if m.get("complete"))
            lines.append(f"  Milestones: {done}/{len(milestones)} complete")
            for m in milestones:
                mark = "✓" if m.get("complete") else "○"
                lines.append(f"    {mark} {m['title']}" + (f" (due {m['due_date']})" if m.get("due_date") else ""))
        lines.append("")

    return {"context": "\n".join(lines)}


@router.get("/projects/{project_id}")
async def get_project(project_id: str, user: User = Depends(current_user)):
    doc = await _get_project(project_id)
    return await _enrich(doc)


@router.patch("/projects/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate, user: User = Depends(current_user)):
    doc = await _get_project(project_id)

    if body.status and body.status not in _STATUS_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(_STATUS_OPTIONS)}")

    updates: dict = {"updated_at": _now()}
    for field in ("title", "description", "status", "owner", "priority", "tags", "due_date", "notes"):
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val

    await db.projects.update_one({"project_id": project_id}, {"$set": updates})
    updated = await _get_project(project_id)
    updated.pop("_id", None)
    return updated


@router.post("/projects/{project_id}/milestone", status_code=201)
async def add_milestone(project_id: str, body: MilestoneCreate, user: User = Depends(current_user)):
    await _get_project(project_id)
    milestone = {
        "id": str(uuid.uuid4()),
        "title": body.title.strip(),
        "due_date": body.due_date,
        "assigned_to": body.assigned_to or "",
        "complete": False,
        "created_at": _now(),
    }
    await db.projects.update_one(
        {"project_id": project_id},
        {"$push": {"milestones": milestone}, "$set": {"updated_at": _now()}}
    )
    return {"milestone": milestone}


@router.patch("/projects/{project_id}/milestone/{milestone_id}")
async def update_milestone(
    project_id: str,
    milestone_id: str,
    body: MilestoneUpdate,
    user: User = Depends(current_user),
):
    doc = await _get_project(project_id)
    milestones = doc.get("milestones", [])
    idx = next((i for i, m in enumerate(milestones) if m.get("id") == milestone_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Milestone not found.")

    for field in ("title", "due_date", "assigned_to", "complete"):
        val = getattr(body, field, None)
        if val is not None:
            milestones[idx][field] = val

    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {"milestones": milestones, "updated_at": _now()}}
    )
    return {"milestone": milestones[idx]}


@router.delete("/projects/{project_id}")
async def archive_project(project_id: str, user: User = Depends(current_user)):
    await _get_project(project_id)
    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {"archived": True, "status": "archived", "updated_at": _now()}}
    )
    return {"archived": True, "project_id": project_id}
