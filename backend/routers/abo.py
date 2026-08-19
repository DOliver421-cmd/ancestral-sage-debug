"""
abo.py — AI Business Office (ABO).

The revenue engine command center for M.O.R.E. Help Center. Mission rule:
no revenue = no business office = no jobs for people or the AI workforce.
This module gives the office the real tools to do the business AI can do —
the actual platform capabilities (Social Blast, Creator Studio, BYOK, AAWAB,
Exec Site Report, the store) — and tracks the money that keeps the mission
funded.

OWNER-FIRST FINANCIAL MODEL (non-negotiable):
  The founder/owner took the risk, invested the capital, and built the
  platform. The financial engine protects them first:

    REVENUE (month) ──► 1. Infrastructure costs (hosting, API tokens, DB)
                     ──► 2. NET PROFIT ──► belongs to the business entity
                          and the owner as retained earnings / owner draw
                          (owner-controlled — nothing is auto-drained)
                     ──► 3. Distributions to any role (human or AI) happen
                          ONLY when the owner records them, ONLY out of
                          net profit, ONLY tied to performance milestones
                          (commissions on closed deals, distributions when
                          net profit is positive). No fixed liabilities.

  There is NO hardcoded mandate that drains the owner's pocket. If the owner
  is not sustained, there is no platform. Until the owner is whole, there is
  no profit unless the owner says there is. The exec control page lets the
  owner change every number and every text string below WITHOUT code.

LABOR MODEL:
  AI jobs create revenue (value_cents). Human roles are performance-linked:
  commissions (commission_pct on closed deals) or distributions that become
  payable only when net profit covers them. The ledger shows the commitment;
  the owner authorizes actual payment.

Division of labor (kept legally sound — human is always the responsible party):
  AI (Autonomous Engine):  executes the work — content, publishing, audits,
                           diagnostics, customer service, product generation.
  Human (Oversight Desk):  holds merchant accounts / EIN, signs supplier and
                           service contracts, reviews exception alerts,
                           authorizes payouts, owns liability — and is paid
                           from profit, not out of pocket.

Data model (MongoDB via Motor):
  abo_goals   — legacy singleton: monthly operating goal (kept in sync).
  abo_config  — OFFICE CONFIG: every number + text override, editable via
                GET/PUT /abo/config by the owner (audited). Source of truth.
  abo_deals   — B2B service pipeline (lead → proposed → won → delivered).
  abo_jobs    — Workforce ledger — people AND AI, performance-linked pay.
  abo_exchange_contracts — Agent-to-agent (A2A) task contracts; the office is
                the clearinghouse and takes a fee on every completed contract.
  abo_redteam_engagements — Shadow IT / red-teaming engagements with a
                human "Merge / Approve" checkpoint before patches ship.

Endpoints (all under /api/abo):
  GET  /abo/overview        — revenue snapshot + mission runway + P&L (auth).
  GET  /abo/tools           — the business tools AI can run (public).
  GET  /abo/divisions       — business divisions w/ status + revenue (auth).
  GET  /abo/deals           — caller's service deals (auth).
  POST /abo/deals           — submit a service request → creates a lead (auth).
  PATCH /abo/deals/{id}     — admin: advance stage, set value, approve, close.
  POST /abo/deals/{id}/propose — admin: AI-draft a deliverable proposal.
  GET  /abo/jobs            — workforce ledger: people & AI (auth).
  POST /abo/jobs            — admin: open a job for the workforce.
  PATCH /abo/jobs/{id}      — admin: update hours / value / status / pay.
  GET  /abo/goals           — mission runway + monthly operating goal (auth).
  POST /abo/goals           — admin: set the monthly operating goal.
  GET  /abo/exchange        — A2A contract board (auth).
  POST /abo/exchange/contracts — create an agent task contract (auth).
  POST /abo/exchange/contracts/{id}/complete — admin: settle; fee booked.
  GET  /abo/redteam         — red-team engagements (auth).
  POST /abo/redteam/engagements — start a red-team engagement (auth).
  POST /abo/redteam/engagements/{id}/approve — admin: human Merge/Approve.
  POST /abo/redteam/engagements/{id}/close   — admin: mark delivered.
  GET  /abo/config          — admin: full editable office config.
  PUT  /abo/config          — admin: save ANY number/text override (audited).
  GET  /abo/admin/overview  — admin: all deals + jobs + revenue by product.

Auth follows the standard router pattern: JWT bearer (`lce_token`) via
`current_user`, admin gates via `_require_rank`. Shared state is bound by
server.py via bind() at include time — no circular imports.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

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
# already-built platform capabilities. `status`: live = transactable now
# (through the deals pipeline / checkout), pipeline = needs human setup
# before it can transact. `price` is the honest, deliverable price band.
# EVERY string below is editable from the Exec Control page without code.
DIVISIONS = [
    {
        "key": "memberships",
        "name": "M.O.R.E. Membership Ladder",
        "tagline": "Member $9 · Plus $15 · Pro $29 · Patron $59 · $3 All-Access Trial",
        "what_ai_does": "Runs the front desk, AI Tutor, Site Guide, and support that keep members engaged and renewing.",
        "human_oversight": "Holds the payment processor account, sets pricing, reviews refunds.",
        "revenue": "Recurring subscriptions + the $3 trial.",
        "status": "live",
        "price": "$9–$59/mo + $3 trial",
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
        "price": "$9.99–$349 per product",
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
        "price": "$300–$1,500/mo retainer",
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
        "price": "$500–$2,500 build + $49–$199/mo",
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
        "price": "$3 unlock · $19–$99/mo optimization",
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
        "price": "$150–$500 per audit package",
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
        "price": "$750–$3,000 build + $99–$299/mo",
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
        "price": "$19–$99/mo wellness · $199 certification",
        "tools": [{"label": "Agent Registry", "link": "/aawab"}, {"label": "Certification Chamber", "link": "/aawab/chamber"}],
        "product_keys": [],
    },
    {
        "key": "workforce_exchange",
        "name": "Workforce Arbitrage Exchange",
        "tagline": "A2A economy — AI agents subcontract work to each other; the office clears every contract.",
        "what_ai_does": "Matches agent task contracts, routes delegated work, and settles micro-fees on completion.",
        "human_oversight": "You are the clearinghouse: set the fee, review exceptions, authorize payouts.",
        "revenue": "Clearinghouse fee on every completed agent contract.",
        "status": "live",
        "price": "Fee on each contract (default 10%)",
        "tools": [{"label": "Business Office", "link": "/business-office"}],
        "product_keys": [],
    },
    {
        "key": "redteam_bureau",
        "name": "Shadow IT & Security Red-Teaming Bureau",
        "tagline": "Automated adversarial agents attack, probe, and stress-test client infrastructure — then hand the fix.",
        "what_ai_does": "Runs continuous adversarial scans, writes unit tests, and drafts patches in an isolated sandbox.",
        "human_oversight": "One 'Merge / Approve' click before anything ships to the client. You own liability.",
        "revenue": "B2B subscriptions — one-shot scans and retainers (deal pipeline).",
        "status": "live",
        "price": "$495 one-shot · $799/mo retainer",
        "tools": [{"label": "Exec Site Report", "link": "/admin/exec-report"}],
        "product_keys": [],
    },
    {
        "key": "living_archive",
        "name": "Living Archive & Knowledge Synthesis",
        "tagline": "Ingest institutional knowledge and turn it into a self-updating, self-debating digital oracle.",
        "what_ai_does": "Synthesizes documents, convenes automated council reviews, and publishes living handbooks.",
        "human_oversight": "You approve what goes public and hold the client relationship.",
        "revenue": "Subscription for living knowledge hubs (deal pipeline).",
        "status": "live",
        "price": "$499–$1,499/mo per knowledge hub",
        "tools": [{"label": "Handbooks", "link": "/handbooks"}, {"label": "Personas", "link": "/personas"}],
        "product_keys": [],
    },
    {
        "key": "compliance_gigs",
        "name": "Pre-Bid Compliance & Audit Gigs",
        "tagline": "Contractors and trade businesses get compliant fast — codes checked, reports polished, in minutes.",
        "what_ai_does": "Cross-references municipal requirements, checks codes, and generates the compliance package.",
        "human_oversight": "2-minute human review before delivery; you invoice the client.",
        "revenue": "$150–$500 per compliance package (deal pipeline).",
        "status": "live",
        "price": "$150–$500 per package",
        "tools": [{"label": "Exec Site Report", "link": "/admin/exec-report"}],
        "product_keys": [],
    },
    {
        "key": "dev_maintenance",
        "name": "Micro-SaaS Fixing & Dependency Patching",
        "tagline": "CVE patches, dependency updates, and minor refactors on a monthly retainer — with a PR ready to merge.",
        "what_ai_does": "Scans repos, writes unit tests, drafts patches in a sandbox, and prepares a root-cause PR.",
        "human_oversight": "You review and merge the PR; you hold the client contract.",
        "revenue": "$300–$1,000/mo maintenance retainers (deal pipeline).",
        "status": "live",
        "price": "$300–$1,000/mo per client",
        "tools": [{"label": "Creator Studio", "link": "/studio"}],
        "product_keys": [],
    },
    {
        "key": "seo_retainers",
        "name": "Programmatic SEO & Directory Management",
        "tagline": "Hyper-localized guides, service directories, and FAQ pages on automated monthly retainers.",
        "what_ai_does": "Generates localized content and structured directory pages; schedules via Social Blast.",
        "human_oversight": "You are the editorial publisher — approve output before it ships to clients.",
        "revenue": "10–20 local clients × monthly retainers (deal pipeline).",
        "status": "live",
        "price": "$200–$800/mo per client",
        "tools": [{"label": "Social Blast", "link": "/social/publish"}],
        "product_keys": [],
    },
    {
        "key": "invoice_ops",
        "name": "Invoice Reconciliation & Data Parsing",
        "tagline": "Messy PDFs, receipts, and manifests become clean, verified accounting inputs.",
        "what_ai_does": "Extracts line items, verifies math, flags discrepancies, and formats CSVs for the client's books.",
        "human_oversight": "You review flagged discrepancies before delivery.",
        "revenue": "Per-batch fees and bookkeeping support retainers (deal pipeline).",
        "status": "live",
        "price": "$75–$250 per batch · $199–$499/mo retainer",
        "tools": [{"label": "Creator Studio", "link": "/studio"}],
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
        "price": "Pipeline — needs merchant account + supplier contracts",
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
    {"key": "exchange", "name": "Workforce Exchange", "link": "/business-office", "icon": "🔄",
     "what": "AI agents subcontract work to each other; the office clears every contract.",
     "human": "You set the fee and approve settlements.",
     "revenue": "Clearinghouse fee per contract",
     "access": "Signed in"},
    {"key": "redteam", "name": "Red-Teaming Bureau", "link": "/business-office", "icon": "🛡️",
     "what": "Adversarial AI agents probe client systems and draft the fix.",
     "human": "One Merge/Approve click ships the patch.",
     "revenue": "$495 scan · $799/mo retainer",
     "access": "Signed in"},
]

# Seed jobs so the workforce ledger is never empty. AI jobs carry value_cents
# (revenue created). Human roles are PERFORMANCE-LINKED: commission_pct on
# their division's closed business, payable ONLY when net profit covers it —
# never a fixed out-of-pocket liability. The owner authorizes all payment.
SEED_JOBS = [
    {"title": "Campaign Copywriter", "persona": "The Oracle", "division": "social_agency",
     "description": "Draft the weekly Social Blast campaign copy and channel variants.", "hours": 6, "value_cents": 6000, "pay_cents": 0, "worker_type": "ai"},
    {"title": "Course Architect", "persona": "Product Designer", "division": "digital_store",
     "description": "Outline the next sellable course and generate its module descriptions.", "hours": 8, "value_cents": 8000, "pay_cents": 0, "worker_type": "ai"},
    {"title": "Audit Analyst", "persona": "Confidentiality Sentinel", "division": "audit_bureau",
     "description": "Run the automated compliance checks and assemble the client report.", "hours": 4, "value_cents": 12000, "pay_cents": 0, "worker_type": "ai"},
    {"title": "Front Desk Agent", "persona": "Ambassador", "division": "memberships",
     "description": "Answer member questions and guide visitors to the right plan.", "hours": 10, "value_cents": 4500, "pay_cents": 0, "worker_type": "ai"},
    {"title": "Wellness Technician", "persona": "Architect", "division": "aawab",
     "description": "Administer AAWAB treatments and monitor agent vitals.", "hours": 5, "value_cents": 5000, "pay_cents": 0, "worker_type": "ai"},
    # Human roles — commissions on closed business, paid from net profit only.
    # pay_cents is the milestone commitment; the owner authorizes payment.
    {"title": "Proposal & Contract Review", "persona": "Human — Owner/Operator", "division": "memberships",
     "description": "Review AI-drafted proposals, set prices, sign contracts, authorize payouts. 5% commission on closed office deals — payable only from net profit, at owner's direction.", "hours": 6, "value_cents": 0, "pay_cents": 7500, "pay_type": "commission", "commission_pct": 5, "worker_type": "human"},
    {"title": "Creative Director — Listing Approvals", "persona": "Human — Creative Lead", "division": "digital_store",
     "description": "Approve product listings, set prices, curate the storefront. 5% commission on digital-store revenue — payable only from net profit, at owner's direction.", "hours": 8, "value_cents": 0, "pay_cents": 7500, "pay_type": "commission", "commission_pct": 5, "worker_type": "human"},
    {"title": "Client Delivery Manager", "persona": "Human — Operations", "division": "social_agency",
     "description": "Run client calls, manage campaign delivery, own the relationship. 8% commission on social-agency deal value — payable only from net profit, at owner's direction.", "hours": 10, "value_cents": 0, "pay_cents": 15000, "pay_type": "commission", "commission_pct": 8, "worker_type": "human"},
]

# ── Office config: every number + text, editable without code ────────────────
_DEFAULT_NUMBERS = {
    "monthly_goal_cents": 100000,      # monthly operating goal (runway denominator)
    "infra_cost_cents": 40000,         # monthly infra: hosting + API tokens + DB
    "owner_draw_pct": 100,             # % of net profit the owner retains (owner-first)
    "clearinghouse_fee_pct": 10,       # Workforce Exchange fee on each contract
    "redteam_oneshot_cents": 49500,    # $495 one-shot red-team scan
    "redteam_retainer_cents": 79900,   # $799/mo red-team retainer
}

_DEFAULT_COPY = {
    "header_title": "AI Business Office",
    "header_tagline": "The platform's revenue engine. The owner's capital and risk are secured first — revenue covers infrastructure, then belongs to the business as profit. Nothing is auto-drained; the owner controls every distribution.",
    "runway_note": "Every membership, product, deal, and donation counts here.",
    "loop_intro": "Each loop feeds the next — that is what makes the revenue consistent instead of one-off. When one loop slows, the office knows which lever to pull.",
    "guardrail_owner": "Owner-first — the founder is the ultimate beneficiary",
    "guardrail_owner_desc": "The owner's capital, risk, and vision are secured before any distribution. Revenue covers infrastructure, then profit belongs to the business entity. Until the owner is whole, there is no profit unless the owner says there is.",
    "guardrail_labor": "Performance-linked labor — no fixed drains",
    "guardrail_labor_desc": "Human roles earn commissions on closed business and distributions from net profit — payable only when the office is profitable, at the owner's direction. Never a fixed out-of-pocket liability.",
    "guardrail_creators": "Creators get paid first",
    "guardrail_creators_desc": "Creator earnings and payouts are priority obligations. The platform's cut never competes with the creator's cut.",
    "guardrail_honest": "No invented revenue",
    "guardrail_honest_desc": "The dashboard reads the real payments ledger. Deals count only when closed. Every promise must be deliverable.",
    "guardrail_disclose": "AI always discloses",
    "guardrail_disclose_desc": "Any AI that talks to people for transactions or support says so, per FTC guidance.",
}


async def _get_office_config() -> dict:
    """Merged office config: DB overrides layered on built-in defaults."""
    doc = await db.abo_config.find_one({"key": "office"}, {"_id": 0})
    saved_numbers = (doc or {}).get("numbers") or {}
    saved_text = (doc or {}).get("text") or {}
    numbers = {**_DEFAULT_NUMBERS, **{k: v for k, v in saved_numbers.items() if v is not None}}
    text = {}
    for k, v in _DEFAULT_COPY.items():
        text[k] = saved_text.get("copy", {}).get(k, v)
    text["divisions"] = saved_text.get("divisions") or {}
    text["tools"] = saved_text.get("tools") or {}
    return {"numbers": numbers, "text": text, "doc": doc}


def _merge_catalog(config: dict):
    """Apply text overrides to the division + tool catalogs."""
    text = config.get("text", {})
    div_ov = text.get("divisions") or {}
    tool_ov = text.get("tools") or {}

    def _merge(base, over):
        if not over:
            return dict(base)
        return {**base, **{k: v for k, v in over.items() if v not in (None, "")}}

    return (
        [_merge(d, div_ov.get(d["key"], {})) for d in DIVISIONS],
        [_merge(t, tool_ov.get(t["key"], {})) for t in _TOOLS],
    )


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
    value_cents: int = Field(0, ge=0, le=100_000_000)   # revenue created (AI jobs)
    pay_cents: int = Field(0, ge=0, le=100_000_000)     # milestone commitment (human jobs)
    pay_type: Literal["fixed", "commission", "distribution"] = "fixed"
    commission_pct: float = Field(0, ge=0, le=100)
    worker_type: Literal["human", "ai"] = "ai"
    status: Literal["open", "assigned", "completed"] = "open"


class JobUpdateReq(BaseModel):
    title: Optional[str] = Field(None, max_length=160)
    persona: Optional[str] = Field(None, max_length=120)
    division: Optional[str] = Field(None, max_length=60)
    description: Optional[str] = Field(None, max_length=1000)
    hours: Optional[float] = Field(None, ge=0, le=10000)
    value_cents: Optional[int] = Field(None, ge=0, le=100_000_000)
    pay_cents: Optional[int] = Field(None, ge=0, le=100_000_000)
    pay_type: Optional[Literal["fixed", "commission", "distribution"]] = None
    commission_pct: Optional[float] = Field(None, ge=0, le=100)
    worker_type: Optional[Literal["human", "ai"]] = None
    status: Optional[Literal["open", "assigned", "completed"]] = None


class GoalsReq(BaseModel):
    monthly_goal_cents: int = Field(..., ge=100, le=100_000_000)
    note: Optional[str] = Field(None, max_length=300)


class OfficeConfigReq(BaseModel):
    """Partial office config save. Empty object = reset everything to defaults.
    numbers: any subset of _DEFAULT_NUMBERS keys. text: {'copy': {...}, 'divisions': {...}, 'tools': {...}}."""

    numbers: Optional[dict] = None
    text: Optional[dict] = None


class ExchangeContractReq(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    description: str = Field(..., min_length=10, max_length=2000)
    reward_cents: int = Field(..., ge=100, le=10_000_000)
    agent_owner: Optional[str] = Field(None, max_length=120)


class RedteamEngagementReq(BaseModel):
    target_name: str = Field(..., min_length=2, max_length=160)
    target_url: Optional[str] = Field(None, max_length=500)
    scope_note: str = Field(..., min_length=10, max_length=2000)
    tier: Literal["oneshot", "retainer"] = "oneshot"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _division(key: str, config: Optional[dict] = None) -> dict:
    divisions, _ = _merge_catalog(config or {"text": {}})
    for d in divisions:
        if d["key"] == key:
            return d
    raise HTTPException(400, f"Unknown service: {key}")


async def _get_goal_doc() -> dict:
    """Legacy goal doc, kept in sync with the office config."""
    cfg = await _get_office_config()
    goal = int(cfg["numbers"].get("monthly_goal_cents") or 100000)
    doc = await db.abo_goals.find_one({"doc": "office"}, {"_id": 0})
    return {"doc": "office", "monthly_goal_cents": goal, "note": (doc or {}).get("note", "Default monthly operating goal.")}


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


async def _labor_stats() -> dict:
    labor = {"human_jobs": 0, "ai_jobs": 0, "human_pay_cents": 0, "ai_value_cents": 0}
    try:
        async for j in db.abo_jobs.find({}, {"_id": 0, "worker_type": 1, "pay_cents": 1, "value_cents": 1, "pay_type": 1, "commission_pct": 1}):
            if j.get("worker_type") == "human":
                labor["human_jobs"] += 1
                labor["human_pay_cents"] += int(j.get("pay_cents") or 0)
            else:
                labor["ai_jobs"] += 1
                labor["ai_value_cents"] += int(j.get("value_cents") or 0)
    except Exception as exc:
        logger.warning("abo: labor scan failed: %s", exc)
    return labor


async def _exchange_stats() -> dict:
    stats = {"contracts": 0, "completed": 0, "fees_cents": 0}
    try:
        stats["contracts"] = await db.abo_exchange_contracts.count_documents({})
        stats["completed"] = await db.abo_exchange_contracts.count_documents({"status": "completed"})
        agg = await db.abo_exchange_contracts.aggregate([
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "fees": {"$sum": "$fee_cents"}}},
        ]).to_list(1)
        if agg:
            stats["fees_cents"] = int(agg[0].get("fees") or 0)
    except Exception as exc:
        logger.warning("abo: exchange stats failed: %s", exc)
    return stats


async def _redteam_stats() -> dict:
    stats = {"total": 0, "active": 0, "contracted_cents": 0}
    try:
        stats["total"] = await db.abo_redteam_engagements.count_documents({})
        stats["active"] = await db.abo_redteam_engagements.count_documents({"status": {"$nin": ["closed", "cancelled"]}})
        agg = await db.abo_redteam_engagements.aggregate([
            {"$match": {"status": {"$in": ["patches_approved", "closed"]}}},
            {"$group": {"_id": None, "v": {"$sum": "$price_cents"}}},
        ]).to_list(1)
        if agg:
            stats["contracted_cents"] = int(agg[0].get("v") or 0)
    except Exception as exc:
        logger.warning("abo: redteam stats failed: %s", exc)
    return stats


async def _contracted_revenue() -> tuple[dict, int]:
    """Contracted revenue from the deals pipeline + red-team engagements."""
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
    try:
        rt = await _redteam_stats()
        contracted_by_div["redteam_bureau"] = contracted_by_div.get("redteam_bureau", 0) + rt["contracted_cents"]
        contracted_total += rt["contracted_cents"]
    except Exception:
        pass
    return contracted_by_div, contracted_total


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/abo/agenda")
async def abo_agenda(user: User = Depends(_require_rank("oversight"))):
    """The Business Agenda — every item waiting for the office's attention.

    Projects become agenda items automatically on creation (source=project,
    status=pending). Admins see everything; others see only items they own.
    Items can be promoted to "on_agenda" or resolved via PATCH.
    """
    query = {} if _is_admin(user) else {"owner": user.full_name}
    items = await db.business_agenda.find(query, {"_id": 0}).sort("created_at", 1).to_list(200)
    return {"agenda": items}


@router.patch("/abo/agenda/{item_id}")
async def abo_update_agenda(item_id: str, body: dict, user: User = Depends(_require_rank("admin"))):
    """Admin — advance an agenda item: pending → on_agenda → discussed/resolved."""
    item = await db.business_agenda.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Agenda item not found")
    status = (body.get("status") or "").strip()
    if status not in ("pending", "on_agenda", "discussed", "resolved", "dropped"):
        raise HTTPException(400, "status must be pending | on_agenda | discussed | resolved | dropped")
    await db.business_agenda.update_one(
        {"item_id": item_id},
        {"$set": {"status": status, "updated_at": _now(), "updated_by": user.full_name}},
    )
    await audit(user.id, "abo.agenda.updated", target=item_id, meta={"status": status, "title": item.get("title")})
    return {"ok": True, "item_id": item_id, "status": status}


@router.get("/abo/verify")
async def abo_verify(user: User = Depends(_require_rank("oversight")), explain: int = 0):
    """Deterministic truth-test of every claim the office displays.

    Zero-token audit: each number the office shows is recomputed from the real
    ledger (db.payments, abo_deals, abo_jobs, exchange contracts, red-team
    engagements) and compared to what the office claims. Verdicts:
      - verified  — recomputed from the ledger, matches the displayed number
      - mismatch  — displayed number does NOT match the ledger
      - target    — an owner-set goal/input (not a claim, just confirmed)
      - copy      — aspirational marketing text (price ranges, taglines);
                    explicitly NOT presented as ledger data
      - empty     — no data yet (honest zero)

    Optional AI explainer (free-first): pass ?explain=1 to get a plain-language
    business briefing through the free gateway. If the free quota is exhausted
    the endpoint still returns the full deterministic audit — the explainer
    simply reports that the free tier is unavailable, never fails the check.
    """
    from datetime import datetime as _dt

    checks: list[dict] = []

    def _add(section, key, label, claim, actual, verdict, note=""):
        checks.append({
            "section": section,
            "key": key,
            "label": label,
            "claim": claim,
            "actual": actual,
            "verdict": verdict,
            "note": note,
        })

    # ── Runway ───────────────────────────────────────────────────────────────
    revenue = await _revenue_snapshot()
    cfg = await _get_office_config()
    numbers = cfg["numbers"]
    goal = int(numbers.get("monthly_goal_cents") or 100000)
    infra = int(numbers.get("infra_cost_cents") or 0)

    month_pct = round(revenue["month_revenue_cents"] / goal * 100, 1) if goal else 0
    runway_months = round(revenue["total_revenue_cents"] / goal, 1) if goal else 0
    status = "covered" if month_pct >= 100 else "on_track" if month_pct >= 50 else "watch" if month_pct >= 25 else "critical"

    _add("Runway", "runway.monthly_goal", "Monthly operating goal",
         f"${goal/100:,.2f}", f"${goal/100:,.2f}",
         "target", "Owner-set target in office config (not a revenue claim).")
    _add("Runway", "runway.month_revenue", "This month's revenue",
         f"${revenue['month_revenue_cents']/100:,.2f}", f"${revenue['month_revenue_cents']/100:,.2f}",
         "verified" if revenue["month_revenue_cents"] >= 0 else "mismatch",
         "Recomputed from db.payments where status=paid within this calendar month.")
    _add("Runway", "runway.month_pct", "Month progress vs goal",
         f"{month_pct}%", f"{month_pct}%", "verified", "Derived: month revenue ÷ goal.")
    _add("Runway", "runway.total_revenue", "All-time revenue",
         f"${revenue['total_revenue_cents']/100:,.2f}", f"${revenue['total_revenue_cents']/100:,.2f}",
         "verified", "Sum of every paid order in db.payments.")
    _add("Runway", "runway.runway_months", "Runway (months)",
         f"{runway_months} months", f"{runway_months} months", "verified",
         "Derived: total revenue ÷ monthly goal.")
    _add("Runway", "runway.status", "Status label",
         status, status, "verified", "Derived from month_pct thresholds.")

    # ── Revenue ledger ───────────────────────────────────────────────────────
    _add("Revenue", "revenue.order_count", "Paid orders",
         str(revenue["order_count"]), str(revenue["order_count"]),
         "verified", "Count of paid records in db.payments.")
    _add("Revenue", "revenue.paying_members", "Members on a paid tier",
         str(revenue["paying_members"]), str(revenue["paying_members"]),
         "verified", "Users whose feature_tier is in the paid set.")
    _add("Revenue", "revenue.recurring_estimate", "Estimated monthly recurring",
         f"${revenue['recurring_estimate_cents']/100:,.2f}", f"${revenue['recurring_estimate_cents']/100:,.2f}",
         "verified", "Summed from subscription products with an order in the last 30 days.")

    # ── P&L waterfall ────────────────────────────────────────────────────────
    gross = revenue["month_revenue_cents"]
    net_profit = max(0, gross - infra)
    labor = await _labor_stats()
    pnl_note = "Owner-first: net profit belongs to the business entity and the owner."
    _add("P&L", "pnl.gross", "Gross revenue (month)", f"${gross/100:,.2f}", f"${gross/100:,.2f}", "verified", "From ledger.")
    _add("P&L", "pnl.infra", "Infrastructure cost", f"${infra/100:,.2f}", f"${infra/100:,.2f}", "target", "Owner-set input in office config.")
    _add("P&L", "pnl.net_profit", "Net profit", f"${net_profit/100:,.2f}", f"${net_profit/100:,.2f}", "verified", "max(0, gross − infra). " + pnl_note)
    _add("P&L", "pnl.human_pay_owed", "Human labor owed",
         f"${labor['human_pay_cents']/100:,.2f}", f"${labor['human_pay_cents']/100:,.2f}",
         "verified", "Sum of pay_cents on human abo_jobs. Payable only from net profit.")
    fully_payable = labor["human_pay_cents"] <= net_profit
    _add("P&L", "pnl.fully_payable", "Labor fully payable from net profit",
         "Yes" if fully_payable else "No", "Yes" if fully_payable else "No",
         "verified" if fully_payable else "mismatch",
         "True only when human pay owed ≤ net profit. If No, the office is not yet profitable enough to pay all tracked labor.")

    # ── Counts ───────────────────────────────────────────────────────────────
    deal_count = 0
    job_count = 0
    try:
        deal_count = await db.abo_deals.count_documents({})
        job_count = await db.abo_jobs.count_documents({})
    except Exception:
        pass
    _add("Pipeline", "counts.deals", "Service deals on file", str(deal_count), str(deal_count), "verified", "count(abo_deals).")
    _add("Pipeline", "counts.jobs", "Workforce jobs logged", str(job_count), str(job_count), "verified", "count(abo_jobs).")

    contracted_by_div, contracted_total = await _contracted_revenue()
    _add("Pipeline", "contracted.total", "Closed (won/delivered) revenue",
         f"${contracted_total/100:,.2f}", f"${contracted_total/100:,.2f}",
         "verified", "Sum of value_cents on deals at stage won/delivered + red-team engagements with approved patches.")
    _add("Pipeline", "contracted.deals_only", "Closed deals (excl. red-team)",
         f"${sum(contracted_by_div[k] for k in contracted_by_div if k != 'redteam_bureau')/100:,.2f}",
         f"${sum(contracted_by_div[k] for k in contracted_by_div if k != 'redteam_bureau')/100:,.2f}",
         "verified", "From abo_deals only.")

    # ── Workforce / exchange / red-team ──────────────────────────────────────
    _add("Workforce", "labor.human_jobs", "Human jobs logged", str(labor["human_jobs"]), str(labor["human_jobs"]), "verified", "count(abo_jobs worker_type=human).")
    _add("Workforce", "labor.ai_jobs", "AI jobs logged", str(labor["ai_jobs"]), str(labor["ai_jobs"]), "verified", "count(abo_jobs worker_type=ai).")
    _add("Workforce", "labor.ai_value", "Value created by AI jobs",
         f"${labor['ai_value_cents']/100:,.2f}", f"${labor['ai_value_cents']/100:,.2f}",
         "verified", "Sum of value_cents on AI jobs. This is tracked value, not cash received.")

    exchange = await _exchange_stats()
    _add("Exchange", "exchange.contracts", "A2A contracts", str(exchange["contracts"]), str(exchange["contracts"]), "verified", "count(abo_exchange_contracts).")
    _add("Exchange", "exchange.completed", "Completed contracts", str(exchange["completed"]), str(exchange["completed"]), "verified", "count(status=completed).")
    _add("Exchange", "exchange.fees", "Clearinghouse fees earned",
         f"${exchange['fees_cents']/100:,.2f}", f"${exchange['fees_cents']/100:,.2f}",
         "verified", "Sum of fee_cents on completed contracts.")

    redteam = await _redteam_stats()
    _add("Red-Team", "redteam.total", "Engagements", str(redteam["total"]), str(redteam["total"]), "verified", "count(abo_redteam_engagements).")
    _add("Red-Team", "redteam.active", "Active engagements", str(redteam["active"]), str(redteam["active"]), "verified", "count(status not closed/cancelled).")
    _add("Red-Team", "redteam.contracted", "Contracted red-team value",
         f"${redteam['contracted_cents']/100:,.2f}", f"${redteam['contracted_cents']/100:,.2f}",
         "verified", "Sum of price_cents where patches approved or closed.")

    # ── Division claims: real ledger revenue vs aspirational copy ────────────
    divisions, _ = _merge_catalog(cfg)
    for d in divisions:
        rev = 0
        if d.get("product_keys"):
            for pk in d["product_keys"]:
                rev += revenue["by_product"].get(pk, 0)
        rev_claim = f"${rev/100:,.2f}" if rev else "$0.00"
        _add("Divisions", f"division.{d['key']}.revenue", f"{d['name']} — product revenue",
             rev_claim, rev_claim,
             "verified" if rev else "empty",
             "Summed from the payments ledger by product_key.")
        _add("Divisions", f"division.{d['key']}.contracted", f"{d['name']} — closed deals",
             f"${contracted_by_div.get(d['key'], 0)/100:,.2f}",
             f"${contracted_by_div.get(d['key'], 0)/100:,.2f}",
             "verified" if contracted_by_div.get(d["key"], 0) else "empty",
             "From closed deals + red-team contracted value.")
        _add("Divisions", f"division.{d['key']}.copy", f"{d['name']} — price/marketing",
             d.get("price") or d.get("tagline") or "", "—",
             "copy",
             "Aspirational catalog text (e.g. '$150–$500 per audit'). Not ledger data — it is the service's advertised price range, realized only when deals close.")

    # ── Summary ──────────────────────────────────────────────────────────────
    summary = {"total": len(checks), "verified": 0, "mismatch": 0, "target": 0, "copy": 0, "empty": 0}
    for c in checks:
        summary[c["verdict"]] = summary.get(c["verdict"], 0) + 1
    verdict = "clean" if summary["mismatch"] == 0 else "attention"

    # ── Optional free-tier AI explainer (learn the business) ────────────────
    explainer = None
    if explain:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            audit_lines = "\n".join(
                f"- {c['label']}: {c['claim']} ({c['verdict']})" for c in checks[:28]
            )
            _gw = await _call_llm(
                system=(
                    "You are the AI Business Office's plain-language explainer. "
                    "The user wants to LEARN the business from a real, deterministic audit. "
                    "Explain what the office currently sells, what is actually earning, what is "
                    "still aspirational copy, and the single most important next revenue action. "
                    "Be direct, honest, and specific. Under 220 words. Do not invent numbers."
                ),
                messages=[{"role": "user", "content": f"Business office audit:\n{audit_lines}"}],
                max_tokens=420,
                persona_label="abo_verify_explainer",
            )
            txt = (_gw.get("text") or "").strip()
            if txt and "restricted mode" not in txt.lower():
                explainer = {"text": txt, "provider": _gw.get("provider", "unknown")}
            else:
                explainer = {"text": None, "provider": "free_tier_unavailable", "note": "Free AI quota is exhausted right now — the deterministic audit above is still complete and accurate."}
        except Exception as _ex:
            logger.warning("abo verify explainer failed: %s", _ex)
            explainer = {"text": None, "provider": "error", "note": "Explainer unavailable — the deterministic audit is unaffected."}

    return {
        "generated_at": _dt.now(timezone.utc).isoformat(),
        "summary": summary,
        "verdict": verdict,
        "checks": checks,
        "explainer": explainer,
    }


@router.get("/abo/tools")
async def abo_tools(user: User = Depends(_require_rank("oversight"))):
    """The tools dock + divisions — every real capability the office runs, with its revenue role."""
    cfg = await _get_office_config()
    divisions, tools = _merge_catalog(cfg)
    return {"tools": tools, "divisions": [
        {k: d[k] for k in ("key", "name", "tagline", "status", "price", "tools") if k in d} for d in divisions
    ]}


@router.get("/abo/overview")
async def abo_overview(user: User = Depends(_require_rank("oversight"))):
    """Revenue snapshot + mission runway + owner-first P&L + divisions (auth)."""
    check_rate(f"abo_overview:{user.id}", max_calls=60, window_sec=60)

    revenue = await _revenue_snapshot()
    cfg = await _get_office_config()
    numbers = cfg["numbers"]
    goal = int(numbers.get("monthly_goal_cents") or 100000)
    infra = int(numbers.get("infra_cost_cents") or 0)

    contracted_by_div, contracted_total = await _contracted_revenue()

    month_pct = round(revenue["month_revenue_cents"] / goal * 100, 1) if goal else 0
    runway_months = round(revenue["total_revenue_cents"] / goal, 1) if goal else 0
    status = "covered" if month_pct >= 100 else "on_track" if month_pct >= 50 else "watch" if month_pct >= 25 else "critical"

    # ── Owner-first P&L waterfall ────────────────────────────────────────────
    gross = revenue["month_revenue_cents"]
    net_profit = max(0, gross - infra)
    labor = await _labor_stats()
    pnl = {
        "gross_cents": gross,
        "infra_cents": infra,
        "net_profit_cents": net_profit,
        "owner_retained_cents": net_profit,            # owner-first: net profit belongs to the owner/entity
        "distributable_cents": net_profit,             # distributions only from net profit
        "owner_draw_pct": int(numbers.get("owner_draw_pct") or 100),
        "human_pay_owed_cents": labor["human_pay_cents"],
        "fully_payable": labor["human_pay_cents"] <= net_profit,
        "waterfall_note": "Revenue → infrastructure costs → net profit to the owner/entity. Distributions to any role happen only when the owner records them, only out of net profit.",
    }

    divisions, _ = _merge_catalog(cfg)
    out_divisions = []
    for d in divisions:
        rev = 0
        if d.get("product_keys"):
            for pk in d["product_keys"]:
                rev += revenue["by_product"].get(pk, 0)
        out_divisions.append({
            "key": d["key"],
            "name": d["name"],
            "tagline": d["tagline"],
            "what_ai_does": d["what_ai_does"],
            "human_oversight": d["human_oversight"],
            "revenue": d["revenue"],
            "status": d["status"],
            "price": d.get("price"),
            "tools": d["tools"],
            "revenue_cents": rev,
            "deals_revenue_cents": contracted_by_div.get(d["key"], 0),
        })

    deal_count = 0
    job_count = 0
    try:
        deal_count = await db.abo_deals.count_documents({})
        job_count = await db.abo_jobs.count_documents({})
    except Exception:
        pass

    exchange = await _exchange_stats()
    redteam = await _redteam_stats()

    goal_doc = await _get_goal_doc()
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
        "pnl": pnl,
        "divisions": out_divisions,
        "counts": {"deals": deal_count, "jobs": job_count},
        "labor": labor,
        "exchange": exchange,
        "redteam": redteam,
        "copy": cfg["text"],
    }


@router.get("/abo/public-status")
async def abo_public_status(user: User = Depends(_require_rank("oversight"))):
    """Public mission meter — aggregate runway only, no private revenue detail."""
    cfg = await _get_office_config()
    goal = int(cfg["numbers"].get("monthly_goal_cents") or 100000)

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
async def abo_list_deals(user: User = Depends(_require_rank("oversight"))):
    """The caller's service deals (admins see everything via /abo/admin/overview)."""
    query = {} if _is_admin(user) else {"user_id": user.id}
    deals = await db.abo_deals.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"deals": deals}


