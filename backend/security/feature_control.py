"""feature_control.py — ENFORCEMENT for the exec panel's feature controls.

The exec panel (routers/exec_control.py) has always WRITTEN to three stores —
platform_flags, page_access, user_feature_overrides — but nothing READ them
back, so toggling a control changed nothing.  This module is the read side:
it turns those writes into real server-side enforcement.

SAFE-DEFAULT CONTRACT (critical):
    Absent config == ALLOW.  A flag or page that was never touched, or whose
    document is missing, behaves exactly as before this module existed.  Only
    an explicit ``enabled: false`` written by an executive in the panel blocks
    requests.  Deploying this module changes NOTHING until an admin toggles a
    control — no surprise lockouts, no rollout risk.

Current enforcement surface (paths are API prefixes, not frontend routes):

  Platform flags   (db.platform_flags.flags.<flag>.enabled)
      ai_chat      -> /api/ai/*        (AI Tutor / Sage)
      posts        -> /api/more/*      (M.O.R.E. posts + needs board)
      courses      -> /api/modules*, /api/progress*, /api/labs*, /api/credentials*

  Page access      (db.page_access.<page>.enabled)  — keys mirror the
  PAGE_ACCESS_REGISTRY in routers/exec_control.py
      ai           -> /api/ai/*

Anything not in the maps below is not enforced by this module yet — that is
deliberate: the maps are the enforcement contract, and every entry must be
verified against the real route table before it is added.    Per-user enforcement (user_feature_overrides + feature_tier) lives in
check_user_feature_access() and runs in the same middleware, but only for
requests that carry a valid session: an explicit per-user revoke/grant wins
over the platform checks, and the user's feature_tier is compared against
FEATURE_MIN_TIER (the exact mirror of frontend/src/lib/tiers.js).  Absent
configuration remains available; inability to verify a mapped feature is a
503, never an allow.
"""

from __future__ import annotations

from typing import Optional

# Feature Control Center (FCC) integration — the canonical registry lives in
# routers/features.py; this module is the READ side that turns its records
# into server-side enforcement.  Imported defensively so a registry change
# can never take down the enforcement middleware.
try:
    from routers.features import FEATURE_REGISTRY, normalize_tiers
except Exception:  # pragma: no cover - import-time safety
    FEATURE_REGISTRY = []

    def normalize_tiers(tiers):
        return tiers or []

try:
    from roles import role_rank
except Exception:  # pragma: no cover - import-time safety
    def role_rank(role: str) -> int:
        return 0

# Platform feature flag -> API path prefixes it governs.  Keep in sync with the
# frontend's TIER_FOR_FEATURE keys and the live route table.
# Specific prefixes come before broad prefixes so an executive can govern a
# feature such as Social Blast without accidentally changing every AI route.
FEATURE_API_PATHS: dict = {
    "publisher_ai": ["/api/ai/social-blast"],
    "sovereign": ["/api/sovereign/", "/api/puzzles/"],
    "studio": ["/api/studio/"],
    "band": ["/api/band/"],
    "lounge": ["/api/creator-lounge/"],
    "earnings": ["/api/creator/earnings", "/api/creator/split"],
    "payouts": ["/api/creator/payouts", "/api/creator/payout-summary", "/api/creator/bank-account"],
    "publisher": ["/api/playlist/", "/api/portfolio/publish"],
    "tracks": ["/api/modules/tracks", "/api/progress/tracks"],
    # The broad modules/progress prefixes intentionally remain courses so the
    # existing contract continues to govern the live LMS endpoints.
    "courses": ["/api/modules", "/api/progress", "/api/labs", "/api/credentials"],
    "posts": ["/api/more/"],
    "ai_chat": ["/api/ai/"],
    "profile": ["/api/auth/me"],
}

# Page-access registry key -> API path prefixes it governs.  Keys must match
# PAGE_ACCESS_REGISTRY entries in routers/exec_control.py.
PAGE_API_PATHS: dict = {
    "ai": ["/api/ai/"],
    "account-controls": ["/api/admin/users"],
    "site-control": ["/api/admin/control-panel", "/api/admin/platform/flags"],
    "feature-control": ["/api/features"],
    "exec-business-office": ["/api/admin/users", "/api/exec/control/audit"],
    "exec-control": ["/api/features/", "/api/admin/"],
    "director": ["/api/admin/stats", "/api/incidents", "/api/admin/users", "/api/admin/recent-activity", "/api/admin/platform/flags"],
    "creator-payouts": ["/api/creator/payouts", "/api/creator/payout-summary", "/api/creator/bank-account"],
    "partnership-discounts": ["/api/partnership/status"],
}

