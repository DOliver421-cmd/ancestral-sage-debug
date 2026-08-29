import { Link, useLocation, useNavigate } from "react-router-dom";
import { API } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ROLE_RANK } from "../lib/roles";
import { tierRank, tierLabel, TIER_FOR_FEATURE } from "../lib/tiers";
import { WAI_LOGO, BRAND } from "../lib/brand";
import {
  LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut,
  FlaskConical, Target, ClipboardCheck, Briefcase, BadgeCheck, Brain,
  ShieldCheck, Shield, Building2, TrendingUp, ScrollText, Calendar,
  ShieldAlert, KeyRound, Crown, Compass, HelpCircle, Layers, HandHelping,
  Scale, Trophy, Network, ShoppingBag, Heart, Receipt, Video, DollarSign,
  UserCircle, WifiOff, Music, Music4, Mic, Palette, FileText,
  Gamepad2, Star, Radio, Globe, ChevronLeft, ChevronRight, Share2,
  Map, BrainCircuit, CreditCard, BarChart3, Wrench, ExternalLink,
  Lock, Search, HeartPulse, Landmark, TicketPercent, Menu, Swords,
} from "lucide-react";
import { isWaiDoor, MORE_HOME } from "../lib/domain";
import NotificationBell from "./NotificationBell";
import { useEffect, useState } from "react";
import { isPageEnabled, loadGates } from "../lib/accessGates";

