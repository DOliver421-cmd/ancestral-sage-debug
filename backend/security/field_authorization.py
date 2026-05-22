"""
Field-Level Authorization Module

Determines which fields a user can see based on their role and relationship to the data.
Applied to all user profile and financial endpoints.
"""

from typing import Set, Dict, Optional


class FieldAuthorization:
    """Role-based field visibility control"""

    # Field visibility matrix: role -> set of allowed fields
    FIELD_VISIBILITY = {
        # Guest/anonymous users (minimal access)
        "guest": {
            "id", "full_name", "role",
            "created_at",  # Public creation date only
        },

        # Student role (sees own profile, limited peer visibility)
        "student": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "bio", "avatar_url", "location",
        },

        # Creator role (sees own financials, limited peer visibility)
        "creator": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "bio", "avatar_url",
            # Creator-specific (only own profile):
            "totalEarnings", "monthlyRevenue", "payoutMethod",
            "bankAccount", "courses_created", "students_enrolled",
        },

        # Mentor role (sees creator data + moderation info)
        "mentor": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "totalEarnings", "monthlyRevenue",
            "courses_created", "students_enrolled",
            "last_login", "is_active",
        },

        # Moderator role (sees all except payment details)
        "moderator": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "totalEarnings", "monthlyRevenue",
            "courses_created", "students_enrolled",
            "last_login", "is_active",
            "reports_against", "warning_count",
            "ip_address", "user_agent",
        },

        # Steward role (can see payment methods, not numbers)
        "steward": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "totalEarnings", "monthlyRevenue",
            "payoutMethod",  # TYPE only, not account number
            "courses_created", "students_enrolled",
            "last_login", "is_active",
            "reports_against", "warning_count",
            "ip_address", "user_agent",
            "last_payout_at",
        },

        # Elder role (full access except passwords)
        "elder": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "totalEarnings", "monthlyRevenue", "payoutMethod",
            "bankAccount",  # Last 4 digits masked
            "courses_created", "students_enrolled",
            "last_login", "is_active",
            "reports_against", "warning_count",
            "ip_address", "user_agent",
            "last_payout_at",
            "associate", "must_change_password",
        },

        # Admin role (full access except master secrets)
        "admin": {
            "id", "full_name", "role", "email",
            "created_at", "partnership_level", "total_points",
            "totalEarnings", "monthlyRevenue", "payoutMethod",
            "bankAccount",  # Last 4 digits masked
            "courses_created", "students_enrolled",
            "last_login", "is_active",
            "reports_against", "warning_count",
            "ip_address", "user_agent",
            "last_payout_at",
            "associate", "must_change_password",
            "2fa_enabled", "last_2fa_at",
        },

        # Executive admin (unrestricted)
        "executive_admin": {
            # All fields (password_hash filtered separately)
        },
    }

    # Sensitive financial fields that require audit logging
    SENSITIVE_FIELDS = {
        "totalEarnings", "monthlyRevenue", "payoutMethod",
        "bankAccount", "stripeConnectId", "paypalEmail",
        "taxId", "ssn", "bankRoutingNumber",
    }

    @classmethod
    def get_visible_fields(
        cls,
        viewer_role: str,
        target_role: str,
        is_own_profile: bool = False,
    ) -> Set[str]:
        """
        Determine which fields a viewer can see.

        Args:
            viewer_role: Role of the person requesting the data
            target_role: Role of the person whose data is being viewed
            is_own_profile: True if viewer is viewing their own profile

        Returns:
            Set of field names that are visible to this viewer
        """
        # Own profile: full visibility for own role
        if is_own_profile:
            return cls.FIELD_VISIBILITY.get(viewer_role, set())

        # Admin/executive can see anyone's data (except passwords)
        if viewer_role in ["admin", "executive_admin"]:
            return cls.FIELD_VISIBILITY.get(viewer_role, set()) or set()

        # Role hierarchy: higher roles see more
        role_hierarchy = {
            "guest": 0,
            "student": 1,
            "creator": 2,
            "mentor": 3,
            "moderator": 4,
            "steward": 5,
            "elder": 6,
            "admin": 7,
            "executive_admin": 8,
        }

        viewer_level = role_hierarchy.get(viewer_role, 0)
        target_level = role_hierarchy.get(target_role, 0)

        # Higher role always sees more
        if viewer_level > target_level:
            return cls.FIELD_VISIBILITY.get(viewer_role, set())

        # Equal role: limited peer visibility
        if viewer_level == target_level:
            return {
                "id", "full_name", "role", "partnership_level",
                "total_points", "bio", "avatar_url", "created_at"
            }

        # Lower role: minimal visibility
        return cls.FIELD_VISIBILITY.get("guest", set())

    @classmethod
    def filter_response(
        cls,
        data: Dict,
        visible_fields: Set[str],
    ) -> Dict:
        """
        Filter a response dict to only include visible fields.

        Args:
            data: Full user document
            visible_fields: Set of allowed field names

        Returns:
            Filtered dict with only visible fields
        """
        # Always remove these fields
        blacklist = {"password_hash", "_id", "recovery_codes", "last_recovery_reset"}

        filtered = {}
        for key, value in data.items():
            if key in blacklist:
                continue
            if key in visible_fields:
                # Mask sensitive fields
                if key == "bankAccount" and value:
                    filtered[key] = f"****{value[-4:]}"  # Last 4 digits only
                elif key == "ssn" and value:
                    filtered[key] = f"***-**-{value[-4:]}"
                else:
                    filtered[key] = value

        return filtered

    @classmethod
    def requires_sensitive_audit(cls, accessed_fields: Set[str]) -> bool:
        """Check if accessed fields require audit logging"""
        return bool(accessed_fields & cls.SENSITIVE_FIELDS)


# Helper function for FastAPI endpoints
def get_visible_fields(viewer: dict, target: dict, is_own: bool = False) -> Set[str]:
    """
    Convenience function for use in FastAPI endpoints.

    Usage:
        visible = get_visible_fields(current_user, target_user, is_own=False)
        filtered = FieldAuthorization.filter_response(target_user, visible)
    """
    return FieldAuthorization.get_visible_fields(
        viewer_role=viewer.get("role", "guest"),
        target_role=target.get("role", "guest"),
        is_own_profile=is_own,
    )
