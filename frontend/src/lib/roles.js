/**
 * roles.js — THE single authority for platform RBAC roles in the frontend.
 *
 * Mirrors backend/roles.py exactly. These are the REAL stored roles, weakest →
 * strongest:
 *
 *   rank  role
 *   1     student
 *   2     trial_pass
 *   3     instructor
 *   4     support_staff
 *   5     oversight
 *   6     admin
 *   7     executive_admin
 *
 * (public / unauthenticated = rank 0, never a stored role.)
 *
 * Pages that previously hardcoded a partial 4-role list (student, instructor,
 * admin, executive_admin) MUST import from here — a local copy drifts from the
 * backend and that is exactly the kind of mismatch that fails an audit.
 */

// Rank of every role. Keep in sync with backend/roles.py ROLE_RANK.
// public (0) is the unauthenticated baseline, never a stored user role.
export const ROLE_RANK = {
  public: 0,
  student: 1,
  trial_pass: 2,
  instructor: 3,
  support_staff: 4,
  oversight: 5,
  admin: 6,
  executive_admin: 7,
};

// Ordered weakest → strongest (the canonical RBAC ladder).
export const ROLES_ALL = [
  "student",
  "trial_pass",
  "instructor",
  "support_staff",
  "oversight",
  "admin",
  "executive_admin",
];

// Human labels for the UI.
export const ROLE_LABELS = {
  "": "All Roles",
  student: "Student",
  trial_pass: "Trial Pass",
  instructor: "Instructor",
  support_staff: "Support Staff",
  oversight: "Oversight",
  admin: "Admin",
  executive_admin: "Executive Admin",
};

// Tailwind badge colors per role (for user rows / chips).
export const ROLE_COLORS = {
  student: "bg-emerald-100 text-emerald-800",
  trial_pass: "bg-teal-100 text-teal-800",
  instructor: "bg-blue-100 text-blue-800",
  support_staff: "bg-violet-100 text-violet-800",
  oversight: "bg-indigo-100 text-indigo-800",
  admin: "bg-slate-100 text-slate-700",
  executive_admin: "bg-amber-100 text-amber-800",
};

/** True when roleA (as a string) is at least as privileged as roleB. */
export function roleAtLeast(role, minRole) {
  return (ROLE_RANK[role] ?? 0) >= (ROLE_RANK[minRole] ?? 0);
}

/** True when the actor may modify a user whose role is targetRole
 *  (admins cannot touch executive_admin; only an executive can). */
export function canModifyRole(actorRole, targetRole) {
  return (ROLE_RANK[actorRole] ?? 0) >= (ROLE_RANK[targetRole] ?? 0);
}
