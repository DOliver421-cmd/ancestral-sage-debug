import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import AppShell from "../../components/AppShell";
import { ProgressBar, LiveChip } from "./academyKit";
import {
  ArrowLeft, Film, Link2, AlertTriangle, RefreshCw, CheckCircle2, Circle, GraduationCap,
} from "lucide-react";

/* /academy/build — STAFF ONLY build tracker for the Homeschool Academy.
   Shows the live course catalog with lesson counts, published status, and
   video-enrichment coverage so staff can see at a glance what is done, what
   is in development, and which courses still need a pinned video ID. */

const BUILD_CHECKLIST = [
  { phase: "Phase 1 — Discovery", items: [
    "Existing architecture mapped (FastAPI + MongoDB + React SPA)",
    "Existing LMS, auth, AI, admin, and seeding patterns mapped",
  ]},
  { phase: "Phase 2 — Academy Gateway", items: [
    "/wai-institute gateway (Homeschool, done right.)",
    "Curriculum entry points + WAI Institute bridge",
  ]},
  { phase: "Phase 3 — Curriculum", items: [
    "Tracks, grades, subjects, courses (published + honest planned entries)",
    "Real lesson trees with knowledge checks for all published courses",
    "Video enrichment mapping (creator-attributed, on-site embeds)",
    "Educator & resource attribution (Black creators and scholars)",
  ]},
  { phase: "Phase 4 — Learning Engine", items: [
    "Student enrollment + lesson progression + 80% mastery gate",
    "Server-side unlock enforcement",
    "Florida compliance toolkit (NOI, quarterly, annual, transcript)",
  ]},
  { phase: "Phase 5 — Growth", items: [
    "Full K–12 content population (planned catalog → published)",
    "Pin remaining video IDs (Crash Course Literature, Math Antics, Amoeba Sisters)",
    "Run DB-backed test suites against live MongoDB before launch sign-off",
  ]},
];

