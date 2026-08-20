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

Per-user feature overrides (user_feature_overrides) are still write-only and
are the known next phase: they need the user identity at the point of the
feature check (handler-level), so they are NOT part of this middleware.
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
