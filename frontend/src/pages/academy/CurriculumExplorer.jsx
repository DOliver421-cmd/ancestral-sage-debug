import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { PublicHeader, AcademyFooter, TrackTag, LiveChip } from "./academyKit";
import { ArrowRight, Search, Filter, BookOpen, Wrench, GraduationCap, Zap } from "lucide-react";

/* /academy/curriculum — THE central catalog for everything on the platform.
   Shows: Academy courses, LMS modules, protocols, workshops, and training. */

const SOURCE_META = {
  academy: { label: "Homeschool Academy", icon: GraduationCap, color: "bg-copper" },
  module: { label: "Course & Workshop", icon: Wrench, color: "bg-green-700" },
  protocol: { label: "Protocol", icon: Zap, color: "bg-purple-700" },
  other: { label: "Training", icon: BookOpen, color: "bg-ink" },
};

function normalizeItem(source, raw) {
  if (source === "academy") {
    return {
      id: raw.slug,
      source: "academy",
      title: raw.title,
      summary: raw.summary || "",
      description: raw.description || "",
      status: raw.status || "planned",
      track: raw.track || raw.tracks?.[0] || "",
      tracks: raw.tracks || [],
      grade_label: raw.grade_label || "",
      subject_label: raw.subject_label || "",
      subject: raw.subject || "",
      grades: raw.grades || [],
      lesson_count: raw.lesson_count || 0,
      est_hours: raw.est_hours || 0,
      slug: raw.slug,
      category: raw.track || raw.subject || "general",
    };
  }
  if (source === "module") {
    return {
      id: raw.slug,
      source: "module",
      title: raw.title,
      summary: raw.description || "",
      description: raw.description || "",
      status: raw.active !== false ? "published" : "planned",
      track: raw.category || "",
      tracks: [raw.category || ""],
      grade_label: raw.level || "",
      subject_label: raw.category_label || raw.category || "",
      subject: raw.category || "",
      grades: [],
      lesson_count: raw.lesson_count || raw.tasks?.length || 0,
      est_hours: 0,
      slug: raw.slug,
      category: raw.category || "general",
      price_cents: raw.price_cents || 0,
    };
  }
  // protocols, other
  return {
    id: raw.slug || raw.id || raw.title,
    source,
    title: raw.title,
    summary: raw.description || raw.summary || "",
    description: raw.description || "",
    status: "published",
    track: raw.category || source,
    tracks: [raw.category || source],
    grade_label: raw.level || "",
    subject_label: raw.category || source,
    subject: raw.category || source,
    grades: [],
    lesson_count: raw.lesson_count || 0,
    est_hours: 0,
    slug: raw.slug || raw.id,
    category: raw.category || source,
  };
}

