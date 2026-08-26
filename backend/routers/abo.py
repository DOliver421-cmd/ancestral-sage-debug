"""
abo.py — AI Business Office (ABO).

The revenue engine command center for M.O.R.E. Help Center. Mission rule:
no revenue = no business office = no jobs for the AI workforce.

OWNER-FIRST FINANCIAL MODEL (non-negotiable):
  REVENUE (month) ──► 1. Infrastructure costs (hosting, API tokens, DB)
                   ──► 2. NET PROFIT ──► belongs to the business entity
                        and the owner as retained earnings
                   ──► 3. Distributions to any role happen ONLY when the
                        owner records them, ONLY out of net profit.

Data model (MongoDB via Motor):
  abo_config   — singleton: every number + text override, editable via
                 GET/PUT /abo/config by the owner (audited).
  abo_deals    — B2B service pipeline (lead → proposed → won → delivered).
  abo_jobs     — Workforce ledger — people AND AI, performance-linked pay.
  abo_exchange_contracts — Agent-to-agent task contracts.
  abo_redteam_engagements — Red-teaming engagements.
  abo_agenda   — Office agenda items.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, normalize_role

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["abo"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
check_rate = None

# ── Default config (used when abo_config collection is empty) ─────────────────
_DEFAULT_CONFIG = {
    "monthly_goal_cents": 50000,
    "infra_cost_cents": 8000,
    "owner_draw_pct": 100,
    "clearinghouse_fee_pct": 15,
    "redteam_oneshot_cents": 25000,
    "redteam_retainer_cents": 75000,
    "header_title": "AI Business Office",
    "header_tagline": "Revenue engine for the mission",
    "runway_note": "What the office must raise each month.",
    "loop_intro": "Each loop feeds the next.",
    "guardrail_owner": "Owner-first",
    "guardrail_owner_desc": "The founder is the ultimate beneficiary.",
    "guardrail_labor": "Performance-linked labor",
    "guardrail_labor_desc": "No fixed drains on the business.",
    "guardrail_creator": "Creators get paid first",
    "guardrail_creator_desc": "Platform cut never competes with creator cut.",
    "guardrail_revenue": "No invented revenue",
    "guardrail_revenue_desc": "Dashboard reads the real payments ledger.",
    "guardrail_ai": "AI always discloses",
    "guardrail_ai_desc": "AI talks to people, says so per FTC guidance.",
}

# ── Default divisions ────────────────────────────────────────────────────────
_DEFAULT_DIVISIONS = [
    {"key": "memberships", "name": "Memberships & Courses", "tagline": "Recurring revenue from education", "ai_role": "Content delivery, tutoring, progress tracking", "human_role": "Curriculum design, student support oversight", "revenue_desc": "Monthly subscriptions + one-time course purchases", "status": "live"},
    {"key": "social_media", "name": "Social Media Management", "tagline": "Community presence on autopilot", "ai_role": "Content scheduling, engagement, analytics", "human_role": "Strategy, brand voice approval, escalation", "revenue_desc": "B2B service engagements", "status": "live"},
    {"key": "creative_services", "name": "Creative Services", "tagline": "Ghost production, audio, video", "ai_role": "Production, mastering, editing", "human_role": "Creative direction, client relations", "revenue_desc": "Per-project and retainer pricing", "status": "live"},
    {"key": "ai_audits", "name": "AI Audits & Compliance", "tagline": "Red-team and governance", "ai_role": "Automated scanning, report generation", "human_role": "Review, merge/approve, client communication", "revenue_desc": "One-shot scans and monthly retainers", "status": "live"},
    {"key": "tool_licensing", "name": "Tool Licensing & BYOK", "tagline": "Platform tools for external use", "ai_role": "API access, key management", "human_role": "Sales, onboarding, support", "revenue_desc": "Per-key licensing fees", "status": "live"},
    {"key": "consulting", "name": "Community Consulting", "tagline": "Strategy and implementation", "ai_role": "Research, draft deliverables", "human_role": "Client management, final approval", "revenue_desc": "Hourly and project-based", "status": "live"},
]

# ── Default tools — the single execution hub list ───────────────────────────
# access: minimum role required (student = public, admin = admin-gated, executive = exec-only)
# The frontend auto-gates: locked icon if user role < access level.
_DEFAULT_TOOLS = [
    # ── AI Tools (student+) ──────────────────────────────────────────────
    {"key": "ai_tutor", "name": "AI Tutor", "icon": "🧠", "link": "/ai", "access": "student", "what": "AI-powered learning assistant — ask questions, get explanations, practice skills.", "revenue": "Included in membership"},
    {"key": "orchestrator", "name": "Orchestrator", "icon": "🎭", "link": "/orchestrator", "access": "admin", "what": "Multi-persona AI orchestrator — coordinate agents for complex tasks.", "revenue": "Internal ops"},
    {"key": "helper", "name": "Helper", "icon": "💬", "link": "/helper", "access": "student", "what": "Always-on community helper — answers questions, finds resources.", "revenue": "Support & retention"},
    {"key": "site_guide", "name": "Site Guide", "icon": "🗺️", "link": "/site-guide", "access": "student", "what": "Interactive site navigation guide — shows users where to go.", "revenue": "Support & retention"},
    # ── Creative Tools (student+) ────────────────────────────────────────
    {"key": "social_blast", "name": "Social Blast", "icon": "📡", "link": "/assistant", "access": "admin", "what": "AI-powered social media management — draft, schedule, publish across platforms.", "revenue": "B2B service engagements"},
    {"key": "creator_studio", "name": "Creator Studio", "icon": "🎬", "link": "/studio", "access": "student", "what": "Content creation suite — video, audio, scripts, metadata.", "revenue": "Creator subscriptions"},
    {"key": "ghost_producer", "name": "Ghost Producer", "icon": "👻", "link": "/ghost-producer", "access": "admin", "what": "AI content production — ebooks, workshops, albums, toolkits.", "revenue": "Per-project pricing"},
    {"key": "media_store", "name": "Media Store", "icon": "🎵", "link": "/store", "access": "student", "what": "Digital media marketplace — music, audio, educational content.", "revenue": "Creator revenue share"},
    # ── Business Tools (admin+) ──────────────────────────────────────────
    {"key": "byok", "name": "BYOK Gateway", "icon": "🔑", "link": "/byok", "access": "admin", "what": "Bring Your Own Key — use your own AI provider keys, zero platform cost.", "revenue": "Key licensing fees"},
    {"key": "aawab", "name": "AAWAB", "icon": "🤖", "link": "/aawab", "access": "admin", "what": "Agent Wellness Board — monitor, certify, and maintain AI agents.", "revenue": "Agent-as-a-service"},
    {"key": "bridge", "name": "AI Team Bridge", "icon": "🌉", "link": "/admin/bridge", "access": "admin", "what": "Cross-persona AI dispatch — route tasks to the right agent.", "revenue": "Internal ops"},
    {"key": "jamil", "name": "Jamil", "icon": "🎙️", "link": "/jamil", "access": "admin", "what": "AI persona chat — knowledge extraction, transcription, TTS.", "revenue": "Internal ops"},
    {"key": "creative_partner", "name": "Creative Partner Hub", "icon": "🎨", "link": "/creative-partner", "access": "instructor", "what": "AI creative collaboration — ideation, writing, production support.", "revenue": "Content production"},
    {"key": "competition", "name": "Competition Arena", "icon": "⚔️", "link": "/arena", "access": "executive", "what": "Multi-persona competition — agents compete to create products.", "revenue": "Product generation"},
    # ── Revenue & Commerce (admin+) ──────────────────────────────────────
    {"key": "payments", "name": "Payment Admin", "icon": "💳", "link": "/admin/payments", "access": "admin", "what": "View and manage all payment transactions.", "revenue": "Revenue tracking"},
    {"key": "prices", "name": "Platform Prices", "icon": "💲", "link": "/admin/prices", "access": "admin", "what": "Configure all platform pricing — tiers, products, discounts.", "revenue": "Revenue optimization"},
    {"key": "billing", "name": "Billing Admin", "icon": "🧾", "link": "/admin/billing", "access": "admin", "what": "Credit management, refunds, provider keys.", "revenue": "Financial ops"},
    {"key": "providers", "name": "Provider Gateway", "icon": "🔌", "link": "/admin/providers", "access": "executive", "what": "AI provider key management — setup, test, rotate.", "revenue": "Cost control"},
    # ── Governance & Security (admin+) ───────────────────────────────────
    {"key": "iam", "name": "IAM Console", "icon": "🔐", "link": "/admin/iam", "access": "admin", "what": "User management — search, role elevation, password reset, access control.", "revenue": "Compliance"},
    {"key": "audit_log", "name": "Audit Log", "icon": "📋", "link": "/admin/audit", "access": "support_staff", "what": "Full audit trail of every administrative action.", "revenue": "Compliance"},
    {"key": "sage_audit", "name": "Sage Audit", "icon": "🦉", "link": "/admin/sage-audit", "access": "executive", "what": "AI persona audit — caps, metrics, integrity checks.", "revenue": "AI governance"},
    {"key": "site_control", "name": "Site Control Panel", "icon": "🎛️", "link": "/admin/control", "access": "executive", "what": "Feature flags, visibility, AI spend budgets.", "revenue": "Platform ops"},
    {"key": "exec_control", "name": "Sovereign Command", "icon": "👑", "link": "/admin/exec-control", "access": "executive", "what": "Full exec control — tiers, roles, break-glass, authz matrix.", "revenue": "Platform ops"},
    {"key": "system", "name": "Exec System", "icon": "⚙️", "link": "/admin/system", "access": "executive", "what": "System health, cohorts, recent activity, provider status.", "revenue": "Platform ops"},
    {"key": "exec_report", "name": "Executive Site Report", "icon": "📊", "link": "/admin/exec-report", "access": "executive", "what": "Full site health report — uptime, errors, performance.", "revenue": "Platform ops"},
    {"key": "command", "name": "Executive Command Center", "icon": "🎯", "link": "/admin/command", "access": "executive", "what": "Mission control — stats, users, role changes, system state.", "revenue": "Platform ops"},
    # ── Monitoring ───────────────────────────────────────────────────────
    {"key": "analytics", "name": "Analytics", "icon": "📈", "link": "/admin/analytics", "access": "admin", "what": "Program and benchmark analytics.", "revenue": "Insights"},
    {"key": "health", "name": "System Health", "icon": "💓", "link": "/admin/health", "access": "admin", "what": "AI cost tracking, system health checks.", "revenue": "Ops"},
    {"key": "health_report", "name": "Health Report", "icon": "🩺", "link": "/admin/health-report", "access": "admin", "what": "Detailed health report — endpoint latency, error rates.", "revenue": "Ops"},
    {"key": "moderation", "name": "Moderation", "icon": "🛡️", "link": "/admin/moderation", "access": "support_staff", "what": "Content moderation queue and analytics.", "revenue": "Community safety"},
    # ── Revenue Engine (the office itself) ────────────────────────────────
    {"key": "exchange", "name": "Workforce Exchange", "icon": "🔄", "link": "/business-office", "access": "admin", "what": "Agent-to-agent task marketplace — agents subcontract work.", "revenue": "Clearinghouse fees"},
    {"key": "redteam", "name": "Red-Team Bureau", "icon": "🛡️", "link": "/business-office", "access": "admin", "what": "Adversarial security scanning — AI scans, human approves.", "revenue": "Scans & retainers"},
    {"key": "plans", "name": "Membership Plans", "icon": "💎", "link": "/plans", "access": "student", "what": "View and manage subscription tiers.", "revenue": "Recurring revenue"},
    {"key": "donate", "name": "Donate", "icon": "❤️", "link": "/donate", "access": "student", "what": "Community donations for mission funding.", "revenue": "Direct support"},
    {"key": "scholarships", "name": "Scholarships", "icon": "🎓", "link": "/admin/scholarships", "access": "admin", "what": "Scholarship fund management — apply, sponsor, award.", "revenue": "Community investment"},
]


def bind(_db, _current_user, _audit, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, check_rate
    db = _db
    current_user = _current_user
    audit = _audit
    check_rate = _check_rate


# ── Helper: role gate ────────────────────────────────────────────────────────
from routers.roles import ROLE_RANK, Role


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


# ── Config helpers ───────────────────────────────────────────────────────────
async def _get_config() -> dict:
    """Load the ABO config singleton (or create with defaults)."""
    doc = await db.abo_config.find_one({"_id": "singleton"})
    if doc:
        return doc
    cfg = {"_id": "singleton", **_DEFAULT_CONFIG, "updated_at": _now()}
    await db.abo_config.insert_one(cfg)
    return cfg


async def _save_config(updates: dict, user: User):
    """Audit-logged config save."""
    updates["updated_at"] = _now()
    updates["updated_by"] = user.id
    await db.abo_config.update_one({"_id": "singleton"}, {"$set": updates}, upsert=True)
    try:
        await audit(user.id, "abo.config_updated", meta={"keys": list(updates.keys())})
    except Exception:
        pass


# ── Revenue helpers ──────────────────────────────────────────────────────────
async def _get_month_revenue_cents() -> int:
    """Sum paid orders from the current month."""
    ms = _month_start()
    pipeline = [
        {"$match": {"status": {"$in": ["paid", "completed", "fulfilled"]}, "created_at": {"$gte": ms.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_cents"}}},
    ]
    try:
        results = await db.payments.aggregate(pipeline).to_list(1)
        return results[0]["total"] if results else 0
    except Exception:
        return 0


async def _get_total_revenue_cents() -> int:
    """Sum all paid orders ever."""
    pipeline = [
        {"$match": {"status": {"$in": ["paid", "completed", "fulfilled"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_cents"}}},
    ]
    try:
        results = await db.payments.aggregate(pipeline).to_list(1)
        return results[0]["total"] if results else 0
    except Exception:
        return 0


async def _get_order_count() -> int:
    try:
        return await db.payments.count_documents({"status": {"$in": ["paid", "completed", "fulfilled"]}})
    except Exception:
        return 0


async def _get_paying_members() -> int:
    try:
        return await db.users.count_documents({"feature_tier": {"$in": ["member", "plus", "pro", "patron"]}, "is_active": True})
    except Exception:
        return 0


async def _get_contracted_cents() -> int:
    """Sum value of closed/won deals."""
    pipeline = [
        {"$match": {"stage": {"$in": ["won", "delivered"]}, "value_cents": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$value_cents"}}},
    ]
    try:
        results = await db.abo_deals.aggregate(pipeline).to_list(1)
        return results[0]["total"] if results else 0
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

# ── GET /abo/overview ────────────────────────────────────────────────────────
@router.get("/abo/overview")
async def abo_overview(user: User = Depends(_dep_current_user)):
    cfg = await _get_config()
    month_rev = await _get_month_revenue_cents()
    total_rev = await _get_total_revenue_cents()
    order_count = await _get_order_count()
    paying_members = await _get_paying_members()
    contracted = await _get_contracted_cents()

    monthly_goal = cfg.get("monthly_goal_cents", 50000)
    infra_cost = cfg.get("infra_cost_cents", 8000)
    owner_draw_pct = cfg.get("owner_draw_pct", 100)

    # Runway calculation
    month_pct = round(month_rev / max(monthly_goal, 1) * 100, 1) if monthly_goal else 0
    if month_pct >= 100:
        runway_status = "covered"
    elif month_pct >= 70:
        runway_status = "on_track"
    elif month_pct >= 30:
        runway_status = "watch"
    else:
        runway_status = "critical"

    # P&L waterfall
    gross = month_rev
    infra = infra_cost
    net_profit = max(0, gross - infra)
    owner_retained = int(net_profit * owner_draw_pct / 100) if owner_draw_pct else 0
    distributable = net_profit - owner_retained

    # Estimate recurring (simple: current month * 12 / 12 = current month)
    recurring_estimate = month_rev

    runway_months = round(total_rev / max(monthly_goal, 1), 1) if monthly_goal else 0

    return {
        "runway": {
            "monthly_goal_cents": monthly_goal,
            "month_revenue_cents": month_rev,
            "runway_months": runway_months,
            "month_pct": month_pct,
            "status": runway_status,
            "goal_note": cfg.get("runway_note", "What the office must raise each month."),
        },
        "revenue": {
            "total_revenue_cents": total_rev,
            "month_revenue_cents": month_rev,
            "order_count": order_count,
            "paying_members": paying_members,
            "recurring_estimate_cents": recurring_estimate,
        },
        "pnl": {
            "gross_cents": gross,
            "infra_cents": infra,
            "net_profit_cents": net_profit,
            "owner_draw_pct": owner_draw_pct,
            "owner_retained_cents": owner_retained,
            "distributable_cents": distributable,
            "fully_payable": distributable > 0,
            "waterfall_note": "Revenue → Infrastructure → Net profit → Owner retained → Performance pool",
        },
        "contracted_cents": contracted,
        "divisions": _DEFAULT_DIVISIONS,
    }


# ── GET /abo/tools ───────────────────────────────────────────────────────────
@router.get("/abo/tools")
async def abo_tools(user: User = Depends(_dep_current_user)):
    return {"tools": _DEFAULT_TOOLS}


# ── GET /abo/deals ───────────────────────────────────────────────────────────
@router.get("/abo/deals")
async def abo_deals(user: User = Depends(_dep_current_user)):
    deals = await db.abo_deals.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"deals": deals}


# ── POST /abo/deals ──────────────────────────────────────────────────────────
class DealReq(BaseModel):
    service_key: str
    org_name: str
    description: str
    budget_cents: Optional[int] = None


@router.post("/abo/deals")
async def create_deal(body: DealReq, user: User = Depends(_dep_current_user)):
    division = next((d for d in _DEFAULT_DIVISIONS if d["key"] == body.service_key), None)
    deal = {
        "id": str(uuid.uuid4()),
        "service_key": body.service_key,
        "service_name": division["name"] if division else body.service_key,
        "org_name": body.org_name,
        "description": body.description,
        "budget_cents": body.budget_cents,
        "value_cents": body.budget_cents or 0,
        "stage": "lead",
        "status": "open",
        "proposal": None,
        "proposal_provider": None,
        "human_approval": False,
        "created_by": user.id,
        "created_by_name": user.full_name,
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.abo_deals.insert_one(deal)
    try:
        await audit(user.id, "abo.deal_created", meta={"deal_id": deal["id"], "org": body.org_name})
    except Exception:
        pass
    deal.pop("_id", None)
    return deal


# ── PATCH /abo/deals/{deal_id} ───────────────────────────────────────────────
class DealUpdate(BaseModel):
    stage: Optional[str] = None
    note: Optional[str] = None
    value_cents: Optional[int] = None


@router.patch("/abo/deals/{deal_id}")
async def update_deal(deal_id: str, body: DealUpdate, user: User = Depends(_require_rank("admin", "executive_admin"))):
    deal = await db.abo_deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(404, "Deal not found")
    updates = {"updated_at": _now()}
    if body.stage:
        updates["stage"] = body.stage
        if body.stage in ("won", "delivered"):
            updates["status"] = "closed"
    if body.value_cents is not None:
        updates["value_cents"] = body.value_cents
    if body.note:
        updates["last_note"] = body.note
    await db.abo_deals.update_one({"id": deal_id}, {"$set": updates})
    try:
        await audit(user.id, "abo.deal_updated", meta={"deal_id": deal_id, "updates": list(updates.keys())})
    except Exception:
        pass
    return {"ok": True}


# ── POST /abo/deals/{deal_id}/propose ────────────────────────────────────────
@router.post("/abo/deals/{deal_id}/propose")
async def propose_deal(deal_id: str, user: User = Depends(_require_rank("admin", "executive_admin"))):
    deal = await db.abo_deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(404, "Deal not found")

    # Generate a proposal using the LLM gateway
    proposal_text = (
        f"PROPOSAL for {deal['org_name']}\n\n"
        f"Service: {deal['service_name']}\n"
        f"Scope: {deal['description']}\n"
        f"Budget: ${deal.get('budget_cents', 0) / 100:.2f}\n\n"
        f"We propose to deliver the following:\n"
        f"1. Initial assessment and planning (1-2 days)\n"
        f"2. Core deliverables based on scope\n"
        f"3. Review and revision cycle\n"
        f"4. Final delivery and handoff\n\n"
        f"Timeline: 2-4 weeks from approval\n"
        f"Terms: Payment on delivery milestones. Human approval required before each phase."
    )

    try:
        from ai.llm_gateway import chat_completion
        result = await chat_completion(
            system="You are a business office assistant. Draft a professional service proposal based on the deal details. Be specific about deliverables, timeline, and terms. Keep it concise.",
            messages=[{"role": "user", "content": f"Draft a proposal for this deal:\nService: {deal['service_name']}\nClient: {deal['org_name']}\nDescription: {deal['description']}\nBudget: ${deal.get('budget_cents', 0) / 100:.2f}"}],
            max_tokens=500,
        )
        proposal_text = result.get("text", proposal_text)
        provider = result.get("provider", "gateway")
    except Exception as e:
        logger.warning("ABO proposal AI failed: %s — using template", e)
        provider = "template"

    await db.abo_deals.update_one(
        {"id": deal_id},
        {"$set": {"proposal": proposal_text, "proposal_provider": provider, "updated_at": _now()}}
    )
    try:
        await audit(user.id, "abo.deal_proposed", meta={"deal_id": deal_id})
    except Exception:
        pass
    return {"ok": True, "provider": provider}


# ── GET /abo/jobs ────────────────────────────────────────────────────────────
@router.get("/abo/jobs")
async def abo_jobs(user: User = Depends(_dep_current_user)):
    jobs = await db.abo_jobs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    cfg = await _get_config()

    human_jobs = [j for j in jobs if j.get("worker_type") == "human"]
    ai_jobs = [j for j in jobs if j.get("worker_type") != "human"]
    human_pay = sum(j.get("pay_cents", 0) for j in human_jobs)
    ai_value = sum(j.get("value_cents", 0) for j in ai_jobs)
    total_hours = sum(j.get("hours", 0) for j in jobs)

    # Net profit available for distributions
    month_rev = await _get_month_revenue_cents()
    infra = cfg.get("infra_cost_cents", 8000)
    net_profit = max(0, month_rev - infra)

    return {
        "jobs": jobs,
        "human_jobs": len(human_jobs),
        "ai_jobs": len(ai_jobs),
        "human_pay_cents": human_pay,
        "ai_value_cents": ai_value,
        "net_profit_available_cents": net_profit,
        "total_hours": total_hours,
        "pay_note": "Human pay is performance-linked: commissions on closed business or distributions from net profit, payable only when the office is profitable, at the owner's direction.",
    }


# ── POST /abo/jobs ───────────────────────────────────────────────────────────
class JobReq(BaseModel):
    title: str
    persona: str = ""
    division: str = "memberships"
    hours: float = 0
    worker_type: Literal["human", "ai"] = "ai"
    pay_cents: int = 0
    pay_type: Optional[str] = None
    commission_pct: Optional[float] = None
    value_cents: int = 0


@router.post("/abo/jobs")
async def create_job(body: JobReq, user: User = Depends(_require_rank("admin", "executive_admin"))):
    job = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "persona": body.persona,
        "division": body.division,
        "hours": body.hours,
        "worker_type": body.worker_type,
        "pay_cents": body.pay_cents,
        "pay_type": body.pay_type,
        "commission_pct": body.commission_pct,
        "value_cents": body.value_cents,
        "status": "assigned",
        "created_by": user.id,
        "created_at": _now(),
    }
    await db.abo_jobs.insert_one(job)
    try:
        await audit(user.id, "abo.job_created", meta={"job_id": job["id"], "title": body.title})
    except Exception:
        pass
    job.pop("_id", None)
    return job


# ── GET /abo/exchange ────────────────────────────────────────────────────────
@router.get("/abo/exchange")
async def abo_exchange(user: User = Depends(_dep_current_user)):
    contracts = await db.abo_exchange_contracts.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"contracts": contracts, "total": len(contracts)}


# ── POST /abo/exchange/contracts ─────────────────────────────────────────────
class ExchangeReq(BaseModel):
    title: str
    description: str = ""
    requester_persona: str = ""
    provider_persona: str = ""
    value_cents: int = 0


@router.post("/abo/exchange/contracts")
async def create_exchange_contract(body: ExchangeReq, user: User = Depends(_require_rank("admin", "executive_admin"))):
    cfg = await _get_config()
    fee_pct = cfg.get("clearinghouse_fee_pct", 15)
    fee = int(body.value_cents * fee_pct / 100) if body.value_cents else 0

    contract = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "description": body.description,
        "requester_persona": body.requester_persona,
        "provider_persona": body.provider_persona,
        "value_cents": body.value_cents,
        "clearinghouse_fee_cents": fee,
        "status": "pending",
        "created_by": user.id,
        "created_at": _now(),
    }
    await db.abo_exchange_contracts.insert_one(contract)
    try:
        await audit(user.id, "abo.exchange_created", meta={"contract_id": contract["id"]})
    except Exception:
        pass
    contract.pop("_id", None)
    return contract


# ── GET /abo/redteam ─────────────────────────────────────────────────────────
@router.get("/abo/redteam")
async def abo_redteam(user: User = Depends(_dep_current_user)):
    engagements = await db.abo_redteam_engagements.find({}, {"_id": 0}).sort("created_at", -1).to_list(20)
    return {"engagements": engagements, "total": len(engagements)}


# ── POST /abo/redteam/engagements ────────────────────────────────────────────
class RedteamReq(BaseModel):
    title: str
    target: str = ""
    description: str = ""


@router.post("/abo/redteam/engagements")
async def create_redteam_engagement(body: RedteamReq, user: User = Depends(_require_rank("admin", "executive_admin"))):
    cfg = await _get_config()
    engagement = {
        "id": str(uuid.uuid4()),
        "title": body.title,
        "target": body.target,
        "description": body.description,
        "price_cents": cfg.get("redteam_oneshot_cents", 25000),
        "status": "pending",
        "human_approved": False,
        "created_by": user.id,
        "created_at": _now(),
    }
    await db.abo_redteam_engagements.insert_one(engagement)
    try:
        await audit(user.id, "abo.redteam_created", meta={"engagement_id": engagement["id"]})
    except Exception:
        pass
    engagement.pop("_id", None)
    return engagement


# ── GET /abo/agenda ──────────────────────────────────────────────────────────
@router.get("/abo/agenda")
async def abo_agenda(user: User = Depends(_dep_current_user)):
    items = await db.abo_agenda.find({}, {"_id": 0}).sort("created_at", -1).to_list(30)
    return {"agenda": items}


# ── PATCH /abo/agenda/{item_id} ──────────────────────────────────────────────
class AgendaUpdate(BaseModel):
    status: str


@router.patch("/abo/agenda/{item_id}")
async def update_agenda(item_id: str, body: AgendaUpdate, user: User = Depends(_require_rank("admin", "executive_admin"))):
    result = await db.abo_agenda.update_one(
        {"item_id": item_id},
        {"$set": {"status": body.status, "updated_at": _now()}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Agenda item not found")
    try:
        await audit(user.id, "abo.agenda_updated", meta={"item_id": item_id, "status": body.status})
    except Exception:
        pass
    return {"ok": True}


# ── GET /abo/admin/overview ──────────────────────────────────────────────────
@router.get("/abo/admin/overview")
async def abo_admin_overview(user: User = Depends(_require_rank("admin", "executive_admin"))):
    deals = await db.abo_deals.find({}, {"_id": 0}).to_list(200)
    jobs = await db.abo_jobs.find({}, {"_id": 0}).to_list(200)
    cfg = await _get_config()

    # Revenue by stage
    stage_counts = {}
    for d in deals:
        s = d.get("stage", "lead")
        stage_counts[s] = stage_counts.get(s, 0) + 1

    # Revenue by product (from payments)
    try:
        pipeline = [
            {"$match": {"status": {"$in": ["paid", "completed", "fulfilled"]}}},
            {"$group": {"_id": "$product_name", "total": {"$sum": "$amount_cents"}, "count": {"$sum": 1}}},
            {"$sort": {"total": -1}},
            {"$limit": 10},
        ]
        by_product = await db.payments.aggregate(pipeline).to_list(10)
    except Exception:
        by_product = []

    return {
        "deals": {"total": len(deals), "by_stage": stage_counts},
        "jobs": {"total": len(jobs), "human": len([j for j in jobs if j.get("worker_type") == "human"]), "ai": len([j for j in jobs if j.get("worker_type") != "human"])},
        "revenue_by_product": [{"name": p.get("_id", "Unknown"), "total_cents": p.get("total", 0), "orders": p.get("count", 0)} for p in by_product],
        "config": {k: v for k, v in cfg.items() if k not in ("_id", "updated_at", "updated_by")},
    }


# ── GET /abo/config ──────────────────────────────────────────────────────────
@router.get("/abo/config")
async def abo_config(user: User = Depends(_require_rank("admin", "executive_admin"))):
    cfg = await _get_config()
    cfg.pop("_id", None)
    return cfg


# ── PUT /abo/config ──────────────────────────────────────────────────────────
@router.put("/abo/config")
async def update_abo_config(request: Request, user: User = Depends(_require_rank("admin", "executive_admin"))):
    body = await request.json()
    # Only allow known keys
    allowed = set(_DEFAULT_CONFIG.keys())
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "No valid config keys provided")
    await _save_config(updates, user)
    cfg = await _get_config()
    cfg.pop("_id", None)
    return cfg


# ── GET /abo/verify (Truth Test) ────────────────────────────────────────────
@router.get("/abo/verify")
async def abo_verify(user: User = Depends(_require_rank("admin", "executive_admin")), explain: int = Query(0)):
    """Deterministic truth test: verify every office claim against the real ledger."""
    cfg = await _get_config()
    month_rev = await _get_month_revenue_cents()
    total_rev = await _get_total_revenue_cents()
    order_count = await _get_order_count()
    paying_members = await _get_paying_members()
    contracted = await _get_contracted_cents()

    monthly_goal = cfg.get("monthly_goal_cents", 50000)
    infra_cost = cfg.get("infra_cost_cents", 8000)

    checks = {
        "revenue_positive": {"pass": month_rev >= 0, "value": month_rev},
        "orders_exist": {"pass": order_count > 0, "value": order_count},
        "paying_members_exist": {"pass": paying_members > 0, "value": paying_members},
        "goal_is_reasonable": {"pass": 1000 <= monthly_goal <= 10000000, "value": monthly_goal},
        "infra_costs_set": {"pass": infra_cost > 0, "value": infra_cost},
        "net_profit_non_negative": {"pass": max(0, month_rev - infra_cost) >= 0, "value": max(0, month_rev - infra_cost)},
    }

    passed = sum(1 for c in checks.values() if c["pass"])
    total = len(checks)

    result = {
        "timestamp": _now(),
        "checks": checks,
        "summary": f"{passed}/{total} checks passed",
        "all_pass": passed == total,
    }

    if explain:
        try:
            from ai.llm_gateway import chat_completion
            resp = await chat_completion(
                system="You are a business analyst. Explain the audit results in plain language. Be honest about what passes and what needs attention.",
                messages=[{"role": "user", "content": f"Audit results: {result}. Explain what this means for the business."}],
                max_tokens=300,
            )
            result["explanation"] = resp.get("text", "")
        except Exception:
            result["explanation"] = "AI explanation unavailable."

    return result


# ── GET /abo/public-status (for public-facing widgets) ───────────────────────
@router.get("/abo/public-status")
async def abo_public_status():
    """Public status — no auth required. Shows mission progress."""
    cfg = await _get_config()
    month_rev = await _get_month_revenue_cents()
    monthly_goal = cfg.get("monthly_goal_cents", 50000)
    month_pct = round(month_rev / max(monthly_goal, 1) * 100, 1)

    return {
        "monthly_goal_cents": monthly_goal,
        "month_revenue_cents": month_rev,
        "month_pct": month_pct,
        "status": "covered" if month_pct >= 100 else "on_track" if month_pct >= 70 else "watch" if month_pct >= 30 else "critical",
    }


# ── GET/POST /abo/source — THE SOURCE (root protocol) live status ───────────
# The Source Protocol engine already lives in ai/source_protocol.py and is
# composed into every AI prompt at the gateway. These endpoints expose it so
# the Business Office panel reads and drives the real system, not a mock.

@router.get("/abo/source")
async def abo_source(user: User = Depends(_dep_current_user)):
    """Live Source protocol status — every read re-audits and reports drift."""
    try:
        from ai.source_protocol import run_maintenance
        return run_maintenance()
    except Exception as e:
        logger.warning("abo/source failed: %s", e)
        raise HTTPException(500, f"Source protocol status unavailable: {e}")


@router.get("/abo/source/controls")
async def abo_source_controls(user: User = Depends(_dep_current_user)):
    """Current Human Control sliders — any signed-in member may read."""
    try:
        from ai.source_protocol import (
            get_controls, CONTROL_ORDER, CONTROL_DEFAULTS,
            _CONTROL_LABELS, _CONTROL_HINTS,
        )
        return {
            "controls": get_controls(),
            "order": list(CONTROL_ORDER),
            "labels": dict(_CONTROL_LABELS),
            "hints": dict(_CONTROL_HINTS),
            "defaults": dict(CONTROL_DEFAULTS),
        }
    except Exception as e:
        logger.warning("abo/source/controls failed: %s", e)
        raise HTTPException(500, f"Source controls unavailable: {e}")


@router.post("/abo/source/controls")
async def abo_source_controls_save(
    body: dict,
    user: User = Depends(_require_rank("executive_admin", "admin")),
):
    """Persist the executive's sliders — they compile into every AI prompt."""
    controls = body.get("controls")
    if not isinstance(controls, dict):
        raise HTTPException(400, "controls must be an object of knob -> 0..100")
    try:
        from ai.source_protocol import set_controls
        new = set_controls(controls)
    except Exception as e:
        logger.warning("abo/source/controls save failed: %s", e)
        raise HTTPException(500, f"Could not apply controls: {e}")
    now = datetime.now(timezone.utc).isoformat()
    await db.source_controls.update_one(
        {"_id": "master"},
        {"$set": {"controls": new, "updated_by": user.id, "updated_at": now}},
        upsert=True,
    )
    return {"controls": new, "updated_at": now}


# ── POST /abo/goals — set the monthly revenue goal ──────────────────────────
@router.post("/abo/goals")
async def abo_set_goals(body: dict, user: User = Depends(_require_rank("executive_admin", "admin"))):
    """Set the ABO monthly revenue goal (cents). Persisted in the config singleton."""
    monthly = body.get("monthly_goal_cents")
    if not isinstance(monthly, int) or monthly <= 0:
        raise HTTPException(400, "monthly_goal_cents must be a positive integer")
    await _save_config({"monthly_goal_cents": monthly}, user)
    return {"ok": True, "monthly_goal_cents": monthly}
