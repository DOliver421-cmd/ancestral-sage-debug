import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { PublicHeader, AcademyFooter, TrackTag, LiveChip } from "./academyKit";
import { ArrowRight, Search, Filter, BookOpen, Wrench, GraduationCap, Zap } from "lucide-react";

/* /academy/curriculum — THE central catalog for everything on the platform.
   Shows: Academy courses, LMS modules, protocols, workshops, and training.
   Primary hierarchy: Grade Level (K-12, Adult, Trade, Creative & Community),
   then Core vs Elective within each grade. */

const SOURCE_META = {
  academy: { label: "Homeschool Academy", icon: GraduationCap, color: "bg-copper" },
  module: { label: "Course & Workshop", icon: Wrench, color: "bg-green-700" },
  protocol: { label: "Protocol", icon: Zap, color: "bg-purple-700" },
  other: { label: "Training", icon: BookOpen, color: "bg-ink" },
};

const CORE_SUBJECTS = new Set(["ela", "math", "science", "social_studies"]);
const GRADE_ORDER = ["K","1","2","3","4","5","6","7","8","9","10","11","12","adult","other"];
function deriveCategory(track, subject, grades) {
  const g = grades || [];
  if (track === "builder" || subject === "trade") return "trade";
  if (track === "artist" || subject === "art") return "creative";
  if (["adult_ed","life_skills","leadership","career","entrepreneurship"].includes(track) || g.includes("adult")) return "adult";
  if (CORE_SUBJECTS.has(subject)) return "k12_core";
  return "k12_elective";
}
function deriveCourseType(track, subject, grades) {
  const cat = deriveCategory(track, subject, grades);
  if (cat === "k12_core") return "core";
  if (cat === "k12_elective") return "elective";
  return cat;
}

