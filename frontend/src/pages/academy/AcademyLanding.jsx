import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { WAI_INSTITUTE_URL } from "../../lib/brand";
import { PublicHeader, AcademyFooter, TrackTag, LiveChip, TRACK_META } from "./academyKit";
import {
  ArrowRight, BookOpenCheck, ShieldCheck, FileText, Sparkles, Users,
  Target, ListChecks, ExternalLink, GraduationCap, Bot, Star, Award, Wrench, Palette,
} from "lucide-react";

/* The Academy gateway — rendered at /wai-institute (and aliased at /academy).
   Positioning: "WAI Homeschool Academy — Homeschool, done right." */

const STEPS = [
  { n: 1, icon: Users, title: "Create a parent account", desc: "One free account runs your whole homeschool — no per-child logins to babysit." },
  { n: 2, icon: GraduationCap, title: "Add a student, pick a track", desc: "Choose a grade (K–12) and a pathway — Foundations, Builder/Trade, Artist, or Scholar. We enroll the right courses." },
  { n: 3, icon: ListChecks, title: "Learn, master, and record", desc: "Lessons unlock as mastery is earned. Watch progress and print student records anytime." },
];

const FEATURES = [
  { icon: ShieldCheck, title: "Parent-managed", desc: "Student profiles live under your account. You choose the grade, the track, and the pace." },
  { icon: Target, title: "Mastery-based", desc: "Each lesson ends in a knowledge check. Score 80%+ and the next lesson unlocks; below it, review and try again." },
  { icon: BookOpenCheck, title: "Real academics", desc: "Sequenced ELA, Math, Science, and Social Studies — plus trade and creative pathways. Content you can actually read and learn from." },
  { icon: FileText, title: "Printable records", desc: "Progress documentation based on completed work: courses, lessons, mastery scores, and dates." },
];

const TRACK_CARDS = [
  { key: "foundations", icon: BookOpenCheck, desc: "K–8 core academics in English, Math, Science, and Social Studies.", status: "published" },
  { key: "builder", icon: Wrench, desc: "Trade-track math, science, and hands-on pathways — starting with Applied Electrical Engineering Year 1.", status: "published" },
  { key: "artist", icon: Palette, desc: "Visual, performing, and digital arts built with academic rigor.", status: "planned" },
  { key: "scholar", icon: Award, desc: "College-preparatory high school academics — starting with Scholar Biology (Grade 9).", status: "published" },
];

