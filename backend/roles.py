"""roles.py — Canonical role definitions for the WAI platform.

Single source of truth.  Import from here instead of duplicating ROLE_RANK
or the Role Literal in every router.

8-tier system (2026-08-19):
  0  public          — unauthenticated visitor
  1  student         — registered learner
  2  trial_pass      — trial / priority member
  3  instructor      — instructor / moderator
  4  support_staff   — site support operations
  5  oversight       — oversight / governance
  6  admin           — platform administrator
  7  executive_admin — owner / executive
"""

from typing import Literal

# ── Role string type ─────────────────────────────────────────────────────────
Role = Literal[
    "student",
    "trial_pass",
    "instructor",
    "support_staff",
    "oversight",
    "admin",
    "executive_admin",
]

# All valid role strings (for migration checks and admin UI dropdowns).
ALL_ROLES: tuple[str, ...] = ("student", "trial_pass", "instructor", "support_staff", "oversight", "admin", "executive_admin")

# ── Hierarchy (higher rank = more authority) ─────────────────────────────────
ROLE_RANK: dict[str, int] = {
    "public":          0,   # unauthenticated — not stored in DB
    "student":         1,
    "trial_pass":      2,
    "instructor":      3,
    "support_staff":   4,
    "oversight":       5,
    "admin":           6,
    "executive_admin": 7,
}

# ── Legacy migration map ─────────────────────────────────────────────────────
# Old role strings that may exist in MongoDB → new canonical strings.
# Keys are old values; values are (new_string, new_rank).
LEGACY_ROLE_MAP: dict[str, tuple[str, int]] = {
    "priority_member":  ("trial_pass",    2),
    "site_support":     ("support_staff", 4),
    "creative_partner": ("instructor",    3),   # vision contributor → instructor rank
    "guest":            ("student",       1),   # legacy guest → student
    "creator":          ("instructor",    3),
    "mentor":           ("instructor",    3),
    "moderator":        ("instructor",    3),
    "steward":          ("oversight",     5),
    "elder":            ("oversight",     5),
}

# ── Role-based defaults for persona routing ──────────────────────────────────
ROLE_PERSONA_DEFAULTS: dict[str, str] = {
    "student":         "assistant_director",
    "trial_pass":      "assistant_director",
    "instructor":      "assistant_director",
    "support_staff":   "assistant_director",
    "oversight":       "director",
    "admin":           "director",
    "executive_admin": "director",
}

# ── Roles that get free BYOK ────────────────────────────────────────────────
FREE_BYOK_ROLES: frozenset[str] = frozenset({
    "instructor", "support_staff", "oversight", "admin", "executive_admin",
})

# ── Convenience helpers ──────────────────────────────────────────────────────

def normalize_role(old_role: str) -> str:
    """Map a legacy role string to the current canonical form.

    Returns the canonical role name.  Unknown roles fall back to 'student'.
    """
    if old_role in LEGACY_ROLE_MAP:
        return LEGACY_ROLE_MAP[old_role][0]
    if old_role in ALL_ROLES:
        return old_role
    return "student"          # safe default — least-privilege


def role_rank(role: str) -> int:
    """Return the integer rank for a role (handles legacy strings via normalize)."""
    canonical = normalize_role(role)
    return ROLE_RANK.get(canonical, 0)


def has_rank(user_role: str, min_role: str) -> bool:
    """True iff user_role's rank >= min_role's rank."""
    return role_rank(user_role) >= role_rank(min_role)
