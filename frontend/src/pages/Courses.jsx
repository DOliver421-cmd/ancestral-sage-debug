import { useState, useEffect, useRef, useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { BookOpen, ShoppingBag, CheckCircle, Loader2, GraduationCap, Wrench, Zap, ArrowRight } from "lucide-react";
import CheckoutModal from "../components/CheckoutModal";

const CATEGORY_META = {
  k12_core:      { label: "K-12 Core Subjects", icon: GraduationCap, color: "bg-copper" },
  k12_elective:  { label: "K-12 Electives", icon: GraduationCap, color: "bg-copper" },
  adult:         { label: "Adult Education & Career", icon: GraduationCap, color: "bg-teal-600" },
  trade:         { label: "Trade & Workforce", icon: Wrench, color: "bg-amber-600" },
  creative:      { label: "Creative & Community", icon: GraduationCap, color: "bg-rose-600" },
  general:       { label: "General", icon: BookOpen, color: "bg-ink" },
  electrical:    { label: "Electrical & Trades", icon: Wrench, color: "bg-amber-600" },
  "ai-tech":     { label: "AI & Technology", icon: Wrench, color: "bg-purple-700" },
  "arts-music":  { label: "Arts & Music", icon: GraduationCap, color: "bg-rose-600" },
  workforce:     { label: "Workforce Development", icon: Wrench, color: "bg-amber-600" },
  wellness:      { label: "Wellness", icon: GraduationCap, color: "bg-green-700" },
  publishing:    { label: "Publishing", icon: BookOpen, color: "bg-ink" },
  business:      { label: "Business", icon: GraduationCap, color: "bg-blue-700" },
  protocol:      { label: "Protocols", icon: Zap, color: "bg-purple-700" },
};

const CATEGORY_ORDER = [
  "k12_core", "k12_elective", "adult", "trade", "creative",
  "general", "electrical", "ai-tech", "arts-music", "workforce",
  "wellness", "publishing", "business", "protocol",
];

function PriceBadge({ cents, source }) {
  if (source === "creator" && cents === 0) return <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Free</span>;
  if (source === "module" && cents === 0) return <span className="text-xs font-bold text-ink/70 bg-ink/5 border border-ink/15 px-2 py-0.5 rounded-full">Included with membership</span>;
  if (cents === 0) return <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Free</span>;
  return <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">${(cents / 100).toFixed(2)}</span>;
}

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
      grade_level: raw.grade_level || (raw.grades?.[0] || ""),
      lesson_count: raw.lesson_count || 0,
      est_hours: raw.est_hours || 0,
      slug: raw.slug,
      category: raw.category || "k12_elective",
      price_cents: 0,
      link: `/academy/courses/${raw.slug}`,
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
      link: `/modules/${raw.slug}`,
    };
  }
  if (source === "protocol") {
    return {
      id: raw.slug || raw.id || "ascension-protocols",
      source: "protocol",
      title: raw.title,
      summary: raw.description || raw.summary || "",
      description: raw.description || "",
      status: "published",
      track: "protocol",
      tracks: ["protocol"],
      grade_label: "",
      subject_label: "Protocol",
      subject: "protocol",
      grades: [],
      lesson_count: raw.lesson_count || 0,
      est_hours: 0,
      slug: raw.slug || "ascension-protocols",
      category: "protocol",
      price_cents: 0,
      link: `/ascension-protocols`,
    };
  }
  if (source === "creator") {
    return {
      id: raw.course_id,
      source: "creator",
      title: raw.title,
      summary: raw.description || "",
      description: raw.description || "",
      status: raw.status || "published",
      track: raw.category || "",
      tracks: [raw.category || ""],
      grade_label: "",
      subject_label: raw.category || "",
      subject: raw.category || "",
      grades: [],
      lesson_count: raw.sections?.reduce((a, s) => a + (s.lessons?.length || 0), 0) || 0,
      est_hours: 0,
      slug: raw.course_id,
      category: raw.category || "general",
      price_cents: raw.price_cents || 0,
      link: null,
    };
  }
  return null;
}