export default function AcademyBuildTracker() {
  const [courses, setCourses] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/academy/courses")
      .then((r) => setCourses(r.data.courses || []))
      .catch((e) => setError(e?.response?.data?.detail || "Could not load the catalog."))
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(() => {
    if (!courses) return null;
    const published = courses.filter((c) => c.status === "published").length;
    const planned = courses.length - published;
    return { total: courses.length, published, planned };
  }, [courses]);

  if (loading) {
    return (
      <AppShell>
        <p className="px-10 py-16 flex items-center gap-2 text-ink/45">
          <RefreshCw className="w-4 h-4 animate-spin" /> Loading build tracker…
        </p>
      </AppShell>
    );
  }
  if (error) {
    return (
      <AppShell>
        <div className="px-10 py-16 max-w-2xl">
          <AlertTriangle className="w-10 h-10 text-destructive" />
          <h1 className="font-heading text-2xl font-bold text-ink mt-3">{error}</h1>
          <Link to="/admin" className="btn-copper inline-flex items-center gap-2 mt-6">
            <ArrowLeft className="w-4 h-4" /> Back to admin
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl" data-testid="academy-build-tracker">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link to="/admin" className="inline-flex items-center gap-1.5 text-sm font-bold text-copper hover:text-ink transition-colors">
              <ArrowLeft className="w-4 h-4" /> Admin
            </Link>
            <h1 className="font-heading text-3xl font-bold text-ink mt-2">Homeschool Build Tracker</h1>
            <p className="text-ink/55 mt-1">Staff-only view of the live catalog, lesson coverage, and video enrichment status.</p>
          </div>
          {stats && (
            <div className="flex gap-3 text-center">
              <div className="card-flat bg-white px-5 py-3 border border-ink/10">
                <div className="font-heading text-2xl font-bold text-ink">{stats.total}</div>
                <div className="overline text-ink/50">Courses</div>
              </div>
              <div className="card-flat bg-white px-5 py-3 border border-ink/10">
                <div className="font-heading text-2xl font-bold text-emerald-700">{stats.published}</div>
                <div className="overline text-ink/50">Published</div>
              </div>
              <div className="card-flat bg-white px-5 py-3 border border-ink/10">
                <div className="font-heading text-2xl font-bold text-amber-700">{stats.planned}</div>
                <div className="overline text-ink/50">Planned</div>
              </div>
            </div>
          )}
        </div>

        {/* Live course table */}
        <div className="card-flat bg-white border border-ink/10 overflow-hidden mt-8">
          <div className="px-6 py-4 border-b border-ink/10 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-copper" />
            <h2 className="font-heading text-lg font-bold text-ink">Live course catalog</h2>
            <span className="text-xs text-ink/40 font-bold ml-auto">from the live seed, not a stale doc</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs overline text-ink/45 border-b border-ink/10">
                  <th className="px-6 py-3">Course</th>
                  <th className="px-4 py-3">Track</th>
                  <th className="px-4 py-3">Grades</th>
                  <th className="px-4 py-3 text-center">Lessons</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Video</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink/5">
                {(courses || []).map((c) => (
                  <tr key={c.slug} className="hover:bg-ink/[0.02]">
                    <td className="px-6 py-3">
                      <Link to={`/academy/courses/${c.slug}`} className="font-bold text-ink hover:text-copper transition-colors">
                        {c.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-ink/60">{c.track}</td>
                    <td className="px-4 py-3 text-ink/60">{c.grade_label}</td>
                    <td className="px-4 py-3 text-center font-bold text-ink/70">{c.lesson_count}</td>
                    <td className="px-4 py-3"><LiveChip status={c.status} /></td>
                    <td className="px-4 py-3">
                      <VideoChip slug={c.slug} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Build plan checklist */}
        <div className="card-flat bg-white border border-ink/10 overflow-hidden mt-8">
          <div className="px-6 py-4 border-b border-ink/10 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-copper" />
            <h2 className="font-heading text-lg font-bold text-ink">Build plan progress</h2>
          </div>
          <div className="p-6 grid md:grid-cols-2 gap-6">
            {BUILD_CHECKLIST.map((phase) => (
              <div key={phase.phase}>
                <div className="overline text-copper mb-2">{phase.phase}</div>
                <ul className="space-y-1.5">
                  {phase.items.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-sm text-ink/75">
                      <Circle className="w-3.5 h-3.5 mt-0.5 text-copper shrink-0" /> {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <p className="px-6 pb-5 text-xs text-ink/40">
            Source of truth: HOMESCHOOL_ACADEMY_BUILD_PLAN.md + HOMESCHOOL_VIDEO_ENRICHMENT_PLAN.md; catalog rows are live from the API.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

/* Video status per course slug — mirror of enrichment mapping coverage.
   (The mapping lives in the seed; the staff-facing summary is kept in sync
   manually until a dedicated tracker endpoint ships in Phase V2.) */
const VIDEO_COVERAGE = {
  ready: new Set([
    "african-kingdoms-empires", "ethnomathematics-black-pioneers", "global-african-diaspora",
    "diaspora-mathematics-algorithms-astronomy", "african-philosophy-ethics",
    "african-american-literature-foundations", "reading-foundations-kindergarten",
    "reading-foundations-grade-2", "reading-foundations-grade-1", "math-grade-1", "math-grade-2",
    "multiplication-division-fractions-grade-4", "math-grade-3", "math-grade-5", "math-grade-6",
    "math-grade-8", "science-grade-2", "science-grade-5", "science-grade-8",
    "social-studies-grade-5", "social-studies-grade-7", "visual-arts-foundations",
    "digital-art-grade-9", "applied-electrical-year-1", "electrical-year-2", "trade-math-grade-8",
    "adult-ed-hse-social-studies", "entrepreneurship-foundations",
  ]),
  noId: new Set(["adult-ed-hse-ela", "adult-ed-hse-math", "adult-ed-hse-science"]),
};

function VideoChip({ slug }) {
  if (VIDEO_COVERAGE.ready.has(slug)) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-600/10 border border-emerald-600/30 rounded-full px-2.5 py-1">
        <Film className="w-3 h-3" /> Embedded
      </span>
    );
  }
  if (VIDEO_COVERAGE.noId.has(slug)) {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-500/10 border border-amber-500/30 rounded-full px-2.5 py-1">
        <AlertTriangle className="w-3 h-3" /> Needs video ID
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs font-bold text-ink/40 bg-ink/5 border border-ink/10 rounded-full px-2.5 py-1">
      <Link2 className="w-3 h-3" /> Resource link
    </span>
  );
}
