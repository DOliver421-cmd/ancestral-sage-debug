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
  Gamepad2, Star, Radio, Globe, Swords,
} from "lucide-react";
import NotificationBell from "./NotificationBell";
import { useEffect, useState } from "react";

// ── Section header ────────────────────────────────────────────────────────────
function NavSection({ label, children, collapsed }) {
  return (
    <div className="mt-4">
      {!collapsed && <div className="px-3 mb-1 text-[10px] font-black uppercase tracking-widest text-white/30">{label}</div>}
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
      className={`flex items-center gap-3 py-2 text-sm font-medium border-l-2 transition-all rounded-r-md ${
        collapsed ? "justify-center px-0" : "px-3"
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
  const [collapsed, setCollapsed] = useState(false);

  const role = user?.role || "student";
  const isAdmin  = role === "admin" || role === "executive_admin";
  const isExec   = role === "executive_admin";
  const isInstructor = role === "instructor" || isAdmin;

  useEffect(() => {
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://ancestral-sage-debug-production.up.railway.app";
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 6000);
    fetch(`${BACKEND_URL}/api/version`, { signal: ctrl.signal })
      .then(r => { clearTimeout(timer); setBackendDown(!r.ok); })
      .catch(() => { clearTimeout(timer); setBackendDown(true); });
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, []);

  return (
    <div className="h-screen flex bg-bone overflow-hidden">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        className="shrink-0 bg-ink text-white flex flex-col overflow-y-auto transition-all duration-200"
        style={{ width: collapsed ? 56 : 256 }}
        data-testid="sidebar"
      >

        {/* Brand */}
        <div className="px-3 py-5 border-b border-white/10 flex items-center justify-between shrink-0" style={{ minHeight: 72 }}>
          {!collapsed && (
            <Link to="/dashboard" className="flex items-center gap-3 min-w-0" data-testid="sidebar-brand">
              <img src={WAI_LOGO} alt="W.A.I." className="w-10 h-10 object-contain shrink-0" style={{ mixBlendMode: "screen" }} />
              <div className="min-w-0">
                <div className="overline text-signal">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm leading-tight truncate">{BRAND.name}</div>
              </div>
            </Link>
          )}
          {collapsed && (
            <Link to="/dashboard" className="flex items-center justify-center w-full" data-testid="sidebar-brand">
              <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "screen" }} />
            </Link>
          )}
          <button
            onClick={() => setCollapsed(c => !c)}
            className="shrink-0 ml-1 text-white/40 hover:text-white transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            style={{ background: "none", border: "none", cursor: "pointer", padding: 4, lineHeight: 1 }}
          >
            {collapsed ? "▶" : "◀"}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4">

          {/* ── CORE (everyone) ───────────────────────────────────────── */}
          <NavSection collapsed={collapsed} label="Home">
            <NavLink collapsed={collapsed} loc={loc} to="/dashboard"       label="Dashboard"       icon={LayoutDashboard} testid="nav-dashboard" />
            <NavLink collapsed={collapsed} loc={loc} to="/profile"         label="My Profile"      icon={UserCircle}      testid="nav-profile" />
            <NavLink collapsed={collapsed} loc={loc} to="/my-position"     label="My Position"     icon={Compass}         testid="nav-my-position" />
            <NavLink collapsed={collapsed} loc={loc} to="/settings"        label="Settings"        icon={KeyRound}        testid="nav-settings" />
          </NavSection>

          <NavSection collapsed={collapsed} label="Learn">
            <NavLink collapsed={collapsed} loc={loc} to="/ai"              label="AI Tutor"        icon={Sparkles}        testid="nav-ai" />
            <NavLink collapsed={collapsed} loc={loc} to="/council"         label="Council (Sage)"  icon={Layers}          testid="nav-council" />
            <NavLink collapsed={collapsed} loc={loc} to="/modules"         label="Curriculum"      icon={BookOpen}        testid="nav-modules" />
            <NavLink collapsed={collapsed} loc={loc} to="/labs"            label="Workforce Labs"  icon={FlaskConical}    testid="nav-labs" />
            <NavLink collapsed={collapsed} loc={loc} to="/lab-simulations" label="Lab Simulations" icon={FlaskConical}    testid="nav-lab-sims" />
            <NavLink collapsed={collapsed} loc={loc} to="/compliance"      label="Compliance"      icon={ShieldCheck}     testid="nav-compliance" />
            <NavLink collapsed={collapsed} loc={loc} to="/adaptive"        label="Learning Path"   icon={Brain}           testid="nav-adaptive" />
            <NavLink collapsed={collapsed} loc={loc} to="/competencies"    label="Competencies"    icon={Target}          testid="nav-competencies" />
          </NavSection>

          <NavSection collapsed={collapsed} label="Credentials">
            <NavLink collapsed={collapsed} loc={loc} to="/credentials"    label="Credentials"      icon={BadgeCheck}      testid="nav-credentials" />
            <NavLink collapsed={collapsed} loc={loc} to="/certificates"   label="Certificates"     icon={Award}           testid="nav-certs" />
            <NavLink collapsed={collapsed} loc={loc} to="/portfolio"      label="Portfolio"        icon={Briefcase}       testid="nav-portfolio" />
          </NavSection>

          <NavSection collapsed={collapsed} label="Community">
            <NavLink collapsed={collapsed} loc={loc} to="/palace"         label="Members' Palace"  icon={Crown}           testid="nav-palace" />
            <NavLink collapsed={collapsed} loc={loc} to="/elder-council"  label="Elder Council"    icon={Layers}          testid="nav-elder-council" />
            <NavLink collapsed={collapsed} loc={loc} to="/leaderboard"    label="XP Leaderboard"   icon={Trophy}          testid="nav-leaderboard" />
            <NavLink collapsed={collapsed} loc={loc} to="/incidents"      label="Report Incident"  icon={ShieldAlert}     testid="nav-incidents" />
          </NavSection>

          <NavSection collapsed={collapsed} label="M.O.R.E.">
            <NavLink collapsed={collapsed} loc={loc} to="/app/more"       label="M.O.R.E. Hub"     icon={HandHelping}     testid="nav-more" />
            <NavLink collapsed={collapsed} loc={loc} to="/more/chat"      label="Community Chat"   icon={Radio}           testid="nav-more-chat" />
            <NavLink collapsed={collapsed} loc={loc} to="/more/litigation" label="Legal Tools"     icon={Scale}           testid="nav-litigation" />
            <NavLink collapsed={collapsed} loc={loc} to="/app/helper"     label="Personal Helper"  icon={HelpCircle}      testid="nav-helper" />
          </NavSection>

          {/* ── CREATOR'S SANCTUARY (all roles — page handles tier locks) ── */}
          <NavSection collapsed={collapsed} label="Creator's Sanctuary">
            <NavLink collapsed={collapsed} loc={loc} to="/studio"               label="Creator Studio"    icon={Music}        testid="nav-creator-studio" />
            <NavLink collapsed={collapsed} loc={loc} to="/creator/courses"      label="Course Manager"    icon={Video}        testid="nav-creator-courses" />
            <NavLink collapsed={collapsed} loc={loc} to="/creator/earnings"     label="My Earnings"       icon={DollarSign}   testid="nav-creator-earnings" />
            <NavLink collapsed={collapsed} loc={loc} to="/creator/payouts"      label="Payout Dashboard"  icon={Receipt}      testid="nav-creator-payouts" />
            <NavLink collapsed={collapsed} loc={loc} to="/creator/profile/edit" label="Creator Profile"   icon={UserCircle}   testid="nav-creator-profile" />
            <NavLink collapsed={collapsed} loc={loc} to="/creator-lounge"       label="Creator Lounge"    icon={Mic}          testid="nav-creator-lounge" />
            <NavLink collapsed={collapsed} loc={loc} to="/ghost-producer"       label="Ghost Producer"    icon={Palette}      testid="nav-ghost-producer" />
            <NavLink collapsed={collapsed} loc={loc} to="/band"                 label="Band on a Page"    icon={Music}        testid="nav-band" />
            <NavLink collapsed={collapsed} loc={loc} to="/social/publish"       label="Social Publisher"  icon={Globe}        testid="nav-social-publish" />
            <NavLink collapsed={collapsed} loc={loc} to="/playlist/dashboard"   label="Playlist Manager"  icon={Radio}        testid="nav-playlist" />
            <NavLink collapsed={collapsed} loc={loc} to="/arcade"               label="Virtual Arcade"    icon={Gamepad2}     testid="nav-arcade" />
          </NavSection>

          <NavSection collapsed={collapsed} label="Commerce">
            <NavLink collapsed={collapsed} loc={loc} to="/store"           label="Store"            icon={ShoppingBag}    testid="nav-store" />
            <NavLink collapsed={collapsed} loc={loc} to="/plans"           label="Plans & Pricing"  icon={Star}           testid="nav-plans" />
            <NavLink collapsed={collapsed} loc={loc} to="/subscribe"       label="Membership"       icon={HandHelping}    testid="nav-subscribe" />
            <NavLink collapsed={collapsed} loc={loc} to="/donate"          label="Donate"           icon={Heart}          testid="nav-donate" />
            <NavLink collapsed={collapsed} loc={loc} to="/payment/history" label="Payment History"  icon={Receipt}        testid="nav-payment-history" />
            <NavLink collapsed={collapsed} loc={loc} to="/partnership"     label="Partnerships"     icon={Network}        testid="nav-partnership" />
          </NavSection>

          {/* ── INSTRUCTOR ────────────────────────────────────────────── */}
          {isInstructor && (
            <NavSection collapsed={collapsed} label="Instructor">
              <NavLink collapsed={collapsed} loc={loc} to="/instructor"      label="My Roster"       icon={Users}           testid="nav-instructor" />
              <NavLink collapsed={collapsed} loc={loc} to="/instructor/labs" label="Lab Approvals"   icon={ClipboardCheck}  testid="nav-lab-approvals" />
              <NavLink collapsed={collapsed} loc={loc} to="/attendance"      label="Attendance"      icon={Calendar}        testid="nav-attendance" />
            </NavSection>
          )}

          {/* ── ADMIN ─────────────────────────────────────────────────── */}
          {isAdmin && (
            <NavSection collapsed={collapsed} label="Administration">
              <NavLink collapsed={collapsed} loc={loc} to="/admin"           label="Admin Overview"  icon={Settings}        testid="nav-admin" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/users"     label="Users"           icon={Users}           testid="nav-admin-users" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/accounts"  label="Accounts"        icon={Users}           testid="nav-accounts" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/tools"     label="Sites & Inventory" icon={Building2}     testid="nav-admin-tools" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/analytics" label="Analytics"       icon={TrendingUp}      testid="nav-analytics" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/audit"     label="Audit Log"       icon={ScrollText}      testid="nav-audit" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/payments"  label="Payments"        icon={Receipt}         testid="nav-admin-payments" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/billing"   label="Billing"         icon={DollarSign}      testid="nav-billing" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/prices"    label="Prices"          icon={Star}            testid="nav-prices" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/health"    label="System Health"   icon={ShieldCheck}     testid="nav-health" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/moderation" label="Moderation"     icon={Shield}          testid="nav-moderation" />
              <NavLink collapsed={collapsed} loc={loc} to="/revenue"         label="Revenue"         icon={DollarSign}      testid="nav-revenue" />
              <NavLink collapsed={collapsed} loc={loc} to="/auditor"         label="Auditor"         icon={FileText}        testid="nav-auditor" />
              <NavLink collapsed={collapsed} loc={loc} to="/more/admin"      label="M.O.R.E. Admin"  icon={HandHelping}     testid="nav-more-admin" />
              <NavLink collapsed={collapsed} loc={loc} to="/more/ops"        label="Dept. AI Ops"    icon={Network}         testid="nav-more-ops" />
              <NavLink collapsed={collapsed} loc={loc} to="/assistant"       label="Admin Assistant" icon={Sparkles}        testid="nav-assistant" />
            </NavSection>
          )}

          {/* ── EXECUTIVE ─────────────────────────────────────────────── */}
          {isExec && (
            <NavSection collapsed={collapsed} label="Executive">
              <NavLink collapsed={collapsed} loc={loc} to="/admin/system"      label="Exec System"      icon={Crown}        testid="nav-exec-system" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/control"     label="Site Control"     icon={Shield}       testid="nav-control-panel" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/exec-control" label="Sovereign Command" icon={Layers}     testid="nav-exec-control" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/director"    label="Director Dash"    icon={Compass}      testid="nav-exec-director" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/sage-audit"  label="Sage Audit"       icon={ScrollText}   testid="nav-sage-audit" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/staff-meetings" label="Staff Meetings" icon={Users}       testid="nav-staff-meetings" />
              <NavLink collapsed={collapsed} loc={loc} to="/admin/providers"   label="Provider Gateway" icon={Network}      testid="nav-providers" />
              <NavLink collapsed={collapsed} loc={loc} to="/team/ops"          label="Team Ops"         icon={Settings}     testid="nav-team-ops" />
              <NavLink collapsed={collapsed} loc={loc} to="/supervisor"        label="Supervisor Hub"   icon={Radio}        testid="nav-supervisor" />
              <NavLink collapsed={collapsed} loc={loc} to="/creative-partner"  label="Creative Partner" icon={Palette}      testid="nav-creative-partner" />
              <NavLink collapsed={collapsed} loc={loc} to="/arena"             label="The Arena"        icon={Swords}          testid="nav-arena" />
              <NavLink collapsed={collapsed} loc={loc} to="/jamil"             label="Jamil"            icon={Sparkles}        testid="nav-jamil" />
              <NavLink collapsed={collapsed} loc={loc} to="/projects"          label="Projects"         icon={ClipboardCheck}  testid="nav-projects" />
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

        {/* User footer */}
        <div className="px-2 py-4 border-t border-white/10 shrink-0">
          {!collapsed && (
            <>
              <div className="px-2 text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
              <div className="px-2 font-heading text-white font-semibold mt-1 truncate flex items-center gap-2">
                {user?.full_name}
                {isExec && <span className="bg-signal text-ink text-[9px] font-black px-1.5 py-0.5" title="Executive Admin" data-testid="exec-badge">EXEC</span>}
                {role === "admin" && <span className="bg-copper text-white text-[9px] font-black px-1.5 py-0.5">ADMIN</span>}
              </div>
              <div className="px-2 text-xs text-white/50 capitalize">{role.replace("_", " ")}{user?.associate ? ` · ${user.associate}` : ""}</div>
            </>
          )}
          <button onClick={() => { logout(); nav("/"); }} data-testid="btn-logout"
            className={`mt-3 w-full flex items-center justify-center gap-2 border border-white/20 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors ${collapsed ? "px-0" : ""}`}
            title={collapsed ? "Log Out" : undefined}>
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
        <main className="flex-1 min-w-0 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
