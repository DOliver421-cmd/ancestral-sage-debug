import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { ArrowRight, Heart, CheckCircle } from "lucide-react";
import BugReportModal from "../components/BugReportModal";

const ROLES = [
  {
    icon: "🎵",
    title: "Music & Arts Marketing",
    dept: "Music Industry Pipeline",
    desc: "Support music creators on the platform — course promotion, social media, community outreach, A&R awareness campaigns. Work directly with music educators and artists.",
    skills: ["Social media", "Music industry knowledge", "Content writing"],
    commitment: "10–15 hrs/week · Remote",
  },
  {
    icon: "📱",
    title: "Content Creation & Social Media",
    dept: "Community Outreach",
    desc: "Create content that reflects the real community we're building. Short-form video, graphics, copywriting, platform posts. Bring the culture — don't sanitize it.",
    skills: ["Video editing", "Graphic design", "Cultural awareness"],
    commitment: "8–12 hrs/week · Remote",
  },
  {
    icon: "🤝",
    title: "M.O.R.E. Program Coordination",
    dept: "M.O.R.E. Help Center",
    desc: "Help moderate and grow the M.O.R.E. Help Center. Connect community members with resources. Work alongside Oliver Guardian to facilitate skill exchanges and needs.",
    skills: ["Community organizing", "Communication", "Empathy"],
    commitment: "10–15 hrs/week · Remote",
  },
  {
    icon: "💻",
    title: "Platform Development",
    dept: "Engineering",
    desc: "Build features that serve the community — frontend React development, Python backend work, MongoDB data modeling. Real production code. Real impact.",
    skills: ["React", "Python/FastAPI", "MongoDB"],
    commitment: "15–20 hrs/week · Remote",
  },
  {
    icon: "📊",
    title: "Community Research & Grants",
    dept: "Executive",
    desc: "Research grant opportunities, write applications, document community impact. Help us build the evidence base for funding the work that's already happening.",
    skills: ["Writing", "Research", "Grant writing basics"],
    commitment: "8–12 hrs/week · Remote",
  },
  {
    icon: "🎓",
    title: "Creator Success & Onboarding",
    dept: "Creator Support",
    desc: "Help new creators get their courses and profiles live. Tutorial creation, 1-on-1 walkthroughs, community welcome. You're the first face creators see.",
    skills: ["Teaching", "Patience", "Platform familiarity"],
    commitment: "10–15 hrs/week · Remote",
  },
];

const WHY = [
  { icon: "✊", title: "Real Work", body: "Not coffee runs. Not busy work. You'll do work that goes live and impacts real community members." },
  { icon: "🧠", title: "Real Mentorship", body: "Direct access to the Executive Director and founding team. We invest in the people who invest in the community." },
  { icon: "📜", title: "Academic Credit", body: "We'll work with your institution to provide documentation for academic credit where eligible." },
  { icon: "🌱", title: "Path to Employment", body: "Exceptional interns will be considered first for paid positions as the platform grows." },
];

