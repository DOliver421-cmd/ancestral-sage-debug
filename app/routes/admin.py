"""app/routes/admin.py — Admin and executive governance endpoints.

Extracted from backend/server.py. No logic changed.
"""
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role, can_modify, assert_role
from app.security.passwords import hash_pw
from app.config import ROLE_RANK, APP_VERSION
from app.utils.audit import audit

logger = logging.getLogger("lcewai")

router = APIRouter()

try:
    from security.field_authorization import FieldAuthorization
except ImportError:
    FieldAuthorization = None

try:
    from seed import MODULES, CREDENTIALS, COMPETENCIES
except ImportError:
    MODULES: list = []
    CREDENTIALS: list = []
    COMPETENCIES: list = []


# ── Request models ────────────────────────────────────────────────────────────

class AdminCreateUserReq(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=500)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = "student"
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminRoleReq(BaseModel):
    role: str


class AdminEditUserReq(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=500)
    email: Optional[EmailStr] = None
    associate: Optional[str] = Field(None, min_length=1, max_length=200)


class AdminActiveReq(BaseModel):
    is_active: bool


class AdminResetPasswordReq(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


# ── User CRUD ─────────────────────────────────────────────────────────────────

@router.get("/admin/users")
async def all_users(
    role: Optional[str] = None,
    associate: Optional[str] = None,
    active: Optional[bool] = None,
    q: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    query: dict = {}
    if role:
        query["role"] = role
    if associate is not None:
        query["associate"] = associate
    if active is not None:
        query["is_active"] = {"$ne": False} if active else False
    if q:
        rx = re.escape(q)
        query["$or"] = [
            {"full_name": {"$regex": rx, "$options": "i"}},
            {"email": {"$regex": rx, "$options": "i"}},
        ]
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(5000)

    if FieldAuthorization is not None:
        visible_fields = FieldAuthorization.get_visible_fields(
            viewer_role=user.role,
            target_role="student",
            is_own_profile=False,
        )
        filtered_users = [FieldAuthorization.filter_response(u, visible_fields) for u in users]
    else:
        filtered_users = users

    try:
        await audit(user.id, "admin.users.list_accessed", target="all_users", meta={"count": len(filtered_users)})
    except Exception:
        pass
    return filtered_users


@router.post("/admin/associate")
async def assign_associate(payload: dict, user: User = Depends(require_role("admin"))):
    uid = payload.get("user_id")
    associate = payload.get("associate")
    if not uid:
        raise HTTPException(400, "user_id required")
    await db.users.update_one({"id": uid}, {"$set": {"associate": associate}})
    await audit(user.id, "admin.user.associate_changed", target=uid, meta={"associate": associate})
    return {"ok": True}


@router.post("/admin/users")
async def admin_create_user(body: AdminCreateUserReq, user: User = Depends(require_role("admin"))):
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
async def admin_change_role(uid: str, body: AdminRoleReq, user: User = Depends(require_role("admin"))):
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
async def admin_edit_user(uid: str, body: AdminEditUserReq, user: User = Depends(require_role("admin"))):
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
async def admin_set_active(uid: str, body: AdminActiveReq, user: User = Depends(require_role("admin"))):
    if uid == user.id and not body.is_active:
        raise HTTPException(400, "Refusing to deactivate yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
    if target.get("role") in ("admin", "executive_admin") and not body.is_active:
        active_admin_class = await db.users.count_documents({
            "role": {"$in": ["admin", "executive_admin"]},
            "is_active": {"$ne": False},
        })
        if active_admin_class <= 1:
            raise HTTPException(400, "Cannot deactivate the last active admin-class user.")
    if target.get("role") == "executive_admin" and not body.is_active:
        active_execs = await db.users.count_documents({"role": "executive_admin", "is_active": {"$ne": False}})
        if active_execs <= 1:
            raise HTTPException(400, "Cannot deactivate the last active executive_admin.")
    await db.users.update_one({"id": uid}, {"$set": {"is_active": body.is_active}})
    await audit(user.id, "admin.user.active_changed", target=uid,
                meta={"is_active": body.is_active})
    return {"ok": True, "id": uid, "is_active": body.is_active}


@router.delete("/admin/users/{uid}")
async def admin_delete_user(uid: str, user: User = Depends(require_role("admin"))):
    if uid == user.id:
        raise HTTPException(400, "Refusing to delete yourself.")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to modify this user.")
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
                               user: User = Depends(require_role("admin"))):
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    target = await db.users.find_one({"id": uid}, {"_id": 0})
    if not target:
        raise HTTPException(404, "User not found")
    if not can_modify(user, target.get("role", "")):
        raise HTTPException(403, "You don't have permission to reset this user's password.")
    await db.users.update_one({"id": uid}, {"$set": {
        "password_hash": hash_pw(body.new_password),
        "must_change_password": True,
    }})
    await audit(user.id, "admin.user.password_reset", target=uid)
    return {"ok": True}


# ── Admin stats / dashboard ───────────────────────────────────────────────────

@router.get("/admin/stats")
async def stats(user: User = Depends(require_role("admin"))):
    return {
        "users": await db.users.count_documents({}),
        "students": await db.users.count_documents({"role": "student"}),
        "instructors": await db.users.count_documents({"role": "instructor"}),
        "admins": await db.users.count_documents({"role": "admin"}),
        "executives": await db.users.count_documents({"role": "executive_admin"}),
        "modules": await db.modules.count_documents({}),
        "completions": await db.progress.count_documents({"status": "completed"}),
        "labs_pending": await db.lab_submissions.count_documents({"status": "pending_review"}),
        "incidents_open": await db.incidents.count_documents({"status": "open"}),
        "credentials_issued": await db.user_credentials.count_documents({}),
    }


@router.get("/admin/recent-activity")
async def recent_activity(limit: int = 15, user: User = Depends(require_role("admin"))):
    rows = await db.audit_log.find({}, {"_id": 0}).sort("at", -1).limit(min(limit, 50)).to_list(50)
    actor_ids = list({r["actor_id"] for r in rows if r.get("actor_id")})
    actors = {}
    if actor_ids:
        async for u in db.users.find({"id": {"$in": actor_ids}}, {"_id": 0, "id": 1, "full_name": 1, "role": 1}):
            actors[u["id"]] = u
    out = []
    for r in rows:
        a = actors.get(r.get("actor_id"))
        out.append({
            "id": r["id"],
            "at": r["at"],
            "action": r["action"],
            "target": r.get("target"),
            "actor_name": a["full_name"] if a else "system",
            "actor_role": a["role"] if a else None,
            "meta": r.get("meta") or {},
        })
    return out


@router.get("/admin/cohorts")
async def cohort_summary(user: User = Depends(require_role("admin"))):
    pipeline = [
        {"$group": {
            "_id": {"associate": "$associate", "role": "$role"},
            "n": {"$sum": 1},
        }}
    ]
    rows = await db.users.aggregate(pipeline).to_list(500)
    cohorts: dict = {}
    for r in rows:
        a = r["_id"].get("associate") or "—"
        c = cohorts.setdefault(a, {"associate": a, "members": 0, "students": 0, "instructors": 0, "admins": 0})
        c["members"] += r["n"]
        if r["_id"]["role"] == "student":
            c["students"] += r["n"]
        elif r["_id"]["role"] == "instructor":
            c["instructors"] += r["n"]
        elif r["_id"]["role"] in ("admin", "executive_admin"):
            c["admins"] += r["n"]
    completion_pipeline = [
        {"$match": {"status": "completed"}},
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "u"}},
        {"$unwind": {"path": "$u", "preserveNullAndEmptyArrays": False}},
        {"$group": {"_id": "$u.associate", "completions": {"$sum": 1}}},
    ]
    comp_rows = await db.progress.aggregate(completion_pipeline).to_list(500)
    comp_by_cohort = {((r["_id"]) if r["_id"] else "—"): r["completions"] for r in comp_rows}
    for cohort_name, c in cohorts.items():
        c["completions"] = comp_by_cohort.get(cohort_name, 0)
    return sorted(cohorts.values(), key=lambda x: -x["members"])


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/admin/audit")
async def view_audit(
    limit: int = 200,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    query: dict = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if actor_id:
        query["actor_id"] = actor_id
    docs = await db.audit_log.find(query, {"_id": 0}).sort("at", -1).to_list(min(limit, 1000))
    user_ids = list({d["actor_id"] for d in docs if d.get("actor_id")})
    users_list = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users_list}
    for d in docs:
        d["actor"] = umap.get(d.get("actor_id")) if d.get("actor_id") else None
    return docs


