import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut, FlaskConical, Target, ClipboardCheck, Briefcase, BadgeCheck, Brain, ShieldCheck, Building2, TrendingUp, ScrollText, Calendar, ShieldAlert, KeyRound } from "lucide-react";
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
  { to: "/admin", label: "Admin", icon: Settings, testid: "nav-admin" },
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

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();

  const items = user?.role === "admin" ? adminNav : user?.role === "instructor" ? instructorNav : studentNav;

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
            const active = loc.pathname.startsWith(i.to);
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
        <div className="px-4 py-5 border-t border-white/10">
          <div className="text-xs text-white/50 uppercase tracking-widest">Signed in as</div>
          <div className="font-heading text-white font-semibold mt-1 truncate">{user?.full_name}</div>
          <div className="text-xs text-white/50 capitalize">{user?.role} {user?.associate ? `• ${user.associate}` : ""}</div>
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
