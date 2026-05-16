import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut, FlaskConical, Target, ClipboardCheck, Briefcase, BadgeCheck, Brain, ShieldCheck, Building2, TrendingUp, ScrollText, Calendar, ShieldAlert, KeyRound, Crown, Compass, HelpCircle } from "lucide-react";
import NotificationBell from "./NotificationBell";

const studentNav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/compliance", label: "Compliance", icon: ShieldCheck, testid: "nav-compliance" },
  { to: "/adaptive", label: "Learning Path", icon: Brain, testid: "nav-adaptive" },
  { to: "/competencies", label: "Competencies", icon: Target, testid: "nav-competencies" },
  { to: "/credentials", label: "Credentials", icon: BadgeCheck, testid: "nav-credentials" },
  { to: "/portfolio", label: "Portfolio", icon: Briefcase, testid: "nav-portfolio" },
  { to: "/incidents", label: "Report Incident", icon: ShieldAlert, testid: "nav-incidents" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
  { to: "/certificates", label: "Certificates", icon: Award, testid: "nav-certs" },
  { to: "/settings", label: "Settings", icon: KeyRound, testid: "nav-settings" },
];

const instructorNav = [
  { to: "/instructor", label: "Roster", icon: Users, testid: "nav-instructor" },
  { to: "/instructor/labs", label: "Lab Approvals", icon: ClipboardCheck, testid: "nav-lab-approvals" },
  { to: "/attendance", label: "Attendance", icon: Calendar, testid: "nav-attendance" },
  { to: "/incidents", label: "Incidents", icon: ShieldAlert, testid: "nav-incidents" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/compliance", label: "Compliance", icon: ShieldCheck, testid: "nav-compliance" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
  { to: "/settings", label: "Settings", icon: KeyRound, testid: "nav-settings" },
];

const adminNav = [
  { to: "/admin", label: "Overview", icon: Settings, testid: "nav-admin" },
  { to: "/admin/users", label: "Users", icon: Users, testid: "nav-admin-users" },
  { to: "/admin/analytics", label: "Analytics", icon: TrendingUp, testid: "nav-analytics" },
  { to: "/admin/audit", label: "Audit Log", icon: ScrollText, testid: "nav-audit" },
  { to: "/admin/tools", label: "Sites & Inventory", icon: Building2, testid: "nav-admin-tools" },
  { to: "/instructor", label: "Roster", icon: Users, testid: "nav-instructor" },
  { to: "/instructor/labs", label: "Lab Approvals", icon: ClipboardCheck, testid: "nav-lab-approvals" },
  { to: "/attendance", label: "Attendance", icon: Calendar, testid: "nav-attendance" },
  { to: "/incidents", label: "Incidents", icon: ShieldAlert, testid: "nav-incidents" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
  { to: "/settings", label: "Settings", icon: KeyRound, testid: "nav-settings" },
];

const execAdminNav = [
  { to: "/admin/system", label: "System", icon: Crown, testid: "nav-exec-system" },
  { to: "/admin/sage-audit", label: "Sage Sessions", icon: Compass, testid: "nav-sage-audit" },
  ...adminNav,
];

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();

  const items = user?.role === "executive_admin" ? execAdminNav
    : user?.role === "admin" ? adminNav
    : user?.role === "instructor" ? instructorNav
    : studentNav;
  const isExec = user?.role === "executive_admin";

  return (
    <div className="min-h-screen flex bg-bone">
      <aside className="w-64 shrink-0 bg-ink text-white flex flex-col" data-testid="sidebar">
        <div className="px-6 py-7 border-b border-white/10 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-3" data-testid="sidebar-brand">
            <img src={WAI_LOGO} alt="W.A.I." className="w-10 h-10 object-contain bg-white p-1 rounded-sm" />
            <div>
              <div className="overline text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <NotificationBell />
        </div>
        <nav className="flex-1 px-3 py-6 space-y-1">
          {items.map((i) => {
            const active = i.to === "/admin"
              ? loc.pathname === "/admin"
              : loc.pathname === i.to || loc.pathname.startsWith(i.to + "/");
            const Icon = i.icon;
            return (
              <Link key={i.to} to={i.to} data-testid={i.testid}
                className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium border-l-2 transition-all ${active ? "bg-white/5 border-signal text-signal" : "border-transparent text-white/70 hover:text-white hover:bg-white/5"}`}>
                <Icon className="w-4 h-4" />
                {i.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 pb-4">
          <Link
            to="/app/helper"
            data-testid="nav-helper"
            className="flex flex-col gap-1 w-full rounded-xl p-4 text-white no-underline transition-all hover:opacity-90"
            style={{ background: "linear-gradient(135deg,#2563eb,#7c3aed)", textDecoration: "none", boxShadow: "0 4px 16px rgba(37,99,235,0.30)" }}
          >
            <div className="flex items-center gap-2">
              <HelpCircle className="w-5 h-5 shrink-0" style={{ color: "#fde68a" }} />
              <span style={{ fontSize: 15, fontWeight: 800, lineHeight: 1.2, color: "#fff" }}>Personal Help Center</span>
            </div>
            <span style={{ fontSize: 11, opacity: 0.85, lineHeight: 1.4, color: "#fff", paddingLeft: 28 }}>
              Understand letters, bills, legal papers, housing notices and more — in plain words
            </span>
          </Link>
        </div>

        <div className="px-4 py-5 border-t border-white/10">
          <div className="text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
          <div className="font-heading text-white font-semibold mt-1 truncate flex items-center gap-2">
            {user?.full_name}
            {isExec && <span className="bg-signal text-ink text-[9px] font-black px-1.5 py-0.5" title="Executive Admin" data-testid="exec-badge">EXEC</span>}
          </div>
          <div className="text-xs text-white/50 capitalize">{(user?.role || "").replace("_", " ")} {user?.associate ? `• ${user.associate}` : ""}</div>
          <button onClick={() => { logout(); nav("/"); }} data-testid="btn-logout"
            className="mt-4 w-full flex items-center justify-center gap-2 border border-white/20 py-2 text-xs uppercase tracking-widest font-bold hover:bg-white hover:text-ink transition-colors">
            <LogOut className="w-3.5 h-3.5" /> Log Out
          </button>
        </div>
      </aside>
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
