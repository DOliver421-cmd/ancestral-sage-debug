import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Users, GraduationCap, BookOpen, Award, Download, UserPlus, Trash2, KeyRound, ShieldCheck, Pencil, Lock, Unlock, Activity, Clock, AlertTriangle, BadgeCheck, Link2, Copy, X } from "lucide-react";

const ROLES = ["student", "instructor", "admin", "executive_admin"];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [activity, setActivity] = useState([]);
  const [cohorts, setCohorts] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ email: "", full_name: "", password: "", role: "student", associate: "Associate-Alpha" });
  const [editing, setEditing] = useState(null); // {id, full_name, email, associate}
  const [filter, setFilter] = useState({ role: "", active: "", q: "" });
  const [resetLink, setResetLink] = useState(null); // {email, url, expires_at, email_sent}

  const load = useCallback(() => Promise.all([
    api.get("/admin/stats").then((r) => setStats(r.data)),
    api.get("/admin/users").then((r) => setUsers(r.data)),
    api.get("/admin/recent-activity?limit=10").then((r) => setActivity(r.data)).catch(() => {}),
    api.get("/admin/cohorts").then((r) => setCohorts(r.data)).catch(() => {}),
  ]), []);
  useEffect(() => { load(); }, [load]);

  const updateAssociate = async (user_id, associate) => {
    try { await api.post("/admin/associate", { user_id, associate }); toast.success("Associate updated"); load(); }
    catch { toast.error("Update failed"); }
  };

  const changeRole = async (uid, role) => {
    try { await api.patch(`/admin/users/${uid}/role`, { role }); toast.success(`Role set to ${role}`); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Role update failed"); }
  };

  const setActive = async (uid, is_active, email) => {
    const verb = is_active ? "reactivate" : "deactivate";
    if (!window.confirm(`${verb.charAt(0).toUpperCase() + verb.slice(1)} ${email}?`)) return;
    try { await api.patch(`/admin/users/${uid}/active`, { is_active }); toast.success(`Account ${is_active ? "reactivated" : "deactivated"}`); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || `${verb} failed`); }
  };

  const deleteUser = async (uid, email) => {
    if (!window.confirm(`Permanently delete ${email}? This cannot be undone.`)) return;
    try { await api.delete(`/admin/users/${uid}`); toast.success("User deleted"); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Delete failed"); }
  };

  const resetPassword = async (uid, email) => {
    const newPass = window.prompt(`New password for ${email}? (min 6 chars)`);
    if (!newPass || newPass.length < 6) { toast.error("Password too short"); return; }
    try { await api.post(`/admin/users/${uid}/password`, { new_password: newPass }); toast.success(`Password reset for ${email}. Share it securely.`); }
    catch (e) { toast.error(e?.response?.data?.detail || "Reset failed"); }
  };

  const sendResetLink = async (uid, email) => {
    if (!window.confirm(`Mint a one-shot reset link for ${email}? It expires in 30 minutes.`)) return;
    try {
      const r = await api.post(`/admin/users/${uid}/reset-link`, {});
      // Backend returns a path-only URL when PUBLIC_APP_URL isn't set;
      // expand it to a fully-qualified URL using the current origin so the
      // admin can copy/paste it directly to the user.
      const path = r.data?.url || "";
      const fullUrl = path.startsWith("http") ? path : `${window.location.origin}${path}`;
      setResetLink({ ...r.data, url: fullUrl });
      toast.success(r.data?.email_sent ? `Reset link emailed to ${email}` : `Reset link minted for ${email}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not mint reset link");
    }
  };

  const copyResetLink = async () => {
    if (!resetLink?.url) return;
    try { await navigator.clipboard.writeText(resetLink.url); toast.success("Link copied"); }
    catch { toast.error("Copy failed — long-press to select."); }
  };

  const saveEdit = async () => {
    if (!editing) return;
    try {
      await api.patch(`/admin/users/${editing.id}`, {
        full_name: editing.full_name, email: editing.email, associate: editing.associate,
      });
      toast.success("User updated");
      setEditing(null);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Edit failed"); }
  };

  const createUser = async () => {
    if (!createForm.email || !createForm.full_name || createForm.password.length < 6) {
      toast.error("Email, name, and password (6+ chars) required"); return;
    }
    try {
      await api.post("/admin/users", createForm);
      toast.success(`Created ${createForm.role}: ${createForm.email}`);
      setCreateForm({ email: "", full_name: "", password: "", role: "student", associate: "Associate-Alpha" });
      setShowCreate(false);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Create failed"); }
  };

  const filtered = users.filter((u) => {
    if (filter.role && u.role !== filter.role) return false;
    if (filter.active === "active" && u.is_active === false) return false;
    if (filter.active === "inactive" && u.is_active !== false) return false;
    if (filter.q) {
      const q = filter.q.toLowerCase();
      if (!(u.full_name || "").toLowerCase().includes(q) && !(u.email || "").toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const exportCSV = () => {
    const rows = [["name", "email", "role", "associate", "is_active", "created_at"], ...filtered.map((u) => [u.full_name, u.email, u.role, u.associate || "", u.is_active === false ? "INACTIVE" : "active", u.created_at])];
    downloadCSV(rows, "lce-wai-users.csv");
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="overline text-copper">Admin</div>
            <h1 className="font-heading text-4xl font-bold mt-2">Institute Overview</h1>
            <p className="text-ink/60 mt-2">Associates, curriculum, completions — end to end.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowCreate(!showCreate)} className="btn-copper inline-flex items-center gap-2" data-testid="btn-toggle-create">
              <UserPlus className="w-4 h-4" /> {showCreate ? "Cancel" : "New User"}
            </button>
            <button onClick={exportCSV} className="btn-primary inline-flex items-center gap-2" data-testid="btn-export"><Download className="w-4 h-4" /> Export CSV</button>
          </div>
        </div>

        {showCreate && (
          <div className="card-flat p-6 mt-8" data-testid="create-user-form">
            <h3 className="font-heading text-xl font-bold mb-4 flex items-center gap-2"><UserPlus className="w-5 h-5 text-copper" /> Create User</h3>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <Field label="Full name" value={createForm.full_name} onChange={(v) => setCreateForm({ ...createForm, full_name: v })} testid="cu-name" />
              <Field label="Email" value={createForm.email} onChange={(v) => setCreateForm({ ...createForm, email: v })} testid="cu-email" />
              <Field label="Password" type="password" value={createForm.password} onChange={(v) => setCreateForm({ ...createForm, password: v })} testid="cu-password" />
              <div>
                <label className="overline text-ink/60">Role</label>
                <select value={createForm.role} onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                  className="w-full mt-1 px-3 py-2 border border-ink/20 text-sm" data-testid="cu-role">
                  {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <Field label="Associate" value={createForm.associate} onChange={(v) => setCreateForm({ ...createForm, associate: v })} testid="cu-associate" />
            </div>
            <button onClick={createUser} className="btn-primary mt-4" data-testid="btn-create-user">Create</button>
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <Stat icon={Users} label="Total Users" value={stats?.users ?? "—"} testid="stat-users" />
          <Stat icon={GraduationCap} label="Students" value={stats?.students ?? "—"} testid="stat-students" />
          <Stat icon={Users} label="Instructors" value={stats?.instructors ?? "—"} testid="stat-instructors" />
          <Stat icon={BookOpen} label="Modules" value={stats?.modules ?? "—"} testid="stat-modules" />
          <Stat icon={Award} label="Completions" value={stats?.completions ?? "—"} testid="stat-completions" />
          <Stat icon={Clock} label="Labs Pending" value={stats?.labs_pending ?? "—"} alert={(stats?.labs_pending || 0) > 5} testid="stat-labs-pending" />
          <Stat icon={AlertTriangle} label="Open Incidents" value={stats?.incidents_open ?? "—"} alert={(stats?.incidents_open || 0) > 0} testid="stat-incidents" />
          <Stat icon={BadgeCheck} label="Credentials" value={stats?.credentials_issued ?? "—"} testid="stat-credentials" />
        </div>

        {/* Recent Activity + Cohort Summaries */}
        <div className="grid lg:grid-cols-2 gap-6 mt-8">
          <div className="card-flat p-6" data-testid="recent-activity">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2"><Activity className="w-5 h-5 text-copper" /> Recent Activity</h3>
            <p className="text-xs text-ink/50 mt-1">Last {activity.length} privileged actions. Full log at <a href="/admin/audit" className="text-copper underline">Audit Log</a>.</p>
            <ul className="mt-4 divide-y divide-ink/5">
              {activity.length === 0 && <li className="py-3 text-sm text-ink/50">No activity yet.</li>}
              {activity.map((a) => (
                <li key={a.id} className="py-2 text-sm flex items-start gap-3" data-testid={`activity-${a.id}`}>
                  <span className="font-mono text-[10px] text-ink/40 mt-1 whitespace-nowrap">{new Date(a.at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                  <span className="flex-1 min-w-0">
                    <span className="font-bold">{a.actor_name}</span>
                    <span className="text-ink/60"> · </span>
                    <span className="font-mono text-xs text-copper">{a.action}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="card-flat p-6" data-testid="cohort-summary">
            <h3 className="font-heading text-xl font-bold flex items-center gap-2"><GraduationCap className="w-5 h-5 text-copper" /> Cohort Summaries</h3>
            <p className="text-xs text-ink/50 mt-1">Membership and completions per Associate.</p>
            <table className="w-full text-sm mt-4">
              <thead className="text-xs uppercase tracking-widest text-ink/50">
                <tr><th className="text-left py-2">Associate</th><th className="text-right">Students</th><th className="text-right">Instr.</th><th className="text-right">Compl.</th></tr>
              </thead>
              <tbody>
                {cohorts.length === 0 && <tr><td colSpan={4} className="py-3 text-ink/50">No cohorts.</td></tr>}
                {cohorts.map((c) => (
                  <tr key={c.associate} className="border-t border-ink/5" data-testid={`cohort-${c.associate}`}>
                    <td className="py-2 font-heading font-bold">{c.associate}</td>
                    <td className="py-2 text-right font-mono">{c.students}</td>
                    <td className="py-2 text-right font-mono">{c.instructors}</td>
                    <td className="py-2 text-right font-mono">{c.completions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <h2 className="font-heading text-2xl font-bold mt-12 mb-3">Users <span className="text-ink/40 text-sm">({filtered.length} of {users.length})</span></h2>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap mb-4" data-testid="user-filters">
          <input placeholder="Search name or email…" value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })}
            className="px-3 py-2 border border-ink/20 text-sm w-64" data-testid="user-search" />
          <select value={filter.role} onChange={(e) => setFilter({ ...filter, role: e.target.value })}
            className="px-3 py-2 border border-ink/20 text-sm" data-testid="filter-role">
            <option value="">All roles</option>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={filter.active} onChange={(e) => setFilter({ ...filter, active: e.target.value })}
            className="px-3 py-2 border border-ink/20 text-sm" data-testid="filter-active">
            <option value="">All accounts</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
        </div>

        <div className="card-flat overflow-x-auto" data-testid="users-table">
          <table className="w-full text-sm">
            <thead className="bg-ink text-white">
              <tr>
                <Th>Name</Th><Th>Email</Th><Th>Role</Th><Th>Associate</Th><Th>Status</Th><Th className="text-right">Actions</Th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id} className={`border-b border-ink/10 hover:bg-bone ${u.is_active === false ? "opacity-50" : ""}`} data-testid={`user-${u.id}`}>
                  <Td>
                    {editing?.id === u.id ? (
                      <input value={editing.full_name} onChange={(e) => setEditing({ ...editing, full_name: e.target.value })}
                        className="px-2 py-1 border border-copper text-sm w-40" data-testid={`edit-name-${u.id}`} />
                    ) : <span className="font-heading font-bold">{u.full_name}</span>}
                  </Td>
                  <Td>
                    {editing?.id === u.id ? (
                      <input value={editing.email} onChange={(e) => setEditing({ ...editing, email: e.target.value })}
                        className="px-2 py-1 border border-copper text-xs w-48 font-mono" data-testid={`edit-email-${u.id}`} />
                    ) : <span className="font-mono text-xs">{u.email}</span>}
                  </Td>
                  <Td>
                    <select value={u.role} onChange={(e) => changeRole(u.id, e.target.value)}
                      className={`px-2 py-1 text-xs font-bold uppercase border ${u.role === "executive_admin" ? "bg-signal text-ink border-signal" : u.role === "admin" ? "bg-ink text-white border-ink" : u.role === "instructor" ? "bg-copper text-white border-copper" : "bg-white text-ink border-ink/20"}`}
                      data-testid={`role-select-${u.id}`}>
                      {ROLES.map((r) => <option key={r} value={r}>{r.replace("_", " ")}</option>)}
                    </select>
                  </Td>
                  <Td>
                    {editing?.id === u.id ? (
                      <input value={editing.associate || ""} onChange={(e) => setEditing({ ...editing, associate: e.target.value })}
                        className="px-2 py-1 border border-copper text-sm w-32" data-testid={`edit-associate-${u.id}`} />
                    ) : (
                      <input defaultValue={u.associate || ""} onBlur={(e) => { if (e.target.value !== (u.associate || "")) updateAssociate(u.id, e.target.value); }}
                        className="px-2 py-1 border border-ink/20 text-sm w-32" data-testid={`associate-input-${u.id}`} />
                    )}
                  </Td>
                  <Td>
                    {u.is_active === false
                      ? <span className="badge-outline text-destructive border-destructive" data-testid={`status-${u.id}`}>INACTIVE</span>
                      : <span className="badge-signal" data-testid={`status-${u.id}`}>ACTIVE</span>}
                  </Td>
                  <Td>
                    <div className="flex gap-1 justify-end items-center">
                      {editing?.id === u.id ? (
                        <>
                          <button onClick={saveEdit} className="px-2 py-1 text-xs font-bold bg-signal text-ink border border-ink" data-testid={`btn-save-${u.id}`}>Save</button>
                          <button onClick={() => setEditing(null)} className="px-2 py-1 text-xs font-bold bg-white border border-ink/20" data-testid={`btn-cancel-${u.id}`}>Cancel</button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => setEditing({ id: u.id, full_name: u.full_name, email: u.email, associate: u.associate || "" })} title="Edit name/email/associate"
                            className="p-1.5 border border-ink/20 hover:bg-ink hover:text-white" data-testid={`btn-edit-${u.id}`}>
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => resetPassword(u.id, u.email)} title="Reset password"
                            className="p-1.5 border border-ink/20 hover:bg-ink hover:text-white" data-testid={`btn-reset-${u.id}`}>
                            <KeyRound className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => setActive(u.id, u.is_active === false, u.email)}
                            title={u.is_active === false ? "Reactivate account" : "Deactivate account"}
                            className={`p-1.5 border ${u.is_active === false ? "border-signal/40 text-signal hover:bg-signal hover:text-ink" : "border-copper/40 text-copper hover:bg-copper hover:text-white"}`}
                            data-testid={`btn-toggle-active-${u.id}`}>
                            {u.is_active === false ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                          </button>
                          <button onClick={() => deleteUser(u.id, u.email)} title="Delete user"
                            className="p-1.5 border border-destructive/30 text-destructive hover:bg-destructive hover:text-white" data-testid={`btn-delete-${u.id}`}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </Td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="p-8 text-center text-ink/50">No users match the current filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-6 text-xs text-ink/50 flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          All role changes, edits, password resets, deactivations, and deletions are auto-logged in <a href="/admin/audit" className="underline hover:text-copper">Audit Log</a>.
        </div>
      </div>

      {resetLink && (
        <div
          className="fixed inset-0 z-40 bg-ink/60 flex items-center justify-center p-4"
          onClick={() => setResetLink(null)}
          data-testid="reset-link-modal"
        >
          <div className="bg-bone w-full max-w-lg p-6 border-2 border-ink" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between">
              <div>
                <div className="overline text-copper">One-shot reset link</div>
                <h3 className="font-heading text-2xl font-bold mt-1 flex items-center gap-2">
                  <Link2 className="w-5 h-5 text-copper" /> Share with {resetLink.email}
                </h3>
              </div>
              <button onClick={() => setResetLink(null)} className="p-1 hover:bg-ink/10" data-testid="reset-link-close">
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-ink/60 mt-3">
              {resetLink.email_sent
                ? "An email with this link was sent to the user. You can also share it directly:"
                : "No email provider configured — share this link with the user directly."}
            </p>
            <div className="mt-4 p-3 bg-white border border-ink/20 font-mono text-xs break-all" data-testid="reset-link-url">
              {resetLink.url}
            </div>
            <div className="text-xs text-ink/50 mt-2">
              Single-use. Expires {new Date(resetLink.expires_at).toLocaleString()}.
            </div>
            <div className="mt-5 flex gap-2">
              <button onClick={copyResetLink} className="btn-primary inline-flex items-center gap-2" data-testid="reset-link-copy">
                <Copy className="w-4 h-4" /> Copy link
              </button>
              <button onClick={() => setResetLink(null)} className="btn-secondary" data-testid="reset-link-done">
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function downloadCSV(rows, filename) {
  const csv = rows.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}

function Field({ label, value, onChange, type = "text", testid }) {
  return (
    <label className="block">
      <span className="overline text-ink/60">{label}</span>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 px-3 py-2 bg-white border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
        data-testid={testid} />
    </label>
  );
}
function Stat({ icon: Icon, label, value, testid, alert }) {
  return (
    <div className={`card-flat p-5 ${alert ? "border-l-4 border-l-destructive" : ""}`} data-testid={testid}>
      <Icon className={`w-5 h-5 ${alert ? "text-destructive" : "text-copper"}`} />
      <div className="font-heading text-3xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
const Th = ({ children, className = "" }) => <th className={`text-left px-4 py-3 overline text-xs font-bold ${className}`}>{children}</th>;
const Td = ({ children }) => <td className="px-4 py-3">{children}</td>;
