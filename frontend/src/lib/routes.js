/**
 * routes — canonical route registry.
 *
 * App.js is the single authority for what routes EXIST. This module is the
 * canonical registry for how code should REFERENCE them, so links can't drift
 * from reality:
 *
 *   - Use ROUTES.* constants / builders instead of hand-writing path strings
 *     (e.g. <Link to={ROUTES.profile(username)}> instead of `/u/${username}`).
 *   - isRegisteredRoute() validates any path at runtime and is used by
 *     scripts/route-integrity.js to fail CI on dead links.
 *
 * The route-integrity test cross-checks every entry here against the <Route>
 * definitions in src/App.js, so forgetting to register a route (or removing
 * one still being referenced) breaks the build, not production.
 */

// ── Static routes (canonical constants) ─────────────────────────────────────
export const ROUTES = {
  home: "/",
  landing: "/",
  login: "/login",
  register: "/register",
  forgotPassword: "/forgot-password",
  dashboard: "/dashboard",
  profile: "/profile",
  settings: "/settings",
  myPosition: "/my-position",
  siteGuide: "/site-guide",
  byok: "/byok",
  helper: "/helper",
  helperApp: "/app/helper",
  aiTutor: "/ai",
  council: "/council",
  orchestrator: "/orchestrator",
  modules: "/modules",
  labs: "/labs",
  compliance: "/compliance",
  credentials: "/credentials",
  certificates: "/certificates",
  portfolio: "/portfolio",
  palace: "/palace",
  elderCouncil: "/elder-council",
  leaderboard: "/leaderboard",
  moreHub: "/app/more",
  moreChat: "/more/chat",
  legalTools: "/more/litigation",
  classicTools: "/classic-tools",
  aawab: "/aawab",
  aawabChamber: "/aawab/chamber",
  businessOffice: "/business-office",
  studio: "/studio",
  socialPublish: "/social/publish",
  creatorCourses: "/creator/courses",
  creatorEarnings: "/creator/earnings",
  creatorPayouts: "/creator/payouts",
  creatorLounge: "/creator-lounge",
  ghostProducer: "/ghost-producer",
  band: "/band",
  playlistDashboard: "/playlist/dashboard",
  arcade: "/arcade",
  store: "/store",
  merch: "/merch",
  plans: "/plans",
  subscribe: "/subscribe",
  donate: "/donate",
  paymentHistory: "/payment/history",
  partnership: "/partnership",
  waiInstitute: "/wai-institute",
  moreHelpCenter: "/more-help-center",
  helpCenter: "/help-center",
  courses: "/courses",
  community: "/community",
  creators: "/creators",
  sponsor: "/sponsor",
  internships: "/internships",
  terms: "/terms",
  privacy: "/privacy",
  arena: "/arena",
  admin: "/admin",
  adminOverview: "/admin",
  adminTools: "/admin/tools",
  adminAnalytics: "/admin/analytics",
  adminAudit: "/admin/audit",
  adminPayments: "/admin/payments",
  adminBilling: "/admin/billing",
  adminPrices: "/admin/prices",
  adminHealth: "/admin/health",
  adminModeration: "/admin/moderation",
  revenue: "/revenue",
  auditor: "/auditor",
  moreAdmin: "/more/admin",
  moreOps: "/more/ops",
  adminAssistant: "/assistant",
  aiTeamBridge: "/admin/bridge",
  aawabAdmin: "/admin/aawab",
  officeControl: "/admin/office-control",
  execSystem: "/admin/system",
  siteControl: "/admin/control",
  execControl: "/admin/exec-control",
  director: "/admin/director",
  sageAudit: "/admin/sage-audit",
  staffMeetings: "/admin/staff-meetings",
  execReport: "/admin/exec-report",
  providerGateway: "/admin/providers",
  teamOps: "/team/ops",
  supervisor: "/supervisor",
  supervisorLogin: "/supervisor-login",
  creativePartner: "/creative-partner",
  jamil: "/jamil",
  projects: "/projects",
};

// ── Dynamic route builders (canonical) ──────────────────────────────────────
export const ROUTE_BUILDERS = {
  profileByUsername: (username) => `/u/${username}`,
  publicPortfolio: (slug) => `/p/${slug}`,
  module: (slug) => `/modules/${slug}`,
  lab: (slug) => `/labs/${slug}`,
  compliance: (slug) => `/compliance/${slug}`,
  persona: (slug) => `/personas/${slug}`,
  classic: (slug) => `/classic/${slug}`,
  creator: (slug) => `/creator/${slug}`,
  arcadeGame: (slug) => `/arcade/${slug}`,
  moreChatRoom: (roomId) => `/more/chat/${roomId}`,
  playlistSubmit: (slug) => `/playlist/${slug}/submit`,
};

// ── Validation helper ───────────────────────────────────────────────────────
const SEG = (p) => p.split("/").filter(Boolean);

/**
 * Does `pattern` (a route pattern, e.g. "/u/:username") match `candidate`
 * (an actual path, e.g. "/u/john")? Parameter segments match anything.
 */
export function pathMatches(pattern, candidate) {
  const ps = SEG(pattern);
  const cs = SEG(candidate);
  if (ps.length !== cs.length) return false;
  return ps.every((seg, i) => seg.startsWith(":") || seg === cs[i]);
}

/**
 * True when `path` resolves to a real registered route (not the catch-all 404).
 * Pass the App.js route list as `routePatterns`; defaults to ROUTES + builders.
 */
export function isRegisteredRoute(path, routePatterns) {
  const patterns =
    routePatterns ||
    Object.values(ROUTES).concat(Object.values(ROUTE_BUILDERS).map((fn) => fn(":p")));
  return patterns.some((p) => pathMatches(p, path));
}
