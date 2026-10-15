import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { errorMessage, AcademyFooter } from "./academyKit";
import { ArrowLeft, Folder, Printer, ShieldCheck } from "lucide-react";
import { WAI_LOGO } from "../../lib/brand";

/* /academy/portfolio?student=… — the evidence half of the record: submitted
   projects, each with the artifacts the student actually produced. Print or
   save it as PDF with the browser's print dialog (the page isolates itself in
   print CSS exactly like the records and compliance pages).

   Private to the family account. Nothing here is public, shared, or published
   unless the parent chooses to share it. */

export default function AcademyPortfolio() {
  const [params] = useSearchParams();
  const studentId = params.get("student");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // No student selected yet: stop the spinner so the "Choose a student"
    // chooser can render. Returning without clearing `loading` left the page
    // on a permanent "Loading..." line with no way forward - the exact dead
    // end the Records/Projects/Compliance pages already avoid.
    if (!studentId) { setLoading(false); return; }
    api.get(`/academy/portfolio?student_id=${studentId}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(errorMessage(e, "Could not load the portfolio.")))
      .finally(() => setLoading(false));
  }, [studentId]);

  const fmt = (iso) => {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }); }
    catch { return iso; }
  };

  const entries = data?.entries || [];

  return (
    <div className="min-h-screen bg-bone">
      <div className="no-print">
        <AppShell>
          <div className="max-w-4xl px-8 py-10">
            <Link to={studentId ? `/academy/projects?student=${studentId}` : "/academy/parent"}
              className="inline-flex items-center gap-1.5 text-sm font-bold text-copper hover:text-ink transition-colors">
              <ArrowLeft className="w-4 h-4" /> {studentId ? "Back to projects" : "Back to the family dashboard"}
            </Link>
            <div className="flex items-center gap-3 mt-4">
              <Folder className="w-7 h-7 text-copper" />
              <h1 className="font-heading text-3xl font-black text-ink">Student Portfolio</h1>
            </div>
            <p className="text-ink/60 mt-2 max-w-3xl leading-relaxed">
              Submitted projects and the work behind them. This is the evidence half of the record;
              the parent-issued transcript on the Records page is the claim.
            </p>
            <div className="mt-4 grid gap-4">
              {loading && <p className="flex items-center gap-2 text-ink/45 text-sm"><Folder className="w-4 h-4" /> Loading…</p>}
              {error && (
                <div className="card-flat p-4 text-sm font-bold text-destructive border-destructive/30 bg-destructive/5" data-testid="portfolio-error">
                  {error}
                </div>
              )}
              {!studentId && !loading && (
                <div className="card-flat bg-white border border-ink/10 p-8">
                  <p className="text-sm text-ink/70">Choose a student to open their portfolio.</p>
                  <div className="flex gap-3 mt-4">
                    <Link to="/academy/projects" className="btn-copper inline-flex items-center gap-2 text-sm">
                      <Folder className="w-4 h-4" /> Open projects
                    </Link>
                  </div>
                </div>
              )}
              {studentId && !loading && entries.length === 0 && !error && (
                <div className="card-flat bg-white border border-ink/10 p-8">
                  <p className="text-sm text-ink/70">
                    No submitted projects yet. Finish a project&rsquo;s steps and submit it, and it appears here.
                  </p>
                  <Link to="/academy/projects" className="btn-copper inline-flex items-center gap-2 text-sm mt-4">
                    <Folder className="w-4 h-4" /> Open projects
                  </Link>
                </div>
              )}
            </div>
          </div>
          <AcademyFooter />
        </AppShell>
      </div>

      {studentId && data && (entries.length > 0 || true) && (
        <div className="print-only bg-white text-ink p-8 max-w-3xl mx-auto">
          <div className="flex items-start justify-between border-b-2 border-ink/15 pb-4">
            <div className="flex items-center gap-3">
              <img src={WAI_LOGO} alt="" className="w-12 h-12 rounded-xl" />
              <div>
                <div className="text-xs font-bold uppercase tracking-widest text-ink/50">WAI Institute · Homeschool Academy</div>
                <h1 className="text-2xl font-black">Student Portfolio</h1>
              </div>
            </div>
            <div className="text-right text-xs text-ink/60">Printed {fmt(new Date().toISOString())}</div>
          </div>

          <div className="mt-6 text-sm space-y-1">
            <div><strong>Student:</strong> {data.student?.name || "—"}</div>
            <div><strong>Projects in portfolio:</strong> {entries.length}</div>
          </div>

          <div className="mt-4 rounded-lg border border-ink/15 bg-bone/60 p-4 text-xs text-ink/60 flex gap-2">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <div>{data.privacy}</div>
          </div>

          {entries.length === 0 ? (
            <p className="mt-6 text-sm text-ink/60">No submitted projects.</p>
          ) : (
            <div className="mt-6 space-y-6">
              {entries.sort((a, b) => (a.submitted_at < b.submitted_at ? 1 : -1)).map((e, i) => (
                <div key={e.id} className="border border-ink/10 rounded-lg p-4">
                  <div className="flex items-baseline justify-between gap-4">
                    <h2 className="font-bold">{i + 1}. {e.title}</h2>
                    <span className="text-xs text-ink/50">{fmt(e.submitted_at)}</span>
                  </div>
                  <div className="text-xs text-ink/50 mt-0.5">
                    {e.kind_label}{e.course_slug ? ` · course: ${e.course_slug}` : ""}
                  </div>
                  {e.summary && <p className="text-sm text-ink/80 mt-2">{e.summary}</p>}
                  {e.steps?.length > 0 ? (
                    <ul className="mt-3 text-sm space-y-1">
                      {e.steps.map((s) => (
                        <li key={s.title} className="flex gap-2">
                          <span className="text-ink/40">•</span>
                          <span><strong>{s.title}</strong>{s.artifact ? ` — ${s.artifact}` : ""}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-ink/60 mt-2">No step artifacts recorded.</p>
                  )}
                  {e.notes && <p className="text-sm text-ink/70 mt-2"><strong>Notes:</strong> {e.notes}</p>}
                </div>
              ))}
            </div>
          )}

          <div className="mt-8 text-xs text-ink/45 leading-relaxed border-t border-ink/10 pt-4">
            This is a parent-issued portfolio of student work, not a state-issued credential.
          </div>
        </div>
      )}

      {studentId && data && (
        <div className="no-print max-w-4xl mx-auto px-8 pb-10">
          <button onClick={() => window.print()}
            className="btn-copper inline-flex items-center gap-2" data-testid="portfolio-print">
            <Printer className="w-4 h-4" /> Print / Save PDF
          </button>
        </div>
      )}
    </div>
  );
}
