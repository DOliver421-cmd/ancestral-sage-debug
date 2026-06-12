import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import {
  LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut,
  FlaskConical, Target, ClipboardCheck, Briefcase, BadgeCheck, Brain,
  ShieldCheck, Shield, Building2, TrendingUp, ScrollText, Calendar,
  ShieldAlert, KeyRound, Crown, Compass, HelpCircle, Layers, HandHelping,
  Scale, Trophy, Network, ShoppingBag, Heart, Receipt, Video, DollarSign,
  UserCircle, WifiOff, Music, Mic, Palette, FileText,
  Gamepad2, Star, Radio, Globe, Swords, ChevronLeft, ChevronRight, Share2,
} from "lucide-react";
import NotificationBell from "./NotificationBell";
import { useEffect, useState } from "react";

// ── Section header ────────────────────────────────────────────────────────────
function NavSection({ label, children, collapsed }) {
  return (
    <div className="mt-4">
      {!collapsed && (
        <div className="px-3 mb-1 text-[10px] font-black uppercase tracking-widest text-white/30">{label}</div>
      )}
      {collapsed && <div className="mb-1 border-t border-white/10 mx-2" />}
      {children}
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
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("sidebar_collapsed") === "true"; } catch { return false; }
  });

  const role = user?.role || "student";
  const isAdmin  = role === "admin" || role === "executive_admin";
  const isExec   = role === "executive_admin";
  const isInstructor = role === "instructor" || isAdmin;

  const toggleCollapsed = () => {
    setCollapsed(c => {
      const next = !c;
      try { localStorage.setItem("sidebar_collapsed", String(next)); } catch {}
      return next;
    });
  };

  useEffect(() => {
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://ancestral-sage-debug-production.up.railway.app";
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 6000);
    fetch(`${BACKEND_URL}/api/version`, { signal: ctrl.signal })
      .then(r => { clearTimeout(timer); setBackendDown(!r.ok); })
      .catch(() => { clearTimeout(timer); setBackendDown(true); });
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, []);

  const nl = (to, label, icon, testid) => (
    <NavLink loc={loc} to={to} label={label} icon={icon} testid={testid} collapsed={collapsed} />
  );

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
            <Link to="/dashboard" className="flex items-center gap-3" data-testid="sidebar-brand">
              <img src={WAI_LOGO} alt="W.A.I." className="w-9 h-9 object-contain" style={{ mixBlendMode: "screen" }} />
              <div>
                <div className="overline text-signal">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
              </div>
            </Link>
          )}
          {collapsed && (
            <Link to="/dashboard" data-testid="sidebar-brand" title="Dashboard">
              <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "screen" }} />
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

          {/* ── CORE (everyone) ───────────────────────────────────────── */}
          <NavSection label="Home" collapsed={collapsed}>
            {nl("/dashboard",       "Dashboard",       LayoutDashboard, "nav-dashboard")}
            {nl("/profile",         "My Profile",      UserCircle,      "nav-profile")}
            {nl("/my-position",     "My Position",     Compass,         "nav-my-position")}
            {nl("/settings",        "Settings",        KeyRound,        "nav-settings")}
          </NavSection>

          <NavSection label="Learn" collapsed={collapsed}>
            {nl("/ai",              "AI Tutor",        Sparkles,        "nav-ai")}
            {nl("/council",         "Council (Sage)",  Layers,          "nav-council")}
            {nl("/modules",         "Curriculum",      BookOpen,        "nav-modules")}
            {nl("/labs",            "Workforce Labs",  FlaskConical,    "nav-labs")}
            {nl("/lab-simulations", "Lab Simulations", FlaskConical,    "nav-lab-sims")}
            {nl("/compliance",      "Compliance",      ShieldCheck,     "nav-compliance")}
            {nl("/adaptive",        "Learning Path",   Brain,           "nav-adaptive")}
            {nl("/competencies",    "Competencies",    Target,          "nav-competencies")}
          </NavSection>

          <NavSection label="Credentials" collapsed={collapsed}>
            {nl("/credentials",    "Credentials",      BadgeCheck,      "nav-credentials")}
            {nl("/certificates",   "Certificates",     Award,           "nav-certs")}
            {nl("/portfolio",      "Portfolio",        Briefcase,       "nav-portfolio")}
          </NavSection>

          <NavSection label="Community" collapsed={collapsed}>
            {nl("/palace",         "Members' Palace",  Crown,           "nav-palace")}
            {nl("/elder-council",  "Elder Council",    Layers,          "nav-elder-council")}
            {nl("/leaderboard",    "XP Leaderboard",   Trophy,          "nav-leaderboard")}
            {nl("/incidents",      "Report Incident",  ShieldAlert,     "nav-incidents")}
          </NavSection>

          <NavSection label="M.O.R.E." collapsed={collapsed}>
            {nl("/app/more",       "M.O.R.E. Hub",     HandHelping,     "nav-more")}
            {nl("/more/chat",      "Community Chat",   Radio,           "nav-more-chat")}
            {nl("/more/litigation","Legal Tools",       Scale,           "nav-litigation")}
            {nl("/app/helper",     "Personal Helper",  HelpCircle,      "nav-helper")}
          </NavSection>

          {/* ── CREATOR'S SANCTUARY (all roles — page handles tier locks) ── */}
          <NavSection label="Creator's Sanctuary" collapsed={collapsed}>
            {nl("/social/publish",       "Social Blast",      Share2,     "nav-social-publish")}
            {nl("/studio",               "Creator Studio",    Music,      "nav-creator-studio")}
            {nl("/creator/courses",      "Course Manager",    Video,      "nav-creator-courses")}
            {nl("/creator/earnings",     "My Earnings",       DollarSign, "nav-creator-earnings")}
            {nl("/creator/payouts",      "Payout Dashboard",  Receipt,    "nav-creator-payouts")}
            {nl("/creator/profile/edit", "Creator Profile",   UserCircle, "nav-creator-profile")}
            {nl("/creator-lounge",       "Creator Lounge",    Mic,        "nav-creator-lounge")}
            {nl("/ghost-producer",       "Ghost Producer",    Palette,    "nav-ghost-producer")}
            {nl("/band",                 "Band on a Page",    Music,      "nav-band")}
            {nl("/playlist/dashboard",   "Playlist Manager",  Radio,      "nav-playlist")}
            {nl("/arcade",               "Virtual Arcade",    Gamepad2,   "nav-arcade")}
          </NavSection>

          <NavSection label="Commerce" collapsed={collapsed}>
            {nl("/store",           "Store",            ShoppingBag,    "nav-store")}
            {nl("/plans",           "Plans & Pricing",  Star,           "nav-plans")}
            {nl("/subscribe",       "Membership",       HandHelping,    "nav-subscribe")}
            {nl("/donate",          "Donate",           Heart,          "nav-donate")}
            {nl("/payment/history", "Payment History",  Receipt,        "nav-payment-history")}
            {nl("/partnership",     "Partnerships",     Network,        "nav-partnership")}
          </NavSection>

          {/* ── INSTRUCTOR ────────────────────────────────────────────── */}
          {isInstructor && (
            <NavSection label="Instructor" collapsed={collapsed}>
              {nl("/instructor",      "My Roster",       Users,          "nav-instructor")}
              {nl("/instructor/labs", "Lab Approvals",   ClipboardCheck, "nav-lab-approvals")}
              {nl("/attendance",      "Attendance",      Calendar,       "nav-attendance")}
            </NavSection>
          )}

          {/* ── ADMIN ─────────────────────────────────────────────────── */}
          {isAdmin && (
            <NavSection label="Administration" collapsed={collapsed}>
              {nl("/admin",           "Admin Overview",  Settings,       "nav-admin")}
              {nl("/admin/users",     "Users",           Users,          "nav-admin-users")}
              {nl("/admin/accounts",  "Accounts",        Users,          "nav-accounts")}
              {nl("/admin/tools",     "Sites & Inventory", Building2,   "nav-admin-tools")}
              {nl("/admin/analytics", "Analytics",       TrendingUp,     "nav-analytics")}
              {nl("/admin/audit",     "Audit Log",       ScrollText,     "nav-audit")}
              {nl("/admin/payments",  "Payments",        Receipt,        "nav-admin-payments")}
              {nl("/admin/billing",   "Billing",         DollarSign,     "nav-billing")}
              {nl("/admin/prices",    "Prices",          Star,           "nav-prices")}
              {nl("/admin/health",    "System Health",   ShieldCheck,    "nav-health")}
              {nl("/admin/moderation","Moderation",      Shield,         "nav-moderation")}
              {nl("/revenue",         "Revenue",         DollarSign,     "nav-revenue")}
              {nl("/auditor",         "Auditor",         FileText,       "nav-auditor")}
              {nl("/more/admin",      "M.O.R.E. Admin",  HandHelping,    "nav-more-admin")}
              {nl("/more/ops",        "Dept. AI Ops",    Network,        "nav-more-ops")}
              {nl("/assistant",       "Admin Assistant", Sparkles,       "nav-assistant")}
            </NavSection>
          )}

          {/* ── EXECUTIVE ─────────────────────────────────────────────── */}
          {isExec && (
            <NavSection label="Executive" collapsed={collapsed}>
              {nl("/admin/system",       "Exec System",       Crown,          "nav-exec-system")}
              {nl("/admin/control",      "Site Control",      Shield,         "nav-control-panel")}
              {nl("/admin/exec-control", "Sovereign Command", Layers,         "nav-exec-control")}
              {nl("/admin/director",     "Director Dash",     Compass,        "nav-exec-director")}
              {nl("/admin/sage-audit",   "Sage Audit",        ScrollText,     "nav-sage-audit")}
              {nl("/admin/staff-meetings","Staff Meetings",   Users,          "nav-staff-meetings")}
              {nl("/admin/providers",    "Provider Gateway",  Network,        "nav-providers")}
              {nl("/team/ops",           "Team Ops",          Settings,       "nav-team-ops")}
              {nl("/supervisor",         "Supervisor Hub",    Radio,          "nav-supervisor")}
              {nl("/creative-partner",   "Creative Partner",  Palette,        "nav-creative-partner")}
              {nl("/arena",              "The Arena",         Swords,         "nav-arena")}
              {nl("/jamil",              "Jamil",             Sparkles,       "nav-jamil")}
              {nl("/projects",           "Projects",          ClipboardCheck, "nav-projects")}
            </NavSection>
          )}

        </nav>

        {/* WAI Institute card */}
        {!collapsed && (
          <div className="px-4 pb-2 shrink-0">
            <Link to="/wai-institute" data-testid="nav-wai-institute"
              className="flex flex-col gap-1 w-full rounded-xl p-4 text-white no-underline transition-all hover:opacity-90"
              style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E", boxShadow: "0 4px 16px rgba(27,67,50,0.40)" }}>
              <div className="flex items-center gap-2">
                <span style={{ fontSize: 16 }}>🏛️</span>
                <span style={{ fontSize: 14, fontWeight: 900, color: "#E8A51E" }}>WAI Institute</span>
              </div>
              <span style={{ fontSize: 11, opacity: 0.85, color: "#fff", paddingLeft: 26 }}>
                Administration · Classrooms · Credentials
              </span>
            </Link>
          </div>
        )}
        {collapsed && (
          <div className="px-1 pb-2 shrink-0 flex justify-center">
            <Link to="/wai-institute" data-testid="nav-wai-institute" title="WAI Institute"
              className="p-2 rounded-xl hover:opacity-90 transition-all"
              style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E" }}>
              <span style={{ fontSize: 18 }}>🏛️</span>
            </Link>
          </div>
        )}

        {/* User footer */}
        <div className={`py-4 border-t border-white/10 shrink-0 ${collapsed ? "px-1" : "px-4"}`}>
          {!collapsed && (
            <>
              <div className="text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
              <div className="font-heading text-white font-semibold mt-1 truncate flex items-center gap-2">
                {user?.full_name}
                {isExec && <span className="bg-signal text-ink text-[9px] font-black px-1.5 py-0.5" title="Executive Admin" data-testid="exec-badge">EXEC</span>}
                {role === "admin" && <span className="bg-copper text-white text-[9px] font-black px-1.5 py-0.5">ADMIN</span>}
              </div>
              <div className="text-xs text-white/50 capitalize">{role.replace("_", " ")}{user?.associate ? ` · ${user.associate}` : ""}</div>
            </>
          )}
          <button onClick={() => { logout(); nav("/"); }} data-testid="btn-logout"
            title="Log Out"
            className={`mt-3 w-full flex items-center justify-center gap-2 border border-white/20 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors ${collapsed ? "px-0" : ""}`}>
            <LogOut className="w-3.5 h-3.5" />
            {!collapsed && "Log Out"}
          </button>
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
