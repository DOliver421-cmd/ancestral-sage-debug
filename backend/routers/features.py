"""
Feature Control Center — canonical feature registry and admin API.

Every platform capability is defined once in FEATURE_REGISTRY.
The admin UI reads and writes feature configs from this single source.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/features", tags=["features"])

# ── Database binding (set by server.py) ──────────────────────────────────────
db = None
current_user = None

def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


# ── Canonical Feature Registry ───────────────────────────────────────────────
# One entry per platform capability. This is the SINGLE source of truth.
# Admin UI reads from here. Backend enforcement reads from here.
# Default access is FAIL-CLOSED: admin/exec only until explicitly opened.

FEATURE_REGISTRY = [
    # ── AI Ecosystem ─────────────────────────────────────────────────────
    {
        "feature_id": "nam.chat",
        "name": "AI Tutor",
        "description": "Chat with NAM AI assistant",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/ai",
        "api_endpoints": ["/api/ai/chat", "/api/nam"],  # /api/ai/tutor does not exist — real surface is /api/ai/chat
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "AI Tutor",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.helper",
        "name": "Personal Helper",
        "description": "Personal AI helper for daily tasks",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/helper",
        "api_endpoints": ["/api/ai/helper"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "Personal Helper",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.assistant",
        "name": "Admin Assistant",
        "description": "AI assistant for administrative tasks",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/assistant",
        "api_endpoints": ["/api/ai/assistant"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "Admin Assistant",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.orchestrator",
        "name": "Orchestrator",
        "description": "AI workflow orchestration across personas",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/orchestrator",
        "api_endpoints": ["/api/ai/orchestrator"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "Orchestrator",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.site_guide",
        "name": "Site Guide",
        "description": "AI guide for navigating the platform",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/site-guide",
        "api_endpoints": ["/api/site-guide"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": True,
        "byok_allowed": False,
        "navigation_group": "NAM",
        "navigation_label": "Site Guide",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.council",
        "name": "Council (Sage)",
        "description": "AI reflection and wisdom persona",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/council",
        "api_endpoints": ["/api/ai/sage", "/api/sovereign"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "Council (Sage)",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.jamil",
        "name": "Jamil — Director AI",
        "description": "AI Director persona with autonomy protocol",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/jamil",
        "api_endpoints": ["/api/jamil"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "Jamil — Director AI",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": True,
    },
    {
        "feature_id": "nam.byok",
        "name": "My AI Keys (BYOK)",
        "description": "Connect your own AI provider keys",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/byok",
        "api_endpoints": ["/api/byok"],
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": True,
        "navigation_group": "NAM",
        "navigation_label": "My AI Keys",
    },

    # ── Create Ecosystem ─────────────────────────────────────────────────
    {
        "feature_id": "create.studio",
        "name": "Creator Studio",
        "description": "Content creation and publishing tools",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/studio",
        "api_endpoints": ["/api/studio"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "Create",
        "navigation_label": "Creator Studio",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "create.courses",
        "name": "Course Manager",
        "description": "Create and manage courses",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/creator/courses",
        "api_endpoints": ["/api/lms/courses"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Create",
        "navigation_label": "Course Manager",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "create.ghost",
        "name": "Ghost Producer",
        "description": "AI-assisted content production",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/ghost-producer",
        "api_endpoints": ["/api/ai/chat"],  # no /api/studio/ghost route — the page (admin-gated) calls the general AI chat
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "Create",
        "navigation_label": "Ghost Producer",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "create.social",
        "name": "Social Blast",
        "description": "AI-powered social media publishing",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/social/publish",
        "api_endpoints": ["/api/ai/social-blast"],  # real Social Blast surface (routers/chat.py)
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": True,
        "navigation_group": "Create",
        "navigation_label": "Social Blast",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "create.lounge",
        "name": "Creator Lounge",
        "description": "Creator community and resources",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/creator-lounge",
        "api_endpoints": ["/api/creator-lounge"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Create",
        "navigation_label": "Creator Lounge",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "create.earnings",
        "name": "My Earnings",
        "description": "View creator earnings and analytics",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/creator/earnings",
        "api_endpoints": ["/api/billing/earnings"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Create",
        "navigation_label": "My Earnings",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "create.payouts",
        "name": "Payout Dashboard",
        "description": "Manage payout methods and history",
        "category": "creation",
        "ecosystem": "CREATE",
        "route": "/creator/payouts",
        "api_endpoints": ["/api/billing/payouts"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Create",
        "navigation_label": "Payout Dashboard",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Learn Ecosystem ──────────────────────────────────────────────────
    {
        "feature_id": "learn.modules",
        "name": "Modules",
        "description": "Browse and enroll in curriculum modules",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/modules",
        "public_access": True,  # /modules and /courses are public discovery pages
        "api_endpoints": ["/api/lms/modules"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Modules",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.adaptive",
        "name": "Learning Path",
        "description": "AI-personalized learning path",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/adaptive",
        "api_endpoints": ["/api/adaptive"],  # real surface: /api/adaptive/me (routers/admin.py)
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Learning Path",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "learn.competencies",
        "name": "Competencies",
        "description": "Track skills and competencies",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/competencies",
        "api_endpoints": ["/api/lms/competencies"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Competencies",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.labs",
        "name": "Workforce Labs",
        "description": "Hands-on practice labs",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/labs",
        "api_endpoints": ["/api/lms/labs"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Workforce Labs",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.simulations",
        "name": "Lab Simulations",
        "description": "Interactive lab simulations",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/lab-simulations",
        "api_endpoints": ["/api/lms/simulations"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Lab Simulations",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.compliance",
        "name": "Compliance",
        "description": "Compliance training and tracking",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/compliance",
        "api_endpoints": ["/api/lms/compliance"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Compliance",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.credentials",
        "name": "Credentials",
        "description": "View earned credentials",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/credentials",
        "api_endpoints": ["/api/lms/credentials"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Credentials",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.certificates",
        "name": "Certificates",
        "description": "View earned certificates",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/certificates",
        "api_endpoints": ["/api/lms/certificates"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Certificates",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "learn.portfolio",
        "name": "Portfolio",
        "description": "Showcase your work",
        "category": "learning",
        "ecosystem": "LEARN",
        "route": "/portfolio",
        "api_endpoints": ["/api/lms/portfolio"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Learn",
        "navigation_label": "Portfolio",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Community Ecosystem ──────────────────────────────────────────────
    {
        "feature_id": "community.palace",
        "name": "Members' Palace",
        "description": "Member community space",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/palace",
        "api_endpoints": ["/api/community/palace"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Members' Palace",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.leaderboard",
        "name": "XP Leaderboard",
        "description": "See who's earning the most experience",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/leaderboard",
        "public_access": True,  # /leaderboard is a public page
        "api_endpoints": ["/api/community/leaderboard"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "XP Leaderboard",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.chat",
        "name": "Community Chat",
        "description": "Real-time community messaging",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/more/chat",
        "api_endpoints": ["/api/chat"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Community Chat",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.legal",
        "name": "Legal Tools",
        "description": "Legal resources and self-help",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/more/litigation",
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Legal Tools",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.incidents",
        "name": "Report Incident",
        "description": "Report issues or concerns",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/incidents",
        "api_endpoints": ["/api/community/incidents"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Report Incident",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.saga",
        "name": "Vonns Saga",
        "description": "Interactive music story experience",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/vonns-saga",
        "public_access": True,  # /vonns-saga is a public page
        "api_endpoints": ["/api/saga"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Vonns Saga",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "community.ascension",
        "name": "Ascension Protocols",
        "description": "Personal growth learning path",
        "category": "community",
        "ecosystem": "COMMUNITY",
        "route": "/ascension-protocols",
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Community",
        "navigation_label": "Ascension Protocols",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Marketplace Ecosystem ────────────────────────────────────────────
    {
        "feature_id": "marketplace.store",
        "name": "Media Store",
        "description": "Browse and purchase digital content",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/store",
        "public_access": True,  # /store is publicly reachable (public MediaStore route)
        "api_endpoints": ["/api/commerce/store"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Media Store",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "marketplace.plans",
        "name": "Plans & Pricing",
        "description": "View membership plans",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/plans",
        "public_access": True,  # /plans is a public page
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Plans & Pricing",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "marketplace.subscribe",
        "name": "Membership",
        "description": "Subscribe to a membership plan",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/subscribe",
        "api_endpoints": ["/api/billing/subscribe"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Membership",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "marketplace.donate",
        "name": "Donate",
        "description": "Support the platform",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/donate",
        "api_endpoints": ["/api/billing/donate"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Donate",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "marketplace.payments",
        "name": "Payment History",
        "description": "View payment history",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/payment/history",
        "api_endpoints": ["/api/billing/history"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Payment History",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "marketplace.partnerships",
        "name": "Partnerships",
        "description": "Partnership opportunities",
        "category": "commerce",
        "ecosystem": "MARKETPLACE",
        "route": "/partnership",
        "api_endpoints": ["/api/billing/partnerships"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Marketplace",
        "navigation_label": "Partnerships",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Sanctuary Ecosystem ──────────────────────────────────────────────
    {
        "feature_id": "sanctuary.reflection",
        "name": "Sanctuary",
        "description": "Personal reflection and journaling",
        "category": "wellness",
        "ecosystem": "SANCTUARY",
        "route": "/sanctuary",
        "api_endpoints": [],  # /sanctuary route redirects to /helper — no dedicated backend surface
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": True,
        "byok_allowed": False,
        "navigation_group": "Sanctuary",
        "navigation_label": "Sanctuary",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": True,
    },
    {
        "feature_id": "sanctuary.knowledge",
        "name": "Knowledge Base",
        "description": "Platform documentation and help",
        "category": "wellness",
        "ecosystem": "SANCTUARY",
        "route": "/knowledge-base",
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Sanctuary",
        "navigation_label": "Knowledge Base",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Music Ecosystem ──────────────────────────────────────────────────
    {
        "feature_id": "music.band",
        "name": "Band on a Page",
        "description": "Create a music page for your band",
        "category": "creation",
        "ecosystem": "MUSIC",
        "route": "/band",
        "api_endpoints": ["/api/band"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["member", "plus", "pro", "patron"],  # legacy labels normalized
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Music",
        "navigation_label": "Band on a Page",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "music.playlist",
        "name": "Playlist Manager",
        "description": "Curate and manage playlists",
        "category": "creation",
        "ecosystem": "MUSIC",
        "route": "/playlist/dashboard",
        "api_endpoints": ["/api/playlist"],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Music",
        "navigation_label": "Playlist Manager",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },

    # ── Games Ecosystem ──────────────────────────────────────────────────
    {
        "feature_id": "games.arcade",
        "name": "Virtual Arcade",
        "description": "Play browser-based games",
        "category": "entertainment",
        "ecosystem": "GAMES",
        "route": "/arcade",
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Games",
        "navigation_label": "Virtual Arcade",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "games.pantheon",
        "name": "M.O.R.E. Pantheon",
        "description": "Community hall of achievements",
        "category": "entertainment",
        "ecosystem": "GAMES",
        "route": "/trash",
        "api_endpoints": [],
        "default_roles": ["student", "admin", "executive_admin"],
        "default_tiers": ["free", "member", "plus", "pro", "patron"],  # legacy labels normalized (creator→member, studio→plus, director→patron)
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Games",
        "navigation_label": "M.O.R.E. Pantheon",
        "internal_only": False,
        "customer_access_allowed": True,
        "cost_bearing": False,
    },
    {
        "feature_id": "games.arena",
        "name": "Arena",
        "description": "AI persona competition (executive only)",
        "category": "entertainment",
        "ecosystem": "GAMES",
        "route": "/arena",
        "api_endpoints": ["/api/competition"],
        "default_roles": ["executive_admin"],
        "default_tiers": [],
        "platform_ai": True,
        "byok_allowed": False,
        "navigation_group": "Director",
        "navigation_label": "The Arena",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": True,
    },

    # ── Admin Ecosystem ──────────────────────────────────────────────────
    {
        "feature_id": "admin.dashboard",
        "name": "Admin Dashboard",
        "description": "Platform administration overview",
        "category": "admin",
        "ecosystem": "ADMIN",
        "route": "/admin",
        "api_endpoints": ["/api/admin"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Director",
        "navigation_label": "Admin Overview",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": False,
    },
    {
        "feature_id": "admin.iam",
        "name": "IAM Console",
        "description": "Identity and access management",
        "category": "admin",
        "ecosystem": "ADMIN",
        "route": "/admin/iam",
        "api_endpoints": ["/api/admin/users"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Director",
        "navigation_label": "IAM Console",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": False,
    },
    {
        "feature_id": "admin.command",
        "name": "Command Center",
        "description": "Executive command center",
        "category": "admin",
        "ecosystem": "ADMIN",
        "route": "/admin/command",
        "api_endpoints": ["/api/exec-command"],
        "default_roles": ["executive_admin"],
        "default_tiers": [],
        "platform_ai": True,
        "byok_allowed": False,
        "navigation_group": "Director",
        "navigation_label": "Command Center",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": False,
    },
    {
        "feature_id": "admin.health",
        "name": "System Health",
        "description": "Monitor platform health",
        "category": "admin",
        "ecosystem": "ADMIN",
        "route": "/admin/health",
        "api_endpoints": ["/api/admin/health"],
        "default_roles": ["admin", "executive_admin"],
        "default_tiers": [],
        "platform_ai": False,
        "byok_allowed": False,
        "navigation_group": "Director",
        "navigation_label": "System Health",
        "internal_only": True,
        "customer_access_allowed": False,
        "cost_bearing": False,
    },
]


# ── Canonical tiers & roles ──────────────────────────────────────────────────
# Must mirror security/feature_control.py TIER_RANK, routers/exec_control.py
# _BUILTIN_TIERS, frontend/src/lib/tiers.js and frontend/src/lib/roles.js.
REAL_TIERS = ["free", "member", "plus", "pro", "patron", "executive"]
REAL_ROLES = [
    "student", "trial_pass", "instructor", "support_staff",
    "oversight", "admin", "executive_admin",
]

# Early Feature Control Center builds used invented tier labels
# (creator/studio/director).  Normalize them to the real product tiers so a
# stored config can never reference a tier that does not exist.
LEGACY_TIER_MAP = {"creator": "member", "studio": "plus", "director": "patron"}


def normalize_tiers(tiers) -> list:
    """Map legacy/invalid tier labels to the real product tiers (deduped)."""
    if not tiers:
        return []
    out = []
    for t in tiers:
        t = LEGACY_TIER_MAP.get(t, t)
        if t in REAL_TIERS and t not in out:
            out.append(t)
    return out


# ── Access check ─────────────────────────────────────────────────────────────

def get_feature_config(feature_id: str) -> Optional[dict]:
    """Registry default for *feature_id* — pure sync helper, no DB read.

    Endpoints use get_feature_config_async() so admin overrides from
    db.feature_configs are actually reflected; this form is kept for callers
    that only need the static default.
    """
    for reg in FEATURE_REGISTRY:
        if reg["feature_id"] == feature_id:
            break
    else:
        return None

    base = {
        "internal_only": reg.get("internal_only", False),
        "customer_access_allowed": reg.get("customer_access_allowed", True),
        "cost_bearing": reg.get("cost_bearing", False),
        "public_access": reg.get("public_access", False),
    }
    return {
        "feature_id": feature_id,
        "enabled": True,
        "allowed_roles": list(reg.get("default_roles", [])),
        "allowed_tiers": normalize_tiers(reg.get("default_tiers", [])),
        "platform_ai": reg.get("platform_ai", False),
        "byok_allowed": reg.get("byok_allowed", False),
        "navigation_visible": True,
        **base,
    }


async def get_feature_config_async(feature_id: str) -> Optional[dict]:
    """Effective config: Feature Control Center DB override > registry default."""
    base = get_feature_config(feature_id)
    if base is None:
        return None
    if db is None:
        return base
    try:
        override = await db.feature_configs.find_one(
            {"feature_id": feature_id}, {"_id": 0}
        )
    except Exception:
        return base
    if not override:
        return base
    return {
        **base,
        "enabled": override.get("enabled", base["enabled"]),
        "allowed_roles": override.get("allowed_roles", base["allowed_roles"]),
        "allowed_tiers": normalize_tiers(
            override.get("allowed_tiers", base["allowed_tiers"])
        ),
        "platform_ai": override.get("platform_ai", base["platform_ai"]),
        "byok_allowed": override.get("byok_allowed", base["byok_allowed"]),
        "navigation_visible": override.get(
            "navigation_visible", base["navigation_visible"]
        ),
        "internal_only": override.get("internal_only", base["internal_only"]),
        "customer_access_allowed": override.get(
            "customer_access_allowed", base["customer_access_allowed"]
        ),
        "cost_bearing": override.get("cost_bearing", base["cost_bearing"]),
        "public_access": override.get("public_access", base["public_access"]),
    }


# ── API Endpoints ────────────────────────────────────────────────────────────

@router.get("")
async def list_features(actor=Depends(current_user)):
    """List all features with current config (admin only)."""
    if not actor or actor.get("role") not in ("admin", "executive_admin"):
        raise HTTPException(403, "Admin access required")

    configs = []
    for reg in FEATURE_REGISTRY:
        config = await get_feature_config_async(reg["feature_id"])
        configs.append({**reg, **config})

    return {"features": configs, "total": len(configs)}


@router.get("/gate-map")
async def feature_gate_map():
    """Public gate map for frontend nav. No auth required."""
    gate_map = {}
    for reg in FEATURE_REGISTRY:
        config = await get_feature_config_async(reg["feature_id"])
        gate_map[reg["feature_id"]] = {
            "enabled": config["enabled"],
            "allowed_roles": config["allowed_roles"],
            "allowed_tiers": config["allowed_tiers"],
            "navigation_visible": config["navigation_visible"],
            "navigation_group": reg["navigation_group"],
            "navigation_label": reg["navigation_label"],
            "route": reg["route"],
            "internal_only": config["internal_only"],
            "customer_access_allowed": config["customer_access_allowed"],
            "cost_bearing": config["cost_bearing"],
            "public_access": config["public_access"],
        }
    return {"features": gate_map}


@router.get("/matrix/tier")
async def tier_matrix(actor=Depends(current_user)):
    """Tier access matrix — shows which tiers can access each feature."""
    if not actor or actor.get("role") not in ("admin", "executive_admin"):
        raise HTTPException(403, "Admin access required")

    all_tiers = list(REAL_TIERS)
    matrix = []
    for reg in FEATURE_REGISTRY:
        config = await get_feature_config_async(reg["feature_id"])
        row = {"feature_id": reg["feature_id"], "name": reg["name"]}
        for tier in all_tiers:
            row[tier] = tier in config["allowed_tiers"]
        matrix.append(row)
    return {"matrix": matrix, "tiers": all_tiers}


@router.get("/matrix/role")
async def role_matrix(actor=Depends(current_user)):
    """Role access matrix — shows which roles can access each feature."""
    if not actor or actor.get("role") not in ("admin", "executive_admin"):
        raise HTTPException(403, "Admin access required")

    all_roles = list(REAL_ROLES)
    matrix = []
    for reg in FEATURE_REGISTRY:
        config = await get_feature_config_async(reg["feature_id"])
        row = {"feature_id": reg["feature_id"], "name": reg["name"]}
        for role in all_roles:
            row[role] = role in config["allowed_roles"]
        matrix.append(row)
    return {"matrix": matrix, "roles": all_roles}


@router.put("/{feature_id}")
async def update_feature(feature_id: str, body: dict, request, actor=Depends(current_user)):
    """Update a feature's access config (admin only)."""
    if not actor or actor.get("role") not in ("admin", "executive_admin"):
        raise HTTPException(403, "Admin access required")

    # Verify feature exists in registry
    reg = next((r for r in FEATURE_REGISTRY if r["feature_id"] == feature_id), None)
    if not reg:
        raise HTTPException(404, f"Unknown feature: {feature_id}")

    # Build update
    update_fields = {}
    for key in ["enabled", "allowed_roles", "allowed_tiers", "platform_ai", "byok_allowed", "navigation_visible", "internal_only", "customer_access_allowed", "cost_bearing", "public_access"]:
        if key in body:
            update_fields[key] = body[key]

    # Store only canonical values: legacy tier labels are normalized to real
    # product tiers and unknown role names are dropped, so a stored config can
    # never reference a role/tier that does not exist in the platform.
    if "allowed_tiers" in update_fields:
        update_fields["allowed_tiers"] = normalize_tiers(update_fields["allowed_tiers"])
    if "allowed_roles" in update_fields:
        roles = update_fields["allowed_roles"]
        update_fields["allowed_roles"] = [r for r in roles if r in REAL_ROLES]

    if not update_fields:
        raise HTTPException(400, "No valid fields to update")

    update_fields["updated_by"] = actor.get("id", "unknown")
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    if db is not None:
        await db.feature_configs.update_one(
            {"feature_id": feature_id},
            {"$set": update_fields},
            upsert=True,
        )

    return {"ok": True, "feature_id": feature_id, "updated": list(update_fields.keys())}
