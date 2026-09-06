import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { TrackTag } from "./academyKit";
import { ArrowLeft, FileText, Printer, AlertCircle, RefreshCw } from "lucide-react";
import { WAI_LOGO } from "../../lib/brand";

/* /academy/records?student=… — printable student educational records /
   progress documentation. Explicitly not a legal transcript. */

export default function AcademyRecords() {
  const [params] = useSearchParams();
  const studentId = params.get("student");
  const [rec, setRec] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!studentId) { setError("Choose a student to view records."); setLoading(false); return; }
    api.get(`/academy/students/${studentId}/records`)
      .then((r) => setRec(r.data))
      .catch((e) => setError(e?.response?.data?.detail || "Could not load records."))
      .finally(() => setLoading(false));
  }, [studentId]);

  const s = rec?.student;
  const fmt = (iso) => {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); }
    catch { return iso; }
  };

  return (
    <AppShell>
      <div className="px-10 py-10">
        <div className="flex items-center justify-between max-w-4xl">
          <Link to={studentId ? `/academy/student/${studentId}` : "/academy/parent"} className="inline-flex items-center gap-1.5 text-sm font-bold text-copper hover:text-ink transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
          <button onClick={() => window.print()} className="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-signal font-black rounded-lg hover:bg-ink/85 transition-colors" data-testid="print-records">
            <Printer className="w-4 h-4" /> Print / Save PDF
          </button>
        </div>

        {loading && <p className="max-w-4xl py-12 flex items-center gap-2 text-ink/45"><RefreshCw className="w-4 h-4 animate-spin" /> Loading records…</p>}
        {error && (
          <div className="max-w-4xl py-12">
            <div className="card-flat p-8 flex items-start gap-3 border-destructive/30 bg-destructive/5 text-destructive"><AlertCircle className="w-5 h-5 shrink-0" /> {error}</div>
          </div>
        )}

        {rec && s && (
          <div id="academy-record" className="mt-6 max-w-4xl bg-white border border-ink/15 shadow-sm" data-testid="records-doc">
            <style>{`
              @media print {
                body * { visibility: hidden; }
                #academy-record, #academy-record * { visibility: visible; }
                #academy-record { position: absolute; left: 0; top: 0; width: 100%; border: none; }
              }
            `}</style>
            {/* Header */}
            <div className="bg-ink text-white px-10 py-8 flex items-center justify-between gap-6 print:bg-white print:text-black print:border-b print:border-black">
              <div className="flex items-center gap-4">
                <img src={WAI_LOGO} alt="" className="w-12 h-12 object-contain" />
                <div>
                  <div className="text-[10px] font-black uppercase tracking-[0.3em] text-signal print:text-black">WAI Institute Homeschool Academy</div>
                  <div className="font-heading font-black text-xl">Student Educational Record</div>
                </div>
              </div>
              <div className="text-right text-xs text-white/60 print:text-black/70">
                <div>Issued {fmt(rec.generated_at)}</div>
                <div>Progress documentation</div>
              </div>
            </div>

            {/* Student block */}
            <div className="px-10 py-6 border-b border-ink/10 grid sm:grid-cols-2 gap-4">
              <div>
                <Label>Student</Label>
                <div className="font-heading text-2xl font-black text-ink">{s.name}</div>
              </div>
              <div className="flex flex-wrap gap-6">
                <div><Label>Grade</Label><div className="font-bold text-ink">{s.grade === "K" ? "Kindergarten" : `Grade ${s.grade}`}</div></div>
                <div><Label>Track</Label><div className="font-bold text-ink capitalize">{s.track}</div></div>
                <div><Label>Enrolled</Label><div className="font-bold text-ink">{fmt(s.created_at)}</div></div>
              </div>
            </div>

            {/* Summary */}
            <div className="px-10 py-5 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-bone/70 print:bg-white">
              <MiniStat label="Courses" value={rec.rows.length} />
              <MiniStat label="Completed" value={rec.summary.courses_completed} />
              <MiniStat label="Lessons passed" value={`${rec.summary.lessons_passed}/${rec.summary.lessons_total}`} />
              <MiniStat label="In progress" value={rec.summary.courses_in_progress} />
            </div>

            {/* Course rows */}
            <div className="px-10 py-8 space-y-8">
              {rec.rows.length === 0 && (
                <p className="text-ink/55 italic">No enrolled courses with published content yet.</p>
              )}
              {rec.rows.map((row) => (
                <div key={row.course_slug}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-widest text-copper print:text-black">{row.subject_label} · {row.grade_label}</div>
                      <div className="font-heading text-lg font-black text-ink">{row.course_title}</div>
                    </div>
                    <span className={`text-xs font-black uppercase tracking-wider px-3 py-1 rounded-full border ${
                      row.status === "completed"
                        ? "text-emerald-700 border-emerald-600/40 bg-emerald-600/5"
                        : row.status === "in_progress"
                          ? "text-copper border-copper/40 bg-copper/5"
                          : "text-ink/45 border-ink/15 bg-ink/5"
                    }`}>{row.status.replace("_", " ")}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                    <MiniStat label="Lessons" value={`${row.stats.lessons_passed}/${row.stats.lessons_total}`} />
                    <MiniStat label="Course %" value={`${row.stats.percent}%`} />
                    <MiniStat label="Mastery avg" value={row.stats.mastery_avg != null ? `${row.stats.mastery_avg}%` : "—"} />
                    <MiniStat label="Pass line" value={`${row.passing_score}%`} />
                  </div>
                  {row.status === "completed" && row.passed_lessons.length > 0 && (
                    <div className="text-xs text-ink/50 mt-2">Completed {fmt(row.passed_lessons[row.passed_lessons.length - 1].passed_at)}</div>
                  )}
                  {row.status === "in_progress" && (
                    <div className="mt-3 border-t border-ink/10 pt-2 space-y-1">
                      {row.passed_lessons.map((p) => (
                        <div key={p.title} className="flex items-center justify-between text-xs text-ink/65">
                          <span className="font-semibold">{p.title}</span>
                          <span>mastered {p.score}% · {fmt(p.passed_at)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Footer note */}
              <div className="border-t border-ink/15 pt-5 text-[11px] text-ink/45 leading-relaxed space-y-1">
                <p>{rec.disclaimer}</p>
                <p>Record generated from actual completed lesson activity in the Academy. Dates are shown for each mastered lesson above.</p>
                <p className="font-bold">WAI Institute Homeschool Academy · part of M.O.R.E. Help Center (morehelp.center) · wai-institute.org</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function Label({ children }) {
  return <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-0.5">{children}</div>;
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded-lg border border-ink/10 bg-white px-3 py-2.5 print:border-black/20">
      <div className="font-heading text-lg font-black text-ink leading-tight">{value}</div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-ink/45">{label}</div>
    </div>
  );
}
