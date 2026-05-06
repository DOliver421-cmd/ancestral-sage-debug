import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import { ClipboardCheck, Download } from "lucide-react";

export default function InstructorLabs() {
  const [subs, setSubs] = useState([]);
  const [report, setReport] = useState([]);
  const [tab, setTab] = useState("pending");
  const [feedback, setFeedback] = useState({});

  const load = useCallback(() => Promise.all([
    api.get("/instructor/submissions").then((r) => setSubs(r.data)),
    api.get("/instructor/lab-report").then((r) => setReport(r.data)),
  ]), []);
  useEffect(() => { load(); }, [load]);

  const review = async (sub_id, status) => {
    try {
      await api.post(`/instructor/submissions/${sub_id}/review`, { status, feedback: feedback[sub_id] || "" });
      toast.success(`Submission ${status}`);
      load();
    } catch { toast.error("Review failed"); }
  };

  const exportCSV = () => {
    const rows = [["name", "email", "associate", "labs_passed", "labs_pending", "skill_points", "lab_hours"],
      ...report.map((r) => [r.full_name, r.email, r.associate || "", r.labs_passed, r.labs_pending, r.skill_points, r.lab_hours])];
    const csv = rows.map((r) => r.map((c) => `"${(c ?? "").toString().replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "lce-wai-lab-report.csv";
    a.click();
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-start justify-between">
          <div>
            <div className="overline text-copper">Instructor</div>
            <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><ClipboardCheck className="w-8 h-8 text-copper" /> Lab Approvals & Reports</h1>
            <p className="text-ink/60 mt-2">Review in-person lab submissions. Approve, reject, or send feedback.</p>
          </div>
          <button onClick={exportCSV} className="btn-primary inline-flex items-center gap-2" data-testid="btn-export-lab-report"><Download className="w-4 h-4" /> Export Report</button>
        </div>

        <div className="flex gap-2 mt-8" data-testid="inst-tabs">
          {[["pending", `Pending (${subs.length})`], ["report", "Performance Report"]].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-5 py-3 text-sm font-bold uppercase tracking-widest border transition-all ${tab === k ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
              data-testid={`inst-tab-${k}`}>{label}</button>
          ))}
        </div>

        {tab === "pending" ? (
          <div className="mt-6 space-y-4">
            {subs.length === 0 && (
              <div className="card-flat p-12 text-center">
                <ClipboardCheck className="w-12 h-12 text-ink/30 mx-auto" />
                <div className="font-heading text-xl font-bold mt-4">Nothing pending</div>
                <div className="text-sm text-ink/60 mt-2">All in-person submissions have been reviewed.</div>
              </div>
            )}
            {subs.map((s) => (
              <div key={s.id} className="card-flat p-6" data-testid={`sub-${s.id}`}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="overline text-copper">{s.lab?.track?.toUpperCase()} · {s.lab?.skill_points}pts</div>
                    <div className="font-heading text-xl font-bold mt-2">{s.lab?.title}</div>
                    <div className="text-sm text-ink/70 mt-1">
                      Submitted by <span className="font-bold">{s.user?.full_name}</span> ({s.user?.email})
                    </div>
                  </div>
                  <span className="badge-copper">Pending</span>
                </div>

                {s.photo_url && (
                  <div className="mt-4">
                    <div className="overline text-ink/60">Submitted work</div>
                    <a href={s.photo_url} target="_blank" rel="noreferrer" className="text-copper font-mono text-sm underline break-all">{s.photo_url}</a>
                  </div>
                )}
                {s.notes && (
                  <div className="mt-3 bg-bone p-3 border border-ink/10 text-sm">
                    <div className="overline text-ink/60 mb-1">Student notes</div>
                    <div>{s.notes}</div>
                  </div>
                )}

                <div className="mt-4">
                  <div className="overline text-copper">Rubric</div>
                  <ul className="mt-2 space-y-1 text-sm text-ink/80">{s.lab?.rubric?.map((r, i) => <li key={i}>— {r}</li>)}</ul>
                </div>

                <textarea value={feedback[s.id] || ""} onChange={(e) => setFeedback({ ...feedback, [s.id]: e.target.value })}
                  placeholder="Feedback to the apprentice…" rows={3}
                  className="w-full mt-4 px-3 py-2 border border-ink/20 focus:border-ink focus:outline-none focus:ring-2 focus:ring-signal text-sm"
                  data-testid={`feedback-${s.id}`} />

                <div className="flex gap-2 mt-3">
                  <button onClick={() => review(s.id, "approved")} className="btn-copper" data-testid={`approve-${s.id}`}>Approve</button>
                  <button onClick={() => review(s.id, "rejected")} className="btn-ghost text-destructive border-destructive hover:bg-destructive hover:text-white" data-testid={`reject-${s.id}`}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card-flat mt-6 overflow-x-auto" data-testid="lab-report-table">
            <table className="w-full text-sm">
              <thead className="bg-ink text-white">
                <tr>
                  <Th>Apprentice</Th><Th>Associate</Th><Th>Passed</Th><Th>Pending</Th><Th>Points</Th><Th>Hours</Th>
                </tr>
              </thead>
              <tbody>
                {report.length === 0 && <tr><td colSpan={6} className="p-8 text-center text-ink/50">No data.</td></tr>}
                {report.map((r) => (
                  <tr key={r.user_id} className="border-b border-ink/10 hover:bg-bone" data-testid={`report-row-${r.user_id}`}>
                    <Td><span className="font-heading font-bold">{r.full_name}</span><div className="text-xs text-ink/50 font-mono">{r.email}</div></Td>
                    <Td>{r.associate || "—"}</Td>
                    <Td>{r.labs_passed}</Td>
                    <Td>{r.labs_pending}</Td>
                    <Td><span className="font-mono font-bold">{r.skill_points}</span></Td>
                    <Td>{r.lab_hours}h</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}

const Th = ({ children }) => <th className="text-left px-4 py-3 overline text-xs font-bold">{children}</th>;
const Td = ({ children }) => <td className="px-4 py-3">{children}</td>;
