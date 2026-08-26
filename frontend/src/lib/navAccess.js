/**
 * navAccess.js — THE pure tier-first navigation decision, single-sourced.
 *
 * AppShell + accessGates call isNavItemVisible; scripts/nav-integrity.js tests
 * it against fixture gate maps. Deliberately dependency-free (no imports, no
 * framework) so the exact same function runs in the browser bundle and in a
 * plain `node` test.
 *
 * The `policy` argument is the gate-map entry for a page key, produced by the
 * backend from the Feature Registry + Feature Control Center overrides:
 *   { enabled, navigation_visible, allowed_roles, allowed_tiers, public_access }
 *
 * Decision order (mirrors the backend FCC enforcement semantics):
 *   1. exec-disabled page        → hidden
 *   2. FCC "Visible in Nav" off  → hidden
 *   3. allowed_roles (internal)  → role must be listed (rank-based backend)
 *   4. anonymous visitor         → only features explicitly marked public
 *   5. allowed_tiers (cumulative)→ user tier must cover the lowest allowed
 *                                  tier; admin/executive bypass (backend
 *                                  TIER_EXEMPT_ROLES)
 *
 * Navigation visibility is UX only — the backend stays authoritative.
 */

// Real product tier ladder (mirrors src/lib/tiers.js and backend TIER_RANK).
const TIER_RANK = {
  free: 0,
  member: 1,
  plus: 2,
  pro: 3,
  patron: 4,
  executive: 5,
};

function tierRank(tier) {
  return TIER_RANK[tier] ?? 0;
}

function isNavItemVisible(key, user, policy) {
  // Home/auth pages are never gated.
  if (key === "home" || key === "login" || key === "register" || key === "forgot-password") {
    return true;
  }
  if (policy === false) return false;
  if (!policy || typeof policy !== "object") return true;
  if (policy.enabled === false) return false;
  if (policy.navigation_visible === false) return false;

  // Anonymous visitors: only explicitly public features. The role list on a
  // public feature must not block anonymous visitors (public_access is the
  // anonymous gate); internal features simply never carry public_access.
  if (!user) return policy.public_access === true;

  // Role check — internal/proprietary features carry their allowed roles.
  const allowedRoles = policy.allowed_roles;
  if (Array.isArray(allowedRoles) && allowedRoles.length > 0) {
    if (!allowedRoles.includes(user.role)) return false;
  }

  // Tier check — cumulative tiers: user must cover the lowest allowed tier.
  const allowedTiers = policy.allowed_tiers;
  if (Array.isArray(allowedTiers) && allowedTiers.length > 0) {
    const role = user.role || "student";
    const staffBypass = role === "admin" || role === "executive_admin";
    if (!staffBypass) {
      const minRank = Math.min(...allowedTiers.map((t) => tierRank(t)));
      if (tierRank(user.feature_tier) < minRank) return false;
    }
  }
  return true;
}

// Plain CommonJS so `node scripts/nav-integrity.js` can require() this exact
// module; webpack/Babel resolve the named imports from module.exports.
module.exports = { TIER_RANK, tierRank, isNavItemVisible };
