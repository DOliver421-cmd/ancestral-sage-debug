import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { TrackTag, ProgressBar } from "./academyKit";
import { ArrowRight, BookOpen, CheckCircle2, FileText, PlayCircle, RefreshCw, Sparkles, Target } from "lucide-react";

/* /academy/student/:studentId — the learner's view.
   Answer the question: "What do I do next?" */

export default function AcademyStudentHome() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [students, setStudents] = useState([]);
  const [dash, setDash] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/academy/students")
      .then((r) => {
        const list = (r.data?.students || []).filter((s) => s.status === "active");
        setStudents(list);
        if (list.length === 0) { setError("no-students"); setLoading(false); return; }
        const chosen = list.find((s) => s.id === studentId) || list[0];
        if (!studentId || chosen.id !== studentId) {
          navigate(`/academy/student/${chosen.id}`, { replace: true });
          return; // effect re-runs with the param set
        }
        api.get(`/academy/students/${chosen.id}/dashboard`)
          .then((d) => setDash(d.data))
          .catch((e) => setError(e?.response?.data?.detail || "Could not load this student."))
          .finally(() => setLoading(false));
      })
      .catch(() => { setError("auth"); setLoading(false); });
  }, [studentId, navigate]);

  const activeCourses = useMemo(() => (dash?.courses || []).filter((c) => !c.stats.completed), [dash]);
  const doneCourses = useMemo(() => (dash?.courses || []).filter((c) => c.stats.completed), [dash]);
  const student = dash?.student;

  if (loading) {
    return (
      <AppShell>
        <p className="px-10 py-16 flex items-center gap-2 text-ink/45"><RefreshCw className="w-4 h-4 animate-spin" /> Loading the classroom…</p>
      </AppShell>
    );
  }
  if (error === "no-students") {
    return (
      <AppShell>
        <div className="px-10 py-16 max-w-2xl">
          <h1 className="font-heading text-3xl font-bold text-ink">No student profiles yet</h1>
          <p className="text-ink/60 mt-2">Add a student (name, grade, track) from your family dashboard to get started.</p>
          <Link to="/academy/parent" className="btn-copper inline-flex items-center gap-2 mt-6">Open Family Dashboard <ArrowRight className="w-4 h-4" /></Link>
        </div>
      </AppShell>
    );
  }
  if (error || !student) {
    return (
      <AppShell>
        <div className="px-10 py-16">
          <p className="text-destructive font-bold">{error === "auth" ? "Please sign in to view the Academy." : error}</p>
          <Link to="/academy/parent" className="btn-copper inline-flex items-center gap-2 mt-5">Back to Family Dashboard</Link>
        </div>
      </AppShell>
    );
  }

  const switchable = students.filter((s) => s.id !== student.id);
  const focus = activeCourses.find((c) => c.next_lesson);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl" data-testid="academy-student">
        {/* Who is learning */}
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="overline text-copper">Student dashboard</div>
            <h1 className="font-heading text-4xl font-bold text-ink mt-1 flex items-center gap-3">
              {student.name}'s Classroom
              <span className="text-sm font-bold text-ink/45 font-body">· {student.grade === "K" ? "Kindergarten" : student.grade === "adult" ? "Adult" : `Grade ${student.grade}`}</span>
            </h1>
            <div className="mt-2"><TrackTag track={student.track} /></div>
          </div>
          <div className="flex items-center gap-3">
            {switchable.length > 0 && (
              <select className="px-3 py-2 rounded-lg border border-ink/20 bg-white text-sm font-bold" value={student.id}
                onChange={(e) => navigate(`/academy/student/${e.target.value}`)} data-testid="student-switcher">
                {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            )}
            <Link to="/academy/parent" className="text-sm font-bold text-copper hover:text-ink underline underline-offset-2">Family dashboard</Link>
            <Link to={`/academy/records?student=${student.id}`} className="inline-flex items-center gap-1.5 text-sm font-bold text-ink border-2 border-ink/15 hover:border-copper rounded-lg px-3 py-2 transition-colors">
              <FileText className="w-4 h-4" /> Records
            </Link>
          </div>
        </div>

        {/* What do I do next */}
        {focus ? (
          <section className="mt-8 bg-ink text-white rounded-2xl p-8 relative overflow-hidden" data-testid="next-up-card">
            <div className="absolute -right-8 -top-8 w-48 h-48 rounded-full bg-signal/10" />
            <div className="overline text-signal">What do I do next?</div>
            <div className="flex flex-wrap items-center justify-between gap-6 mt-2">
              <div className="max-w-xl">
                <div className="text-sm text-white/55 font-bold">{focus.subject_label} · {focus.title}</div>
                <h2 className="font-heading text-2xl font-bold mt-1">{focus.next_lesson.title}</h2>
                <p className="text-white/55 text-sm mt-1">{focus.stats.lessons_passed} of {focus.stats.lessons_total} lessons done in this course</p>
              </div>
              <Link to={`/academy/learn/${focus.slug}/${focus.next_lesson.slug}?student=${student.id}`}
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-signal text-ink font-black rounded-xl hover:bg-signal/85 transition-all" data-testid="continue-learning">
                <PlayCircle className="w-5 h-5" /> Continue learning
              </Link>
            </div>
            <div className="mt-6 max-w-md"><ProgressBar pct={focus.stats.percent} tone="bg-signal" /></div>
          </section>
        ) : (
          dash?.courses?.length > 0 && doneCourses.length === (dash?.courses || []).length ? (
            <section className="mt-8 card-flat bg-white p-8 flex items-center gap-4 border-t-4 border-emerald-500">
              <CheckCircle2 className="w-10 h-10 text-emerald-600" />
              <div>
                <h2 className="font-heading text-2xl font-bold text-ink">All enrolled courses complete — amazing work!</h2>
                <p className="text-ink/60 text-sm mt-1">Print {student.name}'s records from the Records button above.</p>
              </div>
            </section>
          ) : null
        )}

        {/* Course list */}
        <section className="mt-10">
          <h2 className="font-heading text-2xl font-bold text-ink flex items-center gap-2"><BookOpen className="w-6 h-6 text-copper" /> Courses</h2>
          {dash?.courses?.length === 0 && (
            <p className="text-ink/55 mt-3">No published courses match this grade and track yet — new curriculum ships regularly.</p>
          )}
          <div className="grid md:grid-cols-2 gap-5 mt-5">
            {dash?.courses?.map((c) => {
              const active = !c.stats.completed;
              return (
                <div key={c.slug} className={`card-flat p-6 bg-white border flex flex-col gap-3 ${active ? "border-ink/10" : "border-emerald-600/20"}`}>
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-xs font-black uppercase tracking-widest text-copper">{c.subject_label} · {c.grade_label}</span>
                    {c.stats.completed && <span className="inline-flex items-center gap-1 text-[11px] font-black uppercase text-emerald-700 bg-emerald-600/10 border border-emerald-600/30 rounded-full px-2 py-0.5"><CheckCircle2 className="w-3 h-3" /> Complete</span>}
                  </div>
                  <h3 className="font-heading text-xl font-bold text-ink leading-snug">{c.title}</h3>
                  <div className="flex items-center justify-between text-sm font-bold">
                    <span className="text-ink/55">{c.stats.lessons_passed}/{c.stats.lessons_total} lessons</span>
                    {c.stats.mastery_avg != null && <span className="flex items-center gap-1 text-ink/55"><Target className="w-3.5 h-3.5 text-copper" /> avg mastery {c.stats.mastery_avg}%</span>}
                  </div>
                  <ProgressBar pct={c.stats.percent} tone={c.stats.completed ? "bg-emerald-600" : "bg-copper"} />
                  <p className="text-xs text-ink/45">Pass each lesson at {c.passing_score}%+ to advance</p>
                  {c.next_lesson ? (
                    <Link to={`/academy/learn/${c.slug}/${c.next_lesson.slug}?student=${student.id}`} className="mt-auto inline-flex items-center gap-1.5 text-sm font-black uppercase tracking-widest text-copper hover:text-ink transition-colors">
                      Continue: {c.next_lesson.title} <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  ) : c.stats.completed ? (
                    <span className="mt-auto text-sm font-bold text-emerald-700 flex items-center gap-1.5"><Sparkles className="w-4 h-4" /> Completed with mastery</span>
                  ) : null}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