export default function Internships() {
  return (
    <div className="min-h-screen bg-bone text-ink">

      {/* Nav */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-10 h-10 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="overline text-copper leading-none text-xs">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm">{BRAND.name}</div>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/more" className="flex items-center gap-1.5 text-xs font-bold text-amber-600 border border-amber-300 px-3 py-1.5 rounded-full">
              <Heart className="w-3 h-3" /> M.O.R.E.
            </Link>
            <Link to="/register" className="text-xs font-bold bg-ink text-white px-4 py-1.5 rounded-full hover:bg-ink/80 transition-colors">Join Free</Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-ink via-ink/95 to-ink/90 text-white py-24">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-amber-400 text-xs uppercase tracking-widest font-bold mb-4">Grow With Us</p>
          <h1 className="font-heading text-5xl sm:text-6xl font-extrabold mb-6 leading-tight">
            Internships at<br />WAI-Institute
          </h1>
          <p className="text-xl text-white/75 leading-relaxed mb-8 max-w-2xl mx-auto">
            Community-based internships for people who want to do real work that matters.
            We're building a platform for Black creators, artists, musicians, and community members — and we need people who actually care about that mission.
          </p>
          <a
            href="mailto:poetgames@gmail.com"
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-4 rounded-xl transition-all hover:scale-105 text-lg"
          >
            Apply Now <ArrowRight className="w-5 h-5" />
          </a>
          <p className="text-white/40 text-xs mt-4">Email poetgames@gmail.com with your name, role interest, and a sentence about why this matters to you.</p>
        </div>
      </section>

      {/* Why intern here */}
      <section className="py-16 bg-amber-50 border-b border-amber-200">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="font-heading text-3xl font-extrabold text-center mb-10">Why intern here?</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {WHY.map(({ icon, title, body }) => (
              <div key={title} className="text-center">
                <div className="text-4xl mb-3">{icon}</div>
                <h3 className="font-bold text-base mb-2">{title}</h3>
                <p className="text-ink/60 text-sm leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open roles */}
      <section className="py-20 bg-bone">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="font-heading text-4xl font-extrabold mb-3">Open Roles</h2>
          <p className="text-ink/60 mb-12 text-base">All roles are remote. We prioritize BIPOC applicants and people with lived community experience.</p>
          <div className="grid md:grid-cols-2 gap-6">
            {ROLES.map((role) => (
              <div key={role.title} className="bg-white border border-ink/10 rounded-2xl p-7 hover:shadow-md transition-shadow">
                <div className="flex items-start gap-4 mb-4">
                  <div className="text-3xl">{role.icon}</div>
                  <div>
                    <div className="text-xs font-bold text-copper uppercase tracking-wider mb-0.5">{role.dept}</div>
                    <h3 className="font-heading font-extrabold text-lg leading-tight">{role.title}</h3>
                  </div>
                </div>
                <p className="text-ink/65 text-sm leading-relaxed mb-4">{role.desc}</p>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {role.skills.map((s) => (
                    <span key={s} className="text-xs px-2.5 py-1 bg-copper/10 text-copper rounded-full font-medium">{s}</span>
                  ))}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-ink/45 font-medium">{role.commitment}</span>
                  <a
                    href={`mailto:poetgames@gmail.com?subject=Internship Application: ${role.title}`}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-ink hover:text-copper transition-colors"
                  >
                    Apply <ArrowRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Who we're looking for */}
      <section className="py-16 bg-ink text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="font-heading text-4xl font-extrabold mb-6">Who we're looking for</h2>
          <div className="space-y-3 text-left max-w-xl mx-auto mb-8">
            {[
              "You care about Black communities and BIPOC creators — not just as a résumé line",
              "You want to learn how a real platform gets built by real people with limited resources",
              "You bring your whole self — not a sanitized, corporate-filtered version",
              "You understand that community work is also creative work, technical work, and political work",
              "You're ok with being a beginner and saying so",
            ].map((item) => (
              <div key={item} className="flex items-start gap-3 text-sm text-white/75">
                <CheckCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <a
            href="mailto:poetgames@gmail.com"
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-4 rounded-xl transition-all hover:scale-105"
          >
            Send us an email <ArrowRight className="w-5 h-5" />
          </a>
          <p className="text-white/40 text-xs mt-4">poetgames@gmail.com — introduce yourself in 3 sentences or less.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink/10 bg-bone py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-ink/50">
          <span>{BRAND.name}</span>
          <div className="flex items-center gap-4">
            <Link to="/" className="hover:text-ink transition-colors">Home</Link>
            <Link to="/more" className="hover:text-ink transition-colors">M.O.R.E.</Link>
            <Link to="/register" className="hover:text-ink transition-colors">Join</Link>
          </div>
        </div>
      </footer>

      <BugReportModal />
    </div>
  );
}
