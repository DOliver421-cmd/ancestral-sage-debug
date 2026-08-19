"""
exec_control — Executive Governance — site control panel, AI spend budgets, exec control layer (roles, tiers, flags, prices, budgets, provider ranking, IP whitelist, MFA, failover, break-glass).

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

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['exec', 'control'])


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


from routers.payments import GUMROAD_API_KEY, LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES
# ── Site Control Panel — executive_admin only ─────────────────────────────────
# Single endpoint that pulls every real metric in one shot.
# No mocks. No estimates. Every number comes from the DB or payment provider.

@router.get("/admin/control-panel")
async def control_panel_data(user: User = Depends(_require_rank("executive_admin"))):
    """Full real-time site dashboard. executive_admin only."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    # ── Users ──────────────────────────────────────────────────────────────────
    user_total          = await db.users.count_documents({})
    user_active         = await db.users.count_documents({"is_active": {"$ne": False}})
    user_suspended      = await db.users.count_documents({"is_active": False})
    users_today         = await db.users.count_documents({"created_at": {"$gte": today_start}})
    users_this_month    = await db.users.count_documents({"created_at": {"$gte": month_start}})
    role_counts = {}
    for role in ["student", "instructor", "admin", "executive_admin"]:
        role_counts[role] = await db.users.count_documents({"role": role})

    # ── Revenue ────────────────────────────────────────────────────────────────
    # Payments this month
    month_payments = await db.payments.find(
        {"status": "paid", "created_at": {"$gte": month_start}},
        {"_id": 0, "amount_cents": 1, "product_key": 1, "created_at": 1}
    ).to_list(length=2000)
    revenue_month_cents = sum(p.get("amount_cents", 0) for p in month_payments)

    # Payments today
    today_payments = [p for p in month_payments if p.get("created_at", "") >= today_start]
    revenue_today_cents = sum(p.get("amount_cents", 0) for p in today_payments)

    # All-time
    all_payments = await db.payments.find({"status": "paid"}, {"_id": 0, "amount_cents": 1}).to_list(length=10000)
    revenue_alltime_cents = sum(p.get("amount_cents", 0) for p in all_payments)

    # Failed payments (invoices with no matching paid entry — logged via webhook)
    failed_payments_count = await db.payments.count_documents({"status": {"$in": ["failed", "unpaid"]}})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    canceled_subs = await db.subscriptions.count_documents({"status": "canceled"})

    # Creator economy
    creator_courses_total     = await db.creator_courses.count_documents({"status": {"$ne": "archived"}})
    creator_courses_published = await db.creator_courses.count_documents({"status": "published"})
    creator_earnings_pending  = await db.creator_earnings.aggregate([
        {"$match": {"payout_status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$creator_share_cents"}}},
    ]).to_list(1)
    pending_payout_cents = (creator_earnings_pending[0]["total"] if creator_earnings_pending else 0)
    creator_profiles_count = await db.creator_profiles.count_documents({})

    # Revenue by product key this month
    product_breakdown: dict = {}
    for p in month_payments:
        k = p.get("product_key", "unknown")
        product_breakdown[k] = product_breakdown.get(k, 0) + p.get("amount_cents", 0)

    # ── Payments status (Lemon Squeezy → Gumroad) ─────────────
    payments_mode = "disabled"
    if LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID:
        payments_mode = "lemon_squeezy"
    elif GUMROAD_API_KEY:
        payments_mode = "gumroad"

    # ── Platform flags ─────────────────────────────────────────────────────────
    flags_doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
    platform_flags = (flags_doc or {}).get("flags", {})

    # ── Curriculum & learning ──────────────────────────────────────────────────
    modules_total      = await db.modules.count_documents({})
    completions_total  = await db.progress.count_documents({"status": "completed"})
    completions_today  = await db.progress.count_documents({"status": "completed", "completed_at": {"$gte": today_start}})
    labs_pending       = await db.lab_submissions.count_documents({"status": "pending_review"})
    credentials_issued = await db.user_credentials.count_documents({})
    incidents_open     = await db.incidents.count_documents({"status": "open"})

    # ── AI spend ───────────────────────────────────────────────────────────────
    ai_usage = await db.ai_usage_log.find(
        {"created_at": {"$gte": month_start}},
        {"_id": 0, "cost_usd": 1, "provider": 1, "model": 1, "created_at": 1}
    ).to_list(length=5000)
    ai_spend_month = sum(float(r.get("cost_usd") or 0) for r in ai_usage)
    ai_spend_today  = sum(float(r.get("cost_usd") or 0) for r in ai_usage if r.get("created_at", "") >= today_start)
    ai_calls_month  = len(ai_usage)
    ai_by_provider: dict = {}
    for r in ai_usage:
        p = r.get("provider", "unknown")
        ai_by_provider[p] = round(ai_by_provider.get(p, 0) + float(r.get("cost_usd") or 0), 4)

    # ── M.O.R.E. community ────────────────────────────────────────────────────
    more_posts_total    = await db.more_posts.count_documents({})
    more_posts_today    = await db.more_posts.count_documents({"created_at": {"$gte": today_start}})
    more_needs_open     = await db.more_needs.count_documents({"status": {"$nin": ["resolved", "closed"]}})
    more_flags_pending  = await db.more_flags.count_documents({"status": "pending"})
    more_members        = await db.users.count_documents({"more_member": True})

    # ── Audit / governance ────────────────────────────────────────────────────
    audit_today = await db.audit_log.find(
        {"at": {"$gte": today_start}},
        {"_id": 0, "actor_id": 1, "action": 1, "at": 1}
    ).sort("at", -1).limit(50).to_list(50)
    audit_total_today = len(audit_today)
    governance_entries = await db.governance_log.count_documents({})

    # Recent failures / serious events from audit log (last 24h)
    yesterday = (now - timedelta(hours=24)).isoformat()
    failure_keywords = ["fail", "error", "denied", "locked", "suspend", "ban", "refund", "violation"]
    failure_pipeline = [
        {"$match": {"at": {"$gte": yesterday}, "$or": [{"action": {"$regex": k}} for k in failure_keywords]}},
        {"$sort": {"at": -1}},
        {"$limit": 30},
        {"$project": {"_id": 0, "actor_id": 1, "action": 1, "at": 1, "meta": 1}},
    ]
    recent_failures = await db.audit_log.aggregate(failure_pipeline).to_list(30)

    # ── Recent audit trail (last 20 actions) ─────────────────────────────────
    recent_audit = await db.audit_log.find(
        {}, {"_id": 0, "actor_id": 1, "action": 1, "at": 1, "target_id": 1}
    ).sort("at", -1).limit(20).to_list(20)

    # Enrich with actor names
    actor_ids = list({r["actor_id"] for r in recent_audit + recent_failures if r.get("actor_id")})
    actor_map = {}
    if actor_ids:
        async for u in db.users.find({"id": {"$in": actor_ids}}, {"_id": 0, "id": 1, "full_name": 1, "role": 1}):
            actor_map[u["id"]] = u
    for r in recent_audit + recent_failures:
        a = actor_map.get(r.get("actor_id"))
        r["actor_name"] = a["full_name"] if a else "system"
        r["actor_role"] = a["role"] if a else ""

    # ── Payment webhook health (proxy: last recorded payment) ────────────────
    last_payment = await db.payments.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", -1)])
    last_payment_at = last_payment["created_at"] if last_payment else None
    yesterday_iso = (now - timedelta(hours=24)).isoformat()
    payments_24h = await db.payments.count_documents({"created_at": {"$gte": yesterday_iso}})

    # ── AI monthly spend budget ────────────────────────────────────────────────
    budget_doc = await db.platform_config.find_one({"key": "ai_monthly_budget"}, {"_id": 0, "value": 1})
    ai_monthly_budget = float(budget_doc["value"]) if budget_doc else None

    # ── Broadcasts / announcements ─────────────────────────────────────────────
    active_broadcast = await db.broadcasts.find_one({"active": True}, {"_id": 0})

    # ── Pending refunds ────────────────────────────────────────────────────────
    pending_refunds = await db.wai_refunds.count_documents({"status": "pending"})
    pending_escalations = await db.escalations.count_documents({"status": {"$in": ["open", "pending"]}})

    return {
        "generated_at": now.isoformat(),
        "users": {
            "total": user_total, "active": user_active, "suspended": user_suspended,
            "new_today": users_today, "new_this_month": users_this_month,
            "by_role": role_counts,
        },
        "revenue": {
            "today_cents": revenue_today_cents,
            "month_cents": revenue_month_cents,
            "alltime_cents": revenue_alltime_cents,
            "failed_payments": failed_payments_count,
            "active_subscriptions": active_subs,
            "canceled_subscriptions": canceled_subs,
            "by_product_month": product_breakdown,
            "pending_creator_payouts_cents": pending_payout_cents,
        },
        "payments": {
            "mode": payments_mode,
            "provider": payments_mode,
            "balance": None,
        },
        "platform_flags": platform_flags,
        "creator_economy": {
            "courses_total": creator_courses_total,
            "courses_published": creator_courses_published,
            "creator_profiles": creator_profiles_count,
        },
        "learning": {
            "modules": modules_total,
            "completions_total": completions_total,
            "completions_today": completions_today,
            "labs_pending_review": labs_pending,
            "credentials_issued": credentials_issued,
            "incidents_open": incidents_open,
        },
        "ai_spend": {
            "month_usd": round(ai_spend_month, 4),
            "today_usd": round(ai_spend_today, 4),
            "calls_this_month": ai_calls_month,
            "by_provider": ai_by_provider,
            "monthly_budget_usd": ai_monthly_budget,
        },
        "community": {
            "more_members": more_members,
            "posts_total": more_posts_total,
            "posts_today": more_posts_today,
            "needs_open": more_needs_open,
            "flags_pending": more_flags_pending,
        },
        "governance": {
            "audit_events_today": audit_total_today,
            "governance_log_entries": governance_entries,
            "pending_refunds": pending_refunds,
            "pending_escalations": pending_escalations,
        },
        "webhook_health": {
            "last_payment_at": last_payment_at,
            "payments_24h": payments_24h,
        },
        "recent_failures": recent_failures,
        "recent_audit": recent_audit,
        "active_broadcast": active_broadcast,
    }


