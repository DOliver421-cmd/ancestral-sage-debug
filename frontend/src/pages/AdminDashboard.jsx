import { useState, useEffect, useCallback } from "react";
import {
  AlertTriangle, Users, Ban, ShieldAlert,
  RefreshCw, CheckCircle, Clock, Flag,
} from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab]     = useState("incidents");
  const [incidents, setIncidents]     = useState([]);
  const [users, setUsers]             = useState([]);
  const [auditLog, setAuditLog]       = useState([]);
  const [stats, setStats]             = useState(null);
  const [loading, setLoading]         = useState(true);
  const [toast, setToast]             = useState(null);

  function notify(msg, err = false) {
    setToast({ msg, err });
    setTimeout(() => setToast(null), 4000);
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [incR, usrR, actR, stR] = await Promise.allSettled([
        api.get("/incidents"),
        api.get("/admin/users"),
        api.get("/admin/recent-activity?limit=20"),
        api.get("/admin/stats"),
      ]);
      if (incR.status === "fulfilled") setIncidents(incR.value.data || []);
      if (usrR.status === "fulfilled") setUsers(usrR.value.data || []);
      if (actR.status === "fulfilled") setAuditLog(actR.value.data || []);
      if (stR.status  === "fulfilled") setStats(stR.value.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function resolveIncident(iid) {
    const resolution = window.prompt("Enter resolution note:");
    if (!resolution) return;
    try {
      await api.post(`/incidents/${iid}/resolve`, { resolution });
      notify("Incident resolved");
      setIncidents(prev => prev.map(i => i.id === iid ? { ...i, status: "resolved", resolution } : i));
    } catch (e) {
      notify(e?.response?.data?.detail || "Failed to resolve", true);
    }
  }

  async function deactivateUser(uid, name) {
    if (!window.confirm(`Deactivate ${name}?`)) return;
    try {
      await api.patch(`/admin/users/${uid}/active`, { is_active: false });
      notify(`${name} deactivated`);
      setUsers(prev => prev.map(u => u.id === uid ? { ...u, is_active: false } : u));
    } catch (e) {
      notify(e?.response?.data?.detail || "Failed", true);
    }
  }

  const canResolve = ["admin", "executive_admin"].includes(user?.role);

  return (
    <AppShell>
      <div className="min-h-screen bg-bone">
        {/* Header */}
        <div className="bg-ink text-white px-6 lg:px-10 py-6 border-b border-white/10">
          <div className="max-w-6xl mx-auto flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-xs font-bold uppercase tracking-widest text-white/50 mb-1">Admin</div>
              <h1 className="font-heading text-2xl font-extrabold">Governance Dashboard</h1>
              <p className="text-sm text-white/60 mt-1">
                {stats ? `${stats.users ?? 0} users · ${stats.incidents_open ?? 0} open incidents` : "Loading…"}
              </p>
            </div>
            <button onClick={load} disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-sm font-bold rounded-lg transition-colors disabled:opacity-40">
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {toast && (
          <div className={`px-6 py-3 text-sm font-medium ${toast.err ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
            {toast.msg}
          </div>
        )}

        <div className="max-w-6xl mx-auto px-6 lg:px-10 py-6">
          {/* Tabs */}
          <div className="flex gap-6 border-b border-ink/10 mb-6">
            {[
              { key: "incidents", label: `Incidents (${incidents.filter(i => i.status === "open").length})` },
              { key: "users",     label: `Users (${users.length})` },
              { key: "audit",     label: `Audit Log (${auditLog.length})` },
            ].map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)}
                className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === t.key ? "border-copper text-copper" : "border-transparent text-ink/50 hover:text-ink"}`}>
                {t.label}
              </button>
            ))}
          </div>

          {/* INCIDENTS TAB */}
          {activeTab === "incidents" && (
            <div className="space-y-3">
              {loading ? (
                <div className="py-10 text-center text-ink/40 text-sm">Loading…</div>
              ) : incidents.length === 0 ? (
                <div className="py-10 text-center text-ink/40 text-sm">No incidents found.</div>
              ) : incidents.map(inc => (
                <div key={inc.id} className={`bg-white border-l-4 rounded-xl p-5 shadow-sm ${
                  inc.severity === "critical" ? "border-red-500" :
                  inc.severity === "high"     ? "border-orange-400" :
                  inc.severity === "medium"   ? "border-yellow-400" : "border-slate-300"
                }`}>
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-black uppercase px-2 py-0.5 rounded-full ${
                          inc.status === "open" ? "bg-red-100 text-red-700" :
                          inc.status === "resolved" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                        }`}>{inc.status}</span>
                        <span className="text-xs font-bold text-slate-500 uppercase">{inc.severity}</span>
                      </div>
                      <p className="font-heading font-bold text-slate-900">{inc.title || inc.type || "Incident"}</p>
                      <p className="text-sm text-slate-600 mt-1">{inc.description || inc.content || ""}</p>
                      {inc.resolution && <p className="text-xs text-emerald-700 mt-1 italic">Resolution: {inc.resolution}</p>}
                      <p className="text-xs text-slate-400 mt-2">
                        Reported by {inc.reporter?.full_name || inc.reported_by} · {inc.created_at ? new Date(inc.created_at).toLocaleString() : ""}
                      </p>
                    </div>
                    {canResolve && inc.status === "open" && (
                      <button onClick={() => resolveIncident(inc.id)}
                        className="text-xs font-bold px-3 py-1.5 rounded-lg border border-emerald-400 text-emerald-700 hover:bg-emerald-50 transition-colors whitespace-nowrap">
                        <CheckCircle className="w-3.5 h-3.5 inline mr-1" />Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* USERS TAB */}
          {activeTab === "users" && (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-100">
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Name</th>
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Email</th>
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Role</th>
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Status</th>
                    <th className="py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-3 px-4 font-heading font-bold text-slate-900">{u.full_name || "—"}</td>
                      <td className="py-3 px-4 font-mono text-slate-600 text-xs">{u.email}</td>
                      <td className="py-3 px-4 text-xs font-bold text-slate-700 capitalize">{u.role?.replace("_", " ")}</td>
                      <td className="py-3 px-4">
                        {u.is_active === false
                          ? <span className="text-xs font-bold bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Inactive</span>
                          : <span className="text-xs font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">Active</span>}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {canResolve && u.is_active !== false && (
                          <button onClick={() => deactivateUser(u.id, u.full_name)}
                            className="text-xs font-bold px-2 py-1 border border-red-300 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                            Deactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* AUDIT LOG TAB */}
          {activeTab === "audit" && (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-100">
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Time</th>
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Actor</th>
                    <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map((a, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-3 px-4 text-xs text-slate-500 whitespace-nowrap">
                        {a.at ? new Date(a.at).toLocaleString() : "—"}
                      </td>
                      <td className="py-3 px-4 text-slate-700 font-medium">{a.actor_name || a.actor_id || "—"}</td>
                      <td className="py-3 px-4 font-mono text-xs text-amber-700">{a.action}</td>
                    </tr>
                  ))}
                  {auditLog.length === 0 && !loading && (
                    <tr><td colSpan={3} className="py-8 text-center text-slate-400 text-sm">No audit entries found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
