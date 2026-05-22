/**
 * Frontend Security & Access Control
 * Manages role-based access, permission checking, and data visibility
 */

export const USER_ROLES = {
  GUEST: "guest",
  STUDENT: "student",
  CREATOR: "creator",
  MENTOR: "mentor",
  MODERATOR: "moderator",
  STEWARD: "steward",
  ELDER: "elder",
  ADMIN: "admin",
};

export const PARTNERSHIP_LEVELS = {
  SEED: "seed",
  ROOTED: "rooted",
  BUILDER: "builder",
  STEWARD: "steward",
  ELDER: "elder",
};

/**
 * Check if user has required role
 */
export function hasRole(userRole, requiredRole) {
  const roleHierarchy = [
    USER_ROLES.GUEST,
    USER_ROLES.STUDENT,
    USER_ROLES.CREATOR,
    USER_ROLES.MENTOR,
    USER_ROLES.MODERATOR,
    USER_ROLES.STEWARD,
    USER_ROLES.ELDER,
    USER_ROLES.ADMIN,
  ];

  const userRoleIndex = roleHierarchy.indexOf(userRole);
  const requiredRoleIndex = roleHierarchy.indexOf(requiredRole);

  return userRoleIndex >= requiredRoleIndex;
}

/**
 * Check if user can perform action
 */
