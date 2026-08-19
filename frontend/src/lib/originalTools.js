/**
 * originalTools — catalog of the ORIGINAL standalone HTML applications.
 *
 * These are the full-featured originals the site shipped before the React
 * pages. They are preserved, never deleted, and served by the frontend build
 * from /tools/* and /originals/*. The React pages are front-ends; these remain
 * launchable as full-screen experiences from the Classic Tools hub (/classic-tools)
 * and the routes below.
 *
 * `path` must be a static asset inside frontend/public (baked into the build).
 *
 * Optional `status: "unavailable"` retires a tool honestly: the Classic Tools
 * hub and LegacyTool show an explicit availability banner instead of a Launch
 * button that would 404, and the route-integrity test (`npm run test:routes`)
 * skips the asset check for retired tools. No tool is unavailable today — the
 * state exists so retiring one never becomes a silent dead end.
 */

export const ORIGINAL_TOOLS = [
  {
    slug: "creators-sanctuary",
    title: "M.O.R.E. Creators",
    suite: "M.O.R.E. Creators",
    icon: "🎨",
    path: "/tools/creators-sanctuary.html",
    desc: "The original M.O.R.E. Creators hub — publishers, media strategists, oracle work, and electrical courses in one place.",
  },
  {
    slug: "djedi-oracle",
    title: "WA DJEDI — Kemetic AI Oracle",
    suite: "M.O.R.E. Creators",
    icon: "𓂀",
    path: "/tools/djedi-oracle.html",
    desc: "The Kemetic AI Oracle — divination and guidance in the ancestral tradition.",
  },
  {
    slug: "electrical-courses",
    title: "Electrical Courses",
    suite: "M.O.R.E. Creators",
    icon: "⚡",
    path: "/tools/electrical-courses.html",
    desc: "Circuit design, wiring, solar, and safety — the trade-skill course suite.",
  },
  {
    slug: "media-strategist",
    title: "Media Strategist",
    suite: "M.O.R.E. Creators",
    icon: "🎬",
    path: "/tools/media-strategist.html",
    desc: "The media strategy workbench — planning and publishing for creators.",
  },
  {
    slug: "publisher-prime",
    title: "Publisher — Book & Content Publishing",
    suite: "M.O.R.E. Creators",
    icon: "📚",
    path: "/tools/publisher-prime.html",
    desc: "Book and content publishing engine for the creator economy.",
  },
  {
    slug: "litigation-weapon",
    title: "Universal Litigation Weapon",
    suite: "Legal Tools",
    icon: "⚖️",
    path: "/tools/litigation-weapon.html",
    desc: "Know-your-rights tool — evidence checklists, damage calculators, and document templates for EEOC / MSPB / federal filings.",
  },
  {
    slug: "litigation-weapon-v1",
    title: "Case Weapon System v3.0 (original v1)",
    suite: "Legal Tools",
    icon: "🏛️",
    path: "/originals/litigation-weapon-v1.html",
    desc: "The original full case-weapon system — the complete self-advocacy law toolkit.",
  },
  {
    slug: "more-help-center",
    title: "M.O.R.E. Help Center — Original Edition",
    suite: "M.O.R.E. Help Center",
    icon: "🛟",
    path: "/originals/more-help-center.html",
    desc: "The original standalone help center — ambient audio, chat drawer, mic input, persona grid, and supervisor tools.",
  },
  {
    slug: "helper",
    title: "Helper — Authenticated Workspace (original)",
    suite: "M.O.R.E. Help Center",
    icon: "🧭",
    path: "/originals/helper.html",
    desc: "The original authenticated helper workspace with tools and chat.",
  },
  {
    slug: "helper-public",
    title: "Helper — Public Edition (original)",
    suite: "M.O.R.E. Help Center",
    icon: "🔍",
    path: "/originals/helper-public.html",
    desc: "The original public helper edition.",
  },
  {
    slug: "sovereign",
    title: "The Sovereign",
    suite: "Governance",
    icon: "👑",
    path: "/originals/sovereign.html",
    desc: "The original Sovereign interface — the puzzle/points engine and persona home.",
  },
  {
    slug: "supervisor",
    title: "The Supervisor",
    suite: "Governance",
    icon: "🛰️",
    path: "/originals/supervisor.html",
    desc: "The original Supervisor interface — AI governance, hybrid intelligence, and human-AI symbiosis.",
  },
  {
    slug: "supervisor-admin",
    title: "The Supervisor — WAI Institute (admin)",
    suite: "Governance",
    icon: "🏛️",
    path: "/originals/supervisor-admin.html",
    desc: "The original supervisor admin dashboard.",
  },
  {
    slug: "ancestral-sage",
    title: "Ancestral Sage — Resurrected",
    suite: "AI",
    icon: "🦉",
    path: "/ancestral-sage-resurrected.html",
    desc: "The original Ancestral Sage experience — the founding AI persona's home.",
  },
  {
    slug: "free-tier-hub",
    title: "Free Sandbox & Resource Hub",
    suite: "AI",
    icon: "🆓",
    path: "/originals/free-tier-hub.html",
    desc: "The original free-tier sandbox and resource hub.",
  },
];

export const ORIGINAL_BY_SLUG = Object.fromEntries(ORIGINAL_TOOLS.map((t) => [t.slug, t]));

export const ORIGINAL_SUITES = Object.entries(
  ORIGINAL_TOOLS.reduce((acc, t) => {
    (acc[t.suite] = acc[t.suite] || []).push(t);
    return acc;
  }, {})
);
