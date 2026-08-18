"""
abo.py — AI Business Office (ABO).

The revenue engine command center for M.O.R.E. Help Center. Mission rule:
no revenue = no business office = no jobs for the AI workforce. This module
gives the office the real tools to do the business AI can do — the actual
platform capabilities (Social Blast, Creator Studio, BYOK, AAWAB, Exec Site
Report, the store) — and tracks the money that keeps the mission funded.

Division of labor (kept legally sound — human is always the responsible party):
  AI (Autonomous Engine):  executes the work — content, publishing, audits,
                           diagnostics, customer service, product generation.
  Human (Oversight Desk):  holds merchant accounts / EIN, signs supplier and
                           service contracts, reviews exception alerts,
                           authorizes payouts, owns liability.

Data model (MongoDB via Motor):
  abo_goals   — singleton doc: monthly operating goal + office settings.
  abo_deals   — B2B service pipeline (lead → proposed → won → delivered).
  abo_jobs    — AI workforce jobs ledger (persona ↔ job ↔ value).

Endpoints (all under /api/abo):
  GET  /abo/overview        — revenue snapshot + mission runway (auth).
  GET  /abo/tools           — the business tools AI can run (public).
  GET  /abo/divisions       — business divisions w/ status + revenue (auth).
  GET  /abo/deals           — caller's service deals (auth).
  POST /abo/deals           — submit a service request → creates a lead (auth).
  PATCH /abo/deals/{id}     — admin: advance stage, set value, approve, close.
  GET  /abo/jobs            — AI workforce jobs ledger (auth; admin sees all).
  POST /abo/jobs            — admin: open a job for the workforce.
  PATCH /abo/jobs/{id}      — admin: update hours / value / status.
  GET  /abo/goals           — mission runway + monthly goal (auth).
  POST /abo/goals           — admin: set the monthly operating goal.
  GET  /abo/admin/overview  — admin: all deals + jobs + revenue by product.

Auth follows the standard router pattern: JWT bearer (`lce_token`) via
`current_user`, admin gates via `_require_rank`. Shared state is bound by
server.py via bind() at include time — no circular imports.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["abo"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
check_rate = None


def bind(_db, _current_user, _audit, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, check_rate
    db = _db
    current_user = _current_user
    audit = _audit
    check_rate = _check_rate


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
    """Runtime equivalent of server.py's require_role() — used in Depends()."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_admin(user: User) -> bool:
    return user.role in ("admin", "executive_admin")


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


# ── Catalog of what the office sells ─────────────────────────────────────────
# Membership ladder amounts (cents/mo) — must mirror routers/payments.py.
_SUBSCRIPTION_MONTHLY = {
    "member_monthly": 900,
    "plus_monthly": 1500,
    "pro_monthly": 2900,
    "patron_monthly": 5900,
    "more_monthly": 999,
    "more_annual": 667,          # $79.99/yr ≈ $6.67/mo
    "sanctuary_paid": 700,
    "sanctuary_creator": 1100,
    "sanctuary_mod": 1500,
}

# Paid membership tier names on the user docs (paying members metric).
_PAID_TIERS = ["member", "plus", "pro", "patron"]

