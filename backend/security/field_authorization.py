"""
Field-Level Authorization Module

Controls which fields are visible based on the viewer's role.
Roles: student | instructor | admin | executive_admin
"""

from typing import Set, Dict, Optional


# Fields that are ALWAYS stripped from every response
_BLACKLIST = {"password_hash", "_id", "recovery_codes", "last_recovery_reset"}

# Fields every authenticated user can see on their OWN profile
_OWN_PROFILE_FIELDS = {
    "id", "email", "full_name", "role", "associate",
    "is_active", "created_at", "avatar_url",
    "must_change_password", "last_login",
    "partnership_level", "total_points",
    "feature_tier", "sage_tier",
    "totp_secret",
    "terms_accepted_at", "over_13_confirmed",
}

# Fields visible when viewing ANOTHER user's profile
_PEER_FIELDS = {"id", "full_name", "role", "created_at", "avatar_url"}

_INSTRUCTOR_FIELDS = _PEER_FIELDS | {
    "email", "associate", "is_active", "last_login",
    "must_change_password", "partnership_level", "total_points",
}

_ADMIN_FIELDS = _INSTRUCTOR_FIELDS | {
    "feature_tier", "sage_tier",
    "banned", "ban_reason", "banned_at",
    "login_failed_attempts", "login_locked_until",
    "gdpr_deleted_at", "gdpr_grace_until",
}

_EXEC_FIELDS = None  # None = all fields (password_hash still stripped)

_FIELDS_BY_ROLE: Dict[str, Optional[Set[str]]] = {
    "student":          _PEER_FIELDS,
    "instructor":       _INSTRUCTOR_FIELDS,
    "admin":            _ADMIN_FIELDS,
    "executive_admin":  _EXEC_FIELDS,
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
        None means unrestricted (executive_admin).
        """
        if viewer_role == "executive_admin":
            return None

        if is_own_profile:
            return _OWN_PROFILE_FIELDS

        return _FIELDS_BY_ROLE.get(viewer_role, _PEER_FIELDS)

    @classmethod
    def filter_response(
        cls,
        data: Dict,
        visible_fields: Optional[Set[str]],
    ) -> Dict:
        """Strip blacklisted fields and apply role-based visibility."""
        result = {}
        for key, value in data.items():
            if key in _BLACKLIST:
                continue
            if visible_fields is None or key in visible_fields:
                result[key] = value
        return result


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
