"""
Users + RBAC router — user administration, roles, permissions, IP whitelist.

Extracted verbatim from backend/server.py (monolith refactor, slice 2).
Shared state (db, audit, notify, current_user, can_modify, hash_pw) is bound
by server.py via bind() at include time, so this module has no circular imports.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from security.field_authorization import FieldAuthorization

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["users"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = audit = notify = None
current_user = can_modify = hash_pw = None


def bind(_db, _audit, _notify, _current_user, _can_modify, _hash_pw):
    """Called by server.py at include time to inject shared dependencies."""
    global db, audit, notify, current_user, can_modify, hash_pw
    db, audit, notify = _db, _audit, _notify
    current_user, can_modify, hash_pw = _current_user, _can_modify, _hash_pw


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "priority_member": 2, "instructor": 2, "creative_partner": 2, "site_support": 3, "admin": 3, "executive_admin": 4}
Role = Literal["student", "priority_member", "instructor", "creative_partner", "site_support", "admin", "executive_admin"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
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


# ── Request models (mirror server.py definitions) ────────────────────────────
class AdminCreateUserReq(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = "student"
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminRoleReq(BaseModel):
    role: Role


class AdminEditUserReq(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=500)
    email: Optional[EmailStr] = None
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminActiveReq(BaseModel):
    is_active: bool


class AdminResetPasswordReq(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class BanReq(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


# ═════════════════════════════════════════════════════════════════════════════
# Endpoint bodies (extracted verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/admin/users")
async def all_users(
    role: Optional[Role] = None,
    associate: Optional[str] = None,
    active: Optional[bool] = None,
    q: Optional[str] = None,
    user: User = Depends(_require_rank("admin")),
):
    """List users with optional filters.

    Query params (all optional, AND-combined):
      * role=student|instructor|admin|executive_admin
      * associate=Associate-Alpha
      * active=true|false
      * q=substring  (case-insensitive match on full_name OR email)
    """
    query: dict = {}
    if role:
        query["role"] = role
    if associate is not None:
        query["associate"] = associate
    if active is not None:
        # Treat unset is_active as True (legacy users seeded before the field).
        query["is_active"] = {"$ne": False} if active else False
    if q:
        # Mongo regex search escaped for safety.
        import re
        rx = re.escape(q)
        query["$or"] = [
            {"full_name": {"$regex": rx, "$options": "i"}},
            {"email": {"$regex": rx, "$options": "i"}},
        ]
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(5000)

    # Get visible fields for admin viewing user list (admin can see most, but still filter sensitive data)
    visible_fields = FieldAuthorization.get_visible_fields(
        viewer_role=user.role,
        target_role="student",  # Assume viewing students; actual role varies
        is_own_profile=False
    )

    # Filter each user's response
    filtered_users = []
    for u in users:
        filtered = FieldAuthorization.filter_response(u, visible_fields)
        filtered_users.append(filtered)

    # Audit access to user list
    try:
        await audit(user.id, "admin.users.list_accessed", target="all_users", meta={"count": len(filtered_users)})
    except Exception:
        pass  # Audit failure doesn't block the request

    return filtered_users


@router.post("/admin/associate")
async def assign_associate(payload: dict, user: User = Depends(_require_rank("admin"))):
    uid = payload.get("user_id")
    associate = payload.get("associate")
    if not uid:
        raise HTTPException(400, "user_id required")
    await db.users.update_one({"id": uid}, {"$set": {"associate": associate}})
    await audit(user.id, "admin.user.associate_changed", target=uid, meta={"associate": associate})
    return {"ok": True}


@router.post("/admin/users")
async def admin_create_user(body: AdminCreateUserReq, user: User = Depends(_require_rank("admin"))):
    """Admin-only: create a user with any role (including admin/instructor).
    Only executive_admins may create another executive_admin.

    Newly created accounts have `must_change_password=True` — the admin tells
    the user the temp password verbally/email; on first login the frontend
    routes them to /settings until they pick a new one."""
    if body.role == "executive_admin" and user.role != "executive_admin":
        raise HTTPException(403, "Only executive_admin can create another executive_admin.")
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")
    new_user = User(email=body.email, full_name=body.full_name, role=body.role,
                    associate=body.associate, must_change_password=True)
    doc = new_user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    await db.users.insert_one(doc)
    await audit(user.id, "admin.user.created", target=new_user.id,
                meta={"email": body.email, "role": body.role})
    return {"ok": True, "user": new_user.model_dump(mode="json")}


@router.patch("/admin/users/{uid}/role")
async def admin_change_role(uid: str, body: AdminRoleReq, user: User = Depends(_require_rank("admin"))):
    """Admin-only: promote/demote a user.
    Hierarchy guard: an admin cannot promote anyone TO executive_admin and
    cannot modify an existing executive_admin. Only executive_admin can."""
    if uid == user.id and ROLE_RANK.get(body.role, 0) < ROLE_RANK.get(user.role, 0):
        raise HTTPException(400, "Refusing to demote yourself — ask a higher-privileged admin.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    if body.role == "executive_admin" and user.role != "executive_admin":
        raise HTTPException(403, "Only executive_admin can grant the executive_admin role.")
    await db.users.update_one({"id": uid}, {"$set": {"role": body.role}})
    await audit(user.id, "admin.user.role_changed", target=uid,
                meta={"from": target.get("role"), "to": body.role})
    return {"ok": True, "id": uid, "role": body.role}


@router.patch("/admin/users/{uid}")
async def admin_edit_user(uid: str, body: AdminEditUserReq, user: User = Depends(_require_rank("admin"))):
    """Admin-only: edit name / email / associate."""
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    update = {}
    if body.full_name is not None and body.full_name.strip():
        update["full_name"] = body.full_name.strip()
    if body.email is not None and body.email != target.get("email"):
        if await db.users.find_one({"email": body.email, "id": {"$ne": uid}}):
            raise HTTPException(400, "Email already in use")
        update["email"] = body.email
    if body.associate is not None:
        update["associate"] = body.associate.strip() or None
    if not update:
        return {"ok": True, "noop": True}
    await db.users.update_one({"id": uid}, {"$set": update})
    await audit(user.id, "admin.user.edited", target=uid, meta=update)
    return {"ok": True, "updated": list(update.keys())}


@router.patch("/admin/users/{uid}/active")
async def admin_set_active(uid: str, body: AdminActiveReq, user: User = Depends(_require_rank("admin"))):
    """Admin-only: deactivate (lock) or reactivate (unlock) an account.
    Deactivated users cannot log in and existing sessions are rejected on next call."""
    if uid == user.id and not body.is_active:
        raise HTTPException(400, "Refusing to deactivate yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    # Last-active-admin guard (admin OR executive_admin counts as "admin-class")
    if target.get("role") in ("admin", "executive_admin") and not body.is_active:
        active_admin_class = await db.users.count_documents({
            "role": {"$in": ["admin", "executive_admin"]},
            "is_active": {"$ne": False},
        })
        if active_admin_class <= 1:
            raise HTTPException(400, "Cannot deactivate the last active admin-class user.")
    # Last-executive guard
    if target.get("role") == "executive_admin" and not body.is_active:
        active_execs = await db.users.count_documents({"role": "executive_admin", "is_active": {"$ne": False}})
        if active_execs <= 1:
            raise HTTPException(400, "Cannot deactivate the last active executive_admin.")
    await db.users.update_one({"id": uid}, {"$set": {"is_active": body.is_active}})
    await audit(user.id, "admin.user.active_changed", target=uid,
                meta={"is_active": body.is_active})
    return {"ok": True, "id": uid, "is_active": body.is_active}


@router.post("/admin/users/{uid}/ban")
async def admin_ban_user(uid: str, body: BanReq, user: User = Depends(_require_rank("executive_admin"))):
    """Permanently ban a user: deactivates account, records ban reason, and kills all sessions.
    executive_admin only. Cannot ban another executive_admin or yourself."""
    if uid == user.id:
        raise HTTPException(400, "Cannot ban yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if target.get("role") == "executive_admin":
        raise HTTPException(403, "Cannot ban an executive_admin.")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": uid}, {"$set": {
        "is_active": False,
        "banned": True,
        "ban_reason": body.reason,
        "banned_by": user.id,
        "banned_at": now_iso,
    }})
    await db.sessions.delete_many({"user_id": uid})
    await audit(user.id, "admin.user.banned", target=uid, meta={"reason": body.reason})
    return {"ok": True, "id": uid, "banned": True}


@router.post("/admin/users/{uid}/unban")
async def admin_unban_user(uid: str, user: User = Depends(_require_rank("executive_admin"))):
    """Remove a ban and reactivate the account. executive_admin only."""
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {
        "$set": {"is_active": True},
        "$unset": {"banned": "", "ban_reason": "", "banned_by": "", "banned_at": ""},
    })
    await audit(user.id, "admin.user.unbanned", target=uid)
    return {"ok": True, "id": uid, "banned": False}


@router.delete("/admin/users/{uid}")
async def admin_delete_user(uid: str, user: User = Depends(_require_rank("admin"))):
    """Admin-only: delete a user. Refuses self-delete and last-admin/exec delete."""
    if uid == user.id:
        raise HTTPException(400, "Refusing to delete yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    # Last-admin-class guard
    if target.get("role") in ("admin", "executive_admin"):
        admin_class = await db.users.count_documents({"role": {"$in": ["admin", "executive_admin"]}})
        if admin_class <= 1:
            raise HTTPException(400, "Cannot delete the last admin-class user.")
    if target.get("role") == "executive_admin":
        execs = await db.users.count_documents({"role": "executive_admin"})
        if execs <= 1:
            raise HTTPException(400, "Cannot delete the last executive_admin.")
    await db.users.delete_one({"id": uid})
    await audit(user.id, "admin.user.deleted", target=uid,
                meta={"email": target.get("email"), "role": target.get("role")})
    return {"ok": True}


@router.post("/admin/users/{uid}/password")
async def admin_reset_password(uid: str, body: AdminResetPasswordReq,
                               user: User = Depends(_require_rank("admin"))):
    """Admin-only: reset another user's password.
    An admin cannot reset an executive_admin's password; only an
    executive_admin can do that."""
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to reset this user's password.")
    await db.users.update_one({"id": uid}, {"$set": {
        "password_hash": hash_pw(body.new_password),
        "must_change_password": True,  # force rotation on next login
    }})
    await audit(user.id, "admin.user.password_reset", target=uid)
    return {"ok": True}


@router.get("/admin/users/{uid}/sessions")
async def exec_list_user_sessions(uid: str, user: User = Depends(_require_rank("executive_admin"))):
    """List active login sessions for any user (exec-only)."""
    sessions = await db.auth_sessions.find(
        {"user_id": uid},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("last_seen", -1).to_list(length=50)
    return {"sessions": sessions}

@router.delete("/admin/users/{uid}/sessions")
async def exec_force_logout(uid: str, user: User = Depends(_require_rank("executive_admin"))):
    """Force-logout all sessions for a user (exec-only)."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$inc": {"token_version": 1}})
    result = await db.auth_sessions.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.force_logout", target=uid,
                meta={"sessions_revoked": result.deleted_count})
    return {"ok": True, "sessions_revoked": result.deleted_count}