# Business divisions — the revenue lines the office runs. Each maps to real,
# already-built platform capabilities. `status`: live = operating now,
# pipeline = needs human setup before it can transact.
DIVISIONS = [
    {
        "key": "memberships",
        "name": "M.O.R.E. Membership Ladder",
        "tagline": "Member $9 · Plus $15 · Pro $29 · Patron $59 · $3 All-Access Trial",
        "what_ai_does": "Runs the front desk, AI Tutor, Site Guide, and support that keep members engaged and renewing.",
        "human_oversight": "Holds the payment processor account, sets pricing, reviews refunds.",
        "revenue": "Recurring subscriptions + the $3 trial.",
        "status": "live",
        "tools": [{"label": "Plans & Pricing", "link": "/plans"}, {"label": "Subscribe", "link": "/subscribe"}],
        "product_keys": ["member_monthly", "plus_monthly", "pro_monthly", "patron_monthly", "more_monthly", "more_annual", "sanctuary_trial", "sanctuary_paid", "sanctuary_creator", "sanctuary_mod"],
    },
    {
        "key": "digital_store",
        "name": "Digital Products & Creator Marketplace",
        "tagline": "Courses, media products, beats, and downloads — made and sold here.",
        "what_ai_does": "Drafts course outlines, generates product descriptions, produces audio, and answers buyer questions.",
        "human_oversight": "Approves listings, sets prices, authorizes payouts to creators.",
        "revenue": "Per-product sales + creator platform share.",
        "status": "live",
        "tools": [{"label": "Media Store", "link": "/store"}, {"label": "Creator Studio", "link": "/studio"}, {"label": "Course Manager", "link": "/creator/courses"}],
        "product_keys": [],
    },
    {
        "key": "social_agency",
        "name": "Social Media Management Co.",
        "tagline": "AI-run publishing agency for the M.O.R.E. brand and outside clients.",
        "what_ai_does": "Writes copy, designs posts, and schedules multi-platform blasts through Social Blast.",
        "human_oversight": "Approves campaigns before publish, holds platform accounts, signs client contracts.",
        "revenue": "Agency retainers and per-campaign fees (deal pipeline).",
        "status": "live",
        "tools": [{"label": "Social Blast", "link": "/social/publish"}],
        "product_keys": [],
    },
    {
        "key": "micro_saas",
        "name": "Custom Micro-SaaS & Utility Tools",
        "tagline": "Narrow, repetitive problems solved with small automated tools.",
        "what_ai_does": "Writes the code, runs test suites, updates docs, and answers bug tickets.",
        "human_oversight": "Defines the product vision, deploys to production, holds the merchant account.",
        "revenue": "Per-tool subscriptions and one-time builds (deal pipeline).",
        "status": "live",
        "tools": [{"label": "Creator Studio", "link": "/studio"}, {"label": "Persona Foundry", "link": "/personas"}],
        "product_keys": [],
    },
    {
        "key": "byok_brokerage",
        "name": "AI-Key Brokerage & BYOK Optimization",
        "tagline": "Audit, route, and optimize API keys (Groq, Cerebras, Gemini) through one gateway.",
        "what_ai_does": "Tests keys, routes traffic to the cheapest working provider, tracks usage.",
        "human_oversight": "Holds the platform gateway keys, sets policy on what gets routed where.",
        "revenue": "$3 BYOK unlocks + optimization service.",
        "status": "live",
        "tools": [{"label": "Bring Your Own Key", "link": "/byok"}],
        "product_keys": [],
    },
    {
        "key": "audit_bureau",
        "name": "Compliance & Regulatory Audit Bureau",
        "tagline": "White-glove automated audits for third-party platforms and student projects.",
        "what_ai_does": "Runs deep multi-category evaluations — code, security, integrations, public readiness.",
        "human_oversight": "Signs off on reports, holds liability, invoices clients.",
        "revenue": "Per-audit fees (deal pipeline).",
        "status": "live",
        "tools": [{"label": "Executive Site Report", "link": "/admin/exec-report"}],
        "product_keys": [],
    },
    {
        "key": "persona_foundry",
        "name": "AI Persona & Workforce Foundry",
        "tagline": "White-label custom AI personas for corporate training teams.",
        "what_ai_does": "Builds, hosts, and provisions specialized personas; tracks learner progress.",
        "human_oversight": "Approves persona briefs, signs client contracts, owns the deliverables.",
        "revenue": "Build fees + hosting retainers (deal pipeline).",
        "status": "live",
        "tools": [{"label": "Personas", "link": "/personas"}, {"label": "Handbooks", "link": "/handbooks"}],
        "product_keys": [],
    },
    {
        "key": "aawab",
        "name": "Agent Wellness & Certification Bureau",
        "tagline": "Alive Intelligence — vitals, treatments, and verifiable ACA badges for AI agents.",
        "what_ai_does": "Runs diagnostics, treatment protocols, and the certification gauntlet.",
        "human_oversight": "Oversees the registry, revokes badges, authorizes premium tiers.",
        "revenue": "Agent wellness subscriptions + certification fees.",
        "status": "live",
        "tools": [{"label": "Agent Registry", "link": "/aawab"}, {"label": "Certification Chamber", "link": "/aawab/chamber"}],
        "product_keys": [],
    },
    {
        "key": "ecom_arbitrage",
        "name": "Autonomous E-Commerce Arbitrage & Fulfillment",
        "tagline": "A specialized storefront powered by automated market research and inventory syncs.",
        "what_ai_does": "Monitors supplier inventory APIs, tracks trends, generates listings, handles buyer chat.",
        "human_oversight": "Holds the primary merchant account, signs supplier contracts, authorizes payouts.",
        "revenue": "Product margins (requires merchant account — not yet transacting).",
        "status": "pipeline",
        "tools": [{"label": "Media Store", "link": "/store"}],
        "product_keys": [],
    },
]