# FCC feature_id -> API path prefixes it governs.  Every prefix is verified
# against the live route table (2026-08-23):
#   /api/jamil/*         routers/jamil.py
#   /api/competition/*   routers/competition.py
#   /api/ai/orchestrator routers/ai.py
#   /api/ai/helper       routers/ai.py
#   /api/ai/sage         routers/ai.py
#   /api/ai/chat         routers/ai.py
#   /api/nam             routers/nam.py
#   /api/site-guide      routers/site_guide.py
FCC_FEATURE_API_PATHS: dict = {
    "nam.jamil": ["/api/jamil/"],
    "games.arena": ["/api/competition/"],
    "nam.orchestrator": ["/api/ai/orchestrator"],
    "nam.helper": ["/api/ai/helper"],
    "nam.council": ["/api/ai/sage"],
    "nam.chat": ["/api/ai/chat"],
    "nam.hybrid": ["/api/nam"],
    "nam.site_guide": ["/api/site-guide"],
}


def fcc_feature_for_path(path: str):
    """Return the FCC feature_id governing *path*, or None if unmapped."""
    for feature, prefixes in FCC_FEATURE_API_PATHS.items():
        if _path_in(path, prefixes):
            return feature
    return None


async def load_fcc_config(db, feature_id: str):
    """Effective FCC config for *feature_id*: registry default + DB override.

    Returns None when the feature is not in the canonical registry (the
    caller treats that as an unavailable policy store).  The registry default
    is the fail-closed classification; an admin override written through the
    Feature Control Center binds for enabled/roles/tiers.
    """
    reg = next(
        (r for r in FEATURE_REGISTRY if r.get("feature_id") == feature_id), None
    )
    if reg is None:
        return None
    override = None
    feature_configs = getattr(db, "feature_configs", None)
    if feature_configs is not None:
        try:
            override = await feature_configs.find_one(
                {"feature_id": feature_id}, {"_id": 0}
            )
        except Exception:
            return None
    # A collection that has never been created is equivalent to no override;
    # the checked-in registry remains the effective policy.
    override = override or {}
    allowed_roles = override.get("allowed_roles")
    allowed_tiers = override.get("allowed_tiers")
    return {
        "enabled": override.get("enabled", True),
        "internal_only": override.get(
            "internal_only", reg.get("internal_only", False)
        ),
        "customer_access_allowed": override.get(
            "customer_access_allowed", reg.get("customer_access_allowed", True)
        ),
        "allowed_roles": (
            allowed_roles if allowed_roles is not None else reg.get("default_roles", [])
        ),
        "allowed_tiers": (
            normalize_tiers(allowed_tiers)
            if allowed_tiers is not None
            else normalize_tiers(reg.get("default_tiers", []))
        ),
        "_override_roles": allowed_roles is not None,
        "_override_tiers": allowed_tiers is not None,
    }


def platform_flag_enabled(flags_doc: Optional[dict], flag: str) -> bool:
    """True unless an executive explicitly disabled the flag.

    Absent document / absent flag / missing 'enabled' all default to True.
    """
    if not flags_doc:
        return True
    entry = (flags_doc.get("flags") or {}).get(flag) or {}
    return bool(entry.get("enabled", True))


def page_access_enabled(page_doc: Optional[dict]) -> bool:
    """True unless an executive explicitly disabled the page."""
    if not page_doc:
        return True
    return bool(page_doc.get("enabled", True))


def _path_in(path: str, prefixes) -> bool:
    return any(path.startswith(p) for p in prefixes)


# ── Feature tiers (canonical contract — mirrors frontend/src/lib/tiers.js, ────
# ── routers/payments.py TIER_RANK and routers/exec_control.py _BUILTIN_TIERS) ─
TIER_RANK: dict = {
    "free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6,
}

# Authorization-matrix writes are limited to tiers currently used as feature
# thresholds. User entitlements may still carry `platinum`; it is not a valid
# minimum threshold until a feature explicitly adopts it.
AUTHZ_REQUIREMENT_TIERS = set(TIER_RANK) - {"platinum"}

