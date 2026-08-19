"""
Role-Based Access Control (RBAC) System
Manages user roles, permissions, and partnership-based access
"""

from enum import Enum
from typing import List, Set
from datetime import datetime
from roles import normalize_role, role_rank, ALL_ROLES

class UserRole(str, Enum):
    """User roles in WAI platform (8-tier system)"""
    STUDENT = "student"
    TRIAL_PASS = "trial_pass"
    INSTRUCTOR = "instructor"
    SUPPORT_STAFF = "support_staff"
    OVERSIGHT = "oversight"
    ADMIN = "admin"
    EXECUTIVE_ADMIN = "executive_admin"

class PartnershipLevel(str, Enum):
    """Partnership levels tied to milestones"""
    SEED = "seed"
    ROOTED = "rooted"
    BUILDER = "builder"
    STEWARD = "oversight"
    ELDER = "oversight"

# Permission mapping: what each role can do
# 8-tier role permissions (cumulative — each tier inherits lower tiers)
_STUDENT_PERMS = {
    "browse_courses", "enroll_courses", "view_progress", "write_reviews",
    "view_public_profiles", "join_community", "comment_on_posts",
}
_TRIAL_PASS_PERMS = _STUDENT_PERMS | {
    "view_marketplace", "early_access",
}
_INSTRUCTOR_PERMS = _TRIAL_PASS_PERMS | {
    "create_course", "publish_course", "edit_own_courses",
    "view_earnings", "request_payout", "access_creator_dashboard",
    "create_posts", "upload_media", "moderate_posts",
    "delete_harmful_content", "issue_warnings", "mentor_users",
    "access_mentee_data", "create_mentorship_program",
}
_SUPPORT_STAFF_PERMS = _INSTRUCTOR_PERMS | {
    "ban_users", "pin_discussions", "feature_content",
    "view_reports", "view_audit_logs",
}
_OVERSIGHT_PERMS = _SUPPORT_STAFF_PERMS | {
    "vote_on_decisions", "propose_changes", "allocate_creator_fund",
    "access_governance_dashboard", "review_proposals",
    "board_advisory_access", "approve_major_changes",
    "shape_platform_direction", "access_all_analytics",
}
_ADMIN_PERMS = _OVERSIGHT_PERMS | {
    "admin_access", "manage_users", "manage_roles",
    "view_all_data", "modify_system_settings", "access_database",
    "view_financial_reports", "manage_payments", "create_admin_users",
}
_EXEC_PERMS = _ADMIN_PERMS | {
    "system_override", "executive_broadcast",
}

ROLE_PERMISSIONS = {
    UserRole.STUDENT: _STUDENT_PERMS,
    UserRole.TRIAL_PASS: _TRIAL_PASS_PERMS,
    UserRole.INSTRUCTOR: _INSTRUCTOR_PERMS,
    UserRole.SUPPORT_STAFF: _SUPPORT_STAFF_PERMS,
    UserRole.OVERSIGHT: _OVERSIGHT_PERMS,
    UserRole.ADMIN: _ADMIN_PERMS,
    UserRole.EXECUTIVE_ADMIN: _EXEC_PERMS,
}

# Partnership-based permission unlocks
PARTNERSHIP_PERMISSIONS = {
    PartnershipLevel.SEED: set(),
    PartnershipLevel.ROOTED: {
        "create_posts",
        "vote_on_discussions",
        "apply_for_mentorship",
    },
    PartnershipLevel.BUILDER: {
        "create_posts",
        "vote_on_discussions",
        "apply_for_mentorship",
        "vote_on_minor_proposals",
        "propose_minor_changes",
    },
    PartnershipLevel.STEWARD: {
        "create_posts",
        "vote_on_discussions",
        "apply_for_mentorship",
        "vote_on_proposals",
        "propose_changes",
        "allocate_creator_fund",
    },
    PartnershipLevel.ELDER: {
        "create_posts",
        "vote_on_discussions",
        "apply_for_mentorship",
        "vote_on_proposals",
        "propose_changes",
        "allocate_creator_fund",
        "board_advisory_access",
    },
}