// ── Section header (collapsible) ──────────────────────────────────────────────
function NavSection({ label, children, collapsed, defaultOpen = true, badge }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-white/65 hover:text-white transition-colors"
      >
        <svg className={`w-2.5 h-2.5 transition-transform ${open ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" /></svg>
        <span>{label}</span>
        {badge && <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full font-black" style={{ background: "rgba(232,165,30,0.15)", color: "#E8A51E" }}>{badge}</span>}
      </button>
      {open && <div className="ml-1">{children}</div>}
    </div>
  );
}

// ── Single nav link ───────────────────────────────────────────────────────────
function NavLink({ to, label, icon: Icon, testid, loc, collapsed }) {
  const active = to === "/admin"
    ? loc.pathname === "/admin"
    : loc.pathname === to || loc.pathname.startsWith(to + "/");
  return (
    <Link key={to} to={to} data-testid={testid} title={collapsed ? label : undefined}
      onClick={() => window.scrollTo(0, 0)}
      className={`flex items-center gap-3 px-3 py-2 text-sm font-medium border-l-2 transition-all rounded-r-md ${
        collapsed ? "justify-center px-0" : ""
      } ${
        active
          ? "bg-white/8 border-signal text-signal"
          : "border-transparent text-white/75 hover:text-white hover:bg-white/5"
      }`}>
      <Icon className="w-4 h-4 shrink-0" />
      {!collapsed && label}
    </Link>
  );
}

// ── Locked-tier upgrade card ──────────────────────────────────────────────────
function TierCard({ tier, price, features, collapsed }) {
  if (collapsed) {
    return (
      <Link to="/plans"
        className="flex items-center justify-center px-0 py-2 mx-2 mb-1 rounded-md text-white/60 hover:text-white transition-colors"
        title={`${tier} — ${features}`}>
        <Lock className="w-4 h-4" />
      </Link>
    );
  }
  return (
    <Link to="/plans"
      className="block mx-3 mb-2 rounded-xl px-3 py-3 border border-dashed border-white/12 hover:border-white/25 hover:bg-white/[0.03] transition-all"
      data-testid={`nav-tier-locked-${tier.toLowerCase()}`}>
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: "#E8A51E" }}>
            {tier} Tier
          </div>
          <div className="text-[11px] text-white/65 mt-0.5">{features}</div>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-black uppercase" style={{ color: "#E8A51E" }}>
          {price}/mo <span className="text-xs">→</span>
        </div>
      </div>
    </Link>
  );
}

// ── Tier-first customer navigation data ───────────────────────────────────────
// Each section is a tier. Items render only when the user has reached that tier.
// Sections below the user's current tier are shown as locked upgrade cards.
// Sections above the user's tier are not rendered at all (not even as locked —
// only the immediately-next tier shows as an upgrade prompt).
const CUSTOMER_TIERS = [
  {
    tier: "free", label: "Free",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "nav-dashboard" },
      { to: "/studio", label: "Creator Studio", icon: Music, testid: "nav-creator-studio" },
      { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
      { to: "/helper", label: "Personal Helper", icon: HelpCircle, testid: "nav-helper" },
      { to: "/site-guide", label: "Site Guide", icon: Map, testid: "nav-site-guide" },
      { to: "/byok", label: "My AI Keys", icon: BrainCircuit, testid: "nav-byok" },
      { to: "/modules", label: "Modules", icon: BookOpen, testid: "nav-modules" },
      { to: "/competencies", label: "Competencies", icon: Target, testid: "nav-competencies" },
      { to: "/labs", label: "Workforce Labs", icon: FlaskConical, testid: "nav-labs" },
      { to: "/lab-simulations", label: "Lab Simulations", icon: FlaskConical, testid: "nav-lab-sims" },
      { to: "/compliance", label: "Compliance", icon: ShieldCheck, testid: "nav-compliance" },
      { to: "/credentials", label: "Credentials", icon: BadgeCheck, testid: "nav-credentials" },
      { to: "/certificates", label: "Certificates", icon: Award, testid: "nav-certs" },
      { to: "/portfolio", label: "Portfolio", icon: Briefcase, testid: "nav-portfolio" },
      { to: "/knowledge-base", label: "Knowledge Finder", icon: Search, testid: "nav-knowledge" },
      { to: "/palace", label: "Members' Palace", icon: Crown, testid: "nav-palace" },
      { to: "/elder-council", label: "Elder Council", icon: Layers, testid: "nav-elder-council" },
      { to: "/leaderboard", label: "XP Leaderboard", icon: Trophy, testid: "nav-leaderboard" },
      { to: "/more/chat", label: "Community Chat", icon: Radio, testid: "nav-more-chat" },
      { to: "/more/litigation", label: "Legal Tools", icon: Scale, testid: "nav-litigation" },
      { to: "/vonns-saga", label: "Vonn's Saga", icon: BookOpen, testid: "nav-vonns" },
      { to: "/ascension-protocols", label: "Ascension Protocols", icon: Compass, testid: "nav-ascension" },
      { to: "/playlist/dashboard", label: "Playlist Manager", icon: Radio, testid: "nav-playlist" },
      { to: "/arcade", label: "Virtual Arcade", icon: Gamepad2, testid: "nav-arcade" },
      { to: "/trash", label: "M.O.R.E. Pantheon", icon: Star, testid: "nav-trash" },
      { to: "/payment/history", label: "Payment History", icon: Receipt, testid: "nav-payments" },
    ],
  },
  {
    tier: "member", label: "Member", price: "$9",
    features: "Social Blast · My Projects · Creator Lounge",
    items: [
      { to: "/social/publish", label: "Social Blast", icon: Share2, testid: "nav-social-publish" },
      { to: "/creator-lounge", label: "Creator Lounge", icon: Mic, testid: "nav-creator-lounge" },
      { to: "/my-projects", label: "My Projects", icon: Briefcase, testid: "nav-my-projects" },
    ],
  },
  {
    tier: "plus", label: "Plus", price: "$15",
    features: "Studio · Courses · Ghost · Band · Sanctuary · Learning Path · Earnings",
    items: [
      { to: "/studio/music", label: "Music Studio", icon: Music4, testid: "nav-music-studio" },
      { to: "/creator/courses", label: "Course Manager", icon: Video, testid: "nav-creator-courses" },
      { to: "/ghost-producer", label: "Ghost Producer", icon: Palette, testid: "nav-ghost-producer" },
      { to: "/band", label: "Band on a Page", icon: Music, testid: "nav-band" },
      { to: "/adaptive", label: "Learning Path", icon: Brain, testid: "nav-adaptive" },
      { to: "/sanctuary", label: "Sanctuary", icon: ShieldCheck, testid: "nav-sanctuary" },
      { to: "/creator/earnings", label: "My Earnings", icon: DollarSign, testid: "nav-creator-earnings" },
      { to: "/creator/payouts", label: "Payout Dashboard", icon: Receipt, testid: "nav-creator-payouts" },
    ],
  },
];

// ── Staff-only navigation data ────────────────────────────────────────────────
// Each section requires a minimum role rank. Customer roles never see staff nav.
const STAFF_SECTIONS = [
  {
    minRole: "instructor", label: "Instructor",
    items: [
      { to: "/instructor", label: "My Roster", icon: Users, testid: "nav-instructor" },
      { to: "/instructor/labs", label: "Lab Approvals", icon: ClipboardCheck, testid: "nav-lab-approvals" },
      { to: "/attendance", label: "Attendance", icon: Calendar, testid: "nav-attendance" },
    ],
  },
  {
    minRole: "support_staff", label: "Site Support",
    items: [
      { to: "/admin/audit", label: "Audit Log", icon: ScrollText, testid: "nav-support-audit" },
      { to: "/admin/moderation", label: "Moderation", icon: Shield, testid: "nav-support-moderation" },
      { to: "/aawab", label: "Agent Wellness", icon: HeartPulse, testid: "nav-aawab" },
    ],
  },
  {
    minRole: "admin", label: "Director",
    items: [
      { to: "/admin", label: "Admin Overview", icon: Settings, testid: "nav-admin" },
      { to: "/admin/iam", label: "IAM Console", icon: ShieldCheck, testid: "nav-iam" },
      { to: "/business-office", label: "AI Business Office", icon: Landmark, testid: "nav-business-office" },
      { to: "/studio", label: "Creator Studio", icon: Music, testid: "nav-admin-creator-studio" },
      { to: "/nam", label: "Hybrid NAM", icon: BrainCircuit, testid: "nav-hybrid-nam" },
      { to: "/admin/health", label: "System Health", icon: ShieldCheck, testid: "nav-health" },
      { to: "/admin/payments", label: "Payments", icon: Receipt, testid: "nav-admin-payments" },
      { to: "/admin/billing", label: "Billing", icon: CreditCard, testid: "nav-billing" },
      { to: "/admin/prices", label: "Prices", icon: Star, testid: "nav-prices" },
      { to: "/admin/promo-codes", label: "Promo Codes", icon: TicketPercent, testid: "nav-promo-codes" },
      { to: "/revenue", label: "Revenue", icon: BarChart3, testid: "nav-revenue" },
      { to: "/admin/analytics", label: "Analytics", icon: TrendingUp, testid: "nav-analytics" },
      { to: "/admin/audit", label: "Audit Log", icon: ScrollText, testid: "nav-audit" },
      { to: "/admin/moderation", label: "Moderation", icon: Shield, testid: "nav-moderation" },
      { to: "/admin/sage-audit", label: "Sage Audit", icon: ScrollText, testid: "nav-sage-audit" },
      { to: "/admin/features", label: "Feature Control", icon: Wrench, testid: "nav-features" },
      { to: "/admin/bridge", label: "AI Team Bridge", icon: Network, testid: "nav-bridge" },
      { to: "/admin/providers", label: "Provider Gateway", icon: Network, testid: "nav-providers" },
      { to: "/admin/exec-report", label: "Site Report", icon: ClipboardCheck, testid: "nav-exec-report" },
    ],
  },
  {
    minRole: "executive_admin", label: "Executive",
    items: [
      { to: "/executive-suite", label: "Executive Suite", icon: Crown, testid: "nav-executive-suite" },
      { to: "/admin/command", label: "Command Center", icon: Crown, testid: "nav-command-center" },
      { to: "/arena", label: "The Arena", icon: Swords, testid: "nav-arena" },
    ],
  },
];

// ── AppShell ──────────────────────────────────────────────────────────────────
export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();
  const [backendDown, setBackendDown] = useState(false);
  const [gatesLoaded, setGatesLoaded] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("sidebar_collapsed") === "true"; } catch { return false; }
  });
  // Mobile: the sidebar is an off-canvas drawer below the lg breakpoint.
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close the drawer whenever the user navigates (each NavLink already scrolls to top).
  useEffect(() => { setMobileOpen(false); }, [loc.pathname]);

  const waiDoor = isWaiDoor();

  const role = user?.role || "student";
  const rank = ROLE_RANK[role] ?? 0;
  const hasRank = (min) => rank >= (ROLE_RANK[min] ?? 0);
  const isAdmin  = hasRank("admin");
  const isExec   = hasRank("executive_admin");
  const isStaff  = rank >= (ROLE_RANK["instructor"] ?? 0);

  const isAuthed = !!user;
  const tier = user?.feature_tier || "free";
  const hasTier = (min) => tierRank(tier) >= tierRank(min);
  const byokUnlocked = !!user?.byok_enabled;

  const toggleCollapsed = () => {
    setCollapsed(c => {
      const next = !c;
      try { localStorage.setItem("sidebar_collapsed", String(next)); } catch {}
      return next;
    });
  };

  // Load the exec page-access gate map once. Without this, gatesLoaded stays
  // false forever and every nav item renders null — section headers expand to
  // empty lists ("dropdowns that dropdown nothing") and features look missing.
  useEffect(() => {
    loadGates().finally(() => setGatesLoaded(true));
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 6000);
    fetch(`${API}/version`, { signal: ctrl.signal })
      .then(r => { clearTimeout(timer); setBackendDown(!r.ok); })
      .catch(() => { clearTimeout(timer); setBackendDown(true); });
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, []);

  const nl = (to, label, icon, testid) => {
    if (!gatesLoaded) return null;
    if (!isPageEnabled(to, user)) return null;
    return <NavLink loc={loc} to={to} label={label} icon={icon} testid={testid} collapsed={collapsed} />;
  };

  const out = (to, label, icon, testid) => {
    if (!isPageEnabled(to, user)) return null;
    return (
      <a href={`${MORE_HOME}${to}`} target="_blank" rel="noopener noreferrer" data-testid={testid}
        title={collapsed ? label : undefined}
        className={`flex items-center gap-3 px-3 py-2 text-sm font-medium border-l-2 transition-all rounded-r-md ${
          collapsed ? "justify-center px-0" : ""
        } border-transparent text-white/75 hover:text-white hover:bg-white/5`}>
        <icon className="w-4 h-4 shrink-0" />
        {!collapsed && label}
        {!collapsed && <ExternalLink className="w-3 h-3 ml-auto opacity-40" />}
      </a>
    );
  };

  const makeNav = waiDoor ? out : nl;

  return (
    <div className="flex min-h-screen bg-ink">
      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      {/* Mobile backdrop — closes the drawer when tapping outside it. */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setMobileOpen(false)} data-testid="sidebar-backdrop" />
      )}
      <aside
        data-testid="app-shell-sidebar"
        className={`fixed lg:static inset-y-0 left-0 z-50 shrink-0 flex flex-col border-r border-white/10 bg-surface overflow-y-auto transition-transform lg:transition-none shadow-2xl lg:shadow-none w-[240px] ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 ${collapsed ? "lg:w-[54px]" : "lg:w-[240px]"}`}
      >
        {/* Header */}
        <div className={`shrink-0 flex items-center gap-2 py-4 border-b border-white/10 ${collapsed ? "justify-center px-1" : "px-4"}`}>
          <img src={WAI_LOGO} alt={BRAND.short} className="w-9 h-9 object-contain" />
          {!collapsed && (
            <div className="min-w-0">
              <div className="text-[10px] font-black uppercase tracking-[0.18em] leading-none" style={{ color: "#E8A51E" }}>{BRAND.short}</div>
              <div className="text-[11px] font-bold leading-tight truncate text-white/80">{BRAND.name}</div>
            </div>
          )}
          <button onClick={toggleCollapsed} data-testid="sidebar-toggle"
            className={`ml-auto hidden lg:flex p-1 rounded text-white/30 hover:text-white/70 transition-colors ${collapsed ? "hidden" : ""}`}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
            <ChevronLeft className="w-4 h-4" />
          </button>
          {collapsed && (
            <button onClick={toggleCollapsed} className="mt-2 hidden lg:flex p-1 rounded text-white/30 hover:text-white/70 transition-colors">
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* M.O.R.E. Institute card */}
        {!collapsed && (
          <div className="px-4 pb-2 shrink-0">
            {waiDoor ? (
              <a href={MORE_HOME} target="_blank" rel="noopener noreferrer" data-testid="nav-wai-institute"
                className="flex flex-col gap-1 w-full rounded-xl p-4 text-white no-underline transition-all hover:opacity-90"
                style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E", boxShadow: "0 4px 16px rgba(27,67,50,0.40)" }}>
                <div className="flex items-center gap-2">
                  <span style={{ fontSize: 16 }}>🏛️</span>
                  <span style={{ fontSize: 14, fontWeight: 900, color: "#E8A51E" }}>M.O.R.E. Hub</span>
                </div>
                <span style={{ fontSize: 11, opacity: 0.85, color: "#fff", paddingLeft: 26 }}>Support · Billing · Community</span>
              </a>
            ) : (
            <Link to="/wai-institute" data-testid="nav-wai-institute"
              className="flex flex-col gap-1 w-full rounded-xl p-4 text-white no-underline transition-all hover:opacity-90"
              style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E", boxShadow: "0 4px 16px rgba(27,67,50,0.40)" }}>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 16 }}>🏛️</span>
                <span style={{ fontSize: 14, fontWeight: 900, color: "#E8A51E" }}>M.O.R.E. Institute</span>
              </div>
              <span style={{ fontSize: 11, opacity: 0.85, color: "#fff", paddingLeft: 26 }}>Administration · Classrooms · Credentials</span>
            </Link>
            )}
          </div>
        )}
        {collapsed && (
          <div className="px-1 pb-2 shrink-0 flex justify-center">
            {waiDoor ? (
              <a href={MORE_HOME} target="_blank" rel="noopener noreferrer" data-testid="nav-wai-institute" title="M.O.R.E. Help Center"
                className="p-2 rounded-xl hover:opacity-90 transition-all"
                style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E" }}>
                <span style={{ fontSize: 18 }}>🏛️</span>
              </a>
            ) : (
              <Link to="/wai-institute" data-testid="nav-wai-institute" title="M.O.R.E. Help Center"
                className="p-2 rounded-xl hover:opacity-90 transition-all"
                style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E" }}>
                <span style={{ fontSize: 18 }}>🏛️</span>
              </Link>
            )}
          </div>
        )}

        {/* ── Navigation ─────────────────────────────────────────────────── */}
        <nav className="flex-1 py-3 px-1 overflow-y-auto">

          {/* ─────────── NOT AUTHENTICATED ────────────── */}
          {!isAuthed && (
            <>
              <NavSection label="Explore" collapsed={collapsed} defaultOpen={true}>
                {nl("/", "Home", Globe, "nav-home")}
                {nl("/courses", "Courses", BookOpen, "nav-public-courses")}
                {nl("/creators", "Creators", Users, "nav-public-creators")}
                {nl("/community", "Community", Radio, "nav-public-community")}
                {nl("/store", "Store", ShoppingBag, "nav-public-store")}
                {nl("/premium", "WAI Institute Premium Services", Crown, "nav-public-premium")}
                {nl("/vonns-saga", "Vonn's Saga", BookOpen, "nav-public-vonns")}
                {nl("/knowledge", "Knowledge Finder", Search, "nav-public-knowledge")}
                {nl("/personas", "AI Team", BrainCircuit, "nav-public-personas")}
              </NavSection>
              <NavSection label="Access" collapsed={collapsed} defaultOpen={false}>
                {nl("/plans", "Plans & Upgrade", Star, "nav-plans-upgrade")}
              </NavSection>
            </>
          )}

          {/* ─────────── AUTHENTICATED: TIER-FIRST CUSTOMER NAV ──────────── */}
          {isAuthed && !isStaff && (
            <>
              {/* Home */}
              <NavSection label="Home" collapsed={collapsed} defaultOpen={true}>
                {nl("/", "Home / Landing", Globe, "nav-home")}
                {nl("/dashboard", "Dashboard", LayoutDashboard, "nav-dashboard")}
                {isAuthed && !collapsed && (
                  <div className="flex items-center gap-2 px-3 py-2">
                    <UserCircle className="w-4 h-4 text-white/45 shrink-0" />
                    <span className="text-sm text-white/65 truncate">{user?.full_name}</span>
                  </div>
                )}
                {nl("/profile", "My Profile", UserCircle, "nav-profile")}
                {nl("/settings", "Settings", KeyRound, "nav-settings")}
                {nl("/personas", "AI Team", BrainCircuit, "nav-personas")}
                {nl("/premium", "WAI Institute Premium Services", Crown, "nav-premium-customer")}
              </NavSection>

              {/* Tier sections: expanded for current tier, locked card for next, hidden above */}
              {CUSTOMER_TIERS.map((section, idx) => {
                const sectionRank = tierRank(section.tier);
                const userRank = tierRank(tier);
                const isCurrentOrBelow = userRank >= sectionRank;
                const isNextLocked = userRank < sectionRank && (idx === 0 || userRank >= tierRank(CUSTOMER_TIERS[idx - 1].tier));
                if (!isCurrentOrBelow && !isNextLocked) return null;
                if (isCurrentOrBelow) {
                  return (
                    <NavSection
                      key={section.tier}
                      label={section.label}
                      collapsed={collapsed}
                      defaultOpen={true}
                      badge={section.tier === tier ? "You" : null}
                    >
                      {section.items.map((item) => nl(item.to, item.label, item.icon, item.testid))}
                    </NavSection>
                  );
                }
                return <TierCard key={section.tier} tier={section.label} price={section.price} features={section.features} collapsed={collapsed} />;
              })}

              {/* Upgrade prompt (when there IS a next locked tier) */}
              {!collapsed && !hasTier("patron") && (
                <div className="mt-2 mx-3 px-3 py-2 rounded-lg" style={{ background: "rgba(232,165,30,0.06)", border: "1px solid rgba(232,165,30,0.15)" }}>
                  <Link to="/plans" className="text-[11px] font-bold uppercase tracking-widest hover:opacity-80 transition-opacity" style={{ color: "#E8A51E" }}>
                    Upgrade your access →
                  </Link>
                </div>
              )}


            </>
          )}

          {/* ─────────── AUTHENTICATED STAFF ──────────────────────────────── */}
          {isAuthed && isStaff && (
            <>
              {/* Customer quick-access: dashboard + profile */}
              <NavSection label="Account" collapsed={collapsed} defaultOpen={true}>
                {nl("/", "Home", Globe, "nav-home")}
                {nl("/dashboard", "Dashboard", LayoutDashboard, "nav-dashboard")}
                {nl("/profile", "My Profile", UserCircle, "nav-profile")}
                {nl("/settings", "Settings", KeyRound, "nav-settings")}
                {nl("/personas", "AI Team", BrainCircuit, "nav-personas-staff")}
                {nl("/vonns-saga", "Vonn's Saga", BookOpen, "nav-vonns-staff")}
                {nl("/premium", "WAI Institute Premium Services", Crown, "nav-premium-staff")}
              </NavSection>

              {/* Staff nav sections by role */}
              {STAFF_SECTIONS.map((section) => {
                if (rank < (ROLE_RANK[section.minRole] ?? 0)) return null;
                return (
                  <NavSection key={section.minRole} label={section.label} collapsed={collapsed} defaultOpen={false}>
                    {section.items.map((item) => {
                      // For items that appear in multiple staff sections (audit, moderation),
                      // deduplicate by path
                      return nl(item.to, item.label, item.icon, item.testid);
                    })}
                  </NavSection>
                );
              })}
            </>
          )}
        </nav>

        {/* User footer */}
        <div className={`py-4 border-t border-white/10 shrink-0 ${collapsed ? "px-1" : "px-4"}`}>
          {!isAuthed && !collapsed && (
            <>
              <div className="text-xs text-white/50 uppercase tracking-widest">Visitor</div>
              <div className="flex flex-col gap-2 mt-3">
                <Link to="/login" data-testid="nav-sign-in"
                  className="w-full text-center border border-white/25 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors">
                  Sign In
                </Link>
                <Link to="/register" data-testid="nav-register"
                  className="w-full text-center bg-signal text-ink py-2 text-xs uppercase tracking-widest font-bold hover:opacity-90 transition-opacity">
                  Create Account
                </Link>
              </div>
            </>
          )}
          {isAuthed && !collapsed && (
            <>
              <div className="text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
              <div className="font-heading text-white font-semibold mt-1 truncate flex items-center gap-2">
                {user?.full_name}
                {isExec && <span className="bg-signal text-ink text-[9px] font-black px-1.5 py-0.5" title="Executive Admin" data-testid="exec-badge">EXEC</span>}
                {isAdmin && <span className="bg-copper text-white text-[9px] font-black px-1.5 py-0.5">ADMIN</span>}
                {role === "support_staff" && <span style={{ background: "#E8A51E", color: "#0a0a0a" }} className="text-[9px] font-black px-1.5 py-0.5" title="Site Support">SUPPORT</span>}
                {role === "trial_pass" && <span style={{ background: "#E8A51E", color: "#0a0a0a" }} className="text-[9px] font-black px-1.5 py-0.5" title="Priority Member">PRIORITY</span>}
              </div>
              <div className="text-xs text-white/50 capitalize">{role.replace("_", " ")}{user?.associate ? ` · ${user.associate}` : ""}</div>
            </>
          )}
          {isAuthed && (
            <button onClick={() => { logout(); nav("/"); }} data-testid="btn-logout"
              title="Log Out"
              className={`mt-3 w-full flex items-center justify-center gap-2 border border-white/20 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors ${collapsed ? "px-0" : ""}`}>
              <LogOut className="w-3.5 h-3.5" />
              {!collapsed && "Log Out"}
            </button>
          )}
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Mobile top bar — hamburger + brand (hidden on desktop where the
            sidebar is always visible). */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-surface shrink-0">
          <button onClick={() => setMobileOpen(true)} data-testid="mobile-menu-button"
            className="p-2 -ml-1 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Open menu">
            <Menu className="w-5 h-5" />
          </button>
          <Link to="/" className="flex items-center gap-2 min-w-0">
            <img src={WAI_LOGO} alt={BRAND.short} className="w-7 h-7 object-contain shrink-0" />
            <div className="min-w-0 leading-none">
              <div className="text-[10px] font-black uppercase tracking-[0.18em]" style={{ color: "#E8A51E" }}>{BRAND.short}</div>
              <div className="text-[11px] font-bold truncate text-white/80">{BRAND.name}</div>
            </div>
          </Link>
          {isAuthed && (
            <Link to="/profile" className="ml-auto p-1.5 rounded-full text-white/60 hover:text-white" data-testid="mobile-profile" aria-label="My profile">
              <UserCircle className="w-6 h-6" />
            </Link>
          )}
        </div>
        {backendDown && (
          <div className="flex items-center gap-3 px-6 py-3 bg-destructive/10 border-b border-destructive/20" data-testid="backend-offline-banner">
            <WifiOff className="w-4 h-4 text-destructive shrink-0" />
            <span className="text-sm font-semibold text-destructive">Backend offline — data cannot load. Check Railway service status.</span>
          </div>
        )}
        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