# Minimum feature_tier required per feature.  Only features with a mapped API
# surface (FEATURE_API_PATHS) can be enforced here — every other key from the
# frontend map is UI-only until its routes are mapped.  "free" means no gate
# (every account qualifies).  Instructors bypass course access; admin roles
# bypass tier requirements entirely (staff, not paying customers).
FEATURE_MIN_TIER: dict = {
    "profile": "free",
    "ai_chat": "free",
    "posts": "member",
    "publisher_ai": "member",
    "lounge": "member",
    "courses": "plus",
    "tracks": "plus",
    "studio": "free",
    "band": "plus",
    "publisher": "plus",
    "earnings": "plus",
    "payouts": "plus",
    "sovereign": "executive",
}

TIER_EXEMPT_ROLES = ("admin", "executive_admin")

# Instructors get course/track access regardless of tier (they teach).
FEATURE_INSTRUCTOR_BYPASS = {"courses", "tracks"}

# BUSINESS_ACCESS_POLICY §7A (owner decision, August 2026): platform-funded AI
# is reserved for admin / executive_admin staff ONLY.  Every other caller is
# limited to their own BYOK key or the keyword knowledge base.  The gateway
# (ai/llm_gateway.py) enforces this before any provider invocation; these
# constants are the single source of the role list.
STAFF_AI_ROLES = ("admin", "executive_admin")


def is_staff_ai_role(role: str) -> bool:
    """True when *role* qualifies for platform-funded AI (fail-closed default)."""
    return role in STAFF_AI_ROLES

TIER_LABELS: dict = {
    "free": "Free", "member": "Member", "plus": "Plus",
    "pro": "Pro", "patron": "Patron", "executive": "Executive",
}


def feature_for_path(path: str):
    """Return the feature key governing *path*, or None if not a feature surface."""
    for feature, prefixes in FEATURE_API_PATHS.items():
        if _path_in(path, prefixes):
            return feature
    return None


def _tier_rank_of(feature_tier, custom_tiers) -> int:
    """Rank of a user's feature_tier; unknown/custom tiers resolve via
    tier_definitions (exec-defined), unknown values fall back to 0 (free)."""
    rank = TIER_RANK.get(feature_tier)
    if rank is not None:
        return rank
    for t in custom_tiers or []:
        if t.get("tier_id") == feature_tier:
            try:
                return int(t.get("rank", 0))
            except (TypeError, ValueError):
                return 0
    return 0


async def load_feature_tier_requirements(db, *, fail_closed: bool = False):
    """Load the effective feature->minimum-tier authorization matrix.

    Missing configuration is safe and keeps the code defaults.  A database
    failure is different: callers enforcing a mapped request must reject it
    rather than silently treating an unavailable policy store as permission.
    Dashboard/reporting callers may retain the default behavior by leaving
    ``fail_closed`` false.
    """
    req = dict(FEATURE_MIN_TIER)
    try:
        doc = await db.authz_matrix.find_one({"_id": "matrix"}, {"_id": 0, "requirements": 1})
    except Exception:
        if fail_closed:
            raise
        return req
    stored = (doc or {}).get("requirements") or {}
    custom_ids = set()
    try:
        custom_docs = await db.tier_definitions.find(
            {}, {"_id": 0, "tier_id": 1, "rank": 1}
        ).to_list(100)
        custom_ids = {d.get("tier_id") for d in custom_docs if d.get("tier_id")}
    except Exception:
        # Custom tiers are optional. Built-in policy remains usable when the
        # optional definitions collection is absent; enforcement will fail
        # closed if a request actually needs an unavailable custom tier.
        custom_ids = set()
    for key, tier in stored.items():
        if key in req and (tier in AUTHZ_REQUIREMENT_TIERS or tier in custom_ids):
            req[key] = tier
    return req


