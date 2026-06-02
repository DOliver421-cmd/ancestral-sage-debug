"""
Field-Level Authorization Module

Controls which fields are visible based on the viewer's role.

Two overlapping role systems on this platform:
  Core auth:       student | instructor | admin | executive_admin
  Community/creator: guest | student | creator | mentor | moderator | steward | elder | admin

Both are real. This module handles all of them.
"""

from typing import Set, Dict, Optional


# Fields ALWAYS stripped — never returned in any response
_BLACKLIST = {"password_hash", "_id", "recovery_codes", "last_recovery_reset"}

# Unified role hierarchy — higher rank = more visibility
# instructor sits between student and creator (core platform teacher role)
ROLE_RANK: Dict[str, int] = {
    "guest":            0,
    "student":          1,
    "instructor":       2,   # Core platform: teaches courses, views student data
    "creator":          2,   # Community: publishes courses, earns revenue
    "mentor":           3,   # Community: mentors users, additional access
    "moderator":        4,   # Community: moderates content and posts
    "steward":          5,   # Community: governance + financial visibility
    "elder":            6,   # Community: board-level, full analytics
    "admin":            7,   # Platform admin
    "executive_admin":  8,   # Owner — unrestricted
}

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
    "bankAccount", "stripeConnectId", "paypalEmail",
}

_OWN_PROFILE_BY_ROLE: Dict[str, Set[str]] = {
    "guest":            {"id", "full_name", "role", "created_at"},
    "student":          _OWN_PROFILE_BASE,
    "instructor":       _OWN_PROFILE_BASE | {"associate", "must_change_password"},
    "creator":          _OWN_PROFILE_CREATOR,
    "mentor":           _OWN_PROFILE_CREATOR | {"mentee_count"},
    "moderator":        _OWN_PROFILE_BASE | {"reports_against", "warning_count"},
    "steward":          _OWN_PROFILE_CREATOR | {"mentee_count", "vote_weight"},
    "elder":            _OWN_PROFILE_CREATOR | {"mentee_count", "vote_weight", "board_access"},
    "admin":            None,   # None = all fields (password_hash still stripped)
    "executive_admin":  None,
}

# Fields visible when viewing SOMEONE ELSE's profile
_PEER_PUBLIC = {"id", "full_name", "role", "created_at", "avatar_url", "bio", "partnership_level"}

_PEER_BY_VIEWER_ROLE: Dict[str, Optional[Set[str]]] = {
    "guest":            _PEER_PUBLIC - {"bio"},
    "student":          _PEER_PUBLIC,
    "instructor":       _PEER_PUBLIC | {"email", "associate", "is_active", "last_login", "must_change_password"},
    "creator":          _PEER_PUBLIC | {"courses_created", "students_enrolled", "total_points"},
    "mentor":           _PEER_PUBLIC | {"courses_created", "students_enrolled", "total_points", "email"},
    "moderator":        _PEER_PUBLIC | {"email", "is_active", "last_login", "reports_against", "warning_count", "ip_address"},
    "steward":          _PEER_PUBLIC | {
        "email", "is_active", "last_login",
        "totalEarnings", "monthlyRevenue", "payoutMethod",
        "courses_created", "students_enrolled",
        "reports_against", "warning_count",
    },
    "elder":            _PEER_PUBLIC | {
        "email", "is_active", "last_login",
        "totalEarnings", "monthlyRevenue", "payoutMethod",
        "bankAccount",  # masked to last 4 digits in filter_response
        "courses_created", "students_enrolled",
        "reports_against", "warning_count",
        "ip_address", "user_agent",
        "associate", "must_change_password",
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
        """
        if is_own_profile:
            return _OWN_PROFILE_BY_ROLE.get(viewer_role, _OWN_PROFILE_BASE)

        return _PEER_BY_VIEWER_ROLE.get(viewer_role, _PEER_PUBLIC)

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
            "bankAccount", "stripeConnectId", "paypalEmail",
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
        viewer_role=viewer.get("role", "guest"),
        target_role=target.get("role", "guest"),
        is_own_profile=is_own,
    )
