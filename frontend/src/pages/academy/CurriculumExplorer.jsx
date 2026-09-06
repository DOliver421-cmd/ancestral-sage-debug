import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { PublicHeader, AcademyFooter, TrackTag, LiveChip } from "./academyKit";
import { ArrowRight, Search, Filter } from "lucide-react";

/* /academy/curriculum — browse the catalog by grade, track, subject, or keyword. */

export default function CurriculumExplorer() {
  const [all, setAll] = useState([]);
  const [meta, setMeta] = useState({ tracks: [], subjects: [], grades: [] });
  const [loading, setLoading] = useState(true);
  const [grade, setGrade] = useState("");
  const [track, setTrack] = useState("");
  const [subject, setSubject] = useState("");
  const [q, setQ] = useState("");
  const [showPlanned, setShowPlanned] = useState(true);

  useEffect(() => {
    api.get("/academy/tracks").then((r) => setMeta(r.data)).catch(() => {});
    api.get("/academy/courses")
      .then((r) => setAll(r.data?.courses || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const courses = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let list = all;
    // Track filters against a course's full applicability list (a course can
    // serve several tracks, e.g. Grade 7 Math is Foundations AND Builder).
    if (grade) list = list.filter((c) => c.grades.includes(grade));
    if (track) list = list.filter((c) => (c.tracks || []).includes(track));
    if (subject) list = list.filter((c) => c.subject === subject);
    if (!showPlanned) list = list.filter((c) => c.status === "published");
    if (needle) {
      list = list.filter((c) =>
        [c.title, c.summary, c.description, c.subject_label, c.grade_label]
          .join(" ").toLowerCase().includes(needle)
      );
    }
    return list;
  }, [all, grade, track, subject, q, showPlanned]);

  const selectCls = "px-3 py-2.5 rounded-lg border border-ink/20 bg-white text-sm font-semibold text-ink focus:outline-none focus:ring-2 focus:ring-copper";

  return (
    <div className="min-h-screen bg-bone" data-testid="curriculum-explorer">
      <PublicHeader />
      <section className="bg-ink text-white">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="overline text-signal mb-1">Curriculum</div>
          <h1 className="font-heading text-4xl font-bold">Find the right course</h1>
          <p className="text-white/60 mt-2 max-w-2xl">
            Filter by grade, track, subject, or a keyword. Courses marked{" "}
            <span className="text-white font-bold">Available now</span> are fully written and ready to learn;
            everything else is honestly labelled as in development.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="card-flat p-5 border border-ink/10 bg-white">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-copper mb-3">
            <Filter className="w-4 h-4" /> Filter
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Grade</span>
              <select className={`${selectCls} w-full mt-1`} value={grade} onChange={(e) => setGrade(e.target.value)} data-testid="filter-grade">
                <option value="">All grades</option>
                {meta.grades.map((g) => <option key={g} value={g}>{g === "K" ? "Kindergarten" : `Grade ${g}`}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Track</span>
              <select className={`${selectCls} w-full mt-1`} value={track} onChange={(e) => setTrack(e.target.value)} data-testid="filter-track">
                <option value="">All tracks</option>
                {meta.tracks.map((t) => <option key={t.key} value={t.key}>{t.name} ({t.grades})</option>)}
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Subject</span>
              <select className={`${selectCls} w-full mt-1`} value={subject} onChange={(e) => setSubject(e.target.value)} data-testid="filter-subject">
                <option value="">All subjects</option>
                {meta.subjects.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
              </select>
            </label>
            <label className="block sm:col-span-1 lg:col-span-2">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Keyword</span>
              <div className="relative mt-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
                <input className="pl-9 pr-3 py-2.5 w-full rounded-lg border border-ink/20 bg-white text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-copper"
                  placeholder="Try: biology, ratios, phonics, Ohm's law…"
                  value={q} onChange={(e) => setQ(e.target.value)} data-testid="filter-search" />
              </div>
            </label>
          </div>
          <label className="flex items-center gap-2 mt-4 text-sm font-bold text-ink/70 cursor-pointer select-none">
            <input type="checkbox" checked={showPlanned} onChange={(e) => setShowPlanned(e.target.checked)} className="accent-copper w-4 h-4" data-testid="filter-planned" />
            Show courses still in development (so you can see the full roadmap)
          </label>
        </div>

        {/* Results */}
        <div className="flex items-center justify-between mt-8 mb-4">
          <h2 className="font-heading text-xl font-bold text-ink">{courses.length} course{courses.length === 1 ? "" : "s"}</h2>
          <span className="text-xs font-bold text-ink/45">Examples: Grade 7 → Builder → Math · Grade 9 → Scholar → Biology · Grade 9 → Builder → Applied Electrical Engineering</span>
        </div>
        {loading && <p className="text-ink/50 py-10 text-center">Loading curriculum…</p>}
        {!loading && courses.length === 0 && (
          <div className="card-flat p-10 text-center text-ink/60">
            No courses match those filters. Try clearing one.
          </div>
        )}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 pb-16">
          {courses.map((c) => (
            <Link key={c.slug} to={`/academy/courses/${c.slug}`} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white" data-testid={`course-card-${c.slug}`}>
              <div className="flex flex-wrap items-center gap-2">
                <TrackTag track={c.track} />
                <LiveChip status={c.status} />
              </div>
              <div>
                <div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div>
                <div className="text-xs font-black uppercase tracking-widest text-copper mt-1">{c.grade_label} · {c.subject_label}</div>
              </div>
              <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
              <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45">
                {c.status === "published"
                  ? <span>{c.lesson_count} lessons · ~{c.est_hours} hrs</span>
                  : <span>Curriculum in development</span>}
                <span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest group-hover:gap-2 transition-all">View <ArrowRight className="w-3.5 h-3.5" /></span>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <AcademyFooter />
    </div>
  );
}
