"""app/routes/executive_control.py — Executive control layer.

Allows Executive users (via the Executive Dashboard) to:
  - Change user roles and feature tiers
  - Enable/disable features and AI/persona access
  - Control legal tool access
  - Control audio/system controls
  - Edit prices, budgets, provider ranking, IP whitelist, MFA enforcement,
    failover controls, visibility flags, page modes

All changes are:
  - Persisted in the database
  - Immediately effective (no cache TTL issues — resolvers read live from DB)
  - Fully audited (actor, target, before/after values, timestamp, IP)

Requires: executive_admin role.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.security.rbac import ROLE_RANK, role_meets_minimum
from app.security.feature_tiers import (
    FEATURE_TIER_LEVELS,
    SAGE_TIER_MAP,
    TIER_MAP,
    build_capability_contract,
)
from app.utils.audit import audit, notify

logger = logging.getLogger("lcewai")
router = APIRouter()

_EXEC = require_role("executive_admin")
_ADMIN = require_role("admin")


# ── Helper: write a fully-attributed audit record ─────────────────────────────

async def _exec_audit(
    actor: User,
    action: str,
    target_id: Optional[str] = None,
    before: Optional[Dict] = None,
    after: Optional[Dict] = None,
    request: Optional[Request] = None,
    note: str = "",
):
    """Write an executive-level audit record with before/after diff."""
    ip = None
    if request:
        ip = request.client.host if request.client else None
    await db.exec_audit_log.insert_one({
        "id":        str(uuid.uuid4()),
        "actor_id":  actor.id,
        "actor_role": actor.role,
        "action":    action,
        "target_id": target_id,
        "before":    before,
        "after":     after,
        "note":      note,
        "ip":        ip,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(actor.id, action, target=target_id, meta={"note": note})


# ── Models ─────────────────────────────────────────────────────────────────────

class SetUserRoleReq(BaseModel):
    user_id: str
    new_role: Literal["student", "instructor", "admin", "executive_admin"]
    reason:   str = Field(..., min_length=1, max_length=500)


class SetUserTierReq(BaseModel):
    user_id: str
    new_feature_tier: Literal["free", "premium", "executive"]
    new_sage_tier:    Optional[Literal["basic", "advanced"]] = None
    reason:           str = Field(..., min_length=1, max_length=500)


class SetFeatureFlagReq(BaseModel):
    flag_name: str = Field(..., min_length=1, max_length=200)
    enabled:   bool
    scope:     Literal["platform", "user"] = "platform"
    user_id:   Optional[str] = None
    reason:    str = Field(..., min_length=1, max_length=500)


class SetAIAccessReq(BaseModel):
    user_id:   str
    persona:   str   # e.g. "director", "cipher", "all"
    enabled:   bool
    reason:    str = Field(..., min_length=1, max_length=500)


class SetPriceReq(BaseModel):
    price_id:    str
    amount_cents: int = Field(..., ge=0)
    label:       Optional[str] = None
    reason:      str = Field(..., min_length=1, max_length=500)


class SetBudgetReq(BaseModel):
    budget_key:   str   # e.g. "tts_monthly_chars", "llm_monthly_usd"
    limit:        float = Field(..., ge=0)
    reason:       str = Field(..., min_length=1, max_length=500)


class SetProviderRankingReq(BaseModel):
    service:  str  # e.g. "llm", "tts", "stt"
    ranking:  List[str]  # ordered list of provider names
    reason:   str = Field(..., min_length=1, max_length=500)


class SetIPWhitelistReq(BaseModel):
    action:  Literal["add", "remove"]
    ip:      str
    label:   Optional[str] = None
    role:    Literal["executive_admin", "admin"] = "executive_admin"
    reason:  str = Field(..., min_length=1, max_length=500)


class SetMFAConfigReq(BaseModel):
    require_mfa_for_roles: List[str]
    totp_enabled:          bool = True
    backup_codes_enabled:  bool = True
    reason:                str = Field(..., min_length=1, max_length=500)


class SetFailoverReq(BaseModel):
    service:       str   # e.g. "llm", "tts", "database"
    provider:      str
    enabled:       bool
    reason:        str = Field(..., min_length=1, max_length=500)


class SetPageModeReq(BaseModel):
    page:    str   # e.g. "home", "more", "dashboard"
    mode:    str   # e.g. "maintenance", "readonly", "normal"
    reason:  str = Field(..., min_length=1, max_length=500)


class SetVisibilityFlagReq(BaseModel):
    flag:    str   # e.g. "show_pricing", "show_legal_tools"
    enabled: bool
    reason:  str = Field(..., min_length=1, max_length=500)


class SetLegalToolAccessReq(BaseModel):
    user_id:    str
    tool_key:   Literal["legal_guide_1", "legal_guide_2", "all"]
    enabled:    bool
    reason:     str = Field(..., min_length=1, max_length=500)


class SetSageCapReq(BaseModel):
    user_id:   str
    sage_tier: Literal["basic", "advanced"]
    cap_level: Optional[Literal["general", "exploratory", "advanced"]] = None
    reason:    str = Field(..., min_length=1, max_length=500)


# ── User Role Control ──────────────────────────────────────────────────────────

@router.post("/exec/control/user/role")
async def exec_set_user_role(
    body: SetUserRoleReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Change a user's role. Executive only. Fully audited."""
    target = await db.users.find_one({"id": body.user_id}, {"_id": 0, "role": 1, "full_name": 1, "email": 1})
    if not target:
        raise HTTPException(404, "User not found")

    old_role = target.get("role", "student")

    # Executives can only modify users at the same or lower rank
    if ROLE_RANK.get(old_role, 0) >= ROLE_RANK.get("executive_admin", 4) and actor.id != body.user_id:
        raise HTTPException(403, "Cannot modify another executive_admin's role.")

    # Cannot demote yourself below admin while logged in
    if actor.id == body.user_id and ROLE_RANK.get(body.new_role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(400, "Cannot demote your own account below admin.")

    await db.users.update_one(
        {"id": body.user_id},
        {"$set": {"role": body.new_role, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    await _exec_audit(
        actor, "exec.user.role_changed", target_id=body.user_id,
        before={"role": old_role}, after={"role": body.new_role},
        request=request, note=body.reason,
    )

    if body.user_id != actor.id:
        await notify(
            body.user_id, "Account Role Updated",
            f"Your account role has been updated to: {body.new_role}.",
            kind="info",
        )

    return {"ok": True, "user_id": body.user_id, "old_role": old_role, "new_role": body.new_role}


# ── User Tier Control ──────────────────────────────────────────────────────────

@router.post("/exec/control/user/tier")
async def exec_set_user_tier(
    body: SetUserTierReq,
    request: Request,
    actor: User = Depends(_ADMIN),
):
    """Change a user's feature tier and optionally sage_tier. Admin+. Fully audited."""
    target = await db.users.find_one(
        {"id": body.user_id},
        {"_id": 0, "feature_tier": 1, "sage_tier": 1, "email": 1},
    )
    if not target:
        raise HTTPException(404, "User not found")

    old_feature_tier = target.get("feature_tier", "free")
    old_sage_tier    = target.get("sage_tier", "basic")

    update = {
        "feature_tier": body.new_feature_tier,
        "updated_at":   datetime.now(timezone.utc).isoformat(),
    }
    if body.new_sage_tier:
        update["sage_tier"] = body.new_sage_tier

    await db.users.update_one({"id": body.user_id}, {"$set": update})

    await _exec_audit(
        actor, "exec.user.tier_changed", target_id=body.user_id,
        before={"feature_tier": old_feature_tier, "sage_tier": old_sage_tier},
        after=update,
        request=request, note=body.reason,
    )

    await notify(
        body.user_id, "Account Plan Updated",
        f"Your plan has been updated to: {body.new_feature_tier.title()}.",
        link="/dashboard", kind="success",
    )

    return {
        "ok": True, "user_id": body.user_id,
        "old_feature_tier": old_feature_tier, "new_feature_tier": body.new_feature_tier,
        "old_sage_tier": old_sage_tier, "new_sage_tier": body.new_sage_tier or old_sage_tier,
    }


# ── Platform Feature Flag Control ──────────────────────────────────────────────

@router.post("/exec/control/feature-flag")
async def exec_set_feature_flag(
    body: SetFeatureFlagReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Enable or disable a platform-wide or per-user feature flag. Executive only."""
    now = datetime.now(timezone.utc).isoformat()

    if body.scope == "platform":
        old = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0}) or {}
        await db.platform_flags.update_one(
            {"_id": "flags"},
            {"$set": {f"flags.{body.flag_name}.enabled": body.enabled, "updated_at": now,
                      f"flags.{body.flag_name}.updated_by": actor.id,
                      f"flags.{body.flag_name}.updated_at": now}},
            upsert=True,
        )
        await _exec_audit(
            actor, f"exec.platform_flag.{'enabled' if body.enabled else 'disabled'}",
            before={"flag": body.flag_name, "enabled": old.get("flags", {}).get(body.flag_name, {}).get("enabled", None)},
            after={"flag": body.flag_name, "enabled": body.enabled},
            request=request, note=body.reason,
        )
    else:
        if not body.user_id:
            raise HTTPException(400, "user_id required for user-scoped flag")
        await db.user_feature_overrides.update_one(
            {"user_id": body.user_id},
            {"$set": {f"flags.{body.flag_name}": body.enabled, "updated_at": now}},
            upsert=True,
        )
        await _exec_audit(
            actor, f"exec.user_flag.{'enabled' if body.enabled else 'disabled'}",
            target_id=body.user_id,
            after={"flag": body.flag_name, "enabled": body.enabled},
            request=request, note=body.reason,
        )

    return {"ok": True, "flag": body.flag_name, "enabled": body.enabled, "scope": body.scope}


# ── AI / Persona Access Control ────────────────────────────────────────────────

@router.post("/exec/control/ai-access")
async def exec_set_ai_access(
    body: SetAIAccessReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Grant or revoke AI persona access for a specific user. Executive only."""
    now = datetime.now(timezone.utc).isoformat()

    if body.persona == "all":
        update_field = "ai_access_override"
        update_val   = {"all": body.enabled}
    else:
        update_field = f"ai_access.{body.persona}"
        update_val   = body.enabled

    await db.user_feature_overrides.update_one(
        {"user_id": body.user_id},
        {"$set": {update_field: update_val, "updated_at": now}},
        upsert=True,
    )
    await _exec_audit(
        actor, f"exec.ai_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id,
        after={"persona": body.persona, "enabled": body.enabled},
        request=request, note=body.reason,
    )
    return {"ok": True, "user_id": body.user_id, "persona": body.persona, "enabled": body.enabled}


# ── Legal Tool Access Control ──────────────────────────────────────────────────

@router.post("/exec/control/legal-access")
async def exec_set_legal_access(
    body: SetLegalToolAccessReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Grant or revoke legal tool access for a specific user. Executive only."""
    now = datetime.now(timezone.utc).isoformat()

    tools = ["legal_guide_1", "legal_guide_2"] if body.tool_key == "all" else [body.tool_key]
    for tool in tools:
        await db.user_feature_overrides.update_one(
            {"user_id": body.user_id},
            {"$set": {f"legal_access.{tool}": body.enabled, "updated_at": now}},
            upsert=True,
        )
    await _exec_audit(
        actor, f"exec.legal_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id,
        after={"tools": tools, "enabled": body.enabled},
        request=request, note=body.reason,
    )
    return {"ok": True, "user_id": body.user_id, "tools": tools, "enabled": body.enabled}


# ── Price Control ──────────────────────────────────────────────────────────────

@router.post("/exec/control/price")
async def exec_set_price(
    body: SetPriceReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Update a price entry. Executive only."""
    old = await db.platform_prices.find_one({"id": body.price_id}, {"_id": 0})
    if not old:
        raise HTTPException(404, "Price record not found")

    await db.platform_prices.update_one(
        {"id": body.price_id},
        {"$set": {"amount_cents": body.amount_cents, "label": body.label,
                  "updated_by": actor.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await _exec_audit(
        actor, "exec.price.updated", target_id=body.price_id,
        before={"amount_cents": old.get("amount_cents"), "label": old.get("label")},
        after={"amount_cents": body.amount_cents, "label": body.label},
        request=request, note=body.reason,
    )
    return {"ok": True, "price_id": body.price_id, "new_amount_cents": body.amount_cents}


# ── Budget Control ─────────────────────────────────────────────────────────────

@router.post("/exec/control/budget")
async def exec_set_budget(
    body: SetBudgetReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Update a spending budget limit (TTS chars, LLM USD, etc.). Executive only."""
    old = await db.platform_budgets.find_one({"key": body.budget_key}, {"_id": 0, "limit": 1})

    await db.platform_budgets.update_one(
        {"key": body.budget_key},
        {"$set": {"limit": body.limit, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await _exec_audit(
        actor, "exec.budget.updated", target_id=body.budget_key,
        before={"limit": (old or {}).get("limit")},
        after={"limit": body.limit},
        request=request, note=body.reason,
    )
    return {"ok": True, "budget_key": body.budget_key, "new_limit": body.limit}


# ── Provider Ranking ───────────────────────────────────────────────────────────

@router.post("/exec/control/provider-ranking")
async def exec_set_provider_ranking(
    body: SetProviderRankingReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Update the ordered provider preference list for a service. Executive only."""
    old = await db.provider_rankings.find_one({"service": body.service}, {"_id": 0, "ranking": 1})

    await db.provider_rankings.update_one(
        {"service": body.service},
        {"$set": {"ranking": body.ranking, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await _exec_audit(
        actor, "exec.provider_ranking.updated", target_id=body.service,
        before={"ranking": (old or {}).get("ranking")},
        after={"ranking": body.ranking},
        request=request, note=body.reason,
    )
    return {"ok": True, "service": body.service, "new_ranking": body.ranking}


# ── IP Whitelist Control ───────────────────────────────────────────────────────

@router.post("/exec/control/ip-whitelist")
async def exec_set_ip_whitelist(
    body: SetIPWhitelistReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Add or remove an IP from the executive access whitelist. Executive only."""
    if body.action == "add":
        await db.ip_whitelist.update_one(
            {"ip": body.ip, "role": body.role},
            {"$set": {"ip": body.ip, "role": body.role, "label": body.label,
                      "added_by": actor.id, "added_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        action_label = "added"
    else:
        await db.ip_whitelist.delete_one({"ip": body.ip, "role": body.role})
        action_label = "removed"

    await _exec_audit(
        actor, f"exec.ip_whitelist.{action_label}",
        after={"ip": body.ip, "role": body.role, "action": body.action},
        request=request, note=body.reason,
    )
    return {"ok": True, "action": body.action, "ip": body.ip}


# ── MFA Configuration ──────────────────────────────────────────────────────────

@router.post("/exec/control/mfa")
async def exec_set_mfa_config(
    body: SetMFAConfigReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Update MFA enforcement policy. Executive only."""
    old = await db.mfa_config.find_one({"_id": "config"}, {"_id": 0}) or {}

    config = {
        "require_mfa_for_roles": body.require_mfa_for_roles,
        "totp_enabled":          body.totp_enabled,
        "backup_codes_enabled":  body.backup_codes_enabled,
        "updated_by":            actor.id,
        "updated_at":            datetime.now(timezone.utc).isoformat(),
    }
    await db.mfa_config.update_one({"_id": "config"}, {"$set": config}, upsert=True)
    await _exec_audit(
        actor, "exec.mfa_config.updated",
        before=old, after=config,
        request=request, note=body.reason,
    )
    return {"ok": True, "config": config}


# ── Failover Control ───────────────────────────────────────────────────────────

@router.post("/exec/control/failover")
async def exec_set_failover(
    body: SetFailoverReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Enable or disable a failover provider for a service. Executive only."""
    await db.failover_config.update_one(
        {"service": body.service, "provider": body.provider},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await _exec_audit(
        actor, f"exec.failover.{'enabled' if body.enabled else 'disabled'}",
        after={"service": body.service, "provider": body.provider, "enabled": body.enabled},
        request=request, note=body.reason,
    )
    return {"ok": True, "service": body.service, "provider": body.provider, "enabled": body.enabled}


# ── Page Mode Control ──────────────────────────────────────────────────────────

@router.post("/exec/control/page-mode")
async def exec_set_page_mode(
    body: SetPageModeReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Set the display mode for a specific page. Executive only."""
    await db.page_modes.update_one(
        {"page": body.page},
        {"$set": {"mode": body.mode, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await _exec_audit(
        actor, "exec.page_mode.updated",
        after={"page": body.page, "mode": body.mode},
        request=request, note=body.reason,
    )
    return {"ok": True, "page": body.page, "mode": body.mode}


# ── Visibility Flag Control ────────────────────────────────────────────────────

@router.post("/exec/control/visibility")
async def exec_set_visibility(
    body: SetVisibilityFlagReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Enable or disable a UI visibility flag. Executive only."""
    now = datetime.now(timezone.utc).isoformat()
    old = await db.visibility_flags.find_one({"flag": body.flag}, {"_id": 0, "enabled": 1})

    await db.visibility_flags.update_one(
        {"flag": body.flag},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id, "updated_at": now}},
        upsert=True,
    )
    await _exec_audit(
        actor, f"exec.visibility.{'shown' if body.enabled else 'hidden'}",
        before={"flag": body.flag, "enabled": (old or {}).get("enabled")},
        after={"flag": body.flag, "enabled": body.enabled},
        request=request, note=body.reason,
    )
    return {"ok": True, "flag": body.flag, "enabled": body.enabled}


# ── Sage Cap Control ───────────────────────────────────────────────────────────

@router.post("/exec/control/sage-cap")
async def exec_set_sage_cap(
    body: SetSageCapReq,
    request: Request,
    actor: User = Depends(_ADMIN),
):
    """Update a user's Sage tier and safety cap. Admin+."""
    old = await db.users.find_one(
        {"id": body.user_id}, {"_id": 0, "sage_tier": 1, "sage_safety_cap": 1}
    )
    update: Dict[str, Any] = {
        "sage_tier":       body.sage_tier,
        "updated_at":      datetime.now(timezone.utc).isoformat(),
    }
    if body.cap_level is not None:
        update["sage_safety_cap"] = body.cap_level
    await db.users.update_one({"id": body.user_id}, {"$set": update})
    await _exec_audit(
        actor, "exec.sage_cap.updated", target_id=body.user_id,
        before=old, after=update,
        request=request, note=body.reason,
    )
    return {"ok": True, "user_id": body.user_id, "sage_tier": body.sage_tier, "cap_level": body.cap_level}


# ── Read current executive control state ──────────────────────────────────────

@router.get("/exec/control/state")
async def exec_get_control_state(actor: User = Depends(_EXEC)):
    """Return the full executive control state snapshot. Executive only."""
    import asyncio as _asyncio

    flags, budgets, rankings, page_modes, vis_flags, ip_list, mfa_cfg, failover = await _asyncio.gather(
        db.platform_flags.find_one({"_id": "flags"}, {"_id": 0}) or {},
        db.platform_budgets.find({}, {"_id": 0}).to_list(100),
        db.provider_rankings.find({}, {"_id": 0}).to_list(50),
        db.page_modes.find({}, {"_id": 0}).to_list(50),
        db.visibility_flags.find({}, {"_id": 0}).to_list(100),
        db.ip_whitelist.find({}, {"_id": 0}).to_list(500),
        db.mfa_config.find_one({"_id": "config"}, {"_id": 0}),
        db.failover_config.find({}, {"_id": 0}).to_list(50),
    )
    return {
        "platform_flags":    flags,
        "budgets":           budgets,
        "provider_rankings": rankings,
        "page_modes":        page_modes,
        "visibility_flags":  vis_flags,
        "ip_whitelist":      ip_list,
        "mfa_config":        mfa_cfg,
        "failover_config":   failover,
        "fetched_at":        datetime.now(timezone.utc).isoformat(),
    }


# ── Executive audit log ────────────────────────────────────────────────────────

@router.get("/exec/control/audit")
async def exec_control_audit(
    limit: int = 50,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    actor: User = Depends(_EXEC),
):
    """Return executive control audit log. Executive only."""
    limit = min(max(limit, 1), 200)
    query: Dict = {}
    if actor_id:
        query["actor_id"] = actor_id
    if action:
        query["action"] = {"$regex": action, "$options": "i"}

    cursor = db.exec_audit_log.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    records = await cursor.to_list(limit)
    return {"count": len(records), "records": records}


# ── Break-Glass Executive Override System ─────────────────────────────────────
# Time-bound, reason-logged, audited temporary bypass of standard restrictions.
# EXECUTIVE_ADMIN ONLY. Cannot be triggered by admin or below.

class BreakGlassActivateReq(BaseModel):
    reason: str = Field(..., min_length=20, description="Mandatory justification (min 20 chars)")
    scope: str  = Field(..., description="What this override covers (e.g. 'sage_pipeline', 'user_tier', 'legal_access')")
    target_uid: Optional[str] = Field(None, description="Specific user ID if user-scoped override")
    duration_minutes: int = Field(default=60, ge=5, le=480, description="Override duration in minutes (5–480)")


class BreakGlassRevokeReq(BaseModel):
    override_id: str
    reason: Optional[str] = None


@router.post("/exec/control/break-glass/activate")
async def break_glass_activate(
    body: BreakGlassActivateReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Activate a time-bound executive override (break-glass).

    - EXECUTIVE_ADMIN only
    - Mandatory justification required (min 20 chars)
    - Persisted with actor, scope, target, duration, timestamps
    - Every activation is immutably logged and immediately visible in audit
    - Override expires automatically after duration_minutes
    - Does NOT auto-apply restrictions — consuming code must check break_glass_overrides collection
    """
    now = datetime.now(timezone.utc)
    expires_at = datetime(
        now.year, now.month, now.day,
        now.hour, now.minute, now.second,
        tzinfo=timezone.utc,
    )
    from datetime import timedelta
    expires_at = now + timedelta(minutes=body.duration_minutes)

    override_id = str(uuid.uuid4())
    ip = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )

    record = {
        "id":               override_id,
        "actor_id":         actor.id,
        "actor_email":      getattr(actor, "email", "unknown"),
        "scope":            body.scope,
        "target_uid":       body.target_uid,
        "reason":           body.reason,
        "duration_minutes": body.duration_minutes,
        "activated_at":     now,
        "expires_at":       expires_at,
        "revoked":          False,
        "revoked_at":       None,
        "revoked_reason":   None,
        "ip":               ip,
        "status":           "active",
    }

    if db is not None:
        await db.break_glass_overrides.insert_one({**record, "_id": override_id})

    # Immutable audit log entry
    await _exec_audit(
        actor=actor,
        action="break_glass.activated",
        target_id=body.target_uid or "platform",
        before={},
        after={
            "scope":            body.scope,
            "duration_minutes": body.duration_minutes,
            "override_id":      override_id,
        },
        request=request,
        note=f"BREAK GLASS: {body.reason}",
    )

    logger.warning(
        "BREAK-GLASS ACTIVATED: actor=%s scope=%s target=%s duration=%dm override=%s",
        actor.id, body.scope, body.target_uid, body.duration_minutes, override_id,
    )

    return {
        "override_id":      override_id,
        "scope":            body.scope,
        "target_uid":       body.target_uid,
        "activated_at":     now.isoformat(),
        "expires_at":       expires_at.isoformat(),
        "duration_minutes": body.duration_minutes,
        "status":           "active",
        "warning":          "This override is time-bound and fully audited. Justify all actions taken under this override.",
    }


@router.post("/exec/control/break-glass/revoke")
async def break_glass_revoke(
    body: BreakGlassRevokeReq,
    request: Request,
    actor: User = Depends(_EXEC),
):
    """Immediately revoke an active break-glass override before it expires."""
    if db is None:
        raise HTTPException(503, detail={"error": "db_unavailable", "message": "Database not connected."})

    doc = await db.break_glass_overrides.find_one(
        {"id": body.override_id, "revoked": False},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(404, detail={"error": "not_found", "message": "Override not found or already revoked."})

    now = datetime.now(timezone.utc)
    await db.break_glass_overrides.update_one(
        {"id": body.override_id},
        {"$set": {
            "revoked":        True,
            "revoked_at":     now,
            "revoked_reason": body.reason,
            "status":         "revoked",
        }},
    )

    await _exec_audit(
        actor=actor,
        action="break_glass.revoked",
        target_id=doc.get("target_uid") or "platform",
        before={"status": "active", "scope": doc.get("scope")},
        after={"status": "revoked", "revoked_reason": body.reason},
        request=request,
        note=f"BREAK GLASS REVOKED: override_id={body.override_id}",
    )

    logger.warning(
        "BREAK-GLASS REVOKED: actor=%s override=%s reason=%s",
        actor.id, body.override_id, body.reason,
    )

    return {
        "override_id": body.override_id,
        "revoked_at":  now.isoformat(),
        "status":      "revoked",
    }


@router.get("/exec/control/break-glass/active")
async def break_glass_list_active(actor: User = Depends(_EXEC)):
    """List all currently active (non-expired, non-revoked) break-glass overrides."""
    now = datetime.now(timezone.utc)

    if db is None:
        return {"active_overrides": []}

    docs = await db.break_glass_overrides.find(
        {
            "revoked":    False,
            "expires_at": {"$gt": now},
        },
        {"_id": 0},
    ).sort("activated_at", -1).to_list(length=100)

    return {"active_overrides": docs, "count": len(docs)}


@router.get("/exec/control/break-glass/history")
async def break_glass_history(
    limit: int = 50,
    actor: User = Depends(_EXEC),
):
    """Full break-glass activation history (active + expired + revoked). Executive only."""
    limit = min(max(limit, 1), 200)

    if db is None:
        return {"records": [], "count": 0}

    docs = await db.break_glass_overrides.find(
        {}, {"_id": 0}
    ).sort("activated_at", -1).limit(limit).to_list(limit)

    return {"records": docs, "count": len(docs)}
