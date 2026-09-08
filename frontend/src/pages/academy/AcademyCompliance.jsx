import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { ArrowLeft, FileText, Printer, AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { WAI_LOGO } from "../../lib/brand";

/* /academy/compliance?student=… — Florida homeschool compliance document
   generator: Notice of Intent, quarterly reports, annual evaluation packet,
   parent-issued transcript (Bright Futures), and IHIP-style plans. */

const KINDS = [
  { id: "notice_of_intent", label: "Notice of Intent", desc: "File with your county district to start a home education program (s. 1002.41, F.S.)." },
  { id: "quarterly_report", label: "Quarterly Progress Report", desc: "Progress summary for umbrella schools or families moving from quarterly-reporting states." },
  { id: "annual_evaluation", label: "Annual Evaluation Packet", desc: "Portfolio summary for your Florida-certified teacher evaluator (s. 1002.41(1)(f))." },
  { id: "transcript", label: "High School Transcript", desc: "Parent-issued transcript for Bright Futures / FDOE submission." },
  { id: "ihip", label: "IHIP-Style Plan", desc: "For families relocating from states requiring individualized home instruction plans." },
];

const YEAR = "2026-2027";

export default function AcademyCompliance() {
  const [params] = useSearchParams();
  const studentId = params.get("student");
  const [students, setStudents] = useState([]);
  const [kind, setKind] = useState("notice_of_intent");
  const [district, setDistrict] = useState("");
  const [evaluator, setEvaluator] = useState("");
  const [notes, setNotes] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [doc, setDoc] = useState(null);
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.get("/academy/students")
      .then((r) => setStudents(r.data.students || []))
      .catch(() => setError("Could not load students."))
      .finally(() => setLoading(false));
    if (studentId) {
      api.get(`/academy/compliance/docs?student_id=${studentId}`)
        .then((r) => setDocs(r.data.docs || []))
        .catch(() => {});
    }
  }, [studentId]);

  const generate = () => {
    if (!studentId) { setError("Choose a student first."); return; }
    setGenerating(true);
    setError("");
    api.post("/academy/compliance/generate", {
      kind,
      student_id: studentId,
      school_year: YEAR,
      district: district || undefined,
      evaluator_name: evaluator || undefined,
      notes: notes || undefined,
      period_start: periodStart || undefined,
      period_end: periodEnd || undefined,
    })
      .then((r) => setDoc(r.data.doc))
      .catch((e) => setError(e?.response?.data?.detail || "Could not generate document."))
      .finally(() => setGenerating(false));
  };

  const s = students.find((x) => x.id === studentId);
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
          {doc && (
            <button onClick={() => window.print()} className="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-signal font-black rounded-lg hover:bg-ink/85 transition-colors" data-testid="print-compliance">
              <Printer className="w-4 h-4" /> Print / Save PDF
            </button>
          )}
        </div>

        <h1 className="text-3xl font-black text-ink mt-4">Florida Compliance Documents</h1>
        <p className="text-ink/60 max-w-2xl mt-2">
          Generate the paperwork Florida home education law expects — Notice of Intent,
          annual evaluation packets, and Bright Futures-ready transcripts — from your
          child's actual Academy records.
        </p>

        {error && (
          <div className="max-w-4xl mt-6 card-flat p-6 flex items-start gap-3 border-destructive/30 bg-destructive/5 text-destructive">
            <AlertCircle className="w-5 h-5 shrink-0" /> {error}
          </div>
        )}

        {/* Generator */}
        <div className="max-w-4xl mt-6 card-flat p-6 space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-ink/50">
            <ShieldCheck className="w-4 h-4 text-copper" /> Document generator
          </div>

          <div>
            <label className="block text-sm font-bold text-ink mb-1">Student</label>
            <select value={studentId || ""} onChange={(e) => window.location.assign(`/academy/compliance?student=${e.target.value}`)} className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm bg-white" data-testid="compliance-student-select">
              <option value="">Choose a student…</option>
              {students.map((st) => <option key={st.id} value={st.id}>{st.name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-bold text-ink mb-1">Document type</label>
            <div className="grid sm:grid-cols-2 gap-2">
              {KINDS.map((k) => (
                <button key={k.id} onClick={() => setKind(k.id)}
                  className={`text-left p-3 rounded-lg border-2 transition-colors ${kind === k.id ? "border-copper bg-copper/5" : "border-ink/10 hover:border-ink/30"}`}
                  data-testid={`kind-${k.id}`}>
                  <div className="font-bold text-sm text-ink">{k.label}</div>
                  <div className="text-xs text-ink/55 mt-0.5">{k.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-bold text-ink mb-1">School year</label>
              <input value={YEAR} readOnly className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm bg-ink/5" />
            </div>
            {(kind === "notice_of_intent" || kind === "annual_evaluation") && (
              <div>
                <label className="block text-sm font-bold text-ink mb-1">County district (optional)</label>
                <input value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="e.g. Miami-Dade" className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
              </div>
            )}
            {kind === "annual_evaluation" && (
              <div>
                <label className="block text-sm font-bold text-ink mb-1">Evaluator name (optional)</label>
                <input value={evaluator} onChange={(e) => setEvaluator(e.target.value)} className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
              </div>
            )}
            {kind === "quarterly_report" && (
              <>
                <div>
                  <label className="block text-sm font-bold text-ink mb-1">Period start</label>
                  <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-bold text-ink mb-1">Period end</label>
                  <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
                </div>
              </>
            )}
          </div>

          <div>
            <label className="block text-sm font-bold text-ink mb-1">Notes (optional)</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full border-2 border-ink/15 rounded-lg px-3 py-2.5 text-sm" />
          </div>

          <button onClick={generate} disabled={generating || !studentId}
            className="inline-flex items-center gap-2 px-6 py-3 bg-copper text-white font-black rounded-lg hover:bg-copper/85 disabled:opacity-50 transition-colors"
            data-testid="generate-compliance">
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
            {generating ? "Generating…" : "Generate document"}
          </button>
        </div>

        {/* Generated document */}
        {doc && (
          <div id="compliance-doc" className="mt-8 max-w-4xl bg-white border border-ink/15 shadow-sm" data-testid="compliance-doc">
            <style>{`
              @media print {
                body * { visibility: hidden; }
                #compliance-doc, #compliance-doc * { visibility: visible; }
                #compliance-doc { position: absolute; left: 0; top: 0; width: 100%; border: none; }
              }
            `}</style>
            <div className="p-8">
              <div className="flex items-start justify-between border-b-2 border-ink/10 pb-4">
                <div className="flex items-center gap-3">
                  {WAI_LOGO && <img src={WAI_LOGO} alt="WAI Institute" className="w-12 h-12" />}
                  <div>
                    <div className="font-black text-ink text-lg">WAI Institute Homeschool Academy</div>
                    <div className="text-xs text-ink/50">at MoreHelp Center</div>
                  </div>
                </div>
                <div className="text-right text-xs text-ink/50">
                  <div>School year {doc.school_year}</div>
                  <div>Generated {fmt(doc.generated_at)}</div>
                </div>
              </div>

              <h2 className="text-xl font-black text-ink mt-6">{doc.payload?.title}</h2>
              {doc.payload?.statute && <div className="text-xs text-ink/50 mt-1">{doc.payload.statute}</div>}

              {doc.payload?.body && <p className="text-sm text-ink/80 mt-4 leading-relaxed">{doc.payload.body}</p>}

              {s && (
                <div className="mt-4 text-sm text-ink/80 grid grid-cols-2 gap-1">
                  <div><strong>Student:</strong> {s.name}</div>
                  <div><strong>Grade:</strong> {s.grade || s.grade_label || "—"}</div>
                  {doc.district && <div><strong>District:</strong> {doc.district}</div>}
                  {doc.evaluator_name && <div><strong>Evaluator:</strong> {doc.evaluator_name}</div>}
                </div>
              )}

              {doc.payload?.rows?.length > 0 && (
                <table className="w-full mt-4 text-sm">
                  <thead>
                    <tr className="border-b-2 border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
                      <th className="py-2">Course</th>
                      <th className="py-2">Subject</th>
                      <th className="py-2">Lessons passed</th>
                      <th className="py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doc.payload.rows.map((r, i) => (
                      <tr key={i} className="border-b border-ink/5">
                        <td className="py-2 font-bold text-ink">{r.course_title}</td>
                        <td className="py-2">{r.subject_label || r.subject || "—"}</td>
                        <td className="py-2">{r.stats ? `${r.stats.lessons_passed}/${r.stats.lessons_total}` : "—"}</td>
                        <td className="py-2">{r.status?.replace("_", " ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {doc.payload?.graded_courses?.length > 0 && (
                <table className="w-full mt-4 text-sm">
                  <thead>
                    <tr className="border-b-2 border-ink/10 text-left text-xs uppercase tracking-wide text-ink/50">
                      <th className="py-2">Course</th>
                      <th className="py-2">Subject</th>
                      <th className="py-2">Mastery</th>
                      <th className="py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doc.payload.graded_courses.map((g, i) => (
                      <tr key={i} className="border-b border-ink/5">
                        <td className="py-2 font-bold text-ink">{g.course_title}</td>
                        <td className="py-2">{g.subject}</td>
                        <td className="py-2">{g.progress_pct}%</td>
                        <td className="py-2">{g.status.replace("_", " ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {doc.payload?.summary && (
                <div className="mt-4 text-sm text-ink/70">
                  {doc.payload.summary.courses_completed} courses completed · {doc.payload.summary.lessons_passed}/{doc.payload.summary.lessons_total} lessons passed
                </div>
              )}

              {doc.payload?.signature_line && <div className="mt-6 text-sm text-ink/80">{doc.payload.signature_line}</div>}

              <div className="mt-6 pt-4 border-t border-ink/10 text-xs text-ink/45 leading-relaxed">{doc.disclaimer}</div>
            </div>
          </div>
        )}

        {/* Previously generated */}
        {docs.length > 0 && (
          <div className="max-w-4xl mt-8">
            <div className="text-xs font-bold uppercase tracking-widest text-ink/50 mb-2">Previously generated</div>
            <div className="space-y-2">
              {docs.map((d) => (
                <div key={d.id} className="card-flat p-4 flex items-center justify-between text-sm">
                  <div>
                    <span className="font-bold text-ink">{d.payload?.title || d.kind}</span>
                    <span className="text-ink/50 ml-2">{d.school_year}</span>
                  </div>
                  <span className="text-ink/45 text-xs">{fmt(d.generated_at)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
