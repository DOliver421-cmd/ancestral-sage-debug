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
function NavSection({ label, children }) {
  return (
    <div className="mt-4">
      <div className="px-3 mb-1 text-[10px] font-black uppercase tracking-widest text-white/30">{label}</div>
      {children}
    </div>
  );
}

// ── Single nav link ───────────────────────────────────────────────────────────
function NavLink({ to, label, icon: Icon, testid, loc }) {
  const active = to === "/admin"
    ? loc.pathname === "/admin"
    : loc.pathname === to || loc.pathname.startsWith(to + "/");
  return (
    <Link key={to} to={to} data-testid={testid}
      className={`flex items-center gap-3 px-3 py-2 text-sm font-medium border-l-2 transition-all rounded-r-md ${
        active
          ? "bg-white/8 border-signal text-signal"
          : "border-transparent text-white/65 hover:text-white hover:bg-white/5"
      }`}>
      <Icon className="w-4 h-4 shrink-0" />
      {label}
    </Link>
  );
}

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();
  const [backendDown, setBackendDown] = useState(false);

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
    <div className="min-h-screen flex bg-bone">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="w-64 shrink-0 bg-ink text-white flex flex-col overflow-y-auto" data-testid="sidebar">

        {/* Brand */}
        <div className="px-6 py-6 border-b border-white/10 flex items-center justify-between shrink-0">
          <Link to="/dashboard" className="flex items-center gap-3" data-testid="sidebar-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-10 h-10 object-contain" style={{ mixBlendMode: "screen" }} />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <NotificationBell />
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4">

          {/* ── CORE (everyone) ───────────────────────────────────────── */}
          <NavSection label="Home">
            <NavLink loc={loc} to="/dashboard"       label="Dashboard"       icon={LayoutDashboard} testid="nav-dashboard" />
            <NavLink loc={loc} to="/profile"         label="My Profile"      icon={UserCircle}      testid="nav-profile" />
            <NavLink loc={loc} to="/my-position"     label="My Position"     icon={Compass}         testid="nav-my-position" />
            <NavLink loc={loc} to="/settings"        label="Settings"        icon={KeyRound}        testid="nav-settings" />
          </NavSection>

          <NavSection label="Learn">
            <NavLink loc={loc} to="/ai"              label="AI Tutor"        icon={Sparkles}        testid="nav-ai" />
            <NavLink loc={loc} to="/council"         label="Council (Sage)"  icon={Layers}          testid="nav-council" />
            <NavLink loc={loc} to="/modules"         label="Curriculum"      icon={BookOpen}        testid="nav-modules" />
            <NavLink loc={loc} to="/labs"            label="Workforce Labs"  icon={FlaskConical}    testid="nav-labs" />
            <NavLink loc={loc} to="/lab-simulations" label="Lab Simulations" icon={FlaskConical}    testid="nav-lab-sims" />
            <NavLink loc={loc} to="/compliance"      label="Compliance"      icon={ShieldCheck}     testid="nav-compliance" />
            <NavLink loc={loc} to="/adaptive"        label="Learning Path"   icon={Brain}           testid="nav-adaptive" />
            <NavLink loc={loc} to="/competencies"    label="Competencies"    icon={Target}          testid="nav-competencies" />
          </NavSection>

          <NavSection label="Credentials">
            <NavLink loc={loc} to="/credentials"    label="Credentials"      icon={BadgeCheck}      testid="nav-credentials" />
            <NavLink loc={loc} to="/certificates"   label="Certificates"     icon={Award}           testid="nav-certs" />
            <NavLink loc={loc} to="/portfolio"      label="Portfolio"        icon={Briefcase}       testid="nav-portfolio" />
          </NavSection>

          <NavSection label="Community">
            <NavLink loc={loc} to="/palace"         label="Members' Palace"  icon={Crown}           testid="nav-palace" />
            <NavLink loc={loc} to="/elder-council"  label="Elder Council"    icon={Layers}          testid="nav-elder-council" />
            <NavLink loc={loc} to="/leaderboard"    label="XP Leaderboard"   icon={Trophy}          testid="nav-leaderboard" />
            <NavLink loc={loc} to="/incidents"      label="Report Incident"  icon={ShieldAlert}     testid="nav-incidents" />
          </NavSection>

          <NavSection label="M.O.R.E.">
            <NavLink loc={loc} to="/app/more"       label="M.O.R.E. Hub"     icon={HandHelping}     testid="nav-more" />
            <NavLink loc={loc} to="/more/chat"      label="Community Chat"   icon={Radio}           testid="nav-more-chat" />
            <NavLink loc={loc} to="/more/litigation" label="Legal Tools"     icon={Scale}           testid="nav-litigation" />
            <NavLink loc={loc} to="/app/helper"     label="Personal Helper"  icon={HelpCircle}      testid="nav-helper" />
          </NavSection>

          {/* ── CREATOR'S SANCTUARY (all roles — page handles tier locks) ── */}
          <NavSection label="Creator's Sanctuary">
            <NavLink loc={loc} to="/studio"               label="Creator Studio"    icon={Music}        testid="nav-creator-studio" />
            <NavLink loc={loc} to="/creator/courses"      label="Course Manager"    icon={Video}        testid="nav-creator-courses" />
            <NavLink loc={loc} to="/creator/earnings"     label="My Earnings"       icon={DollarSign}   testid="nav-creator-earnings" />
            <NavLink loc={loc} to="/creator/payouts"      label="Payout Dashboard"  icon={Receipt}      testid="nav-creator-payouts" />
            <NavLink loc={loc} to="/creator/profile/edit" label="Creator Profile"   icon={UserCircle}   testid="nav-creator-profile" />
            <NavLink loc={loc} to="/creator-lounge"       label="Creator Lounge"    icon={Mic}          testid="nav-creator-lounge" />
            <NavLink loc={loc} to="/ghost-producer"       label="Ghost Producer"    icon={Palette}      testid="nav-ghost-producer" />
            <NavLink loc={loc} to="/band"                 label="Band on a Page"    icon={Music}        testid="nav-band" />
            <NavLink loc={loc} to="/social/publish"       label="Social Publisher"  icon={Globe}        testid="nav-social-publish" />
            <NavLink loc={loc} to="/playlist/dashboard"   label="Playlist Manager"  icon={Radio}        testid="nav-playlist" />
            <NavLink loc={loc} to="/arcade"               label="Virtual Arcade"    icon={Gamepad2}     testid="nav-arcade" />
          </NavSection>

          <NavSection label="Commerce">
            <NavLink loc={loc} to="/store"           label="Store"            icon={ShoppingBag}    testid="nav-store" />
            <NavLink loc={loc} to="/plans"           label="Plans & Pricing"  icon={Star}           testid="nav-plans" />
            <NavLink loc={loc} to="/subscribe"       label="Membership"       icon={HandHelping}    testid="nav-subscribe" />
            <NavLink loc={loc} to="/donate"          label="Donate"           icon={Heart}          testid="nav-donate" />
            <NavLink loc={loc} to="/payment/history" label="Payment History"  icon={Receipt}        testid="nav-payment-history" />
            <NavLink loc={loc} to="/partnership"     label="Partnerships"     icon={Network}        testid="nav-partnership" />
          </NavSection>

          {/* ── INSTRUCTOR ────────────────────────────────────────────── */}
          {isInstructor && (
            <NavSection label="Instructor">
              <NavLink loc={loc} to="/instructor"      label="My Roster"       icon={Users}           testid="nav-instructor" />
              <NavLink loc={loc} to="/instructor/labs" label="Lab Approvals"   icon={ClipboardCheck}  testid="nav-lab-approvals" />
              <NavLink loc={loc} to="/attendance"      label="Attendance"      icon={Calendar}        testid="nav-attendance" />
            </NavSection>
          )}

          {/* ── ADMIN ─────────────────────────────────────────────────── */}
          {isAdmin && (
            <NavSection label="Administration">
              <NavLink loc={loc} to="/admin"           label="Admin Overview"  icon={Settings}        testid="nav-admin" />
              <NavLink loc={loc} to="/admin/users"     label="Users"           icon={Users}           testid="nav-admin-users" />
              <NavLink loc={loc} to="/admin/accounts"  label="Accounts"        icon={Users}           testid="nav-accounts" />
              <NavLink loc={loc} to="/admin/tools"     label="Sites & Inventory" icon={Building2}     testid="nav-admin-tools" />
              <NavLink loc={loc} to="/admin/analytics" label="Analytics"       icon={TrendingUp}      testid="nav-analytics" />
              <NavLink loc={loc} to="/admin/audit"     label="Audit Log"       icon={ScrollText}      testid="nav-audit" />
              <NavLink loc={loc} to="/admin/payments"  label="Payments"        icon={Receipt}         testid="nav-admin-payments" />
              <NavLink loc={loc} to="/admin/billing"   label="Billing"         icon={DollarSign}      testid="nav-billing" />
              <NavLink loc={loc} to="/admin/prices"    label="Prices"          icon={Star}            testid="nav-prices" />
              <NavLink loc={loc} to="/admin/health"    label="System Health"   icon={ShieldCheck}     testid="nav-health" />
              <NavLink loc={loc} to="/admin/moderation" label="Moderation"     icon={Shield}          testid="nav-moderation" />
              <NavLink loc={loc} to="/revenue"         label="Revenue"         icon={DollarSign}      testid="nav-revenue" />
              <NavLink loc={loc} to="/auditor"         label="Auditor"         icon={FileText}        testid="nav-auditor" />
              <NavLink loc={loc} to="/more/admin"      label="M.O.R.E. Admin"  icon={HandHelping}     testid="nav-more-admin" />
              <NavLink loc={loc} to="/more/ops"        label="Dept. AI Ops"    icon={Network}         testid="nav-more-ops" />
              <NavLink loc={loc} to="/assistant"       label="Admin Assistant" icon={Sparkles}        testid="nav-assistant" />
            </NavSection>
          )}

          {/* ── EXECUTIVE ─────────────────────────────────────────────── */}
          {isExec && (
            <NavSection label="Executive">
              <NavLink loc={loc} to="/admin/system"      label="Exec System"      icon={Crown}        testid="nav-exec-system" />
              <NavLink loc={loc} to="/admin/control"     label="Site Control"     icon={Shield}       testid="nav-control-panel" />
              <NavLink loc={loc} to="/admin/exec-control" label="Sovereign Command" icon={Layers}     testid="nav-exec-control" />
              <NavLink loc={loc} to="/admin/director"    label="Director Dash"    icon={Compass}      testid="nav-exec-director" />
              <NavLink loc={loc} to="/admin/sage-audit"  label="Sage Audit"       icon={ScrollText}   testid="nav-sage-audit" />
              <NavLink loc={loc} to="/admin/staff-meetings" label="Staff Meetings" icon={Users}       testid="nav-staff-meetings" />
              <NavLink loc={loc} to="/admin/providers"   label="Provider Gateway" icon={Network}      testid="nav-providers" />
              <NavLink loc={loc} to="/team/ops"          label="Team Ops"         icon={Settings}     testid="nav-team-ops" />
              <NavLink loc={loc} to="/supervisor"        label="Supervisor Hub"   icon={Radio}        testid="nav-supervisor" />
              <NavLink loc={loc} to="/creative-partner"  label="Creative Partner" icon={Palette}      testid="nav-creative-partner" />
              <NavLink loc={loc} to="/arena"             label="The Arena"        icon={Swords}       testid="nav-arena" />
              <NavLink loc={loc} to="/jamil"             label="Jamil"            icon={Sparkles}     testid="nav-jamil" />
            </NavSection>
          )}

        </nav>

        {/* WAI Institute card */}
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

        {/* User footer */}
        <div className="px-4 py-5 border-t border-white/10 shrink-0">
          <div className="text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
          <div className="font-heading text-white font-semibold mt-1 truncate flex items-center gap-2">
            {user?.full_name}
            {isExec && <span className="bg-signal text-ink text-[9px] font-black px-1.5 py-0.5" title="Executive Admin" data-testid="exec-badge">EXEC</span>}
            {role === "admin" && <span className="bg-copper text-white text-[9px] font-black px-1.5 py-0.5">ADMIN</span>}
          </div>
          <div className="text-xs text-white/50 capitalize">{role.replace("_", " ")}{user?.associate ? ` · ${user.associate}` : ""}</div>
          <button onClick={() => { logout(); nav("/"); }} data-testid="btn-logout"
            className="mt-4 w-full flex items-center justify-center gap-2 border border-white/20 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors">
            <LogOut className="w-3.5 h-3.5" /> Log Out
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