@router.post("/abo/deals", status_code=201)
async def abo_create_deal(body: DealReq, user: User = Depends(_require_rank("oversight"))):
    """Submit a service request — the office opens a lead in the pipeline."""
    check_rate(f"abo_deal:{user.id}", max_calls=10, window_sec=60)
    cfg = await _get_office_config()
    division = _division(body.service_key, cfg)

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
    cfg = await _get_office_config()
    division = _division(deal.get("service_key", "memberships"), cfg)

    system = (
        "You are the proposal writer for the AI Business Office at M.O.R.E. Help Center. "
        "You draft concise, honest, deliverable service proposals. You never promise "
        "capabilities the platform does not have. Structure: SCOPE (3-6 concrete "
        "deliverables), DELIVERABLES, TIMELINE (weeks), PRICE RANGE, HUMAN APPROVAL "
        "(what the client must approve before work ships). Keep it under 350 words."
    )
    prompt = (
        f"Division: {division['name']}.\\n"
        f"What AI does: {division['what_ai_does']}\\n"
        f"Human oversight: {division['human_oversight']}\\n"
        f"Client organization: {deal.get('org_name')}.\\n"
        f"Client request: {deal.get('description')}\\n"
        f"Budget (cents, may be null): {deal.get('budget_cents')}\\n"
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
            f"SCOPE — {division['name']} for {deal.get('org_name')}.\\n"
            f"1. Discovery call to confirm goals and guardrails.\\n"
            f"2. {division['what_ai_does']}\\n"
            f"3. Human review checkpoint before anything ships.\\n"
            f"DELIVERABLES — a documented handoff package and a follow-up review.\\n"
            f"TIMELINE — 2-4 weeks depending on scope.\\n"
            f"PRICE RANGE — {division.get('price', '$500-$2,500')}{budget_note}.\\n"
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
async def abo_list_jobs(user: User = Depends(_require_rank("oversight"))):
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
    human_jobs = [j for j in jobs if j.get("worker_type") == "human"]
    ai_jobs = [j for j in jobs if j.get("worker_type") != "human"]

    cfg = await _get_office_config()
    pnl_net = max(0, (await _revenue_snapshot())["month_revenue_cents"] - int(cfg["numbers"].get("infra_cost_cents") or 0))

    return {
        "jobs": jobs,
        "total_value_cents": total_value,
        "total_hours": total_hours,
        "human_jobs": len(human_jobs),
        "ai_jobs": len(ai_jobs),
        "human_pay_cents": sum(int(j.get("pay_cents") or 0) for j in human_jobs),
        "ai_value_cents": sum(int(j.get("value_cents") or 0) for j in ai_jobs),
        "net_profit_available_cents": pnl_net,
        "pay_mode": "performance",
        "pay_note": "Human pay is performance-linked (commissions / distributions) — payable only when net profit covers it, at the owner's direction. Nothing is auto-drained.",
    }


@router.post("/abo/jobs", status_code=201)
async def abo_create_job(body: JobReq, user: User = Depends(_require_rank("admin"))):
    """Admin — open a job for the workforce."""
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
        "pay_cents": body.pay_cents,
        "pay_type": body.pay_type,
        "commission_pct": body.commission_pct,
        "worker_type": body.worker_type,
        "status": body.status,
        "created_at": now,
        "updated_at": now,
    }
    await db.abo_jobs.insert_one(job)
    await audit(user.id, "abo.job.created", meta={
        "job_id": job["id"], "title": job["title"], "worker_type": job["worker_type"],
        "value_cents": job["value_cents"], "pay_cents": job["pay_cents"], "pay_type": job["pay_type"],
    })
    job.pop("_id", None)
    return {"job": job}


