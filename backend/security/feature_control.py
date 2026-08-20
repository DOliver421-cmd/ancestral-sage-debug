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
verified against the real route table before it is added.

Per-user enforcement (user_feature_overrides + feature_tier) lives in
check_user_feature_access() and runs in the same middleware, but only for
requests that carry a valid session: an explicit per-user revoke/grant wins
over the platform checks, and the user's feature_tier is compared against
FEATURE_MIN_TIER (the exact mirror of frontend/src/lib/tiers.js).  Absent
override == no verdict == behave exactly as before this module existed.
"""

from __future__ import annotations

from typing import Optional

# Platform feature flag -> API path prefixes it governs.  Keep in sync with the
# frontend's TIER_FOR_FEATURE keys and the live route table.
FEATURE_API_PATHS: dict = {
    "ai_chat": ["/api/ai/"],
    "posts": ["/api/more/"],
    "courses": ["/api/modules", "/api/progress", "/api/labs", "/api/credentials"],
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
    "ai_chat": "free",   # no gate — but revocable per-user via flags/ai_access
    "posts": "member",
    "courses": "plus",
}

TIER_EXEMPT_ROLES = ("admin", "executive_admin")

# Instructors get course/track access regardless of tier (they teach).
FEATURE_INSTRUCTOR_BYPASS = {"courses"}

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


async def load_feature_tier_requirements(db):
    """Effective feature->min-tier map: the DB authorization matrix over code defaults.

    Only keys that exist in the code defaults are honored — the enforcement
    contract is the code map, so a bad write can never create a gate for an
    unmapped feature.  Absent doc / DB error -> code defaults (identical to
    today's behavior: deploy changes nothing until an executive edits the
    matrix in the console).
    """
    req = dict(FEATURE_MIN_TIER)
    try:
        doc = await db.authz_matrix.find_one({"_id": "matrix"}, {"_id": 0, "requirements": 1})
    except Exception:
        return req
    stored = (doc or {}).get("requirements") or {}
    for key, tier in stored.items():
        if key in req and tier in TIER_RANK:
            req[key] = tier
    return req


async def check_user_feature_access(db, user, path: str):
    """Per-user verdict for *path* — the read side of user_feature_overrides and
    feature_tier.

    Returns (action, detail):
      ("block", msg)  — deny the request (403 with msg)
      ("allow", None) — explicit per-user grant; skip the platform checks
      ("pass", None)  — no per-user verdict; continue to platform checks

    Precedence: an explicit per-user revoke/grant (flags.<feature> or
    ai_access_override.all) wins over everything.  Only then is the user's
    feature_tier compared against FEATURE_MIN_TIER.  Absent config == allow;
    db/user None or DB errors fail open.
    """
    feature = feature_for_path(path)
    if feature is None or db is None or user is None:
        return ("pass", None)

    overrides = None
    try:
        overrides = await db.user_feature_overrides.find_one(
            {"user_id": user.id}, {"_id": 0}
        )
    except Exception:
        overrides = None  # fail-open on DB errors (never block the site)

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
    requirements = FEATURE_MIN_TIER
    if db is not None:
        try:
            requirements = await load_feature_tier_requirements(db)
        except Exception:
            requirements = FEATURE_MIN_TIER
    required = requirements.get(feature)
    if required:
        if user.role in TIER_EXEMPT_ROLES:
            return ("pass", None)  # staff bypass tier gates
        if feature in FEATURE_INSTRUCTOR_BYPASS and user.role == "instructor":
            return ("pass", None)
        custom_tiers = []
        if user.feature_tier not in TIER_RANK:
            try:
                custom_tiers = await db.tier_definitions.find(
                    {}, {"_id": 0, "tier_id": 1, "rank": 1}
                ).to_list(100)
            except Exception:
                custom_tiers = []
        if _tier_rank_of(user.feature_tier, custom_tiers) < TIER_RANK[required]:
            label = TIER_LABELS.get(required, required)
            return ("block", f"This feature requires the {label} plan or higher. Please upgrade to continue.")

    return ("pass", None)


async def check_request_config(db, path: str, flags_doc: Optional[dict] = None) -> Optional[tuple]:
    """Return (status_code, detail) to reject *path* with, or None to allow.

    Runs AFTER the existing platform_locked check.  Only blocks when an
    explicit ``enabled: false`` exists for a mapped flag/page.  db may be None
    (database disabled) — then nothing is ever blocked.
    """
    # ── Platform feature flags ────────────────────────────────────────────────
    for flag, prefixes in FEATURE_API_PATHS.items():
        if _path_in(path, prefixes) and not platform_flag_enabled(flags_doc, flag):
            return (403, f"'{flag}' is currently disabled by the executive team. Please check back later.")

    # ── Page access board (server-side, not just hidden in the frontend) ─────
    for page_key, prefixes in PAGE_API_PATHS.items():
        if _path_in(path, prefixes):
            page_doc = None
            if db is not None:
                try:
                    page_doc = await db.page_access.find_one(
                        {"page": page_key}, {"_id": 0, "enabled": 1}
                    )
                except Exception:
                    page_doc = None  # fail-open on DB errors (never block the site)
            if not page_access_enabled(page_doc):
                return (403, f"This feature is currently disabled by the executive team. Please check back later.")

    return None
