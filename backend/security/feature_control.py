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
    "free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5,
}

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
    "studio": "plus",
    "band": "plus",
    "publisher": "plus",
    "earnings": "plus",
    "payouts": "plus",
    "sovereign": "executive",
}

TIER_EXEMPT_ROLES = ("admin", "executive_admin")

# Instructors get course/track access regardless of tier (they teach).
FEATURE_INSTRUCTOR_BYPASS = {"courses", "tracks"}

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
        if key in req and (tier in TIER_RANK or tier in custom_ids):
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
    if feature is None or user is None:
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

    # ── 3. Feature-tier requirement (editable authorization matrix) ────────────
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
