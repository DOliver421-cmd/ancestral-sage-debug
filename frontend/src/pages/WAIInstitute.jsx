import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND, WAI_INSTITUTE_URL } from "../lib/brand";
import {
  BookOpen, Bot, Compass, Library, GraduationCap, FlaskConical, MonitorSmartphone,
  Rocket, ArrowRight, HelpCircle, User, Wrench, Globe, LogIn, UserPlus, ExternalLink,
} from "lucide-react";

const WAI_PROGRAMS_URL = `${WAI_INSTITUTE_URL}/programs`;
const WAI_ACADEMY_URL = WAI_INSTITUTE_URL; // The full academy lives on wai-institute.org.

/**
 * /wai-institute — WAI Institute Homeschool Academy gateway.
 *
 * Journey: M.O.R.E. Help Center → Homeschool Academy gateway → wai-institute.org
 *
 * Rule honored here: every button links to something that actually exists —
 * live MHC routes (/courses, /ai, /finder, /register) or the real WAI site.
 * Nothing here pretends an unfinished feature is live.
 */
export default function WAIInstitute() {
  return (
    <div className="min-h-screen bg-bone">
      {/* Header */}
      <header className="bg-ink text-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-10 h-10 object-contain" />
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <div className="flex flex-wrap items-center gap-4">
            <Link to="/help-center" className="flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors">
              <HelpCircle className="w-4 h-4" /> Help & Support
            </Link>
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors">
              <Globe className="w-4 h-4" /> WAIInstitute.org
            </a>
            <Link to="/login" className="flex items-center gap-2 text-sm font-bold text-white/70 hover:text-white transition-colors">
              <LogIn className="w-4 h-4" /> Sign In
            </Link>
            <Link to="/register" className="flex items-center gap-2 px-4 py-2 bg-signal text-ink text-sm font-bold hover:bg-signal/80 transition-colors">
              <UserPlus className="w-4 h-4" /> Enroll
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-ink text-white pb-16 pt-12">
        <div className="max-w-6xl mx-auto px-6">
          <div className="overline text-signal mb-3">WAI Institute · Homeschool Academy</div>
          <h1 className="font-heading text-5xl font-bold leading-tight max-w-3xl">
            Learning. Building. Creating. Preparing for the Future.
          </h1>
          <p className="text-white/60 mt-4 max-w-2xl text-lg leading-relaxed">
            A flexible learning environment for homeschool families, students, and independent
            learners — with courses, projects, AI-assisted learning, career exploration, and
            practical skills.
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-8">
            <Link to="/courses" className="inline-flex items-center gap-2 px-6 py-3 bg-signal text-ink font-bold hover:bg-signal/80 transition-colors">
              Explore Homeschool Academy <ArrowRight className="w-4 h-4" />
            </Link>
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-6 py-3 border border-white/30 text-white font-bold hover:bg-white/10 transition-colors">
              Visit WAI Institute <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          <p className="text-white/40 text-sm mt-6 max-w-2xl">
            Your journey can begin here at M.O.R.E. Help Center. When you're ready for the full
            WAI Institute experience, continue to{" "}
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer" className="underline hover:text-white/70">wai-institute.org</a>.
          </p>
        </div>
      </section>

      {/* Section 1 — Start Here */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="overline text-copper mb-2">Start Here</div>
        <h2 className="font-heading text-3xl font-bold text-ink mb-10">Where do you want to begin?</h2>
        <div className="grid md:grid-cols-2 gap-5">
          <StartCard
            icon={GraduationCap}
            title="Homeschool Academy"
            desc="Structured learning for homeschool students — courses, lessons, projects, activities, and learning pathways designed to support independent and family-directed education."
            to="/courses"
            cta="Enter Homeschool"
            accent="text-copper"
            border="border-copper"
          />
          <StartCard
            icon={Bot}
            title="AI Learning Assistant"
            desc="Get help when you get stuck. Use AI assistance to explain concepts, brainstorm ideas, practice skills, and help you move forward."
            to="/ai"
            cta="Meet Your AI Tutor"
            accent="text-signal"
            border="border-signal"
          />
          <StartCard
            icon={Compass}
            title="Career & Skills"
            desc="Discover what comes next — explore technology, trades, entrepreneurship, creative work, and other practical pathways."
            to="/ai"
            cta="Explore Pathways"
            accent="text-amber-600"
            border="border-amber-500"
          />
          <StartCard
            icon={Library}
            title="Learning Resources"
            desc="Build your own learning library — books, guides, educational resources, and additional materials to support independent learning."
            to="/finder"
            cta="Explore Resources"
            accent="text-copper"
            border="border-copper"
          />
        </div>
      </section>

      {/* Section 2 — The Academy, the star */}
      <section className="bg-white border-y border-ink/10 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="overline text-copper mb-2">The WAI Institute Homeschool Academy</div>
          <h2 className="font-heading text-3xl font-bold text-ink">More than lessons. A pathway.</h2>
          <p className="text-ink/60 mt-3 max-w-2xl leading-relaxed">
            The Academy is a learning ecosystem — not just another course list. Four pillars carry
            a student from first lesson to real-world readiness.
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 mt-10">
            {[
              { icon: BookOpen, title: "Academics", desc: "Core subjects, structured courses, lessons and assessments." },
              { icon: FlaskConical, title: "Projects", desc: "Hands-on learning that connects knowledge to real-world problems." },
              { icon: MonitorSmartphone, title: "Technology & AI", desc: "Digital literacy, AI-assisted learning, coding and technology exploration." },
              { icon: Rocket, title: "Career & Entrepreneurship", desc: "Practical skills, trades, creative careers and entrepreneurship." },
            ].map((p) => {
              const Icon = p.icon;
              return (
                <div key={p.title} className="card-flat p-6 border-t-4 border-copper">
                  <Icon className="w-8 h-8 text-copper mb-3" />
                  <div className="font-heading text-lg font-bold text-ink">{p.title}</div>
                  <p className="text-sm text-ink/60 mt-2 leading-relaxed">{p.desc}</p>
                </div>
              );
            })}
          </div>
          <div className="mt-10 text-center">
            <p className="text-ink/60 mb-4">Your learning doesn't have to stop at the classroom.</p>
            <a href={WAI_ACADEMY_URL} target="_blank" rel="noopener noreferrer"
              className="btn-copper inline-flex items-center gap-2">
              Explore the Academy at WAI Institute <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Section 3 — Why WAI Institute */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="overline text-copper mb-2">Why WAI Institute?</div>
        <h2 className="font-heading text-3xl font-bold text-ink">Ready to Go Further?</h2>
        <div className="grid md:grid-cols-2 gap-8 mt-8 items-start">
          <div className="card-flat p-8">
            <div className="overline text-signal mb-2">You are here</div>
            <div className="font-heading text-2xl font-bold text-ink">M.O.R.E. Help Center</div>
            <p className="text-ink/60 mt-3 leading-relaxed">
              Your starting point — free help, courses, AI tutoring, and resources to get moving today.
            </p>
          </div>
          <div className="card-flat p-8 border-l-4 border-copper">
            <div className="overline text-copper mb-2">The next step</div>
            <div className="font-heading text-2xl font-bold text-ink">WAI Institute</div>
            <p className="text-ink/60 mt-3 leading-relaxed">
              Where the larger learning experience continues — structured programs, specialized
              courses, creative opportunities, technology, career pathways, and additional Academy
              experiences.
            </p>
            <a href={WAI_INSTITUTE_URL} target="_blank" rel="noopener noreferrer"
              className="btn-copper inline-flex items-center gap-2 mt-6">
              Go to WAI Institute <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* Section 4 — M.O.R.E. Help loop */}
      <section className="border-t border-ink/10 bg-white py-12">
        <div className="max-w-6xl mx-auto px-6">
          <div className="overline text-copper mb-3">The M.O.R.E. Help Center — your home base</div>
          <h2 className="font-heading text-2xl font-bold text-ink mb-2">Need Help Along the Way?</h2>
          <p className="text-ink/60 max-w-2xl mb-8 leading-relaxed">
            The loop: start here, learn at the Academy, go further at WAI Institute — and M.O.R.E.
            Help Center remains your home base the whole way.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: HelpCircle, title: "Help & Support", desc: "Get answers and assistance when you need it.", to: "/help-center" },
              { icon: User, title: "Your Account", desc: "Manage your MoreHelp account and access.", to: "/profile" },
              { icon: Wrench, title: "M.O.R.E. Resources", desc: "Explore additional tools, resources and services.", to: "/finder" },
            ].map((c) => {
              const Icon = c.icon;
              return (
                <Link key={c.title} to={c.to}
                  className="card-flat p-6 border border-ink/10 bg-white hover:border-copper transition-all group">
                  <Icon className="w-7 h-7 text-copper mb-3" />
                  <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">{c.title}</div>
                  <p className="text-sm text-ink/60 mt-2 leading-relaxed">{c.desc}</p>
                  <div className="mt-4 text-sm font-bold uppercase tracking-widest text-copper flex items-center gap-1 group-hover:gap-2 transition-all">
                    Open <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </Link>
              );
            })}
          </div>
          <div className="mt-10 text-center">
            <Link to="/" className="btn-copper inline-flex items-center gap-2">
              Return to M.O.R.E. Help Center <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="bg-ink text-white/40 text-xs text-center py-6">
        © {new Date().getFullYear()} {BRAND.name} · A division of {BRAND.legal} ·{" "}
        <a href="https://www.morehelp.center" className="hover:text-white">www.morehelp.center</a>
      </footer>
    </div>
  );
}

function StartCard({ icon: Icon, title, desc, to, cta, accent, border }) {
  return (
    <Link to={to}
      className={`card-flat p-8 flex gap-6 items-start group border-l-4 hover:shadow-lg transition-all ${border}`}>
      <div className={`mt-1 ${accent}`}><Icon className="w-8 h-8" /></div>
      <div className="flex-1">
        <div className={`font-heading text-xl font-bold ${accent}`}>{title}</div>
        <p className="text-ink/70 mt-2 text-sm leading-relaxed">{desc}</p>
        <div className={`mt-4 text-sm font-bold uppercase tracking-widest flex items-center gap-1 ${accent} group-hover:gap-2 transition-all`}>
          {cta} <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </Link>
  );
}