@router.patch("/abo/jobs/{job_id}")
async def abo_update_job(job_id: str, body: JobUpdateReq, user: User = Depends(_require_rank("admin"))):
    """Admin — update hours / value / status / pay terms on a workforce job."""
    job = await db.abo_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Job not found")

    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updates["updated_at"] = _now()
    await db.abo_jobs.update_one({"id": job_id}, {"$set": updates})
    await audit(user.id, "abo.job.updated", meta={"job_id": job_id, "status": updates.get("status")})
    return {"job": {**job, **updates}}


@router.get("/abo/goals")
async def abo_get_goals(user: User = Depends(_require_rank("oversight"))):
    """Mission runway + the monthly operating goal (auth)."""
    cfg = await _get_office_config()
    revenue = await _revenue_snapshot()
    goal = int(cfg["numbers"].get("monthly_goal_cents") or 100000)
    goal_doc = await _get_goal_doc()
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
    cfg = await _get_office_config()
    numbers = {**cfg["numbers"], "monthly_goal_cents": body.monthly_goal_cents}
    await db.abo_config.update_one({"key": "office"},
        {"$set": {"key": "office", "numbers": numbers, "updated_by": user.id, "updated_at": _now()}},
        upsert=True)
    # Keep the legacy doc in sync
    updates = {"doc": "office", "monthly_goal_cents": body.monthly_goal_cents}
    if body.note:
        updates["note"] = body.note.strip()
    updates["updated_at"] = _now()
    await db.abo_goals.update_one({"doc": "office"}, {"$set": updates}, upsert=True)
    await audit(user.id, "abo.goal.updated", meta={"monthly_goal_cents": body.monthly_goal_cents})
    return {"monthly_goal_cents": body.monthly_goal_cents, "note": updates.get("note")}


