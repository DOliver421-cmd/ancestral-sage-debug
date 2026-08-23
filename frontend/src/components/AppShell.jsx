import { Link, useLocation, useNavigate } from "react-router-dom";
import { API } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ROLE_RANK } from "../lib/roles";
import { tierRank, tierLabel } from "../lib/tiers";
import { WAI_LOGO, BRAND } from "../lib/brand";
import {
  LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut,
  FlaskConical, Target, ClipboardCheck, Briefcase, BadgeCheck, Brain,
  ShieldCheck, Shield, Building2, TrendingUp, ScrollText, Calendar,
  ShieldAlert, KeyRound, Crown, Compass, HelpCircle, Layers, HandHelping,
  Scale, Trophy, Network, ShoppingBag, Heart, Receipt, Video, DollarSign,
  UserCircle, WifiOff, Music, Mic, Palette, FileText,
  Gamepad2, Star, Radio, Globe, Swords, ChevronLeft, ChevronRight, Share2,
  Map, BrainCircuit, CreditCard, BarChart3, Wrench, Server, ExternalLink,
} from "lucide-react";
import { isWaiDoor, MORE_HOME } from "../lib/domain";
import NotificationBell from "./NotificationBell";
import { Search, HeartPulse, Landmark, Archive, Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { isPageEnabled, loadGates } from "../lib/accessGates";

// ── Section header (collapsible) ──────────────────────────────────────────────
function NavSection({ label, children, collapsed, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  if (collapsed) {
    return (
      <div className="mt-4">
        <div className="mb-1 border-t border-white/10 mx-2" />
        {children}
      </div>
    );
  }
  return (
    <div className="mt-4">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 mb-1 text-[10px] font-black uppercase tracking-widest text-white/30 hover:text-white/50 transition-colors"
      >
        <span>{label}</span>
        <svg className={`w-3 h-3 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && children}
    </div>
  );
}

// ── Collapsible sub-group within a section ───────────────────────────────────
function NavSubGroup({ label, children, collapsed, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  if (collapsed) return children;
  return (
    <div className="ml-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-white/25 hover:text-white/45 transition-colors"
      >
        <svg className={`w-2.5 h-2.5 transition-transform ${open ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" /></svg>
        <span>{label}</span>
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
          : "border-transparent text-white/65 hover:text-white hover:bg-white/5"
      }`}>
      <Icon className="w-4 h-4 shrink-0" />
      {!collapsed && label}
    </Link>
  );
}

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();
  const [backendDown, setBackendDown] = useState(false);
  const [gatesLoaded, setGatesLoaded] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("sidebar_collapsed") === "true"; } catch { return false; }
  });

  // Domain-aware sidebar: on the wai-institute.org door, education stays in-app
  // and every support/billing/creative item becomes an outbound link to MORE.
  const waiDoor = isWaiDoor();

  // Role hierarchy comes from lib/roles.js (mirrors backend/roles.py).
  const role = user?.role || "student";
  const rank = ROLE_RANK[role] ?? 0;
  const hasRank = (min) => rank >= (ROLE_RANK[min] ?? 0);
  const isAdmin  = hasRank("admin");
  const isExec   = hasRank("executive_admin");
  const isInstructor = hasRank("instructor");
  const isSupport = hasRank("support_staff");

  // Tier-first customer access (mirrors src/lib/tiers.js ladder). A signed-in
  // user's feature_tier drives which customer sections/items are visible; the
  // gate map (Feature Registry + FCC) supplies the per-item allowed_tiers.
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

  useEffect(() => {
    // Same resolution as lib/api.js — same-origin by default, so this stays in
    // sync with every other API call (no stale hardcoded host).
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 6000);
    fetch(`${API}/version`, { signal: ctrl.signal })
      .then(r => { clearTimeout(timer); setBackendDown(!r.ok); })
      .catch(() => { clearTimeout(timer); setBackendDown(true); });
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, []);

  // Exec-controlled page access: a disabled page disappears from the sidebar.
  // Until the gate map loads, hide ALL gated nav items to prevent flash-of-content
  // where restricted features briefly appear before role enforcement kicks in.
  const nl = (to, label, icon, testid) => {
    if (!gatesLoaded) return null;
    if (!isPageEnabled(to, user)) return null;
    return <NavLink loc={loc} to={to} label={label} icon={icon} testid={testid} collapsed={collapsed} />;
  };

  // Outbound link to the M.O.R.E. Help Center (used on the WAI door for
  // support/billing/creative items that live on morehelp.center).
  const out = (to, label, icon, testid) => {
    if (!isPageEnabled(to, user)) return null;
    return (
      <a key={to} href={MORE_HOME + to} target="_blank" rel="noopener noreferrer"
        data-testid={testid} title={collapsed ? label : undefined}
        className={`flex items-center gap-3 px-3 py-2 text-sm font-medium border-l-2 border-transparent text-white/65 hover:text-white hover:bg-white/5 transition-all rounded-r-md ${collapsed ? "justify-center px-0" : ""}`}>
        <Icon className="w-4 h-4 shrink-0" />
        {!collapsed && (
          <>
            <span className="flex-1">{label}</span>
            <ExternalLink className="w-3 h-3 opacity-50 shrink-0" />
          </>
        )}
      </a>
    );
  };

  useEffect(() => { loadGates().then(() => setGatesLoaded(true)); }, []);

  return (
    <div className="min-h-screen flex bg-bone">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className={`${collapsed ? "w-14" : "w-64"} shrink-0 bg-ink text-white flex flex-col overflow-y-auto transition-all duration-200`}
        data-testid="sidebar"
      >

        {/* Brand */}
        <div className={`py-5 border-b border-white/10 flex items-center shrink-0 ${collapsed ? "justify-center px-2 flex-col gap-2" : "px-4 justify-between"}`}>
          {!collapsed && (
            <Link to="/" className="flex items-center gap-3" data-testid="sidebar-brand">
              <img src={WAI_LOGO} alt="M.O.R.E." className="w-9 h-9 object-contain" />
              <div>
                <div className="overline text-signal">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
              </div>
            </Link>
          )}
          {collapsed && (
            <Link to="/" data-testid="sidebar-brand" title="Home">
              <img src={WAI_LOGO} alt="M.O.R.E." className="w-8 h-8 object-contain" />
            </Link>
          )}
          <div className={`flex items-center ${collapsed ? "flex-col gap-1" : "gap-1"}`}>
            {!collapsed && <NotificationBell />}
            <button
              onClick={toggleCollapsed}
              title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="p-1 rounded hover:bg-white/10 text-white/50 hover:text-white transition-colors"
              data-testid="sidebar-toggle"
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
          {collapsed && <NotificationBell />}
        </div>

        {/* Nav */}
        <nav className={`flex-1 py-4 ${collapsed ? "px-1" : "px-2"}`}>

          {/* Site search — opens the global command palette (Ctrl+K) */}
          <button
            onClick={() => window.dispatchEvent(new CustomEvent("open-site-search"))}
            data-testid="nav-search"
            title={collapsed ? "Search (Ctrl+K)" : undefined}
            className={`flex items-center gap-3 px-3 py-2 text-sm font-medium border-l-2 border-transparent text-white/65 hover:text-white hover:bg-white/5 rounded-r-md transition-all ${collapsed ? "justify-center px-0" : ""}`}
          >
            <Search className="w-4 h-4 shrink-0" />
            {!collapsed && <span className="flex-1 text-left">Search</span>}
            {!collapsed && <kbd className="text-[10px] font-black text-white/30 border border-white/15 rounded px-1.5 py-0.5">⌘K</kbd>}
          </button>

          {/* ── HOME (everyone) ───────────────────────────────────────── */}
          <NavSection label="Home" collapsed={collapsed}>
            {nl("/",                "Home / Landing",  Globe,            "nav-home")}
            {isAuthed && nl("/dashboard",       "Dashboard",       LayoutDashboard, "nav-dashboard")}
            {isAuthed && (waiDoor ? (
              <>
                {out("/profile",        "My Profile",      UserCircle,      "nav-profile")}
                {out("/settings",       "Settings",        KeyRound,        "nav-settings")}
              </>
            ) : (
              <>
                {nl("/profile",         "My Profile",      UserCircle,      "nav-profile")}
                {nl("/settings",        "Settings",        KeyRound,        "nav-settings")}
              </>
            ))}
          </NavSection>

          {/* PUBLIC — anonymous visitors only (no dashboard, no premium items) */}
          {!isAuthed && (
            <NavSection label="Explore" collapsed={collapsed} defaultOpen={true}>
              {nl("/courses",       "Courses",        BookOpen,        "nav-public-courses")}
              {nl("/creators",      "Creators",       Users,           "nav-public-creators")}
              {nl("/community",     "Community",      Radio,           "nav-public-community")}
              {nl("/store",         "Store",          ShoppingBag,     "nav-public-store")}
              {nl("/help-center",   "Help",           HelpCircle,      "nav-public-help")}
              {nl("/knowledge",      "Knowledge Finder", Search,        "nav-public-knowledge")}
            </NavSection>
          )}

          {/* YOUR ACCESS — tier status so signed-in users see the boundary */}
          {isAuthed && (
            <NavSection label="Your Access" collapsed={collapsed} defaultOpen={false}>
              <div className="px-3 pb-1 text-[10px] font-black uppercase tracking-widest text-white/40">
                {tierLabel(tier)} access{byokUnlocked ? " · BYOK unlocked" : ""}
              </div>
              {nl("/plans", "Plans & Upgrade", Star, "nav-plans-upgrade")}
            </NavSection>
          )}

          {/* ── NAM (AI Leadership — first-class, always accessible) ──── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="AI" collapsed={collapsed}>
            <NavSubGroup label="AI Assistants" collapsed={collapsed} defaultOpen={true}>
              {nl("/ai",              "AI Tutor",        Sparkles,        "nav-ai")}
              {nl("/helper",          "Personal Helper",  HelpCircle,      "nav-helper")}
              {nl("/assistant",       "Admin Assistant", Brain,           "nav-assistant")}
              {nl("/site-guide",      "Site Guide",       Map,             "nav-site-guide")}
            </NavSubGroup>
            <NavSubGroup label="Leadership" collapsed={collapsed}>
              {nl("/council",         "Council (Sage)",  ShieldCheck,     "nav-council")}
              {nl("/jamil",           "Jamil",            Compass,         "nav-jamil")}
              {nl("/byok",            "My AI (BYOK)",    BrainCircuit,    "nav-byok")}
            </NavSubGroup>
          </NavSection>
          )}

          {/* ── CREATE (Creator tools & content) ─────────────────────── */}
          {isAuthed && hasRank("student") && hasTier("member") && (
          <NavSection label="Create" collapsed={collapsed}>
            {waiDoor ? (
              <>
                {out("/studio",             "Creator Studio",     Music,    "nav-creator-studio")}
                {out("/creator/courses",    "Course Manager",     Video,    "nav-creator-courses")}
                {out("/ghost-producer",     "Ghost Producer",     Palette,  "nav-ghost-producer")}
                {out("/social/publish",     "Social Blast",       Share2,   "nav-social-publish")}
                {out("/creator-lounge",     "Creator Lounge",     Mic,      "nav-creator-lounge")}
                {out("/creator/earnings",   "My Earnings",        DollarSign,"nav-creator-earnings")}
                {out("/creator/payouts",    "Payout Dashboard",   Receipt,  "nav-creator-payouts")}
              </>
            ) : (
              <>
                {nl("/studio",             "Creator Studio",     Music,    "nav-creator-studio")}
                {nl("/creator/courses",    "Course Manager",     Video,    "nav-creator-courses")}
                {nl("/ghost-producer",     "Ghost Producer",     Palette,  "nav-ghost-producer")}
                {nl("/social/publish",     "Social Blast",       Share2,   "nav-social-publish")}
                {nl("/creator-lounge",     "Creator Lounge",     Mic,      "nav-creator-lounge")}
                {nl("/creator/earnings",   "My Earnings",        DollarSign,"nav-creator-earnings")}
                {nl("/creator/payouts",    "Payout Dashboard",   Receipt,  "nav-creator-payouts")}
              </>
            )}
          </NavSection>
          )}

          {/* ── LEARN (Curriculum & credentials) ─────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Learn" collapsed={collapsed}>
            <NavSubGroup label="Discover" collapsed={collapsed} defaultOpen={false}>
              {nl("/knowledge",      "Knowledge Finder", Search,        "nav-knowledge")}
            </NavSubGroup>
            <NavSubGroup label="Curriculum" collapsed={collapsed} defaultOpen={true}>
              {nl("/modules",         "Modules",         BookOpen,        "nav-modules")}
              {nl("/adaptive",        "Learning Path",   Brain,           "nav-adaptive")}
              {nl("/competencies",    "Competencies",    Target,          "nav-competencies")}
            </NavSubGroup>
            <NavSubGroup label="Labs & Practice" collapsed={collapsed}>
              {nl("/labs",            "Workforce Labs",  FlaskConical,    "nav-labs")}
              {nl("/lab-simulations", "Lab Simulations", FlaskConical,    "nav-lab-sims")}
            </NavSubGroup>
            <NavSubGroup label="Compliance" collapsed={collapsed}>
              {nl("/compliance",      "Compliance",      ShieldCheck,     "nav-compliance")}
            </NavSubGroup>
            <NavSubGroup label="Credentials" collapsed={collapsed}>
              {nl("/credentials",    "Credentials",      BadgeCheck,      "nav-credentials")}
              {nl("/certificates",   "Certificates",     Award,           "nav-certs")}
              {nl("/portfolio",      "Portfolio",        Briefcase,       "nav-portfolio")}
            </NavSubGroup>
          </NavSection>
          )}

          {/* ── COMMUNITY (Social & guilds) ──────────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Community" collapsed={collapsed}>
            {waiDoor ? (
              <>
                {out("/palace",         "Members' Palace",  Crown,           "nav-palace")}
                {out("/elder-council",  "Elder Council",    Layers,          "nav-elder-council")}
                {out("/leaderboard",    "XP Leaderboard",   Trophy,          "nav-leaderboard")}
                {out("/more/chat",      "Community Chat",   Radio,           "nav-more-chat")}
                {out("/more/litigation","Legal Tools",      Scale,           "nav-litigation")}
                {out("/incidents",      "Report Incident",  ShieldAlert,     "nav-incidents")}
                {out("/vonns-saga",     "Vonns Saga",       BookOpen,        "nav-vonns")}
                {out("/ascension-protocols", "Ascension Protocols", Compass, "nav-ascension")}
              </>
            ) : (
              <>
                {nl("/palace",          "Members' Palace",  Crown,           "nav-palace")}
                {nl("/leaderboard",     "XP Leaderboard",   Trophy,          "nav-leaderboard")}
                {nl("/more/chat",       "Community Chat",   Radio,           "nav-more-chat")}
                {nl("/more/litigation", "Legal Tools",      Scale,           "nav-litigation")}
                {nl("/incidents",       "Report Incident",  ShieldAlert,     "nav-incidents")}
                {nl("/vonns-saga",      "Vonns Saga",       BookOpen,        "nav-vonns")}
                {nl("/ascension-protocols", "Ascension Protocols", Compass, "nav-ascension")}
              </>
            )}
          </NavSection>
          )}

          {/* ── MARKETPLACE (Commerce & sales) ───────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Marketplace" collapsed={collapsed}>
            {waiDoor ? (
              <>
                {out("/store",           "Media Store",      Music,          "nav-media-store")}
                {out("/merch",           "Store",            ShoppingBag,    "nav-store")}
                {out("/plans",           "Plans & Pricing",  Star,           "nav-plans")}
                {out("/subscribe",       "Membership",       HandHelping,    "nav-subscribe")}
                {out("/donate",          "Donate",           Heart,          "nav-donate")}
                {out("/payment/history", "Payment History",  Receipt,        "nav-payment-history")}
                {out("/partnership",     "Partnerships",     Network,        "nav-partnership")}
              </>
            ) : (
              <>
                {nl("/store",           "Media Store",      Music,          "nav-media-store")}
                {nl("/plans",           "Plans & Pricing",  Star,           "nav-plans")}
                {nl("/subscribe",       "Membership",       HandHelping,    "nav-subscribe")}
                {nl("/donate",          "Donate",           Heart,          "nav-donate")}
                {nl("/payment/history", "Payment History",  Receipt,        "nav-payment-history")}
                {nl("/partnership",     "Partnerships",     Network,        "nav-partnership")}
              </>
            )}
          </NavSection>
          )}

          {/* ── SANCTUARY (Healing & reflection) ─────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Sanctuary" collapsed={collapsed}>
            {nl("/sanctuary",       "Sanctuary",       Heart,           "nav-sanctuary")}
            {nl("/knowledge-base",  "Knowledge Base",   BookOpen,        "nav-kb")}
          </NavSection>
          )}

          {/* ── MUSIC (Studio & catalog) ─────────────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Music" collapsed={collapsed}>
            {nl("/band",            "Band on a Page",   Music,           "nav-band")}
            {nl("/playlist/dashboard","Playlist Manager", Radio,          "nav-playlist")}
          </NavSection>
          )}

          {/* ── GAMES (Arcade & competition) ─────────────────────────── */}
          {isAuthed && hasRank("student") && (
          <NavSection label="Games" collapsed={collapsed}>
            {nl("/arcade",          "Virtual Arcade",   Gamepad2,        "nav-arcade")}
            {nl("/trash",           "M.O.R.E. Pantheon", Star,          "nav-trash")}
          </NavSection>
          )}

          {/* ── AGENT WELLNESS (oversight+) */}
          {hasRank("oversight") && (
          <NavSection label="Agent Wellness" collapsed={collapsed}>
            {nl("/aawab",          "Agent Registry",  HeartPulse,      "nav-aawab")}
            {nl("/aawab/chamber",  "Certification",   Award,           "nav-aawab-chamber")}
          </NavSection>
          )}          {/* ── DIRECTOR (Admin & governance — canonical /admin ecosystem) */}
          {isAdmin && (
            <NavSection label="Director" collapsed={collapsed} defaultOpen={false}>
              <NavSubGroup label="Overview" collapsed={collapsed} defaultOpen={true}>
                {nl("/admin",           "Admin Overview",  Settings,       "nav-admin")}
                {nl("/admin/iam",       "IAM Console",     ShieldCheck,    "nav-iam")}
                {nl("/admin/office",    "Business Office", Landmark,       "nav-exec-office")}
                {nl("/admin/health",    "System Health",   ShieldCheck,    "nav-health")}
              </NavSubGroup>
              <NavSubGroup label="Finance" collapsed={collapsed}>
                {nl("/admin/payments",  "Payments",        Receipt,        "nav-admin-payments")}
                {nl("/admin/billing",   "Billing",         CreditCard,     "nav-billing")}
                {nl("/admin/prices",    "Prices",          Star,           "nav-prices")}
                {nl("/revenue",         "Revenue",         BarChart3,      "nav-revenue")}
              </NavSubGroup>
              <NavSubGroup label="Operations" collapsed={collapsed}>
                {nl("/admin/analytics", "Analytics",       TrendingUp,     "nav-analytics")}
                {nl("/admin/audit",     "Audit Log",       ScrollText,     "nav-audit")}
                {nl("/admin/moderation","Moderation",      Shield,         "nav-moderation")}
                {nl("/admin/sage-audit","Sage Audit",      ScrollText,     "nav-sage-audit")}
              </NavSubGroup>
              <NavSubGroup label="Tools" collapsed={collapsed}>
                {nl("/admin/features", "Feature Control", Wrench, "nav-features")}
                {nl("/admin/tools",     "Sites & Inventory", Building2,    "nav-admin-tools")}
                {nl("/admin/bridge",    "AI Team Bridge",  Network,        "nav-bridge")}
                {nl("/admin/providers", "Provider Gateway", Network,       "nav-providers")}
                {nl("/admin/exec-report","Site Report",    ClipboardCheck,"nav-exec-report")}
              </NavSubGroup>
            </NavSection>
          )}

          {/* ── EXECUTIVE (exec-only — proprietary internal systems) ───── */}
          {isExec && (
            <NavSection label="Executive" collapsed={collapsed} defaultOpen={false}>
              {nl("/admin/command", "Command Center", Crown, "nav-command-center")}
              {nl("/arena",         "The Arena",      Swords, "nav-arena")}
            </NavSection>
          )}

          {/* ── INSTRUCTOR ────────────────────────────────────────────── */}
          {isInstructor && (
            <NavSection label="Instructor" collapsed={collapsed}>
              {nl("/instructor",      "My Roster",       Users,          "nav-instructor")}
              {nl("/instructor/labs", "Lab Approvals",   ClipboardCheck, "nav-lab-approvals")}
              {nl("/attendance",      "Attendance",      Calendar,       "nav-attendance")}
            </NavSection>
          )}

          {/* ── SITE SUPPORT (support_staff+) ──────────────────────── */}
          {isSupport && (
            <NavSection label="Site Support" collapsed={collapsed}>
              {nl("/admin/audit",       "Audit Log",       ScrollText,     "nav-support-audit")}
              {nl("/admin/moderation",  "Moderation",      Shield,         "nav-support-moderation")}
            </NavSection>
          )}

        </nav>

        {/* M.O.R.E. Institute card — on the WAI door the sidebar already IS the institute, so this links out to the MORE hub instead. */}
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
                <span style={{ fontSize: 11, opacity: 0.85, color: "#fff", paddingLeft: 26 }}>
                  Support · Billing · Community
                </span>
              </a>
            ) : (
            <Link to="/wai-institute" data-testid="nav-wai-institute"
              className="flex flex-col gap-1 w-full rounded-xl p-4 text-white no-underline transition-all hover:opacity-90"
              style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E", boxShadow: "0 4px 16px rgba(27,67,50,0.40)" }}>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 16 }}>🏛️</span>
                <span style={{ fontSize: 14, fontWeight: 900, color: "#E8A51E" }}>M.O.R.E. Institute</span>
              </div>
              <span style={{ fontSize: 11, opacity: 0.85, color: "#fff", paddingLeft: 26 }}>
                Administration · Classrooms · Credentials
              </span>
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
                {role === "admin" && <span className="bg-copper text-white text-[9px] font-black px-1.5 py-0.5">ADMIN</span>}
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