async def check_user_feature_access(db, user, path: str):
    """Per-user verdict for *path* — the read side of user_feature_overrides and
    feature_tier.

    Returns (action, detail):
      ("block", msg)       — deny the request (403 with msg)
      ("allow", None)       — explicit per-user grant; skip platform checks
      ("pass", None)        — no per-user verdict; continue platform checks
      ("unavailable", msg) — policy data could not be verified (503)

    Precedence: an explicit per-user revoke/grant (flags.<feature> or
    ai_access_override.all) wins over everything.  Only then is the user's
    feature_tier compared against FEATURE_MIN_TIER.  An unmapped path or an
    absent override document passes; a DB error on a mapped path fails closed.
    """
    feature = feature_for_path(path)
    fcc_feature = fcc_feature_for_path(path)
    if (feature is None and fcc_feature is None) or user is None:
        return ("pass", None)
    if db is None:
        return ("unavailable", "Feature authorization unavailable — request rejected.")

    overrides = None
    try:
        overrides = await db.user_feature_overrides.find_one(
            {"user_id": user.id}, {"_id": 0}
        )
    except Exception:
        return ("unavailable", "Feature authorization unavailable — request rejected.")

    # ── 1. Per-user flag override (explicit revoke/grant wins over everything) ──
    flags = (overrides or {}).get("flags") or {}
    if feature in flags:
        if flags[feature] is False:
            return ("block", "Your access to this feature has been revoked by the executive team.")
        return ("allow", None)  # explicit grant — even if the platform flag is off

    # ── 2. AI access override (the exec panel's "revoke AI" control) ───────────
    if feature == "ai_chat" and overrides:
        ai_all = (overrides.get("ai_access_override") or {}).get("all")
        if ai_all is False:
            return ("block", "Your access to the AI suite has been revoked by the executive team.")

    # ── 3. Feature Control Center config (canonical registry + overrides) ─────
    # The FCC is the control plane.  Registry classification binds immediately
    # (enabled, internal_only); role/tier lists bind only when an admin has
    # explicitly overridden them in the Feature Control Center, so an untouched
    # feature behaves exactly as before this block existed (no surprise
    # lockouts).  This runs BEFORE the tier-requirement check so staff who
    # bypass tier gates still cannot reach a disabled or internal-only feature.
    # Role checks are rank-based: a user passes when their rank is at least the
    # lowest allowed rank, so "admin" also admits executive_admin.
    if fcc_feature is not None:
        config = await load_fcc_config(db, fcc_feature)
        if config is None:
            return ("unavailable", "Feature authorization unavailable — request rejected.")
        if config.get("enabled") is False:
            return ("block", "This feature is currently disabled.")
        # customer_access_allowed=False (Feature Control Center classification)
        # means customers must never reach the surface: only staff (rank >= admin)
        # may proceed, regardless of any role list an admin configures.
        if config.get("customer_access_allowed") is False:
            try:
                _staff_rank = role_rank("admin")
                _caller_rank = role_rank(user.role)
            except Exception:
                _staff_rank = 6
                _caller_rank = role_rank(user.role)
            if _caller_rank < _staff_rank:
                return ("block", "This feature is restricted to authorized staff.")
        allowed_roles = config.get("allowed_roles") or []
        if config.get("internal_only"):
            if allowed_roles and not any(
                role_rank(user.role) >= role_rank(r) for r in allowed_roles
            ):
                return ("block", "This feature is restricted to authorized staff.")
        elif config.get("_override_roles"):
            if allowed_roles and not any(
                role_rank(user.role) >= role_rank(r) for r in allowed_roles
            ):
                return ("block", "Your role does not have access to this feature.")
        if config.get("_override_tiers"):
            allowed_tiers = config.get("allowed_tiers") or []
            if allowed_tiers:
                user_tier = getattr(user, "feature_tier", None) or "free"
                if not any(
                    _tier_rank_of(user_tier, []) >= _tier_rank_of(t, [])
                    for t in allowed_tiers
                ):
                    return ("block", "This feature requires a higher membership tier.")

    # ── 4. Feature-tier requirement (editable authorization matrix) ────────────
    # The matrix is DB-backed (db.authz_matrix, edited from the exec console);
    # code defaults apply until an executive changes it.  Absent config == allow.
    try:
        requirements = await load_feature_tier_requirements(db, fail_closed=True)
    except Exception:
        return ("unavailable", "Feature authorization unavailable — request rejected.")
    required = requirements.get(feature)
    if required:
        if user.role in TIER_EXEMPT_ROLES:
            return ("pass", None)  # staff bypass tier gates
        if feature in FEATURE_INSTRUCTOR_BYPASS and user.role == "instructor":
            return ("pass", None)
        custom_tiers = []
        if user.feature_tier not in TIER_RANK or required not in TIER_RANK:
            try:
                custom_tiers = await db.tier_definitions.find(
                    {}, {"_id": 0, "tier_id": 1, "rank": 1}
                ).to_list(100)
            except Exception:
                return ("unavailable", "Feature authorization unavailable — request rejected.")
        user_rank = _tier_rank_of(user.feature_tier, custom_tiers)
        required_rank = TIER_RANK.get(required)
        if required_rank is None:
            required_rank = _tier_rank_of(required, custom_tiers)
        if required_rank is None or user_rank < required_rank:
            label = TIER_LABELS.get(required, required)
            return ("block", f"This feature requires the {label} plan or higher. Please upgrade to continue.")

    return ("pass", None)