export default function CurriculumExplorer() {
  const [academyCourses, setAcademyCourses] = useState([]);
  const [modules, setModules] = useState([]);
  const [protocols, setProtocols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [grade, setGrade] = useState("");
  const [track, setTrack] = useState("");
  const [subject, setSubject] = useState("");
  const [source, setSource] = useState("");
  const [q, setQ] = useState("");
  const [showPlanned, setShowPlanned] = useState(true);

  useEffect(() => {
    const done = () => setLoading(false);
    // Academy courses
    api.get("/academy/courses")
      .then((r) => setAcademyCourses((r.data?.courses || []).map(c => normalizeItem("academy", c))))
      .catch(() => {})
      .finally(() => {});
    // LMS modules (trades, workshops, general courses)
    api.get("/modules")
      .then((r) => setModules((Array.isArray(r.data) ? r.data : []).map(m => normalizeItem("module", m))))
      .catch(() => {})
      .finally(() => {});
    // Protocols (ascension, etc.)
    api.get("/ascension-protocols")
      .then((r) => setProtocols((Array.isArray(r.data) ? r.data : []).map(p => normalizeItem("protocol", p))))
      .catch(() => {})
      .finally(done);
    // Fallback: if protocols endpoint doesn't exist, still finish loading
    setTimeout(done, 3000);
  }, []);

  const all = useMemo(() => [...academyCourses, ...modules, ...protocols], [academyCourses, modules, protocols]);

  // Collect unique values for filters
  const allTracks = useMemo(() => {
    const s = new Set(all.map(i => i.track).filter(Boolean));
    return [...s].sort();
  }, [all]);
  const allSubjects = useMemo(() => {
    const s = new Set(all.map(i => i.subject).filter(Boolean));
    return [...s].sort();
  }, [all]);
  const allGrades = useMemo(() => {
    const s = new Set(all.map(i => i.grades).flat().filter(Boolean));
    return [...s].sort();
  }, [all]);

  const items = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let list = all;
    if (grade) list = list.filter((i) => i.grades.includes(grade));
    if (track) list = list.filter((i) => i.tracks.includes(track) || i.track === track);
    if (subject) list = list.filter((i) => i.subject === subject);
    if (source) list = list.filter((i) => i.source === source);
    if (!showPlanned) list = list.filter((i) => i.status === "published");
    if (needle) {
      list = list.filter((i) =>
        [i.title, i.summary, i.description, i.subject_label, i.grade_label, i.track]
          .join(" ").toLowerCase().includes(needle)
      );
    }
    return list;
  }, [all, grade, track, subject, source, q, showPlanned]);

  // Group by source, then by grade within academy
  const grouped = useMemo(() => {
    const g = {};
    const gradeOrder = ['K','1','2','3','4','5','6','7','8','9','10','11','12','adult'];
    for (const item of items) {
      const key = item.source;
      if (!g[key]) g[key] = [];
      g[key].push(item);
    }
    // Sort academy courses by grade, then by title
    if (g.academy) {
      g.academy.sort((a, b) => {
        const aGrade = gradeOrder.indexOf(a.grades?.[0] || '99');
        const bGrade = gradeOrder.indexOf(b.grades?.[0] || '99');
        if (aGrade !== bGrade) return aGrade - bGrade;
        return (a.title || '').localeCompare(b.title || '');
      });
    }
    return g;
  }, [items]);

  // Grade separators for academy section
  const academyGradeGroups = useMemo(() => {
    if (!grouped.academy) return [];
    const groups = [];
    const gradeOrder = ['K','1','2','3','4','5','6','7','8','9','10','11','12','adult'];
    for (const item of grouped.academy) {
      const grade = item.grades?.[0] || 'other';
      const existing = groups.find(g => g.grade === grade);
      if (existing) {
        existing.items.push(item);
      } else {
        groups.push({ grade, items: [item] });
      }
    }
    groups.sort((a, b) => gradeOrder.indexOf(a.grade) - gradeOrder.indexOf(b.grade));
    return groups;
  }, [grouped]);

  const selectCls = "px-3 py-2.5 rounded-lg border border-ink/20 bg-white text-sm font-semibold text-ink focus:outline-none focus:ring-2 focus:ring-copper";

  const sourceCounts = useMemo(() => {
    const c = { academy: 0, module: 0, protocol: 0, other: 0 };
    for (const i of all) c[i.source] = (c[i.source] || 0) + 1;
    return c;
  }, [all]);

  return (
    <div className="min-h-screen bg-bone" data-testid="curriculum-explorer">
      <PublicHeader />
      <section className="bg-ink text-white">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="overline text-signal mb-1">All Courses & Training</div>
          <h1 className="font-heading text-4xl font-bold">Find the right course</h1>
          <p className="text-white/60 mt-2 max-w-2xl">
            Everything on the platform in one place: Homeschool Academy courses, trade workshops,
            training modules, and protocols. Filter by category, subject, or keyword.
          </p>
          <div className="flex gap-3 mt-4 flex-wrap">
            {Object.entries(sourceCounts).filter(([,c]) => c > 0).map(([k, c]) => (
              <span key={k} className="text-xs font-bold px-3 py-1 rounded-full bg-white/10">
                {SOURCE_META[k]?.label || k}: {c}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="card-flat p-5 border border-ink/10 bg-white">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-copper mb-3">
            <Filter className="w-4 h-4" /> Filter
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-6 gap-3">
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Category</span>
              <select className={`${selectCls} w-full mt-1`} value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="">All categories</option>
                <option value="academy">Homeschool Academy ({sourceCounts.academy})</option>
                <option value="module">Courses & Workshops ({sourceCounts.module})</option>
                <option value="protocol">Protocols ({sourceCounts.protocol})</option>
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Grade</span>
              <select className={`${selectCls} w-full mt-1`} value={grade} onChange={(e) => setGrade(e.target.value)}>
                <option value="">All grades</option>
                {allGrades.map((g) => <option key={g} value={g}>{g === "K" ? "Kindergarten" : g === "adult" ? "Adult" : `Grade ${g}`}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Track</span>
              <select className={`${selectCls} w-full mt-1`} value={track} onChange={(e) => setTrack(e.target.value)}>
                <option value="">All tracks</option>
                {allTracks.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Subject</span>
              <select className={`${selectCls} w-full mt-1`} value={subject} onChange={(e) => setSubject(e.target.value)}>
                <option value="">All subjects</option>
                {allSubjects.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="block sm:col-span-1 lg:col-span-2">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Keyword</span>
              <div className="relative mt-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
                <input className="pl-9 pr-3 py-2.5 w-full rounded-lg border border-ink/20 bg-white text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-copper"
                  placeholder="Try: biology, electrical, phonics, protocol…"
                  value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
            </label>
          </div>
          <label className="flex items-center gap-2 mt-4 text-sm font-bold text-ink/70 cursor-pointer select-none">
            <input type="checkbox" checked={showPlanned} onChange={(e) => setShowPlanned(e.target.checked)} className="accent-copper w-4 h-4" />
            Show courses still in development (so you can see the full roadmap)
          </label>
        </div>

        {/* Results */}
        <div className="flex items-center justify-between mt-8 mb-4">
          <h2 className="font-heading text-xl font-bold text-ink">{items.length} item{items.length === 1 ? "" : "s"}</h2>
        </div>
        {loading && <p className="text-ink/50 py-10 text-center">Loading curriculum…</p>}
        {!loading && items.length === 0 && (
          <div className="card-flat p-10 text-center text-ink/60">
            No courses match those filters. Try clearing one.
          </div>
        )}

        {/* Grouped sections */}
        {Object.entries(grouped).map(([src, srcItems]) => {
          const meta = SOURCE_META[src] || SOURCE_META.other;
          const Icon = meta.icon;
          return (
            <div key={src} className="mb-10">
              <div className="flex items-center gap-2 mb-4">
                <span className={`${meta.color} text-white p-1.5 rounded-lg`}><Icon className="w-4 h-4" /></span>
                <h3 className="font-heading text-lg font-bold text-ink">{meta.label}</h3>
                <span className="text-xs text-ink/40 font-bold">({srcItems.length})</span>
              </div>
              {/* Academy: group by grade with separators */}
              {src === 'academy' && academyGradeGroups.map(({ grade, items: gradeItems }) => (
                <div key={grade} className="mb-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-px flex-1 bg-ink/10" />
                    <span className="text-xs font-black uppercase tracking-widest text-copper bg-copper/10 px-3 py-1 rounded-full">
                      {grade === 'K' ? 'Kindergarten' : grade === 'adult' ? 'Adult Education' : `Grade ${grade}`}
                    </span>
                    <div className="h-px flex-1 bg-ink/10" />
                  </div>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {gradeItems.map((c) => (
                      <Link
                    key={c.id}
                    to={c.source === "academy" ? `/academy/courses/${c.slug}` : c.source === "module" ? `/modules/${c.slug}` : `/ascension-protocols`}
                    className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      {c.track && <TrackTag track={c.track} />}
                      <LiveChip status={c.status} />
                      {c.price_cents > 0 && (
                        <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">
                          ${(c.price_cents / 100).toFixed(2)}
                        </span>
                      )}
                      {c.price_cents === 0 && c.source !== "academy" && (
                        <span className="text-xs font-bold text-ink/70 bg-ink/5 border border-ink/15 px-2 py-0.5 rounded-full">Included with membership</span>
                      )}
                    </div>
                    <div>
                      <div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div>
                      {(c.grade_label || c.subject_label) && (
                        <div className="text-xs font-black uppercase tracking-widest text-copper mt-1">
                          {[c.grade_label, c.subject_label].filter(Boolean).join(" · ")}
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                    <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45">
                      {c.lesson_count > 0
                        ? <span>{c.lesson_count} lessons{c.est_hours > 0 ? ` · ~${c.est_hours} hrs` : ""}</span>
                        : <span>{c.status === "published" ? "Available now" : "In development"}</span>
                      }
                      <span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
          {/* Non-academy: flat grid */}
          {src !== 'academy' && (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
              {srcItems.map((c) => (
                <Link
                  key={c.id}
                  to={c.source === 'module' ? `/modules/${c.slug}` : `/ascension-protocols`}
                  className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    {c.track && <TrackTag track={c.track} />}
                    <LiveChip status={c.status} />
                    {c.price_cents > 0 && (
                      <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">
                        ${(c.price_cents / 100).toFixed(2)}
                      </span>
                    )}
                    {c.price_cents === 0 && (
                      <span className="text-xs font-bold text-ink/70 bg-ink/5 border border-ink/15 px-2 py-0.5 rounded-full">Included with membership</span>
                    )}
                  </div>
                  <div>
                    <div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div>
                    {(c.grade_label || c.subject_label) && (
                      <div className="text-xs font-black uppercase tracking-widest text-copper mt-1">
                        {[c.grade_label, c.subject_label].filter(Boolean).join(' · ')}
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                  <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45">
                    {c.lesson_count > 0
                      ? <span>{c.lesson_count} lessons{c.est_hours > 0 ? ` · ~${c.est_hours} hrs` : ''}</span>
                      : <span>{c.status === 'published' ? 'Available now' : 'In development'}</span>
                    }
                    <span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span>
                  </div>
                </Link>
              ))}
            </div>
          )}
          </div>
          );
        })}
      </section>
      <AcademyFooter />
    </div>
  );
}
