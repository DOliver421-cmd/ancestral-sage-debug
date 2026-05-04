import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Users, GraduationCap, BookOpen, Award, Download } from "lucide-react";

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);

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
        <div className="flex items-center justify-between">
          <div>
            <div className="overline text-copper">Admin</div>
            <h1 className="font-heading text-4xl font-bold mt-2">Institute Overview</h1>
            <p className="text-ink/60 mt-2">Associates, curriculum, completions — end to end.</p>
          </div>
          <button onClick={exportCSV} className="btn-primary inline-flex items-center gap-2" data-testid="btn-export"><Download className="w-4 h-4" /> Export CSV</button>
        </div>

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
                <Th>Name</Th><Th>Email</Th><Th>Role</Th><Th>Associate</Th><Th></Th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-ink/10 hover:bg-bone" data-testid={`user-${u.id}`}>
                  <Td><span className="font-heading font-bold">{u.full_name}</span></Td>
                  <Td><span className="font-mono text-xs">{u.email}</span></Td>
                  <Td><span className={u.role === "admin" ? "badge-ink" : u.role === "instructor" ? "badge-copper" : "badge-outline"}>{u.role}</span></Td>
                  <Td>
                    <input defaultValue={u.associate || ""} onBlur={(e) => { if (e.target.value !== (u.associate || "")) updateAssociate(u.id, e.target.value); }}
                      className="px-2 py-1 border border-ink/20 text-sm w-32" data-testid={`associate-input-${u.id}`} />
                  </Td>
                  <Td></Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
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
const Th = ({ children }) => <th className="text-left px-4 py-3 overline text-xs font-bold">{children}</th>;
const Td = ({ children }) => <td className="px-4 py-3">{children}</td>;