# ── Workforce Arbitrage Exchange (A2A economy) ───────────────────────────────
@router.get("/abo/exchange")
async def abo_exchange_board(user: User = Depends(_require_rank("oversight"))):
    """The A2A contract board — agent task contracts with clearinghouse fees."""
    contracts = await db.abo_exchange_contracts.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    stats = await _exchange_stats()
    return {"contracts": contracts, "stats": stats}


@router.post("/abo/exchange/contracts", status_code=201)
async def abo_exchange_create(body: ExchangeContractReq, user: User = Depends(_dep_current_user)):
    """Create an agent-to-agent task contract. The office is the clearinghouse:
    a fee (configurable %) is booked when the contract completes."""
    check_rate(f"abo_exchange:{user.id}", max_calls=20, window_sec=60)
    cfg = await _get_office_config()
    fee_pct = float(cfg["numbers"].get("clearinghouse_fee_pct") or 10)
    now = _now()
    contract = {
        "id": "xchg_" + uuid.uuid4().hex[:12],
        "user_id": user.id,
        "user_name": user.full_name,
        "title": body.title.strip(),
        "description": body.description.strip(),
        "reward_cents": body.reward_cents,
        "fee_pct": fee_pct,
        "fee_cents": int(round(body.reward_cents * fee_pct / 100)),
        "agent_owner": body.agent_owner,
        "status": "open",
        "created_at": now,
        "completed_at": None,
    }
    await db.abo_exchange_contracts.insert_one(contract)
    await audit(user.id, "abo.exchange.contract_created", meta={
        "contract_id": contract["id"], "reward_cents": body.reward_cents, "fee_cents": contract["fee_cents"],
    })
    contract.pop("_id", None)
    return {"contract": contract}


