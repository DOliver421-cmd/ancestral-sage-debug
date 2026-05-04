import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { ScrollText, Download } from "lucide-react";

const ACTION_COLOR = (a) => a.includes("failed") ? "text-destructive" : a.includes("rejected") ? "text-destructive" : a.includes("approved") || a.includes("earned") || a.includes("success") ? "text-copper" : "text-ink/60";

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  useEffect(() => { api.get("/admin/audit?limit=300").then((r) => setLogs(r.data)); }, []);

  const exportCSV = () => {
    const rows = [["when", "actor_name", "actor_id", "action", "target", "meta"], ...logs.map((l) => [l.at, l.actor?.full_name || "system", l.actor_id || "", l.action, l.target || "", JSON.stringify(l.meta || {})])];
    const csv = rows.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `wai-audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="overline text-copper">Compliance & Security</div>
            <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><ScrollText className="w-8 h-8 text-copper" /> Audit Log</h1>
            <p className="text-ink/60 mt-2 max-w-2xl">Append-only record of every privileged action — for compliance audits, grant reporting, and incident forensics.</p>
          </div>
          <button onClick={exportCSV} disabled={logs.length === 0} className="btn-primary inline-flex items-center gap-2 disabled:opacity-50" data-testid="btn-audit-export">
            <Download className="w-4 h-4" /> Export CSV ({logs.length})
          </button>
        </div>

        <div className="card-flat mt-8 overflow-x-auto" data-testid="audit-table">
          <table className="w-full text-sm">
            <thead className="bg-ink text-white">
              <tr><Th>When</Th><Th>Actor</Th><Th>Action</Th><Th>Target</Th><Th>Meta</Th></tr>
            </thead>
            <tbody>
              {logs.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-ink/50">No audit entries.</td></tr>}
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-ink/5 hover:bg-bone" data-testid={`audit-${l.id}`}>
                  <Td><span className="font-mono text-xs">{new Date(l.at).toLocaleString()}</span></Td>
                  <Td>{l.actor ? <span className="font-heading font-bold">{l.actor.full_name}</span> : <span className="text-ink/40">system</span>}</Td>
                  <Td><span className={`font-mono font-bold text-xs ${ACTION_COLOR(l.action)}`}>{l.action}</span></Td>
                  <Td><span className="font-mono text-xs text-ink/60 truncate max-w-xs inline-block">{l.target || "—"}</span></Td>
                  <Td><span className="font-mono text-[10px] text-ink/50">{l.meta && Object.keys(l.meta).length ? JSON.stringify(l.meta) : ""}</span></Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
const Th = ({ children }) => <th className="text-left px-3 py-2 overline text-xs">{children}</th>;
const Td = ({ children }) => <td className="px-3 py-2 align-top">{children}</td>;
