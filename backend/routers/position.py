"""
position — My Position — member position, history, proceeds preference, step-down/exit flows.

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
router = APIRouter(tags=['me', 'position'])


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


# ── MY POSITION (/me/position*) ───────────────────────────────────────────────

@router.get("/me/position")
async def get_my_position(user: User = Depends(_dep_current_user)):
    u = await db.users.find_one({"id": user.id}, {"_id": 0})
    if not u:
        raise HTTPException(404, "User not found")
    return {
        "id": u["id"],
        "full_name": u.get("full_name", ""),
        "email": u.get("email", ""),
        "role": u.get("role", "student"),
        "feature_tier": u.get("feature_tier", "free"),
        "status": u.get("status", "active"),
        "exit_requested": u.get("exit_requested", False),
        "exit_reason": u.get("exit_reason", ""),
        "exit_requested_at": u.get("exit_requested_at"),
        "more_member": u.get("more_member", False),
    }

@router.get("/me/position/history")
async def get_position_history(user: User = Depends(_dep_current_user)):
    log = await db.audit_log.find(
        {"actor_id": user.id, "action": {"$in": ["role_change", "tier_change", "step_down", "exit_request"]}},
        {"_id": 0}
    ).sort("at", -1).limit(50).to_list(50)
    return {"history": log}

@router.get("/me/proceeds-preference")
async def get_proceeds_preference(user: User = Depends(_dep_current_user)):
    u = await db.users.find_one({"id": user.id}, {"proceeds_preference": 1})
    return {"preference": (u or {}).get("proceeds_preference", "platform")}

@router.post("/me/proceeds-preference")
async def set_proceeds_preference(body: dict, user: User = Depends(_dep_current_user)):
    pref = body.get("preference", "platform")
    if pref not in ("platform", "personal", "split", "donate"):
        raise HTTPException(400, "Invalid preference value")
    await db.users.update_one({"id": user.id}, {"$set": {"proceeds_preference": pref}})
    await audit(db, user.id, "proceeds_preference_set", {"preference": pref})
    return {"preference": pref}

@router.post("/me/step-down")
async def step_down(body: dict, user: User = Depends(_dep_current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    role_rank = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4}
    if role_rank.get(user.role, 1) <= 1:
        raise HTTPException(400, "Already at base role")
    roles = list(role_rank.keys())
    new_role = roles[role_rank.get(user.role, 2) - 2]
    await db.users.update_one({"id": user.id}, {"$set": {"role": new_role}})
    await audit(db, user.id, "step_down", {"from_role": user.role, "to_role": new_role, "reason": reason})
    return {"role": new_role, "message": f"Stepped down to {new_role}"}

@router.post("/me/request-exit")
async def request_exit(body: dict, user: User = Depends(_dep_current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    await db.users.update_one({"id": user.id}, {"$set": {
        "exit_requested": True,
        "exit_reason": reason,
        "exit_requested_at": _now(),
        "exit_type": "standard",
    }})
    await audit(db, user.id, "exit_requested", {"reason": reason})
    return {"exit_requested": True, "message": "Exit request submitted. Account remains active for 30 days."}

@router.post("/me/emergency-exit")
async def emergency_exit(body: dict, user: User = Depends(_dep_current_user)):
    reason = (body.get("reason") or "").strip()
    if not reason:
        raise HTTPException(400, "Reason required")
    await db.users.update_one({"id": user.id}, {"$set": {
        "exit_requested": True,
        "exit_reason": reason,
        "exit_requested_at": _now(),
        "exit_type": "emergency",
        "is_active": False,
    }})
    await audit(db, user.id, "emergency_exit", {"reason": reason})
    return {"exit_requested": True, "message": "Emergency exit initiated. Account suspended pending review."}

@router.post("/me/cancel-exit")
async def cancel_exit(user: User = Depends(_dep_current_user)):
    await db.users.update_one({"id": user.id}, {"$unset": {
        "exit_requested": "", "exit_reason": "", "exit_requested_at": "", "exit_type": ""
    }, "$set": {"is_active": True}})
    await audit(db, user.id, "exit_cancelled", {})
    return {"exit_requested": False, "message": "Exit request cancelled."}

@router.post("/me/leave-more")
async def leave_more(user: User = Depends(_dep_current_user)):
    await db.users.update_one({"id": user.id}, {"$set": {"more_member": False}})
    await audit(db, user.id, "left_more", {})
    return {"more_member": False, "message": "Removed from M.O.R.E. community."}
