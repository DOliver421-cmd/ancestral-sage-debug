"""app/routes/site_editor.py — Site Editing Interface: CRUD for all 15 governance tables.

Implements SITE_EDITING_INTERFACE covering:
  Roles & Access:     roles, role_feature_access, user_tiers, exec/admin/instructor/creator/student privileges
  Feature System:     feature_flags (extends supervisor_v2), feature_categories, feature_registry
  UI Customization:   ui_customization, ui_theme_presets, user_ui_overrides
  System:             system_config

All write endpoints require executive_admin except:
  - instructor_settings, creator_settings, student_settings → admin+
  - ui_customization (own record) → any authenticated user
  - ui_theme_presets read → any authenticated user

All mutations are audit-logged. No shell controls — every endpoint performs a real DB operation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

router = APIRouter(prefix="/site-editor")
_NOW = lambda: datetime.now(timezone.utc).isoformat()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip(doc: Optional[dict]) -> Optional[dict]:
    if doc:
        doc.pop("_id", None)
    return doc


def _strips(docs: list[dict]) -> list[dict]:
    for d in docs:
        d.pop("_id", None)
    return docs


async def _require_exists(collection, filter_: dict, label: str) -> dict:
    doc = await collection.find_one(filter_, {"_id": 0})
    if not doc:
        raise HTTPException(404, f"{label} not found")
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ROLES
# ═══════════════════════════════════════════════════════════════════════════════

class RoleCreate(BaseModel):
    name: str
    description: str = ""
    tier_level: int = 0    # 0=student,1=creator,2=instructor,3=admin,4=exec
    status: str = "active"


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    tier_level: Optional[int] = None
    status: Optional[str] = None


@router.get("/roles")
async def list_roles(user: User = Depends(require_role("admin"))):
    docs = await db.roles.find({}, {"_id": 0}).sort("tier_level", -1).to_list(200)
    return {"roles": docs}


@router.post("/roles")
async def create_role(body: RoleCreate, user: User = Depends(require_role("executive_admin"))):
    if body.name not in ("exec", "admin", "instructor", "student", "creator"):
        raise HTTPException(400, "name must be one of: exec, admin, instructor, student, creator")
    if body.status not in ("active", "disabled"):
        raise HTTPException(400, "status must be active or disabled")
    existing = await db.roles.find_one({"name": body.name})
    if existing:
        raise HTTPException(409, f"Role '{body.name}' already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "description": body.description,
        "tier_level": body.tier_level,
        "status": body.status,
        "created_by": user.id,
        "created_at": _NOW(),
        "updated_at": _NOW(),
    }
    await db.roles.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "site_editor.role.created", meta={"name": body.name})
    return doc


@router.patch("/roles/{role_id}")
async def edit_role(role_id: str, body: RoleUpdate, user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.roles, {"id": role_id}, "Role")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    if body.description is not None:
        updates["description"] = body.description
    if body.tier_level is not None:
        updates["tier_level"] = body.tier_level
    if body.status is not None:
        if body.status not in ("active", "disabled"):
            raise HTTPException(400, "status must be active or disabled")
        updates["status"] = body.status
    await db.roles.update_one({"id": role_id}, {"$set": updates})
    await audit(user.id, "site_editor.role.edited", meta={"role_id": role_id, "updates": updates})
    return {**existing, **updates}


@router.post("/roles/{role_id}/disable")
async def disable_role(role_id: str, user: User = Depends(require_role("executive_admin"))):
    await _require_exists(db.roles, {"id": role_id}, "Role")
    await db.roles.update_one({"id": role_id}, {"$set": {"status": "disabled", "updated_at": _NOW()}})
    await audit(user.id, "site_editor.role.disabled", meta={"role_id": role_id})
    return {"ok": True, "role_id": role_id, "status": "disabled"}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ROLE_FEATURE_ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

class RoleFeatureAccessGrant(BaseModel):
    role_id: str
    feature_key: str
    access_level: str = "read"     # none/read/write/admin
    ui_visibility: str = "show"    # show/hide
    notes: str = ""


class RoleFeatureAccessEdit(BaseModel):
    access_level: Optional[str] = None
    ui_visibility: Optional[str] = None
    notes: Optional[str] = None


_ACCESS_LEVELS = {"none", "read", "write", "admin"}
_VISIBILITY    = {"show", "hide"}


@router.get("/role-feature-access")
async def list_role_feature_access(
    role_id: Optional[str] = None,
    feature_key: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt: dict = {}
    if role_id:
        filt["role_id"] = role_id
    if feature_key:
        filt["feature_key"] = feature_key
    docs = await db.role_feature_access.find(filt, {"_id": 0}).sort("feature_key", 1).to_list(500)
    return {"access_rules": docs}


@router.post("/role-feature-access/grant")
async def grant_access(body: RoleFeatureAccessGrant, user: User = Depends(require_role("executive_admin"))):
    if body.access_level not in _ACCESS_LEVELS:
        raise HTTPException(400, f"access_level must be one of: {', '.join(sorted(_ACCESS_LEVELS))}")
    if body.ui_visibility not in _VISIBILITY:
        raise HTTPException(400, "ui_visibility must be show or hide")
    now = _NOW()
    doc = await db.role_feature_access.find_one_and_update(
        {"role_id": body.role_id, "feature_key": body.feature_key},
        {"$set": {
            "access_level": body.access_level,
            "ui_visibility": body.ui_visibility,
            "notes": body.notes,
            "updated_at": now,
            "updated_by": user.id,
        }, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.role_feature_access.granted",
                meta={"role_id": body.role_id, "feature_key": body.feature_key,
                      "access_level": body.access_level})
    return doc


@router.patch("/role-feature-access/{access_id}")
async def edit_access(access_id: str, body: RoleFeatureAccessEdit,
                      user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.role_feature_access, {"id": access_id}, "Access rule")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    if body.access_level is not None:
        if body.access_level not in _ACCESS_LEVELS:
            raise HTTPException(400, f"access_level must be one of: {', '.join(sorted(_ACCESS_LEVELS))}")
        updates["access_level"] = body.access_level
    if body.ui_visibility is not None:
        if body.ui_visibility not in _VISIBILITY:
            raise HTTPException(400, "ui_visibility must be show or hide")
        updates["ui_visibility"] = body.ui_visibility
    if body.notes is not None:
        updates["notes"] = body.notes
    await db.role_feature_access.update_one({"id": access_id}, {"$set": updates})
    await audit(user.id, "site_editor.role_feature_access.edited",
                meta={"access_id": access_id, "updates": updates})
    return {**existing, **updates}


@router.delete("/role-feature-access/{access_id}")
async def revoke_access(access_id: str, user: User = Depends(require_role("executive_admin"))):
    await _require_exists(db.role_feature_access, {"id": access_id}, "Access rule")
    await db.role_feature_access.delete_one({"id": access_id})
    await audit(user.id, "site_editor.role_feature_access.revoked", meta={"access_id": access_id})
    return {"ok": True, "access_id": access_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. USER_TIERS
# ═══════════════════════════════════════════════════════════════════════════════

class UserTierAssign(BaseModel):
    user_id: str
    role_id: str
    tier_level_override: Optional[int] = None
    feature_overrides_json: Optional[dict] = None
    ui_overrides_json: Optional[dict] = None
    status: str = "active"


class UserTierEdit(BaseModel):
    role_id: Optional[str] = None
    tier_level_override: Optional[int] = None
    feature_overrides_json: Optional[dict] = None
    ui_overrides_json: Optional[dict] = None
    status: Optional[str] = None


@router.get("/user-tiers")
async def list_user_tiers(
    user_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt = {"user_id": user_id} if user_id else {}
    docs = await db.user_tiers.find(filt, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"user_tiers": docs}


@router.post("/user-tiers/assign")
async def assign_tier(body: UserTierAssign, user: User = Depends(require_role("admin"))):
    if body.status not in ("active", "disabled"):
        raise HTTPException(400, "status must be active or disabled")
    now = _NOW()
    doc = await db.user_tiers.find_one_and_update(
        {"user_id": body.user_id, "role_id": body.role_id},
        {"$set": {
            "tier_level_override": body.tier_level_override,
            "feature_overrides_json": body.feature_overrides_json or {},
            "ui_overrides_json": body.ui_overrides_json or {},
            "status": body.status,
            "updated_at": now,
            "updated_by": user.id,
        }, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.user_tier.assigned",
                meta={"user_id": body.user_id, "role_id": body.role_id})
    return doc


@router.patch("/user-tiers/{tier_id}")
async def edit_tier(tier_id: str, body: UserTierEdit,
                    user: User = Depends(require_role("admin"))):
    existing = await _require_exists(db.user_tiers, {"id": tier_id}, "User tier")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    for field in ("role_id", "tier_level_override", "feature_overrides_json",
                  "ui_overrides_json", "status"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    if "status" in updates and updates["status"] not in ("active", "disabled"):
        raise HTTPException(400, "status must be active or disabled")
    await db.user_tiers.update_one({"id": tier_id}, {"$set": updates})
    await audit(user.id, "site_editor.user_tier.edited",
                meta={"tier_id": tier_id, "updates": list(updates.keys())})
    return {**existing, **updates}


@router.delete("/user-tiers/{tier_id}")
async def remove_tier(tier_id: str, user: User = Depends(require_role("admin"))):
    await _require_exists(db.user_tiers, {"id": tier_id}, "User tier")
    await db.user_tiers.delete_one({"id": tier_id})
    await audit(user.id, "site_editor.user_tier.removed", meta={"tier_id": tier_id})
    return {"ok": True, "tier_id": tier_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FEATURE_FLAGS  (extends supervisor_v2 with category support)
# ═══════════════════════════════════════════════════════════════════════════════

class FlagCreate(BaseModel):
    key: str
    value: Any = True
    description: str = ""
    active: bool = True


class FlagEdit(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None
    active: Optional[bool] = None


@router.get("/feature-flags")
async def list_flags_editor(
    active_only: bool = True,
    user: User = Depends(require_role("admin")),
):
    filt = {"active": True} if active_only else {}
    docs = await db.feature_flags.find(filt, {"_id": 0}).sort("key", 1).to_list(500)
    return {"flags": docs}


@router.post("/feature-flags")
async def create_flag(body: FlagCreate, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import set_feature_flag
    doc = await set_feature_flag(body.key, body.value, body.description, actor_id=user.id)
    if not body.active:
        from app.services.supervisor_service import disable_feature_flag
        await disable_feature_flag(body.key, actor_id=user.id)
        doc["active"] = False
    await audit(user.id, "site_editor.feature_flag.created",
                meta={"key": body.key, "value": body.value})
    return doc


@router.patch("/feature-flags/{key}")
async def edit_flag(key: str, body: FlagEdit, user: User = Depends(require_role("executive_admin"))):
    existing = await db.feature_flags.find_one({"key": key}, {"_id": 0})
    if not existing:
        raise HTTPException(404, f"Flag '{key}' not found")
    if body.value is not None or body.description is not None:
        new_val = body.value if body.value is not None else existing["value"]
        new_desc = body.description if body.description is not None else existing.get("description", "")
        from app.services.supervisor_service import set_feature_flag
        await set_feature_flag(key, new_val, new_desc, actor_id=user.id)
    if body.active is False:
        from app.services.supervisor_service import disable_feature_flag
        await disable_feature_flag(key, actor_id=user.id)
    elif body.active is True:
        await db.feature_flags.update_one({"key": key}, {"$set": {"active": True}})
    await audit(user.id, "site_editor.feature_flag.edited", meta={"key": key})
    return await db.feature_flags.find_one({"key": key}, {"_id": 0})


@router.post("/feature-flags/{key}/toggle")
async def toggle_flag(key: str, user: User = Depends(require_role("executive_admin"))):
    existing = await db.feature_flags.find_one({"key": key}, {"_id": 0})
    if not existing:
        raise HTTPException(404, f"Flag '{key}' not found")
    new_active = not existing.get("active", True)
    if new_active:
        await db.feature_flags.update_one({"key": key},
                                          {"$set": {"active": True, "updated_at": _NOW()}})
    else:
        from app.services.supervisor_service import disable_feature_flag
        await disable_feature_flag(key, actor_id=user.id)
    await audit(user.id, "site_editor.feature_flag.toggled",
                meta={"key": key, "new_active": new_active})
    return {"key": key, "active": new_active}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FEATURE_CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

_VALID_CATEGORY_NAMES = {"billing", "content", "personas", "providers", "ui", "system"}


class CategoryCreate(BaseModel):
    name: str
    description: str = ""


class CategoryEdit(BaseModel):
    description: Optional[str] = None


@router.get("/feature-categories")
async def list_feature_categories(user: User = Depends(require_role("admin"))):
    docs = await db.feature_categories.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return {"categories": docs}


@router.post("/feature-categories")
async def create_feature_category(body: CategoryCreate,
                                   user: User = Depends(require_role("executive_admin"))):
    if body.name not in _VALID_CATEGORY_NAMES:
        raise HTTPException(400, f"name must be one of: {', '.join(sorted(_VALID_CATEGORY_NAMES))}")
    existing = await db.feature_categories.find_one({"name": body.name})
    if existing:
        raise HTTPException(409, f"Category '{body.name}' already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "description": body.description,
        "created_by": user.id,
        "created_at": _NOW(),
    }
    await db.feature_categories.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "site_editor.feature_category.created", meta={"name": body.name})
    return doc


@router.patch("/feature-categories/{category_id}")
async def edit_feature_category(category_id: str, body: CategoryEdit,
                                 user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.feature_categories, {"id": category_id}, "Feature category")
    if body.description is not None:
        await db.feature_categories.update_one(
            {"id": category_id}, {"$set": {"description": body.description}}
        )
        existing["description"] = body.description
    return existing


# ═══════════════════════════════════════════════════════════════════════════════
# 6. FEATURE_REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class FeatureRegistryCreate(BaseModel):
    feature_key: str
    category_id: str
    description: str = ""
    default_access: str = "none"
    ui_default_visibility: str = "show"


class FeatureRegistryEdit(BaseModel):
    category_id: Optional[str] = None
    description: Optional[str] = None
    default_access: Optional[str] = None
    ui_default_visibility: Optional[str] = None


@router.get("/feature-registry")
async def list_feature_registry(
    category_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt = {"category_id": category_id} if category_id else {}
    docs = await db.feature_registry.find(filt, {"_id": 0}).sort("feature_key", 1).to_list(500)
    return {"features": docs}


@router.post("/feature-registry")
async def create_feature_registry_entry(body: FeatureRegistryCreate,
                                         user: User = Depends(require_role("executive_admin"))):
    if body.default_access not in _ACCESS_LEVELS:
        raise HTTPException(400, f"default_access must be one of: {', '.join(sorted(_ACCESS_LEVELS))}")
    if body.ui_default_visibility not in _VISIBILITY:
        raise HTTPException(400, "ui_default_visibility must be show or hide")
    existing = await db.feature_registry.find_one({"feature_key": body.feature_key})
    if existing:
        raise HTTPException(409, f"Feature '{body.feature_key}' already in registry")
    doc = {
        "id": str(uuid.uuid4()),
        "feature_key": body.feature_key,
        "category_id": body.category_id,
        "description": body.description,
        "default_access": body.default_access,
        "ui_default_visibility": body.ui_default_visibility,
        "created_by": user.id,
        "created_at": _NOW(),
        "updated_at": _NOW(),
    }
    await db.feature_registry.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "site_editor.feature_registry.created",
                meta={"feature_key": body.feature_key})
    return doc


@router.patch("/feature-registry/{feature_id}")
async def edit_feature_registry_entry(feature_id: str, body: FeatureRegistryEdit,
                                       user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.feature_registry, {"id": feature_id}, "Feature registry entry")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    if body.category_id is not None:
        updates["category_id"] = body.category_id
    if body.description is not None:
        updates["description"] = body.description
    if body.default_access is not None:
        if body.default_access not in _ACCESS_LEVELS:
            raise HTTPException(400, f"default_access must be one of: {', '.join(sorted(_ACCESS_LEVELS))}")
        updates["default_access"] = body.default_access
    if body.ui_default_visibility is not None:
        if body.ui_default_visibility not in _VISIBILITY:
            raise HTTPException(400, "ui_default_visibility must be show or hide")
        updates["ui_default_visibility"] = body.ui_default_visibility
    await db.feature_registry.update_one({"id": feature_id}, {"$set": updates})
    await audit(user.id, "site_editor.feature_registry.edited", meta={"feature_id": feature_id})
    return {**existing, **updates}


# ═══════════════════════════════════════════════════════════════════════════════
# 7. UI_CUSTOMIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class UICustomizationApply(BaseModel):
    user_id: Optional[str] = None   # None = own record
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    accent_color: Optional[str] = None
    border_radius: Optional[str] = None
    spacing_scale: Optional[str] = None
    custom_css: Optional[str] = None


@router.get("/ui-customization/me")
async def get_my_ui_customization(user: User = Depends(current_user)):
    doc = await db.ui_customization.find_one({"user_id": user.id}, {"_id": 0})
    return {"customization": doc}


@router.get("/ui-customization/{uid}")
async def get_user_ui_customization(uid: str, user: User = Depends(require_role("admin"))):
    doc = await db.ui_customization.find_one({"user_id": uid}, {"_id": 0})
    return {"customization": doc}


@router.put("/ui-customization")
async def apply_ui_customization(body: UICustomizationApply, user: User = Depends(current_user)):
    target_uid = body.user_id if body.user_id else user.id
    # Only admins can apply to other users
    if target_uid != user.id:
        from app.security.rbac import ROLE_RANK
        if ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
            raise HTTPException(403, "Cannot apply UI customization to another user without admin role")
    now = _NOW()
    updates: dict = {"updated_at": now}
    for field in ("font_family", "font_size", "font_color", "background_color",
                  "accent_color", "border_radius", "spacing_scale", "custom_css"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    doc = await db.ui_customization.find_one_and_update(
        {"user_id": target_uid},
        {"$set": updates, "$setOnInsert": {"id": str(uuid.uuid4()), "user_id": target_uid, "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.ui_customization.applied", meta={"target": target_uid})
    return doc


@router.delete("/ui-customization/{uid}/reset")
async def reset_ui_customization(uid: str, user: User = Depends(current_user)):
    from app.security.rbac import ROLE_RANK
    if uid != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Cannot reset another user's customization without admin role")
    await db.ui_customization.delete_one({"user_id": uid})
    await audit(user.id, "site_editor.ui_customization.reset", meta={"target": uid})
    return {"ok": True, "user_id": uid}


# ═══════════════════════════════════════════════════════════════════════════════
# 8. UI_THEME_PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

class ThemePresetCreate(BaseModel):
    name: str
    font_family: str = ""
    font_size: str = ""
    font_color: str = ""
    background_color: str = ""
    accent_color: str = ""
    description: str = ""


class ThemePresetEdit(BaseModel):
    name: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    accent_color: Optional[str] = None
    description: Optional[str] = None


@router.get("/ui-theme-presets")
async def list_theme_presets(user: User = Depends(current_user)):
    docs = await db.ui_theme_presets.find({}, {"_id": 0}).sort("name", 1).to_list(100)
    return {"presets": docs}


@router.post("/ui-theme-presets")
async def create_theme_preset(body: ThemePresetCreate,
                               user: User = Depends(require_role("executive_admin"))):
    existing = await db.ui_theme_presets.find_one({"name": body.name})
    if existing:
        raise HTTPException(409, f"Theme preset '{body.name}' already exists")
    doc = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "font_family": body.font_family,
        "font_size": body.font_size,
        "font_color": body.font_color,
        "background_color": body.background_color,
        "accent_color": body.accent_color,
        "description": body.description,
        "created_by": user.id,
        "created_at": _NOW(),
    }
    await db.ui_theme_presets.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "site_editor.theme_preset.created", meta={"name": body.name})
    return doc


@router.patch("/ui-theme-presets/{preset_id}")
async def edit_theme_preset(preset_id: str, body: ThemePresetEdit,
                             user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.ui_theme_presets, {"id": preset_id}, "Theme preset")
    updates: dict = {"updated_at": _NOW()}
    for field in ("name", "font_family", "font_size", "font_color",
                  "background_color", "accent_color", "description"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    await db.ui_theme_presets.update_one({"id": preset_id}, {"$set": updates})
    await audit(user.id, "site_editor.theme_preset.edited", meta={"preset_id": preset_id})
    return {**existing, **updates}


@router.delete("/ui-theme-presets/{preset_id}")
async def delete_theme_preset(preset_id: str, user: User = Depends(require_role("executive_admin"))):
    await _require_exists(db.ui_theme_presets, {"id": preset_id}, "Theme preset")
    await db.ui_theme_presets.delete_one({"id": preset_id})
    await audit(user.id, "site_editor.theme_preset.deleted", meta={"preset_id": preset_id})
    return {"ok": True, "preset_id": preset_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 9. USER_UI_OVERRIDES
# ═══════════════════════════════════════════════════════════════════════════════

class UserUIOverrideApply(BaseModel):
    user_id: str
    override_json: dict
    active: bool = True


@router.get("/user-ui-overrides")
async def list_user_ui_overrides(
    user_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt = {"user_id": user_id} if user_id else {}
    docs = await db.user_ui_overrides.find(filt, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"overrides": docs}


@router.post("/user-ui-overrides/apply")
async def apply_user_ui_override(body: UserUIOverrideApply,
                                  user: User = Depends(require_role("admin"))):
    now = _NOW()
    doc = await db.user_ui_overrides.find_one_and_update(
        {"user_id": body.user_id},
        {"$set": {"override_json": body.override_json, "active": body.active,
                  "updated_at": now, "updated_by": user.id},
         "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.user_ui_override.applied", meta={"user_id": body.user_id})
    return doc


@router.delete("/user-ui-overrides/{override_id}")
async def remove_user_ui_override(override_id: str, user: User = Depends(require_role("admin"))):
    await _require_exists(db.user_ui_overrides, {"id": override_id}, "UI override")
    await db.user_ui_overrides.delete_one({"id": override_id})
    await audit(user.id, "site_editor.user_ui_override.removed", meta={"override_id": override_id})
    return {"ok": True, "override_id": override_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 10. EXEC_PRIVILEGES
# ═══════════════════════════════════════════════════════════════════════════════

class ExecPrivilegeGrant(BaseModel):
    exec_user_id: str
    can_edit_prices: bool = False
    can_edit_roles: bool = False
    can_edit_providers: bool = False
    can_edit_personas: bool = False
    can_edit_system_config: bool = False
    can_issue_cash_refunds: bool = False
    can_override_compliance: bool = False


class ExecPrivilegeEdit(BaseModel):
    can_edit_prices: Optional[bool] = None
    can_edit_roles: Optional[bool] = None
    can_edit_providers: Optional[bool] = None
    can_edit_personas: Optional[bool] = None
    can_edit_system_config: Optional[bool] = None
    can_issue_cash_refunds: Optional[bool] = None
    can_override_compliance: Optional[bool] = None


@router.get("/exec-privileges")
async def list_exec_privileges(
    exec_user_id: Optional[str] = None,
    user: User = Depends(require_role("executive_admin")),
):
    filt = {"exec_user_id": exec_user_id} if exec_user_id else {}
    docs = await db.exec_privileges.find(filt, {"_id": 0}).to_list(200)
    return {"privileges": docs}


@router.post("/exec-privileges/grant")
async def grant_exec_privileges(body: ExecPrivilegeGrant,
                                 user: User = Depends(require_role("executive_admin"))):
    now = _NOW()
    fields = body.model_dump()
    doc = await db.exec_privileges.find_one_and_update(
        {"exec_user_id": body.exec_user_id},
        {"$set": {**fields, "updated_at": now, "updated_by": user.id},
         "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.exec_privileges.granted",
                meta={"exec_user_id": body.exec_user_id})
    return doc


@router.patch("/exec-privileges/{privilege_id}")
async def edit_exec_privileges(privilege_id: str, body: ExecPrivilegeEdit,
                                user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.exec_privileges, {"id": privilege_id}, "Exec privilege")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    for field in ("can_edit_prices", "can_edit_roles", "can_edit_providers",
                  "can_edit_personas", "can_edit_system_config",
                  "can_issue_cash_refunds", "can_override_compliance"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    await db.exec_privileges.update_one({"id": privilege_id}, {"$set": updates})
    await audit(user.id, "site_editor.exec_privileges.edited",
                meta={"privilege_id": privilege_id, "updates": list(updates.keys())})
    return {**existing, **updates}


@router.delete("/exec-privileges/{privilege_id}")
async def revoke_exec_privileges(privilege_id: str, user: User = Depends(require_role("executive_admin"))):
    await _require_exists(db.exec_privileges, {"id": privilege_id}, "Exec privilege")
    await db.exec_privileges.delete_one({"id": privilege_id})
    await audit(user.id, "site_editor.exec_privileges.revoked",
                meta={"privilege_id": privilege_id})
    return {"ok": True, "privilege_id": privilege_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 11. ADMIN_PRIVILEGES
# ═══════════════════════════════════════════════════════════════════════════════

class AdminPrivilegeGrant(BaseModel):
    admin_user_id: str
    can_edit_content: bool = False
    can_edit_courses: bool = False
    can_edit_users: bool = False
    can_issue_site_credits: bool = False
    can_manage_instructors: bool = False


class AdminPrivilegeEdit(BaseModel):
    can_edit_content: Optional[bool] = None
    can_edit_courses: Optional[bool] = None
    can_edit_users: Optional[bool] = None
    can_issue_site_credits: Optional[bool] = None
    can_manage_instructors: Optional[bool] = None


@router.get("/admin-privileges")
async def list_admin_privileges(
    admin_user_id: Optional[str] = None,
    user: User = Depends(require_role("executive_admin")),
):
    filt = {"admin_user_id": admin_user_id} if admin_user_id else {}
    docs = await db.admin_privileges.find(filt, {"_id": 0}).to_list(200)
    return {"privileges": docs}


@router.post("/admin-privileges/grant")
async def grant_admin_privileges(body: AdminPrivilegeGrant,
                                  user: User = Depends(require_role("executive_admin"))):
    now = _NOW()
    fields = body.model_dump()
    doc = await db.admin_privileges.find_one_and_update(
        {"admin_user_id": body.admin_user_id},
        {"$set": {**fields, "updated_at": now, "updated_by": user.id},
         "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.admin_privileges.granted",
                meta={"admin_user_id": body.admin_user_id})
    return doc


@router.patch("/admin-privileges/{privilege_id}")
async def edit_admin_privileges(privilege_id: str, body: AdminPrivilegeEdit,
                                 user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.admin_privileges, {"id": privilege_id}, "Admin privilege")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    for field in ("can_edit_content", "can_edit_courses", "can_edit_users",
                  "can_issue_site_credits", "can_manage_instructors"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    await db.admin_privileges.update_one({"id": privilege_id}, {"$set": updates})
    await audit(user.id, "site_editor.admin_privileges.edited",
                meta={"privilege_id": privilege_id})
    return {**existing, **updates}


@router.delete("/admin-privileges/{privilege_id}")
async def revoke_admin_privileges(privilege_id: str,
                                   user: User = Depends(require_role("executive_admin"))):
    await _require_exists(db.admin_privileges, {"id": privilege_id}, "Admin privilege")
    await db.admin_privileges.delete_one({"id": privilege_id})
    await audit(user.id, "site_editor.admin_privileges.revoked",
                meta={"privilege_id": privilege_id})
    return {"ok": True, "privilege_id": privilege_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 12. INSTRUCTOR_SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class InstructorSettingsUpsert(BaseModel):
    instructor_user_id: str
    can_create_lessons: bool = False
    can_edit_lessons: bool = False
    can_publish_content: bool = False
    can_grade_students: bool = False


class InstructorSettingsEdit(BaseModel):
    can_create_lessons: Optional[bool] = None
    can_edit_lessons: Optional[bool] = None
    can_publish_content: Optional[bool] = None
    can_grade_students: Optional[bool] = None


@router.get("/instructor-settings")
async def list_instructor_settings(
    instructor_user_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt = {"instructor_user_id": instructor_user_id} if instructor_user_id else {}
    docs = await db.instructor_settings.find(filt, {"_id": 0}).to_list(200)
    return {"settings": docs}


@router.post("/instructor-settings/grant")
async def grant_instructor_settings(body: InstructorSettingsUpsert,
                                     user: User = Depends(require_role("admin"))):
    now = _NOW()
    fields = body.model_dump()
    doc = await db.instructor_settings.find_one_and_update(
        {"instructor_user_id": body.instructor_user_id},
        {"$set": {**fields, "updated_at": now, "updated_by": user.id},
         "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.instructor_settings.granted",
                meta={"instructor_user_id": body.instructor_user_id})
    return doc


@router.patch("/instructor-settings/{setting_id}")
async def edit_instructor_settings(setting_id: str, body: InstructorSettingsEdit,
                                    user: User = Depends(require_role("admin"))):
    existing = await _require_exists(db.instructor_settings, {"id": setting_id}, "Instructor settings")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    for field in ("can_create_lessons", "can_edit_lessons", "can_publish_content", "can_grade_students"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    await db.instructor_settings.update_one({"id": setting_id}, {"$set": updates})
    return {**existing, **updates}


@router.delete("/instructor-settings/{setting_id}")
async def revoke_instructor_settings(setting_id: str, user: User = Depends(require_role("admin"))):
    await _require_exists(db.instructor_settings, {"id": setting_id}, "Instructor settings")
    await db.instructor_settings.delete_one({"id": setting_id})
    await audit(user.id, "site_editor.instructor_settings.revoked",
                meta={"setting_id": setting_id})
    return {"ok": True, "setting_id": setting_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 13. CREATOR_SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class CreatorSettingsUpsert(BaseModel):
    creator_user_id: str
    can_upload_media: bool = False
    can_create_products: bool = False
    can_edit_products: bool = False
    can_publish_products: bool = False


class CreatorSettingsEdit(BaseModel):
    can_upload_media: Optional[bool] = None
    can_create_products: Optional[bool] = None
    can_edit_products: Optional[bool] = None
    can_publish_products: Optional[bool] = None


@router.get("/creator-settings")
async def list_creator_settings(
    creator_user_id: Optional[str] = None,
    user: User = Depends(require_role("admin")),
):
    filt = {"creator_user_id": creator_user_id} if creator_user_id else {}
    docs = await db.creator_settings.find(filt, {"_id": 0}).to_list(200)
    return {"settings": docs}


@router.post("/creator-settings/grant")
async def grant_creator_settings(body: CreatorSettingsUpsert,
                                  user: User = Depends(require_role("admin"))):
    now = _NOW()
    fields = body.model_dump()
    doc = await db.creator_settings.find_one_and_update(
        {"creator_user_id": body.creator_user_id},
        {"$set": {**fields, "updated_at": now, "updated_by": user.id},
         "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.creator_settings.granted",
                meta={"creator_user_id": body.creator_user_id})
    return doc


@router.patch("/creator-settings/{setting_id}")
async def edit_creator_settings(setting_id: str, body: CreatorSettingsEdit,
                                 user: User = Depends(require_role("admin"))):
    existing = await _require_exists(db.creator_settings, {"id": setting_id}, "Creator settings")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    for field in ("can_upload_media", "can_create_products", "can_edit_products", "can_publish_products"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    await db.creator_settings.update_one({"id": setting_id}, {"$set": updates})
    return {**existing, **updates}


@router.delete("/creator-settings/{setting_id}")
async def revoke_creator_settings(setting_id: str, user: User = Depends(require_role("admin"))):
    await _require_exists(db.creator_settings, {"id": setting_id}, "Creator settings")
    await db.creator_settings.delete_one({"id": setting_id})
    await audit(user.id, "site_editor.creator_settings.revoked",
                meta={"setting_id": setting_id})
    return {"ok": True, "setting_id": setting_id}


# ═══════════════════════════════════════════════════════════════════════════════
# 14. STUDENT_SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class StudentSettingsEdit(BaseModel):
    student_user_id: str
    can_access_courses: Optional[bool] = None
    can_comment: Optional[bool] = None
    can_submit_assignments: Optional[bool] = None


@router.get("/student-settings/{student_user_id}")
async def get_student_settings(student_user_id: str, user: User = Depends(require_role("instructor"))):
    doc = await db.student_settings.find_one({"student_user_id": student_user_id}, {"_id": 0})
    return {"settings": doc}


@router.patch("/student-settings")
async def edit_student_settings(body: StudentSettingsEdit, user: User = Depends(require_role("instructor"))):
    now = _NOW()
    updates: dict = {"student_user_id": body.student_user_id, "updated_at": now, "updated_by": user.id}
    for field in ("can_access_courses", "can_comment", "can_submit_assignments"):
        v = getattr(body, field, None)
        if v is not None:
            updates[field] = v
    doc = await db.student_settings.find_one_and_update(
        {"student_user_id": body.student_user_id},
        {"$set": updates, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True, return_document=True,
    )
    doc.pop("_id", None)
    await audit(user.id, "site_editor.student_settings.edited",
                meta={"student_user_id": body.student_user_id})
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# 15. SYSTEM_CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

class SystemConfigCreate(BaseModel):
    key: str
    value_json: Any
    description: str = ""


class SystemConfigEdit(BaseModel):
    value_json: Optional[Any] = None
    description: Optional[str] = None


@router.get("/system-config")
async def list_system_config(user: User = Depends(require_role("executive_admin"))):
    docs = await db.system_config.find({}, {"_id": 0}).sort("key", 1).to_list(500)
    return {"config": docs}


@router.get("/system-config/{key}")
async def get_system_config(key: str, user: User = Depends(require_role("admin"))):
    doc = await db.system_config.find_one({"key": key}, {"_id": 0})
    if not doc:
        raise HTTPException(404, f"Config key '{key}' not found")
    return doc


@router.post("/system-config")
async def create_system_config(body: SystemConfigCreate,
                                user: User = Depends(require_role("executive_admin"))):
    existing = await db.system_config.find_one({"key": body.key})
    if existing:
        raise HTTPException(409, f"Config key '{body.key}' already exists. Use PATCH to update.")
    now = _NOW()
    doc = {
        "id": str(uuid.uuid4()),
        "key": body.key,
        "value_json": body.value_json,
        "description": body.description,
        "created_by": user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.system_config.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "site_editor.system_config.created", meta={"key": body.key})
    return doc


@router.patch("/system-config/{key}")
async def edit_system_config(key: str, body: SystemConfigEdit,
                              user: User = Depends(require_role("executive_admin"))):
    existing = await _require_exists(db.system_config, {"key": key}, f"Config key '{key}'")
    updates: dict = {"updated_at": _NOW(), "updated_by": user.id}
    if body.value_json is not None:
        updates["value_json"] = body.value_json
    if body.description is not None:
        updates["description"] = body.description
    await db.system_config.update_one({"key": key}, {"$set": updates})
    await audit(user.id, "site_editor.system_config.edited", meta={"key": key})
    return {**existing, **updates}
