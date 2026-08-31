"""
Persona Management — CRUD for AI personas.

A persona is a row in the `ai_personas` collection:
    {
        persona_id: "director",              # unique slug
        name: "Director",
        system_prompt: "...",                # full markdown/directive text
        priority: 100,                        # execution weight order (lower = higher priority)
        active: true,                         # false = disabled
        allowed_roles: ["admin", "executive_admin"],
        model_override: "claude-3-opus",      # optional model string
        created_by: "user_id",
        updated_at: "ISO datetime"
    }

The router is bound by server.py at startup. All admin actions require
executive_admin or oversight role.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from routers.roles import Role, ROLE_RANK

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["personas"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


# ── Auth ────────────────────────────────────────────────────────────────────

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    full_name: str
    role: Role = "student"
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = None) -> User:
    return await current_user(authorization)


def _require_admin():
    async def dep(user: User = Depends(_dep_current_user)) -> User:
        if user.role not in ("admin", "executive_admin", "oversight"):
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user
    return dep


# ── Models ───────────────────────────────────────────────────────────────────

class PersonaCreate(BaseModel):
    persona_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=128)
    system_prompt: str = Field(..., min_length=1)
    priority: int = Field(default=100, ge=0, le=10000)
    active: bool = True
    allowed_roles: List[str] = ["admin", "executive_admin"]
    model_override: Optional[str] = None


class PersonaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    system_prompt: Optional[str] = Field(None, min_length=1)
    priority: Optional[int] = Field(None, ge=0, le=10000)
    active: Optional[bool] = None
    allowed_roles: Optional[List[str]] = None
    model_override: Optional[str] = None


class PersonaPriorityUpdate(BaseModel):
    priority: int = Field(..., ge=0, le=10000)


class PersonaOut(BaseModel):
    persona_id: str
    name: str
    system_prompt: str
    priority: int
    active: bool
    allowed_roles: List[str]
    model_override: Optional[str]
    created_by: str
    updated_at: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _doc_to_out(doc: dict) -> PersonaOut:
    return PersonaOut(
        persona_id=doc.get("persona_id", ""),
        name=doc.get("name", ""),
        system_prompt=doc.get("system_prompt", ""),
        priority=doc.get("priority", 100),
        active=doc.get("active", True),
        allowed_roles=doc.get("allowed_roles", []),
        model_override=doc.get("model_override"),
        created_by=doc.get("created_by", ""),
        updated_at=doc.get("updated_at", ""),
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/admin/personas")
async def list_personas(user: User = Depends(_require_admin())):
    """Fetch all system personas. Admin/exec only.

    Path is /admin/personas (not /personas) to avoid shadowing the public
    persona roster at GET /personas defined in routers/ai.py. The two
    endpoints serve different audiences — this returns full configs
    (system_prompt, priority, active), the other returns public metadata only.
    """
    docs = await db.ai_personas.find({}, {"_id": 0}).sort("priority", 1).to_list(length=500)
    return [_doc_to_out(d).model_dump() for d in docs]


@router.post("/personas")
async def create_persona(body: PersonaCreate, user: User = Depends(_require_admin())):
    """Create a new persona with custom system prompt and priority."""
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "persona_id": body.persona_id,
        "name": body.name,
        "system_prompt": body.system_prompt,
        "priority": body.priority,
        "active": body.active,
        "allowed_roles": body.allowed_roles,
        "model_override": body.model_override,
        "created_by": user.id,
        "updated_at": now,
    }
    try:
        await db.ai_personas.insert_one(doc)
    except Exception as e:
        raise HTTPException(409, f"Persona '{body.persona_id}' already exists or insert failed: {e}")

    await audit(user.id, "persona.created", target=body.persona_id, meta={"name": body.name})
    return _doc_to_out(doc).model_dump()


@router.put("/personas/{persona_id}")
async def update_persona(persona_id: str, body: PersonaUpdate, user: User = Depends(_require_admin())):
    """Update name, system prompt, active state, or priority."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nothing to update.")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.ai_personas.update_one({"persona_id": persona_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Persona not found.")

    await audit(user.id, "persona.updated", target=persona_id, meta=updates)
    doc = await db.ai_personas.find_one({"persona_id": persona_id}, {"_id": 0})
    return _doc_to_out(doc).model_dump()


@router.put("/personas/{persona_id}/priority")
async def update_priority(persona_id: str, body: PersonaPriorityUpdate, user: User = Depends(_require_admin())):
    """Reorder execution priority weight."""
    result = await db.ai_personas.update_one(
        {"persona_id": persona_id},
        {"$set": {"priority": body.priority, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Persona not found.")

    await audit(user.id, "persona.priority", target=persona_id, meta={"priority": body.priority})
    return {"ok": True, "persona_id": persona_id, "priority": body.priority}


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str, user: User = Depends(_require_admin())):
    """Soft-delete a persona (archive by setting active=false)."""
    result = await db.ai_personas.update_one(
        {"persona_id": persona_id},
        {"$set": {"active": False, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Persona not found.")

    await audit(user.id, "persona.deleted", target=persona_id)
    return {"ok": True, "persona_id": persona_id, "active": False}


@router.get("/personas/stack")
async def get_active_persona_stack(user: User = Depends(_require_admin())):
    """Return active personas sorted by priority (execution stack order)."""
    docs = await db.ai_personas.find({"active": True}).sort("priority", 1).to_list(length=100)
    return [_doc_to_out(d).model_dump() for d in docs]