@router.post("/admin/ai-spend-budget")
async def admin_set_ai_spend_budget(
    payload: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Set or clear the monthly AI spend budget alert threshold (USD). executive_admin only.
    Body: { budget_usd: float|null }
    """
    raw = payload.get("budget_usd")
    if raw is None:
        await db.platform_config.delete_one({"key": "ai_monthly_budget"})
        await audit(user.id, "admin.ai_budget.cleared")
        return {"budget_usd": None}
    try:
        val = float(raw)
        if val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(400, "budget_usd must be a positive number")
    await db.platform_config.update_one(
        {"key": "ai_monthly_budget"},
        {"$set": {"key": "ai_monthly_budget", "value": val, "set_by": user.id, "set_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "admin.ai_budget.set", meta={"budget_usd": val})
    return {"budget_usd": val}


@router.post("/admin/control-panel/broadcast")
async def control_panel_set_broadcast(
    payload: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Set or clear the site-wide broadcast banner. executive_admin only.
    Body: { message: str, kind: 'info'|'warning'|'error', active: bool }
    """
    message = (payload.get("message") or "").strip()
    kind = payload.get("kind", "info")
    active = bool(payload.get("active", True))
    if kind not in ("info", "warning", "error"):
        raise HTTPException(400, "kind must be info, warning, or error")
    now_iso = datetime.now(timezone.utc).isoformat()
    if active and not message:
        raise HTTPException(400, "message is required when active=true")
    await db.broadcasts.update_one(
        {"_id": "site_banner"},
        {"$set": {
            "active": active,
            "message": message,
            "kind": kind,
            "set_by": user.id,
            "updated_at": now_iso,
        }},
        upsert=True,
    )
    await audit(user.id, f"broadcast:{'set' if active else 'cleared'}", meta={"message": message[:100], "kind": kind})
    return {"active": active, "message": message, "kind": kind}


# ═══════════════════════════════════════════════════════════════════════════════
#  EXECUTIVE CONTROL LAYER  —  /api/exec/control/*
#  Ported from dead app/routes/executive_control.py into the live server.
#  All endpoints require executive_admin unless noted. All writes are audited.
# ═══════════════════════════════════════════════════════════════════════════════

class _ExecSetUserRoleReq(BaseModel):
    user_id:  str
    new_role: Literal["student", "trial_pass", "instructor", "support_staff",
                      "oversight", "admin", "executive_admin"]
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecSetUserTierReq(BaseModel):
    user_id:          str
    new_feature_tier: str = Field(..., min_length=1, max_length=64)  # exec can define custom tiers
    new_sage_tier:    Optional[Literal["basic", "advanced"]] = None
    reason:           str = Field(..., min_length=1, max_length=500)

class _ExecTierDefReq(BaseModel):
    tier_id:     str   = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    label:       str   = Field(..., min_length=1, max_length=100)
    rank:        int   = Field(..., ge=0, le=100)   # higher = more access
    description: str   = ""
    color:       str   = "#b5651d"                 # hex for UI badge
    price_hint:  str   = ""                        # e.g. "$9/mo" for display

class _ExecFeatureFlagReq(BaseModel):
    flag_name: str  = Field(..., min_length=1, max_length=200)
    enabled:   bool
    scope:     Literal["platform", "user"] = "platform"
    user_id:   Optional[str] = None
    reason:    str  = Field(..., min_length=1, max_length=500)

class _ExecAIAccessReq(BaseModel):
    user_id: str
    persona: str
    enabled: bool
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecLegalAccessReq(BaseModel):
    user_id:  str
    tool_key: Literal["legal_guide_1", "legal_guide_2", "all"]
    enabled:  bool
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecPriceReq(BaseModel):
    price_id:     str
    amount_cents: int = Field(..., ge=0)
    label:        Optional[str] = None
    reason:       str = Field(..., min_length=1, max_length=500)

class _ExecBudgetReq(BaseModel):
    budget_key: str
    limit:      float = Field(..., ge=0)
    reason:     str   = Field(..., min_length=1, max_length=500)

class _ExecProviderRankingReq(BaseModel):
    service: str
    ranking: List[str]
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecIPWhitelistReq(BaseModel):
    action: Literal["add", "remove"]
    ip:     str
    label:  Optional[str] = None
    role:   Literal["executive_admin", "admin"] = "executive_admin"
    reason: str = Field(..., min_length=1, max_length=500)

class _ExecMFAReq(BaseModel):
    require_mfa_for_roles: List[str]
    totp_enabled:          bool = True
    backup_codes_enabled:  bool = True
    reason:                str  = Field(..., min_length=1, max_length=500)

class _ExecFailoverReq(BaseModel):
    service:  str
    provider: str
    enabled:  bool
    reason:   str = Field(..., min_length=1, max_length=500)

class _ExecPageModeReq(BaseModel):
    page:   str
    mode:   str
    reason: str = Field(..., min_length=1, max_length=500)

class _ExecVisibilityReq(BaseModel):
    flag:    str
    enabled: bool
    reason:  str = Field(..., min_length=1, max_length=500)

class _ExecSageCapReq(BaseModel):
    user_id:   str
    sage_tier: Literal["basic", "advanced"]
    cap_level: Optional[Literal["general", "exploratory", "advanced"]] = None
    reason:    str = Field(..., min_length=1, max_length=500)

class _BreakGlassActivateReq(BaseModel):
    reason:           str = Field(..., min_length=20)
    scope:            str
    target_uid:       Optional[str] = None
    duration_minutes: int = Field(default=60, ge=5, le=480)

class _BreakGlassRevokeReq(BaseModel):
    override_id: str
    reason:      Optional[str] = None


async def _exec_audit(actor: User, action: str, target_id: Optional[str] = None,
                      before: Optional[dict] = None, after: Optional[dict] = None,
                      request: Optional[Request] = None, note: str = ""):
    ip = None
    if request:
        fwd = request.headers.get("x-forwarded-for", "")
        ip  = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else None)
    await db.exec_audit_log.insert_one({
        "id": str(uuid.uuid4()), "actor_id": actor.id, "actor_role": actor.role,
        "action": action, "target_id": target_id, "before": before, "after": after,
        "note": note, "ip": ip, "created_at": datetime.now(timezone.utc).isoformat(),
    })
    await audit(actor.id, action, target=target_id, meta={"note": note})