export function canPerformAction(userRole, action) {
  const actionRoles = {
    // Content creation
    create_post: [USER_ROLES.STUDENT, USER_ROLES.CREATOR, USER_ROLES.MENTOR],
    create_course: [USER_ROLES.CREATOR, USER_ROLES.MENTOR, USER_ROLES.STEWARD, USER_ROLES.ELDER],
    publish_course: [USER_ROLES.CREATOR, USER_ROLES.MENTOR, USER_ROLES.STEWARD, USER_ROLES.ELDER],
    // Moderation
    delete_comment: [USER_ROLES.MODERATOR, USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    ban_user: [USER_ROLES.MODERATOR, USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    pin_post: [USER_ROLES.MODERATOR, USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    // Governance
    vote_proposal: [USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    propose_change: [USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    allocate_fund: [USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN],
    // Admin
    manage_users: [USER_ROLES.ADMIN],
    view_analytics: [USER_ROLES.ADMIN, USER_ROLES.ELDER],
  };

  const allowedRoles = actionRoles[action] || [];
  return allowedRoles.includes(userRole);
}

/**
 * Determine which profile fields are visible to viewer
 */
export function getVisibleProfileFields(viewer, target) {
  const baseFields = ["username", "bio", "profilePicture", "partnershipLevel", "badges"];

  // User viewing own profile sees everything
  if (viewer.userId === target.userId) {
    return [
      ...baseFields,
      "email",
      "createdAt",
      "totalEarnings",
      "coursesCompleted",
      "coursesCreated",
      "menteeCount",
      "payoutMethod",
      "accountSettings",
    ];
  }

  // Viewing creator profile
  if (target.role === USER_ROLES.CREATOR || target.role === USER_ROLES.MENTOR) {
    return [
      ...baseFields,
      "coursesPublished",
      "studentsEnrolled",
      "avgRating",
      "menteeCount",
    ];
  }

  // Admin sees everything
  if (viewer.role === USER_ROLES.ADMIN) {
    return [
      ...baseFields,
      "email",
      "createdAt",
      "totalEarnings",
      "coursesCompleted",
      "coursesCreated",
      "menteeCount",
      "payoutMethod",
      "accountSettings",
      "ipAddress",
      "loginHistory",
      "paymentMethods",
    ];
  }

  // Default: just public fields
  return baseFields;
}

/**
 * Filter object to only show visible fields
 */
export function filterProfileData(data, visibleFields) {
  const filtered = {};
  visibleFields.forEach((field) => {
    if (field in data) {
      filtered[field] = data[field];
    }
  });
  return filtered;
}

/**
 * Check if can edit user profile
 */
export function canEditProfile(editorId, targetId, editorRole) {
  // User can edit own profile
  if (editorId === targetId) {
    return true;
  }
  // Admin can edit any profile
  if (editorRole === USER_ROLES.ADMIN) {
    return true;
  }
  return false;
}

/**
 * Check if can view earnings/financial info
 */
export function canViewEarnings(viewerId, targetId, viewerRole) {
  // User can view own earnings
  if (viewerId === targetId) {
    return true;
  }
  // Admin and steward+ can view (for moderation)
  if ([USER_ROLES.ADMIN, USER_ROLES.STEWARD, USER_ROLES.ELDER].includes(viewerRole)) {
    return true;
  }
  return false;
}

/**
 * Check if can view payout/banking info (most sensitive)
 */
export function canViewPayoutInfo(viewerId, targetId, viewerRole) {
  // Only user themselves or admin
  if (viewerId === targetId) {
    return true;
  }
  if (viewerRole === USER_ROLES.ADMIN) {
    return true;
  }
  return false;
}

/**
 * Partnership-based permission checks
 */
export function canAccessFeature(partnershipLevel, feature) {
  const featureRequirements = {
    // Rooted features
    vote_discussions: PARTNERSHIP_LEVELS.ROOTED,
    apply_mentorship: PARTNERSHIP_LEVELS.ROOTED,
    create_posts: PARTNERSHIP_LEVELS.ROOTED,
    // Builder features
    vote_proposals: PARTNERSHIP_LEVELS.BUILDER,
    propose_minor_changes: PARTNERSHIP_LEVELS.BUILDER,
    // Steward features
    allocate_creator_fund: PARTNERSHIP_LEVELS.STEWARD,
    propose_major_changes: PARTNERSHIP_LEVELS.STEWARD,
    // Elder features
    board_advisory: PARTNERSHIP_LEVELS.ELDER,
  };

  const requiredLevel = featureRequirements[feature];
  if (!requiredLevel) return true; // Feature not restricted

  const levelHierarchy = [
    PARTNERSHIP_LEVELS.SEED,
    PARTNERSHIP_LEVELS.ROOTED,
    PARTNERSHIP_LEVELS.BUILDER,
    PARTNERSHIP_LEVELS.STEWARD,
    PARTNERSHIP_LEVELS.ELDER,
  ];

  const userIndex = levelHierarchy.indexOf(partnershipLevel);
  const requiredIndex = levelHierarchy.indexOf(requiredLevel);

  return userIndex >= requiredIndex;
}

/**
 * Determine discount based on partnership level
 */
export function getDiscountPercentage(partnershipLevel) {
  const discounts = {
    [PARTNERSHIP_LEVELS.SEED]: 0,
    [PARTNERSHIP_LEVELS.ROOTED]: 0.05,
    [PARTNERSHIP_LEVELS.BUILDER]: 0.1,
    [PARTNERSHIP_LEVELS.STEWARD]: 0.15,
    [PARTNERSHIP_LEVELS.ELDER]: 0.15,
  };
  return discounts[partnershipLevel] || 0;
}

/**
 * Check if content should be visible to user
 */
export function shouldShowContent(user, content) {
  // Content deleted or flagged
  if (content.deleted || content.flagged) {
    // Only user, moderators, admin can see
    return (
      user.userId === content.authorId ||
      [USER_ROLES.MODERATOR, USER_ROLES.STEWARD, USER_ROLES.ELDER, USER_ROLES.ADMIN].includes(user.role)
    );
  }

  // Content restricted to partnership level
  if (content.requiredPartnershipLevel) {
    return canAccessFeature(user.partnershipLevel, content.requiredPartnershipLevel);
  }

  // Public content
  return true;
}

/**
 * React component wrapper for permission-gated content
 */
export function PermissionGated({ children, requiredRole, requiredAction, user, fallback = null }) {
  let hasPermission = true;

  if (requiredRole) {
    hasPermission = hasRole(user.role, requiredRole);
  }

  if (requiredAction) {
    hasPermission = canPerformAction(user.role, requiredAction);
  }

  if (!hasPermission) {
    return fallback || (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-sm">
        <strong>Locked:</strong> You need higher partnership level to access this feature.
      </div>
    );
  }

  return children;
}

/**
 * Mask sensitive data
 */
export function maskSensitiveData(data, fields) {
  const masked = { ...data };
  fields.forEach((field) => {
    if (field in masked && typeof masked[field] === "string") {
      const value = masked[field];
      masked[field] = value.substring(0, 3) + "*".repeat(Math.max(0, value.length - 6)) + value.substring(value.length - 3);
    }
  });
  return masked;
}

/**
 * Audit log action
 */
export function logAuditAction(userId, action, resource, details) {
  // In real app, send to backend audit log
  console.log("[AUDIT]", {
    timestamp: new Date().toISOString(),
    userId,
    action,
    resource,
    details,
  });
}

/**
 * Rate limit check (client-side)
 */
export function checkRateLimit(action, maxPerMinute = 10) {
  const key = `ratelimit_${action}`;
  const now = Date.now();
  const timestamp = parseInt(localStorage.getItem(`${key}_time`) || "0");
  const count = parseInt(localStorage.getItem(`${key}_count`) || "0");

  // Reset if minute has passed
  if (now - timestamp > 60000) {
    localStorage.setItem(`${key}_time`, now.toString());
    localStorage.setItem(`${key}_count`, "1");
    return true;
  }

  // Check if limit exceeded
  if (count >= maxPerMinute) {
    return false;
  }

  // Increment counter
  localStorage.setItem(`${key}_count`, (count + 1).toString());
  return true;
}
