"""
backend/security/unifier_access.py

Unifier access control.

Policy (owner decision):
  - staff role OR higher (support_staff, oversight, admin, executive_admin)
  - patron feature tier OR higher (patron, platinum, executive)

This is the authoritative helper for the Unifier router. Do not let the
router duplicate this logic. Tier ranking is imported from the canonical
contract in security/feature_control.py so this gate can never drift from
the rest of the platform.
"""

from __future__ import annotations

from typing import Any

from security.feature_control import TIER_RANK

STAFF_ROLES = frozenset({
    "support_staff",
    "oversight",
    "admin",
    "executive_admin",
})

_PATRON_RANK = TIER_RANK["patron"]


def user_can_use_unifier(user: Any) -> bool:
    if user is None:
        return False
    role = getattr(user, "role", "student") or "student"
    role_lower = str(role).strip().lower()
    if role_lower not in STAFF_ROLES:
        return False
    tier = getattr(user, "feature_tier", "free") or "free"
    tier_lower = str(tier).strip().lower()
    return TIER_RANK.get(tier_lower, 0) >= _PATRON_RANK
