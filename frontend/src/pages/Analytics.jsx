import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { TrendingUp, AlertTriangle, Users, BookOpen, Award, Activity, ShieldAlert, Clock, Download } from "lucide-react";

export default function Analytics() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/analytics/program").then((r) => setData(r.data)); }, []);
  if (!data) return <AppShell><div className="p-10">Loading…</div></AppShell>;
  const t = data.totals;

  const exportCSV = () => {
    const lines = [];
    lines.push(["section", "key", "value"]);
    Object.entries(t).forEach(([k, v]) => lines.push(["totals", k, v]));
    data.by_associate.forEach((a) => lines.push(["by_associate", a.associate, `${a.students} students / ${a.completions} completions`]));
    data.weakest_competencies.forEach((w) => lines.push(["weakest_competencies", w.name, w.points]));
    data.module_completion_rates.forEach((m) => lines.push(["module_completion_rates", m.title, `${m.completions} (${m.rate}%)`]));
    const csv = lines.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `wai-analytics-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="overline text-copper">Program Analytics</div>
            <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><TrendingUp className="w-8 h-8 text-copper" /> Program Health</h1>
            <p className="text-ink/60 mt-2 max-w-2xl">Cohort-wide view of completions, credential status, weak spots, and operational risk — refreshed every page load.</p>
          </div>
          <button onClick={exportCSV} className="btn-primary inline-flex items-center gap-2" data-testid="btn-analytics-export">
            <Download className="w-4 h-4" /> Export CSV
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
          <Stat icon={Users} label="Students" value={t.students} />
          <Stat icon={Users} label="Instructors" value={t.instructors} />
          <Stat icon={Activity} label="Active 30d" value={t.active_30d} />
          <Stat icon={BookOpen} label="Module Completions" value={t.module_completions} />
          <Stat icon={Award} label="Credentials Issued" value={t.credentials_issued} highlight />
          <Stat icon={Clock} label="Labs Pending Review" value={t.labs_pending_review} alert={t.labs_pending_review > 5} />
          <Stat icon={AlertTriangle} label="Credentials Expiring 90d" value={t.credentials_expiring_90d} alert={t.credentials_expiring_90d > 0} />
          <Stat icon={ShieldAlert} label="Open Incidents" value={t.open_incidents} alert={t.open_incidents > 0} />
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mt-10">
          <div className="card-flat p-6" data-testid="by-associate">
            <h2 className="font-heading text-xl font-bold">By Associate Group</h2>
            <table className="w-full mt-4 text-sm">
              <thead className="bg-bone"><tr><Th>Associate</Th><Th>Students</Th><Th>Completions</Th></tr></thead>
              <tbody>
                {data.by_associate.map((a) => (
                  <tr key={a.associate} className="border-b border-ink/10"><Td>{a.associate}</Td><Td>{a.students}</Td><Td className="font-mono font-bold">{a.completions}</Td></tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card-flat p-6" data-testid="weakest-comps">
            <h2 className="font-heading text-xl font-bold">Weakest Cohort Competencies</h2>
            <div className="mt-4 space-y-3">
              {data.weakest_competencies.map((w) => (
                <div key={w.key} className="p-3 border-l-4 border-copper bg-bone">
                  <div className="font-heading font-bold text-sm">{w.name}</div>
                  <div className="font-mono text-xs text-ink/60 mt-1">{w.points} cohort points · invest in remediation labs here</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card-flat p-6 mt-6" data-testid="completion-rates">
          <h2 className="font-heading text-xl font-bold">Module Completion Rates</h2>
          <div className="mt-4 space-y-2">
            {data.module_completion_rates.map((m) => (
              <div key={m.slug} className="flex items-center gap-4">
                <div className="flex-1 text-sm font-heading font-semibold truncate">{m.title}</div>
                <div className="font-mono text-xs text-ink/60 w-24 text-right">{m.completions} / {t.students}</div>
                <div className="w-32 h-2 bg-ink/10">
                  <div className="h-full bg-copper" style={{ width: `${m.rate}%` }} />
                </div>
                <div className="font-mono text-xs w-12 text-right">{m.rate}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ icon: Icon, label, value, highlight, alert }) {
  return (
    <div className={`card-flat p-4 ${highlight ? "bg-signal border-ink" : alert ? "border-destructive border-2" : ""}`}>
      <Icon className={`w-4 h-4 ${highlight ? "text-ink" : alert ? "text-destructive" : "text-copper"}`} />
      <div className="font-heading text-2xl font-black mt-2">{value}</div>
      <div className="overline text-ink/60 text-[10px] mt-1">{label}</div>
    </div>
  );
}
const Th = ({ children }) => <th className="text-left px-3 py-2 overline text-xs">{children}</th>;
const Td = ({ children, className = "" }) => <td className={`px-3 py-2 ${className}`}>{children}</td>;
