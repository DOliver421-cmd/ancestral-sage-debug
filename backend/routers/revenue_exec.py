"""
revenue_exec — Revenue executive overview, creator revenue split tiers, provider test.

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
router = APIRouter(tags=['revenue', 'exec'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None


def bind(_db, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user
    
    db = _db
    current_user = _current_user


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


# ── Revenue Executive Overview ────────────────────────────────────────────────
# Single-call dashboard for executive revenue: monthly goal progress, product
# breakdown, per-creator pending payouts, AI spend, and subscription health.

@router.get("/revenue/exec-overview")
async def revenue_exec_overview(user: User = Depends(_require_rank("executive_admin"))):
    """Real-time executive revenue overview. executive_admin only."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    MONTHLY_GOAL_CENTS = 800_000  # $8,000

    # Platform revenue this month
    month_payments = await db.payments.find(
        {"status": "paid", "created_at": {"$gte": month_start}},
        {"_id": 0, "amount_cents": 1, "product_key": 1, "created_at": 1},
    ).to_list(length=5000)
    revenue_month_cents = sum(p.get("amount_cents", 0) for p in month_payments)
    revenue_today_cents = sum(p.get("amount_cents", 0) for p in month_payments if p.get("created_at", "") >= today_start)

    all_payments = await db.payments.find({"status": "paid"}, {"_id": 0, "amount_cents": 1}).to_list(length=20000)
    revenue_alltime_cents = sum(p.get("amount_cents", 0) for p in all_payments)

    # Product breakdown this month
    by_product: dict = {}
    for p in month_payments:
        k = p.get("product_key", "unknown")
        by_product[k] = by_product.get(k, 0) + p.get("amount_cents", 0)

    # Monthly trend — last 6 periods
    months_trend = []
    for i in range(5, -1, -1):
        target_date = now.replace(day=1) - timedelta(days=1) if i > 0 else now.replace(day=1)
        for _ in range(i):
            target_date = (target_date.replace(day=1) - timedelta(days=1))
        period_label = target_date.strftime("%Y-%m")
        period_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        if i == 0:
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = next_month.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        else:
            next_m = (target_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            period_end = next_m.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        total = await db.payments.aggregate([
            {"$match": {"status": "paid", "created_at": {"$gte": period_start, "$lt": period_end}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount_cents"}}},
        ]).to_list(1)
        months_trend.append({"period": period_label, "revenue_cents": total[0]["total"] if total else 0})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})
    canceled_subs = await db.subscriptions.count_documents({"status": "canceled"})

    # Creator payout details — all creators with pending earnings
    pending_pipeline = [
        {"$match": {"payout_status": "pending"}},
        {"$group": {"_id": "$creator_id", "pending_cents": {"$sum": "$creator_share_cents"}, "sales": {"$sum": 1}}},
        {"$sort": {"pending_cents": -1}},
    ]
    pending_by_creator = await db.creator_earnings.aggregate(pending_pipeline).to_list(200)
    total_pending_creator_cents = sum(c["pending_cents"] for c in pending_by_creator)

    # Enrich creator names and bank status
    creator_ids = [c["_id"] for c in pending_by_creator]
    creator_names: dict = {}
    if creator_ids:
        async for u in db.users.find({"id": {"$in": creator_ids}}, {"_id": 0, "id": 1, "full_name": 1, "email": 1}):
            creator_names[u["id"]] = u
    bank_set = set()
    if creator_ids:
        async for b in db.creator_bank_accounts.find({"creator_id": {"$in": creator_ids}}, {"_id": 0, "creator_id": 1}):
            bank_set.add(b["creator_id"])

    creator_payouts_detail = []
    for c in pending_by_creator:
        u = creator_names.get(c["_id"], {})
        creator_payouts_detail.append({
            "creator_id": c["_id"],
            "name": u.get("full_name", "Unknown"),
            "email": u.get("email", ""),
            "pending_cents": c["pending_cents"],
            "sales": c["sales"],
            "bank_on_file": c["_id"] in bank_set,
        })

    # AI spend this month
    ai_usage = await db.ai_usage_log.find(
        {"created_at": {"$gte": month_start}},
        {"_id": 0, "cost_usd": 1, "provider": 1},
    ).to_list(length=5000)
    ai_spend_month = round(sum(float(r.get("cost_usd") or 0) for r in ai_usage), 4)
    ai_calls_month = len(ai_usage)
    ai_by_provider: dict = {}
    for r in ai_usage:
        p = r.get("provider", "unknown")
        ai_by_provider[p] = round(ai_by_provider.get(p, 0) + float(r.get("cost_usd") or 0), 4)

    return {
        "generated_at": now.isoformat(),
        "goal": {
            "monthly_target_cents": MONTHLY_GOAL_CENTS,
            "month_cents": revenue_month_cents,
            "today_cents": revenue_today_cents,
            "alltime_cents": revenue_alltime_cents,
            "progress_pct": round(revenue_month_cents / MONTHLY_GOAL_CENTS * 100, 1),
        },
        "by_product": by_product,
        "monthly_trend": months_trend,
        "subscriptions": {
            "active": active_subs,
            "canceled": canceled_subs,
        },
        "creator_payouts": {
            "total_pending_cents": total_pending_creator_cents,
            "creators_pending": len(creator_payouts_detail),
            "detail": creator_payouts_detail,
        },
        "ai_spend": {
            "month_usd": ai_spend_month,
            "calls_month": ai_calls_month,
            "by_provider": ai_by_provider,
        },
    }



# ── Creator Revenue Split Tiers ─────────────────────────────────────────────

async def get_creator_split(user_id: str) -> dict:
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        return {"creator_pct": 70, "platform_pct": 30, "tier": "base", "tier_label": "Base Creator"}
    is_certified = user_doc.get("creator_certified", False)
    course = await db.courses.find_one({"instructor_id": user_id, "published": True})
    has_students = False
    if course:
        enrollment = await db.enrollments.find_one({"course_id": str(course.get("_id", ""))})
        has_students = enrollment is not None
    instructor_rating = user_doc.get("instructor_rating", 0)
    if is_certified and has_students and instructor_rating >= 4.0:
        return {"creator_pct": 85, "platform_pct": 15, "tier": "certified_instructor", "tier_label": "Certified Instructor"}
    elif has_students:
        return {"creator_pct": 80, "platform_pct": 20, "tier": "active_instructor", "tier_label": "Active Instructor"}
    elif is_certified:
        return {"creator_pct": 75, "platform_pct": 25, "tier": "certified", "tier_label": "Certified Creator"}
    else:
        return {"creator_pct": 70, "platform_pct": 30, "tier": "base", "tier_label": "Base Creator"}

def _next_tier_info(current_tier: str) -> dict:
    tiers = {
        "base": {"label": "Certified Creator (75%)", "action": "Complete Creator Certification", "link": "/certification"},
        "certified": {"label": "Active Instructor (80%)", "action": "Publish a course and get your first student", "link": "/creator/courses"},
        "active_instructor": {"label": "Certified Instructor (85%)", "action": "Get Creator Certified and maintain 4.0+ rating", "link": "/certification"},
        "certified_instructor": {"label": "You're at the top! 85%", "action": "Keep creating and teaching.", "link": "/studio"},
    }
    return tiers.get(current_tier, tiers["base"])

@router.get("/creator/split")
async def get_my_split(user: User = Depends(_dep_current_user)):
    return await get_creator_split(user.id)

@router.get("/creator/payout-summary")
async def payout_summary(user: User = Depends(_dep_current_user)):
    split = await get_creator_split(user.id)
    bookings = await db.band_bookings.find(
        {"artist_user_id": user.id, "status": "accepted"}
    ).sort("created_at", -1).limit(20).to_list(length=20)
    total_earned = 0
    for b in bookings:
        offer = b.get("offer_cents", 0) or 0
        b["creator_cut_cents"] = int(offer * split["creator_pct"] / 100)
        b["platform_cut_cents"] = offer - b["creator_cut_cents"]
        total_earned += b["creator_cut_cents"]
        b["id"] = str(b.pop("_id", ""))
    return {
        "split": split,
        "total_earned_cents": total_earned,
        "recent_bookings": bookings[:10],
        "next_tier": _next_tier_info(split["tier"]),
    }


@router.get("/ai/provider-test")
async def ai_provider_test(user: User = Depends(_require_rank("admin"))):
    """Live test of every LLM provider — returns which ones actually respond.
    Use this to diagnose widget failures. Hits each provider with a 1-token ping."""
    from ai.llm_gateway import (
        GROQ_API_KEY, GROQ_BASE, GROQ_MODEL,
        CEREBRAS_API_KEY, CEREBRAS_BASE, CEREBRAS_MODEL,
        SAMBANOVA_API_KEY, SAMBANOVA_BASE, SAMBANOVA_MODEL,
        GEMINI_API_KEY, GEMINI_BASE, GEMINI_MODEL,
        XAI_API_KEY, XAI_BASE, XAI_MODEL,
        MISTRAL_API_KEY, MISTRAL_BASE, MISTRAL_MODEL,
        TOGETHER_API_KEY, TOGETHER_BASE, TOGETHER_MODEL,
        OPENROUTER_API_KEY, OPENROUTER_BASE, OPENROUTER_MODEL,
        _oai_compat_call, gateway_status,
        _hour_tokens_used, HOURLY_TOKEN_CAP,
    )
    import os as _os
    import httpx as _httpx

    ping_msg = [{"role": "user", "content": "Say OK"}]
    ping_sys = "Reply with just OK."

    results = {}

    async def _test(name, base, key, model):
        if not key:
            return {"ok": False, "reason": "no_key"}
        try:
            r = await _oai_compat_call(base, key, model, ping_sys, ping_msg, 8, None)
            return {"ok": True, "text": r["text"][:40]}
        except Exception as e:
            return {"ok": False, "reason": str(e)[:120]}

    results["groq"]       = await _test("groq",       GROQ_BASE,       GROQ_API_KEY,       GROQ_MODEL)
    results["cerebras"]   = await _test("cerebras",   CEREBRAS_BASE,   CEREBRAS_API_KEY,   CEREBRAS_MODEL)
    results["sambanova"]  = await _test("sambanova",  SAMBANOVA_BASE,  SAMBANOVA_API_KEY,  SAMBANOVA_MODEL)
    results["gemini"]     = await _test("gemini",     GEMINI_BASE,     GEMINI_API_KEY,     GEMINI_MODEL)
    results["grok"]       = await _test("grok",       XAI_BASE,        XAI_API_KEY,        XAI_MODEL)
    results["mistral"]    = await _test("mistral",    MISTRAL_BASE,    MISTRAL_API_KEY,    MISTRAL_MODEL)
    results["together"]   = await _test("together",   TOGETHER_BASE,   TOGETHER_API_KEY,   TOGETHER_MODEL)
    results["openrouter"] = await _test("openrouter", OPENROUTER_BASE, OPENROUTER_API_KEY, OPENROUTER_MODEL)

    working = [k for k, v in results.items() if v.get("ok")]
    return {
        "providers": results,
        "working_count": len(working),
        "working": working,
        "budget": {"used": _hour_tokens_used, "cap": HOURLY_TOKEN_CAP},
        "watchdog_disabled": bool(_os.environ.get("WATCHDOG_DISABLE")),
    }