# ── Sites, inventory, tool checkout ──────────────────────────────────────────

@router.get("/admin/sites")
async def list_sites(user: User = Depends(require_role("admin", "instructor"))):
    docs = await db.sites.find({}, {"_id": 0}).to_list(100)
    return docs


@router.post("/admin/sites")
async def create_site(payload: dict, user: User = Depends(require_role("admin"))):
    if not payload.get("slug") or not payload.get("name"):
        raise HTTPException(400, "slug and name required")
    if await db.sites.find_one({"slug": payload["slug"]}):
        raise HTTPException(400, "Site slug exists")
    doc = {
        "id": str(uuid.uuid4()),
        "slug": payload["slug"],
        "name": payload["name"],
        "address": payload.get("address", ""),
        "capacity": int(payload.get("capacity", 0)),
    }
    await db.sites.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/admin/inventory")
async def list_inventory(site_slug: Optional[str] = None, user: User = Depends(require_role("admin", "instructor"))):
    q = {"site_slug": site_slug} if site_slug else {}
    items = await db.inventory.find(q, {"_id": 0}).to_list(500)
    return items


@router.post("/admin/inventory")
async def add_inventory(payload: dict, user: User = Depends(require_role("admin"))):
    required = ["sku", "name", "category", "quantity_total", "site_slug"]
    if any(k not in payload for k in required):
        raise HTTPException(400, f"Required: {required}")
    if await db.inventory.find_one({"sku": payload["sku"]}):
        raise HTTPException(400, "SKU exists")
    doc = {
        "id": str(uuid.uuid4()),
        "sku": payload["sku"],
        "name": payload["name"],
        "category": payload["category"],
        "site_slug": payload["site_slug"],
        "quantity_total": int(payload["quantity_total"]),
        "quantity_available": int(payload["quantity_total"]),
    }
    await db.inventory.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/admin/checkout")
