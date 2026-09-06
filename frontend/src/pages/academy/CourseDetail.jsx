import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { PublicHeader, AcademyFooter, TrackTag, LiveChip } from "./academyKit";
import { ArrowRight, Lock, BookOpen, Clock, Target, ChevronDown, AlertCircle, GraduationCap } from "lucide-react";

/* /academy/courses/:slug — public course page (full lesson content is gated
   to an enrolled student owner via content_visible). */

export default function CourseDetail() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [openUnits, setOpenUnits] = useState([]);

  useEffect(() => {
    setData(null);
    api.get(`/academy/courses/${slug}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail || "Course not found"));
  }, [slug]);

  const toggleUnit = (u) => setOpenUnits((cur) =>
    cur.includes(u) ? cur.filter((x) => x !== u) : [...cur, u]
  );

  if (error) {
    return (
      <div className="min-h-screen bg-bone">
        <PublicHeader />
        <div className="max-w-3xl mx-auto px-6 py-24 text-center">
          <AlertCircle className="w-10 h-10 text-destructive mx-auto mb-4" />
          <h1 className="font-heading text-2xl font-bold text-ink">{error}</h1>
          <Link to="/academy/curriculum" className="btn-copper inline-flex items-center gap-2 mt-6">Back to curriculum</Link>
        </div>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="min-h-screen bg-bone">
        <PublicHeader />
        <p className="text-center text-ink/50 py-24">Loading course…</p>
      </div>
    );
  }

  const planned = data.status === "planned";
  const totalLessons = data.units.reduce((a, u) => a + u.lessons.length, 0);

  return (
    <div className="min-h-screen bg-bone" data-testid="course-detail">
      <PublicHeader />
      <section className="bg-ink text-white">
        <div className="max-w-6xl mx-auto px-6 py-10">
          <Link to="/academy/curriculum" className="text-white/50 hover:text-white text-sm font-bold flex items-center gap-1 mb-4">
            <ArrowRight className="w-3.5 h-3.5 rotate-180" /> Curriculum
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <TrackTag track={data.track} />
            <LiveChip status={data.status} />
            <span className="text-xs text-white/50 font-bold">{data.grade_label} · {data.subject_label}</span>
          </div>
          <h1 className="font-heading text-4xl font-bold mt-4 leading-tight max-w-3xl">{data.title}</h1>
          <p className="text-white/65 mt-3 max-w-3xl leading-relaxed">{data.description}</p>
          <div className="flex flex-wrap items-center gap-4 mt-5 text-sm text-white/60 font-bold">
            <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-signal" /> ~{data.est_hours} hours</span>
            <span className="flex items-center gap-1.5"><BookOpen className="w-4 h-4 text-signal" /> {totalLessons} lessons</span>
            <span className="flex items-center gap-1.5"><Target className="w-4 h-4 text-signal" /> Pass each lesson at {data.passing_score}%+ to advance</span>
          </div>
          {!planned && (
            <Link to="/academy/parent" className="inline-flex items-center gap-2 px-6 py-3 bg-signal text-ink font-black hover:bg-signal/85 transition-colors mt-6">
              <GraduationCap className="w-4 h-4" /> {user ? "Enroll this course for your student" : "Start Homeschooling Free"} <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        {planned ? (
          <div className="card-flat border-l-4 border-amber-500 p-8 bg-white">
            <div className="font-heading text-xl font-bold text-ink flex items-center gap-2"><AlertCircle className="w-5 h-5 text-amber-600" /> This course is in development</div>
            <p className="text-ink/60 mt-2 leading-relaxed">
              This catalog entry shows the shape of the full program, but its lessons aren't written yet.
              We won't pretend it's ready: it will appear as <strong>Available now</strong> only once real
              content ships. Explore the courses that are live today, or check back as the curriculum grows.
            </p>
            <Link to="/academy/curriculum" className="btn-copper inline-flex items-center gap-2 mt-5">See available courses <ArrowRight className="w-4 h-4" /></Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Unit / lesson map */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="font-heading text-2xl font-bold text-ink">Course map</h2>
              {data.units.map((unit, ui) => {
                const open = openUnits.includes(unit.slug) || ui === 0;
                return (
                  <div key={unit.slug} className="card-flat bg-white border border-ink/10 overflow-hidden">
                    <button onClick={() => toggleUnit(unit.slug)} className="w-full flex items-center justify-between gap-3 p-5 text-left hover:bg-ink/[0.02] transition-colors">
                      <div>
                        <div className="overline text-copper">Unit {unit.order}</div>
                        <div className="font-heading text-lg font-bold text-ink">{unit.title}</div>
                        <p className="text-xs text-ink/50 mt-0.5">{unit.lessons.length} lessons</p>
                      </div>
                      <ChevronDown className={`w-5 h-5 text-ink/40 transition-transform ${open ? "rotate-180" : ""}`} />
                    </button>
                    {open && (
                      <ol className="border-t border-ink/10 divide-y divide-ink/5">
                        {unit.lessons.map((lesson) => (
                          <li key={lesson.slug} className="flex items-center gap-3 px-5 py-3">
                            {data.content_visible
                              ? <BookOpen className="w-4 h-4 text-copper shrink-0" />
                              : <Lock className="w-4 h-4 text-ink/30 shrink-0" />}
                            <span className="text-sm font-bold text-ink flex-1">{lesson.title}</span>
                            <span className="text-xs text-ink/45 font-bold">{lesson.minutes} min</span>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                );
              })}
              {!data.content_visible && (
                <div className="card-flat border-l-4 border-copper bg-white p-6">
                  <div className="font-heading font-bold text-ink flex items-center gap-2"><Lock className="w-4 h-4 text-copper" /> Lesson content is for enrolled students</div>
                  <p className="text-sm text-ink/60 mt-1.5 leading-relaxed">
                    Create a free parent account, add a student in this grade, and the course will be
                    ready to open — lessons unlock one at a time as mastery is earned.
                  </p>
                  <div className="flex flex-wrap gap-3 mt-4">
                    <Link to={user ? "/academy/parent" : "/register"} className="btn-copper inline-flex items-center gap-2 text-sm">{user ? "Open my family dashboard" : "Create a parent account"} <ArrowRight className="w-3.5 h-3.5" /></Link>
                    {!user && <Link to="/login" className="text-sm font-bold text-copper hover:text-ink self-center">I already have an account</Link>}
                  </div>
                </div>
              )}
              {data.content_visible && data.units[0]?.lessons?.length > 0 && (
                // No ?student= needed: the lesson player resolves this account's
                // enrolled student from the learn payload (data.student_id).
                <Link to={`/academy/learn/${data.slug}/${data.units[0].lessons[0].slug}`}
                  className="btn-copper inline-flex items-center gap-2 text-sm" data-testid="course-open">
                  Open course and start lesson 1 <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>

            {/* Objectives sidebar */}
            <aside className="space-y-4">
              <div className="card-flat bg-white border border-ink/10 p-6">
                <h3 className="font-heading text-lg font-bold text-ink flex items-center gap-2 mb-3"><Target className="w-5 h-5 text-copper" /> What your student will learn</h3>
                <ul className="space-y-2.5">
                  {data.objectives.map((o) => (
                    <li key={o} className="flex gap-2 text-sm text-ink/75 leading-relaxed">
                      <span className="text-copper font-black mt-0.5">✓</span> {o}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="card-flat bg-white border border-ink/10 p-6 text-sm text-ink/60 leading-relaxed">
                <strong className="text-ink">How mastery works here:</strong> read the lesson, then take the
                knowledge check. Score {data.passing_score}% or higher and the lesson counts as complete and the
                next one unlocks. Below {data.passing_score}%? Review the explanations and try again — progress
                and best scores are saved for your parent dashboard.
              </div>
            </aside>
          </div>
        )}
      </section>
      <AcademyFooter />
    </div>
  );
}