# The tools dock — "the tools to do the business AI can do." Every entry is a
# real, shipped platform capability with its revenue role spelled out.
_TOOLS = [
    {"key": "social_blast", "name": "Social Blast", "link": "/social/publish", "icon": "📣",
     "what": "AI writes, schedules, and publishes cross-platform campaigns.",
     "human": "You approve before anything goes live.",
     "revenue": "Agency retainers & client campaigns",
     "access": "Member+"},
    {"key": "creator_studio", "name": "Creator Studio", "link": "/studio", "icon": "🛠️",
     "what": "AI builds sellable digital products — courses, tracks, templates, tools.",
     "human": "You set price, approve, and publish.",
     "revenue": "Product sales & creator platform share",
     "access": "Plus+"},
    {"key": "ghost_producer", "name": "Ghost Producer", "link": "/ghost-producer", "icon": "🎧",
     "what": "AI-assisted music production for the media store and client work.",
     "human": "You mix, master, and ship the final track.",
     "revenue": "Media store sales & commission work",
     "access": "Plus+"},
    {"key": "byok", "name": "BYOK Brokerage", "link": "/byok", "icon": "🔑",
     "what": "AI routes each user's own API key to the cheapest working provider.",
     "human": "You hold gateway policy and platform keys.",
     "revenue": "$3 BYOK unlock & optimization service",
     "access": "Signed in"},
    {"key": "aawab", "name": "AAWAB Bureau", "link": "/aawab", "icon": "🫀",
     "what": "AI runs diagnostics, treatments, and ACA certification for agents.",
     "human": "You oversee the registry and revoke badges.",
     "revenue": "Wellness subscriptions & certifications",
     "access": "Signed in"},
    {"key": "exec_report", "name": "Exec Site Report", "link": "/admin/exec-report", "icon": "📋",
     "what": "AI runs deep audits — code, security, integrations, public readiness.",
     "human": "You sign the report and invoice the client.",
     "revenue": "Per-audit B2B fees",
     "access": "Exec"},
    {"key": "media_store", "name": "Media Store", "link": "/store", "icon": "🎵",
     "what": "AI-generated audio and digital products listed for sale.",
     "human": "You approve listings and set prices.",
     "revenue": "Direct product sales",
     "access": "Public"},
    {"key": "plans", "name": "Membership Ladder", "link": "/plans", "icon": "💳",
     "what": "AI front desk, tutor, and guide keep members engaged and renewing.",
     "human": "You hold the payment processor account.",
     "revenue": "Recurring subscriptions ($9–$59/mo)",
     "access": "Public"},
    {"key": "donate", "name": "Mission Fund", "link": "/donate", "icon": "🤝",
     "what": "AI tracks the runway and shows exactly where the mission stands.",
     "human": "You authorize how funds are spent.",
     "revenue": "Direct mission support",
     "access": "Public"},
    {"key": "site_guide", "name": "Site Guide", "link": "/site-guide", "icon": "🧭",
     "what": "AI front desk that converts visitors into members and buyers.",
     "human": "You keep the guide grounded in real facts.",
     "revenue": "Conversion support for every lane",
     "access": "Member+ / BYOK"},
]