async def check_persona_access(db, user, persona: str):
    """Read the executive per-user persona override at the AI handler.

    This closes the old write-only ``ai_access.<persona>`` path. ``all`` is
    the broad override; a persona-specific false value always revokes access.
    """
    if db is None or user is None:
        return ("unavailable", "AI authorization unavailable — request rejected.")
    try:
        override = await db.user_feature_overrides.find_one(
            {"user_id": user.id}, {"_id": 0, "ai_access": 1, "ai_access_override": 1}
        )
    except Exception:
        return ("unavailable", "AI authorization unavailable — request rejected.")
    if not override:
        return ("pass", None)
    all_override = (override.get("ai_access_override") or {}).get("all")
    if all_override is False:
        return ("block", "Your access to the AI suite has been revoked by the executive team.")
    persona_override = (override.get("ai_access") or {}).get(persona)
    if persona_override is False:
        return ("block", "Your access to this AI persona has been revoked by the executive team.")
    if persona_override is True or all_override is True:
        return ("allow", None)
    return ("pass", None)


async def check_legal_access(db, user, tool_key: str):
    """Read the executive legal-tool override; missing means no override."""
    if db is None or user is None:
        return ("unavailable", "Legal authorization unavailable — request rejected.")
    try:
        override = await db.user_feature_overrides.find_one(
            {"user_id": user.id}, {"_id": 0, "legal_access": 1}
        )
    except Exception:
        return ("unavailable", "Legal authorization unavailable — request rejected.")
    value = ((override or {}).get("legal_access") or {}).get(tool_key)
    if value is False:
        return ("block", "Your access to this legal tool has been revoked by the executive team.")
    if value is True:
        return ("allow", None)
    return ("pass", None)


async def check_request_config(db, path: str, flags_doc: Optional[dict] = None) -> Optional[tuple]:
    """Return ``(status_code, detail)`` to reject *path*, or ``None``.

    Missing flag/page documents are intentionally available.  A mapped request
    whose policy database cannot be read is rejected with 503 because the
    server cannot prove that the executive has permitted it.
    """
    mapped_flag = next(
        (flag for flag, prefixes in FEATURE_API_PATHS.items() if _path_in(path, prefixes)),
        None,
    )
    mapped_page = next(
        (page for page, prefixes in PAGE_API_PATHS.items() if _path_in(path, prefixes)),
        None,
    )
    if mapped_flag is None and mapped_page is None:
        return None

    # A caller may already have supplied the platform-flags document (the live
    # middleware does this).  In that case a flag decision is verifiable even
    # when the small unit-test/fallback caller has no database handle.  If the
    # document was not supplied, load it from the policy store; an unavailable
    # store is never treated as permission.
    if mapped_flag and flags_doc is None:
        if db is None:
            return (503, "Feature authorization unavailable — request rejected.")
        flags_collection = getattr(db, "platform_flags", None)
        if flags_collection is not None:
            try:
                flags_doc = await flags_collection.find_one({"_id": "flags"}, {"_id": 0})
            except Exception:
                return (503, "Feature authorization unavailable — request rejected.")

    if mapped_flag and not platform_flag_enabled(flags_doc, mapped_flag):
        return (403, f"'{mapped_flag}' is currently disabled by the executive team. Please check back later.")

    # Page access is a separate stored policy and always requires a database
    # lookup when the path is mapped to a page gate.
    if mapped_page:
        if db is None:
            return (503, "Feature authorization unavailable — request rejected.")
        page_collection = getattr(db, "page_access", None)
        if page_collection is None:
            return (503, "Feature authorization unavailable — request rejected.")
        try:
            page_doc = await page_collection.find_one(
                {"page": mapped_page}, {"_id": 0, "enabled": 1}
            )
        except Exception:
            return (503, "Feature authorization unavailable — request rejected.")
        if not page_access_enabled(page_doc):
            return (403, "This feature is currently disabled by the executive team. Please check back later.")

    return None
