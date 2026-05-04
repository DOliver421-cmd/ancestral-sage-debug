import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Users, Clock, Award } from "lucide-react";

export default function InstructorDashboard() {
  const [roster, setRoster] = useState([]);
  useEffect(() => { api.get("/roster").then((r) => setRoster(r.data)).catch(() => {}); }, []);

  const totalHours = roster.reduce((a, s) => a + (s.hours || 0), 0);
  const totalCompletions = roster.reduce((a, s) => a + (s.modules_completed || 0), 0);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Instructor</div>
        <h1 className="font-heading text-4xl font-bold mt-2">Class Roster</h1>
        <p className="text-ink/60 mt-2">Watch the associate. Unlock modules. Sign off skill demonstrations.</p>

        <div className="grid grid-cols-3 gap-5 mt-8">
          <Stat icon={Users} label="Apprentices" value={roster.length} testid="stat-apprentices" />
          <Stat icon={Award} label="Modules Completed" value={totalCompletions} testid="stat-completions" />
          <Stat icon={Clock} label="Associate Hours" value={totalHours} testid="stat-associate-hours" />
        </div>

        <div className="card-flat mt-8 overflow-x-auto" data-testid="roster-table">
          <table className="w-full text-sm">
            <thead className="bg-ink text-white">
              <tr>
                <Th>Apprentice</Th>
                <Th>Email</Th>
                <Th>Associate</Th>
                <Th>Modules</Th>
                <Th>Hours</Th>
                <Th>Avg Score</Th>
              </tr>
            </thead>
            <tbody>
              {roster.length === 0 && (
                <tr><td colSpan={6} className="p-8 text-center text-ink/50">No apprentices enrolled yet.</td></tr>
              )}
              {roster.map((s) => (
                <tr key={s.id} className="border-b border-ink/10 hover:bg-bone" data-testid={`row-${s.id}`}>
                  <Td><span className="font-heading font-bold">{s.full_name}</span></Td>
                  <Td><span className="font-mono text-xs">{s.email}</span></Td>
                  <Td>{s.associate || "—"}</Td>
                  <Td>{s.modules_completed}/12</Td>
                  <Td>{s.hours}h</Td>
                  <Td>{s.avg_score ? `${s.avg_score}%` : "—"}</Td>
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
    <div className="card-flat p-6" data-testid={testid}>
      <Icon className="w-5 h-5 text-copper" />
      <div className="font-heading text-3xl font-black mt-3">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
const Th = ({ children }) => <th className="text-left px-4 py-3 overline text-xs font-bold">{children}</th>;
const Td = ({ children }) => <td className="px-4 py-3">{children}</td>;