class AccessControl:
    """Check user permissions and access rights"""

    @staticmethod
    def has_permission(user_role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission"""
        permissions = ROLE_PERMISSIONS.get(user_role, set())
        return permission in permissions

    @staticmethod
    def has_partnership_permission(
        partnership_level: PartnershipLevel, permission: str
    ) -> bool:
        """Check if partnership level grants permission"""
        permissions = PARTNERSHIP_PERMISSIONS.get(partnership_level, set())
        return permission in permissions

    @staticmethod
    def get_role_permissions(user_role: UserRole) -> Set[str]:
        """Get all permissions for a role"""
        return ROLE_PERMISSIONS.get(user_role, set())

    @staticmethod
    def can_edit_user_profile(editor_user_id: str, target_user_id: str, editor_role: UserRole) -> bool:
        """Check if editor can edit target user's profile"""
        # Users can edit their own profile
        if editor_user_id == target_user_id:
            return True
        # Admins can edit anyone
        if editor_role == UserRole.ADMIN:
            return True
        # Others cannot edit
        return False

    @staticmethod
    def can_view_earnings(viewer_user_id: str, target_user_id: str, viewer_role: UserRole) -> bool:
        """Check if viewer can see earnings data"""
        # Users can view their own earnings
        if viewer_user_id == target_user_id:
            return True
        # Only admin+ can view others' earnings
        if role_rank(viewer_role.value) >= role_rank("oversight"):
            return True
        return False

    @staticmethod
    def can_view_payout_info(viewer_user_id: str, target_user_id: str, viewer_role: UserRole) -> bool:
        """Check if viewer can see payout/banking info (most sensitive)"""
        # Only the user themselves or admins
        if viewer_user_id == target_user_id:
            return True
        if viewer_role == UserRole.ADMIN:
            return True
        return False

    @staticmethod
    def can_moderate_content(user_role: UserRole) -> bool:
        """Check if user can moderate/delete content (instructor+)"""
        return role_rank(user_role.value) >= role_rank("instructor")

    @staticmethod
    def can_publish_course(user_role: UserRole) -> bool:
        """Check if user can publish courses (instructor+)"""
        return role_rank(user_role.value) >= role_rank("instructor")

    @staticmethod
    def can_vote_on_governance(user_role: UserRole, partnership_points: int) -> bool:
        """Check if user can vote on platform decisions (oversight+)"""
        return role_rank(user_role.value) >= role_rank("oversight")

    @staticmethod
    def get_visible_profile_fields(
        viewer_user_id: str,
        target_user_id: str,
        viewer_role: UserRole,
        target_role: UserRole,
    ) -> Set[str]:
        """
        Determine which profile fields viewer can see
        Different fields are visible to different people
        """
        base_fields = {"username", "bio", "profile_picture", "partnership_level", "badges"}

        # Users see more of their own profile
        if viewer_user_id == target_user_id:
            return (
                base_fields
                | {
                    "email",
                    "created_at",
                    "total_earnings",
                    "courses_completed",
                    "courses_created",
                    "mentee_count",
                    "payout_method",
                    "payout_status",
                    "account_settings",
                }
            )

        # Instructor+ profiles show public stats
        if role_rank(target_role.value) >= role_rank("instructor"):
            base_fields = base_fields | {
                "courses_published", "students_enrolled", "avg_rating",
                "total_earnings_public", "mentee_count",
            }

        # Admins see everything
        if viewer_role == UserRole.ADMIN:
            return {
                "username",
                "email",
                "bio",
                "profile_picture",
                "partnership_level",
                "badges",
                "created_at",
                "total_earnings",
                "courses_completed",
                "courses_created",
                "mentee_count",
                "payout_method",
                "payout_status",
                "account_settings",
                "ip_address",
                "login_history",
                "payment_methods",
            }

        return base_fields


class PermissionDeniedError(Exception):
    """Raised when user lacks required permission"""
    pass


async def require_permission(user_role: UserRole, permission: str):
    """Decorator/middleware to enforce permissions"""
    if not AccessControl.has_permission(user_role, permission):
        raise PermissionDeniedError(
            f"User role '{user_role}' does not have permission '{permission}'"
        )


async def require_role(user_role: UserRole, required_roles: List[UserRole]):
    """Enforce minimum role requirement"""
    if user_role not in required_roles:
        raise PermissionDeniedError(
            f"User role '{user_role}' not in allowed roles: {required_roles}"
        )
