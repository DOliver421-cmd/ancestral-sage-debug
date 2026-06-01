import { useState, useEffect, useCallback, useRef } from "react";
import { RefreshCw, Search, ChevronDown, X, UserCheck, UserX, Key, Clock, Shield, Ban, BookOpen, EyeOff, Archive, RotateCcw } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";

const ROLE_RANK  = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };
const ALL_ROLES  = ["student", "instructor", "admin", "executive_admin"];
const ROLE_LABEL = { student: "Student", instructor: "Instructor", admin: "Admin", executive_admin: "Executive Admin" };
const ROLE_COLOR = {
  student:         "bg-slate-100 text-slate-600",
  instructor:      "bg-blue-50 text-blue-700",
  admin:           "bg-amber-50 text-amber-700",
  executive_admin: "bg-emerald-50 text-emerald-800",
};

function notify_toast(setToast, msg, err = false) {
  setToast({ msg, err });
  setTimeout(() => setToast(null), 4000);
}

// ── Edit User Modal ───────────────────────────────────────────────────────────
function EditUserModal({ user: target, actorRole, onSave, onClose }) {
  const [name,  setName]  = useState(target.full_name || "");
  const [email, setEmail] = useState(target.email || "");
  const [role,  setRole]  = useState(target.role || "student");
  const [pw,    setPw]    = useState("");
  const [saving, setSaving] = useState(false);
  const [err,   setErr]   = useState("");

  const isExec = actorRole === "executive_admin";

  async function handleSave() {
    setSaving(true); setErr("");
    try {
      await api.patch(`/admin/users/${target.id}`, { full_name: name.trim(), email: email.trim() });
      if (role !== target.role) {
        await api.patch(`/admin/users/${target.id}/role`, { role });
      }
      if (pw.trim()) {
        await api.post(`/admin/users/${target.id}/password`, { new_password: pw.trim() });
      }
      onSave({ ...target, full_name: name.trim(), email: email.trim(), role });
    } catch (e) {
      setErr(e?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  // Only exec can set executive_admin role; non-exec cannot touch exec accounts
  const availableRoles = isExec
    ? ALL_ROLES
    : ALL_ROLES.filter(r => r !== "executive_admin" && ROLE_RANK[target.role] < 4);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="font-heading font-bold text-lg text-slate-900">Edit User</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-5 space-y-4">
          {err && <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-2">{err}</div>}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">Full Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">Email Address</label>
            <input value={email} onChange={e => setEmail(e.target.value)} type="email"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">Role</label>
            <select value={role} onChange={e => setRole(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper bg-white">
              {availableRoles.map(r => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
            {!isExec && target.role === "executive_admin" && (
              <p className="text-xs text-red-600 mt-1">Only Executive Admin can modify other exec accounts.</p>
            )}
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">New Password <span className="font-normal normal-case">(leave blank to keep current)</span></label>
            <input value={pw} onChange={e => setPw(e.target.value)} type="password" placeholder="••••••••"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
          </div>
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
          <button onClick={handleSave} disabled={saving}
            className="text-sm px-5 py-2 rounded-lg bg-ink text-white font-bold hover:bg-ink/90 disabled:opacity-50">
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── User Sessions Modal ───────────────────────────────────────────────────────
function SessionsModal({ user: target, onClose, onForceLogout }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    api.get(`/admin/users/${target.id}/sessions`)
      .then(r => setSessions(r.data.sessions || []))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, [target.id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h2 className="font-heading font-bold text-lg text-slate-900">Active Sessions</h2>
            <p className="text-xs text-slate-400 mt-0.5">{target.full_name} · {target.email}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-4 max-h-80 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-slate-400 py-4 text-center">Loading sessions…</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">No active sessions found.</p>
          ) : sessions.map(s => (
            <div key={s.session_id} className="flex items-start gap-3 py-3 border-b border-slate-50 last:border-0">
              <Clock className="w-4 h-4 text-slate-300 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-slate-600 truncate">{s.user_agent || "Unknown browser"}</p>
                <p className="text-xs text-slate-400 mt-0.5">IP: {s.ip || "—"} · Last seen: {s.last_seen ? new Date(s.last_seen).toLocaleString() : "—"}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Close</button>
          {sessions.length > 0 && (
            <button onClick={() => { onForceLogout(); onClose(); }}
              className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">
              Force Logout All
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── User Audit Modal ──────────────────────────────────────────────────────────
function UserAuditModal({ user: target, onClose }) {
  const [log, setLog]       = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/admin/users/${target.id}/audit?limit=50`)
      .then(r => setLog(Array.isArray(r.data) ? r.data : []))
      .catch(() => setLog([]))
      .finally(() => setLoading(false));
  }, [target.id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h2 className="font-heading font-bold text-lg text-slate-900">Activity History</h2>
            <p className="text-xs text-slate-400 mt-0.5">{target.full_name} · {target.email}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-2 max-h-96 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-slate-400 py-8 text-center">Loading…</p>
          ) : log.length === 0 ? (
            <p className="text-sm text-slate-400 py-8 text-center">No activity found.</p>
          ) : log.map((a, i) => (
            <div key={i} className="flex items-start gap-3 py-2.5 border-b border-slate-50 last:border-0">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-amber-700 truncate">{a.action}</p>
                <p className="text-xs text-slate-400 mt-0.5">{a.at ? new Date(a.at).toLocaleString() : "—"}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-end px-6 py-4 border-t border-slate-100">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Close</button>
        </div>
      </div>
    </div>
  );
}

// ── Ban User Modal ────────────────────────────────────────────────────────────
function BanModal({ user: target, onBan, onClose }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function handleBan() {
    if (reason.trim().length < 5) { setErr("Reason must be at least 5 characters."); return; }
    setBusy(true); setErr("");
    try {
      await api.post(`/admin/users/${target.id}/ban`, { reason: reason.trim() });
      onBan(target.id);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Ban failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Ban className="w-4 h-4 text-red-600" />
            <h2 className="font-heading font-bold text-lg text-slate-900">Permanently Ban User</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-800">
            <strong>{target.full_name}</strong> ({target.email}) will be permanently banned.
            Their account will be deactivated and all sessions killed immediately.
          </div>
          {err && <div className="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-2">{err}</div>}
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">Ban Reason <span className="font-normal normal-case text-red-500">*required</span></label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              placeholder="Document the specific reason for this ban…"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
              autoFocus
            />
          </div>
        </div>
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-100">
          <button onClick={onClose} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
          <button onClick={handleBan} disabled={busy || reason.trim().length < 5}
            className="flex items-center gap-2 text-sm px-5 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-50">
            <Ban className="w-4 h-4" />
            {busy ? "Banning…" : "Confirm Ban"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Bulk Action Bar ───────────────────────────────────────────────────────────
function BulkBar({ selected, onBulk, onClear }) {
  const [newRole, setNewRole] = useState("instructor");
  return (
    <div className="flex items-center gap-3 flex-wrap bg-ink text-white px-5 py-3 rounded-xl mb-4">
      <span className="text-sm font-bold">{selected.length} selected</span>
      <div className="flex items-center gap-2 ml-auto flex-wrap">
        <select value={newRole} onChange={e => setNewRole(e.target.value)}
          className="text-xs bg-white/10 border border-white/20 rounded-lg px-2 py-1.5 text-white outline-none">
          {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
        </select>
        <button onClick={() => onBulk("role", newRole)}
          className="text-xs font-bold px-3 py-1.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600">Set Role</button>
        <button onClick={() => onBulk("suspend")}
          className="text-xs font-bold px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600">Suspend All</button>
        <button onClick={() => onBulk("unsuspend")}
          className="text-xs font-bold px-3 py-1.5 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600">Unsuspend All</button>
        <button onClick={onClear} className="text-xs px-3 py-1.5 bg-white/10 rounded-lg hover:bg-white/20">Clear</button>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function AdminDashboard() {
  const { user }            = useAuth();
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers]   = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [auditLog, setAuditLog]   = useState([]);
  const [stats, setStats]         = useState(null);
  const [loading, setLoading]     = useState(true);
  const [toast, setToast]         = useState(null);

  // User management state
  const [search,     setSearch]     = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selected,   setSelected]   = useState([]);
  const [editing,    setEditing]    = useState(null);
  const [viewSessions, setViewSessions] = useState(null);
  const [viewAudit,  setViewAudit]  = useState(null);
  const [banTarget,  setBanTarget]  = useState(null);
  const [courses,    setCourses]    = useState([]);
  const [coursesLoading, setCoursesLoading] = useState(false);
  const [courseStatusFilter, setCourseStatusFilter] = useState("published");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 50;

  // Audit filters
  const [auditAction, setAuditAction] = useState("");
  const [auditActor,  setAuditActor]  = useState("");
  const [auditLimit,  setAuditLimit]  = useState(100);

  const isExec = user?.role === "executive_admin";
  const canAdmin = ["admin", "executive_admin"].includes(user?.role);

  const notify = (msg, err = false) => notify_toast(setToast, msg, err);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [usrR, incR, stR] = await Promise.allSettled([
        api.get("/admin/users"),
        api.get("/incidents"),
        api.get("/admin/stats"),
      ]);
      if (usrR.status === "fulfilled") setUsers(Array.isArray(usrR.value.data) ? usrR.value.data : []);
      if (incR.status === "fulfilled") setIncidents(Array.isArray(incR.value.data) ? incR.value.data : []);
      if (stR.status  === "fulfilled") setStats(stR.value.data);
    } finally { setLoading(false); }
  }, []);

  const loadAudit = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: String(auditLimit) });
      if (auditAction.trim()) params.set("action", auditAction.trim());
      if (auditActor.trim())  params.set("actor_id", auditActor.trim());
      const r = await api.get(`/admin/audit?${params}`);
      setAuditLog(Array.isArray(r.data) ? r.data : []);
    } catch { setAuditLog([]); }
  }, [auditAction, auditActor, auditLimit]);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => { if (activeTab === "audit") loadAudit(); }, [activeTab, loadAudit]);
  useEffect(() => { if (activeTab === "courses") loadCourses(); }, [activeTab, courseStatusFilter]);

  // ── Filtered user list ──────────────────────────────────────────────────────
  const filteredUsers = users.filter(u => {
    const q = search.toLowerCase();
    if (q && !`${u.full_name} ${u.email} ${u.id} ${u.role}`.toLowerCase().includes(q)) return false;
    if (roleFilter !== "all" && u.role !== roleFilter) return false;
    if (statusFilter === "active"   && u.is_active === false) return false;
    if (statusFilter === "inactive" && u.is_active !== false) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE));
  const pagedUsers = filteredUsers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [search, roleFilter, statusFilter]);

  // ── User actions ────────────────────────────────────────────────────────────
  async function toggleActive(u) {
    const next = u.is_active === false;
    try {
      await api.patch(`/admin/users/${u.id}/active`, { is_active: next });
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, is_active: next } : x));
      notify(`${u.full_name} ${next ? "reactivated" : "deactivated"}`);
    } catch (e) { notify(e?.response?.data?.detail || "Failed", true); }
  }

  async function forceLogout(uid, name) {
    try {
      await api.delete(`/admin/users/${uid}/sessions`);
      notify(`${name} force-logged out`);
    } catch (e) { notify(e?.response?.data?.detail || "Failed", true); }
  }

  async function sendResetLink(u) {
    try {
      const r = await api.post(`/admin/users/${u.id}/reset-link`);
      const link = r.data?.reset_link || r.data?.link || "(no link returned)";
      window.prompt(`Password reset link for ${u.email}:`, link);
    } catch (e) { notify(e?.response?.data?.detail || "Failed", true); }
  }

  async function deleteUser(u) {
    if (!window.confirm(`Permanently delete ${u.full_name}? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/users/${u.id}`);
      setUsers(prev => prev.filter(x => x.id !== u.id));
      notify(`${u.full_name} deleted`);
    } catch (e) { notify(e?.response?.data?.detail || "Failed", true); }
  }

  async function handleBulk(action, role) {
    if (!selected.length) return;
    const confirm_msg = action === "role"
      ? `Set ${selected.length} users to ${ROLE_LABEL[role]}?`
      : action === "suspend"
        ? `Suspend ${selected.length} users?`
        : `Unsuspend ${selected.length} users?`;
    if (!window.confirm(confirm_msg)) return;
    try {
      const body = { action, uids: selected, ...(action === "role" ? { role } : {}) };
      const r = await api.post("/admin/users/bulk", body);
      notify(`Bulk ${action}: ${(r.data.ok || []).length} ok, ${(r.data.err || []).length} errors`);
      setSelected([]);
      loadAll();
    } catch (e) { notify(e?.response?.data?.detail || "Bulk action failed", true); }
  }

  async function banUser(uid) {
    setUsers(prev => prev.map(u => u.id === uid ? { ...u, is_active: false, banned: true } : u));
    setBanTarget(null);
    notify("User banned.");
  }

  async function unbanUser(u) {
    if (!window.confirm(`Remove ban for ${u.full_name} and reactivate their account?`)) return;
    try {
      await api.post(`/admin/users/${u.id}/unban`);
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, is_active: true, banned: false, ban_reason: undefined } : x));
      notify(`${u.full_name} unbanned.`);
    } catch (e) { notify(e?.response?.data?.detail || "Unban failed.", true); }
  }

  async function loadCourses() {
    setCoursesLoading(true);
    try {
      const { data } = await api.get(`/admin/courses${courseStatusFilter ? `?status=${courseStatusFilter}` : ""}`);
      setCourses(data.courses || []);
    } catch { notify("Could not load courses.", true); }
    finally { setCoursesLoading(false); }
  }

  async function moderateCourse(course, action) {
    const reason = window.prompt(`Reason for ${action}ing "${course.title}"? (optional)`);
    if (reason === null) return;
    try {
      await api.post(`/admin/courses/${course.course_id}/moderate`, { action, reason: reason.trim() });
      notify(`Course ${action}d.`);
      loadCourses();
    } catch (e) { notify(e?.response?.data?.detail || "Moderation failed.", true); }
  }

  async function resolveIncident(iid) {
    const resolution = window.prompt("Enter resolution note:");
    if (!resolution) return;
    try {
      await api.post(`/incidents/${iid}/resolve`, { resolution });
      notify("Incident resolved");
      setIncidents(prev => prev.map(i => i.id === iid ? { ...i, status: "resolved", resolution } : i));
    } catch (e) { notify(e?.response?.data?.detail || "Failed", true); }
  }

  function toggleSelect(uid) {
    setSelected(prev => prev.includes(uid) ? prev.filter(id => id !== uid) : [...prev, uid]);
  }
  function toggleSelectAll() {
    const visIds = filteredUsers.map(u => u.id);
    const allSelected = visIds.every(id => selected.includes(id));
    setSelected(allSelected ? selected.filter(id => !visIds.includes(id)) : [...new Set([...selected, ...visIds])]);
  }

  const canEditUser = (target) => {
    if (!canAdmin) return false;
    if (target.role === "executive_admin" && !isExec) return false;
    return true;
  };

  return (
    <AppShell>
      <div className="min-h-screen bg-bone">
        {/* Header */}
        <div className="bg-ink text-white px-6 lg:px-10 py-6 border-b border-white/10">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-xs font-bold uppercase tracking-widest text-white/50 mb-1">Admin</div>
              <h1 className="font-heading text-2xl font-extrabold">Governance Dashboard</h1>
              <p className="text-sm text-white/60 mt-1">
                {stats ? `${stats.users ?? users.length} users · ${stats.incidents_open ?? incidents.filter(i=>i.status==="open").length} open incidents` : `${users.length} users loaded`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isExec && (
                <a href="/supervisor" className="flex items-center gap-2 px-4 py-2 bg-emerald-700/30 hover:bg-emerald-700/50 text-emerald-300 text-sm font-bold rounded-lg transition-colors">
                  <Shield className="w-4 h-4" /> Supervisor Panel
                </a>
              )}
              <button onClick={loadAll} disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-sm font-bold rounded-lg transition-colors disabled:opacity-40">
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>
          </div>
        </div>

        {toast && (
          <div className={`px-6 py-3 text-sm font-medium ${toast.err ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"}`}>
            {toast.msg}
          </div>
        )}

        {/* Modals */}
        {editing    && <EditUserModal user={editing} actorRole={user?.role} onSave={(updated) => { setUsers(prev => prev.map(u => u.id === updated.id ? updated : u)); setEditing(null); notify("User updated"); }} onClose={() => setEditing(null)} />}
        {viewSessions && <SessionsModal user={viewSessions} onClose={() => setViewSessions(null)} onForceLogout={() => forceLogout(viewSessions.id, viewSessions.full_name)} />}
        {viewAudit  && <UserAuditModal user={viewAudit} onClose={() => setViewAudit(null)} />}
        {banTarget  && <BanModal user={banTarget} onBan={banUser} onClose={() => setBanTarget(null)} />}

        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-6">
          {/* Tabs */}
          <div className="flex gap-6 border-b border-ink/10 mb-6">
            {[
              { key: "users",     label: `Users (${users.length})` },
              { key: "incidents", label: `Incidents (${incidents.filter(i=>i.status==="open").length} open)` },
              { key: "courses",   label: "Course Moderation" },
              { key: "audit",     label: "Audit Log" },
            ].map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)}
                className={`pb-3 text-sm font-bold border-b-2 transition-colors ${activeTab === t.key ? "border-copper text-copper" : "border-transparent text-ink/80 hover:text-ink"}`}>
                {t.label}
              </button>
            ))}
          </div>

          {/* ── USERS TAB ── */}
          {activeTab === "users" && (
            <div>
              {/* Search + Filters */}
              <div className="flex flex-wrap gap-3 mb-4">
                <div className="relative flex-1 min-w-52">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, email, ID, or role…"
                    className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
                </div>
                <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none bg-white">
                  <option value="all">All Roles</option>
                  {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                </select>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none bg-white">
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* Bulk bar */}
              {selected.length > 0 && isExec && (
                <BulkBar selected={selected} onBulk={handleBulk} onClear={() => setSelected([])} />
              )}

              {/* Table */}
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <div style={{ maxHeight: 560, overflowY: "auto" }}>
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-white z-10">
                        <tr className="border-b-2 border-slate-100">
                          {isExec && (
                            <th className="py-3 px-4 w-10">
                              <input type="checkbox" onChange={toggleSelectAll}
                                checked={filteredUsers.length > 0 && filteredUsers.every(u => selected.includes(u.id))}
                                className="rounded border-slate-300" />
                            </th>
                          )}
                          <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Name</th>
                          <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Email</th>
                          <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Role</th>
                          <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Status</th>
                          <th className="py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {loading ? (
                          <tr><td colSpan={isExec?6:5} className="py-10 text-center text-slate-400 text-sm">Loading…</td></tr>
                        ) : filteredUsers.length === 0 ? (
                          <tr><td colSpan={isExec?6:5} className="py-10 text-center text-slate-400 text-sm">No users match your filters.</td></tr>
                        ) : pagedUsers.map(u => (
                          <tr key={u.id} className={`border-b border-slate-50 hover:bg-slate-50 ${selected.includes(u.id) ? "bg-amber-50/40" : ""}`}>
                            {isExec && (
                              <td className="py-3 px-4">
                                {u.id !== user?.id && (
                                  <input type="checkbox" checked={selected.includes(u.id)} onChange={() => toggleSelect(u.id)}
                                    className="rounded border-slate-300" />
                                )}
                              </td>
                            )}
                            <td className="py-3 px-4">
                              <div className="font-heading font-bold text-slate-900">{u.full_name || "—"}</div>
                              <div className="text-xs text-slate-400 font-mono mt-0.5">{u.id}</div>
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-600 text-xs">{u.email}</td>
                            <td className="py-3 px-4">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ROLE_COLOR[u.role] || "bg-slate-100 text-slate-600"}`}>
                                {ROLE_LABEL[u.role] || u.role}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              {u.banned
                                ? <span className="text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full" title={u.ban_reason}>Banned</span>
                                : u.is_active === false
                                ? <span className="text-xs font-bold bg-red-50 text-red-600 px-2 py-0.5 rounded-full">Inactive</span>
                                : <span className="text-xs font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">Active</span>}
                              {u.elevated_until && new Date(u.elevated_until) > new Date() && (
                                <span className="ml-1 text-xs font-bold bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">Elevated</span>
                              )}
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex items-center justify-end gap-1.5 flex-wrap">
                                {canEditUser(u) && (
                                  <button onClick={() => setEditing(u)}
                                    className="text-xs font-bold px-2 py-1 border border-blue-200 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                    Edit
                                  </button>
                                )}
                                {canEditUser(u) && (
                                  <button onClick={() => sendResetLink(u)}
                                    className="text-xs font-bold px-2 py-1 border border-amber-200 text-amber-700 hover:bg-amber-50 rounded-lg transition-colors">
                                    <Key className="w-3 h-3 inline mr-0.5" />Reset Link
                                  </button>
                                )}
                                {isExec && (
                                  <button onClick={() => setViewSessions(u)}
                                    className="text-xs font-bold px-2 py-1 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                                    <Clock className="w-3 h-3 inline mr-0.5" />Sessions
                                  </button>
                                )}
                                {canEditUser(u) && (
                                  <button onClick={() => setViewAudit(u)}
                                    className="text-xs font-bold px-2 py-1 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                                    History
                                  </button>
                                )}
                                {canEditUser(u) && u.id !== user?.id && (
                                  <button onClick={() => toggleActive(u)}
                                    className={`text-xs font-bold px-2 py-1 border rounded-lg transition-colors ${
                                      u.is_active === false
                                        ? "border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                                        : "border-red-300 text-red-500 hover:bg-red-50"
                                    }`}>
                                    {u.is_active === false ? <><UserCheck className="w-3 h-3 inline mr-0.5" />Activate</> : <><UserX className="w-3 h-3 inline mr-0.5" />Deactivate</>}
                                  </button>
                                )}
                                {isExec && u.id !== user?.id && (
                                  <button onClick={() => { if(window.confirm(`Force logout ${u.full_name}?`)) forceLogout(u.id, u.full_name); }}
                                    className="text-xs font-bold px-2 py-1 border border-orange-200 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">
                                    Logout
                                  </button>
                                )}
                                {isExec && u.id !== user?.id && u.role !== "executive_admin" && (
                                  u.banned ? (
                                    <button onClick={() => unbanUser(u)}
                                      className="text-xs font-bold px-2 py-1 border border-emerald-300 text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors">
                                      Unban
                                    </button>
                                  ) : (
                                    <button onClick={() => setBanTarget(u)}
                                      className="flex items-center gap-0.5 text-xs font-bold px-2 py-1 border border-red-400 text-red-700 hover:bg-red-50 rounded-lg transition-colors">
                                      <Ban className="w-3 h-3" />Ban
                                    </button>
                                  )
                                )}
                                {isExec && u.id !== user?.id && u.role !== "executive_admin" && (
                                  <button onClick={() => deleteUser(u)}
                                    className="text-xs font-bold px-2 py-1 border border-red-300 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                                    Delete
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="px-4 py-2 border-t border-slate-100 flex items-center justify-between gap-4 flex-wrap">
                  <span className="text-xs text-slate-400">
                    {filteredUsers.length} of {users.length} users{selected.length > 0 ? ` · ${selected.length} selected` : ""}
                    {totalPages > 1 && ` · page ${page} of ${totalPages}`}
                  </span>
                  {totalPages > 1 && (
                    <div className="flex items-center gap-1">
                      <button onClick={() => setPage(1)} disabled={page === 1}
                        className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40">«</button>
                      <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                        className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40">‹</button>
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        const start = Math.max(1, Math.min(page - 2, totalPages - 4));
                        const pg = start + i;
                        return pg <= totalPages ? (
                          <button key={pg} onClick={() => setPage(pg)}
                            className={`text-xs px-2.5 py-1 border rounded ${pg === page ? "bg-ink text-white border-ink" : "border-slate-200 hover:bg-slate-50"}`}>
                            {pg}
                          </button>
                        ) : null;
                      })}
                      <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                        className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40">›</button>
                      <button onClick={() => setPage(totalPages)} disabled={page === totalPages}
                        className="text-xs px-2 py-1 border border-slate-200 rounded hover:bg-slate-50 disabled:opacity-40">»</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ── INCIDENTS TAB ── */}
          {activeTab === "incidents" && (
            <div className="space-y-3">
              {loading ? (
                <div className="py-10 text-center text-ink/70 text-sm">Loading…</div>
              ) : incidents.length === 0 ? (
                <div className="py-10 text-center text-ink/70 text-sm">No incidents found.</div>
              ) : incidents.map(inc => (
                <div key={inc.id} className={`bg-white border-l-4 rounded-xl p-5 shadow-sm ${
                  inc.severity === "critical" ? "border-red-500" :
                  inc.severity === "high"     ? "border-orange-400" :
                  inc.severity === "medium"   ? "border-yellow-400" : "border-slate-300"
                }`}>
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
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
                    {canAdmin && inc.status === "open" && (
                      <button onClick={() => resolveIncident(inc.id)}
                        className="text-xs font-bold px-3 py-1.5 rounded-lg border border-emerald-400 text-emerald-700 hover:bg-emerald-50 transition-colors whitespace-nowrap">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── COURSES TAB ── */}
          {activeTab === "courses" && (
            <div>
              <div className="flex items-center gap-3 mb-4 flex-wrap">
                <select value={courseStatusFilter} onChange={e => setCourseStatusFilter(e.target.value)}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none">
                  <option value="">All Statuses</option>
                  <option value="published">Published</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </select>
                <button onClick={loadCourses} disabled={coursesLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-ink text-white text-sm font-bold rounded-lg hover:bg-ink/90 disabled:opacity-40">
                  <RefreshCw className={`w-4 h-4 ${coursesLoading ? "animate-spin" : ""}`} /> Refresh
                </button>
                <span className="text-xs text-ink/40 ml-auto">{courses.length} courses shown</span>
              </div>
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                <div style={{ maxHeight: 560, overflowY: "auto" }}>
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-white z-10">
                      <tr className="border-b-2 border-slate-100">
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Course</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Creator</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Status</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Price</th>
                        <th className="py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {coursesLoading ? (
                        <tr><td colSpan={5} className="py-10 text-center text-slate-400 text-sm">Loading…</td></tr>
                      ) : courses.length === 0 ? (
                        <tr><td colSpan={5} className="py-10 text-center text-slate-400 text-sm">No courses found.</td></tr>
                      ) : courses.map(c => (
                        <tr key={c.course_id} className="border-b border-slate-50 hover:bg-slate-50">
                          <td className="py-3 px-4">
                            <div className="font-heading font-bold text-slate-900 text-sm">{c.title}</div>
                            <div className="text-xs text-slate-400 mt-0.5">{c.category} · {c.enrollment_count || 0} enrolled</div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="text-xs font-medium text-slate-700">{c.creator_name}</div>
                            <div className="text-xs text-slate-400 font-mono">{c.creator_email}</div>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                              c.status === "published" ? "bg-green-100 text-green-700" :
                              c.status === "draft" ? "bg-slate-100 text-slate-600" :
                              "bg-red-100 text-red-600"
                            }`}>{c.status}</span>
                            {c.moderated_by && (
                              <div className="text-xs text-red-400 mt-0.5">Moderated</div>
                            )}
                          </td>
                          <td className="py-3 px-4 text-sm text-slate-700">
                            {c.price_cents === 0 ? "Free" : `$${(c.price_cents / 100).toFixed(2)}`}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center justify-end gap-1.5">
                              {c.status === "published" && (
                                <button onClick={() => moderateCourse(c, "unpublish")}
                                  className="flex items-center gap-1 text-xs font-bold px-2 py-1 border border-amber-300 text-amber-700 hover:bg-amber-50 rounded-lg transition-colors">
                                  <EyeOff className="w-3 h-3" />Unpublish
                                </button>
                              )}
                              {c.status !== "archived" && (
                                <button onClick={() => moderateCourse(c, "archive")}
                                  className="flex items-center gap-1 text-xs font-bold px-2 py-1 border border-red-300 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                                  <Archive className="w-3 h-3" />Archive
                                </button>
                              )}
                              {c.status === "archived" && (
                                <button onClick={() => moderateCourse(c, "restore")}
                                  className="flex items-center gap-1 text-xs font-bold px-2 py-1 border border-green-300 text-green-700 hover:bg-green-50 rounded-lg transition-colors">
                                  <RotateCcw className="w-3 h-3" />Restore
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── AUDIT LOG TAB ── */}
          {activeTab === "audit" && (
            <div>
              <div className="flex flex-wrap gap-3 mb-4">
                <input value={auditAction} onChange={e => setAuditAction(e.target.value)} placeholder="Filter by action (regex)…"
                  className="flex-1 min-w-40 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
                <input value={auditActor} onChange={e => setAuditActor(e.target.value)} placeholder="Actor ID…"
                  className="w-52 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper" />
                <select value={auditLimit} onChange={e => setAuditLimit(Number(e.target.value))}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none">
                  {[50,100,200,500].map(n => <option key={n} value={n}>Last {n}</option>)}
                </select>
                <button onClick={loadAudit} className="px-4 py-2 bg-ink text-white text-sm font-bold rounded-lg hover:bg-ink/90">Search</button>
                {isExec && (
                  <a href={`/api/admin/audit/export?format=csv&limit=1000${auditAction?`&action=${encodeURIComponent(auditAction)}`:""}`}
                    className="px-4 py-2 bg-emerald-700 text-white text-sm font-bold rounded-lg hover:bg-emerald-800">
                    Export CSV
                  </a>
                )}
              </div>
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                <div style={{ maxHeight: 520, overflowY: "auto" }}>
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-white">
                      <tr className="border-b-2 border-slate-100">
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Time</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Actor</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Action</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-wider text-slate-600 font-bold">Target</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLog.length === 0 ? (
                        <tr><td colSpan={4} className="py-8 text-center text-slate-400 text-sm">No audit entries. Click Search to load.</td></tr>
                      ) : auditLog.map((a, i) => (
                        <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
                          <td className="py-2.5 px-4 text-xs text-slate-400 whitespace-nowrap">{a.at ? new Date(a.at).toLocaleString() : "—"}</td>
                          <td className="py-2.5 px-4 text-slate-700 font-medium text-xs">{a.actor_name || a.actor_id || "—"}</td>
                          <td className="py-2.5 px-4 font-mono text-xs text-amber-700">{a.action}</td>
                          <td className="py-2.5 px-4 text-xs text-slate-400 font-mono">{a.target_id || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="px-4 py-2 border-t border-slate-100 text-xs text-slate-400">{auditLog.length} entries</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