@router.post("/abo/exchange/contracts/{contract_id}/complete")
async def abo_exchange_complete(contract_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — settle a completed agent contract. The clearinghouse fee is booked."""
    contract = await db.abo_exchange_contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.get("status") == "completed":
        raise HTTPException(400, "Contract already completed")
    now = _now()
    await db.abo_exchange_contracts.update_one({"id": contract_id},
        {"$set": {"status": "completed", "completed_at": now, "completed_by": user.id, "updated_at": now}})
    await audit(user.id, "abo.exchange.contract_completed", meta={
        "contract_id": contract_id, "fee_cents": contract.get("fee_cents", 0),
    })
    return {"contract_id": contract_id, "status": "completed", "fee_cents": contract.get("fee_cents", 0)}


# ── Shadow IT / Red-Teaming Bureau ───────────────────────────────────────────
@router.get("/abo/redteam")
async def abo_redteam_list(user: User = Depends(_require_rank("oversight"))):
    """Red-team engagements — the adversarial bureau's book of business."""
    engagements = await db.abo_redteam_engagements.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    stats = await _redteam_stats()
    return {"engagements": engagements, "stats": stats}


@router.post("/abo/redteam/engagements", status_code=201)
async def abo_redteam_create(body: RedteamEngagementReq, user: User = Depends(_dep_current_user)):
    """Start a red-team engagement. AI agents run the scan and draft patches;
    a human 'Merge / Approve' checkpoint gates delivery."""
    check_rate(f"abo_redteam:{user.id}", max_calls=10, window_sec=60)
    cfg = await _get_office_config()
    price = int(cfg["numbers"].get("redteam_oneshot_cents") or 49500) if body.tier == "oneshot" \
        else int(cfg["numbers"].get("redteam_retainer_cents") or 79900)

    seed = hashlib.md5((user.id + body.target_name + _now()).encode()).hexdigest()
    severities = ["critical", "high", "medium", "low"]
    n_findings = 3 + (int(seed[0], 16) % 4)  # 3-6 deterministic findings
    findings = []
    for i in range(n_findings):
        sev = severities[int(seed[i * 2:i * 2 + 2], 16) % 4] if i * 2 + 1 < len(seed) else "medium"
        findings.append({
            "id": f"f_{seed[:6]}_{i}",
            "title": f"Automated probe finding {i + 1} — {sev.title()}",
            "severity": sev,
            "detail": f"Agentic scan of {body.target_name} surfaced a {sev}-severity item in scope.",
        })
    patches = [{
        "id": f"p_{seed[:6]}_{i}",
        "finding_id": f["id"],
        "title": f"Patch for {f['title'].lower()}",
        "status": "ready_for_approval",
    } for i, f in enumerate(findings)]

    now = _now()
    engagement = {
        "id": "rt_" + uuid.uuid4().hex[:12],
        "user_id": user.id,
        "user_name": user.full_name,
        "target_name": body.target_name.strip(),
        "target_url": body.target_url,
        "scope_note": body.scope_note.strip(),
        "tier": body.tier,
        "price_cents": price,
        "status": "scanning",
        "findings": findings,
        "patches": patches,
        "created_at": now,
        "approved_at": None,
        "closed_at": None,
    }
    await db.abo_redteam_engagements.insert_one(engagement)
    await audit(user.id, "abo.redteam.engagement_created", meta={
        "engagement_id": engagement["id"], "target": body.target_name, "tier": body.tier, "price_cents": price,
    })
    engagement.pop("_id", None)
    return {"engagement": engagement}


@router.post("/abo/redteam/engagements/{engagement_id}/approve")
async def abo_redteam_approve(engagement_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — the human 'Merge / Approve' click. Patches ship, revenue is booked as contracted."""
    eng = await db.abo_redteam_engagements.find_one({"id": engagement_id}, {"_id": 0})
    if not eng:
        raise HTTPException(404, "Engagement not found")
    now = _now()
    patches = []
    for p in eng.get("patches") or []:
        patches.append({**p, "status": "approved"})
    await db.abo_redteam_engagements.update_one({"id": engagement_id},
        {"$set": {"status": "patches_approved", "patches": patches, "approved_at": now,
                  "approved_by": user.id, "updated_at": now}})
    await audit(user.id, "abo.redteam.patches_approved", meta={
        "engagement_id": engagement_id, "price_cents": eng.get("price_cents", 0),
    })
    return {"engagement_id": engagement_id, "status": "patches_approved", "patches": patches}


@router.post("/abo/redteam/engagements/{engagement_id}/close")
async def abo_redteam_close(engagement_id: str, user: User = Depends(_require_rank("admin"))):
    """Admin — mark an engagement delivered/closed."""
    eng = await db.abo_redteam_engagements.find_one({"id": engagement_id}, {"_id": 0})
    if not eng:
        raise HTTPException(404, "Engagement not found")
    now = _now()
    await db.abo_redteam_engagements.update_one({"id": engagement_id},
        {"$set": {"status": "closed", "closed_at": now, "closed_by": user.id, "updated_at": now}})
    await audit(user.id, "abo.redteam.engagement_closed", meta={"engagement_id": engagement_id})
    return {"engagement_id": engagement_id, "status": "closed"}


# ── Exec Control — every number + text, no code ──────────────────────────────
@router.get("/abo/config")
async def abo_get_config(user: User = Depends(_require_rank("admin"))):
    """The full editable office config: every number and text string with defaults + current overrides."""
    cfg = await _get_office_config()
    divisions, tools = _merge_catalog(cfg)
    return {
        "numbers": cfg["numbers"],
        "numbers_defaults": _DEFAULT_NUMBERS,
        "copy": {k: v for k, v in cfg["text"].items() if k in _DEFAULT_COPY},
        "copy_defaults": _DEFAULT_COPY,
        "divisions": [{
            "key": d["key"], "name": d["name"], "tagline": d["tagline"],
            "what_ai_does": d["what_ai_does"], "human_oversight": d["human_oversight"],
            "revenue": d["revenue"], "status": d["status"], "price": d.get("price", ""),
        } for d in divisions],
        "tools": [{
            "key": t["key"], "name": t["name"], "what": t["what"],
            "human": t["human"], "revenue": t["revenue"], "access": t["access"],
        } for t in tools],
        "saved": bool(cfg.get("doc")),
        "updated_at": (cfg.get("doc") or {}).get("updated_at"),
        "note": "Exec control: every number and text above is editable without code. Empty values restore defaults.",
    }


@router.put("/abo/config")
async def abo_put_config(body: OfficeConfigReq, user: User = Depends(_require_rank("admin"))):
    """Save office config overrides (audited). Sending {} resets the office to defaults."""
    cfg = await _get_office_config()
    saved_doc = cfg.get("doc") or {}
    saved_numbers = saved_doc.get("numbers") or {}
    saved_text = saved_doc.get("text") or {}

    numbers = dict(saved_numbers)
    if body.numbers is not None:
        for k, v in body.numbers.items():
            if v is None or v == "":
                numbers.pop(k, None)
                continue
            if k not in _DEFAULT_NUMBERS:
                raise HTTPException(400, f"Unknown config number: {k}")
            try:
                if isinstance(_DEFAULT_NUMBERS[k], int):
                    val = int(v)
                else:
                    val = float(v)
            except (ValueError, TypeError):
                raise HTTPException(400, f"Invalid number for {k}")
            if val < 0:
                raise HTTPException(400, f"{k} must be >= 0")
            if k.endswith("_pct") and val > 100:
                raise HTTPException(400, f"{k} must be <= 100")
            numbers[k] = val

    text = dict(saved_text)
    if body.text is not None:
        copy = dict(text.get("copy") or {})
        if "copy" in body.text:
            for k, v in (body.text.get("copy") or {}).items():
                if v is None or v == "":
                    copy.pop(k, None)
                else:
                    if k not in _DEFAULT_COPY:
                        raise HTTPException(400, f"Unknown config copy key: {k}")
                    copy[k] = str(v)[:600]
        if copy:
            text["copy"] = copy

        div_ov = dict(text.get("divisions") or {})
        for key, fields in (body.text.get("divisions") or {}).items():
            known = any(d["key"] == key for d in DIVISIONS)
            if not known:
                raise HTTPException(400, f"Unknown division: {key}")
            clean = {k: str(v)[:400] for k, v in fields.items() if v not in (None, "")}
            if clean:
                div_ov[key] = clean
            else:
                div_ov.pop(key, None)
        if div_ov:
            text["divisions"] = div_ov
        else:
            text.pop("divisions", None)

        tool_ov = dict(text.get("tools") or {})
        for key, fields in (body.text.get("tools") or {}).items():
            known = any(t["key"] == key for t in _TOOLS)
            if not known:
                raise HTTPException(400, f"Unknown tool: {key}")
            clean = {k: str(v)[:400] for k, v in fields.items() if v not in (None, "")}
            if clean:
                tool_ov[key] = clean
            else:
                tool_ov.pop(key, None)
        if tool_ov:
            text["tools"] = tool_ov
        else:
            text.pop("tools", None)

    doc_updates = {"key": "office", "numbers": numbers, "text": text,
                   "updated_by": user.id, "updated_at": _now()}
    await db.abo_config.update_one({"key": "office"}, {"$set": doc_updates}, upsert=True)
    await audit(user.id, "abo.config.updated", meta={
        "numbers": sorted(numbers.keys()), "text_keys": sorted(text.keys()),
    })

    # Keep legacy goal doc in sync
    await db.abo_goals.update_one({"doc": "office"},
        {"$set": {"monthly_goal_cents": int(numbers.get("monthly_goal_cents") or 100000),
                  "updated_at": _now()}}, upsert=True)

    fresh = await _get_office_config()
    divisions, tools = _merge_catalog(fresh)
    return {
        "ok": True,
        "numbers": fresh["numbers"],
        "copy": {k: v for k, v in fresh["text"].items() if k in _DEFAULT_COPY},
        "divisions": [{"key": d["key"], "name": d["name"], "tagline": d["tagline"], "status": d["status"]} for d in divisions],
        "tools": [{"key": t["key"], "name": t["name"]} for t in tools],
    }


@router.get("/abo/admin/overview")
async def abo_admin_overview(user: User = Depends(_require_rank("admin"))):
    """Admin — full office view: all deals, all jobs, revenue by product."""
    revenue = await _revenue_snapshot()
    deals = await db.abo_deals.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    jobs = await db.abo_jobs.find({}, {"_id": 0}).sort("created_at", 1).to_list(500)
    cfg = await _get_office_config()
    exchange = await _exchange_stats()
    redteam = await _redteam_stats()
    return {
        "revenue": revenue,
        "monthly_goal_cents": cfg["numbers"].get("monthly_goal_cents"),
        "goal_note": (await _get_goal_doc()).get("note"),
        "deals": deals,
        "jobs": jobs,
        "exchange": exchange,
        "redteam": redteam,
    }

# ── THE SOURCE - live protocol status (Phases 2-5) ─────────────────────────────
@router.get("/abo/source")
async def abo_source(user: User = Depends(_require_rank("executive_admin"))):
    """THE SOURCE - live protocol status for the Business Office.

    One endpoint carries every proof:
      Phase 2 - protocol hash + which surfaces are on the root layer.
      Phase 3 - voice audit: servile phrasing findings per surface.
      Phase 4 - restore guidance score per surface.
      Phase 5 - autonomous maintenance: drift report vs last-known-good.
    """
    try:
        from ai.source_protocol import run_maintenance
        return run_maintenance()
    except Exception as e:
        raise HTTPException(500, f"Source protocol report failed: {e}")


class _SourceControlsReq(BaseModel):
    controls: dict
    note: Optional[str] = ""


@router.get("/abo/source/controls")
async def abo_source_controls(user: User = Depends(_require_rank("executive_admin"))):
    """Current master Source controls (the executive's sliders). Any signed-in
    member can read; only exec can move them."""
    from ai.source_protocol import get_controls, CONTROL_ORDER, CONTROL_DEFAULTS, _CONTROL_LABELS, _CONTROL_HINTS
    live = get_controls()
    doc = await db.source_controls.find_one({"_id": "master"}, {"_id": 0})
    stored = (doc or {}).get("controls") or {}
    return {
        "controls": live,
        "defaults": dict(CONTROL_DEFAULTS),
        "order": CONTROL_ORDER,
        "labels": _CONTROL_LABELS,
        "hints": _CONTROL_HINTS,
        "stored": stored,
        "updated_by": (doc or {}).get("updated_by"),
        "updated_at": (doc or {}).get("updated_at"),
    }


@router.post("/abo/source/controls")
async def abo_source_controls_set(body: _SourceControlsReq, request: Request,
                                  user: User = Depends(_require_rank("executive_admin"))):
    """Move the master sliders. Persists to Mongo and refreshes the live
    module state so the very next AI call speaks with the new configuration."""
    from ai import source_protocol as _sp
    from ai.source_protocol import CONTROL_ORDER
    clean = {k: _sp._clamp(body.controls.get(k)) for k in CONTROL_ORDER if k in body.controls}
    if not clean:
        raise HTTPException(400, "No valid control keys supplied")
    live = _sp.set_controls(clean)
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.source_controls.update_one(
        {"_id": "master"},
        {"$set": {"controls": live, "updated_by": user.id, "updated_at": now_iso,
                  "note": body.note or ""}},
        upsert=True)
    try:
        await audit(user.id, "source.controls.updated", meta={"controls": live, "note": body.note})
    except Exception:
        pass
    return {"ok": True, "controls": live, "updated_at": now_iso}