@router.post("/admin/users/bulk")
async def exec_bulk_action(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Bulk action on multiple users: upgrade, downgrade, suspend, unsuspend.
    body: { action: 'role'|'suspend'|'unsuspend', uids: [...], role?: str }"""
    action = body.get("action")
    uids = body.get("uids", [])
    if not uids or not isinstance(uids, list):
        raise HTTPException(400, "uids must be a non-empty list")
    if action not in ("role", "suspend", "unsuspend"):
        raise HTTPException(400, "action must be role|suspend|unsuspend")
    results = {"ok": [], "err": []}
    for uid in uids:
        try:
            target = await db.users.find_one({"id": uid}, {"_id": 0, "role": 1, "full_name": 1})
            if not target:
                results["err"].append({"uid": uid, "reason": "not found"})
                continue
            if not can_modify(user, target.get("role", "")):
                results["err"].append({"uid": uid, "reason": "hierarchy"})
                continue
            if action == "role":
                new_role = body.get("role")
                if new_role not in ROLE_RANK:
                    results["err"].append({"uid": uid, "reason": "invalid role"})
                    continue
                await db.users.update_one({"id": uid}, {"$set": {"role": new_role}})
                await audit(user.id, "exec.bulk.role_changed", target=uid,
                            meta={"from": target["role"], "to": new_role})
            elif action == "suspend":
                await db.users.update_one({"id": uid}, {"$set": {"is_active": False}})
                await audit(user.id, "exec.bulk.suspended", target=uid)
            elif action == "unsuspend":
                await db.users.update_one({"id": uid}, {"$set": {"is_active": True}})
                await audit(user.id, "exec.bulk.unsuspended", target=uid)
            results["ok"].append(uid)
        except Exception as e:
            results["err"].append({"uid": uid, "reason": str(e)})
    return results

@router.get("/admin/users/{uid}/audit")
async def exec_user_audit(uid: str, limit: int = 50, user: User = Depends(_require_rank("admin"))):
    """Audit history for a specific user (as actor or target), admin+."""
    entries = await db.audit_log.find(
        {"$or": [{"actor_id": uid}, {"target_id": uid}]},
        {"_id": 0},
    ).sort("at", -1).limit(min(limit, 200)).to_list(length=200)
    return entries

@router.get("/admin/rbac/matrix")
async def get_rbac_matrix(user: User = Depends(_require_rank("executive_admin"))):
    """Return the platform permission matrix stored in DB."""
    doc = await db.platform_config.find_one({"key": "rbac_matrix"}, {"_id": 0})
    default_matrix = {
        "student":         {"content_read": True,  "content_create": False, "content_edit_own": True,  "content_delete_own": True,  "user_warn": False, "user_mute": False, "user_ban": False, "api_access": False, "billing_view": False, "export_data": False},
        "instructor":      {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": False, "api_access": True,  "billing_view": False, "export_data": False},
        "admin":           {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
        "executive_admin": {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
    }
    return {"matrix": (doc or {}).get("value", default_matrix)}

@router.patch("/admin/rbac/matrix")
async def set_rbac_matrix(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Update the platform permission matrix (exec-only)."""
    matrix = body.get("matrix")
    if not isinstance(matrix, dict):
        raise HTTPException(400, "matrix must be an object")
    valid_roles = set(ROLE_RANK.keys())
    for role in matrix:
        if role not in valid_roles:
            raise HTTPException(400, f"Unknown role: {role}")
    await db.platform_config.update_one(
        {"key": "rbac_matrix"},
        {"$set": {"key": "rbac_matrix", "value": matrix, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "exec.rbac.matrix_updated", meta={"roles": list(matrix.keys())})
    return {"ok": True}

@router.get("/admin/mfa/config")
async def get_mfa_config(user: User = Depends(_require_rank("executive_admin"))):
    """Return MFA enforcement config per role."""
    doc = await db.platform_config.find_one({"key": "mfa_config"}, {"_id": 0})
    default = {"executive_admin": True, "admin": True, "instructor": False, "student": False}
    return {"mfa": (doc or {}).get("value", default)}

@router.patch("/admin/mfa/config")
async def set_mfa_config(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Set MFA enforcement per role (exec-only)."""
    mfa = body.get("mfa")
    if not isinstance(mfa, dict):
        raise HTTPException(400, "mfa must be an object")
    await db.platform_config.update_one(
        {"key": "mfa_config"},
        {"$set": {"key": "mfa_config", "value": mfa, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "exec.mfa.config_updated", meta=mfa)
    return {"ok": True, "mfa": mfa}

@router.get("/admin/access/ipwhitelist")
async def get_ip_whitelist(user: User = Depends(_require_rank("executive_admin"))):
    """Return IP whitelist entries."""
    entries = await db.ip_whitelist.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=200)
    return {"entries": entries}

@router.post("/admin/access/ipwhitelist")
async def add_ip_whitelist(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Add an IP/CIDR to the whitelist for a role."""
    ip = (body.get("ip") or "").strip()
    role = body.get("role", "executive_admin")
    note = (body.get("note") or "").strip()
    if not ip:
        raise HTTPException(400, "ip is required")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Unknown role: {role}")
    import uuid as _uuid
    entry = {"id": str(_uuid.uuid4()), "ip": ip, "role": role, "note": note,
             "added_by": user.id, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ip_whitelist.insert_one(entry)
    await audit(user.id, "exec.access.ip_added", meta={"ip": ip, "role": role})
    entry.pop("_id", None)
    return entry

@router.delete("/admin/access/ipwhitelist/{entry_id}")
async def remove_ip_whitelist(entry_id: str, user: User = Depends(_require_rank("executive_admin"))):
    """Remove an IP whitelist entry."""
    result = await db.ip_whitelist.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Entry not found")
    await audit(user.id, "exec.access.ip_removed", meta={"entry_id": entry_id})
    return {"ok": True}

@router.post("/admin/users/{uid}/elevated-role")
async def grant_elevated_role(uid: str, body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """Grant a time-bound elevated role to a user (exec-only).
    body: { role: str, expires_hours: int, reason: str }"""
    role = body.get("role")
    hours = body.get("expires_hours", 24)
    reason = body.get("reason", "")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Unknown role: {role}")
    if not (1 <= hours <= 168):
        raise HTTPException(400, "expires_hours must be 1-168")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "role": 1, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
    import uuid as _uuid
    record = {
        "id": str(_uuid.uuid4()), "user_id": uid, "role": role,
        "original_role": target["role"], "expires_at": expires_at,
        "reason": reason, "granted_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.elevated_roles.insert_one(record)
    await db.users.update_one({"id": uid}, {"$set": {"role": role, "elevated_until": expires_at, "original_role": target["role"]}})
    await audit(user.id, "exec.user.elevated_role", target=uid,
                meta={"role": role, "expires_at": expires_at, "reason": reason})
    record.pop("_id", None)
    return record

@router.get("/admin/users/{uid}/elevated-role")
async def get_elevated_role(uid: str, user: User = Depends(_require_rank("executive_admin"))):
    """Get active elevated role record for user."""
    record = await db.elevated_roles.find_one(
        {"user_id": uid, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0},
    )
    return {"elevated": record}

@router.delete("/admin/users/{uid}/elevated-role")
async def revoke_elevated_role(uid: str, user: User = Depends(_require_rank("executive_admin"))):
    """Revoke time-bound elevated role and revert to original."""
    target = await db.users.find_one({"id": uid}, {"_id": 0, "original_role": 1, "elevated_until": 1})
    if not target or not target.get("original_role"):
        raise HTTPException(404, "No active elevation found")
    original = target["original_role"]
    await db.users.update_one({"id": uid}, {"$set": {"role": original}, "$unset": {"elevated_until": 1, "original_role": 1}})
    await db.elevated_roles.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.elevation_revoked", target=uid, meta={"reverted_to": original})
    return {"ok": True, "reverted_to": original}

@router.patch("/admin/users/{uid}/sage-tier")
async def set_user_sage_tier(uid: str, body: dict, user: User = Depends(_require_rank("admin"))):
    """Grant or revoke Sage advanced tier for a user (admin+).
    body: { tier: "basic" | "advanced" }"""
    tier = (body.get("tier") or "").strip().lower()
    if tier not in ("basic", "advanced"):
        raise HTTPException(400, "tier must be 'basic' or 'advanced'")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$set": {"sage_tier": tier}})
    await audit(user.id, "admin.sage.tier_updated", target=uid, meta={"tier": tier})
    return {"ok": True, "uid": uid, "sage_tier": tier}


class _AcceptTermsReq(BaseModel):
    version: str = "v1"
    timestamp: Optional[str] = None


@router.post("/users/accept-terms")
async def users_accept_terms(body: _AcceptTermsReq, user: User = Depends(_dep_current_user)):
    """Record the current user's acceptance of the terms version.
    Idempotent upsert — re-accepting a version just refreshes the timestamp.
    The frontend (TermsOfService.jsx) fires this on page load; before this
    endpoint existed the call silently 404'd and acceptance was never stored.
    """
    now = datetime.now(timezone.utc)
    record = {
        "version": body.version,
        "client_timestamp": body.timestamp,
        "accepted_at": now.isoformat(),
    }
    await db.terms_acceptance.update_one(
        {"user_id": user.id},
        {"$set": record},
        upsert=True)
    await audit(user.id, "user.terms_accepted", meta={"version": body.version})
    return {"ok": True, "version": body.version, "accepted_at": now.isoformat()}
