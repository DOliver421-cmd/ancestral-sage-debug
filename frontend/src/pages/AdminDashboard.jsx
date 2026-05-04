import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Users, GraduationCap, BookOpen, Award, Download, UserPlus, Trash2, KeyRound, ShieldCheck } from "lucide-react";

const ROLES = ["student", "instructor", "admin"];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ email: "", full_name: "", password: "", role: "student", associate: "Associate-Alpha" });

  const load = () => {
    api.get("/admin/stats").then((r) => setStats(r.data));
    api.get("/admin/users").then((r) => setUsers(r.data));
  };
  useEffect(load, []);

  const updateAssociate = async (user_id, associate) => {
    try {
      await api.post("/admin/associate", { user_id, associate });
      toast.success("Associate updated");
      load();
    } catch { toast.error("Update failed"); }
  };

  const changeRole = async (uid, role) => {
    try {
      await api.patch(`/admin/users/${uid}/role`, { role });
      toast.success(`Role set to ${role}`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Role update failed"); }
  };

  const deleteUser = async (uid, email) => {
    if (!window.confirm(`Permanently delete ${email}? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/users/${uid}`);
      toast.success("User deleted");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Delete failed"); }
  };

  const resetPassword = async (uid, email) => {
    const newPass = window.prompt(`New password for ${email}? (min 6 chars)`);
    if (!newPass || newPass.length < 6) { toast.error("Password too short"); return; }
    try {
      await api.post(`/admin/users/${uid}/password`, { new_password: newPass });
      toast.success(`Password reset for ${email}. Share it securely.`);
    } catch (e) { toast.error(e?.response?.data?.detail || "Reset failed"); }
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

  const exportCSV = () => {
    const rows = [["name", "email", "role", "associate", "created_at"], ...users.map((u) => [u.full_name, u.email, u.role, u.associate || "", u.created_at])];
    const csv = rows.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "lce-wai-users.csv";
    a.click();
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

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
          <Stat icon={Users} label="Total Users" value={stats?.users ?? "—"} testid="stat-users" />
          <Stat icon={GraduationCap} label="Students" value={stats?.students ?? "—"} testid="stat-students" />
          <Stat icon={Users} label="Instructors" value={stats?.instructors ?? "—"} testid="stat-instructors" />
          <Stat icon={BookOpen} label="Modules" value={stats?.modules ?? "—"} testid="stat-modules" />
          <Stat icon={Award} label="Completions" value={stats?.completions ?? "—"} testid="stat-completions" />
        </div>

        <h2 className="font-heading text-2xl font-bold mt-12 mb-4">Users</h2>
        <div className="card-flat overflow-x-auto" data-testid="users-table">
          <table className="w-full text-sm">
            <thead className="bg-ink text-white">
              <tr>
                <Th>Name</Th><Th>Email</Th><Th>Role</Th><Th>Associate</Th><Th className="text-right">Actions</Th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-ink/10 hover:bg-bone" data-testid={`user-${u.id}`}>
                  <Td><span className="font-heading font-bold">{u.full_name}</span></Td>
                  <Td><span className="font-mono text-xs">{u.email}</span></Td>
                  <Td>
                    <select value={u.role} onChange={(e) => changeRole(u.id, e.target.value)}
                      className={`px-2 py-1 text-xs font-bold uppercase border ${u.role === "admin" ? "bg-ink text-white border-ink" : u.role === "instructor" ? "bg-copper text-white border-copper" : "bg-white text-ink border-ink/20"}`}
                      data-testid={`role-select-${u.id}`}>
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </Td>
                  <Td>
                    <input defaultValue={u.associate || ""} onBlur={(e) => { if (e.target.value !== (u.associate || "")) updateAssociate(u.id, e.target.value); }}
                      className="px-2 py-1 border border-ink/20 text-sm w-32" data-testid={`associate-input-${u.id}`} />
                  </Td>
                  <Td>
                    <div className="flex gap-1 justify-end">
                      <button onClick={() => resetPassword(u.id, u.email)} title="Reset password"
                        className="p-1.5 border border-ink/20 hover:bg-ink hover:text-white" data-testid={`btn-reset-${u.id}`}>
                        <KeyRound className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => deleteUser(u.id, u.email)} title="Delete user"
                        className="p-1.5 border border-destructive/30 text-destructive hover:bg-destructive hover:text-white" data-testid={`btn-delete-${u.id}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-6 text-xs text-ink/50 flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5" />
          Role changes, password resets, and deletions are auto-logged in <a href="/admin/audit" className="underline hover:text-copper">Audit Log</a>.
        </div>
      </div>
    </AppShell>
  );
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
function Stat({ icon: Icon, label, value, testid }) {
  return (
    <div className="card-flat p-5" data-testid={testid}>
      <Icon className="w-5 h-5 text-copper" />
      <div className="font-heading text-3xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
const Th = ({ children, className = "" }) => <th className={`text-left px-4 py-3 overline text-xs font-bold ${className}`}>{children}</th>;
const Td = ({ children }) => <td className="px-4 py-3">{children}</td>;
