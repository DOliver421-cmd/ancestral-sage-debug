import { useEffect, useState, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import EmergencyPanel from "../components/EmergencyPanel";
import {
  Crown, Database, Users, Shield,
  Activity, AlertTriangle, BadgeCheck,
  GraduationCap, Award, RefreshCw,
  CheckCircle2, XCircle, Clock, MessageSquare,
  HandHelping, Siren, Search, ChevronDown, ShieldAlert,
  UserPlus, Trash2, ArrowUpCircle, ArrowDownCircle, Copy, KeyRound, Eye, EyeOff,
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
      <div className="text-xs font-bold uppercase tracking-wider text-slate-700 mt-1">{label}</div>
      {sub && <div className="text-xs text-slate-600 mt-0.5">{sub}</div>}
    </div>
  );
}

// ── User Database panel ───────────────────────────────────────────────────────
const ROLES_ALL    = ["student", "instructor", "admin", "executive_admin"];
const ROLES_FILTER = ["", ...ROLES_ALL];
const ROLE_LABELS  = { "": "All Roles", student: "Student", instructor: "Instructor", admin: "Admin", executive_admin: "Exec Admin" };
const ROLE_COLORS  = { executive_admin: "bg-amber-100 text-amber-800", admin: "bg-slate-100 text-slate-700", instructor: "bg-blue-100 text-blue-800", student: "bg-emerald-100 text-emerald-800" };
const ROLE_RANK    = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };

function fmtJoined(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// ── Create User Modal ─────────────────────────────────────────────────────────
function UserCreateModal({ onClose, onCreated, notify }) {
  const [name,      setName]     = useState("");
  const [email,     setEmail]    = useState("");
  const [role,      setRole]     = useState("student");
  const [assoc,     setAssoc]    = useState("");
  const [pw,        setPw]       = useState("");
  const [showPw,    setShowPw]   = useState(false);
  const [saving,    setSaving]   = useState(false);
  const [resetLink, setResetLink]= useState(null);
  const [created,   setCreated]  = useState(null);

  function genPw() {
    const chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#";
    setPw(Array.from({ length: 14 }, () => chars[Math.floor(Math.random() * chars.length)]).join(""));
    setShowPw(true);
  }

  async function create() {
    if (!name.trim())        return notify("Full name is required", true);
    if (!email.trim())       return notify("Email is required", true);
    if (pw.length < 8)       return notify("Password must be at least 8 characters", true);
    setSaving(true);
    try {
      const r = await api.post("/admin/users", {
        full_name: name.trim(), email: email.trim().toLowerCase(),
        password: pw, role, associate: assoc.trim() || undefined,
      });
      const newUser = r.data;
      setCreated(newUser);
      notify(`${name} created as ${ROLE_LABELS[role]}`);
      onCreated(newUser);
      // auto-generate reset link so exec can send it directly
      try {
        const lr = await api.post(`/admin/users/${newUser.id}/reset-link`);
        setResetLink(lr.data.reset_url || lr.data.link || null);
      } catch (_) {}
    } catch (e) {
      notify(`Error: ${e?.response?.data?.detail || "create failed"}`, true);
    } finally {
      setSaving(false);
    }
  }

  // After creation — show confirmation with link
  if (created) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.6)" }}>
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 bg-emerald-50 flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
            <div>
              <p className="font-bold text-emerald-900">Account Created</p>
              <p className="text-xs text-emerald-700 mt-0.5">{created.full_name} · {ROLE_LABELS[created.role]}</p>
            </div>
          </div>
          <div className="px-6 py-5 space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Email</p>
              <p className="font-mono text-sm text-slate-800">{created.email}</p>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Temporary Password</p>
              <div className="flex items-center gap-2 bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                <span className="font-mono text-sm text-slate-800 flex-1">{pw}</span>
                <button onClick={() => navigator.clipboard?.writeText(pw)} className="text-xs font-bold text-amber-600 hover:underline flex items-center gap-1">
                  <Copy className="w-3 h-3" /> Copy
                </button>
              </div>
              <p className="text-xs text-slate-400 mt-1">User will be prompted to change this on first login.</p>
            </div>
            {resetLink && (
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">One-Time Login Link <span className="font-normal text-slate-400">(send this to skip password entry)</span></p>
                <div className="flex items-start gap-2 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200">
                  <span className="font-mono text-xs text-amber-800 flex-1 break-all">{resetLink}</span>
                  <button onClick={() => navigator.clipboard?.writeText(resetLink)} className="text-xs font-bold text-amber-600 hover:underline flex items-center gap-1 shrink-0">
                    <Copy className="w-3 h-3" /> Copy
                  </button>
                </div>
              </div>
            )}
          </div>
          <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end">
            <button onClick={onClose} className="text-sm font-bold bg-slate-900 text-white px-6 py-2 rounded-lg hover:bg-slate-700">Done</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.55)" }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-amber-500" />
            <h3 className="font-heading font-extrabold text-slate-900 text-lg">Create New Account</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xl font-bold leading-none">×</button>
        </div>

        <div className="px-6 py-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Full Name *</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="First Last"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Email Address *</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-mono focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Access Level / Role *</label>
            <div className="relative">
              <select value={role} onChange={e => setRole(e.target.value)}
                className="w-full appearance-none border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400 bg-white pr-8">
                {ROLES_ALL.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
            <div className="mt-1.5 text-xs text-slate-400 space-y-0.5">
              <p><strong className="text-slate-600">Student</strong> — takes courses, submits labs, earns credentials</p>
              <p><strong className="text-slate-600">Instructor</strong> — manages rosters, reviews lab submissions, grades</p>
              <p><strong className="text-slate-600">Admin</strong> — full platform management, sees all data</p>
              <p><strong className="text-amber-600">Exec Admin</strong> — executive control, AI governance, emergency controls</p>
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Associate Cohort <span className="font-normal text-slate-400">(optional)</span></label>
            <input value={assoc} onChange={e => setAssoc(e.target.value)} placeholder="e.g. Associate-Alpha"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">Temporary Password *</label>
              <button type="button" onClick={genPw} className="text-xs font-bold text-amber-600 hover:underline flex items-center gap-1">
                <KeyRound className="w-3 h-3" /> Generate secure password
              </button>
            </div>
            <div className="relative">
              <input type={showPw ? "text" : "password"} value={pw} onChange={e => setPw(e.target.value)}
                placeholder="Min 8 characters"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 pr-10 text-sm text-slate-800 font-mono focus:outline-none focus:border-amber-400" />
              <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">A one-time reset link is auto-generated after creation so you can send them direct access without sharing this password.</p>
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-slate-50">
          <button onClick={onClose} className="text-sm text-slate-600 hover:text-slate-700 px-4 py-2">Cancel</button>
          <button onClick={create} disabled={saving}
            className="text-sm font-bold bg-amber-500 hover:bg-amber-600 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-40 flex items-center gap-2">
            <UserPlus className="w-4 h-4" />
            {saving ? "Creating…" : "Create Account"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Edit User Modal ───────────────────────────────────────────────────────────
function UserEditModal({ user: u, onClose, onUpdated, onDeleted, notify }) {
  const [name,      setName]     = useState(u.full_name || "");
  const [email,     setEmail]    = useState(u.email || "");
  const [role,      setRole]     = useState(u.role || "student");
  const [assoc,     setAssoc]    = useState(u.associate || "");
  const [pw,        setPw]       = useState("");
  const [showPw,    setShowPw]   = useState(false);
  const [saving,    setSaving]   = useState(false);
  const [resetLink, setLink]     = useState(null);

  async function save() {
    setSaving(true);
    try {
      await api.patch(`/admin/users/${u.id}`, { full_name: name, email, associate: assoc || undefined });
      if (role !== u.role) await api.patch(`/admin/users/${u.id}/role`, { role });
      if (pw.trim()) await api.post(`/admin/users/${u.id}/password`, { new_password: pw });
      notify(`${name} updated`);
      onUpdated({ ...u, full_name: name, email, role, associate: assoc });
      onClose();
    } catch (e) {
      notify(`Error: ${e?.response?.data?.detail || "save failed"}`, true);
    } finally { setSaving(false); }
  }

  async function toggleActive() {
    setSaving(true);
    try {
      await api.patch(`/admin/users/${u.id}/active`, { is_active: u.is_active === false });
      notify(`${u.full_name} ${u.is_active === false ? "activated" : "deactivated"}`);
      onUpdated({ ...u, is_active: u.is_active === false });
      onClose();
    } catch (e) {
      notify(`Error: ${e?.response?.data?.detail || "action failed"}`, true);
    } finally { setSaving(false); }
  }

  async function deleteUser() {
    if (!window.confirm(`Permanently delete ${u.full_name || u.email}? This cannot be undone.`)) return;
    setSaving(true);
    try {
      await api.delete(`/admin/users/${u.id}`);
      notify(`${u.full_name || u.email} deleted`);
      onDeleted(u.id);
      onClose();
    } catch (e) {
      notify(`Error: ${e?.response?.data?.detail || "delete failed"}`, true);
    } finally { setSaving(false); }
  }

  async function getResetLink() {
    setSaving(true);
    try {
      const r = await api.post(`/admin/users/${u.id}/reset-link`);
      setLink(r.data.reset_url || r.data.link || JSON.stringify(r.data));
    } catch (e) {
      notify(`Error: ${e?.response?.data?.detail || "could not generate link"}`, true);
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.55)" }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div>
            <h3 className="font-heading font-extrabold text-slate-900 text-lg">{u.full_name || u.email}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ROLE_COLORS[u.role] || "bg-slate-100 text-slate-600"}`}>{ROLE_LABELS[u.role] || u.role}</span>
              {u.is_active === false && <span className="text-xs font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full">Inactive</span>}
              <span className="text-xs text-slate-400 font-mono">{u.email}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xl font-bold leading-none">×</button>
        </div>

        <div className="px-6 py-5 space-y-4 max-h-[65vh] overflow-y-auto">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Full Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 font-mono focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Access Level / Role</label>
            <div className="relative">
              <select value={role} onChange={e => setRole(e.target.value)}
                className="w-full appearance-none border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400 bg-white pr-8">
                {ROLES_ALL.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Associate Cohort</label>
            <input value={assoc} onChange={e => setAssoc(e.target.value)} placeholder="e.g. Associate-Alpha"
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:border-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
              Set New Password <span className="font-normal text-slate-400">(leave blank to keep current)</span>
            </label>
            <div className="relative">
              <input type={showPw ? "text" : "password"} value={pw} onChange={e => setPw(e.target.value)} placeholder="Min 8 characters"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 pr-10 text-sm text-slate-800 font-mono focus:outline-none focus:border-amber-400" />
              <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500">Password Reset Link</label>
              <button onClick={getResetLink} disabled={saving} className="text-xs font-bold text-amber-600 hover:underline disabled:opacity-40 flex items-center gap-1">
                <KeyRound className="w-3 h-3" /> Generate one-time link
              </button>
            </div>
            {resetLink && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs text-amber-700 font-mono break-all">{resetLink}</p>
                <button onClick={() => navigator.clipboard?.writeText(resetLink)} className="text-xs font-bold text-amber-600 hover:underline mt-1 flex items-center gap-1">
                  <Copy className="w-3 h-3" /> Copy link
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-slate-50 gap-3 flex-wrap">
          <div className="flex gap-2">
            <button onClick={toggleActive} disabled={saving}
              className={`text-xs font-bold px-3 py-2 rounded-lg border transition-colors disabled:opacity-40 ${u.is_active === false ? "border-emerald-500 text-emerald-600 hover:bg-emerald-50" : "border-orange-400 text-orange-600 hover:bg-orange-50"}`}>
              {u.is_active === false ? "Activate" : "Deactivate"}
            </button>
            <button onClick={deleteUser} disabled={saving}
              className="text-xs font-bold px-3 py-2 rounded-lg border border-red-300 text-red-500 hover:bg-red-50 transition-colors disabled:opacity-40 flex items-center gap-1">
              <Trash2 className="w-3 h-3" /> Delete
            </button>
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="text-sm text-slate-600 hover:text-slate-700 px-4 py-2">Cancel</button>
            <button onClick={save} disabled={saving}
              className="text-sm font-bold bg-amber-500 hover:bg-amber-600 text-white px-5 py-2 rounded-lg transition-colors disabled:opacity-40">
              {saving ? "Saving…" : "Save Changes"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── User Database ─────────────────────────────────────────────────────────────
function UserDatabase() {
  const [users,       setUsers]      = useState([]);
  const [loading,     setLoading]    = useState(true);
  const [error,       setError]      = useState(null);
  const [q,           setQ]          = useState("");
  const [roleFilter,  setRoleFilter] = useState("");
  const [activeFilter,setActiveFilter]=useState("");
  const [toast,       setToast]      = useState(null);
  const [editing,     setEditing]    = useState(null);
  const [creating,    setCreating]   = useState(false);
  const [promoting,   setPromoting]  = useState({}); // uid → bool
  const debounce                     = useRef(null);

  function notify(msg, isErr = false) {
    setToast({ msg, isErr });
    setTimeout(() => setToast(null), 5000);
  }

  const fetchUsers = useCallback(async (search, role, active) => {
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (role)   params.set("role", role);
      if (active) params.set("active", active);
      const r = await api.get(`/admin/users?${params}`);
      setUsers(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load users");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    clearTimeout(debounce.current);
    debounce.current = setTimeout(() => fetchUsers(q, roleFilter, activeFilter), 300);
    return () => clearTimeout(debounce.current);
  }, [q, roleFilter, activeFilter, fetchUsers]);

  function handleUpdated(updated) {
    setUsers(prev => prev.map(x => x.id === updated.id ? { ...x, ...updated } : x));
  }
  function handleDeleted(uid) {
    setUsers(prev => prev.filter(x => x.id !== uid));
  }
  function handleCreated(newUser) {
    setUsers(prev => [newUser, ...prev]);
  }

  // Quick role change directly on the row — one click promote/demote
  async function quickRole(u, newRole) {
    setPromoting(p => ({ ...p, [u.id]: true }));
    try {
      await api.patch(`/admin/users/${u.id}/role`, { role: newRole });
      setUsers(prev => prev.map(x => x.id === u.id ? { ...x, role: newRole } : x));
      notify(`${u.full_name || u.email} → ${ROLE_LABELS[newRole]}`);
    } catch (e) {
      notify(`Role change failed: ${e?.response?.data?.detail || e.message}`, true);
    } finally {
      setPromoting(p => ({ ...p, [u.id]: false }));
    }
  }

  const byRole = ROLES_ALL.reduce((acc, r) => ({ ...acc, [r]: users.filter(u => u.role === r).length }), {});

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm mb-6 overflow-hidden">
      {/* header */}
      <div className="px-6 py-4 border-b border-slate-100">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <h2 className="font-heading font-extrabold text-lg text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-slate-400" /> User Database
            <span className="text-sm font-normal text-slate-400 ml-1">({users.length} shown)</span>
          </h2>
          <button onClick={() => setCreating(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-bold rounded-xl transition-colors">
            <UserPlus className="w-4 h-4" /> Create Account
          </button>
        </div>

        {/* role summary chips */}
        <div className="flex gap-2 flex-wrap mb-3">
          {ROLES_ALL.map(r => (
            <button key={r} onClick={() => setRoleFilter(roleFilter === r ? "" : r)}
              className={`text-xs font-bold px-3 py-1 rounded-full border transition-all ${roleFilter === r ? ROLE_COLORS[r] + " border-transparent" : "border-slate-200 text-slate-500 hover:border-slate-300"}`}>
              {ROLE_LABELS[r]} ({byRole[r] || 0})
            </button>
          ))}
        </div>

        {/* filters row */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search name or email…"
              className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-amber-400" />
          </div>
          <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
            className="py-1.5 px-3 text-sm border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:border-amber-400 bg-white">
            {ROLES_FILTER.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
          </select>
          <select value={activeFilter} onChange={e => setActiveFilter(e.target.value)}
            className="py-1.5 px-3 text-sm border border-slate-200 rounded-lg text-slate-700 focus:outline-none focus:border-amber-400 bg-white">
            <option value="">All Status</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
          <button onClick={() => fetchUsers(q, roleFilter, activeFilter)} className="text-xs font-bold text-slate-600 hover:text-amber-600 border border-slate-200 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      </div>

      {/* toast */}
      {toast && (
        <div className={`px-6 py-2 border-b text-sm font-medium ${toast.isErr ? "bg-red-50 border-red-100 text-red-700" : "bg-amber-50 border-amber-100 text-amber-800"}`}>
          {toast.msg}
        </div>
      )}

      {/* table */}
      <div className="overflow-x-auto">
        {loading ? (
          <div className="py-10 text-center text-slate-400 text-sm">Loading users…</div>
        ) : error ? (
          <div className="py-10 text-center text-red-500 text-sm">{error}</div>
        ) : users.length === 0 ? (
          <div className="py-10 text-center text-slate-400 text-sm">No users match these filters.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-100 bg-slate-50/60">
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Name</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Email</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Role</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Cohort</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Joined</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Status</th>
                <th className="text-left py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold">Promote / Demote</th>
                <th className="py-2.5 px-4 text-xs uppercase tracking-wider text-slate-500 font-bold text-right">Edit</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                const rank    = ROLE_RANK[u.role] || 1;
                const canUp   = rank < 4;
                const canDown = rank > 1;
                const nextUp   = ROLES_ALL[rank];      // one step up
                const nextDown = ROLES_ALL[rank - 2];  // one step down
                const busy    = !!promoting[u.id];
                return (
                  <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50/70">
                    <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap">{u.full_name || "—"}</td>
                    <td className="py-3 px-4 font-mono text-slate-600 text-xs whitespace-nowrap">{u.email}</td>
                    <td className="py-3 px-4">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${ROLE_COLORS[u.role] || "bg-slate-100 text-slate-700"}`}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 text-xs">{u.associate || <span className="text-slate-300">—</span>}</td>
                    <td className="py-3 px-4 text-slate-500 text-xs whitespace-nowrap">{fmtJoined(u.created_at)}</td>
                    <td className="py-3 px-4">
                      {u.is_active === false
                        ? <span className="text-xs font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full">Inactive</span>
                        : <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Active</span>
                      }
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1">
                        {canUp && (
                          <button onClick={() => quickRole(u, nextUp)} disabled={busy} title={`Promote to ${ROLE_LABELS[nextUp]}`}
                            className="flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 disabled:opacity-40 transition-colors whitespace-nowrap">
                            <ArrowUpCircle className="w-3.5 h-3.5" />
                            {ROLE_LABELS[nextUp]}
                          </button>
                        )}
                        {canDown && (
                          <button onClick={() => quickRole(u, nextDown)} disabled={busy} title={`Demote to ${ROLE_LABELS[nextDown]}`}
                            className="flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100 disabled:opacity-40 transition-colors whitespace-nowrap">
                            <ArrowDownCircle className="w-3.5 h-3.5" />
                            {ROLE_LABELS[nextDown]}
                          </button>
                        )}
                        {!canUp && !canDown && <span className="text-xs text-slate-300">—</span>}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button onClick={() => setEditing(u)}
                        className="text-xs font-bold px-3 py-1.5 rounded-lg border border-amber-300 text-amber-700 hover:bg-amber-50 transition-colors">
                        Edit
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {creating && (
        <UserCreateModal
          onClose={() => setCreating(false)}
          onCreated={handleCreated}
          notify={notify}
        />
      )}
      {editing && (
        <UserEditModal
          user={editing}
          onClose={() => setEditing(null)}
          onUpdated={handleUpdated}
          onDeleted={handleDeleted}
          notify={notify}
        />
      )}
    </div>
  );
}

