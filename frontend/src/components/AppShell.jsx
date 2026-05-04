import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Zap, LayoutDashboard, BookOpen, Award, Users, Settings, Sparkles, LogOut, FlaskConical, Target, ClipboardCheck } from "lucide-react";

const studentNav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testid: "nav-dashboard" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/competencies", label: "Competencies", icon: Target, testid: "nav-competencies" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
  { to: "/certificates", label: "Certificates", icon: Award, testid: "nav-certs" },
];

const instructorNav = [
  { to: "/instructor", label: "Roster", icon: Users, testid: "nav-instructor" },
  { to: "/instructor/labs", label: "Lab Approvals", icon: ClipboardCheck, testid: "nav-lab-approvals" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
];

const adminNav = [
  { to: "/admin", label: "Admin", icon: Settings, testid: "nav-admin" },
  { to: "/instructor", label: "Roster", icon: Users, testid: "nav-instructor" },
  { to: "/instructor/labs", label: "Lab Approvals", icon: ClipboardCheck, testid: "nav-lab-approvals" },
  { to: "/modules", label: "Curriculum", icon: BookOpen, testid: "nav-modules" },
  { to: "/labs", label: "Apprentice Labs", icon: FlaskConical, testid: "nav-labs" },
  { to: "/ai", label: "AI Tutor", icon: Sparkles, testid: "nav-ai" },
];

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();

  const items = user?.role === "admin" ? adminNav : user?.role === "instructor" ? instructorNav : studentNav;

  return (
    <div className="min-h-screen flex bg-bone">
      <aside className="w-64 shrink-0 bg-ink text-white flex flex-col" data-testid="sidebar">
        <div className="px-6 py-7 border-b border-white/10">
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-signal flex items-center justify-center">
              <Zap className="w-5 h-5 text-ink" strokeWidth={3} />
            </div>
            <div>
              <div className="overline text-signal">LCE-WAI</div>
              <div className="font-heading font-bold text-sm leading-tight">Lightning City</div>
            </div>
          </Link>
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
