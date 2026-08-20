"""tiers.py — Centralized access registry: canonical 7-role RBAC + compliance view.

AUTHORITATIVE RBAC: the platform's real 7-role hierarchy (single source of
truth lives in backend/roles.py — this module re-exports it):

    rank  role
    0     public           (unauthenticated baseline, not stored in DB)
    1     student
    2     trial_pass
    3     instructor
    4     support_staff
    5     oversight
    6     admin
    7     executive_admin

The four COMPLIANCE TIERS (Public / User / Auditor / Executive) are a derived
reporting view over that RBAC — they exist for executives and auditors, never
as a replacement for role-rank enforcement.  Every tier is bound to a real
minimum role, and the gateway always enforces real role ranks.

    tier       level  min_role      roles covered
    public     0      public        public
    user       1      student       student, trial_pass, instructor
    auditor    2      support_staff support_staff, oversight
    executive  3      admin         admin, executive_admin

CONTROL_REGISTRY declares the monitored site-control surface: each control
lists the routes the gateway intercepts, its compliance tier, and its exact
minimum RBAC role (min_role).  The gateway NEVER loosens an existing handler
guard — where a control's tier is looser than its handler's own check, the
handler still enforces the stricter rule.

This module is pure Python (no FastAPI dependency) so it can be unit-tested
in isolation and imported from the middleware, the dashboard and tests alike.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Dict, List, Optional, Tuple

from roles import ROLE_RANK, role_rank

# ── Canonical 7-role RBAC hierarchy (from backend/roles.py) ───────────────────
# Ordered weakest → strongest.  public (0) is the unauthenticated baseline and
# is not a stored user role.
ROLE_HIERARCHY: List[Tuple[str, int]] = [
    ("public", 0),
    ("student", 1),
    ("trial_pass", 2),
    ("instructor", 3),
    ("support_staff", 4),
    ("oversight", 5),
    ("admin", 6),
    ("executive_admin", 7),
]

# Stored (DB) roles only — the 7-role RBAC.
STORED_ROLES: List[str] = [r for r, _ in ROLE_HIERARCHY if r != "public"]


def rbac_hierarchy() -> List[dict]:
    """Plain-JSON-able snapshot of the canonical RBAC (for the executive UI)."""
    return [{"role": role, "rank": rank, "stored": role != "public"} for role, rank in ROLE_HIERARCHY]


# ── Compliance tier view over the RBAC ─────────────────────────────────────────
ACCESS_TIERS: Dict[str, dict] = {
    "public": {
        "level": 0,
        "label": "Public",
        "min_role": "public",
        "min_rank": ROLE_RANK["public"],
        "roles": ["public"],
        "description": "Unauthenticated visitors — marketing, pricing, public content.",
    },
    "user": {
        "level": 1,
        "label": "User",
        "min_role": "student",
        "min_rank": ROLE_RANK["student"],
        "roles": ["student", "trial_pass", "instructor"],
        "description": "Any authenticated account — standard learner/creator access.",
    },
    "auditor": {
        "level": 2,
        "label": "Auditor",
        "min_role": "support_staff",
        "min_rank": ROLE_RANK["support_staff"],
        "roles": ["support_staff", "oversight"],
        "description": "Read-only governance, audit ledger and oversight visibility.",
    },
    "executive": {
        "level": 3,
        "label": "Executive",
        "min_role": "admin",
        "min_rank": ROLE_RANK["admin"],
        "roles": ["admin", "executive_admin"],
        "description": "Site-control authority — CRUD, user management, control panels.",
    },
}

TIER_BY_LEVEL: Dict[int, dict] = {t["level"]: t for t in ACCESS_TIERS.values()}
TIER_ORDER: List[str] = ["public", "user", "auditor", "executive"]


def tier_key_for_role(role: str) -> str:
    """Return the compliance tier key for a real RBAC role string.

    Empty or "public" roles map to the Public tier (rank 0 — the
    unauthenticated baseline).  Any other unknown string falls through to
    roles.role_rank(), whose least-privilege fallback is 'student' (User tier).
    """
    role = (role or "").strip()
    if not role or role == "public":
        return "public"
    rank = role_rank(role)
    for key in reversed(TIER_ORDER):
        if rank >= ACCESS_TIERS[key]["min_rank"]:
            return key
    return "public"


def tier_level_for_role(role: str) -> int:
    """Return the numeric compliance tier level (0-3) for a role string."""
    return ACCESS_TIERS[tier_key_for_role(role)]["level"]


# ── Monitored control surface ─────────────────────────────────────────────────
# route patterns:
#   * "..."            → exact path match
#   * ".../"           → prefix match at a path-segment boundary (covers sub-routes)
#   * "...*"           → glob prefix match (fnmatch semantics)
#   * (methods, pat)   → only enforce for the given HTTP methods
# `exclude` lists exact paths that must NEVER be gated by this control (they are
# user-facing or public even though they share the control's prefix).
CONTROL_REGISTRY: Dict[str, dict] = {
    # ── User & Role Administration ──────────────────────────────────────────
    "admin_user_management": {
        "label": "User Management (CRUD)",
        "category": "User & Role Administration",
        "source": "routers/users.py, routers/auth.py",
        "description": "Create, read, update, delete, ban, re-role and reset platform users.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/admin/users", "/api/admin/users/", "/api/admin/associate"],
    },
    "admin_dashboard_moderation": {
        "label": "Admin Dashboard & Course Moderation",
        "category": "User & Role Administration",
        "source": "routers/admin.py",
        "description": "Admin stats, recent activity, cohorts and course moderation.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": [
            "/api/admin/stats", "/api/admin/recent-activity", "/api/admin/cohorts",
            "/api/admin/courses", "/api/admin/courses/",
        ],
    },

    # ── Site Control ────────────────────────────────────────────────────────
    "site_control_panel": {
        "label": "Site Control Panel (live metrics)",
        "category": "Site Control",
        "source": "routers/exec_control.py",
        "description": "Real-time site dashboard: users, revenue, payments, subscriptions, creators.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/control-panel*"],
    },
    "exec_control_layer": {
        "label": "Exec Control Layer",
        "category": "Site Control",
        "source": "routers/exec_control.py",
        "description": "Roles, tiers, feature flags, prices, budgets, provider ranking, IP whitelist, MFA, failover, break-glass.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/exec/control/"],
        "exclude": ["/api/exec/control/access/public"],
    },
    "emergency_breaker_panel": {
        "label": "Emergency Breaker Panel & Gateway",
        "category": "Site Control",
        "source": "server.py / emergency_panel.py",
        "description": "Breaker toggles, gateway failover (primary/backup/emergency) and panel health.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/exec/panel", "/api/exec/panel/", "/api/exec/failover"],
    },
    "gateway_key_management": {
        "label": "Gateway API Key Management",
        "category": "Site Control",
        "source": "server.py",
        "description": "Push, revoke and toggle live LLM provider keys without redeploy.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/gateway/keys", "/api/admin/gateway/keys/"],
    },
    "exec_command_center": {
        "label": "Exec Command Center",
        "category": "Site Control",
        "source": "routers/exec_command.py",
        "description": "System overview and operational manuals for the executive seat.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/exec/system", "/api/exec/manuals"],
    },
    "admin_broadcast": {
        "label": "Admin Broadcast",
        "category": "Site Control",
        "source": "routers/ops.py",
        "description": "Send platform-wide broadcast notifications to users.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/admin/broadcast"],
    },
    "admin_insights_export": {
        "label": "Admin Insights & Audit Export",
        "category": "Site Control",
        "source": "routers/misc.py",
        "description": "AI cost overview and audit-log export.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/admin/ai-costs", "/api/admin/audit/export"],
    },

    # ── Finance & Commerce ──────────────────────────────────────────────────
    "commerce_tools_instructor": {
        "label": "Commerce Tools (instructor checkout)",
        "category": "Finance & Commerce",
        "source": "routers/commerce.py",
        "description": "Instructor-facing sites/inventory/checkout tooling (handler enforces instructor+).",
        "required_tier": "user",
        "min_role": "instructor",
        "routes": [
            ("GET", "/api/admin/sites"), ("GET", "/api/admin/inventory"),
            ("POST", "/api/admin/checkout"),
        ],
    },
    "commerce_admin": {
        "label": "Commerce Administration",
        "category": "Finance & Commerce",
        "source": "routers/commerce.py",
        "description": "Site/inventory writes, checkout returns, checks, payments and discounts.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": [
            ("POST", "/api/admin/sites"), ("POST", "/api/admin/inventory"),
            "/api/admin/checkout/", "/api/admin/checkouts",
            "/api/admin/run-checks", "/api/admin/payments",
            "/api/admin/discounts", "/api/admin/discounts/",
        ],
    },
    "commerce_governance_audit": {
        "label": "Commerce Governance Audit",
        "category": "Finance & Commerce",
        "source": "routers/commerce.py",
        "description": "Read audit trail of commerce/governance actions (support_staff+).",
        "required_tier": "auditor",
        "min_role": "support_staff",
        "routes": [("GET", "/api/admin/audit")],
    },
    "platform_feature_flags": {
        "label": "Platform Feature Flags",
        "category": "Finance & Commerce",
        "source": "routers/commerce.py",
        "description": "Read and toggle platform-level feature flags.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/platform/"],
    },
    "creator_payout_processing": {
        "label": "Creator Payout Processing",
        "category": "Finance & Commerce",
        "source": "routers/creator.py",
        "description": "Process monthly creator payouts (marks pending earnings paid).",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/creator-payouts/"],
    },
    "platform_pricing_admin": {
        "label": "Platform Pricing Administration",
        "category": "Finance & Commerce",
        "source": "routers/auditor.py",
        "description": "Read/write platform price keys and values (public /prices/public stays open).",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/admin/prices", "/api/admin/prices/"],
    },
    "revenue_executive": {
        "label": "Revenue Executive Overview",
        "category": "Finance & Commerce",
        "source": "routers/revenue_exec.py",
        "description": "Executive revenue overview across products and streams.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/revenue/exec-overview"],
    },
    "billing_admin": {
        "label": "Billing Administration",
        "category": "Finance & Commerce",
        "source": "routers/billing.py",
        "description": "Credit grants, refunds and sage-session billing resolution.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": [
            "/api/billing/credits/grant", "/api/billing/refunds/",
            "/api/billing/sage-sessions", "/api/billing/sage-sessions/",
        ],
    },
    "provider_management": {
        "label": "Provider Management",
        "category": "Finance & Commerce",
        "source": "routers/billing.py",
        "description": "LLM provider configuration, keys and usage logs.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/providers", "/api/providers/"],
    },
    "team_operations": {
        "label": "Team Operations",
        "category": "Finance & Commerce",
        "source": "routers/billing.py",
        "description": "Team action history and monitor status.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/team/"],
    },

    # ── Governance & Audit ──────────────────────────────────────────────────
    "auditor_ledger": {
        "label": "Auditor Ledger & Reports",
        "category": "Governance & Audit",
        "source": "routers/auditor.py",
        "description": "Read-only delivery ledger, reports, debt and risk tracking (handler enforces admin+).",
        "required_tier": "auditor",
        "min_role": "admin",
        "routes": ["/api/auditor/"],
    },
    "sentinel_governance": {
        "label": "Sentinel (Governance Monitor)",
        "category": "Governance & Audit",
        "source": "routers/sentinel.py",
        "description": "Protocols, research notes, AI briefs, drift checks and action reversals.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/sentinel/"],
    },
    "supervisor_control": {
        "label": "Supervisor Control Panel",
        "category": "Governance & Audit",
        "source": "routers/supervisor.py",
        "description": "Escalations, greeter config, content approval, backup gateway and continuity checks.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/supervisor/"],
    },
    "bridge_governance": {
        "label": "Cross-Domain AI Bridge",
        "category": "Governance & Audit",
        "source": "routers/bridge.py",
        "description": "Team bridge configuration, personas, dispatch and logs.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/bridge/"],
    },
    "program_analytics_admin": {
        "label": "Program Analytics (admin)",
        "category": "Governance & Audit",
        "source": "routers/ops.py",
        "description": "Program-wide analytics reporting.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/analytics/program"],
    },
    "incident_resolution": {
        "label": "Incident Resolution",
        "category": "Governance & Audit",
        "source": "routers/ops.py",
        "description": "Resolve reported incidents (user reporting endpoints stay open).",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": [("POST", "/api/incidents/*/resolve")],
    },

    # ── AI & Pipeline Operations ────────────────────────────────────────────
    "exec_pipeline": {
        "label": "Exec Pipeline (LLM intent routing)",
        "category": "AI & Pipeline Operations",
        "source": "server.py",
        "description": "Route social media posts through the intent pipeline (single + batch).",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/exec/pipeline/"],
    },
    "exec_operations": {
        "label": "Exec Operations",
        "category": "AI & Pipeline Operations",
        "source": "routers/exec.py",
        "description": "Scout, merch, personas, products, staff meetings, site report and analytics.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": [
            "/api/exec/scout*", "/api/exec/audio", "/api/exec/merch*",
            "/api/exec/analytics", "/api/exec/personas", "/api/exec/personas/",
            "/api/exec/dashboard", "/api/exec/products", "/api/exec/products/",
            "/api/exec/staff-meetings", "/api/exec/staff-meeting",
            "/api/exec/site-report", "/api/exec/checkout/conversion",
        ],
    },
    "ai_spend_budget": {
        "label": "AI Spend Budget",
        "category": "AI & Pipeline Operations",
        "source": "routers/exec_control.py",
        "description": "Set and enforce AI cost spend budgets.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/ai-spend-budget"],
    },
    "sage_cap_administration": {
        "label": "Sage Safety Cap Administration",
        "category": "AI & Pipeline Operations",
        "source": "routers/ai.py",
        "description": "Read/set global and per-user Sage safety caps, audit and metrics.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/admin/sage/"],
    },
    "ai_provider_test": {
        "label": "AI Provider Live Test",
        "category": "AI & Pipeline Operations",
        "source": "routers/revenue_exec.py",
        "description": "Live ping of every LLM provider to diagnose failures.",
        "required_tier": "executive",
        "min_role": "admin",
        "routes": ["/api/ai/provider-test"],
    },

    # ── Unified Access Control (this module) ────────────────────────────────
    "executive_access_control": {
        "label": "Executive Access Control Dashboard",
        "category": "Unified Access Control",
        "source": "security/access_control/dashboard.py",
        "description": "The master executive interface for the monitored control surface.",
        "required_tier": "executive",
        "min_role": "executive_admin",
        "routes": ["/api/exec/access-control", "/api/exec/access-control/"],
    },
}


def _pattern_matches(pattern: str, path: str) -> bool:
    """Match a registered route pattern against a request path."""
    if "*" in pattern:
        return fnmatchcase(path, pattern)
    if pattern.endswith("/"):
        return path == pattern or path.startswith(pattern)
    return path == pattern


# ── Matching index ────────────────────────────────────────────────────────────
# Every request passes through the gateway's find_control(), so the lookup must
# be near-zero cost.  All control patterns live under /api/<segment>/..., so we
# index by the second path segment: only the handful of patterns in that group
# are ever scanned (a dict get + 1-3 pattern checks instead of ~80 pattern
# comparisons per request).
_CONTROL_INDEX: Dict[str, list] = {}
for _key, _spec in CONTROL_REGISTRY.items():
    for _entry in _spec.get("routes", []):
        _methods, _pattern = _entry if isinstance(_entry, tuple) else (None, _entry)
        _parts = _pattern.split("/")
        _seg = _parts[2] if len(_parts) > 2 else ""
        _CONTROL_INDEX.setdefault(_seg, []).append((_key, _spec, _methods, _pattern))


def find_control(path: str, method: str = "GET") -> Optional[dict]:
    """Return the first control spec whose route patterns match *path*.

    Indexed by the second path segment so the common case (an unregistered
    path such as /api/health) costs a single dict lookup.

    Public/user-facing paths that happen to share a control's prefix (e.g.
    /api/exec/control/access/public, /api/prices/public, /api/exec/audio/{id})
    are NOT matched — either they are excluded explicitly or they simply do
    not match any registered pattern (exact-match semantics).
    """
    method = (method or "GET").upper()
    parts = path.split("/")
    seg = parts[2] if len(parts) > 2 else ""
    for key, spec, methods, pattern in _CONTROL_INDEX.get(seg, ()):
        if path in (spec.get("exclude") or []):
            continue
        if methods is not None and method not in methods:
            continue
        if _pattern_matches(pattern, path):
            return {**spec, "key": key}
    return None


def registry_snapshot() -> List[dict]:
    """Return a plain-JSON-able snapshot of the control registry (for the dashboard)."""
    out = []
    for key, spec in CONTROL_REGISTRY.items():
        tier = ACCESS_TIERS[spec["required_tier"]]
        out.append({
            "key": key,
            "label": spec["label"],
            "category": spec["category"],
            "source": spec["source"],
            "description": spec.get("description", ""),
            "routes": [r if isinstance(r, str) else f"{'|'.join(r[0])} {r[1]}" for r in spec["routes"]],
            "required_tier": spec["required_tier"],
            "required_tier_label": tier["label"],
            "required_tier_level": tier["level"],
            "min_role": spec.get("min_role"),
        })
    return out
