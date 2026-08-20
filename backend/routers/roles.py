"""
Platform role definitions — shared by backend routers and server.py.

Role hierarchy (aligned with the platform's oversight structure):
    0. public          — unauthenticated visitor
    1. student         — registered user, basic access
    2. trial_pass      — temporary elevated access (trial period)
    3. instructor      — can moderate, manage curriculum (moderator alias)
    4. site_support    — support staff, ticketing, help desk
    5. oversight       — can view analytics, audit logs, platform health
    6. admin           — full administrative access
    7. executive_admin — executive control, sovereign command, seat-level authority

Legacy aliases are preserved so existing MongoDB documents continue to work.
"""
from typing import Literal

# ── Role type ──────────────────────────────────────────────────────────────
# Covers every role string used anywhere in the codebase.
Role = Literal[
    "public",
    "student",
    "trial_pass",
    "creative_partner",
    "priority_member",
    "instructor",
    "moderator",
    "site_support",
    "support_staff",
    "oversight",
    "admin",
    "executive_admin",
    "elder",
]

# ── Numeric rank for hierarchical access checks ────────────────────────────
# Higher rank passes lower-rank checks.  Legacy aliases map to their
# canonical equivalents so `require_role("admin")` still works for
# documents that store "site_support" etc.
ROLE_RANK: dict[str, int] = {
    "public":          0,
    "student":         1,
    "trial_pass":      2,
    "creative_partner": 2,   # legacy alias — treated like trial_pass
    "priority_member":  2,   # legacy alias — treated like trial_pass
    "instructor":      3,
    "moderator":       3,   # alias for instructor
    "site_support":    4,
    "support_staff":   4,   # alias for site_support
    "oversight":       5,
    "admin":           6,
    "executive_admin": 7,
    "elder":           7,   # elder council = executive level
}
