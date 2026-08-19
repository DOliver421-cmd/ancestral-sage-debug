import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { BookOpen, Settings, Sparkles, Award, Users, LogIn, UserPlus, ArrowRight } from "lucide-react";

const PORTALS = [
  {
    icon: BookOpen,
    label: "Classrooms",
    desc: "Curriculum, modules, labs, and skill demonstrations. The Camper-to-Classroom program.",
    to: "/login",
    cta: "Enter Classrooms",
    color: "border-copper",
    accent: "text-copper",
  },
  {
    icon: Settings,
    label: "Administration",
    desc: "Instructor roster, attendance, compliance, incident reports, and program management.",
    to: "/login",
    cta: "Administration Portal",
    color: "border-ink",
    accent: "text-ink",
  },
  {
    icon: Sparkles,
    label: "AI Tutor",
    desc: "The on-demand learning guide. Powered by the M.O.R.E. gateway — always free, always available.",
    to: "/login",
    cta: "Open AI Tutor",
    color: "border-signal",
    accent: "text-signal",
  },
  {
    icon: Award,
    label: "Credentials",
    desc: "Certificates earned, competencies verified, and portfolio evidence of your trade skills.",
    to: "/login",
    cta: "View Credentials",
    color: "border-amber-500",
    accent: "text-amber-600",
  },
];

export default function WAIInstitute() {
  return (
    <div className="min-h-screen bg-bone">
      {/* Header */}
      <header className="bg-ink text-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <Link to="https://www.morehelp.center" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-10 h-10 object-contain" />
            <div>
              <div className="text-[10px] font-black uppercase tracking-widest text-signal">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <div className="flex items-center gap-3">
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
      <section className="bg-ink text-white pb-16 pt-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="overline text-signal mb-3">WAI Institute · NAM Oshun Edutainment LLC</div>
          <h1 className="font-heading text-5xl font-bold leading-tight max-w-3xl">
            Electrical Education & Media Strategy
          </h1>
          <p className="text-white/60 mt-4 max-w-2xl text-lg leading-relaxed">
            Trade training that pays, credentials that verify, and media skills that move the
            message — focused, professional, and built to survive the storm.
          </p>
          <div className="flex items-center gap-4 mt-8">
            <Link to="/register" className="inline-flex items-center gap-2 px-6 py-3 bg-signal text-ink font-bold hover:bg-signal/80 transition-colors">
              Enroll Now <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/login" className="inline-flex items-center gap-2 px-6 py-3 border border-white/30 text-white font-bold hover:bg-white/10 transition-colors">
              <LogIn className="w-4 h-4" /> Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Portals */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="overline text-copper mb-2">Access Your Portal</div>
        <h2 className="font-heading text-3xl font-bold text-ink mb-10">Where do you need to go?</h2>
        <div className="grid md:grid-cols-2 gap-5">
          {PORTALS.map((p) => {
            const Icon = p.icon;
            return (
              <Link key={p.label} to={p.to}
                className={`card-flat p-8 flex gap-6 items-start group border-l-4 hover:shadow-lg transition-all ${p.color}`}>
                <div className={`mt-1 ${p.accent}`}>
                  <Icon className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <div className={`font-heading text-xl font-bold ${p.accent}`}>{p.label}</div>
                  <p className="text-ink/70 mt-2 text-sm leading-relaxed">{p.desc}</p>
                  <div className={`mt-4 text-sm font-bold uppercase tracking-widest flex items-center gap-1 ${p.accent} group-hover:gap-2 transition-all`}>
                    {p.cta} <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Support — everything outside the classroom lives on M.O.R.E. */}
      <section className="border-t border-ink/10 bg-bone py-12">
        <div className="max-w-6xl mx-auto px-6">
          <div className="overline text-copper mb-3">Help, billing & the creative community</div>
          <h2 className="font-heading text-2xl font-bold text-ink mb-6">Everything else lives at the M.O.R.E. Help Center</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { title: "Help & Support", desc: "Tickets, troubleshooting, LMS guides, and the knowledge base.", href: "https://www.morehelp.center/help-center", cta: "Get Help" },
              { title: "Billing & Account", desc: "Subscriptions, payment history, refunds, and account recovery.", href: "https://www.morehelp.center/plans", cta: "Manage Billing" },
              { title: "M.O.R.E. Creators & Pantheon", desc: "The creative suite, community chat, and the M.O.R.E. Pantheon.", href: "https://www.morehelp.center/creators", cta: "Explore Creators" },
            ].map((c) => (
              <a key={c.title} href={c.href} target="_blank" rel="noopener noreferrer"
                className="card-flat p-6 border border-ink/10 bg-white hover:border-copper transition-all group">
                <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">{c.title}</div>
                <p className="text-sm text-ink/60 mt-2 leading-relaxed">{c.desc}</p>
                <div className="mt-4 text-sm font-bold uppercase tracking-widest text-copper flex items-center gap-1 group-hover:gap-2 transition-all">
                  {c.cta} <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Community link */}
      <section className="border-t border-ink/10 bg-white py-12">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <Users className="w-8 h-8 text-copper" />
            <div>
              <div className="font-heading font-bold text-ink">Part of the M.O.R.E. Community</div>
              <div className="text-sm text-ink/60">M.O.R.E. Help Center connects people to skills, support, and community care — free and open to all.</div>
            </div>
          </div>
          <a href="https://www.morehelp.center" className="btn-copper inline-flex items-center gap-2 whitespace-nowrap">
            Visit M.O.R.E. Hub <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      <footer className="bg-ink text-white/40 text-xs text-center py-6">
        © {new Date().getFullYear()} {BRAND.name} · A division of {BRAND.legal} · <a href="https://www.morehelp.center" className="hover:text-white">www.morehelp.center</a>
      </footer>
    </div>
  );
}