export default function AcademyLanding() {
  const [courses, setCourses] = useState([]);
  useEffect(() => {
    api.get("/academy/courses")
      .then((r) => setCourses((r.data?.courses || []).filter((c) => c.status === "published")))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-bone" data-testid="academy-landing">
      <PublicHeader current="home" />

      {/* Hero */}
      <section className="bg-ink text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07]" style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)", backgroundSize: "28px 28px" }} />
        <div className="relative max-w-7xl mx-auto px-6 pt-16 pb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-signal/40 bg-signal/10 text-signal text-xs font-black uppercase tracking-widest">
            <Star className="w-3.5 h-3.5" /> WAI Institute Homeschool Academy
          </div>
          <h1 className="font-heading text-5xl md:text-6xl font-black leading-[1.02] max-w-3xl mt-6">
            Homeschool, <span className="text-signal">done right.</span>
          </h1>
          <p className="text-white/70 text-xl leading-relaxed max-w-2xl mt-5">
            A sequenced K–12 and trade-track academy for families who want{" "}
            <span className="text-white font-semibold">real academics, real skills, and real credentials</span>{" "}
            — with full parental control.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-9">
            <Link to="/academy/parent" className="inline-flex items-center gap-2 px-7 py-3.5 bg-signal text-ink font-black hover:bg-signal/85 transition-all shadow-[4px_4px_0_rgba(255,255,255,0.15)] hover:translate-x-[-1px]" data-testid="academy-cta-start">
              Start Homeschooling Free <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/academy/curriculum" className="inline-flex items-center gap-2 px-7 py-3.5 border-2 border-white/30 text-white font-bold hover:bg-white/10 transition-colors" data-testid="academy-cta-curriculum">
              See the Curriculum
            </Link>
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-3 text-white/70 hover:text-white text-sm font-bold transition-colors">
              Visit WAI Institute <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-12 max-w-3xl">
            {["Parent-managed student profiles", "80% mastery to advance", "K–12 + trade tracks", "Printable student records"].map((t) => (
              <div key={t} className="flex items-center gap-2 text-white/80 text-xs font-bold bg-white/5 border border-white/10 rounded-lg px-3 py-2.5">
                <Sparkles className="w-3.5 h-3.5 text-signal shrink-0" /> {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="overline text-copper mb-2">How it works</div>
        <h2 className="font-heading text-3xl font-bold text-ink mb-8">Three steps to a working homeschool</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {STEPS.map((s) => {
            const Icon = s.icon;
            return (
              <div key={s.n} className="card-flat p-7 relative border-t-4 border-copper">
                <div className="absolute -top-4 left-6 w-9 h-9 rounded-full bg-ink text-signal flex items-center justify-center font-heading font-black">{s.n}</div>
                <Icon className="w-7 h-7 text-copper mt-4 mb-3" />
                <div className="font-heading text-lg font-bold text-ink">{s.title}</div>
                <p className="text-sm text-ink/60 mt-2 leading-relaxed">{s.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Tracks */}
      <section className="bg-white border-y border-ink/10 py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="overline text-copper mb-2">Pathways</div>
          <h2 className="font-heading text-3xl font-bold text-ink mb-3">Choose a track — or let your child explore</h2>
          <p className="text-ink/60 max-w-2xl mb-9">Every student gets core academics for their grade. Tracks add direction. We're building them all out — and we'll always tell you what's live versus in development.</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {TRACK_CARDS.map((t) => {
              const Icon = t.icon;
              const meta = TRACK_META[t.key];
              return (
                <div key={t.key} className="card-flat p-6 flex flex-col gap-3 hover:border-copper/60 hover:-translate-y-0.5 transition-all">
                  <div className="flex items-center justify-between">
                    <Icon className="w-7 h-7 text-copper" />
                    <LiveChip status={t.status} />
                  </div>
                  <div>
                    <div className="font-heading text-xl font-bold text-ink">{meta.name}</div>
                    <div className="text-xs font-black uppercase tracking-widest text-copper mt-0.5">{meta.grade}</div>
                  </div>
                  <p className="text-sm text-ink/60 leading-relaxed">{t.desc}</p>
                </div>
              );
            })}
          </div>
          <div className="mt-8 text-center">
            <Link to="/academy/curriculum" className="btn-copper inline-flex items-center gap-2">
              Explore the full curriculum <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-2 gap-5">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="card-flat p-7 flex gap-5 items-start">
                <div className="w-12 h-12 shrink-0 rounded-lg bg-ink/5 border border-ink/10 flex items-center justify-center text-copper"><Icon className="w-6 h-6" /></div>
                <div>
                  <div className="font-heading text-xl font-bold text-ink">{f.title}</div>
                  <p className="text-ink/60 mt-1.5 text-sm leading-relaxed">{f.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Live curriculum preview */}
      <section className="bg-ink text-white py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="overline text-signal mb-2">Available now — real courses, real lessons</div>
          <h2 className="font-heading text-3xl font-bold">Start learning today</h2>
          <p className="text-white/60 mt-2 max-w-2xl">Every course below is fully written: instructional material, examples, activities, and mastery checks. The rest of the catalog is being expanded — nothing here pretends to be done when it isn't.</p>
          {courses.length === 0 && (
            <p className="text-white/40 mt-6 text-sm">Loading the live catalog…</p>
          )}
          <div className="grid md:grid-cols-2 gap-5 mt-8">
            {courses.map((c) => (
              <Link key={c.slug} to={`/academy/courses/${c.slug}`} className="group bg-white/[0.04] border border-white/10 hover:border-signal/60 p-6 rounded-lg transition-all hover:-translate-y-0.5">
                <div className="flex flex-wrap items-center gap-2">
                  <TrackTag track={c.track} />
                  <span className="text-xs text-white/50 font-bold">{c.grade_label} · {c.subject_label}</span>
                </div>
                <div className="font-heading text-xl font-bold mt-3 group-hover:text-signal transition-colors">{c.title}</div>
                <p className="text-sm text-white/55 mt-2 leading-relaxed line-clamp-2">{c.summary}</p>
                <div className="flex items-center justify-between mt-4 text-xs font-bold text-white/45">
                  <span>{c.lesson_count} lessons · ~{c.est_hours} hrs</span>
                  <span className="flex items-center gap-1 text-signal group-hover:gap-2 transition-all">Open <ArrowRight className="w-3.5 h-3.5" /></span>
                </div>
              </Link>
            ))}
          </div>
          <div className="mt-8">
            <Link to="/academy/curriculum" className="inline-flex items-center gap-2 text-signal font-black uppercase tracking-widest text-sm hover:text-white transition-colors">
              Browse every course (including in development) <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* WAI Institute bridge */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-5 gap-8 items-center">
          <div className="md:col-span-3">
            <div className="overline text-copper mb-2">Ready to go further?</div>
            <h2 className="font-heading text-4xl font-bold text-ink leading-tight">WAI Institute — the next step beyond the Academy</h2>
            <p className="text-ink/60 mt-3 max-w-xl leading-relaxed">
              MoreHelp Center is your home base and this Academy is your structured start. When you're
              ready for the broader WAI Institute experience — its programs, community, and additional
              opportunities — continue at wai-institute.org. This Academy is separate from WAI Institute:
              your account and records here are managed by MoreHelp Center.
            </p>
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className="btn-copper inline-flex items-center gap-2 mt-6" data-testid="academy-cta-wai">
              Visit WAI Institute <ArrowRight className="w-4 h-4" />
            </a>
          </div>
          <div className="md:col-span-2 card-flat p-7">
            <Bot className="w-8 h-8 text-copper mb-3" />
            <div className="font-heading text-xl font-bold text-ink">Learning support is built in</div>
            <p className="text-sm text-ink/60 mt-2 leading-relaxed">
              Stuck on a concept? The lesson Coach connects to the same AI tutoring gateway as the
              MoreHelp AI Tutor — it explains, gives examples, and guides practice. It won't hand over
              answers to your mastery checks.
            </p>
            <Link to="/ai" className="mt-5 inline-flex items-center gap-2 text-copper font-black uppercase tracking-widest text-sm hover:text-ink transition-colors">
              Meet the AI Tutor <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <AcademyFooter />
    </div>
  );
}