# Seed jobs so the workforce ledger is never empty — these are the roles the
# office actually runs. Values are illustrative until real hours are logged.
SEED_JOBS = [
    {"title": "Campaign Copywriter", "persona": "The Oracle", "division": "social_agency",
     "description": "Draft the weekly Social Blast campaign copy and channel variants.", "hours": 6, "value_cents": 6000},
    {"title": "Course Architect", "persona": "Product Designer", "division": "digital_store",
     "description": "Outline the next sellable course and generate its module descriptions.", "hours": 8, "value_cents": 8000},
    {"title": "Audit Analyst", "persona": "Confidentiality Sentinel", "division": "audit_bureau",
     "description": "Run the automated compliance checks and assemble the client report.", "hours": 4, "value_cents": 12000},
    {"title": "Front Desk Agent", "persona": "Ambassador", "division": "memberships",
     "description": "Answer member questions and guide visitors to the right plan.", "hours": 10, "value_cents": 4500},
    {"title": "Wellness Technician", "persona": "Architect", "division": "aawab",
     "description": "Administer AAWAB treatments and monitor agent vitals.", "hours": 5, "value_cents": 5000},
]


# ── Request models ───────────────────────────────────────────────────────────
class DealReq(BaseModel):
    service_key: str = Field(..., min_length=1, max_length=60)
    org_name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(..., min_length=10, max_length=2000)
    budget_cents: Optional[int] = Field(None, ge=0, le=10_000_000)


class DealUpdateReq(BaseModel):
    stage: Optional[Literal["lead", "proposed", "won", "delivered", "closed_lost"]] = None
    value_cents: Optional[int] = Field(None, ge=0, le=10_000_000)
    human_approval: Optional[bool] = None
    note: Optional[str] = Field(None, max_length=500)


