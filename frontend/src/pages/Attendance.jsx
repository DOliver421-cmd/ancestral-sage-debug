import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Calendar, Save, Download } from "lucide-react";

export default function Attendance() {
  const [roster, setRoster] = useState([]);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [statuses, setStatuses] = useState({});
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/attendance/roster").then((r) => setRoster(r.data));
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const setStatus = (id, s) => setStatuses({ ...statuses, [id]: s });

  const exportCSV = () => {
    const rows = [["full_name", "associate", "present", "absent", "tardy", "excused", "total", "rate_%"], ...roster.map((r) => [r.full_name, r.associate || "", r.present, r.absent, r.tardy, r.excused, r.total, r.rate])];
    const csv = rows.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `wai-attendance-summary-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  const save = async () => {
    const attendees = roster.map((r) => ({ user_id: r.user_id, status: statuses[r.user_id] || "present" }));
    setSaving(true);
    try {
      await api.post("/attendance", { date, attendees });
      toast.success(`Saved ${attendees.length} entries for ${date}`);
      setStatuses({});
      load();
    } catch { toast.error("Save failed"); }
    setSaving(false);
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-5xl">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="overline text-copper">Instructor</div>
            <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><Calendar className="w-8 h-8 text-copper" /> Attendance</h1>
            <p className="text-ink/60 mt-2 max-w-2xl">Daily roll for grant reporting and incident traceability.</p>
          </div>
          <button onClick={exportCSV} disabled={roster.length === 0} className="btn-primary inline-flex items-center gap-2 disabled:opacity-50" data-testid="btn-attendance-export">
            <Download className="w-4 h-4" /> Export Roster CSV
          </button>
        </div>

        <div className="card-flat p-6 mt-8" data-testid="attendance-form">
          <div className="flex items-center gap-4 flex-wrap">
            <div>
              <label className="overline text-ink/60">Session date</label>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                className="block mt-1 px-3 py-2 border border-ink/20 text-sm font-mono"
                data-testid="attendance-date" />
            </div>
            <button onClick={save} disabled={saving || roster.length === 0} className="btn-primary inline-flex items-center gap-2 ml-auto" data-testid="btn-save-attendance">
              <Save className="w-4 h-4" /> {saving ? "Saving…" : "Save Roll"}
            </button>
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-ink text-white">
                <tr><Th>Apprentice</Th><Th>Associate</Th><Th>Rate</Th><Th>Status</Th></tr>
              </thead>
              <tbody>
                {roster.length === 0 && <tr><td colSpan={4} className="p-6 text-center text-ink/50">No students.</td></tr>}
                {roster.map((r) => (
                  <tr key={r.user_id} className="border-b border-ink/10" data-testid={`row-${r.user_id}`}>
                    <Td><span className="font-heading font-bold">{r.full_name}</span></Td>
                    <Td>{r.associate || "—"}</Td>
                    <Td><span className="font-mono">{r.rate}%</span> <span className="text-xs text-ink/50">({r.total} sessions)</span></Td>
                    <Td>
                      <div className="flex gap-1">
                        {["present", "absent", "tardy", "excused"].map((s) => (
                          <button key={s} onClick={() => setStatus(r.user_id, s)}
                            className={`px-2 py-1 text-[10px] uppercase font-bold border ${statuses[r.user_id] === s || (!statuses[r.user_id] && s === "present") ? (s === "present" ? "bg-signal text-ink border-ink" : s === "absent" ? "bg-destructive text-white border-destructive" : s === "tardy" ? "bg-copper text-white border-copper" : "bg-ink text-white border-ink") : "bg-white text-ink border-ink/20"}`}
                            data-testid={`att-${r.user_id}-${s}`}>{s[0].toUpperCase()}</button>
                        ))}
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
const Th = ({ children }) => <th className="text-left px-3 py-2 overline text-xs">{children}</th>;
const Td = ({ children }) => <td className="px-3 py-2">{children}</td>;