function normalizeItem(source, raw) {
  if (source === "academy") {
    const cat = raw.category || deriveCategory(raw.track || raw.tracks?.[0] || "", raw.subject || "", raw.grades || []);
    const ct = raw.course_type || deriveCourseType(raw.track || raw.tracks?.[0] || "", raw.subject || "", raw.grades || []);
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
      grade_level: raw.grade_level || (raw.grades?.[0] || ""),
      lesson_count: raw.lesson_count || 0,
      est_hours: raw.est_hours || 0,
      slug: raw.slug,
      category: cat,
      course_type: ct,
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
  const [auditData, setAuditData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [grade, setGrade] = useState("");
  const [categoryFilter, setCategoryFilter] = useState(""); // k12_core | k12_elective | adult | trade | creative
  const [courseType, setCourseType] = useState("");
  const [track, setTrack] = useState("");
  const [subject, setSubject] = useState("");
  const [source, setSource] = useState("");
  const [q, setQ] = useState("");
  const [showPlanned, setShowPlanned] = useState(true);

  useEffect(() => {
    const done = () => setLoading(false);
    api.get("/academy/courses")
      .then((r) => setAcademyCourses((r.data?.courses || []).map(c => normalizeItem("academy", c))))
      .catch(() => {})
      .finally(() => {});
    api.get("/modules")
      .then((r) => setModules((Array.isArray(r.data) ? r.data : []).map(m => normalizeItem("module", m))))
      .catch(() => {})
      .finally(() => {});
    api.get("/ascension-protocols")
      .then((r) => setProtocols((Array.isArray(r.data) ? r.data : []).map(p => normalizeItem("protocol", p))))
      .catch(() => {})
      .finally(done);
    api.get("/academy/curriculum-audit").then((r) => setAuditData(r.data)).catch(() => {});
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
    if (grade) list = list.filter((i) => i.grades.includes(grade) || i.grade_level === grade);
    if (categoryFilter) list = list.filter((i) => i.category === categoryFilter);
    if (courseType) list = list.filter((i) => i.course_type === courseType);
    if (track) list = list.filter((i) => i.tracks.includes(track) || i.track === track);
    if (subject) list = list.filter((i) => i.subject === subject);
    if (source) list = list.filter((i) => i.source === source);
    if (!showPlanned) list = list.filter((i) => i.status === "published");
    if (needle) {
      list = list.filter((i) =>
        [i.title, i.summary, i.description, i.subject_label, i.grade_label, i.track, i.category, i.course_type]
          .join(" ").toLowerCase().includes(needle)
      );
    }
    return list;
  }, [all, grade, categoryFilter, courseType, track, subject, source, q, showPlanned]);

  // K-12 grade -> { core: [], electives: [] }, plus non-grade buckets
  const gradeHierarchy = useMemo(() => {
    const hierarchy = {};
    const buckets = { adult: [], trade: [], creative: [] };
    for (const item of items) {
      if (item.source !== "academy") continue;
      if (item.category === "adult") { buckets.adult.push(item); continue; }
      if (item.category === "trade") { buckets.trade.push(item); continue; }
      if (item.category === "creative") { buckets.creative.push(item); continue; }
      const gl = item.grade_level || item.grades?.[0] || "other";
      if (!hierarchy[gl]) hierarchy[gl] = { core: [], electives: [] };
      if (item.course_type === "core") hierarchy[gl].core.push(item);
      else hierarchy[gl].electives.push(item);
    }
    // sort within each group by title
    for (const g of Object.keys(hierarchy)) {
      hierarchy[g].core.sort((a,b) => (a.title||"").localeCompare(b.title||""));
      hierarchy[g].electives.sort((a,b) => (a.title||"").localeCompare(b.title||""));
    }
    buckets.adult.sort((a,b) => (a.title||"").localeCompare(b.title||""));
    buckets.trade.sort((a,b) => (a.title||"").localeCompare(b.title||""));
    buckets.creative.sort((a,b) => (a.title||"").localeCompare(b.title||""));
    return { hierarchy, buckets };
  }, [items]);

  // Also keep source-grouped for non-academy sections
  const grouped = useMemo(() => {
    const g = {};
    for (const item of items) {
      const key = item.source;
      if (!g[key]) g[key] = [];
      g[key].push(item);
    }
    return g;
  }, [items]);

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
            Primary filter: grade level — then Core vs Elective within each grade, plus Adult, Trade, and Creative &amp; Community sections. Everything on the platform in one place.
          </p>
          {auditData && (
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-white/10">Core subjects: {auditData.core_subjects?.join(", ")}</span>
              <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-emerald-500/20 text-emerald-200">{auditData.grades?.filter(g=>g.status==="COMPLETE").length || 0} grades complete</span>
              <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-amber-500/20 text-amber-200">{auditData.grades?.filter(g=>g.status==="INCOMPLETE").length || 0} grades need core courses</span>
            </div>
          )}
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
        {/* Primary: Grade Level, Secondary: category/course type */}
        <div className="card-flat p-5 border border-ink/10 bg-white">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-copper mb-3">
            <Filter className="w-4 h-4" /> Filters — grade first, then type
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Grade level (primary)</span>
              <select className={`${selectCls} w-full mt-1`} value={grade} onChange={(e) => setGrade(e.target.value)}>
                <option value="">All grades</option>
                <option value="K">Kindergarten</option>
                {["1","2","3","4","5","6","7","8","9","10","11","12"].map((g) => <option key={g} value={g}>Grade {g}</option>)}
                <option value="adult">Adult</option>
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Core / Elective</span>
              <select className={`${selectCls} w-full mt-1`} value={courseType} onChange={(e) => setCourseType(e.target.value)}>
                <option value="">All</option>
                <option value="core">Core</option>
                <option value="elective">Elective</option>
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Non-grade section</span>
              <select className={`${selectCls} w-full mt-1`} value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
                <option value="">All sections</option>
                <option value="k12_core">K-12 Core</option>
                <option value="k12_elective">K-12 Elective</option>
                <option value="adult">Adult Courses</option>
                <option value="trade">Trade Courses</option>
                <option value="creative">Creative &amp; Community</option>
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
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Keyword</span>
              <div className="relative mt-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
                <input className="pl-9 pr-3 py-2.5 w-full rounded-lg border border-ink/20 bg-white text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-copper"
                  placeholder="biology, electrical, phonics…"
                  value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
            </label>
          </div>
          <div className="flex flex-wrap gap-3 mt-4">
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Source category</span>
              <select className={`${selectCls} mt-1`} value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="">All categories</option>
                <option value="academy">Homeschool Academy ({sourceCounts.academy})</option>
                <option value="module">Courses & Workshops ({sourceCounts.module})</option>
                <option value="protocol">Protocols ({sourceCounts.protocol})</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm font-bold text-ink/70 cursor-pointer select-none mt-6">
              <input type="checkbox" checked={showPlanned} onChange={(e) => setShowPlanned(e.target.checked)} className="accent-copper w-4 h-4" />
              Show courses still in development
            </label>
          </div>
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

        {/* Academy: hierarchical by grade → Core | Elective, then non-grade buckets */}
        {(grouped.academy?.length > 0 || gradeHierarchy.hierarchy && Object.keys(gradeHierarchy.hierarchy).length > 0) && (
          <div className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-copper text-white p-1.5 rounded-lg"><GraduationCap className="w-4 h-4" /></span>
              <h3 className="font-heading text-lg font-bold text-ink">Homeschool Academy</h3>
              <span className="text-xs text-ink/40 font-bold">({grouped.academy?.length || 0})</span>
            </div>
            {GRADE_ORDER.filter(g => gradeHierarchy.hierarchy[g]).map((g) => {
              const { core, electives } = gradeHierarchy.hierarchy[g];
              const auditRow = auditData?.grades?.find(r => r.grade === g);
              const label = g === "K" ? "Kindergarten" : `Grade ${g}`;
              return (
                <div key={g} className="mb-8">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-px flex-1 bg-ink/10" />
                    <span className="text-xs font-black uppercase tracking-widest text-copper bg-copper/10 px-3 py-1 rounded-full">{label}</span>
                    {auditRow && auditRow.status === "COMPLETE" && <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-full bg-emerald-600 text-white">Complete</span>}
                    {auditRow && auditRow.status === "INCOMPLETE" && <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-full bg-amber-500 text-white" title={`Missing: ${auditRow.missing.join(", ")}`}>Missing: {auditRow.missing.join(", ")}</span>}
                    <div className="h-px flex-1 bg-ink/10" />
                  </div>
                  {(core.length > 0 || (!courseType || courseType === "core")) && (
                    <div className="mb-4">
                      <div className="text-[11px] font-black uppercase tracking-widest text-ink/50 mb-2">Core Curriculum</div>
                      {core.length === 0 ? <p className="text-sm text-ink/40 italic">No core courses for this grade yet — shown as incomplete in the audit above.</p> : (
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                          {core.map((c) => (
                            <Link key={c.id} to={`/academy/courses/${c.slug}`} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white border-l-4 border-l-copper">
                              <div className="flex flex-wrap items-center gap-2">
                                {c.track && <TrackTag track={c.track} />}
                                <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-ink text-white">Core</span>
                                <LiveChip status={c.status} />
                              </div>
                              <div><div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div><div className="text-xs font-black uppercase tracking-widest text-copper mt-1">{[c.grade_label, c.subject_label].filter(Boolean).join(" · ")}</div></div>
                              <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                              <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45"><span>{c.lesson_count > 0 ? `${c.lesson_count} lessons${c.est_hours>0?` · ~${c.est_hours} hrs`:""}` : c.status==="published"?"Available now":"In development"}</span><span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span></div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {(electives.length > 0 || (!courseType || courseType === "elective")) && electives.length > 0 && (
                    <div>
                      <div className="text-[11px] font-black uppercase tracking-widest text-ink/50 mb-2">Electives</div>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {electives.map((c) => (
                          <Link key={c.id} to={`/academy/courses/${c.slug}`} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white">
                            <div className="flex flex-wrap items-center gap-2">{c.track && <TrackTag track={c.track} />}<span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-ink/10 text-ink border border-ink/15">Elective</span><LiveChip status={c.status} /></div>
                            <div><div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div><div className="text-xs font-black uppercase tracking-widest text-copper mt-1">{[c.grade_label, c.subject_label].filter(Boolean).join(" · ")}</div></div>
                            <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                            <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45"><span>{c.lesson_count>0?`${c.lesson_count} lessons${c.est_hours>0?` · ~${c.est_hours} hrs`:""}`:c.status==="published"?"Available now":"In development"}</span><span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span></div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            {/* Non-grade academy buckets */}
            {["adult","trade","creative"].map((bucket) => {
              const list = gradeHierarchy.buckets[bucket];
              if (!list || list.length === 0) return null;
              const labels = { adult: "Adult Courses", trade: "Trade Courses", creative: "Creative & Community Courses" };
              return (
                <div key={bucket} className="mb-8">
                  <div className="flex items-center gap-3 mb-3"><div className="h-px flex-1 bg-ink/10" /><span className="text-xs font-black uppercase tracking-widest text-copper bg-copper/10 px-3 py-1 rounded-full">{labels[bucket]}</span><div className="h-px flex-1 bg-ink/10" /></div>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {list.map((c) => (
                      <Link key={c.id} to={`/academy/courses/${c.slug}`} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white">
                        <div className="flex flex-wrap items-center gap-2"><TrackTag track={c.track} /><span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-ink/10 text-ink border border-ink/15">{bucket === "adult" ? "Adult" : bucket === "trade" ? "Trade" : "Creative"}</span><LiveChip status={c.status} /></div>
                        <div><div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div><div className="text-xs font-black uppercase tracking-widest text-copper mt-1">{[c.grade_label, c.subject_label].filter(Boolean).join(" · ")}</div></div>
                        <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                        <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45"><span>{c.lesson_count>0?`${c.lesson_count} lessons${c.est_hours>0?` · ~${c.est_hours} hrs`:""}`:c.status==="published"?"Available now":"In development"}</span><span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span></div>
                      </Link>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        {/* Non-academy sections: modules, protocols — unchanged */}
        {Object.entries(grouped).filter(([src]) => src !== "academy").map(([src, srcItems]) => {
          const meta = SOURCE_META[src] || SOURCE_META.other;
          const Icon = meta.icon;
          return (
            <div key={src} className="mb-10">
              <div className="flex items-center gap-2 mb-4"><span className={`${meta.color} text-white p-1.5 rounded-lg`}><Icon className="w-4 h-4" /></span><h3 className="font-heading text-lg font-bold text-ink">{meta.label}</h3><span className="text-xs text-ink/40 font-bold">({srcItems.length})</span></div>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                {srcItems.map((c) => (
                  <Link key={c.id} to={c.source==='module'?`/modules/${c.slug}`:`/ascension-protocols`} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all bg-white">
                    <div className="flex flex-wrap items-center gap-2">{c.track && <TrackTag track={c.track} />}<LiveChip status={c.status} />{c.price_cents>0 && <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">${(c.price_cents/100).toFixed(2)}</span>}{c.price_cents===0 && <span className="text-xs font-bold text-ink/70 bg-ink/5 border border-ink/15 px-2 py-0.5 rounded-full">Included with membership</span>}</div>
                    <div><div className="font-heading text-lg font-bold text-ink leading-snug">{c.title}</div>{(c.grade_label||c.subject_label)&&<div className="text-xs font-black uppercase tracking-widest text-copper mt-1">{[c.grade_label,c.subject_label].filter(Boolean).join(" · ")}</div>}</div>
                    <p className="text-sm text-ink/60 leading-relaxed line-clamp-2">{c.summary}</p>
                    <div className="mt-auto flex items-center justify-between text-xs font-bold text-ink/45"><span>{c.lesson_count>0?`${c.lesson_count} lessons${c.est_hours>0?` · ~${c.est_hours} hrs`:""}`:c.status==="published"?"Available now":"In development"}</span><span className="flex items-center gap-1 text-copper font-black uppercase tracking-widest">View <ArrowRight className="w-3.5 h-3.5" /></span></div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </section>
      <AcademyFooter />
    </div>
  );
}