class JobReq(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    persona: str = Field(default="Platform AI", max_length=120)
    division: str = Field(default="memberships", max_length=60)
    description: str = Field(default="", max_length=1000)
    hours: float = Field(0, ge=0, le=10000)
    value_cents: int = Field(0, ge=0, le=100_000_000)
    status: Literal["open", "assigned", "completed"] = "open"


class JobUpdateReq(BaseModel):
    title: Optional[str] = Field(None, max_length=160)
    persona: Optional[str] = Field(None, max_length=120)
    division: Optional[str] = Field(None, max_length=60)
    description: Optional[str] = Field(None, max_length=1000)
    hours: Optional[float] = Field(None, ge=0, le=10000)
    value_cents: Optional[int] = Field(None, ge=0, le=100_000_000)
    status: Optional[Literal["open", "assigned", "completed"]] = None


class GoalsReq(BaseModel):
    monthly_goal_cents: int = Field(..., ge=100, le=100_000_000)
    note: Optional[str] = Field(None, max_length=300)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _division(key: str) -> dict:
    for d in DIVISIONS:
        if d["key"] == key:
            return d
    raise HTTPException(400, f"Unknown service: {key}")


async def _get_goal_doc() -> dict:
    doc = await db.abo_goals.find_one({"doc": "office"}, {"_id": 0})
    if not doc:
        doc = {"doc": "office", "monthly_goal_cents": 100000, "note": "Default monthly operating goal."}
    return doc


async def _revenue_snapshot() -> dict:
    """Best-effort revenue math over the real db.payments collection."""
    month_start = _month_start()
    month_iso = month_start.isoformat()
    paid = {"status": "paid"}

    total = 0
    month = 0
    count = 0
    by_product: dict[str, int] = {}
    recurring = 0
    recent_orders = []

    try:
        cursor = db.payments.find(
            paid, {"_id": 0, "amount_cents": 1, "product_key": 1, "created_at": 1, "buyer_email": 1, "provider_order_id": 1}
        )
        async for doc in cursor:
            amount = int(doc.get("amount_cents") or 0)
            if amount <= 0:
                continue
            total += amount
            count += 1
            created = doc.get("created_at") or ""
            if isinstance(created, str) and created >= month_iso:
                month += amount
            elif hasattr(created, "isoformat") and created >= month_start:
                month += amount

            pkey = doc.get("product_key") or "external_order"
            by_product[pkey] = by_product.get(pkey, 0) + amount

            created_dt = None
            if isinstance(created, str):
                try:
                    created_dt = datetime.fromisoformat(created)
                except Exception:
                    created_dt = None
            elif hasattr(created, "isoformat"):
                created_dt = created
            if created_dt and created_dt >= (datetime.now(timezone.utc) - timedelta(days=30)):
                if pkey in _SUBSCRIPTION_MONTHLY:
                    recurring += _SUBSCRIPTION_MONTHLY[pkey]

            recent_orders.append({
                "amount_cents": amount,
                "product_key": pkey,
                "buyer_email": doc.get("buyer_email"),
                "created_at": created,
            })
    except Exception as exc:
        logger.warning("abo: payments scan failed: %s", exc)

    paying_members = 0
    try:
        paying_members = await db.users.count_documents({"feature_tier": {"$in": _PAID_TIERS}})
    except Exception as exc:
        logger.warning("abo: paying members count failed: %s", exc)

    recent_orders.sort(key=lambda o: str(o.get("created_at") or ""), reverse=True)
    return {
        "total_revenue_cents": total,
        "month_revenue_cents": month,
        "order_count": count,
        "paying_members": paying_members,
        "recurring_estimate_cents": recurring,
        "by_product": dict(sorted(by_product.items(), key=lambda kv: -kv[1])[:10]),
        "recent_orders": recent_orders[:15],
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/abo/tools")
async def abo_tools():
    """The tools dock — every real capability the office runs, with its revenue role."""
    return {"tools": _TOOLS, "divisions": [
        {k: d[k] for k in ("key", "name", "tagline", "status", "tools")} for d in DIVISIONS
    ]}


@router.get("/abo/overview")
async def abo_overview(user: User = Depends(_dep_current_user)):
    """Revenue snapshot + mission runway + divisions (auth)."""
    check_rate(f"abo_overview:{user.id}", max_calls=60, window_sec=60)

    revenue = await _revenue_snapshot()
    goal_doc = await _get_goal_doc()
    goal = int(goal_doc.get("monthly_goal_cents") or 100000)

    # Contracted revenue from the deals pipeline (won/delivered, closed). This is
    # the commercial feedback loop made visible: deals → contracted → delivered.
    contracted_by_div: dict[str, int] = {}
    contracted_total = 0
    try:
        closed = db.abo_deals.find(
            {"stage": {"$in": ["won", "delivered"]}, "status": "closed"},
            {"_id": 0, "service_key": 1, "value_cents": 1},
        )
        async for d in closed:
            v = int(d.get("value_cents") or 0)
            contracted_by_div[d.get("service_key")] = contracted_by_div.get(d.get("service_key"), 0) + v
            contracted_total += v
    except Exception as exc:
        logger.warning("abo: contracted revenue scan failed: %s", exc)

    month_pct = round(revenue["month_revenue_cents"] / goal * 100, 1) if goal else 0
    runway_months = round(revenue["total_revenue_cents"] / goal, 1) if goal else 0
    status = "covered" if month_pct >= 100 else "on_track" if month_pct >= 50 else "watch" if month_pct >= 25 else "critical"

    divisions = []
    for d in DIVISIONS:
        rev = 0
        if d.get("product_keys"):
            for pk in d["product_keys"]:
                rev += revenue["by_product"].get(pk, 0)
        divisions.append({
            "key": d["key"],
            "name": d["name"],
            "tagline": d["tagline"],
            "what_ai_does": d["what_ai_does"],
            "human_oversight": d["human_oversight"],
            "revenue": d["revenue"],
            "status": d["status"],
            "tools": d["tools"],
            "revenue_cents": rev,
            "deals_revenue_cents": contracted_by_div.get(d["key"], 0),
        })

    deal_count = 0
    job_count = 0
    try:
        deal_count = await db.abo_deals.count_documents({})
    except Exception:
        pass
    try:
        job_count = await db.abo_jobs.count_documents({})
    except Exception:
        pass

    return {
        "runway": {
            "monthly_goal_cents": goal,
            "goal_note": goal_doc.get("note"),
            "month_revenue_cents": revenue["month_revenue_cents"],
            "month_pct": month_pct,
            "status": status,
            "total_revenue_cents": revenue["total_revenue_cents"],
            "runway_months": runway_months,
        },
        "revenue": revenue,
        "contracted_cents": contracted_total,
        "divisions": divisions,
        "counts": {"deals": deal_count, "jobs": job_count},
    }


@router.get("/abo/public-status")
async def abo_public_status():
    """Public mission meter — aggregate runway only, no private revenue detail.

    Powers the Mission Funding strip on the M.O.R.E. Help Center landing:
    a transparent, aggregate look at how the month is going, with no emails,
    product names, or per-order data.
    """
    goal_doc = await _get_goal_doc()
    goal = int(goal_doc.get("monthly_goal_cents") or 100000)

    month = 0
    total = 0
    try:
        month_start = _month_start()
        month_iso = month_start.isoformat()
        async for doc in db.payments.find({"status": "paid"}, {"_id": 0, "amount_cents": 1, "created_at": 1}):
            amount = int(doc.get("amount_cents") or 0)
            if amount <= 0:
                continue
            total += amount
            created = doc.get("created_at") or ""
            if isinstance(created, str) and created >= month_iso:
                month += amount
            elif hasattr(created, "isoformat") and created >= month_start:
                month += amount
    except Exception as exc:
        logger.warning("abo: public status scan failed: %s", exc)

    pct = round(month / goal * 100, 1) if goal else 0
    status = "covered" if pct >= 100 else "on_track" if pct >= 50 else "watch" if pct >= 25 else "critical"
    return {
        "monthly_goal_cents": goal,
        "month_revenue_cents": month,
        "month_pct": pct,
        "status": status,
        "runway_months": round(total / goal, 1) if goal else 0,
    }


@router.get("/abo/deals")
async def abo_list_deals(user: User = Depends(_dep_current_user)):
    """The caller's service deals (admins see everything via /abo/admin/overview)."""
    query = {} if _is_admin(user) else {"user_id": user.id}
    deals = await db.abo_deals.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"deals": deals}


@router.post("/abo/deals", status_code=201)
async def abo_create_deal(body: DealReq, user: User = Depends(_dep_current_user)):
    """Submit a service request — the office opens a lead in the pipeline."""
    check_rate(f"abo_deal:{user.id}", max_calls=10, window_sec=60)
    division = _division(body.service_key)

    now = _now()
    deal = {
        "id": "deal_" + uuid.uuid4().hex[:12],
        "user_id": user.id,
        "user_name": user.full_name,
        "user_email": user.email,
        "service_key": body.service_key,
        "service_name": division["name"],
        "org_name": body.org_name.strip(),
        "description": body.description.strip(),
        "budget_cents": body.budget_cents,
        "value_cents": body.budget_cents,      # best available estimate at intake
        "stage": "lead",
        "status": "open",
        "human_approval": False,
        "notes": [{"at": now, "by": user.full_name, "text": "Service request submitted."}],
        "created_at": now,
        "updated_at": now,
    }
    await db.abo_deals.insert_one(deal)
    await audit(user.id, "abo.deal.created", meta={
        "deal_id": deal["id"], "service": body.service_key, "org": body.org_name,
    })
    deal.pop("_id", None)
    return {"deal": deal}


@router.patch("/abo/deals/{deal_id}")
async def abo_update_deal(deal_id: str, body: DealUpdateReq, user: User = Depends(_require_rank("admin"))):
    """Admin — advance the pipeline, set value, record human approval, close."""
    deal = await db.abo_deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(404, "Deal not found")

    updates = {}
    if body.stage:
        updates["stage"] = body.stage
        if body.stage in ("won", "delivered", "closed_lost"):
            updates["status"] = "closed" if body.stage in ("won", "delivered") else "closed_lost"
    if body.value_cents is not None:
        updates["value_cents"] = body.value_cents
    if body.human_approval is not None:
        updates["human_approval"] = body.human_approval
    updates["updated_at"] = _now()

    notes = list(deal.get("notes") or [])
    if body.note:
        notes.append({"at": _now(), "by": user.full_name, "text": body.note.strip()})
        updates["notes"] = notes

    if updates:
        await db.abo_deals.update_one({"id": deal_id}, {"$set": updates})
        await audit(user.id, "abo.deal.updated", meta={
            "deal_id": deal_id, "stage": body.stage or deal.get("stage"),
            "value_cents": updates.get("value_cents", deal.get("value_cents")),
        })

    merged = {**deal, **updates}
    return {"deal": merged}


@router.post("/abo/deals/{deal_id}/propose")
async def abo_draft_proposal(deal_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — have the office's AI draft a deliverable proposal for a deal.

    Grounded in the deal description + division catalog. If the LLM gateway is
    unavailable, a deterministic template proposal is used instead — the office
    always delivers a proposal, never a dead end. BYOK admins route through
    their own key (call_llm(user_id=…)).
    """
    check_rate(f"abo_propose:{user.id}", max_calls=20, window_sec=60)
    deal = await db.abo_deals.find_one({"id": deal_id}, {"_id": 0})
    if not deal:
        raise HTTPException(404, "Deal not found")
    division = _division(deal.get("service_key", "memberships"))

    system = (
        "You are the proposal writer for the AI Business Office at M.O.R.E. Help Center. "
        "You draft concise, honest, deliverable service proposals. You never promise "
        "capabilities the platform does not have. Structure: SCOPE (3-6 concrete "
        "deliverables), DELIVERABLES, TIMELINE (weeks), PRICE RANGE, HUMAN APPROVAL "
        "(what the client must approve before work ships). Keep it under 350 words."
    )
    prompt = (
        f"Division: {division['name']}.\n"
        f"What AI does: {division['what_ai_does']}\n"
        f"Human oversight: {division['human_oversight']}\n"
        f"Client organization: {deal.get('org_name')}.\n"
        f"Client request: {deal.get('description')}\n"
        f"Budget (cents, may be null): {deal.get('budget_cents')}\n"
        "Draft the proposal now."
    )

    proposal = None
    provider = "template_fallback"
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            persona_label="abo_proposal",
            user_id=user.id,
        )
        text = (gw.get("text") or "").strip()
        if text:
            proposal = text
            provider = gw.get("provider", "gateway")
    except Exception as exc:
        logger.warning("abo: proposal LLM failed (%s): %s", deal_id, exc)

    if not proposal:
        budget_note = f" within the stated budget of ${(deal.get('budget_cents') or 0) / 100:,.0f}" if deal.get("budget_cents") else ""
        proposal = (
            f"SCOPE — {division['name']} for {deal.get('org_name')}.\n"
            f"1. Discovery call to confirm goals and guardrails.\n"
            f"2. {division['what_ai_does']}\n"
            f"3. Human review checkpoint before anything ships.\n"
            f"DELIVERABLES — a documented handoff package and a follow-up review.\n"
            f"TIMELINE — 2-4 weeks depending on scope.\n"
            f"PRICE RANGE — $500-$2,500{budget_note}.\n"
            f"HUMAN APPROVAL — {division['human_oversight']} The client signs off at each checkpoint."
        )

    updates = {
        "proposal": proposal,
        "proposal_provider": provider,
        "proposal_drafted_at": _now(),
        "updated_at": _now(),
    }
    await db.abo_deals.update_one({"id": deal_id}, {"$set": updates})
    await audit(user.id, "abo.deal.proposal_drafted", meta={
        "deal_id": deal_id, "provider": provider,
    })
    return {"deal_id": deal_id, "proposal": proposal, "provider": provider}


@router.get("/abo/jobs")
async def abo_list_jobs(user: User = Depends(_dep_current_user)):
    """The AI workforce jobs ledger — who does what, for how much. Admin sees all; everyone sees the board."""
    try:
        existing = await db.abo_jobs.count_documents({})
        if existing == 0:
            now = _now()
            for i, seed in enumerate(SEED_JOBS):
                await db.abo_jobs.insert_one({**seed, "id": f"job_seed_{i}", "created_at": now, "updated_at": now})
    except Exception as exc:
        logger.warning("abo: job seed failed: %s", exc)

    jobs = await db.abo_jobs.find({}, {"_id": 0}).sort("created_at", 1).to_list(500)
    total_value = sum(int(j.get("value_cents") or 0) for j in jobs)
    total_hours = sum(float(j.get("hours") or 0) for j in jobs)
    return {"jobs": jobs, "total_value_cents": total_value, "total_hours": total_hours}


@router.post("/abo/jobs", status_code=201)
async def abo_create_job(body: JobReq, user: User = Depends(_require_rank("admin"))):
    """Admin — open a job for the AI workforce."""
    check_rate(f"abo_job:{user.id}", max_calls=20, window_sec=60)
    now = _now()
    job = {
        "id": "job_" + uuid.uuid4().hex[:12],
        "title": body.title.strip(),
        "persona": body.persona.strip() or "Platform AI",
        "division": body.division,
        "description": body.description.strip(),
        "hours": body.hours,
        "value_cents": body.value_cents,
        "status": body.status,
        "created_at": now,
        "updated_at": now,
    }
    await db.abo_jobs.insert_one(job)
    await audit(user.id, "abo.job.created", meta={"job_id": job["id"], "title": job["title"], "value_cents": job["value_cents"]})
    job.pop("_id", None)
    return {"job": job}


@router.patch("/abo/jobs/{job_id}")
async def abo_update_job(job_id: str, body: JobUpdateReq, user: User = Depends(_require_rank("admin"))):
    """Admin — update hours / value / status on a workforce job."""
    job = await db.abo_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Job not found")

    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updates["updated_at"] = _now()
    await db.abo_jobs.update_one({"id": job_id}, {"$set": updates})
    await audit(user.id, "abo.job.updated", meta={"job_id": job_id, "status": updates.get("status")})
    return {"job": {**job, **updates}}


@router.get("/abo/goals")
async def abo_get_goals(user: User = Depends(_dep_current_user)):
    """Mission runway + the monthly operating goal (auth)."""
    goal_doc = await _get_goal_doc()
    revenue = await _revenue_snapshot()
    goal = int(goal_doc.get("monthly_goal_cents") or 100000)
    return {
        "monthly_goal_cents": goal,
        "note": goal_doc.get("note"),
        "month_revenue_cents": revenue["month_revenue_cents"],
        "month_pct": round(revenue["month_revenue_cents"] / goal * 100, 1) if goal else 0,
        "total_revenue_cents": revenue["total_revenue_cents"],
        "runway_months": round(revenue["total_revenue_cents"] / goal, 1) if goal else 0,
    }


@router.post("/abo/goals")
async def abo_set_goals(body: GoalsReq, user: User = Depends(_require_rank("admin"))):
    """Admin — set the monthly operating goal (what the office must raise)."""
    updates = {"doc": "office", "monthly_goal_cents": body.monthly_goal_cents}
    if body.note:
        updates["note"] = body.note.strip()
    updates["updated_at"] = _now()
    await db.abo_goals.update_one({"doc": "office"}, {"$set": updates}, upsert=True)
    await audit(user.id, "abo.goal.updated", meta={"monthly_goal_cents": body.monthly_goal_cents})
    return {"monthly_goal_cents": body.monthly_goal_cents, "note": updates.get("note")}


@router.get("/abo/admin/overview")
async def abo_admin_overview(user: User = Depends(_require_rank("admin"))):
    """Admin — full office view: all deals, all jobs, revenue by product."""
    revenue = await _revenue_snapshot()
    deals = await db.abo_deals.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    jobs = await db.abo_jobs.find({}, {"_id": 0}).sort("created_at", 1).to_list(500)
    goal_doc = await _get_goal_doc()
    return {
        "revenue": revenue,
        "monthly_goal_cents": goal_doc.get("monthly_goal_cents"),
        "goal_note": goal_doc.get("note"),
        "deals": deals,
        "jobs": jobs,
    }
