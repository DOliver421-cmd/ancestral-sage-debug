import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  AlertTriangle, Activity, Users, TrendingUp, Lock, Unlock,
  ShieldAlert, RefreshCw, CheckCircle, XCircle, Radio,
  BarChart3, FileText, Power, Megaphone, KeyRound,
} from "lucide-react";

const SEV_COLOR = {
  critical: "bg-red-50 border-red-600",
  high: "bg-orange-50 border-orange-600",
  medium: "bg-yellow-50 border-yellow-500",
  low: "bg-gray-50 border-gray-400",
};
const SEV_BADGE = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-600 text-white",
  medium: "bg-yellow-500 text-white",
  low: "bg-gray-400 text-white",
};

const FEATURES = [
  { key: "marketplace_disabled", label: "Marketplace", desc: "Blocks new enrollments and course publishing." },
  { key: "ai_disabled",          label: "AI Services",  desc: "Disables all AI chat endpoints platform-wide." },
  { key: "community_disabled",   label: "Community (M.O.R.E.)", desc: "Blocks posting and interaction in M.O.R.E." },
  { key: "labs_disabled",        label: "Labs",         desc: "Disables lab submission and simulation access." },
];

export default function ExecutiveDirectorDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("threats");

  // --- password change state ---
  const [pwForm, setPwForm]         = useState({ current: "", next: "", confirm: "" });
  const [pwLoading, setPwLoading]   = useState(false);
  const [loading, setLoading] = useState(true);

  // --- data state ---
  const [stats, setStats]         = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [users, setUsers]         = useState([]);
  const [auditLog, setAuditLog]   = useState([]);
  const [flags, setFlags]         = useState({});
  const [platformLocked, setPlatformLocked] = useState(false);

  // --- modal state ---
  const [resolveTarget, setResolveTarget]     = useState(null); // { id }
  const [resolveNote, setResolveNote]         = useState("");
  const [deactivateTarget, setDeactivateTarget] = useState(null); // { uid, name }
  const [deleteTarget, setDeleteTarget]       = useState(null); // { uid, name }
  const [lockReason, setLockReason]           = useState("");
  const [confirmLock, setConfirmLock]         = useState(false);
  const [disableFlagTarget, setDisableFlagTarget] = useState(null); // { flagKey, label }
  const [disableFlagReason, setDisableFlagReason] = useState("");

  // --- broadcast state ---
  const [bcTarget, setBcTarget]   = useState("all");
  const [bcTitle, setBcTitle]     = useState("");
  const [bcMsg, setBcMsg]         = useState("");
  const [bcSending, setBcSending] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    const [statsRes, incRes, usersRes, auditRes, flagsRes] = await Promise.allSettled([
      api.get("/admin/stats"),
      api.get("/incidents?status=open"),
      api.get("/admin/users"),
      api.get("/admin/recent-activity?limit=50"),
      api.get("/admin/platform/flags"),
    ]);
    if (statsRes.status === "fulfilled") setStats(statsRes.value.data);
    if (incRes.status === "fulfilled")   setIncidents(incRes.value.data || []);
    if (usersRes.status === "fulfilled") setUsers(usersRes.value.data || []);
    if (auditRes.status === "fulfilled") setAuditLog(auditRes.value.data || []);
    if (flagsRes.status === "fulfilled") {
      const f = flagsRes.value.data?.flags || {};
      setFlags(f);
      setPlatformLocked(!!f.platform_locked?.enabled);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const criticalCount = incidents.filter(i => i.severity === "critical").length;
  const highCount     = incidents.filter(i => i.severity === "high").length;

  // ── INCIDENT ACTIONS ──────────────────────────────────────────────────────
  async function resolveIncident(id) {
    setResolveTarget({ id });
    setResolveNote("");
  }

  async function doResolveIncident() {
    const { id } = resolveTarget;
    setResolveTarget(null);
    try {
      await api.post(`/incidents/${id}/resolve`, { resolution_notes: resolveNote });
      toast.success("Incident resolved");
      setIncidents(prev => prev.filter(i => i.id !== id));
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  // ── USER ACTIONS ──────────────────────────────────────────────────────────
  async function deactivateUser(uid, name) {
    setDeactivateTarget({ uid, name });
  }

  async function doDeactivateUser() {
    const { uid, name } = deactivateTarget;
    setDeactivateTarget(null);
    try {
      await api.patch(`/admin/users/${uid}/active`, { is_active: false });
      toast.success(`${name} deactivated`);
      setUsers(prev => prev.map(u => u.id === uid ? { ...u, is_active: false } : u));
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  async function activateUser(uid, name) {
    try {
      await api.patch(`/admin/users/${uid}/active`, { is_active: true });
      toast.success(`${name} activated`);
      setUsers(prev => prev.map(u => u.id === uid ? { ...u, is_active: true } : u));
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  async function deleteUser(uid, name) {
    setDeleteTarget({ uid, name });
  }

  async function doDeleteUser() {
    const { uid, name } = deleteTarget;
    setDeleteTarget(null);
    try {
      await api.delete(`/admin/users/${uid}`);
      toast.success(`${name} deleted`);
      setUsers(prev => prev.filter(u => u.id !== uid));
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  // ── PLATFORM LOCK ─────────────────────────────────────────────────────────
  async function togglePlatformLock() {
    const next = !platformLocked;
    if (next) {
      setLockReason("");
      setConfirmLock(true);
    } else {
      await applyPlatformLock(false, "Lock removed by executive");
    }
  }

  async function applyPlatformLock(next, reason) {
    setConfirmLock(false);
    try {
      await api.post("/admin/platform/flags/platform_locked", { value: next, reason });
      setPlatformLocked(next);
      toast.success(next ? "Platform locked — users cannot make changes" : "Platform unlocked");
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  // ── FEATURE FLAGS ─────────────────────────────────────────────────────────
  async function toggleFeature(flagKey, label) {
    const current = !!flags[flagKey]?.enabled;
    const next = !current;
    if (next) {
      setDisableFlagTarget({ flagKey, label });
      setDisableFlagReason("");
    } else {
      await applyFeatureFlag(flagKey, label, false, `${label} re-enabled by executive`);
    }
  }

  async function applyFeatureFlag(flagKey, label, next, reason) {
    setDisableFlagTarget(null);
    try {
      await api.post(`/admin/platform/flags/${flagKey}`, { value: next, reason });
      setFlags(prev => ({
        ...prev,
        [flagKey]: { enabled: next, reason, set_at: new Date().toISOString() },
      }));
      toast.success(`${label} ${next ? "disabled" : "re-enabled"}`);
    } catch (e) {
      toast.error("Failed: " + (e.response?.data?.detail || e.message));
    }
  }

  // ── BROADCAST ─────────────────────────────────────────────────────────────
  async function sendBroadcast() {
    if (!bcMsg.trim()) { toast.error("Message is required"); return; }
    setBcSending(true);
    try {
      const res = await api.post("/admin/broadcast", {
        target: bcTarget,
        title: bcTitle.trim() || "Platform Announcement",
        message: bcMsg.trim(),
      });
      toast.success(`Broadcast sent to ${res.data.sent} user(s)`);
      setBcMsg(""); setBcTitle("");
    } catch (e) {
      toast.error("Broadcast failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setBcSending(false);
    }
  }

  const fmtTime = iso => iso
    ? new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
    : "—";

  const TABS = [
    { id: "threats",   label: `Threats (${incidents.length})`,        icon: <ShieldAlert className="w-4 h-4" /> },
    { id: "users",     label: `Users (${users.length})`,              icon: <Users className="w-4 h-4" /> },
    { id: "controls",  label: "Emergency Controls",                   icon: <Power className="w-4 h-4" /> },
    { id: "broadcast", label: "Broadcast",                            icon: <Megaphone className="w-4 h-4" /> },
    { id: "audit",     label: "Audit Log",                            icon: <FileText className="w-4 h-4" /> },
    { id: "account",   label: "Account",                              icon: <KeyRound className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-bone text-ink">

      {/* Critical alert banner — only when real incidents exist */}
      {criticalCount > 0 && (
        <div className="bg-red-900 text-white px-6 py-4 border-b-4 border-red-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
            <div>
              <p className="font-bold">CRITICAL INCIDENTS ACTIVE</p>
              <p className="text-sm">{criticalCount} require immediate action</p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab("threats")}
            className="px-4 py-2 bg-red-700 hover:bg-red-800 rounded font-bold text-sm"
          >
            VIEW THREATS
          </button>
        </div>
      )}

      {/* Platform locked banner */}
      {platformLocked && (
        <div className="bg-amber-100 border-b-2 border-amber-500 px-6 py-3 flex items-center gap-3">
          <Lock className="w-5 h-5 text-amber-700" />
          <p className="text-amber-800 font-semibold text-sm">
            Platform is currently locked — users cannot make changes. Only admins can operate.
          </p>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="font-heading text-3xl font-bold">Executive Director</h1>
            <p className="text-ink/80 text-sm mt-1">Platform governance, crisis response, strategic oversight</p>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/admin/providers" className="px-3 py-2 border border-ink/20 rounded-lg text-xs font-semibold hover:bg-ink/5">Provider Gateway</Link>
            <Link to="/admin/billing"   className="px-3 py-2 border border-ink/20 rounded-lg text-xs font-semibold hover:bg-ink/5">Billing & Credits</Link>
            <button onClick={loadAll} className="flex items-center gap-2 px-4 py-2 border border-ink/20 rounded-lg text-sm font-semibold hover:bg-ink/5">
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white border border-ink/10 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span className="text-xs font-bold text-ink/80 uppercase tracking-wide">Critical</span>
            </div>
            <p className="text-3xl font-bold text-red-600">{criticalCount}</p>
            <p className="text-xs text-ink/80 mt-1">Open incidents</p>
          </div>
          <div className="bg-white border border-ink/10 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              <span className="text-xs font-bold text-ink/80 uppercase tracking-wide">High</span>
            </div>
            <p className="text-3xl font-bold text-orange-500">{highCount}</p>
            <p className="text-xs text-ink/80 mt-1">Open incidents</p>
          </div>
          <div className="bg-white border border-ink/10 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-ink" />
              <span className="text-xs font-bold text-ink/80 uppercase tracking-wide">Users</span>
            </div>
            <p className="text-3xl font-bold text-ink">{loading ? "—" : (stats?.users ?? users.length)}</p>
            <p className="text-xs text-ink/80 mt-1">Registered</p>
          </div>
          <div className="bg-white border border-ink/10 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-ink" />
              <span className="text-xs font-bold text-ink/80 uppercase tracking-wide">Platform</span>
            </div>
            <p className="text-3xl font-bold" style={{ color: platformLocked ? "#dc2626" : "#16a34a" }}>
              {platformLocked ? "Locked" : "Active"}
            </p>
            <p className="text-xs text-ink/80 mt-1">Current state</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-ink/10 flex gap-6 mb-8 overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 py-3 font-bold border-b-2 transition-all whitespace-nowrap text-sm ${
                activeTab === t.id
                  ? "border-ink text-ink"
                  : "border-transparent text-ink/80 hover:text-ink"
              }`}
            >
              {t.icon}{t.label}
            </button>
          ))}
        </div>

        {/* ── THREATS TAB ─────────────────────────────────────────────────── */}
        {activeTab === "threats" && (
          <div className="space-y-4">
            {loading && <p className="text-ink/80">Loading incidents…</p>}
            {!loading && incidents.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
                <CheckCircle className="w-10 h-10 text-green-600 mx-auto mb-3" />
                <p className="font-bold text-green-800">No open incidents</p>
                <p className="text-green-700 text-sm mt-1">Platform is clear.</p>
              </div>
            )}
            {incidents.map(inc => (
              <div key={inc.id} className={`p-5 border-l-4 rounded-lg ${SEV_COLOR[inc.severity] || SEV_COLOR.low}`}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${SEV_BADGE[inc.severity] || SEV_BADGE.low}`}>
                        {(inc.severity || "unknown").toUpperCase()}
                      </span>
                      <span className="text-xs text-ink/80">{inc.type || "incident"}</span>
                      <span className="text-xs text-ink/70">{fmtTime(inc.created_at)}</span>
                    </div>
                    <p className="font-bold text-ink">{inc.title || inc.summary}</p>
                    {inc.description && <p className="text-sm text-ink/70 mt-1">{inc.description}</p>}
                    {inc.reported_by && <p className="text-xs text-ink/80 mt-2">Reported by: {inc.reported_by}</p>}
                  </div>
                  <button
                    onClick={() => resolveIncident(inc.id)}
                    className="px-4 py-2 bg-green-600 text-white text-sm font-bold rounded hover:bg-green-700 whitespace-nowrap"
                  >
                    Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── USERS TAB ────────────────────────────────────────────────────── */}
        {activeTab === "users" && (
          <div className="bg-white border border-ink/10 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between">
              <h2 className="font-bold text-ink">All Users ({users.length})</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-ink/10 text-ink/80 text-xs uppercase tracking-wide">
                    <th className="text-left px-5 py-3">Name</th>
                    <th className="text-left px-5 py-3">Email</th>
                    <th className="text-left px-5 py-3">Role</th>
                    <th className="text-left px-5 py-3">Status</th>
                    <th className="text-left px-5 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr><td colSpan={5} className="text-center py-8 text-ink/70">Loading…</td></tr>
                  )}
                  {!loading && users.length === 0 && (
                    <tr><td colSpan={5} className="text-center py-8 text-ink/70">No users found.</td></tr>
                  )}
                  {users.map(u => (
                    <tr key={u.id} className="border-b border-ink/5 hover:bg-ink/10">
                      <td className="px-5 py-3 font-semibold">{u.full_name || "—"}</td>
                      <td className="px-5 py-3 font-mono text-xs text-ink/70">{u.email}</td>
                      <td className="px-5 py-3">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                          {(u.role || "").replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {u.is_active === false
                          ? <span className="text-xs font-bold px-2 py-0.5 rounded bg-red-100 text-red-700">Inactive</span>
                          : <span className="text-xs font-bold px-2 py-0.5 rounded bg-green-100 text-green-700">Active</span>
                        }
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          {u.is_active === false
                            ? <button onClick={() => activateUser(u.id, u.full_name || u.email)} className="text-xs px-3 py-1.5 bg-green-600 text-white rounded font-bold hover:bg-green-700">Activate</button>
                            : <button onClick={() => deactivateUser(u.id, u.full_name || u.email)} className="text-xs px-3 py-1.5 bg-orange-500 text-white rounded font-bold hover:bg-orange-600">Deactivate</button>
                          }
                          {u.id !== user?.id && (
                            <button onClick={() => deleteUser(u.id, u.full_name || u.email)} className="text-xs px-3 py-1.5 bg-red-100 text-red-700 border border-red-300 rounded font-bold hover:bg-red-600 hover:text-white">Delete</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── EMERGENCY CONTROLS TAB ───────────────────────────────────────── */}
        {activeTab === "controls" && (
          <div className="max-w-2xl space-y-5">

            {/* Platform Lock */}
            <div className={`p-6 rounded-lg border-2 ${platformLocked ? "bg-red-50 border-red-500" : "bg-white border-ink/10"}`}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    {platformLocked ? <Lock className="w-5 h-5 text-red-600" /> : <Unlock className="w-5 h-5 text-ink" />}
                    <h3 className="font-bold text-lg">Platform Lock</h3>
                  </div>
                  <p className="text-sm text-ink/80">
                    When locked, all users are in read-only mode. No posts, enrollments, or submissions go through.
                    Auth and admin endpoints remain operational. Reason is logged.
                  </p>
                  {platformLocked && flags.platform_locked?.reason && (
                    <p className="text-sm text-red-700 font-semibold mt-2">Reason: {flags.platform_locked.reason}</p>
                  )}
                </div>
                <button
                  onClick={togglePlatformLock}
                  className={`px-5 py-2.5 rounded font-bold text-sm whitespace-nowrap ${
                    platformLocked
                      ? "bg-green-600 text-white hover:bg-green-700"
                      : "bg-red-600 text-white hover:bg-red-700"
                  }`}
                >
                  {platformLocked ? "Unlock Platform" : "Lock Platform"}
                </button>
              </div>
            </div>

            {/* Feature Flags */}
            {FEATURES.map(f => {
              const active = !!flags[f.key]?.enabled;
              return (
                <div key={f.key} className={`p-6 rounded-lg border-2 ${active ? "bg-red-50 border-red-400" : "bg-white border-ink/10"}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Power className={`w-4 h-4 ${active ? "text-red-600" : "text-ink/80"}`} />
                        <h3 className="font-bold">{f.label}</h3>
                        {active && <span className="text-xs font-bold px-2 py-0.5 rounded bg-red-600 text-white">DISABLED</span>}
                      </div>
                      <p className="text-sm text-ink/80">{f.desc}</p>
                      {active && flags[f.key]?.reason && (
                        <p className="text-xs text-red-700 font-semibold mt-1">Reason: {flags[f.key].reason}</p>
                      )}
                    </div>
                    <button
                      onClick={() => toggleFeature(f.key, f.label)}
                      className={`px-4 py-2 rounded font-bold text-sm whitespace-nowrap ${
                        active
                          ? "bg-green-600 text-white hover:bg-green-700"
                          : "bg-red-600 text-white hover:bg-red-700"
                      }`}
                    >
                      {active ? `Re-enable ${f.label}` : `Disable ${f.label}`}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── BROADCAST TAB ─────────────────────────────────────────────────── */}
        {activeTab === "broadcast" && (
          <div className="max-w-2xl">
            <div className="bg-white border border-ink/10 rounded-lg p-6">
              <h2 className="font-bold text-lg mb-5">Send Platform Broadcast</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wide text-ink/80 mb-1">Target Audience</label>
                  <select
                    value={bcTarget}
                    onChange={e => setBcTarget(e.target.value)}
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm font-medium"
                  >
                    <option value="all">Everyone (all users)</option>
                    <option value="student">Students only</option>
                    <option value="instructor">Instructors only</option>
                    <option value="admin">Admins only</option>
                    <option value="executive_admin">Executive Admins only</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wide text-ink/80 mb-1">Title</label>
                  <input
                    value={bcTitle}
                    onChange={e => setBcTitle(e.target.value)}
                    placeholder="Platform Announcement"
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wide text-ink/80 mb-1">Message</label>
                  <textarea
                    value={bcMsg}
                    onChange={e => setBcMsg(e.target.value)}
                    placeholder="Enter your message here…"
                    rows={5}
                    className="w-full px-3 py-2.5 border border-ink/20 rounded-lg text-sm resize-vertical"
                  />
                </div>
                <button
                  onClick={sendBroadcast}
                  disabled={bcSending || !bcMsg.trim()}
                  className="px-6 py-3 bg-ink text-white rounded-lg font-bold text-sm hover:bg-ink/80 disabled:opacity-50"
                >
                  {bcSending ? "Sending…" : "Send Broadcast"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── ACCOUNT TAB ───────────────────────────────────────────────────── */}
        {activeTab === "account" && (
          <div className="bg-white border border-ink/10 rounded-lg p-6 max-w-md">
            <h2 className="font-bold text-lg mb-4 flex items-center gap-2">
              <KeyRound className="w-5 h-5" /> Change Password
            </h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (pwForm.next !== pwForm.confirm) {
                  toast.error("New passwords do not match.");
                  return;
                }
                if (pwForm.next.length < 8) {
                  toast.error("New password must be at least 8 characters.");
                  return;
                }
                setPwLoading(true);
                try {
                  await api.post("/auth/change-password", {
                    current_password: pwForm.current,
                    new_password: pwForm.next,
                  });
                  toast.success("Password updated. Use your new password next time you log in.");
                  setPwForm({ current: "", next: "", confirm: "" });
                } catch (err) {
                  toast.error(err?.response?.data?.detail || "Password change failed.");
                } finally {
                  setPwLoading(false);
                }
              }}
              className="space-y-4"
            >
              {[
                { label: "Current password", key: "current" },
                { label: "New password",     key: "next"    },
                { label: "Confirm new password", key: "confirm" },
              ].map(({ label, key }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-ink mb-1">{label}</label>
                  <input
                    type="password"
                    value={pwForm[key]}
                    onChange={e => setPwForm(f => ({ ...f, [key]: e.target.value }))}
                    required
                    className="w-full border border-ink/20 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold"
                  />
                </div>
              ))}
              <button
                type="submit"
                disabled={pwLoading}
                className="w-full bg-gold text-white font-semibold py-2 rounded-md hover:bg-gold/90 disabled:opacity-50 transition"
              >
                {pwLoading ? "Saving…" : "Update Password"}
              </button>
            </form>
          </div>
        )}

        {/* ── AUDIT LOG TAB ─────────────────────────────────────────────────── */}
        {activeTab === "audit" && (
          <div className="bg-white border border-ink/10 rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-ink/10">
              <h2 className="font-bold">Recent Platform Actions</h2>
            </div>
            <div className="divide-y divide-ink/5 max-h-[600px] overflow-y-auto">
              {loading && <p className="text-center py-8 text-ink/70">Loading…</p>}
              {!loading && auditLog.length === 0 && (
                <p className="text-center py-8 text-ink/70">No audit entries found.</p>
              )}
              {auditLog.map((entry, i) => (
                <div key={i} className="px-5 py-3 flex items-start justify-between gap-4 text-sm">
                  <div>
                    <p className="font-semibold text-ink">{entry.action || entry.event || "—"}</p>
                    {entry.actor && <p className="text-xs text-ink/80 mt-0.5">By: {entry.actor}</p>}
                    {entry.detail && typeof entry.detail === "object" && (
                      <p className="text-xs text-ink/70 mt-0.5 font-mono">
                        {JSON.stringify(entry.detail).slice(0, 120)}
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-ink/70 whitespace-nowrap">{fmtTime(entry.created_at || entry.ts)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Resolve incident modal */}
      {resolveTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Resolve Incident</h2>
            <p className="text-sm text-slate-600 mb-3">Enter a resolution note (required):</p>
            <textarea value={resolveNote} onChange={e => setResolveNote(e.target.value)} rows={3} placeholder="What was done to resolve this?" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4 resize-none focus:outline-none focus:border-green-500" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setResolveTarget(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doResolveIncident} disabled={!resolveNote.trim()} className="text-sm px-4 py-2 rounded-lg bg-green-600 text-white font-bold hover:bg-green-700 disabled:opacity-40">Resolve</button>
            </div>
          </div>
        </div>
      )}

      {/* Deactivate user modal */}
      {deactivateTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Deactivate User</h2>
            <p className="text-sm text-slate-600 mb-6">Deactivate <strong>{deactivateTarget.name}</strong>? They will lose platform access.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeactivateTarget(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doDeactivateUser} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Deactivate</button>
            </div>
          </div>
        </div>
      )}

      {/* Delete user modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Permanently Delete User</h2>
            <p className="text-sm text-slate-600 mb-6">Permanently delete <strong>{deleteTarget.name}</strong>? This cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteTarget(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doDeleteUser} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Lock platform modal */}
      {confirmLock && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Lock Platform</h2>
            <p className="text-sm text-slate-600 mb-3">Enter the reason for locking the platform (required):</p>
            <input value={lockReason} onChange={e => setLockReason(e.target.value)} placeholder="Reason…" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:border-red-400" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmLock(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={() => applyPlatformLock(true, lockReason)} disabled={!lockReason.trim()} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-40">Lock</button>
            </div>
          </div>
        </div>
      )}

      {/* Disable feature flag modal */}
      {disableFlagTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Disable {disableFlagTarget.label}</h2>
            <p className="text-sm text-slate-600 mb-3">Enter the reason for disabling {disableFlagTarget.label} (required):</p>
            <input value={disableFlagReason} onChange={e => setDisableFlagReason(e.target.value)} placeholder="Reason…" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:border-red-400" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setDisableFlagTarget(null)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={() => applyFeatureFlag(disableFlagTarget.flagKey, disableFlagTarget.label, true, disableFlagReason)} disabled={!disableFlagReason.trim()} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-40">Disable</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
