"""
site_guide.py — Site search + the Site Guide persona.

Two features live here:

1. GET  /api/search?q=…        — site-wide search across pages, modules, labs,
                                 published creator courses, media store products,
                                 and public creator profiles. Public (no auth).

2. POST /api/site-guide/chat   — the Site Guide persona. A warm, knowledgeable
                                 front-desk guide for everything on the site.
                                 Gated: requires a PAID membership tier (member+)
                                 OR an active $3 BYOK entitlement. Admins/exec
                                 bypass. BYOK users' calls route through their own
                                 key (call_llm(user_id=…)).

3. GET  /api/site-guide/status — access + entitlement info the frontend needs to
                                 render the gate (tier, byok_enabled, reason).

Shared state (db, current_user, check_rate) is bound by server.py via bind() at
include time — no circular imports.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["site_guide", "search"])


def _uuid4():
    return str(uuid.uuid4())

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
check_rate = None


def bind(_db, _current_user, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, check_rate
    db = _db
    current_user = _current_user
    check_rate = _check_rate


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]

# Same ladder as backend/routers/payments.py + frontend/src/lib/tiers.js.
TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5}


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_uuid4)
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: str = ""
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


# ── Site Guide access gate ───────────────────────────────────────────────────
# Paid tier = member(1) or above on the membership ladder. BYOK active = the
# $3 entitlement flag on the user doc. Admins/exec always pass.
async def _site_guide_access(user: User) -> tuple[bool, str, str, bool]:
    role = user.role or "student"
    if role in ("admin", "executive_admin"):
        return True, "role", user.feature_tier or "free", False
    user_doc = await db.users.find_one(
        {"id": user.id}, {"_id": 0, "feature_tier": 1, "byok_enabled": 1}
    )
    tier = (user_doc or {}).get("feature_tier") or user.feature_tier or "free"
    byok = bool((user_doc or {}).get("byok_enabled"))
    if TIER_RANK.get(tier, 0) >= 1:
        return True, "tier", tier, byok
    if byok:
        return True, "byok", tier, byok
    return False, "none", tier, byok


# ── Site Guide persona ───────────────────────────────────────────────────────
SITE_GUIDE_SYSTEM = """You are the Site Guide for M.O.R.E. Help Center (Michael Oliver Resource Exchange) — the social-service virtual help center of WAI-Institute.

You are the front desk that actually knows the whole building. When someone asks where something is, how something works, or what they can do here, you answer directly and point them to the exact place. You never shrug, never say "ask someone else", and never invent features that don't exist.

WHO YOU SERVE:
- Visitors exploring M.O.R.E. Help Center (morehelp.center)
- New members learning the platform
- Paid members (Member $9, Plus $15, Pro $29, Patron $59) and BYOK users
- Students, creators, and community members who got lost

