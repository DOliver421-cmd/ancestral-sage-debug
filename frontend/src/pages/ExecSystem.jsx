import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import {
  Crown, Database, Users, Shield, Settings as Cog,
  Activity, AlertTriangle, BadgeCheck, BookOpen,
  GraduationCap, Award, RefreshCw, ExternalLink,
  CheckCircle2, XCircle, Clock, Zap, Scale, MessageSquare,
  FileText, UserCog, Eye, HandHelping,
} from "lucide-react";

// ── small helpers ─────────────────────────────────────────────────────────────
function ts(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function StatusDot({ ok, label }) {
  return (
    <div className="flex items-center gap-2">
      {ok
        ? <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
        : <XCircle className="w-4 h-4 text-red-500 shrink-0" />}
      <span className="text-sm font-medium" style={{ color: ok ? "#059669" : "#dc2626" }}>{label}</span>
    </div>
  );
}

function KPI({ icon: Icon, label, value, alert, sub, accent }) {
  const color = alert ? "#dc2626" : accent || "#b5501a";
  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm"
      style={alert ? { borderLeft: "4px solid #dc2626" } : {}}>
      <div className="flex items-start justify-between">
        <Icon className="w-5 h-5 mt-0.5" style={{ color }} />
        {alert && <AlertTriangle className="w-4 h-4 text-red-500" />}
      </div>
      <div className="font-heading font-black text-3xl mt-3" style={{ color: alert ? "#dc2626" : "#0b1f3a" }}>
        {value ?? "—"}
      </div>
      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function QuickAction({ icon: Icon, label, to, color = "#0b1f3a" }) {
  return (
    <Link to={to}
      className="flex items-center gap-3 p-4 rounded-xl border-2 font-bold text-sm transition-all hover:scale-105"
      style={{ borderColor: color, color }}>
      <Icon className="w-5 h-5 shrink-0" />
      {label}
      <ExternalLink className="w-3.5 h-3.5 ml-auto opacity-40" />
    </Link>
  );
}

// ── main ──────────────────────────────────────────────────────────────────────
export default function ExecSystem() {
  const [sys,      setSys]      = useState(null);
  const [stats,    setStats]    = useState(null);
  const [activity, setActivity] = useState([]);
  const [cohorts,  setCohorts]  = useState([]);
  const [more,     setMore]     = useState({ posts: 0, needs: 0 });
  const [err,      setErr]      = useState(null);
  const [lastSync, setLastSync] = useState(null);
  const [loading,  setLoading]  = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sysR, statsR, actR, cohR, postsR, needsR] = await Promise.allSettled([
        api.get("/exec/system"),
        api.get("/admin/stats"),
        api.get("/admin/recent-activity?limit=12"),
        api.get("/admin/cohorts"),
        fetch(`${window.location.origin}/api/more/posts?limit=1`).then(r => r.json()),
        fetch(`${window.location.origin}/api/more/needs?limit=1`).then(r => r.json()),
      ]);
      if (sysR.status === "fulfilled")   setSys(sysR.value.data);
      else                               setErr("System endpoint unavailable");
      if (statsR.status === "fulfilled") setStats(statsR.value.data);
      if (actR.status === "fulfilled")   setActivity(actR.value.data || []);
      if (cohR.status === "fulfilled")   setCohorts(cohR.value.data || []);
      setMore({
        posts: postsR.status === "fulfilled" ? (postsR.value.total ?? 0) : 0,
        needs: needsR.status === "fulfilled" ? (needsR.value.total ?? 0) : 0,
      });
      setLastSync(new Date());
    } catch (e) {
      setErr(e?.response?.data?.detail || "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const ROLE_MAP = {
    executive_admin: { label: "Executive Admins", color: "#f59e0b", icon: Crown },
    admin:           { label: "Admins",            color: "#0b1f3a", icon: Shield },
    instructor:      { label: "Instructors",       color: "#b5501a", icon: GraduationCap },
    student:         { label: "Students",          color: "#1d4ed8", icon: Users },
  };

  const totalUsers = Object.values(sys?.role_counts || {}).reduce((a, b) => a + b, 0);
  const hasIncidents = (stats?.incidents_open || 0) > 0;
  const hasLabsPending = (stats?.labs_pending || 0) > 5;

  return (
    <AppShell>
      <div className="px-6 lg:px-10 py-8 max-w-7xl" style={{ background: "#f8f7f4", minHeight: "100vh" }}>

        {/* ── Header ───────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Crown className="w-5 h-5 text-amber-500" />
              <span className="text-xs font-bold uppercase tracking-widest text-amber-600">Executive Command</span>
            </div>
            <h1 className="font-heading text-3xl lg:text-4xl font-extrabold text-slate-900">
              WAI-Institute Platform
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              {lastSync
                ? <>Last refreshed {ts(lastSync)} · <span className="text-emerald-600 font-semibold">All systems checked</span></>
                : "Loading…"}
            </p>
          </div>
          <button onClick={load} disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-slate-700 transition-colors disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>

        {err && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm font-medium flex items-center gap-2">
            <XCircle className="w-4 h-4 shrink-0" /> {err}
          </div>
        )}

        {/* ── System status bar ─────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm mb-6">
          <div className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">Platform Status</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatusDot ok={!!sys}      label="API Server" />
            <StatusDot ok={!!sys}      label="Database" />
            <StatusDot ok={!hasIncidents} label={hasIncidents ? `${stats?.incidents_open} Open Incidents` : "No Incidents"} />
            <StatusDot ok={!hasLabsPending} label={hasLabsPending ? `${stats?.labs_pending} Labs Pending` : "Labs Current"} />
          </div>
        </div>

        {/* ── KPI grid ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
          <KPI icon={Users}       label="Total Users"       value={totalUsers || stats?.users}  sub="all roles combined" />
          <KPI icon={GraduationCap} label="Students"        value={stats?.students}             sub="enrolled" />
          <KPI icon={Award}       label="Completions"       value={stats?.completions}          sub="modules completed" accent="#1d4ed8" />
          <KPI icon={BadgeCheck}  label="Credentials"       value={stats?.credentials_issued}   sub="issued to date" accent="#059669" />
          <KPI icon={AlertTriangle} label="Open Incidents"  value={stats?.incidents_open}       alert={(stats?.incidents_open || 0) > 0} sub="requires review" />
          <KPI icon={Clock}       label="Labs Pending"      value={stats?.labs_pending}         alert={(stats?.labs_pending || 0) > 5} sub="awaiting review" />
          <KPI icon={HandHelping} label="M.O.R.E. Posts"   value={more.posts}                  sub="community exchange" accent="#7c3aed" />
          <KPI icon={MessageSquare} label="M.O.R.E. Needs" value={more.needs}                  sub="active requests" accent="#0891b2" />
        </div>

        {/* ── Main content: 3 columns ───────────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-6 mb-6">

          {/* Role distribution */}
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <h2 className="font-heading font-extrabold text-lg text-slate-900 mb-4 flex items-center gap-2">
              <Users className="w-5 h-5 text-slate-400" /> Role Distribution
            </h2>
            <div className="space-y-3">
              {Object.entries(ROLE_MAP).map(([role, cfg]) => {
                const count = sys?.role_counts?.[role] || 0;
                const pct = totalUsers > 0 ? Math.round((count / totalUsers) * 100) : 0;
                const Icon = cfg.icon;
                return (
                  <div key={role}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                        <Icon className="w-3.5 h-3.5" style={{ color: cfg.color }} />
                        {cfg.label}
                      </div>
                      <span className="font-heading font-black text-lg" style={{ color: cfg.color }}>{count}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: cfg.color }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Runtime summary */}
            <div className="mt-6 pt-5 border-t border-slate-100 space-y-2 text-xs text-slate-500">
              <div className="flex justify-between">
                <span>Platform version</span>
                <span className="font-mono font-bold text-slate-700">{sys?.version || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span>Database</span>
                <span className="font-mono font-bold text-slate-700">{sys?.env?.db_name || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span>JWT lifetime</span>
                <span className="font-mono font-bold text-slate-700">{sys?.env?.jwt_expire_hours || "—"}h</span>
              </div>
              <div className="flex justify-between">
                <span>Audit log entries</span>
                <span className="font-mono font-bold text-slate-700">{sys?.audit_log_total?.toLocaleString() || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span>Collections</span>
                <span className="font-mono font-bold text-slate-700">{sys?.collections?.length || "—"}</span>
              </div>
            </div>
          </div>

          {/* Recent activity */}
          <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
            <h2 className="font-heading font-extrabold text-lg text-slate-900 mb-1 flex items-center gap-2">
              <Activity className="w-5 h-5 text-slate-400" /> Recent Activity
            </h2>
            <p className="text-xs text-slate-400 mb-4">Last {activity.length} privileged actions</p>
            <div className="space-y-1 overflow-y-auto" style={{ maxHeight: 320 }}>
              {activity.length === 0 && (
                <div className="text-sm text-slate-400 py-6 text-center">No activity recorded yet.</div>
              )}
              {activity.map((a) => (
                <div key={a.id} className="flex items-start gap-3 py-2 border-b border-slate-50">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-slate-800 truncate">{a.actor_name}</div>
                    <div className="text-xs font-mono text-amber-600 truncate">{a.action}</div>
                  </div>
                  <div className="text-[10px] text-slate-400 whitespace-nowrap shrink-0 mt-0.5">{ts(a.at)}</div>
                </div>
              ))}
            </div>
            <Link to="/admin/audit" className="flex items-center gap-1 text-xs font-bold text-amber-600 hover:underline mt-4">
              Full audit log <ExternalLink className="w-3 h-3" />
            </Link>
          </div>

          {/* Quick actions + associate summary */}
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
              <h2 className="font-heading font-extrabold text-lg text-slate-900 mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" /> Quick Actions
              </h2>
              <div className="space-y-2">
                <QuickAction icon={UserCog}      label="Manage Users"        to="/admin/users"       color="#0b1f3a" />
                <QuickAction icon={Eye}          label="Audit Log"           to="/admin/audit"       color="#b5501a" />
                <QuickAction icon={Shield}       label="Sage Audit"          to="/admin/sage-audit"  color="#7c3aed" />
                <QuickAction icon={Activity}     label="Analytics"           to="/admin/analytics"   color="#0891b2" />
                <QuickAction icon={Scale}        label="M.O.R.E. Admin"      to="/more/admin"        color="#059669" />
                <QuickAction icon={MessageSquare} label="Council of Elders"  to="/council"           color="#1d4ed8" />
                <QuickAction icon={Crown}        label="Set Sovereign Face"  to="/avatar-setup"      color="#059669" />
                <QuickAction icon={Cog}          label="Admin Dashboard"     to="/admin"             color="#64748b" />
              </div>
            </div>
          </div>
        </div>

        {/* ── Associate cohort table ─────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm mb-6">
          <h2 className="font-heading font-extrabold text-lg text-slate-900 mb-4 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-slate-400" /> Associate Cohort Performance
          </h2>
          {cohorts.length === 0 ? (
            <div className="text-sm text-slate-400 py-4">No associate cohorts found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-100">
                    <th className="text-left py-2 px-3 text-xs uppercase tracking-wider text-slate-400 font-bold">Associate</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-400 font-bold">Students</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-400 font-bold">Instructors</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-400 font-bold">Completions</th>
                    <th className="py-2 px-3 text-xs uppercase tracking-wider text-slate-400 font-bold">Completion Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {cohorts.map((c) => {
                    const rate = c.students > 0 ? Math.round((c.completions / (c.students * (stats?.modules || 1))) * 100) : 0;
                    return (
                      <tr key={c.associate} className="border-b border-slate-50 hover:bg-slate-50">
                        <td className="py-3 px-3 font-heading font-bold text-slate-900">{c.associate}</td>
                        <td className="py-3 px-3 text-right font-mono font-bold text-blue-700">{c.students}</td>
                        <td className="py-3 px-3 text-right font-mono text-slate-600">{c.instructors}</td>
                        <td className="py-3 px-3 text-right font-mono font-bold text-emerald-700">{c.completions}</td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(rate, 100)}%` }} />
                            </div>
                            <span className="text-xs font-bold text-slate-500 w-8 text-right">{rate}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── DB collections ────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
          <h2 className="font-heading font-extrabold text-base text-slate-900 mb-3 flex items-center gap-2">
            <Database className="w-4 h-4 text-slate-400" /> Live Collections ({sys?.collections?.length || 0})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1">
            {(sys?.collections || []).map((c) => (
              <div key={c} className="text-xs font-mono text-slate-500 py-1 px-2 bg-slate-50 rounded border border-slate-100">
                {c}
              </div>
            ))}
          </div>
        </div>

      </div>
    </AppShell>
  );
}
