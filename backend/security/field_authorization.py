"""
Field-Level Authorization Module

Controls which fields are visible based on the viewer's role.
8-tier system: student(1) | trial_pass(2) | instructor(3) | support_staff(4)
              | oversight(5) | admin(6) | executive_admin(7)
"""

from typing import Set, Dict, Optional
from roles import role_rank, normalize_role, ROLE_RANK as CANONICAL_ROLE_RANK


# Fields ALWAYS stripped — never returned in any response
_BLACKLIST = {"password_hash", "_id", "recovery_codes", "last_recovery_reset"}

# Role hierarchy imported from roles.py (canonical source of truth)

# Fields each role can see on their OWN profile
_OWN_PROFILE_BASE = {
    "id", "email", "full_name", "role", "associate",
    "is_active", "created_at", "avatar_url",
    "must_change_password", "last_login",
    "partnership_level", "total_points",
    "feature_tier", "sage_tier",
    "terms_accepted_at", "over_13_confirmed",
    "bio", "location",
}

_OWN_PROFILE_CREATOR = _OWN_PROFILE_BASE | {
    "totalEarnings", "monthlyRevenue", "payoutMethod",
    "courses_created", "students_enrolled",
    "bankAccount", "payoutAccountId", "paypalEmail",
}

_OWN_PROFILE_BY_ROLE: Dict[str, Set[str]] = {
    "student":          _OWN_PROFILE_BASE,
    "trial_pass":       _OWN_PROFILE_BASE,
    "instructor":       _OWN_PROFILE_BASE | {"associate", "must_change_password"},
    "support_staff":    _OWN_PROFILE_BASE | {"reports_against", "warning_count"},
    "oversight":        _OWN_PROFILE_CREATOR | {"mentee_count", "vote_weight", "board_access"},
    "admin":            None,   # None = all fields (password_hash still stripped)
    "executive_admin":  None,
}

# Fields visible when viewing SOMEONE ELSE's profile
_PEER_PUBLIC = {"id", "full_name", "role", "created_at", "avatar_url", "bio", "partnership_level"}

_PEER_BY_VIEWER_ROLE: Dict[str, Optional[Set[str]]] = {
    "student":          _PEER_PUBLIC,
    "trial_pass":       _PEER_PUBLIC,
    "instructor":       _PEER_PUBLIC | {"email", "associate", "is_active", "last_login", "must_change_password"},
    "support_staff":    _PEER_PUBLIC | {"email", "is_active", "last_login", "reports_against", "warning_count", "ip_address"},
    "oversight":        _PEER_PUBLIC | {
        "email", "is_active", "last_login",
        "totalEarnings", "monthlyRevenue", "payoutMethod",
        "courses_created", "students_enrolled",
        "reports_against", "warning_count",
    },
    "admin":            None,
    "executive_admin":  None,
}


class FieldAuthorization:

    @classmethod
    def get_visible_fields(
        cls,
        viewer_role: str,
        target_role: str,
        is_own_profile: bool = False,
    ) -> Optional[Set[str]]:
        """
        Return the set of fields the viewer may see.
        None = unrestricted (admin / executive_admin) — password_hash still stripped.
        Legacy role strings are normalized before lookup.
        """
        canonical = normalize_role(viewer_role)
        if is_own_profile:
            return _OWN_PROFILE_BY_ROLE.get(canonical, _OWN_PROFILE_BASE)

        return _PEER_BY_VIEWER_ROLE.get(canonical, _PEER_PUBLIC)

    @classmethod
    def filter_response(
        cls,
        data: Dict,
        visible_fields: Optional[Set[str]],
    ) -> Dict:
        """Strip blacklisted fields, apply visibility, mask sensitive values."""
        result = {}
        for key, value in data.items():
            if key in _BLACKLIST:
                continue
            if visible_fields is None or key in visible_fields:
                # Mask last-4 for bank account numbers
                if key == "bankAccount" and value and isinstance(value, str) and len(value) > 4:
                    result[key] = f"****{value[-4:]}"
                elif key == "ssn" and value and isinstance(value, str) and len(value) > 4:
                    result[key] = f"***-**-{value[-4:]}"
                else:
                    result[key] = value
        return result

    @classmethod
    def requires_sensitive_audit(cls, accessed_fields: Set[str]) -> bool:
        _sensitive = {
            "totalEarnings", "monthlyRevenue", "payoutMethod",
            "bankAccount", "payoutAccountId", "paypalEmail",
            "taxId", "ssn", "bankRoutingNumber",
        }
        return bool(accessed_fields & _sensitive)


def get_visible_fields(
    viewer: dict,
    target: dict,
    is_own: bool = False,
) -> Optional[Set[str]]:
    """Convenience wrapper for FastAPI endpoints."""
    return FieldAuthorization.get_visible_fields(
        viewer_role=viewer.get("role", "student"),
        target_role=target.get("role", "student"),
        is_own_profile=is_own,
    )