export default function Courses() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get("highlight");
  const highlightRef = useRef(null);
  const [courses, setCourses] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);
  const [checkoutUrl, setCheckoutUrl] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [academyRes, modulesRes, creatorRes, enrollRes] = await Promise.allSettled([
          api.get("/academy/courses"),
          api.get("/modules"),
          api.get("/creator/courses/published", { params: { limit: 48 } }),
          user ? api.get("/creator/enrollments/me") : Promise.resolve(null),
        ]);
        const items = [];
        if (academyRes.status === "fulfilled") {
          for (const c of (academyRes.value.data?.courses || [])) {
            const n = normalizeItem("academy", c);
            if (n) items.push(n);
          }
        }
        if (modulesRes.status === "fulfilled") {
          for (const m of (Array.isArray(modulesRes.value.data) ? modulesRes.value.data : [])) {
            const n = normalizeItem("module", m);
            if (n) items.push(n);
          }
        }
        if (creatorRes.status === "fulfilled") {
          for (const c of (creatorRes.value.data?.courses || [])) {
            const n = normalizeItem("creator", c);
            if (n) items.push(n);
          }
        }
        if (enrollRes.status === "fulfilled" && enrollRes.value) {
          setEnrolledIds(new Set(enrollRes.value.data.enrolled_course_ids || []));
        }
        setCourses(items);
      } catch {
        toast.error("Could not load courses.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  async function handleEnrollOrBuy(course) {
    if (!user) {
      window.location.href = "/login";
      return;
    }
    setBuying(course.id);
    try {
      const { data } = await api.post(`/creator/courses/${course.id}/checkout`);
      if (data.enrolled) {
        setEnrolledIds(prev => new Set([...prev, course.id]));
        toast.success("Enrolled! Check your dashboard.");
      } else if (data.url) {
        setCheckoutUrl(data.url);
      }
    } catch (e) {
      const detail = e?.response?.data?.detail || "";
      if (e?.response?.status === 501 || /not configured/i.test(String(detail))) {
        toast.info("Paid courses are coming soon — free courses enroll instantly, and nothing can be charged yet.");
      } else {
        toast.error(detail || "Could not start enrollment.");
      }
    } finally {
      setBuying(null);
    }
  }

  const grouped = useMemo(() => {
    const g = {};
    for (const c of courses) {
      const key = c.category || "other";
      if (!g[key]) g[key] = [];
      g[key].push(c);
    }
    for (const k of Object.keys(g)) {
      g[k].sort((a, b) => (a.title || "").localeCompare(b.title || ""));
    }
    return g;
  }, [courses]);

  const visibleCategories = useMemo(() => {
    return CATEGORY_ORDER.filter(k => (grouped[k] || []).length > 0);
  }, [grouped]);

  const isHighlighted = (item) => item.id === highlightId;

  return (
    <div className="min-h-screen bg-bone">
      <PublicNav />
      <div className="relative py-12 px-6 border-b border-ink/10"
        style={{ backgroundImage: "linear-gradient(rgba(10,10,15,0.72), rgba(10,10,15,0.82)), url('https://images.pexels.com/photos/28593054/pexels-photo-28593054.jpeg?auto=compress&cs=tinysrgb&w=1600')", backgroundSize: "cover", backgroundPosition: "center" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-signal">M.O.R.E. Institute</div>
        </div>
      </div>
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to="/" />
        <div className="mt-6">
          <div className="overline text-copper">Course Catalogue</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">All courses & training</h1>
          <p className="text-ink/60 mt-3 max-w-2xl">
            Every learning path on the platform — homeschool academy, workforce modules, protocols, and community creator courses. Browse freely; sign in to enroll.
          </p>
        </div>

        {/* Featured free course */}
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <div className="overline text-copper">Featured Free Course</div>
          </div>
          <Link to={user ? "/ascension-protocols" : "/register"}
            className="flex flex-col sm:flex-row sm:items-center gap-4 rounded-2xl p-6 transition-all hover:shadow-lg"
            style={{ background: "linear-gradient(135deg,#14120a 0%,#241a08 60%,#0d1a0a 100%)", border: "1px solid rgba(232,165,30,0.35)" }}>
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0" style={{ background: "rgba(232,165,30,0.15)", fontSize: 28 }}>𓋹</div>
            <div className="flex-1">
              <div className="overline" style={{ color: "#E8A51E" }}>Free for members · Zero Tokens · Sign-up required</div>
              <div className="font-heading font-extrabold text-white" style={{ fontSize: "1.15rem", lineHeight: 1.25 }}>
                The Ascension Protocols — Ancestral & Cosmic Remembrance
              </div>
              <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.65)" }}>
                A 7/30/90-day Kemetic-grounded course. The syllabus is the teacher, the moon keeps the schedule.
              </p>
            </div>
            <span className="inline-flex items-center gap-2 font-bold text-sm px-5 py-2.5 rounded-xl shrink-0 self-start sm:self-center" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              {user ? "Begin free →" : "Sign up to begin — free →"}
            </span>
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24 text-ink/40">
            <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading courses…
          </div>
        ) : courses.length === 0 ? (
          <div className="text-center py-24">
            <BookOpen className="w-10 h-10 text-ink/20 mx-auto mb-3" />
            <p className="text-ink/40 text-sm">No published courses yet.</p>
          </div>
        ) : (
          <div className="mt-10 space-y-12">
            {visibleCategories.map((catKey) => {
              const items = grouped[catKey];
              const meta = CATEGORY_META[catKey] || { label: catKey, icon: BookOpen, color: "bg-ink" };
              const Icon = meta.icon;
              return (
                <section key={catKey}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className={`${meta.color} text-white p-1.5 rounded-lg`}><Icon className="w-4 h-4" /></span>
                    <h2 className="font-heading text-xl font-bold text-ink">{meta.label}</h2>
                    <span className="text-xs text-ink/40 font-bold">({items.length})</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {items.map((course) => {
                      const enrolled = enrolledIds.has(course.id);
                      const isBuying = buying === course.id;
                      const highlighted = isHighlighted(course);
                      const CardContent = (
                        <div
                          ref={highlighted ? (el => { if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "center" }), 300); }) : null}
                          className={`card-flat p-5 flex flex-col gap-3 transition-all ${highlighted ? "ring-2 ring-copper shadow-lg" : ""}`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="text-xs text-ink/40 font-medium">{meta.label}</span>
                            <PriceBadge cents={course.price_cents} source={course.source} />
                          </div>
                          <div className="font-heading font-bold text-ink text-base leading-snug">{course.title}</div>
                          {course.summary && (
                            <p className="text-xs text-ink/60 line-clamp-2">{course.summary}</p>
                          )}
                          <div className="flex items-center justify-between mt-auto pt-2 border-t border-ink/10">
                            <span className="text-xs text-ink/40">
                              {course.lesson_count > 0 ? `${course.lesson_count} lesson${course.lesson_count === 1 ? "" : "s"}${course.est_hours > 0 ? ` · ~${course.est_hours} hrs` : ""}` : course.status === "published" ? "Available now" : "In development"}
                            </span>
                            {course.source === "creator" ? (
                              enrolled ? (
                                <span className="flex items-center gap-1 text-xs font-bold text-green-600">
                                  <CheckCircle className="w-3.5 h-3.5" /> Enrolled
                                </span>
                              ) : (
                                <button
                                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleEnrollOrBuy(course); }}
                                  disabled={isBuying}
                                  className="flex items-center gap-1.5 text-xs font-bold bg-copper hover:bg-amber-600 text-bone px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
                                >
                                  {isBuying ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShoppingBag className="w-3 h-3" />}
                                  {course.price_cents === 0 ? "Enroll Free" : "Buy Now"}
                                </button>
                              )
                            ) : (
                              <span className="inline-flex items-center gap-1 text-xs font-black uppercase tracking-widest text-copper">
                                View <ArrowRight className="w-3.5 h-3.5" />
                              </span>
                            )}
                          </div>
                        </div>
                      );

                      if (course.link) {
                        return (
                          <Link key={course.id} to={course.link} ref={highlighted ? highlightRef : null} className="block">
                            {CardContent}
                          </Link>
                        );
                      }
                      return <div key={course.id}>{CardContent}</div>;
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        )}

        <div className="text-center mt-10 text-sm text-ink/40">
          Want to teach?{" "}
          {user ? (
            <Link to="/creator/courses" className="text-copper font-bold">Publish your first course →</Link>
          ) : (
            <Link to="/register" className="text-copper font-bold">Create an account →</Link>
          )}
        </div>
        <CheckoutModal url={checkoutUrl} onClose={async () => {
          setCheckoutUrl(null);
          if (user) {
            try {
              const { data } = await api.get("/creator/enrollments/me");
              setEnrolledIds(new Set(data.enrolled_course_ids || []));
            } catch {}
          }
        }} />
      </div>
    </div>
  );
}