async def checkout_tool(payload: dict, user: User = Depends(require_role("instructor", "admin"))):
    sku = payload.get("sku")
    student_id = payload.get("user_id")
    qty = int(payload.get("quantity", 1))
    if not sku or not student_id:
        raise HTTPException(400, "sku and user_id required")
    item = await db.inventory.find_one({"sku": sku}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Item not found")
    if item["quantity_available"] < qty:
        raise HTTPException(400, f"Only {item['quantity_available']} available")
    co = {
        "id": str(uuid.uuid4()),
        "sku": sku,
        "user_id": student_id,
        "quantity": qty,
        "checked_out_by": user.id,
        "checked_out_at": datetime.now(timezone.utc).isoformat(),
        "returned_at": None,
        "status": "out",
    }
    await db.tool_checkouts.insert_one(co)
    await db.inventory.update_one({"sku": sku}, {"$inc": {"quantity_available": -qty}})
    co.pop("_id", None)
    return co


@router.post("/admin/checkout/{checkout_id}/return")
async def return_tool(checkout_id: str, user: User = Depends(require_role("instructor", "admin"))):
    co = await db.tool_checkouts.find_one({"id": checkout_id}, {"_id": 0})
    if not co or co["status"] == "returned":
        raise HTTPException(400, "Invalid or already returned")
    await db.tool_checkouts.update_one(
        {"id": checkout_id},
        {"$set": {"status": "returned", "returned_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.inventory.update_one({"sku": co["sku"]}, {"$inc": {"quantity_available": co["quantity"]}})
    return {"ok": True}


@router.get("/admin/checkouts")
async def list_checkouts(status: Optional[str] = None, user: User = Depends(require_role("instructor", "admin"))):
    q = {"status": status} if status else {}
    docs = await db.tool_checkouts.find(q, {"_id": 0}).sort("checked_out_at", -1).to_list(500)
    user_ids = list({d["user_id"] for d in docs})
    skus = list({d["sku"] for d in docs})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    items = await db.inventory.find({"sku": {"$in": skus}}, {"_id": 0}).to_list(500)
    u_map = {u["id"]: u for u in users}
    i_map = {i["sku"]: i for i in items}
    for d in docs:
        d["user"] = u_map.get(d["user_id"])
        d["item"] = i_map.get(d["sku"])
    return docs


# ── Platform flags / broadcast ────────────────────────────────────────────────

@router.get("/admin/platform/flags")
async def get_platform_flags(user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
    if not doc:
        return {"flags": {}}
    return {"flags": doc.get("flags", {})}


@router.post("/admin/platform/flags/{flag}")
async def set_platform_flag(
    flag: str,
    payload: dict,
    user: User = Depends(require_role("executive_admin")),
):
    ALLOWED = {"platform_locked", "marketplace_disabled", "ai_disabled",
               "community_disabled", "labs_disabled"}
    if flag not in ALLOWED:
        raise HTTPException(400, f"Unknown flag '{flag}'. Allowed: {', '.join(sorted(ALLOWED))}")
    value = bool(payload.get("value", True))
    reason = (payload.get("reason") or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    await db.platform_flags.update_one(
        {"_id": "flags"},
        {"$set": {
            f"flags.{flag}": {
                "enabled": value,
                "set_by": user.id,
                "set_at": now,
                "reason": reason,
            }
        }},
        upsert=True,
    )
    await audit(user.id, f"platform_flag:{flag}:{value}", {"reason": reason})
    return {"flag": flag, "enabled": value, "set_at": now}


@router.post("/admin/broadcast")
async def broadcast_notification(
    payload: dict,
    user: User = Depends(require_role("executive_admin", "admin")),
):
    message = (payload.get("message") or "").strip()
    title   = (payload.get("title") or "Platform Announcement").strip()
    target  = (payload.get("target") or "all").strip()
    if not message:
        raise HTTPException(400, "message is required")
    query: dict = {}
    if target != "all":
        query = {"$or": [{"role": target}, {"associate": target}]}
    recipients = await db.users.find(query, {"_id": 0, "id": 1}).to_list(10000)
    if not recipients:
        return {"sent": 0, "message": "No recipients matched"}
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": r["id"],
            "title": title,
            "message": message,
            "type": "broadcast",
            "read": False,
            "created_at": now,
            "sent_by": user.id,
        }
        for r in recipients
    ]
    await db.notifications.insert_many(docs)
    await audit(user.id, f"broadcast:{target}", {"title": title, "recipients": len(docs)})
    return {"sent": len(docs), "target": target}


# ── Sage safety caps ──────────────────────────────────────────────────────────

@router.get("/admin/sage/cap")
async def admin_get_sage_cap(user: User = Depends(require_role("executive_admin"))):
    from app.routes.ai import _SAFETY_LEVELS
    glob = await db.safety_caps.find_one({"_id": "global"}, {"_id": 0, "level": 1})
    overrides_raw = await db.safety_caps.find(
        {"_id": {"$regex": "^user:"}}, {"_id": 1, "level": 1}
    ).to_list(2000)
    user_ids = [d["_id"].split("user:", 1)[1] for d in overrides_raw]
    users = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users}
    overrides = [
        {
            "user_id": d["_id"].split("user:", 1)[1],
            "email": by_id.get(d["_id"].split("user:", 1)[1], {}).get("email"),
            "full_name": by_id.get(d["_id"].split("user:", 1)[1], {}).get("full_name"),
            "level": d["level"],
        }
        for d in overrides_raw
    ]
    return {
        "global_level": glob["level"] if glob else None,
        "available_levels": _SAFETY_LEVELS,
        "overrides": overrides,
    }


@router.put("/admin/sage/cap/global")
async def admin_set_sage_cap_global(
    body: dict, user: User = Depends(require_role("executive_admin"))
):
    level = body.get("level")
    if level is None:
        await db.safety_caps.delete_one({"_id": "global"})
    else:
        await db.safety_caps.update_one(
            {"_id": "global"},
            {"$set": {"level": level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_global_set",
        "details": {"level": level},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "global_level": level}


@router.put("/admin/sage/cap/user/{uid}")
async def admin_set_sage_cap_user(
    uid: str,
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    level = body.get("level")
    key = f"user:{uid}"
    if level is None:
        await db.safety_caps.delete_one({"_id": key})
    else:
        await db.safety_caps.update_one(
            {"_id": key},
            {"$set": {"level": level, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by": user.id}},
            upsert=True,
        )
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "actor_id": user.id,
        "action": "sage_cap_user_set",
        "target_id": uid,
        "details": {"level": level, "email": target.get("email")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "user_id": uid, "level": level}


@router.get("/admin/sage/audit")
async def admin_sage_audit(
    user: User = Depends(require_role("executive_admin")),
    user_id: Optional[str] = None,
    kind: Optional[str] = "all",
    limit: int = 100,
):
    limit = max(1, min(int(limit or 100), 500))
    chat_q: dict = {"mode": "ancestral_sage"}
    if user_id:
        chat_q["user_id"] = user_id
    if kind == "refusal":
        chat_q["refusal_reason"] = {"$exists": True, "$ne": None}
    elif kind == "crisis":
        chat_q["refusal_reason"] = "crisis_safety_template"
    rows = []
    if kind != "consent":
        chats = await db.chat_history.find(chat_q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        for c in chats:
            rows.append({
                "kind": (
                    "crisis" if c.get("refusal_reason") == "crisis_safety_template"
                    else "refusal" if c.get("refusal_reason")
                    else "chat"
                ),
                "id": c.get("id"),
                "user_id": c.get("user_id"),
                "session_id": c.get("session_id"),
                "intensity": c.get("intensity"),
                "safety_level": c.get("safety_level"),
                "consent_log_id": c.get("consent_log_id"),
                "refusal_reason": c.get("refusal_reason"),
                "user_msg": (c.get("user_msg") or "")[:300],
                "assistant_preview": (c.get("assistant_msg") or "")[:300] if c.get("assistant_msg") else None,
                "created_at": c.get("created_at"),
            })
    if kind in ("all", "consent"):
        consent_q: dict = {}
        if user_id:
            consent_q["user_id"] = user_id
        consents = await db.ai_consents.find(consent_q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        for cd in consents:
            rows.append({
                "kind": "consent",
                "id": cd.get("id"),
                "user_id": cd.get("user_id"),
                "intensity": cd.get("intensity"),
                "safety_level": cd.get("safety_level"),
                "created_at": cd.get("created_at"),
                "expires_at": cd.get("expires_at"),
            })
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    rows = rows[:limit]
    user_ids = list({r["user_id"] for r in rows if r.get("user_id")})
    users_list = await db.users.find(
        {"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "full_name": 1}
    ).to_list(2000) if user_ids else []
    by_id = {u["id"]: u for u in users_list}
    for r in rows:
        u = by_id.get(r.get("user_id") or "")
        if u:
            r["email"] = u.get("email")
            r["full_name"] = u.get("full_name")
    return {"rows": rows, "limit": limit, "kind": kind}


@router.get("/admin/sage/status")
async def admin_sage_status(user: User = Depends(require_role("executive_admin"))):
    from app.routes.ai import _sage_prompt_integrity_ok, SYSTEM_PROMPTS, ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
    integrity_ok = _sage_prompt_integrity_ok()
    modules = {
        "A": "present" if SYSTEM_PROMPTS.get("ancestral_sage") else "missing",
        "E": "present",
        "F": "present" if ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED else "missing",
        "D": "present",
    }
    last_audit = await db.audit_log.find(
        {"action": {"$regex": "^sage_"}}, {"_id": 0, "id": 1}
    ).sort("created_at", -1).limit(1).to_list(1)
    return {
        "prompt_hash_status": "match" if integrity_ok else "mismatch",
        "modules": modules,
        "fallback_active": not integrity_ok,
        "last_audit_id": (last_audit[0]["id"] if last_audit else None),
    }


@router.get("/admin/sage/metrics")
async def admin_sage_metrics(user: User = Depends(require_role("executive_admin"))):
    from app.routes.ai import (
        _tts_metrics, _tts_failures, _tts_breaker_state,
        TTS_METRICS_WINDOW_S, TTS_SESSION_CHAR_CAP, TTS_USER_DAILY_CHAR_CAP,
    )
    if not _tts_metrics:
        return {
            "p95_latency_ms": 0.0,
            "cache_hit_ratio": 0.0,
            "error_rate": 0.0,
            "sample_count": 0,
            "window_seconds": TTS_METRICS_WINDOW_S,
            "breaker": _tts_breaker_state(),
            "session_char_cap": TTS_SESSION_CHAR_CAP,
            "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
        }
    latencies = sorted(m[1] for m in _tts_metrics if not m[2] and not m[3])
    p95 = 0.0
    if latencies:
        idx = max(0, int(round(0.95 * (len(latencies) - 1))))
        p95 = round(latencies[idx], 1)
    hits = sum(1 for m in _tts_metrics if m[2])
    errors = sum(1 for m in _tts_metrics if m[3])
    n = len(_tts_metrics)
    return {
        "p95_latency_ms": p95,
        "cache_hit_ratio": round(hits / n, 3),
        "error_rate": round(errors / n, 3),
        "sample_count": n,
        "window_seconds": TTS_METRICS_WINDOW_S,
        "breaker": _tts_breaker_state(),
        "breaker_recent_failures": len(_tts_failures),
        "session_char_cap": TTS_SESSION_CHAR_CAP,
        "user_daily_char_cap": TTS_USER_DAILY_CHAR_CAP,
    }


# ── Run checks ────────────────────────────────────────────────────────────────

@router.post("/admin/run-checks")
async def admin_run_checks(user: User = Depends(require_role("admin"))):
    from app.services.engagement import run_escalation_check, run_engagement_check
    await run_escalation_check()
    await run_engagement_check()
    await audit(user.id, "admin.checks.manual_trigger")
    return {"ok": True, "message": "Escalation and engagement checks completed. Check notifications for flags."}


# ── AI costs ──────────────────────────────────────────────────────────────────

@router.get("/admin/ai-costs")
async def get_ai_costs(
    persona: Optional[str] = None,
    days: int = 7,
    user: User = Depends(require_role("admin")),
):
    from ai_cost_tracker import get_persona_costs, get_total_cost
    costs = await get_persona_costs(db, persona=persona, days=days)
    total = await get_total_cost(db, days=days)
    return {"costs": costs, "total": total, "period_days": days}


# ── Payments admin ────────────────────────────────────────────────────────────

@router.get("/admin/payments")
async def admin_payment_list(user=Depends(require_role("admin"))):
    cursor = db.payments.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    records = await cursor.to_list(500)
    total_cents = sum(r.get("amount_cents", 0) for r in records if r.get("status") == "paid")
    return {"payments": records, "total_revenue_cents": total_cents, "count": len(records)}


# ── Discount management ───────────────────────────────────────────────────────

@router.get("/admin/discounts")
async def get_active_discount(user: User = Depends(require_role("executive_admin"))):
    from app.routes.payments import _discount_manager
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")
    discount = await _discount_manager.get_active_discount()
    if discount:
        return discount.dict()
    return None


@router.post("/admin/discounts")
async def set_discount(body: dict, user: User = Depends(require_role("executive_admin"))):
    from app.routes.payments import _discount_manager
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")
    try:
        percentage = body.get("percentage")
        active = body.get("active", True)
        notes = body.get("notes", "")
        if percentage is None:
            raise ValueError("percentage is required")
        if not isinstance(percentage, int) or not (0 <= percentage <= 100):
            raise ValueError("percentage must be an integer between 0 and 100")
        if not active:
            discount = await _discount_manager.deactivate_discount()
            if discount:
                await audit(user.id, "discount.deactivated", meta={"discount_id": discount.id})
                return discount.dict()
            return None
        existing = await _discount_manager.get_active_discount()
        if existing:
            discount = await _discount_manager.update_discount_percentage(percentage, notes)
            await audit(user.id, "discount.updated", meta={"discount_id": discount.id, "new_percentage": percentage, "notes": notes})
        else:
            discount = await _discount_manager.create_discount(percentage, user.id, notes)
            await audit(user.id, "discount.created", meta={"discount_id": discount.id, "percentage": percentage, "expires_at": discount.expires_at.isoformat(), "notes": notes})
        return discount.dict()
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.exception("Error setting discount: %s", e)
        raise HTTPException(500, f"Error setting discount: {str(e)}")


# ── Executive governance ──────────────────────────────────────────────────────

@router.get("/admin/users/{uid}/sessions")
async def exec_list_user_sessions(uid: str, user: User = Depends(require_role("executive_admin"))):
    sessions = await db.auth_sessions.find(
        {"user_id": uid},
        {"_id": 0, "session_id": 1, "user_agent": 1, "ip": 1, "created_at": 1, "last_seen": 1},
    ).sort("last_seen", -1).to_list(length=50)
    return {"sessions": sessions}


@router.delete("/admin/users/{uid}/sessions")
async def exec_force_logout(uid: str, user: User = Depends(require_role("executive_admin"))):
    target = await db.users.find_one({"id": uid}, {"_id": 0, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$inc": {"token_version": 1}})
    result = await db.auth_sessions.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.force_logout", target=uid,
                meta={"sessions_revoked": result.deleted_count})
    return {"ok": True, "sessions_revoked": result.deleted_count}


@router.post("/admin/users/bulk")
async def exec_bulk_action(body: dict, user: User = Depends(require_role("executive_admin"))):
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
                await audit(user.id, "exec.bulk.role_changed", target=uid, meta={"from": target["role"], "to": new_role})
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
async def exec_user_audit(uid: str, limit: int = 50, user: User = Depends(require_role("admin"))):
    entries = await db.audit_log.find(
        {"$or": [{"actor_id": uid}, {"target_id": uid}]},
        {"_id": 0},
    ).sort("at", -1).limit(min(limit, 200)).to_list(length=200)
    return entries


@router.get("/admin/rbac/matrix")
async def get_rbac_matrix(user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_config.find_one({"key": "rbac_matrix"}, {"_id": 0})
    default_matrix = {
        "student":         {"content_read": True,  "content_create": False, "content_edit_own": True,  "content_delete_own": True,  "user_warn": False, "user_mute": False, "user_ban": False, "api_access": False, "billing_view": False, "export_data": False},
        "instructor":      {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": False, "api_access": True,  "billing_view": False, "export_data": False},
        "admin":           {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
        "executive_admin": {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
    }
    return {"matrix": (doc or {}).get("value", default_matrix)}


@router.patch("/admin/rbac/matrix")
async def set_rbac_matrix(body: dict, user: User = Depends(require_role("executive_admin"))):
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
async def get_mfa_config(user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_config.find_one({"key": "mfa_config"}, {"_id": 0})
    default = {"executive_admin": True, "admin": True, "instructor": False, "student": False}
    return {"mfa": (doc or {}).get("value", default)}


@router.patch("/admin/mfa/config")
async def set_mfa_config(body: dict, user: User = Depends(require_role("executive_admin"))):
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
async def get_ip_whitelist(user: User = Depends(require_role("executive_admin"))):
    entries = await db.ip_whitelist.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=200)
    return {"entries": entries}


@router.post("/admin/access/ipwhitelist")
async def add_ip_whitelist(body: dict, user: User = Depends(require_role("executive_admin"))):
    ip = (body.get("ip") or "").strip()
    role = body.get("role", "executive_admin")
    note = (body.get("note") or "").strip()
    if not ip:
        raise HTTPException(400, "ip is required")
    if role not in ROLE_RANK:
        raise HTTPException(400, f"Unknown role: {role}")
    entry = {"id": str(uuid.uuid4()), "ip": ip, "role": role, "note": note,
             "added_by": user.id, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ip_whitelist.insert_one(entry)
    await audit(user.id, "exec.access.ip_added", meta={"ip": ip, "role": role})
    entry.pop("_id", None)
    return entry


@router.delete("/admin/access/ipwhitelist/{entry_id}")
async def remove_ip_whitelist(entry_id: str, user: User = Depends(require_role("executive_admin"))):
    result = await db.ip_whitelist.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Entry not found")
    await audit(user.id, "exec.access.ip_removed", meta={"entry_id": entry_id})
    return {"ok": True}


@router.post("/admin/users/{uid}/elevated-role")
async def grant_elevated_role(uid: str, body: dict, user: User = Depends(require_role("executive_admin"))):
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
    record = {
        "id": str(uuid.uuid4()), "user_id": uid, "role": role,
        "original_role": target["role"], "expires_at": expires_at,
        "reason": reason, "granted_by": user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.elevated_roles.insert_one(record)
    await db.users.update_one({"id": uid}, {"$set": {"role": role, "elevated_until": expires_at, "original_role": target["role"]}})
    await audit(user.id, "exec.user.elevated_role", target=uid, meta={"role": role, "expires_at": expires_at, "reason": reason})
    record.pop("_id", None)
    return record


@router.get("/admin/users/{uid}/elevated-role")
async def get_elevated_role(uid: str, user: User = Depends(require_role("executive_admin"))):
    record = await db.elevated_roles.find_one(
        {"user_id": uid, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0},
    )
    return {"elevated": record}


@router.delete("/admin/users/{uid}/elevated-role")
async def revoke_elevated_role(uid: str, user: User = Depends(require_role("executive_admin"))):
    target = await db.users.find_one({"id": uid}, {"_id": 0, "original_role": 1, "elevated_until": 1})
    if not target or not target.get("original_role"):
        raise HTTPException(404, "No active elevation found")
    original = target["original_role"]
    await db.users.update_one({"id": uid}, {"$set": {"role": original}, "$unset": {"elevated_until": 1, "original_role": 1}})
    await db.elevated_roles.delete_many({"user_id": uid})
    await audit(user.id, "exec.user.elevation_revoked", target=uid, meta={"reverted_to": original})
    return {"ok": True, "reverted_to": original}


@router.patch("/admin/users/{uid}/sage-tier")
async def set_user_sage_tier(uid: str, body: dict, user: User = Depends(require_role("admin"))):
    tier = (body.get("tier") or "").strip().lower()
    if tier not in ("basic", "advanced"):
        raise HTTPException(400, "tier must be 'basic' or 'advanced'")
    target = await db.users.find_one({"id": uid}, {"_id": 0, "id": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")
    await db.users.update_one({"id": uid}, {"$set": {"sage_tier": tier}})
    await audit(user.id, "admin.sage.tier_updated", target=uid, meta={"tier": tier})
    return {"ok": True, "uid": uid, "sage_tier": tier}


@router.get("/admin/audit/export")
async def export_audit_log(
    format: str = "json",
    limit: int = 1000,
    action: str = None,
    actor_id: str = None,
    user: User = Depends(require_role("executive_admin")),
):
    filt: dict = {}
    if action:
        import re as _re
        filt["action"] = {"$regex": action, "$options": "i"}
    if actor_id:
        filt["actor_id"] = actor_id
    entries = await db.audit_log.find(filt, {"_id": 0}).sort("at", -1).limit(min(limit, 5000)).to_list(length=5000)
    if format == "csv":
        import io as _io, csv as _csv
        from fastapi.responses import Response as _Response
        buf = _io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=["at", "actor_id", "actor_name", "action", "target_id", "meta"])
        writer.writeheader()
        for e in entries:
            writer.writerow({"at": e.get("at",""), "actor_id": e.get("actor_id",""), "actor_name": e.get("actor_name",""),
                             "action": e.get("action",""), "target_id": e.get("target_id",""), "meta": str(e.get("meta",""))})
        return _Response(content=buf.getvalue(), media_type="text/csv",
                         headers={"Content-Disposition": "attachment; filename=audit_export.csv"})
    return entries


# ── Gateway management ────────────────────────────────────────────────────────

@router.post("/admin/gateway/keys")
async def push_gateway_key(body: dict, user: User = Depends(require_role("executive_admin"))):
    ALLOWED = {
        "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
        "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
        "OPENROUTER_API_KEY",
    }
    var_name = (body.get("var_name") or "").strip().upper()
    value    = (body.get("value")    or "").strip()
    if var_name not in ALLOWED:
        raise HTTPException(400, f"var_name '{var_name}' not in allowed set")
    if not value:
        raise HTTPException(400, "value cannot be empty")
    import ai.llm_gateway as _gw
    import os as _os
    ATTR_MAP = {
        "GROQ_API_KEY": "GROQ_API_KEY", "CEREBRAS_API_KEY": "CEREBRAS_API_KEY",
        "GEMINI_API_KEY": "GEMINI_API_KEY", "XAI_API_KEY": "XAI_API_KEY",
        "COHERE_API_KEY": "COHERE_API_KEY", "HUGGINGFACE_API_KEY": "HUGGINGFACE_API_KEY",
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    }
    attr = ATTR_MAP[var_name]
    setattr(_gw, attr, value)
    _os.environ[var_name] = value
    await audit(user.id, "gateway.key.pushed", meta={"var": var_name})
    logger.info("Gateway key pushed by exec: %s", var_name)
    return {"ok": True, "var": var_name, "active": True}


@router.delete("/admin/gateway/keys/{var_name}")
async def revoke_gateway_key(var_name: str, user: User = Depends(require_role("executive_admin"))):
    ALLOWED = {
        "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
        "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
        "OPENROUTER_API_KEY",
    }
    var_name = var_name.strip().upper()
    if var_name not in ALLOWED:
        raise HTTPException(400, f"var_name '{var_name}' not in allowed set")
    import ai.llm_gateway as _gw
    import os as _os
    setattr(_gw, var_name, "")
    _os.environ.pop(var_name, None)
    await audit(user.id, "gateway.key.revoked", meta={"var": var_name})
    logger.info("Gateway key revoked by exec: %s", var_name)
    return {"ok": True, "var": var_name, "active": False}


@router.patch("/admin/gateway/keys/{var_name}/toggle")
async def toggle_gateway_key(var_name: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    ALLOWED = {
        "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY",
        "XAI_API_KEY",  "COHERE_API_KEY",   "HUGGINGFACE_API_KEY",
        "OPENROUTER_API_KEY",
    }
    var_name = var_name.strip().upper()
    if var_name not in ALLOWED:
        raise HTTPException(400, f"var_name '{var_name}' not in allowed set")
    enabled = bool(body.get("enabled", True))
    import ai.llm_gateway as _gw
    import os as _os
    if not enabled:
        _saved = _os.environ.get(var_name, "") or getattr(_gw, var_name, "")
        setattr(_gw, var_name, "")
        await db.platform_config.update_one(
            {"key": f"gateway_key_saved_{var_name}"},
            {"$set": {"key": f"gateway_key_saved_{var_name}", "value": _saved}},
            upsert=True,
        )
    else:
        doc = await db.platform_config.find_one({"key": f"gateway_key_saved_{var_name}"}, {"_id": 0})
        saved = (doc or {}).get("value", "") or _os.environ.get(var_name, "")
        if not saved:
            raise HTTPException(400, f"No saved key for {var_name} — push the key first via POST /admin/gateway/keys")
        setattr(_gw, var_name, saved)
        _os.environ[var_name] = saved
    await audit(user.id, "gateway.key.toggled", meta={"var": var_name, "enabled": enabled})
    logger.info("Gateway key %s %s by exec", var_name, "enabled" if enabled else "disabled")
    return {"ok": True, "var": var_name, "enabled": enabled}


@router.patch("/admin/gateway/budget")
async def set_gateway_budget(body: dict, user: User = Depends(require_role("executive_admin"))):
    import ai.llm_gateway as _gw
    cap = body.get("hourly_cap")
    if not isinstance(cap, int) or cap < 1000:
        raise HTTPException(400, "hourly_cap must be an integer >= 1000")
    if cap > 10_000_000:
        raise HTTPException(400, "hourly_cap cannot exceed 10,000,000")
    _gw.HOURLY_TOKEN_CAP = cap
    await db.platform_config.update_one(
        {"key": "gateway_hourly_cap"},
        {"$set": {"key": "gateway_hourly_cap", "value": cap}},
        upsert=True,
    )
    await audit(user.id, "gateway.budget.updated", meta={"hourly_cap": cap})
    logger.info("Gateway hourly_cap set to %d by exec", cap)
    return {"ok": True, "hourly_cap": cap}


@router.post("/admin/gateway/reset-budget")
async def reset_gateway_budget(user: User = Depends(require_role("executive_admin"))):
    import ai.llm_gateway as _gw
    prev = _gw._hour_tokens_used
    _gw._hour_tokens_used = 0
    _gw._hour_window_start = 0.0
    await audit(user.id, "gateway.budget.reset", meta={"previous_tokens_used": prev})
    logger.info("Gateway hourly token counter reset by exec (was %d)", prev)
    return {"ok": True, "previous_tokens_used": prev}


_PROVIDER_RANKING_KEY = "gateway_provider_ranking"
_DEFAULT_PROVIDER_RANKING = [
    "groq", "cerebras", "gemini", "grok", "cohere", "openrouter", "huggingface", "anthropic",
]


@router.get("/admin/gateway/ranking")
async def get_gateway_ranking(user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_config.find_one({"key": _PROVIDER_RANKING_KEY}, {"_id": 0})
    ranking = (doc or {}).get("value", _DEFAULT_PROVIDER_RANKING)
    return {"ranking": ranking, "default": _DEFAULT_PROVIDER_RANKING}


@router.patch("/admin/gateway/ranking")
async def set_gateway_ranking(body: dict, user: User = Depends(require_role("executive_admin"))):
    ranking = body.get("ranking", [])
    valid = set(_DEFAULT_PROVIDER_RANKING)
    if not isinstance(ranking, list) or set(ranking) != valid:
        raise HTTPException(400, f"ranking must be a list containing exactly: {sorted(valid)}")
    await db.platform_config.update_one(
        {"key": _PROVIDER_RANKING_KEY},
        {"$set": {"key": _PROVIDER_RANKING_KEY, "value": ranking}},
        upsert=True,
    )
    await audit(user.id, "gateway.ranking.updated", meta={"ranking": ranking})
    return {"ok": True, "ranking": ranking}


@router.get("/admin/gateway/status")
async def admin_gateway_status(user: User = Depends(require_role("admin"))):
    from ai.llm_gateway import gateway_status
    return gateway_status()


# ── Prices ────────────────────────────────────────────────────────────────────

@router.get("/admin/prices")
async def list_prices(user: User = Depends(require_role("admin"))):
    docs = await db.platform_prices.find({}, {"_id": 0}).sort("key", 1).to_list(length=500)
    return {"prices": docs}


@router.post("/admin/prices")
async def create_price(body: dict, user: User = Depends(require_role("admin"))):
    key   = (body.get("key") or "").strip()
    value = body.get("value")
    desc  = (body.get("description") or "").strip()
    if not key:
        raise HTTPException(400, "key is required")
    if value is None:
        raise HTTPException(400, "value is required")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "value must be a number")
    existing = await db.platform_prices.find_one({"key": key})
    if existing:
        raise HTTPException(409, f"Price key '{key}' already exists — use PATCH to update")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "key": key,
        "value": value,
        "description": desc,
        "last_modified_by": user.id,
        "last_modified_at": now,
    }
    await db.platform_prices.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_create", "actor": user.id,
        "detail": f"Created price key={key} value={value}", "at": now,
    })
    return {k: v for k, v in doc.items() if k != "_id"}


@router.patch("/admin/prices/{price_id}")
async def update_price(price_id: str, body: dict, user: User = Depends(require_role("admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    updates: dict = {}
    if "value" in body:
        try:
            updates["value"] = float(body["value"])
        except (TypeError, ValueError):
            raise HTTPException(400, "value must be a number")
    if "description" in body:
        updates["description"] = (body["description"] or "").strip()
    if "key" in body:
        new_key = (body["key"] or "").strip()
        if not new_key:
            raise HTTPException(400, "key cannot be empty")
        conflict = await db.platform_prices.find_one({"key": new_key, "id": {"$ne": price_id}})
        if conflict:
            raise HTTPException(409, f"Key '{new_key}' already in use")
        updates["key"] = new_key
    if not updates:
        raise HTTPException(400, "No fields to update")
    now = datetime.now(timezone.utc).isoformat()
    updates["last_modified_by"] = user.id
    updates["last_modified_at"] = now
    await db.platform_prices.update_one({"id": price_id}, {"$set": updates})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_update", "actor": user.id,
        "detail": f"Updated price id={price_id} fields={list(updates.keys())}", "at": now,
    })
    updated = await db.platform_prices.find_one({"id": price_id}, {"_id": 0})
    return updated


@router.delete("/admin/prices/{price_id}")
async def delete_price(price_id: str, user: User = Depends(require_role("executive_admin"))):
    doc = await db.platform_prices.find_one({"id": price_id})
    if not doc:
        raise HTTPException(404, "Price not found")
    await db.platform_prices.delete_one({"id": price_id})
    now = datetime.now(timezone.utc).isoformat()
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "action": "price_delete", "actor": user.id,
        "detail": f"Deleted price key={doc.get('key')} id={price_id}", "at": now,
    })
    return {"deleted": price_id}
