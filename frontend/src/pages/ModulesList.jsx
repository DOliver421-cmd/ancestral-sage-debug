import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL, openAuthedUrl } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Link } from "react-router-dom";
import { Lock, Zap, BookOpen, ShoppingBag, CheckCircle, Loader2, Award, FlaskConical, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import SharePanel from "../components/SharePanel";

const COURSE_CATEGORIES = {
  general: "General",
  electrical: "Electrical & Trades",
  "ai-tech": "AI & Tech",
  "arts-music": "Arts & Music",
  workforce: "Workforce",
  wellness: "Wellness",
  publishing: "Publishing",
  business: "Business",
};

export default function ModulesList() {
  const { user } = useAuth();
  const [modules, setModules] = useState([]);
  const [progress, setProgress] = useState([]);
  const [creatorCourses, setCreatorCourses] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState(new Set());
  const [tab, setTab] = useState("core");
  const [category, setCategory] = useState("");
  const [buying, setBuying] = useState(null);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [catalogLoading, setCatalogLoading] = useState(true);

  const loadCatalog = useCallback(() => {
    setCatalogLoading(true);
    setCatalogError("");
    fetch(`${BACKEND_URL}/api/modules`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => setModules(Array.isArray(data) ? data : []))
      .catch((e) => setCatalogError(e.message || "Could not load the curriculum."))
      .finally(() => setCatalogLoading(false));
    if (user) {
      api.get("/progress/me").then((r) => setProgress(r.data)).catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  useEffect(() => {
    if (tab !== "community") return;
    setLoadingCourses(true);
    Promise.allSettled([
      api.get("/creator/courses/published", { params: { limit: 48, category } }),
      user ? api.get("/creator/enrollments/me") : Promise.resolve(null),
    ]).then(([catalogRes, enrollRes]) => {
      if (catalogRes.status === "fulfilled") setCreatorCourses(catalogRes.value.data.courses || []);
      if (enrollRes.status === "fulfilled" && enrollRes.value) setEnrolledIds(new Set(enrollRes.value.data.enrolled_course_ids || []));
    }).finally(() => setLoadingCourses(false));
  }, [tab, category, user]);

  async function handleEnrollOrBuy(course) {
    if (!user) { window.location.href = "/login"; return; }
    setBuying(course.course_id);
    try {
      const { data } = await api.post(`/creator/courses/${course.course_id}/checkout`);
      if (data.enrolled) { setEnrolledIds(prev => new Set([...prev, course.course_id])); }
      else if (data.url) { window.location.href = data.url; }
    } catch (e) {
      // Never fail silently — the customer clicked and deserves an answer.
      const detail = e?.response?.data?.detail || "";
      if (e?.response?.status === 501 || /not configured/i.test(String(detail))) {
        toast.info("Paid courses are coming soon — free courses enroll instantly, and nothing can be charged yet.");
      } else {
        toast.error(detail || "Could not start enrollment. Please try again.");
      }
    }
    finally { setBuying(null); }
  }

  const bySlug = Object.fromEntries(progress.map((p) => [p.module_slug, p]));
  const completedCount = modules.filter((m) => bySlug[m.slug]?.status === "completed").length;

  return (
    <AppShell>
      <div className="relative py-10 sm:py-12 px-4 sm:px-10"
        style={{ backgroundImage: "linear-gradient(rgba(10,10,15,0.72), rgba(10,10,15,0.82)), url('https://images.pexels.com/photos/34211750/pexels-photo-34211750.jpeg?auto=compress&cs=tinysrgb&w=1600')", backgroundSize: "cover", backgroundPosition: "center" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-signal">Core Curriculum</div>
          <h1 className="font-heading text-3xl sm:text-4xl font-black text-white mt-2">Learn. Build. Credential.</h1>
          <p className="text-white/70 mt-2 max-w-2xl">Core electrical training, creator-published courses, compliance certifications, and open-access learning — all in one place.</p>
        </div>
      </div>
      <div className="px-4 sm:px-10 py-8 sm:py-10 max-w-6xl">

        {/* TABS */}
        <div className="flex gap-2 flex-wrap mt-6">
          {[
            { key: "core", label: "Core Program", icon: Award, sub: `${modules.length} modules · ${completedCount} done` },
            { key: "community", label: "Creator Courses", icon: BookOpen, sub: `${creatorCourses.length} courses` },
            { key: "compliance", label: "Compliance", icon: ShieldCheck, sub: "OSHA · NFPA 70E" },
          ].map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 text-sm font-bold px-5 py-3 rounded-xl border transition-colors ${tab === t.key ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}>
              <t.icon className="w-4 h-4" />
              <div className="text-left">
                <div>{t.label}</div>
                <div className="text-[10px] font-normal opacity-60">{t.sub}</div>
              </div>
            </button>
          ))}
        </div>

        {/* CORE PROGRAM TAB */}
        {tab === "core" && (
          <>
            {catalogError && (
              <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700 flex items-start justify-between gap-4">
                <div>
                  <div className="font-bold mb-1">The curriculum could not be loaded.</div>
                  <div className="text-red-600/80">The server returned an error ({catalogError}). This is a site problem, not yours — try again, and if it persists the team has been told.</div>
                </div>
                <button onClick={loadCatalog} className="shrink-0 text-xs font-black bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">Retry</button>
              </div>
            )}
            {catalogLoading && !catalogError && (
              <div className="flex items-center justify-center py-24 text-ink/40"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading curriculum…</div>
            )}
            {!catalogLoading && !catalogError && modules.length === 0 && (
              <div className="text-center py-24">
                <BookOpen className="w-10 h-10 text-ink/20 mx-auto mb-3" />
                <p className="text-ink/40 text-sm">No curriculum modules published yet.</p>
              </div>
            )}
            <div className="mt-3 flex flex-wrap gap-5 text-sm">
              <button onClick={() => openAuthedUrl("/handbooks/instructor")} className="font-bold text-copper hover:underline cursor-pointer bg-transparent border-0 p-0">📘 Instructor Handbook →</button>
              <button onClick={() => openAuthedUrl("/handbooks/student")} className="font-bold text-copper hover:underline cursor-pointer bg-transparent border-0 p-0">📕 Student Handbook →</button>
              {user ? (
                <Link to="/ascension-protocols" className="font-bold text-copper hover:underline">🌱 Ascension Protocols (free) →</Link>
              ) : (
                <Link to="/register" className="font-bold text-copper hover:underline">🌱 Ascension Protocols (free for members) →</Link>
              )}
            </div>

        <div className="grid md:grid-cols-2 gap-5 mt-10">
          {modules.map((m) => {
            const p = bySlug[m.slug];
            const isFree = m.free;
            // Course CONTENT is never public — every module requires a registered
            // account (GET /modules/{slug} is auth-gated). "FREE" means "included in
            // the free tier once you're signed in", not "browseable logged out".
            const isLocked = !user;
            const badge = p?.status === "completed" ? "badge-signal" : p?.status === "in_progress" ? "badge-copper" : !user ? "badge-outline" : isFree ? "badge-signal" : "badge-outline";
            const label = p?.status === "completed" ? "Completed" : p?.status === "in_progress" ? "In Progress" : !user ? "Sign up to access" : isFree ? "FREE" : "Not Started";
            return (
              <div key={m.slug} className="card-flat p-6 group relative" data-testid={`mod-card-${m.slug}`}>
                {isLocked && (
                  <div className="absolute inset-0 bg-white/60 backdrop-blur-[1px] rounded-2xl z-10 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                      <Lock className="w-6 h-6 text-ink/30 mx-auto mb-2" />
                      <div className="text-sm font-bold text-ink/50">Sign up to unlock</div>
                    </div>
                  </div>
                )}
                <div className="flex items-start justify-between">
                  <div className="font-heading text-xs font-black text-copper">{isFree ? "FREE INTRO" : `MODULE ${m.order.toString().padStart(2, "0")}`}</div>
                  <span className={`${badge} flex items-center gap-1`}>
                    {isFree && <Zap className="w-3 h-3" />}{label}
                  </span>
                </div>
                <div className="font-heading text-xl font-bold mt-3 text-ink group-hover:text-copper transition-colors">{m.title}</div>
                <p className="text-sm text-ink/70 mt-3 leading-relaxed">{m.summary}</p>
                <div className="mt-5 flex gap-4 text-xs overline text-ink/60">
                  <span>{m.hours}h</span>
                  <span>{m.tasks.length} tasks</span>
                  {m.points && <span className="text-amber-600">+{m.points} pts</span>}
                  {m.leads_to && <span className="text-copper">Leads into full program</span>}
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <Link
                    to={isLocked ? "/register" : `/modules/${m.slug}`}
                    className="text-sm font-bold text-copper hover:underline"
                  >
                    {isLocked ? "Sign up to start →" : "Start module →"}
                  </Link>
                  {isFree && user && (
                    <SharePanel compact url={`/modules/${m.slug}`} title={m.title} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div className="text-center mt-8">
          <Link to="/courses" className="text-sm font-bold text-copper hover:underline">Browse all creator courses →</Link>
        </div>
          </>
        )}

        {/* COMMUNITY COURSES TAB */}
        {tab === "community" && (
          <>
            <div className="flex gap-2 flex-wrap mt-4">
              <button onClick={() => setCategory("")} className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-colors ${category === "" ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}>All</button>
              {Object.entries(COURSE_CATEGORIES).map(([key, label]) => (
                <button key={key} onClick={() => setCategory(key)}
                  className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-colors ${category === key ? "bg-ink text-bone border-ink" : "border-ink/20 text-ink/60 hover:border-ink/40"}`}>{label}</button>
              ))}
            </div>
            {loadingCourses ? (
              <div className="flex items-center justify-center py-24 text-ink/40"><Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading courses…</div>
            ) : creatorCourses.length === 0 ? (
              <div className="text-center py-24">
                <BookOpen className="w-10 h-10 text-ink/20 mx-auto mb-3" />
                <p className="text-ink/40 text-sm">No published courses yet in this category.</p>
                {user && <Link to="/creator/courses" className="text-copper text-sm font-bold mt-2 inline-block">Publish your own →</Link>}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                {creatorCourses.map((course) => {
                  const enrolled = enrolledIds.has(course.course_id);
                  const isBuying = buying === course.course_id;
                  return (
                    <div key={course.course_id} className="card-flat p-5 flex flex-col gap-3">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs text-ink/40 font-medium">{COURSE_CATEGORIES[course.category] || course.category}</span>
                        <span className="text-xs font-bold text-copper bg-amber-100 px-2 py-0.5 rounded-full">
                          {course.price_cents === 0 ? "Free" : `$${(course.price_cents / 100).toFixed(2)}`}
                        </span>
                      </div>
                      <div className="font-heading font-bold text-ink text-base leading-snug">{course.title}</div>
                      {course.description && <p className="text-xs text-ink/60 line-clamp-2">{course.description}</p>}
                      <div className="flex items-center justify-between mt-auto pt-2 border-t border-ink/10">
                        <span className="text-xs text-ink/40">{course.enrollment_count || 0} enrolled</span>
                        {enrolled ? (
                          <span className="flex items-center gap-1 text-xs font-bold text-green-600"><CheckCircle className="w-3.5 h-3.5" /> Enrolled</span>
                        ) : (
                          <button onClick={() => handleEnrollOrBuy(course)} disabled={isBuying}
                            className="flex items-center gap-1.5 text-xs font-bold bg-copper hover:bg-amber-600 text-bone px-3 py-1.5 rounded-full transition-colors disabled:opacity-50">
                            {isBuying ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShoppingBag className="w-3 h-3" />}
                            {course.price_cents === 0 ? "Enroll Free" : "Buy Now"}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {/* COMPLIANCE TAB */}
        {tab === "compliance" && (
          <div className="mt-6 space-y-4">
            <p className="text-sm text-ink/60 max-w-2xl">Industry compliance certifications — OSHA 10, NFPA 70E, PPE, and LOTO. These modules expire and must be renewed.</p>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                { slug: "osha-10-electrical", title: "OSHA 10 — Electrical Industry Awareness", hours: 10, expires: "36 months" },
                { slug: "nfpa-70e-awareness", title: "NFPA 70E — Workplace Electrical Safety", hours: 6, expires: "12 months" },
                { slug: "ppe-fitting", title: "PPE Selection, Fit & Maintenance", hours: 4, expires: "12 months" },
                { slug: "loto-procedure", title: "Lockout/Tagout Procedure Certification", hours: 4, expires: "12 months" },
              ].map((c) => (
                <div key={c.slug} className="card-flat p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <ShieldCheck className="w-4 h-4 text-copper" />
                    <span className="font-heading font-bold text-ink text-sm">{c.title}</span>
                  </div>
                  <div className="flex gap-4 text-xs text-ink/50 mt-1">
                    <span>{c.hours}h</span>
                    <span>Expires: {c.expires}</span>
                  </div>
                  <Link to={`/compliance/${c.slug}`} className="text-sm font-bold text-copper hover:underline mt-3 inline-block">Start →</Link>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