@router.post("/exec/control/user/role")
async def ec_set_user_role(body: _ExecSetUserRoleReq, request: Request,
                           actor: User = Depends(_require_rank("executive_admin"))):
    target = await db.users.find_one({"id": body.user_id}, {"_id": 0, "role": 1, "full_name": 1})
    if not target:
        raise HTTPException(404, "User not found")
    old_role = target.get("role", "student")
    if ROLE_RANK.get(old_role, 0) >= ROLE_RANK.get("executive_admin", 4) and actor.id != body.user_id:
        raise HTTPException(403, "Cannot modify another executive_admin's role.")
    if actor.id == body.user_id and ROLE_RANK.get(body.new_role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(400, "Cannot demote your own account below admin.")
    await db.users.update_one({"id": body.user_id},
        {"$set": {"role": body.new_role, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await _exec_audit(actor, "exec.user.role_changed", target_id=body.user_id,
        before={"role": old_role}, after={"role": body.new_role}, request=request, note=body.reason)
    if body.user_id != actor.id:
        await notify(body.user_id, "Account Role Updated",
            f"Your account role has been updated to: {body.new_role}.", kind="info")
    return {"ok": True, "user_id": body.user_id, "old_role": old_role, "new_role": body.new_role}


@router.post("/exec/control/user/tier")
async def ec_set_user_tier(body: _ExecSetUserTierReq, request: Request,
                           actor: User = Depends(_require_rank("admin"))):
    target = await db.users.find_one({"id": body.user_id},
        {"_id": 0, "feature_tier": 1, "sage_tier": 1})
    if not target:
        raise HTTPException(404, "User not found")
    old_ft = target.get("feature_tier", "free")
    old_st = target.get("sage_tier", "basic")
    upd = {"feature_tier": body.new_feature_tier, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.new_sage_tier:
        upd["sage_tier"] = body.new_sage_tier
    await db.users.update_one({"id": body.user_id}, {"$set": upd})
    await _exec_audit(actor, "exec.user.tier_changed", target_id=body.user_id,
        before={"feature_tier": old_ft, "sage_tier": old_st}, after=upd,
        request=request, note=body.reason)
    await db.users.update_one(
        {"id": body.user_id},
        {"$set": {"feature_tier_source": "admin_override", "feature_tier_updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await notify(body.user_id, "Account Plan Updated",
        f"Your plan has been updated to {body.new_feature_tier}.", link="/profile", kind="success")
    return {"ok": True, "user_id": body.user_id,
            "old_feature_tier": old_ft, "new_feature_tier": body.new_feature_tier,
            "old_sage_tier": old_st, "new_sage_tier": body.new_sage_tier or old_st}


# ── Exec: list, create, edit, delete custom tier definitions ──────────────────
_BUILTIN_TIERS = [
    {"tier_id": "free",      "label": "Free",      "rank": 0, "description": "Default tier — community access",               "color": "#6b7280", "price_hint": "Free"},
    {"tier_id": "member",    "label": "Member",    "rank": 1, "description": "Full M.O.R.E. + AI Tutor + creator basics",      "color": "#3b82f6", "price_hint": "$9/mo"},
    {"tier_id": "plus",      "label": "Plus",      "rank": 2, "description": "Priority matching + expanded courses + studio",  "color": "#8b5cf6", "price_hint": "$15/mo"},
    {"tier_id": "pro",       "label": "Pro",       "rank": 3, "description": "Advanced courses, labs, full AI suite",          "color": "#b5651d", "price_hint": "$29/mo"},
    {"tier_id": "patron",    "label": "Patron",    "rank": 4, "description": "Founders circle + funds free access for others", "color": "#E8A51E", "price_hint": "$59/mo"},
    {"tier_id": "executive", "label": "Executive", "rank": 5, "description": "Admin-granted — all features unlocked",          "color": "#ef4444", "price_hint": "Admin grant"},
]

@router.get("/exec/control/tiers")
async def ec_list_tiers(actor: User = Depends(_require_rank("admin"))):
    custom = await db.tier_definitions.find({}, {"_id": 0}).to_list(100)
    return {"tiers": _BUILTIN_TIERS + custom}

@router.post("/exec/control/tiers")
async def ec_upsert_tier(body: _ExecTierDefReq, request: Request,
                         actor: User = Depends(_require_rank("executive_admin"))):
    builtin_ids = {t["tier_id"] for t in _BUILTIN_TIERS}
    if body.tier_id in builtin_ids:
        raise HTTPException(400, "Cannot overwrite a built-in tier via this endpoint")
    doc = body.model_dump()
    doc["created_by"] = actor.id
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.tier_definitions.update_one(
        {"tier_id": body.tier_id},
        {"$set": doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await _exec_audit(actor, "exec.tier_definition.upserted", request=request,
                      note=f"tier={body.tier_id} rank={body.rank}")
    return {"ok": True, "tier": doc}

@router.delete("/exec/control/tiers/{tier_id}")
async def ec_delete_tier(tier_id: str, request: Request,
                         actor: User = Depends(_require_rank("executive_admin"))):
    builtin_ids = {t["tier_id"] for t in _BUILTIN_TIERS}
    if tier_id in builtin_ids:
        raise HTTPException(400, "Cannot delete a built-in tier")
    result = await db.tier_definitions.delete_one({"tier_id": tier_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Tier not found")
    await _exec_audit(actor, "exec.tier_definition.deleted", request=request, note=f"tier={tier_id}")
    return {"ok": True}


@router.post("/exec/control/feature-flag")
async def ec_feature_flag(body: _ExecFeatureFlagReq, request: Request,
                          actor: User = Depends(_require_rank("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    if body.scope == "platform":
        await db.platform_flags.update_one({"_id": "flags"},
            {"$set": {f"flags.{body.flag_name}.enabled": body.enabled,
                      f"flags.{body.flag_name}.updated_by": actor.id,
                      f"flags.{body.flag_name}.updated_at": now_iso,
                      "updated_at": now_iso}}, upsert=True)
        await _exec_audit(actor, f"exec.platform_flag.{'enabled' if body.enabled else 'disabled'}",
            after={"flag": body.flag_name, "enabled": body.enabled}, request=request, note=body.reason)
    else:
        if not body.user_id:
            raise HTTPException(400, "user_id required for user-scoped flag")
        await db.user_feature_overrides.update_one({"user_id": body.user_id},
            {"$set": {f"flags.{body.flag_name}": body.enabled, "updated_at": now_iso}}, upsert=True)
        await _exec_audit(actor, f"exec.user_flag.{'enabled' if body.enabled else 'disabled'}",
            target_id=body.user_id, after={"flag": body.flag_name, "enabled": body.enabled},
            request=request, note=body.reason)
    return {"ok": True, "flag": body.flag_name, "enabled": body.enabled, "scope": body.scope}


@router.post("/exec/control/ai-access")
async def ec_ai_access(body: _ExecAIAccessReq, request: Request,
                       actor: User = Depends(_require_rank("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    if body.persona == "all":
        upd_field, upd_val = "ai_access_override", {"all": body.enabled}
    else:
        upd_field, upd_val = f"ai_access.{body.persona}", body.enabled
    await db.user_feature_overrides.update_one({"user_id": body.user_id},
        {"$set": {upd_field: upd_val, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.ai_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id, after={"persona": body.persona, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "persona": body.persona, "enabled": body.enabled}


@router.post("/exec/control/legal-access")
async def ec_legal_access(body: _ExecLegalAccessReq, request: Request,
                          actor: User = Depends(_require_rank("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    tools = ["legal_guide_1", "legal_guide_2"] if body.tool_key == "all" else [body.tool_key]
    for t in tools:
        await db.user_feature_overrides.update_one({"user_id": body.user_id},
            {"$set": {f"legal_access.{t}": body.enabled, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.legal_access.{'granted' if body.enabled else 'revoked'}",
        target_id=body.user_id, after={"tools": tools, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "tools": tools, "enabled": body.enabled}


@router.post("/exec/control/price")
async def ec_set_price(body: _ExecPriceReq, request: Request,
                       actor: User = Depends(_require_rank("executive_admin"))):
    old = await db.platform_prices.find_one({"id": body.price_id}, {"_id": 0})
    if not old:
        raise HTTPException(404, "Price record not found")
    await db.platform_prices.update_one({"id": body.price_id},
        {"$set": {"amount_cents": body.amount_cents, "label": body.label,
                  "updated_by": actor.id, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await _exec_audit(actor, "exec.price.updated", target_id=body.price_id,
        before={"amount_cents": old.get("amount_cents"), "label": old.get("label")},
        after={"amount_cents": body.amount_cents, "label": body.label},
        request=request, note=body.reason)
    return {"ok": True, "price_id": body.price_id, "new_amount_cents": body.amount_cents}


@router.post("/exec/control/budget")
async def ec_set_budget(body: _ExecBudgetReq, request: Request,
                        actor: User = Depends(_require_rank("executive_admin"))):
    old = await db.platform_budgets.find_one({"key": body.budget_key}, {"_id": 0, "limit": 1})
    await db.platform_budgets.update_one({"key": body.budget_key},
        {"$set": {"limit": body.limit, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.budget.updated", target_id=body.budget_key,
        before={"limit": (old or {}).get("limit")}, after={"limit": body.limit},
        request=request, note=body.reason)
    return {"ok": True, "budget_key": body.budget_key, "new_limit": body.limit}


@router.post("/exec/control/provider-ranking")
async def ec_provider_ranking(body: _ExecProviderRankingReq, request: Request,
                              actor: User = Depends(_require_rank("executive_admin"))):
    old = await db.provider_rankings.find_one({"service": body.service}, {"_id": 0, "ranking": 1})
    await db.provider_rankings.update_one({"service": body.service},
        {"$set": {"ranking": body.ranking, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.provider_ranking.updated", target_id=body.service,
        before={"ranking": (old or {}).get("ranking")}, after={"ranking": body.ranking},
        request=request, note=body.reason)
    return {"ok": True, "service": body.service, "new_ranking": body.ranking}


@router.post("/exec/control/ip-whitelist")
async def ec_ip_whitelist(body: _ExecIPWhitelistReq, request: Request,
                          actor: User = Depends(_require_rank("executive_admin"))):
    if body.action == "add":
        await db.ip_whitelist.update_one({"ip": body.ip, "role": body.role},
            {"$set": {"ip": body.ip, "role": body.role, "label": body.label,
                      "added_by": actor.id, "added_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    else:
        await db.ip_whitelist.delete_one({"ip": body.ip, "role": body.role})
    await _exec_audit(actor, f"exec.ip_whitelist.{'added' if body.action == 'add' else 'removed'}",
        after={"ip": body.ip, "role": body.role, "action": body.action},
        request=request, note=body.reason)
    return {"ok": True, "action": body.action, "ip": body.ip}


@router.post("/exec/control/mfa")
async def ec_mfa_config(body: _ExecMFAReq, request: Request,
                        actor: User = Depends(_require_rank("executive_admin"))):
    old = await db.mfa_config.find_one({"_id": "config"}, {"_id": 0}) or {}
    config = {"require_mfa_for_roles": body.require_mfa_for_roles,
               "totp_enabled": body.totp_enabled, "backup_codes_enabled": body.backup_codes_enabled,
               "updated_by": actor.id, "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.mfa_config.update_one({"_id": "config"}, {"$set": config}, upsert=True)
    await _exec_audit(actor, "exec.mfa_config.updated", before=old, after=config,
        request=request, note=body.reason)
    return {"ok": True, "config": config}


@router.post("/exec/control/failover")
async def ec_failover(body: _ExecFailoverReq, request: Request,
                      actor: User = Depends(_require_rank("executive_admin"))):
    await db.failover_config.update_one({"service": body.service, "provider": body.provider},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, f"exec.failover.{'enabled' if body.enabled else 'disabled'}",
        after={"service": body.service, "provider": body.provider, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "service": body.service, "provider": body.provider, "enabled": body.enabled}


@router.post("/exec/control/page-mode")
async def ec_page_mode(body: _ExecPageModeReq, request: Request,
                       actor: User = Depends(_require_rank("executive_admin"))):
    await db.page_modes.update_one({"page": body.page},
        {"$set": {"mode": body.mode, "updated_by": actor.id,
                  "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    await _exec_audit(actor, "exec.page_mode.updated",
        after={"page": body.page, "mode": body.mode}, request=request, note=body.reason)
    return {"ok": True, "page": body.page, "mode": body.mode}


@router.post("/exec/control/visibility")
async def ec_visibility(body: _ExecVisibilityReq, request: Request,
                        actor: User = Depends(_require_rank("executive_admin"))):
    now_iso = datetime.now(timezone.utc).isoformat()
    old = await db.visibility_flags.find_one({"flag": body.flag}, {"_id": 0, "enabled": 1})
    await db.visibility_flags.update_one({"flag": body.flag},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id, "updated_at": now_iso}}, upsert=True)
    await _exec_audit(actor, f"exec.visibility.{'shown' if body.enabled else 'hidden'}",
        before={"flag": body.flag, "enabled": (old or {}).get("enabled")},
        after={"flag": body.flag, "enabled": body.enabled}, request=request, note=body.reason)
    return {"ok": True, "flag": body.flag, "enabled": body.enabled}


@router.post("/exec/control/sage-cap")
async def ec_sage_cap(body: _ExecSageCapReq, request: Request,
                      actor: User = Depends(_require_rank("admin"))):
    old = await db.users.find_one({"id": body.user_id},
        {"_id": 0, "sage_tier": 1, "sage_safety_cap": 1})
    upd: dict = {"sage_tier": body.sage_tier, "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.cap_level is not None:
        upd["sage_safety_cap"] = body.cap_level
    await db.users.update_one({"id": body.user_id}, {"$set": upd})
    await _exec_audit(actor, "exec.sage_cap.updated", target_id=body.user_id,
        before=old, after=upd, request=request, note=body.reason)
    return {"ok": True, "user_id": body.user_id, "sage_tier": body.sage_tier, "cap_level": body.cap_level}


@router.get("/exec/control/state")
async def ec_get_state(actor: User = Depends(_require_rank("executive_admin"))):
    import asyncio as _aio
    flags, budgets, rankings, page_modes, vis_flags, ip_list, mfa_cfg, failover = await _aio.gather(
        db.platform_flags.find_one({"_id": "flags"}, {"_id": 0}),
        db.platform_budgets.find({}, {"_id": 0}).to_list(100),
        db.provider_rankings.find({}, {"_id": 0}).to_list(50),
        db.page_modes.find({}, {"_id": 0}).to_list(50),
        db.visibility_flags.find({}, {"_id": 0}).to_list(100),
        db.ip_whitelist.find({}, {"_id": 0}).to_list(500),
        db.mfa_config.find_one({"_id": "config"}, {"_id": 0}),
        db.failover_config.find({}, {"_id": 0}).to_list(50),
    )
    return {"platform_flags": flags or {}, "budgets": budgets, "provider_rankings": rankings,
            "page_modes": page_modes, "visibility_flags": vis_flags, "ip_whitelist": ip_list,
            "mfa_config": mfa_cfg, "failover_config": failover,
            "fetched_at": datetime.now(timezone.utc).isoformat()}


@router.get("/exec/control/audit")
async def ec_audit_log(limit: int = 50, actor_id: Optional[str] = None,
                       action: Optional[str] = None,
                       actor: User = Depends(_require_rank("executive_admin"))):
    limit = min(max(limit, 1), 200)
    q: dict = {}
    if actor_id: q["actor_id"] = actor_id
    if action:   q["action"]   = {"$regex": re.escape(action), "$options": "i"}
    records = await db.exec_audit_log.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"count": len(records), "records": records}


@router.post("/exec/control/break-glass/activate")
async def ec_break_glass_activate(body: _BreakGlassActivateReq, request: Request,
                                  actor: User = Depends(_require_rank("executive_admin"))):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=body.duration_minutes)
    override_id = str(uuid.uuid4())
    fwd = request.headers.get("x-forwarded-for", "")
    ip  = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    record = {"id": override_id, "actor_id": actor.id,
              "actor_email": getattr(actor, "email", "unknown"),
              "scope": body.scope, "target_uid": body.target_uid,
              "reason": body.reason, "duration_minutes": body.duration_minutes,
              "activated_at": now, "expires_at": expires_at,
              "revoked": False, "revoked_at": None, "revoked_reason": None,
              "ip": ip, "status": "active"}
    await db.break_glass_overrides.insert_one({**record, "_id": override_id})
    await _exec_audit(actor, "break_glass.activated", target_id=body.target_uid or "platform",
        after={"scope": body.scope, "duration_minutes": body.duration_minutes, "override_id": override_id},
        request=request, note=f"BREAK GLASS: {body.reason}")
    return {"override_id": override_id, "scope": body.scope, "target_uid": body.target_uid,
            "activated_at": now.isoformat(), "expires_at": expires_at.isoformat(),
            "duration_minutes": body.duration_minutes, "status": "active",
            "warning": "This override is time-bound and fully audited."}


@router.post("/exec/control/break-glass/revoke")
async def ec_break_glass_revoke(body: _BreakGlassRevokeReq, request: Request,
                                actor: User = Depends(_require_rank("executive_admin"))):
    doc = await db.break_glass_overrides.find_one({"id": body.override_id, "revoked": False}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Override not found or already revoked.")
    now = datetime.now(timezone.utc)
    await db.break_glass_overrides.update_one({"id": body.override_id},
        {"$set": {"revoked": True, "revoked_at": now, "revoked_reason": body.reason, "status": "revoked"}})
    await _exec_audit(actor, "break_glass.revoked", target_id=doc.get("target_uid") or "platform",
        before={"status": "active"}, after={"status": "revoked", "reason": body.reason},
        request=request, note=f"BREAK GLASS REVOKED: {body.override_id}")
    return {"override_id": body.override_id, "revoked_at": now.isoformat(), "status": "revoked"}


@router.get("/exec/control/break-glass/active")
async def ec_break_glass_active(actor: User = Depends(_require_rank("executive_admin"))):
    now = datetime.now(timezone.utc)
    docs = await db.break_glass_overrides.find(
        {"revoked": False, "expires_at": {"$gt": now}}, {"_id": 0}
    ).sort("activated_at", -1).to_list(100)
    return {"active_overrides": docs, "count": len(docs)}


@router.get("/exec/control/break-glass/history")
async def ec_break_glass_history(limit: int = 50,
                                 actor: User = Depends(_require_rank("executive_admin"))):
    limit = min(max(limit, 1), 200)
    docs = await db.break_glass_overrides.find({}, {"_id": 0}).sort("activated_at", -1).limit(limit).to_list(limit)
    return {"records": docs, "count": len(docs)}


# ═════════════════════════════════════════════════════════════════════════════
# Page & Feature Access Control — one place to see every app page and flip
# whether it is reachable. Exec-only to change; any signed-in user can read
# the public gate map (AppShell filters nav, App.js blocks disabled pages).
# ═════════════════════════════════════════════════════════════════════════════

PAGE_ACCESS_REGISTRY = [
    {"key": "dashboard", "label": "Dashboard", "path": "/dashboard"},
    {"key": "helper", "label": "Helper", "path": "/helper"},
    {"key": "ai", "label": "AI Tutor", "path": "/ai"},
    {"key": "palace", "label": "Palace", "path": "/palace"},
    {"key": "studio", "label": "Creator Studio", "path": "/studio"},
    {"key": "ghost-producer", "label": "Ghost Producer", "path": "/ghost-producer"},
    {"key": "band", "label": "Band", "path": "/band"},
    {"key": "playlist", "label": "Playlist Curation", "path": "/playlist"},
    {"key": "arcade", "label": "Arcade", "path": "/arcade"},
    {"key": "store", "label": "Store", "path": "/store"},
    {"key": "merch", "label": "Merch", "path": "/merch"},
    {"key": "aawab", "label": "AAWAB", "path": "/aawab"},
    {"key": "more", "label": "M.O.R.E. Hub", "path": "/more"},
    {"key": "legal-tools", "label": "Legal Tools", "path": "/more/litigation"},
    {"key": "classic-tools", "label": "Classic Tools", "path": "/classic-tools"},
    {"key": "business-office", "label": "Business Office", "path": "/business-office"},
    {"key": "partnership", "label": "Partnership", "path": "/partnership"},
    {"key": "creator-lounge", "label": "Creator Lounge", "path": "/creator-lounge"},
    {"key": "community", "label": "Community", "path": "/community"},
    {"key": "creators", "label": "Creators", "path": "/creators"},
    {"key": "courses", "label": "Courses", "path": "/courses"},
    {"key": "modules", "label": "Modules", "path": "/modules"},
    {"key": "labs", "label": "Labs", "path": "/labs"},
    {"key": "compliance", "label": "Compliance", "path": "/compliance"},
    {"key": "credentials", "label": "Credentials", "path": "/credentials"},
    {"key": "certificates", "label": "Certificates", "path": "/certificates"},
    {"key": "leaderboard", "label": "Leaderboard", "path": "/leaderboard"},
    {"key": "projects", "label": "Projects", "path": "/projects"},
    {"key": "byok", "label": "Bring Your Own Key", "path": "/byok"},
    {"key": "social", "label": "Social Publisher", "path": "/social"},
    {"key": "revenue", "label": "Revenue", "path": "/revenue"},
    {"key": "auditor", "label": "Auditor", "path": "/auditor"},
    {"key": "supervisor", "label": "Supervisor", "path": "/supervisor"},
    {"key": "council", "label": "Council", "path": "/council"},
    {"key": "elder-council", "label": "Elder Council", "path": "/elder-council"},
    {"key": "jamil", "label": "Jamil", "path": "/jamil"},
    {"key": "portfolio", "label": "Portfolio", "path": "/portfolio"},
    {"key": "arena", "label": "Arena (Exec)", "path": "/arena"},
    {"key": "admin", "label": "Administration", "path": "/admin"},
    {"key": "exec", "label": "Executive Suite", "path": "/admin/exec"},
    {"key": "team", "label": "Team Ops", "path": "/team"},
    {"key": "settings", "label": "Settings", "path": "/settings"},
    {"key": "profile", "label": "Profile", "path": "/profile"},
]


class _ExecAccessReq(BaseModel):
    page: str = Field(..., min_length=1, max_length=100)
    enabled: bool = True
    reason: str = Field("", max_length=500)


@router.get("/exec/control/access")
async def ec_access_list(actor: User = Depends(_require_rank("executive_admin"))):
    """Full page registry with current enabled state — the consolidated
    page/feature access board (one place, no hunting across panels)."""
    docs = await db.page_access.find({}, {"_id": 0}).to_list(500)
    state = {d["page"]: d for d in docs}
    pages = []
    for reg in PAGE_ACCESS_REGISTRY:
        d = state.get(reg["key"], {})
        pages.append({
            "key": reg["key"],
            "label": reg["label"],
            "path": reg["path"],
            "enabled": d.get("enabled", True),
            "updated_by": d.get("updated_by"),
            "updated_at": d.get("updated_at"),
        })
    return {"pages": pages, "fetched_at": datetime.now(timezone.utc).isoformat()}


@router.post("/exec/control/access")
async def ec_access_set(body: _ExecAccessReq, request: Request,
                        actor: User = Depends(_require_rank("executive_admin"))):
    if not any(r["key"] == body.page for r in PAGE_ACCESS_REGISTRY):
        raise HTTPException(400, f"Unknown page key '{body.page}'")
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.page_access.update_one({"page": body.page},
        {"$set": {"enabled": body.enabled, "updated_by": actor.id, "updated_at": now_iso}},
        upsert=True)
    await _exec_audit(actor, f"exec.page_access.{'enabled' if body.enabled else 'disabled'}",
        after={"page": body.page, "enabled": body.enabled},
        request=request, note=body.reason)
    return {"ok": True, "page": body.page, "enabled": body.enabled}


@router.get("/exec/control/access/public")
async def ec_access_public(user: User = Depends(_dep_current_user)):
    """Gate map for the frontend shell — {page_key: enabled}. Missing keys
    default to enabled (a gate is only closed when exec explicitly closes it)."""
    docs = await db.page_access.find({}, {"_id": 0, "page": 1, "enabled": 1}).to_list(500)
    pages = {d["page"]: d.get("enabled", True) for d in docs}
    return {"pages": pages}
