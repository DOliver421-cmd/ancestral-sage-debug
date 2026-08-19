"""
revenue — Revenue Division — API keys, credential verification, employer portal, course licensing, sovereign workspaces, resume builder.

Extracted verbatim from backend/server.py (monolith refactor, slice 12).
Shared state (db, current_user, ...) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['revenue', 'api-keys', 'licensing'])


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


# ── API-as-a-Service: Revenue Division ─────────────────────────────────────────

@router.get("/revenue/api-keys")
async def revenue_list_keys(user: User = Depends(_dep_current_user)):
    """List API keys for the current user (hashes only, never raw keys)."""
    from api_keys import list_api_keys
    keys = await list_api_keys(db, user.id)
    return {"keys": keys}


@router.post("/revenue/api-keys")
async def revenue_create_key(body: dict, user: User = Depends(_dep_current_user)):
    """Create a new API key. Body: {"label": "...", "tier": "free|starter|pro|enterprise"}"""
    from api_keys import create_api_key
    label = body.get("label", "").strip()
    tier = body.get("tier", "free")
    if not label:
        raise HTTPException(400, "label is required")
    if tier not in ("free", "starter", "pro", "enterprise"):
        raise HTTPException(400, "tier must be free, starter, pro, or enterprise")
    result = await create_api_key(db, label, tier, user.id)
    await audit(user.id, "revenue.api_key.created", meta={"tier": tier, "label": label})
    return result


@router.delete("/revenue/api-keys/{key_hash}")
async def revenue_revoke_key(key_hash: str, user: User = Depends(_dep_current_user)):
    """Revoke an API key."""
    from api_keys import revoke_api_key
    ok = await revoke_api_key(db, key_hash, user.id)
    if not ok:
        raise HTTPException(404, "Key not found or already revoked")
    await audit(user.id, "revenue.api_key.revoked")
    return {"ok": True}


@router.get("/revenue/api-keys/stats")
async def revenue_key_stats(user: User = Depends(_dep_current_user)):
    """Usage statistics for all keys owned by the current user."""
    from api_keys import get_usage_stats
    stats = await get_usage_stats(db, user.id)
    return stats


@router.get("/revenue/api-keys/tiers")
async def revenue_list_tiers():
    """List available API key tiers and their rate limits."""
    from api_keys import TIERS
    return {"tiers": TIERS}


# ── Credential Verification Employer Portal ────────────────────────────────────

@router.post("/revenue/verify-credential")
async def revenue_verify_credential(body: dict):
    """Public endpoint for employers to verify a candidate credential.
    Body: {"verification_code": "..."} or {"assertion_url": "..."}"""
    code = body.get("verification_code", "")
    if not code:
        raise HTTPException(400, "verification_code is required")
    cred = await db.credentials.find_one(
        {"verification_code": code},
        {"_id": 0, "password_hash": 0},
    )
    if not cred:
        raise HTTPException(404, "Credential not found")
    # Return only what an employer should see
    return {
        "valid": True,
        "credential": cred.get("title", ""),
        "holder": cred.get("holder_name", ""),
        "issued": cred.get("issued_at", ""),
        "expires": cred.get("expires_at", ""),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/revenue/employer/verify-batch")
async def revenue_employer_batch_verify(
    codes: str = "",
    user: User = Depends(_require_rank("instructor")),
):
    """Batch verify multiple credential codes. Instructor+ only.
    Query: ?codes=CODE1,CODE2,CODE3"""
    if not codes:
        raise HTTPException(400, "Provide comma-separated verification codes")
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    results = []
    for code in code_list:
        cred = await db.credentials.find_one(
            {"verification_code": code},
            {"_id": 0, "title": 1, "holder_name": 1, "issued_at": 1, "expires_at": 1},
        )
        results.append({
            "code": code,
            "valid": cred is not None,
            "credential": cred.get("title", "") if cred else None,
            "holder": cred.get("holder_name", "") if cred else None,
        })
    return {"results": results, "total": len(results), "valid": sum(1 for r in results if r["valid"])}


# ── Course Licensing Marketplace ───────────────────────────────────────────────

@router.get("/revenue/courses/public")
async def revenue_public_courses():
    """Public catalog of licensable courses for contractors."""
    modules = await db.modules.find({}, {"_id": 0, "slug": 1, "title": 1, "description": 1,
                                          "hours": 1, "competencies": 1, "price": 1}).to_list(length=50)
    return {"courses": modules}


@router.post("/revenue/courses/license")
async def revenue_license_course(body: dict, user: User = Depends(_dep_current_user)):
    """License a course for a contractor organization.
    Body: {"organization": "...", "course_slugs": ["slug1","slug2"], "seats": 5}"""
    org = body.get("organization", "").strip()
    slugs = body.get("course_slugs", [])
    seats = int(body.get("seats", 1))
    if not org or not slugs:
        raise HTTPException(400, "organization and course_slugs are required")
    if seats < 1 or seats > 1000:
        raise HTTPException(400, "seats must be between 1 and 1000")
    license_id = str(uuid.uuid4())
    await db.course_licenses.insert_one({
        "license_id": license_id,
        "organization": org,
        "course_slugs": slugs,
        "seats": seats,
        "user_id": user.id,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.course.licensed", meta={"org": org, "slugs": slugs, "seats": seats})
    return {"license_id": license_id, "organization": org, "seats": seats}


@router.get("/revenue/courses/my-licenses")
async def revenue_my_licenses(user: User = Depends(_dep_current_user)):
    """List course licenses owned by the current user."""
    licenses = await db.course_licenses.find(
        {"user_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=50)
    return {"licenses": licenses}


# ── Compliance Hour Tracking — Employer Dashboard ─────────────────────────────

@router.get("/revenue/employer/compliance")
async def revenue_employer_compliance(
    associate: str = "",
    user: User = Depends(_require_rank("instructor")),
):
    """Employer/instructor dashboard: compliance hour summary by cohort.
    Query: ?associate=COHORT_NAME for filtering."""
    match = {}
    if associate:
        match["associate"] = associate
    # Aggregate attendance + lab completion as compliance hours
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$user_id",
            "total_hours": {"$sum": "$hours"},
            "lab_count": {"$sum": 1},
            "last_activity": {"$max": "$created_at"},
        }},
        {"$sort": {"total_hours": -1}},
        {"$limit": 100},
    ]
    try:
        attendance = await db.attendance.aggregate(pipeline).to_list(length=100)
    except Exception:
        attendance = []
    total_hours = sum(a.get("total_hours", 0) for a in attendance)
    return {
        "total_apprentices": len(attendance),
        "total_hours": total_hours,
        "average_hours": round(total_hours / len(attendance), 1) if attendance else 0,
        "records": attendance,
        "associate_filter": associate or "all",
    }


# ── Sovereign AI Team Seats ────────────────────────────────────────────────────

@router.post("/revenue/sovereign/workspace")
async def revenue_create_workspace(body: dict, user: User = Depends(_require_rank("admin"))):
    """Create a Sovereign AI workspace for a team. Admin+.
    Body: {"name": "...", "member_ids": ["uid1","uid2"]}"""
    name = body.get("name", "").strip()
    member_ids = body.get("member_ids", [])
    if not name:
        raise HTTPException(400, "workspace name is required")
    ws_id = str(uuid.uuid4())
    await db.sovereign_workspaces.insert_one({
        "workspace_id": ws_id,
        "name": name,
        "owner_id": user.id,
        "member_ids": member_ids,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(user.id, "revenue.sovereign.workspace_created", meta={"name": name, "members": len(member_ids)})
    return {"workspace_id": ws_id, "name": name}


@router.get("/revenue/sovereign/workspaces")
async def revenue_list_workspaces(user: User = Depends(_require_rank("admin"))):
    """List Sovereign workspaces accessible to the current user."""
    workspaces = await db.sovereign_workspaces.find(
        {"$or": [{"owner_id": user.id}, {"member_ids": user.id}]},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=50)
    return {"workspaces": workspaces}


@router.post("/revenue/sovereign/workspace/{ws_id}/chat")
async def revenue_workspace_chat(ws_id: str, body: dict, user: User = Depends(_dep_current_user)):
    """Chat within a Sovereign workspace. All workspace members share context."""
    from bson.objectid import ObjectId
    ws = await db.sovereign_workspaces.find_one({"workspace_id": ws_id})
    if not ws:
        raise HTTPException(404, "Workspace not found")
    if user.id != ws["owner_id"] and user.id not in ws.get("member_ids", []):
        raise HTTPException(403, "Not a member of this workspace")
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(400, "message is required")
    # Load workspace memory (shared across members)
    memory = await db.sovereign_memory.find(
        {"workspace_id": ws_id},
        {"_id": 0},
    ).sort("ts", -1).limit(10).to_list(length=10)
    memory_context = "\n".join(f"[{m.get('actor','')}]: {m.get('content','')}" for m in reversed(memory))
    system_prompt = f"You are the Sovereign AI for workspace '{ws['name']}'. Respond helpfully."
    if memory_context:
        system_prompt += f"\n\nRecent workspace memory:\n{memory_context}"
    from ai.llm_gateway import call_llm as _call_llm
    _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="revenue_workspace", user_id=user.id)
    reply = _gw["text"].strip()
    # Store in workspace memory
    await db.sovereign_memory.insert_one({
        "workspace_id": ws_id, "actor": user.id, "content": message[:500],
        "reply": reply[:500], "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "workspace": ws["name"]}


# ── AI Resume Builder ─────────────────────────────────────────────────────────

@router.get("/revenue/resume/preview")
async def revenue_resume_preview(user: User = Depends(_dep_current_user)):
    """Preview an AI-generated resume from portfolio + credentials data."""
    portfolio = await db.portfolio.find_one({"user_id": user.id}, {"_id": 0})
    credentials = await db.credentials.find(
        {"user_id": user.id},
        {"_id": 0, "title": 1, "issued_at": 1, "issuer": 1},
    ).to_list(length=50)
    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "full_name": 1, "email": 1})
    return {
        "name": user_doc.get("full_name", "") if user_doc else "",
        "email": user_doc.get("email", "") if user_doc else "",
        "credentials": credentials,
        "portfolio_bio": (portfolio or {}).get("bio", ""),
        "portfolio_projects": (portfolio or {}).get("projects", []),
    }
