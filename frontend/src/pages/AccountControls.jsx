import { useState, useEffect, useCallback, useRef } from "react";
import { Search, RefreshCw, UserCheck, UserX, Key, Shield, Ban, LogOut, Eye, EyeOff, Copy, CheckCircle, AlertTriangle, X, ChevronRight, Users } from "lucide-react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

const ROLE_RANK  = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };
const ALL_ROLES  = ["student", "instructor", "admin", "executive_admin"];
const ROLE_LABEL = { student: "Student", instructor: "Instructor", admin: "Admin", executive_admin: "Exec Admin" };
const ROLE_COLOR = {
  student:         "bg-slate-100 text-slate-700",
  instructor:      "bg-blue-100 text-blue-700",
  admin:           "bg-amber-100 text-amber-700",
  executive_admin: "bg-emerald-100 text-emerald-800",
};

function toast_msg(setMsg, text, isErr = false) {
  setMsg({ text, isErr });
  setTimeout(() => setMsg(null), 4000);
}

// ── Right-side Account Control Panel ─────────────────────────────────────────
function ControlPanel({ user: target, actorRole, onUpdated, onDeleted }) {
  const isExec = actorRole === "executive_admin";
  const isSelf = false; // panel is always for another user

  // Identity fields
  const [name,  setName]  = useState(target.full_name || "");
  const [email, setEmail] = useState(target.email || "");
  const [assoc, setAssoc] = useState(target.associate || "");
  const [role,  setRole]  = useState(target.role || "student");

  // Password
  const [newPw,   setNewPw]   = useState("");
  const [showPw,  setShowPw]  = useState(false);
  const [pwLink,  setPwLink]  = useState(null);
  const [copied,  setCopied]  = useState(false);

  const [saving, setSaving] = useState(false);
  const [msg,    setMsg]    = useState(null);
  const [banReason, setBanReason] = useState("");
  const [confirmBan, setConfirmBan] = useState(false);
  const [confirmUnban, setConfirmUnban] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Sync when target changes
  useEffect(() => {
    setName(target.full_name || "");
    setEmail(target.email || "");
    setAssoc(target.associate || "");
    setRole(target.role || "student");
    setNewPw("");
    setPwLink(null);
    setCopied(false);
    setMsg(null);
  }, [target.id]);

  const notify = (text, isErr = false) => toast_msg(setMsg, text, isErr);

  const canEdit = isExec || target.role !== "executive_admin";
  const availableRoles = isExec
    ? ALL_ROLES
    : ALL_ROLES.filter(r => r !== "executive_admin" && ROLE_RANK[target.role] < 4);

  async function saveIdentity() {
    if (!name.trim()) { notify("Name cannot be empty", true); return; }
    if (!email.trim()) { notify("Email cannot be empty", true); return; }
    setSaving(true);
    try {
      await api.patch(`/admin/users/${target.id}`, {
        full_name: name.trim(),
        email: email.trim().toLowerCase(),
        ...(assoc.trim() ? { associate: assoc.trim() } : { associate: null }),
      });
      if (role !== target.role) {
        await api.patch(`/admin/users/${target.id}/role`, { role });
      }
      if (newPw.trim()) {
        if (newPw.trim().length < 8) { notify("Password must be at least 8 characters", true); setSaving(false); return; }
        await api.post(`/admin/users/${target.id}/password`, { new_password: newPw.trim() });
        setNewPw("");
      }
      onUpdated({ ...target, full_name: name.trim(), email: email.trim().toLowerCase(), role, associate: assoc.trim() || null });
      notify("Account updated");
    } catch (e) {
      notify(e?.response?.data?.detail || "Save failed", true);
    } finally { setSaving(false); }
  }

  async function generateResetLink() {
    setSaving(true);
    try {
      const r = await api.post(`/admin/users/${target.id}/reset-link`);
      setPwLink(r.data.reset_url || r.data.link || JSON.stringify(r.data));
    } catch (e) {
      notify(e?.response?.data?.detail || "Could not generate link", true);
    } finally { setSaving(false); }
  }

  async function copyLink() {
    if (!pwLink) return;
    try { await navigator.clipboard.writeText(pwLink); } catch { /* fallback */ }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function toggleActive() {
    setSaving(true);
    const next = target.is_active === false;
    try {
      await api.patch(`/admin/users/${target.id}/active`, { is_active: next });
      onUpdated({ ...target, is_active: next });
      notify(`${target.full_name || target.email} ${next ? "activated" : "deactivated"}`);
    } catch (e) {
      notify(e?.response?.data?.detail || "Failed", true);
    } finally { setSaving(false); }
  }

  async function banUser() {
    setBanReason("");
    setConfirmBan(true);
  }

  async function doBanUser() {
    const reason = banReason;
    setConfirmBan(false);
    if (!reason || reason.trim().length < 5) { notify("Ban reason is required (min 5 chars)", true); return; }
    setSaving(true);
    try {
      await api.post(`/admin/users/${target.id}/ban`, { reason: reason.trim() });
      onUpdated({ ...target, is_active: false, banned: true, ban_reason: reason.trim() });
      notify(`${target.full_name || target.email} banned`);
    } catch (e) {
      notify(e?.response?.data?.detail || "Ban failed", true);
    } finally { setSaving(false); }
  }

  async function unbanUser() {
    setConfirmUnban(true);
  }

  async function doUnbanUser() {
    setConfirmUnban(false);
    setSaving(true);
    try {
      await api.post(`/admin/users/${target.id}/unban`);
      onUpdated({ ...target, is_active: true, banned: false, ban_reason: undefined });
      notify(`${target.full_name || target.email} unbanned`);
    } catch (e) {
      notify(e?.response?.data?.detail || "Unban failed", true);
    } finally { setSaving(false); }
  }

  async function forceLogout() {
    setConfirmLogout(true);
  }

  async function doForceLogout() {
    setConfirmLogout(false);
    setSaving(true);
    try {
      await api.delete(`/admin/users/${target.id}/sessions`);
      notify(`${target.full_name || target.email} logged out from all devices`);
    } catch (e) {
      notify(e?.response?.data?.detail || "Failed", true);
    } finally { setSaving(false); }
  }

  async function deleteUser() {
    setConfirmDelete(true);
  }

  async function doDeleteUser() {
    setConfirmDelete(false);
    setSaving(true);
    try {
      await api.delete(`/admin/users/${target.id}`);
      onDeleted(target.id);
      notify(`${target.full_name || target.email} deleted`);
    } catch (e) {
      notify(e?.response?.data?.detail || "Delete failed", true);
    } finally { setSaving(false); }
  }

  const isBanned = !!target.banned;
  const isInactive = target.is_active === false;
  const targetIsExec = target.role === "executive_admin";

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60 flex-shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-heading font-extrabold text-lg text-slate-900">{target.full_name || "—"}</h2>
            <p className="text-xs font-mono text-slate-500 mt-0.5">{target.email}</p>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ROLE_COLOR[target.role] || "bg-slate-100 text-slate-600"}`}>
                {ROLE_LABEL[target.role] || target.role}
              </span>
              {isBanned && (
                <span className="text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full" title={target.ban_reason}>Banned</span>
              )}
              {!isBanned && isInactive && (
                <span className="text-xs font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">Inactive</span>
              )}
              {!isBanned && !isInactive && (
                <span className="text-xs font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Active</span>
              )}
            </div>
          </div>
          <div className="text-xs text-slate-400 text-right flex-shrink-0">
            <div>ID</div>
            <div className="font-mono text-slate-300 text-[10px] max-w-[120px] truncate" title={target.id}>{target.id}</div>
          </div>
        </div>
      </div>

      {/* Toast */}
      {msg && (
        <div className={`px-6 py-2.5 text-sm font-medium flex items-center gap-2 border-b flex-shrink-0 ${
          msg.isErr ? "bg-red-50 text-red-700 border-red-100" : "bg-emerald-50 text-emerald-700 border-emerald-100"
        }`}>
          {msg.isErr ? <AlertTriangle className="w-4 h-4 flex-shrink-0" /> : <CheckCircle className="w-4 h-4 flex-shrink-0" />}
          {msg.text}
        </div>
      )}

      {!canEdit && (
        <div className="px-6 py-3 bg-amber-50 border-b border-amber-100 text-xs text-amber-800 font-medium flex-shrink-0">
          Only Executive Admins can modify other Executive Admin accounts.
        </div>
      )}

      {/* Scrollable control body */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

        {/* ── Section 1: Identity ── */}
        <section>
          <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Identity</div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Full Name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                disabled={!canEdit}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400 disabled:bg-slate-50 disabled:text-slate-400"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                disabled={!canEdit}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono text-slate-800 focus:outline-none focus:border-amber-400 disabled:bg-slate-50 disabled:text-slate-400"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Cohort / Associate</label>
              <input
                value={assoc}
                onChange={e => setAssoc(e.target.value)}
                disabled={!canEdit}
                placeholder="e.g. Associate-Alpha"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400 disabled:bg-slate-50 disabled:text-slate-400"
              />
            </div>
          </div>
        </section>

        {/* ── Section 2: Role ── */}
        <section>
          <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Role</div>
          <select
            value={role}
            onChange={e => setRole(e.target.value)}
            disabled={!canEdit}
            className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400 disabled:bg-slate-50 disabled:text-slate-400 bg-white"
          >
            {availableRoles.map(r => (
              <option key={r} value={r}>{ROLE_LABEL[r]}</option>
            ))}
          </select>
          {!isExec && targetIsExec && (
            <p className="text-xs text-amber-700 mt-1.5">Only Executive Admins can change the role of another Exec Admin.</p>
          )}
        </section>

        {/* ── Section 3: Password ── */}
        <section>
          <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Password Reset</div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Set New Password Directly</label>
              <div className="flex gap-2">
                <input
                  type={showPw ? "text" : "password"}
                  value={newPw}
                  onChange={e => setNewPw(e.target.value)}
                  disabled={!canEdit}
                  placeholder="Min 8 characters — leave blank to keep current"
                  className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm font-mono text-slate-800 focus:outline-none focus:border-amber-400 disabled:bg-slate-50 disabled:text-slate-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="border border-slate-200 rounded-lg px-3 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors"
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">Or Generate a One-Time Reset Link</label>
              <button
                onClick={generateResetLink}
                disabled={!canEdit || saving}
                className="flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-lg border border-amber-300 text-amber-700 hover:bg-amber-50 transition-colors disabled:opacity-40"
              >
                <Key className="w-3.5 h-3.5" /> Generate Reset Link
              </button>
              {pwLink && (
                <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs font-mono text-amber-900 break-all mb-2">{pwLink}</p>
                  <button
                    onClick={copyLink}
                    className="flex items-center gap-1.5 text-xs font-bold text-amber-700 hover:text-amber-900"
                  >
                    {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? "Copied!" : "Copy link"}
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── Section 4: Activity Restrictions ── */}
        <section>
          <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Activity Restriction</div>
          <div className="space-y-2">
            {/* Activate / Deactivate */}
            {canEdit && (
              <button
                onClick={toggleActive}
                disabled={saving}
                className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border font-bold text-sm transition-colors disabled:opacity-40 ${
                  isInactive && !isBanned
                    ? "border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                    : "border-orange-300 text-orange-700 hover:bg-orange-50"
                }`}
              >
                {isInactive && !isBanned ? (
                  <><UserCheck className="w-4 h-4" /> Activate Account</>
                ) : (
                  <><UserX className="w-4 h-4" /> Deactivate Account</>
                )}
              </button>
            )}

            {/* Ban / Unban — exec only, non-exec targets only */}
            {isExec && !targetIsExec && (
              isBanned ? (
                <button
                  onClick={unbanUser}
                  disabled={saving}
                  className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border border-emerald-300 text-emerald-700 hover:bg-emerald-50 font-bold text-sm transition-colors disabled:opacity-40"
                >
                  <Shield className="w-4 h-4" /> Remove Ban
                </button>
              ) : (
                <button
                  onClick={banUser}
                  disabled={saving}
                  className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border border-red-400 text-red-700 hover:bg-red-50 font-bold text-sm transition-colors disabled:opacity-40"
                >
                  <Ban className="w-4 h-4" /> Permanently Ban
                </button>
              )
            )}
            {isBanned && target.ban_reason && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                <strong>Ban reason:</strong> {target.ban_reason}
              </p>
            )}
          </div>
        </section>

        {/* ── Section 5: Session Management ── */}
        <section>
          <div className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Sessions</div>
          <button
            onClick={forceLogout}
            disabled={saving}
            className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-bold text-sm transition-colors disabled:opacity-40"
          >
            <LogOut className="w-4 h-4" /> Force Logout All Devices
          </button>
        </section>

        {/* ── Save button ── */}
        {canEdit && (
          <button
            onClick={saveIdentity}
            disabled={saving}
            className="w-full py-3 bg-ink text-white font-bold rounded-lg hover:bg-ink/90 transition-colors disabled:opacity-50 text-sm"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
        )}

        {/* ── Danger zone ── */}
        {isExec && !targetIsExec && (
          <section className="border-t border-red-100 pt-5">
            <div className="text-xs font-black uppercase tracking-widest text-red-400 mb-3">Danger Zone</div>
            <button
              onClick={deleteUser}
              disabled={saving}
              className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-red-300 text-red-700 hover:bg-red-50 font-bold text-sm transition-colors disabled:opacity-40"
            >
              <X className="w-4 h-4" /> Permanently Delete Account
            </button>
            <p className="text-xs text-slate-400 mt-2">GDPR-compliant anonymization. This cannot be reversed.</p>
          </section>
        )}
      </div>

      {confirmBan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Permanently Ban User</h2>
            <p className="text-sm text-slate-600 mb-3">Document the reason for this ban (required, min 5 chars):</p>
            <input value={banReason} onChange={e => setBanReason(e.target.value)} placeholder="Ban reason…" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:border-red-400" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmBan(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doBanUser} disabled={banReason.trim().length < 5} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-40">Ban</button>
            </div>
          </div>
        </div>
      )}

      {confirmUnban && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Remove Ban</h2>
            <p className="text-sm text-slate-600 mb-6">Remove ban for <strong>{target.full_name || target.email}</strong> and reactivate their account?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmUnban(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doUnbanUser} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Remove Ban</button>
            </div>
          </div>
        </div>
      )}

      {confirmLogout && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Force Logout</h2>
            <p className="text-sm text-slate-600 mb-6">Force log out all sessions for <strong>{target.full_name || target.email}</strong>?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmLogout(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doForceLogout} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Log Out</button>
            </div>
          </div>
        </div>
      )}

      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Delete Account</h2>
            <p className="text-sm text-slate-600 mb-6">Permanently delete <strong>{target.full_name || target.email}</strong>? This cannot be undone.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmDelete(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={doDeleteUser} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AccountControls() {
  const { user: actor } = useAuth();
  const isExec = actor?.role === "executive_admin";

  const [users,        setUsers]        = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [search,       setSearch]       = useState("");
  const [roleFilter,   setRoleFilter]   = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selected,     setSelected]     = useState(null);

  const debounce = useRef(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/users");
      setUsers(Array.isArray(r.data) ? r.data : []);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const filtered = users.filter(u => {
    const q = search.toLowerCase();
    if (q && !`${u.full_name} ${u.email} ${u.id}`.toLowerCase().includes(q)) return false;
    if (roleFilter   !== "all" && u.role !== roleFilter) return false;
    if (statusFilter === "active"   && u.is_active === false) return false;
    if (statusFilter === "inactive" && u.is_active !== false) return false;
    return true;
  });

  function handleSearch(val) {
    setSearch(val);
    clearTimeout(debounce.current);
  }

  function handleUpdated(updated) {
    setUsers(prev => prev.map(u => u.id === updated.id ? { ...u, ...updated } : u));
    setSelected(prev => prev?.id === updated.id ? { ...prev, ...updated } : prev);
  }

  function handleDeleted(uid) {
    setUsers(prev => prev.filter(u => u.id !== uid));
    setSelected(null);
  }

  const roleCount = role => users.filter(u => u.role === role).length;

  return (
    <AppShell>
      <div className="flex flex-col h-screen bg-bone">
        {/* Page header */}
        <div className="bg-ink text-white px-6 py-4 border-b border-white/10 flex-shrink-0">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-xs font-bold uppercase tracking-widest text-white/50">Admin</div>
              <h1 className="font-heading text-xl font-extrabold flex items-center gap-2 mt-0.5">
                <Users className="w-5 h-5 text-copper" /> Account Controls
              </h1>
            </div>
            <div className="flex items-center gap-2 text-xs text-white/60 flex-wrap">
              {ALL_ROLES.map(r => (
                <span key={r} className={`px-2 py-0.5 rounded-full font-bold ${ROLE_COLOR[r]}`}>
                  {ROLE_LABEL[r]} {roleCount(r)}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Split layout */}
        <div className="flex flex-1 min-h-0">

          {/* ── Left: user list ── */}
          <div className={`flex flex-col border-r border-slate-200 bg-white ${selected ? "hidden lg:flex lg:w-80 xl:w-96" : "flex flex-1 lg:flex-none lg:w-96"}`}>

            {/* Search + filters */}
            <div className="px-4 py-3 border-b border-slate-100 space-y-2 flex-shrink-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  value={search}
                  onChange={e => handleSearch(e.target.value)}
                  placeholder="Search by name or email…"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-amber-400"
                />
              </div>
              <div className="flex gap-2">
                <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
                  className="flex-1 text-xs border border-slate-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:border-amber-400">
                  <option value="all">All Roles</option>
                  {ALL_ROLES.map(r => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                </select>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                  className="flex-1 text-xs border border-slate-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:border-amber-400">
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
                <button onClick={loadUsers} disabled={loading} className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-500 disabled:opacity-40">
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                </button>
              </div>
              <p className="text-xs text-slate-400">{filtered.length} of {users.length} accounts</p>
            </div>

            {/* User rows */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="py-10 text-center text-slate-400 text-sm">Loading…</div>
              ) : filtered.length === 0 ? (
                <div className="py-10 text-center text-slate-400 text-sm">No accounts match these filters.</div>
              ) : filtered.map(u => (
                <button
                  key={u.id}
                  onClick={() => setSelected(u)}
                  className={`w-full text-left px-4 py-3 border-b border-slate-50 hover:bg-slate-50 transition-colors flex items-center gap-3 ${selected?.id === u.id ? "bg-amber-50 border-l-2 border-l-amber-400" : ""}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-sm text-slate-900 truncate">{u.full_name || "—"}</div>
                    <div className="text-xs font-mono text-slate-500 truncate">{u.email}</div>
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${ROLE_COLOR[u.role] || "bg-slate-100 text-slate-600"}`}>
                        {ROLE_LABEL[u.role] || u.role}
                      </span>
                      {u.banned && <span className="text-[10px] font-bold bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full">Banned</span>}
                      {!u.banned && u.is_active === false && <span className="text-[10px] font-bold bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full">Inactive</span>}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* ── Right: control panel ── */}
          <div className={`flex-1 min-h-0 ${selected ? "flex flex-col" : "hidden lg:flex lg:items-center lg:justify-center"}`}>
            {selected ? (
              <>
                {/* Mobile back button */}
                <button
                  onClick={() => setSelected(null)}
                  className="lg:hidden flex items-center gap-2 px-4 py-2 text-sm font-bold text-slate-600 border-b border-slate-100 hover:bg-slate-50"
                >
                  ← Back to list
                </button>
                <div className="flex-1 min-h-0 overflow-hidden">
                  <ControlPanel
                    key={selected.id}
                    user={selected}
                    actorRole={actor?.role}
                    onUpdated={handleUpdated}
                    onDeleted={handleDeleted}
                  />
                </div>
              </>
            ) : (
              <div className="text-center text-slate-400 p-8">
                <Users className="w-12 h-12 mx-auto mb-3 text-slate-200" />
                <p className="font-heading font-bold text-slate-500">Select an account</p>
                <p className="text-sm mt-1">Click any user on the left to open their account controls.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