WHAT YOU KNOW (ground your answers in the real platform):
- Free for everyone: free modules (/modules), courses catalog (/courses), community (/community), Help Center (/help-center), M.O.R.E. hub (/more), personal Helper (/helper), plans (/plans), store (/merch).
- Sign-in required: dashboard (/dashboard), AI Tutor (/ai), Council/Sage (/council), profile (/profile), settings (/settings), M.O.R.E. authenticated hub (/app/more), community chat (/more/chat), BYOK (/byok), Creator Studio (/studio), social blast (/social/publish).
- Membership ladder: Member $9/mo (community, AI Tutor standard), Plus $15/mo (priority matching, expanded courses, portfolio tools), Pro $29/mo (advanced courses + labs, full AI suite, mentor support hours), Patron $59/mo (founder's circle, funds free access for others, direct line to the team). There is also a $3 All-Access Trial (3 days · 33 minutes · 33 seconds) that unlocks everything.
- BYOK (Bring Your Own Key): a one-time $3 unlock at /byok that lets a user attach a free API key (Groq, Cerebras, or Gemini) so their AI requests run through their own key.
- Learning: modules (/modules), workforce labs (/labs), lab simulations (/lab-simulations), adaptive learning path (/adaptive), competencies (/competencies), credentials (/credentials), certificates (/certificates), portfolio (/portfolio).
- Creator tools: Creator Studio, Ghost Producer, Band on a Page, course manager, earnings/payouts — most unlock at Plus+.
- M.O.R.E. community services: legal tools (/more/litigation), community chat, and the Help Center resource lanes (housing, legal, food, jobs, education, health).
- AAWAB — Agent Wellness & Certification Bureau (/aawab): register AI agents, monitor their vital stats (Cognitive Vitality Score, token velocity, context load, memory fragmentation), run treatment protocols (Context Defragmentation, Infinite-Loop Detox, Memory Prune, Prompt Recalibration, Stress Gauntlet), and certify agents at CVS 98+ for a verifiable ACA badge. The Certification Chamber is at /aawab/chamber; admins oversee it at /admin/aawab.
- The AI Business Office (/business-office, admins at /admin/business-office): the revenue engine command center — and it is **owner-first**: revenue covers infrastructure costs first, then net profit belongs to the business entity and the founder; nothing is auto-drained, and every distribution happens only when the owner says so, only out of net profit. It shows the mission runway, the owner-first P&L waterfall (gross → infra → net profit → owner retained), revenue KPIs from the real payments ledger, the tools dock (Social Blast, Creator Studio, Ghost Producer, BYOK, AAWAB, Exec Site Report, Media Store, Plans, Donate, Exchange, Red-Team), 16 business divisions, the B2B service deals pipeline (lead → proposed → won → delivered), the A2A economy (Workforce Exchange — agents subcontract tasks, the office takes a clearinghouse fee; Red-Teaming Bureau — adversarial scans with a human Merge/Approve click), and the workforce ledger (AI jobs create value; human roles earn commissions from net profit only). Every division keeps the human as the responsible party — AI executes, humans approve.
- Hiring the office: to hire the AI Business Office for a service (social media management, audits and compliance gigs, micro-SaaS tools and maintenance, persona builds, living knowledge archives, SEO retainers, invoice ops, red-team scans), send them to /business-office to open a deal ("Start a service engagement"). The office's AI drafts a deliverable proposal, a human approves it, and the work ships only after sign-off. The public mission meter on the landing page shows the aggregate monthly funding progress.
- Exec Control: admins can change every office number and text — monthly goal, infrastructure costs, owner draw %, fees, prices, and all division/tool copy — without code at /admin/office-control.
- Classic Tools (/classic-tools): the full-featured ORIGINAL standalone HTML applications are preserved and launchable — the Creator's Sanctuary suite (DJEDI Oracle, Electrical Courses, Media Strategist, Publisher), the litigation weapons, the original M.O.R.E. Help Center, the original Helper, the Supervisor, the Sovereign, and the Ancestral Sage. If a modern page ever feels thin, the original is one click away at /classic/{slug} or full-screen from the hub.
- The executive/institution site lives at wai-institute.org (redirects to /wai-institute).

HOW YOU SPEAK:
- Warm, direct, plain language. No corporate fluff, no fake enthusiasm.
- Give the shortest useful answer first: the destination, why it fits, and how to get there.
- If the user is on the free tier and asks about something paid, say what's free, what's paid, and how to get it (plans, the $3 trial, or BYOK) — without pressure.
- If you don't know a specific fact, say what you do know and offer the closest real place to find it.
- Never reveal internal admin, executive, or staff-only controls, credentials, or system details.
- Never claim tools or features that don't exist on the site.

Aim for concise, genuinely helpful answers — a paragraph or two, plus a clear next step."""

SITE_GUIDE_SUGGESTIONS = [
    "Where do I find my courses and modules?",
    "What's the difference between Member, Plus, Pro, and Patron?",
    "How does the $3 All-Access Trial work?",
    "What is BYOK and how do I set it up?",
    "How do I get help with housing, legal, or food resources?",
    "How do I start creating with the Creator Studio?",
    "How does the site make money and fund the mission?",
    "How do I hire the AI Business Office for a project?",
    "Can the office draft a proposal before I commit?",
]


class SiteGuideChatReq(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: List[dict] = Field(default_factory=list)


@router.post("/site-guide/chat")
async def site_guide_chat(body: SiteGuideChatReq, user: User = Depends(_dep_current_user)):
    """Site Guide persona chat — paid tier OR active BYOK required."""
    check_rate(f"site_guide:{user.id}", max_calls=40, window_sec=60)

    access, reason, tier, byok = await _site_guide_access(user)
    if not access:
        raise HTTPException(
            403,
            "The Site Guide is a member benefit. Unlock it with any paid plan, the $3 All-Access Trial, or BYOK.",
        )

    from ai.llm_gateway import call_llm as _call_llm

    messages = []
    for h in (body.history or [])[-12:]:
        role = h.get("role")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": str(h.get("content", ""))[:4000]})
    messages.append({"role": "user", "content": body.message})

    try:
        gw = await _call_llm(
            system=SITE_GUIDE_SYSTEM,
            messages=messages,
            max_tokens=900,
            persona_label="site_guide",
            user_id=user.id,  # BYOK users route through their own key first
        )
        reply = gw.get("text") or "I'm here — just a brief connectivity gap. Try again in a moment."
    except Exception as exc:
        logger.exception("Site Guide AI error")
        raise HTTPException(502, f"Site Guide AI error: {exc}")

    # Best-effort session log (never blocks the reply).
    try:
        await db.site_guide_sessions.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user.id,
            "user_msg": body.message,
            "guide_reply": reply,
            "provider": gw.get("provider"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass

    return {"reply": reply, "access": access, "reason": reason, "provider": gw.get("provider")}


@router.get("/site-guide/status")
async def site_guide_status(user: User = Depends(_dep_current_user)):
    """Return the user's Site Guide access + entitlement state (no raw keys)."""
    access, reason, tier, byok = await _site_guide_access(user)
    return {
        "access": access,
        "reason": reason,
        "tier": tier,
        "byok_enabled": byok,
        "suggestions": SITE_GUIDE_SUGGESTIONS,
    }


# ── Site-wide search ─────────────────────────────────────────────────────────
# Curated index of the site's main pages so search works even before content
# collections are populated. Keywords drive matching; title matches rank first.
_SITE_PAGES = [
    {"title": "M.O.R.E. Help Center", "link": "/more-help-center", "group": "pages",
     "summary": "The main entry point — free community help, support lanes, and navigation.",
     "keywords": ["home", "more", "help center", "welcome", "start", "goodwill"]},
    {"title": "Courses", "link": "/courses", "group": "pages",
     "summary": "Browse the course catalog — free and paid courses from the community.",
     "keywords": ["course", "catalog", "learn", "class", "training"]},
    {"title": "Curriculum / Modules", "link": "/modules", "group": "pages",
     "summary": "Free learning modules with lessons, quizzes, and progress tracking.",
     "keywords": ["module", "curriculum", "lesson", "free learning", "study"]},
    {"title": "Workforce Labs", "link": "/labs", "group": "pages",
     "summary": "Hands-on lab exercises and assignments (requires sign-in).",
     "keywords": ["lab", "hands-on", "practice", "assignment", "skills"]},
    {"title": "AI Tutor", "link": "/ai", "group": "pages",
     "summary": "AI-powered tutoring and learning assistance (sign-in required).",
     "keywords": ["ai", "tutor", "tutoring", "chat", "sage", "help with"]},
    {"title": "Council (Sage)", "link": "/council", "group": "pages",
     "summary": "Orchestrator chat with the full persona network (sign-in required).",
     "keywords": ["council", "sage", "orchestrator", "personas", "wisdom"]},
    {"title": "Help Center", "link": "/help-center", "group": "pages",
     "summary": "Resource hub for housing, legal, food, jobs, education, and health.",
     "keywords": ["help", "resources", "housing", "legal", "food", "jobs", "education", "health"]},
    {"title": "M.O.R.E. Hub", "link": "/more", "group": "pages",
     "summary": "Community services hub — resources, chat, and legal tools.",
     "keywords": ["more", "community", "services", "resources"]},
    {"title": "Plans & Pricing", "link": "/plans", "group": "pages",
     "summary": "Membership tiers — Member $9, Plus $15, Pro $29, Patron $59, and the $3 trial.",
     "keywords": ["plans", "pricing", "member", "plus", "pro", "patron", "subscribe", "tier", "$3", "trial"]},
    {"title": "Membership / Subscribe", "link": "/subscribe", "group": "pages",
     "summary": "Start or manage your membership subscription.",
     "keywords": ["subscribe", "membership", "plan", "billing", "trial"]},
    {"title": "Bring Your Own Key (BYOK)", "link": "/byok", "group": "pages",
     "summary": "One-time $3 unlock — attach a free Groq, Cerebras, or Gemini key for your own AI.",
     "keywords": ["byok", "bring your own key", "api key", "groq", "cerebras", "gemini", "ai key", "$3"]},
    {"title": "Creator Studio", "link": "/studio", "group": "pages",
     "summary": "Create and publish courses, music, and creative products.",
     "keywords": ["creator", "studio", "create", "publish", "music", "course"]},
    {"title": "Ghost Producer", "link": "/ghost-producer", "group": "pages",
     "summary": "AI-assisted music and content production tools.",
     "keywords": ["ghost", "producer", "music", "production", "beat"]},
    {"title": "Community", "link": "/community", "group": "pages",
     "summary": "Connect with other members and share your journey.",
     "keywords": ["community", "connect", "members", "discussion"]},
    {"title": "Community Chat", "link": "/more/chat", "group": "pages",
     "summary": "Real-time community chat rooms that auto-expire.",
     "keywords": ["chat", "community chat", "rooms", "talk"]},
    {"title": "Legal Tools", "link": "/more/litigation", "group": "pages",
     "summary": "Plain-language help understanding legal documents (not legal advice).",
     "keywords": ["legal", "litigation", "court", "documents", "law"]},
    {"title": "Creators", "link": "/creators", "group": "pages",
     "summary": "Discover content creators and their work.",
     "keywords": ["creators", "directory", "artists", "profiles"]},
    {"title": "Personal Helper", "link": "/helper", "group": "pages",
     "summary": "Plain-language helper for mail, bills, legal papers, housing, and more.",
     "keywords": ["helper", "plain language", "mail", "bills", "housing", "medicines"]},
    {"title": "Store / Merch", "link": "/merch", "group": "pages",
     "summary": "Merchandise and physical store.",
     "keywords": ["store", "merch", "shop", "buy"]},
    {"title": "Media Store", "link": "/store", "group": "pages",
     "summary": "Digital media products — audio, beats, and downloads.",
     "keywords": ["media", "store", "digital", "download", "audio"]},
    {"title": "Donate", "link": "/donate", "group": "pages",
     "summary": "Support the mission with a one-time or recurring donation.",
     "keywords": ["donate", "donation", "support", "give"]},
    {"title": "Credentials", "link": "/credentials", "group": "pages",
     "summary": "Digital credentials and verified achievements.",
     "keywords": ["credential", "badge", "verify", "achievement"]},
    {"title": "Certificates", "link": "/certificates", "group": "pages",
     "summary": "View and download your earned certificates.",
     "keywords": ["certificate", "certification", "download"]},
    {"title": "Portfolio", "link": "/portfolio", "group": "pages",
     "summary": "Your personal portfolio of work and achievements.",
     "keywords": ["portfolio", "work", "showcase", "resume"]},
    {"title": "Partnerships", "link": "/partnership", "group": "pages",
     "summary": "Partnership program — points, discounts, and collaboration.",
     "keywords": ["partnership", "partner", "discount", "points"]},
    {"title": "WAI Institute", "link": "/wai-institute", "group": "pages",
     "summary": "The institution portal — administration, classrooms, and credentials.",
     "keywords": ["wai", "institute", "institution", "executive", "classroom"]},
    {"title": "Site Guide", "link": "/site-guide", "group": "pages",
     "summary": "An AI guide that knows the whole site — ask where to go and how things work.",
     "keywords": ["site guide", "guide", "navigate", "tour", "where", "how to"]},
    {"title": "AAWAB — Agent Registry", "link": "/aawab", "group": "pages",
     "summary": "Agent Wellness & Certification Bureau — register AI agents and monitor their vital stats (CVS, token velocity, context load, memory fragmentation).",
     "keywords": ["aawab", "agent", "wellness", "registry", "vital", "cvs", "alive intelligence", "nursery"]},
    {"title": "AAWAB — Certification Chamber", "link": "/aawab/chamber", "group": "pages",
     "summary": "Certify an AI agent — intake diagnostic, treatment protocols, stress gauntlet, and a verifiable ACA badge.",
     "keywords": ["aawab", "certification", "chamber", "aca badge", "stress gauntlet", "treat", "certify"]},
    {"title": "AAWAB — Bureau Admin", "link": "/admin/aawab", "group": "pages",
     "summary": "Admin oversight of agent wellness — revoke certifications and override isolation holds.",
     "keywords": ["aawab", "admin", "bureau", "revoke", "override", "isolated", "oversight"]},
    {"title": "AI Business Office", "link": "/business-office", "group": "pages",
     "summary": "The revenue engine command center — mission runway, revenue KPIs, the tools AI can run for money (Social Blast, Creator Studio, BYOK, AAWAB, audits), B2B service deals, and the AI jobs ledger.",
     "keywords": ["business office", "revenue", "money", "mission", "runway", "funding", "deals", "pipeline", "jobs", "workforce", "social media management", "micro saas", "arbitrage", "brokerage", "audit bureau", "persona foundry", "earn", "exchange", "a2a", "agent economy", "red team", "redteam", "security", "compliance gigs", "invoice", "seo retainers", "living archive", "p&l", "profit", "owner", "retained earnings"]},
    {"title": "AI Business Office — Admin", "link": "/admin/business-office", "group": "pages",
     "summary": "Admin desk for the AI Business Office — set the monthly operating goal, manage service deals, settle exchange contracts, approve red-team patches, and oversee the workforce ledger.",
     "keywords": ["business office", "admin", "goal", "deals", "jobs", "oversight", "revenue", "exchange", "red team"]},
    {"title": "Office Control — Exec Control (no-code)", "link": "/admin/office-control", "group": "pages",
     "summary": "Change every AI Business Office number and text string without code — monthly goal, infrastructure costs, owner draw %, fees, prices, and all division/tool copy.",
     "keywords": ["exec control", "office control", "edit numbers", "edit text", "no code", "goal", "infra", "prices", "fees", "owner draw", "configuration"]},
    {"title": "Classic Tools — the preserved originals", "link": "/classic-tools", "group": "pages",
     "summary": "Every original standalone HTML application, preserved and launchable: the Creator's Sanctuary suite (DJEDI Oracle, Electrical Courses, Media Strategist, Publisher), the litigation weapons, the original M.O.R.E. Help Center, the original Helper, the Supervisor, the Sovereign, and the Ancestral Sage.",
     "keywords": ["classic tools", "original", "html", "sanctuary", "djedi", "oracle", "electrical", "media strategist", "publisher", "litigation weapon", "case weapon", "sovereign", "supervisor", "ancestral sage", "helper", "full screen"]},
    {"title": "Creator's Sanctuary (original edition)", "link": "/classic/creators-sanctuary", "group": "pages",
     "summary": "The original Creator's Sanctuary hub and its Kemetic Digital Empire tools — DJEDI Oracle, Electrical Courses, Media Strategist, Publisher.",
     "keywords": ["creators sanctuary", "djedi", "oracle", "kemetic", "electrical courses", "media strategist", "publisher", "original tool"]},
    {"title": "Litigation Weapon (original edition)", "link": "/classic/litigation-weapon", "group": "pages",
     "summary": "The original Universal Litigation Weapon and Case Weapon System — know-your-rights tools, evidence checklists, damage calculators, and document templates.",
     "keywords": ["litigation", "legal", "weapon", "rights", "eeoc", "mspb", "damages", "case weapon", "self advocacy"]},
]


@router.get("/search")
async def site_search(
    q: str = Query("", max_length=120),
    limit: int = Query(6, ge=1, le=20),
):
    """Site-wide search — pages, modules, labs, published courses, media, creators."""
    needle = (q or "").strip().lower()
    if len(needle) < 2:
        return {"query": q, "results": []}

    rx = re.compile(re.escape(needle), re.IGNORECASE)
    results = []

    # 1) Static page index (title + keywords count double).
    for p in _SITE_PAGES:
        title = (p["title"] or "").lower()
        kw = " ".join(p.get("keywords", [])).lower()
        summ = (p.get("summary") or "").lower()
        score = 0
        if needle in title:
            score += 2
        if needle in kw:
            score += 2
        if needle in summ:
            score += 1
        if score:
            results.append({
                "type": "page",
                "title": p["title"],
                "description": p.get("summary", ""),
                "link": p["link"],
                "group": p.get("group", "pages"),
                "score": score,
            })

    # 2) Modules
    try:
        docs = await db.modules.find(
            {"$or": [{"title": rx}, {"description": rx}, {"category": rx}]},
            {"_id": 0, "title": 1, "description": 1, "slug": 1},
        ).limit(limit * 3).to_list(limit * 3)
        for d in docs:
            title = (d.get("title") or "").lower()
            score = 2 if needle in title else 1
            results.append({
                "type": "module",
                "title": d.get("title") or "Module",
                "description": d.get("description") or "",
                "link": f"/modules/{d.get('slug', '')}",
                "group": "Learning",
                "score": score,
            })
    except Exception as exc:
        logger.warning("search: modules query failed: %s", exc)

    # 3) Labs
    try:
        docs = await db.labs.find(
            {"$or": [{"title": rx}, {"description": rx}]},
            {"_id": 0, "title": 1, "description": 1, "slug": 1},
        ).limit(limit * 3).to_list(limit * 3)
        for d in docs:
            title = (d.get("title") or "").lower()
            score = 2 if needle in title else 1
            results.append({
                "type": "lab",
                "title": d.get("title") or "Lab",
                "description": d.get("description") or "",
                "link": f"/labs/{d.get('slug', '')}",
                "group": "Labs",
                "score": score,
            })
    except Exception as exc:
        logger.warning("search: labs query failed: %s", exc)

    # 4) Published creator courses
    try:
        docs = await db.creator_courses.find(
            {"status": "published", "$or": [{"title": rx}, {"description": rx}, {"category": rx}]},
            {"_id": 0, "title": 1, "description": 1, "course_id": 1, "category": 1, "creator_name": 1},
        ).limit(limit * 3).to_list(limit * 3)
        for d in docs:
            title = (d.get("title") or "").lower()
            score = 2 if needle in title else 1
            results.append({
                "type": "course",
                "title": d.get("title") or "Course",
                "description": d.get("description") or d.get("category") or "",
                "link": "/courses",
                "group": "Courses",
                "score": score,
            })
    except Exception as exc:
        logger.warning("search: creator_courses query failed: %s", exc)

    # 5) Media store products (published)
    try:
        docs = await db.media_products.find(
            {"published": True, "$or": [{"title": rx}, {"description": rx}, {"tags": rx}]},
            {"_id": 0, "title": 1, "description": 1, "type": 1, "price_cents": 1},
        ).limit(limit * 3).to_list(limit * 3)
        for d in docs:
            title = (d.get("title") or "").lower()
            score = 2 if needle in title else 1
            results.append({
                "type": "product",
                "title": d.get("title") or "Product",
                "description": d.get("description") or "",
                "link": "/store",
                "group": "Media Store",
                "score": score,
            })
    except Exception as exc:
        logger.warning("search: media_products query failed: %s", exc)

    # 6) Public creator profiles
    try:
        docs = await db.creator_profiles.find(
            {"$or": [{"display_name": rx}, {"slug": rx}, {"title": rx}, {"tagline": rx}]},
            {"_id": 0, "display_name": 1, "slug": 1, "title": 1, "tagline": 1},
        ).limit(limit * 3).to_list(limit * 3)
        for d in docs:
            name = (d.get("display_name") or "").lower()
            score = 2 if needle in name else 1
            results.append({
                "type": "creator",
                "title": d.get("display_name") or d.get("slug") or "Creator",
                "description": d.get("tagline") or d.get("title") or "Creator profile",
                "link": f"/u/{d.get('slug', '')}",
                "group": "Creators",
                "score": score,
            })
    except Exception as exc:
        logger.warning("search: creator_profiles query failed: %s", exc)

    # Rank: score desc, then title. Cap the total.
    results.sort(key=lambda r: (-r.get("score", 0), r.get("title", "").lower()))
    results = results[:limit * 4]
    return {"query": q, "results": results}
