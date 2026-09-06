import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import AppShell from "../../components/AppShell";
import { TrackTag, ProgressBar } from "./academyKit";
import {
  GraduationCap, UserPlus, ArrowRight, FileText, Trash2, RefreshCw,
  AlertTriangle, CheckCircle2, Users, Sparkles, BookOpen,
} from "lucide-react";

const TRACK_OPTIONS = [
  { key: "foundations", name: "Foundations (K–8)", desc: "Core academics — ELA, Math, Science, Social Studies." },
  { key: "builder", name: "Builder / Trade (6–12)", desc: "Trade math & science plus trade pathways like electrical." },
  { key: "artist", name: "Artist (K–12)", desc: "Creative disciplines with academic rigor." },
  { key: "scholar", name: "Scholar (9–12)", desc: "College-preparatory academics." },
];

export default function AcademyParentHome() {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [summaries, setSummaries] = useState({});
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", grade: "1", track: "foundations" });
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    api.get("/academy/students")
      .then(async (r) => {
        const list = r.data?.students || [];
        setStudents(list);
        const sums = {};
        await Promise.all(list.filter((s) => s.status === "active").map((s) =>
          api.get(`/academy/students/${s.id}/dashboard`)
            .then((d) => { sums[s.id] = d.data; })
            .catch(() => {})
        ));
        setSummaries(sums);
      })
      .catch(() => setError("Could not load your students. Try again."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const addStudent = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      const r = await api.post("/academy/students", form);
      setNotice(`Added ${form.name} — enrolled in ${r.data.auto_enrolled.length} course${r.data.auto_enrolled.length === 1 ? "" : "s"} for ${form.grade === "K" ? "Kindergarten" : "Grade " + form.grade} ${form.track}.`);
      setForm({ name: "", grade: "1", track: "foundations" });
      setAdding(false);
      load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not add this student.");
    } finally { setBusy(false); }
  };

  const archive = async (s) => {
    if (!window.confirm(`Archive ${s.name}'s profile? Their records stay in the database but they'll be hidden from the dashboard.`)) return;
    await api.delete(`/academy/students/${s.id}`).catch(() => {});
    load();
  };

  const active = students.filter((s) => s.status === "active");
  const showOnboarding = !loading && active.length === 0;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl" data-testid="academy-parent">
        <div className="overline text-copper">WAI Institute Homeschool Academy</div>
        <h1 className="font-heading text-4xl font-bold text-ink mt-1">Family Dashboard</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">
          Welcome{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}. This is your homeschool control
          room: add students, watch progress, and print records. <strong className="text-ink">How is my child progressing?</strong> is the question this page answers.
        </p>

        {notice && (
          <div className="mt-6 flex items-start gap-3 p-4 rounded-xl border border-emerald-600/30 bg-emerald-600/5 text-emerald-800">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <div className="text-sm font-semibold leading-relaxed">{notice}</div>
          </div>
        )}
        {error && (
          <div className="mt-6 flex items-center gap-3 p-4 rounded-xl border border-destructive/30 bg-destructive/5 text-destructive text-sm font-semibold">
            <AlertTriangle className="w-5 h-5 shrink-0" /> {error}
            <button onClick={load} className="ml-auto underline font-bold">Retry</button>
          </div>
        )}

        {/* Onboarding — three steps */}
        {showOnboarding && (
          <div className="card-flat bg-white border-t-4 border-copper p-8 mt-8">
            <div className="overline text-copper mb-1">Getting started</div>
            <h2 className="font-heading text-2xl font-bold text-ink">Set up your homeschool in three steps</h2>
            <ol className="mt-6 space-y-4">
              <li className="flex gap-4">
                <span className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-heading font-black shrink-0">1</span>
                <div><div className="font-bold text-ink">Create a parent account</div><p className="text-sm text-ink/60">Done — you're signed in. Your account manages every student below.</p></div>
              </li>
              <li className="flex gap-4">
                <span className="w-8 h-8 rounded-full bg-copper text-white flex items-center justify-center font-heading font-black shrink-0">2</span>
                <div className="flex-1">
                  <div className="font-bold text-ink">Add a student and choose grade + track</div>
                  <p className="text-sm text-ink/60">We'll enroll them in every available course that fits.</p>
                  {!adding && (
                    <button onClick={() => setAdding(true)} className="mt-3 inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-signal font-black text-sm rounded-lg hover:bg-ink/85 transition-colors" data-testid="academy-add-student">
                      <UserPlus className="w-4 h-4" /> Add your first student
                    </button>
                  )}
                </div>
              </li>
              <li className="flex gap-4">
                <span className="w-8 h-8 rounded-full bg-ink text-signal flex items-center justify-center font-heading font-black shrink-0">3</span>
                <div><div className="font-bold text-ink">Track learning and print records</div><p className="text-sm text-ink/60">Progress, mastery, and printable records live on this dashboard and each student's page.</p></div>
              </li>
            </ol>
          </div>
        )}

        {/* Add-student form */}
        {(adding || active.length > 0) && (
          <div className="mt-8 flex items-center justify-between">
            <h2 className="font-heading text-2xl font-bold text-ink">Your students</h2>
            <button onClick={() => { setAdding((v) => !v); setNotice(""); }} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-ink/15 text-ink font-black text-sm hover:border-copper hover:text-copper transition-colors" data-testid="academy-toggle-add">
              <UserPlus className="w-4 h-4" /> {adding ? "Close" : "Add a student"}
            </button>
          </div>
        )}

        {adding && (
          <form onSubmit={addStudent} className="card-flat bg-white border border-ink/10 p-6 mt-4">
            <div className="grid sm:grid-cols-3 gap-4">
              <label className="block sm:col-span-1">
                <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Student name</span>
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-semibold focus:ring-2 focus:ring-copper focus:outline-none"
                  placeholder="e.g. Jordan" data-testid="academy-student-name" />
              </label>
              <label className="block">
                <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Grade</span>
                <select value={form.grade} onChange={(e) => setForm({ ...form, grade: e.target.value })}
                  className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-semibold focus:ring-2 focus:ring-copper focus:outline-none" data-testid="academy-student-grade">
                  {["K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"].map((g) => (
                    <option key={g} value={g}>{g === "K" ? "Kindergarten" : `Grade ${g}`}</option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Track</span>
                <select value={form.track} onChange={(e) => setForm({ ...form, track: e.target.value })}
                  className="mt-1 w-full px-3 py-2.5 rounded-lg border border-ink/20 text-sm font-semibold focus:ring-2 focus:ring-copper focus:outline-none" data-testid="academy-student-track">
                  {TRACK_OPTIONS.map((t) => <option key={t.key} value={t.key}>{t.name}</option>)}
                </select>
              </label>
            </div>
            <p className="text-xs text-ink/50 mt-2">{TRACK_OPTIONS.find((t) => t.key === form.track)?.desc}</p>
            <button type="submit" disabled={busy} className="mt-4 inline-flex items-center gap-2 px-6 py-2.5 bg-signal text-ink font-black rounded-lg hover:bg-signal/85 transition-colors disabled:opacity-50" data-testid="academy-add-submit">
              {busy ? "Adding…" : "Add student & auto-enroll"} <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        )}

        {/* Student list */}
        {loading && <p className="text-ink/45 py-16 flex items-center gap-2 justify-center"><RefreshCw className="w-4 h-4 animate-spin" /> Loading your homeschool…</p>}

        {!loading && active.length > 0 && (
          <div className="grid md:grid-cols-2 gap-5 mt-4 pb-10">
            {active.map((s) => {
              const sum = summaries[s.id];
              const rec = sum?.records;
              return (
                <div key={s.id} className="card-flat bg-white border border-ink/10 p-6 flex flex-col gap-4" data-testid={`student-card-${s.id}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-heading text-xl font-bold text-ink">{s.name}</h3>
                        <TrackTag track={s.track} />
                      </div>
                      <div className="text-xs font-black uppercase tracking-widest text-copper mt-1">
                        {s.grade === "K" ? "Kindergarten" : `Grade ${s.grade}`} · {TRACK_OPTIONS.find((t) => t.key === s.track)?.name || s.track}
                      </div>
                    </div>
                    <button onClick={() => archive(s)} title="Archive student" className="text-ink/30 hover:text-destructive transition-colors" data-testid={`archive-${s.id}`}>
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {rec ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center justify-between font-bold text-ink">
                        <span className="text-ink/60">Overall progress</span>
                        <span>{rec.lessons_passed}/{rec.lessons_total} lessons</span>
                      </div>
                      <ProgressBar pct={rec.overall_percent} />
                      <div className="grid grid-cols-3 gap-2 pt-2">
                        <Stat label="Courses" value={sum.courses.length} />
                        <Stat label="In progress" value={sum.courses.filter((c) => !c.stats.completed && c.stats.lessons_passed > 0).length} />
                        <Stat label="Completed" value={rec.courses_completed} />
                      </div>
                      {sum.courses.filter((c) => !c.stats.completed && c.next_lesson).length > 0 && (
                        <p className="text-xs text-ink/55 pt-1">
                          Next up: <strong className="text-ink">{sum.courses.find((c) => !c.stats.completed && c.next_lesson)?.next_lesson?.title}</strong>
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-ink/50">No active courses yet.</p>
                  )}

                  <div className="mt-auto flex flex-wrap gap-2 pt-2 border-t border-ink/5">
                    <Link to={`/academy/student/${s.id}`} className="inline-flex items-center gap-2 px-4 py-2 bg-ink text-signal font-black text-sm rounded-lg hover:bg-ink/85 transition-colors" data-testid={`open-student-${s.id}`}>
                      <GraduationCap className="w-4 h-4" /> Student dashboard
                    </Link>
                    <Link to={`/academy/records?student=${s.id}`} className="inline-flex items-center gap-2 px-4 py-2 border-2 border-ink/15 text-ink font-black text-sm rounded-lg hover:border-copper hover:text-copper transition-colors">
                      <FileText className="w-4 h-4" /> Records
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!loading && active.length === 0 && !adding && (
          <div className="card-flat bg-white p-8 mt-6 text-center">
            <Users className="w-9 h-9 text-copper mx-auto mb-3" />
            <p className="font-heading font-bold text-ink text-lg">No students yet</p>
            <p className="text-sm text-ink/55 mt-1 mb-4">Add a student above to start the Academy experience.</p>
            <Link to="/academy/curriculum" className="btn-copper inline-flex items-center gap-2 text-sm"><BookOpen className="w-4 h-4" /> Browse the curriculum first</Link>
          </div>
        )}

        <div className="pb-6 -mt-2">
          <p className="text-xs text-ink/45 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-copper" />
            New courses auto-enroll when they fit a student's grade and track. Change a student's grade or track and their enrollment re-balances.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-lg bg-ink/[0.03] border border-ink/5 px-3 py-2 text-center">
      <div className="font-heading text-lg font-black text-ink">{value}</div>
      <div className="text-[10px] font-bold uppercase tracking-wider text-ink/45">{label}</div>
    </div>
  );
}