// ── API Key Manager ───────────────────────────────────────────────────────────
const AI_PROVIDERS = [
  { key: "gemini",  label: "Google Gemini",  hint: "AIza…",  tier: "Free via AI Studio",        link: "https://aistudio.google.com" },
  { key: "cohere",  label: "Cohere",         hint: "…",      tier: "Free trial tier",            link: "https://dashboard.cohere.com" },
  { key: "hf",      label: "Hugging Face",   hint: "hf_…",   tier: "Free inference API",         link: "https://huggingface.co/settings/tokens" },
  { key: "grok",    label: "Grok (xAI)",     hint: "xai-…",  tier: "Free beta tier",             link: "https://console.x.ai" },
];

function ApiKeyManager() {
  const STORAGE_KEY = "supervisor_api_keys";
  const [keys, setKeys] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}"); } catch { return {}; }
  });
  const [saved, setSaved] = useState({});

  function handleSave(provider) {
    const val = keys[provider] || "";
    if (!val.trim()) return;
    const updated = { ...keys, [provider]: val.trim() };
    setKeys(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setSaved(s => ({ ...s, [provider]: true }));
    setTimeout(() => setSaved(s => ({ ...s, [provider]: false })), 3000);
  }

  function handleClear(provider) {
    const updated = { ...keys };
    delete updated[provider];
    setKeys(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  }

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
      <h2 className="font-heading font-extrabold text-base text-slate-900 mb-1 flex items-center gap-2">
        <Shield className="w-4 h-4 text-amber-500" /> AI Service API Keys
      </h2>
      <p className="text-xs text-slate-500 mb-5">Keys are stored locally in your browser. All providers offer free tiers. Used by The Supervisor backup system.</p>
      <div className="grid sm:grid-cols-2 gap-4">
        {AI_PROVIDERS.map(p => (
          <div key={p.key} className="border border-slate-100 rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="font-heading font-bold text-sm text-slate-900">{p.label}</span>
              {keys[p.key]
                ? <span className="text-xs font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">Key Set ✓</span>
                : <span className="text-xs font-bold bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">Not Set</span>
              }
            </div>
            <p className="text-xs text-slate-400 mb-3">{p.tier}</p>
            <div className="flex gap-2">
              <input
                type="password"
                className="flex-1 text-xs font-mono px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-slate-500"
                placeholder={p.hint}
                value={keys[p.key] || ""}
                onChange={e => setKeys(k => ({ ...k, [p.key]: e.target.value }))}
                onKeyDown={e => e.key === "Enter" && handleSave(p.key)}
              />
              <button
                onClick={() => handleSave(p.key)}
                className="px-3 py-2 text-xs font-bold bg-slate-900 text-white rounded-lg hover:bg-slate-700 transition-colors whitespace-nowrap">
                {saved[p.key] ? "Saved ✓" : "Save"}
              </button>
              {keys[p.key] && (
                <button onClick={() => handleClear(p.key)}
                  className="px-3 py-2 text-xs font-bold border border-red-200 text-red-500 rounded-lg hover:bg-red-50 transition-colors">
                  ✕
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
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
  const [showPanel, setShowPanel] = useState(false);

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
      <div className="px-6 lg:px-10 py-8 max-w-7xl" style={{ background: "linear-gradient(160deg,#06251c,#0a0a0f 70%)", minHeight: "100vh", color: "#0b1f3a" }}>

        {/* ── Header ───────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Crown className="w-5 h-5" style={{ color: "var(--wai-gold)" }} />
              <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "var(--wai-gold-light)" }}>Sovereign Command · Zamunda</span>
            </div>
            <h1 className="font-heading text-3xl lg:text-4xl font-extrabold" style={{ color: "var(--wai-gold-light)" }}>
              WAI-Institute Platform
            </h1>
            <p className="text-sm mt-1" style={{ color: "rgba(241,240,251,0.6)" }}>
              {lastSync
                ? <>Last refreshed {ts(lastSync)} · <span className="text-emerald-600 font-semibold">All systems checked</span></>
                : "Loading…"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link to="/admin/director"
              className="flex items-center gap-2 px-4 py-2 bg-red-800 text-white text-sm font-bold rounded-xl hover:bg-red-700 transition-colors border-2 border-red-600">
              <ShieldAlert className="w-4 h-4" /> Director
            </Link>
            <button onClick={() => setShowPanel(!showPanel)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-bold rounded-xl border-2 transition-all ${showPanel ? "bg-amber-900/30 border-amber-500 text-amber-400" : "bg-slate-900 border-slate-700 text-white hover:bg-slate-800"}`}>
              <Siren className="w-4 h-4" /> Breaker Panel
            </button>
            <button onClick={load} disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-slate-700 transition-colors disabled:opacity-50">
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>
        </div>

        {err && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm font-medium flex items-center gap-2">
            <XCircle className="w-4 h-4 shrink-0" /> {err}
          </div>
        )}

        {/* ── System status bar ─────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm mb-6">
          <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Platform Status</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatusDot ok={!!sys}      label="API Server" />
            <StatusDot ok={!!sys}      label="Database" />
            <StatusDot ok={!hasIncidents} label={hasIncidents ? `${stats?.incidents_open} Open Incidents` : "No Incidents"} />
            <StatusDot ok={!hasLabsPending} label={hasLabsPending ? `${stats?.labs_pending} Labs Pending` : "Labs Current"} />
          </div>
        </div>

        {/* ── Emergency Breaker Panel (toggle) ──────────────────────────── */}
        {showPanel && (
          <div className="mb-6">
            <EmergencyPanel onClose={() => setShowPanel(false)} />
          </div>
        )}

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
            <div className="mt-6 pt-5 border-t border-slate-100 space-y-2 text-xs text-slate-700">
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
            <p className="text-xs text-slate-600 mb-4">Last {activity.length} privileged actions</p>
            <div className="space-y-1 overflow-y-auto" style={{ maxHeight: 320 }}>
              {activity.length === 0 && (
                <div className="text-sm text-slate-600 py-6 text-center">No activity recorded yet.</div>
              )}
              {activity.map((a) => (
                <div key={a.id} className="flex items-start gap-3 py-2 border-b border-slate-50">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-slate-800 truncate">{a.actor_name}</div>
                    <div className="text-xs font-mono text-amber-600 truncate">{a.action}</div>
                  </div>
                  <div className="text-[10px] text-slate-600 whitespace-nowrap shrink-0 mt-0.5">{ts(a.at)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Associate cohort table ─────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm mb-6">
          <h2 className="font-heading font-extrabold text-lg text-slate-900 mb-4 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-slate-400" /> Associate Cohort Performance
          </h2>
          {cohorts.length === 0 ? (
            <div className="text-sm text-slate-600 py-4">No associate cohorts found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-100">
                    <th className="text-left py-2 px-3 text-xs uppercase tracking-wider text-slate-600 font-bold">Associate</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-600 font-bold">Students</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-600 font-bold">Instructors</th>
                    <th className="text-right py-2 px-3 text-xs uppercase tracking-wider text-slate-600 font-bold">Completions</th>
                    <th className="py-2 px-3 text-xs uppercase tracking-wider text-slate-600 font-bold">Completion Rate</th>
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
                            <span className="text-xs font-bold text-slate-700 w-8 text-right">{rate}%</span>
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

        {/* ── User Database ─────────────────────────────────────────────── */}
        <UserDatabase />

        {/* ── API Key Management ────────────────────────────────────────── */}
        <ApiKeyManager />

        {/* ── DB collections ────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm">
          <h2 className="font-heading font-extrabold text-base text-slate-900 mb-3 flex items-center gap-2">
            <Database className="w-4 h-4 text-slate-400" /> Live Collections ({sys?.collections?.length || 0})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1">
            {(sys?.collections || []).map((c) => (
              <div key={c} className="text-xs font-mono text-slate-700 py-1 px-2 bg-slate-50 rounded border border-slate-100">
                {c}
              </div>
            ))}
          </div>
        </div>

      </div>
    </AppShell>
  );
}
