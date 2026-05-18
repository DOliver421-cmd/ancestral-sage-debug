import { Link } from "react-router-dom";
import { WAI_LOGO, BRAND } from "../lib/brand";
import { ShieldCheck, BookOpen, Sun, Award, Wrench, ArrowRight, HelpCircle, HandHelping, Scale, MessageSquare } from "lucide-react";

const HERO = "https://placehold.co/1200x600/0A1628/C9A84C?text=WAI+Institute";
const LAB = "https://placehold.co/800x500/0A1628/C9A84C?text=Apprentice+Labs";
const SOLAR = "https://images.pexels.com/photos/9875448/pexels-photo-9875448.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

export default function Landing() {
  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Top bar */}
      <header className="border-b border-ink/10 bg-bone">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid="landing-logo">
            <img src={WAI_LOGO} alt="W.A.I." className="w-12 h-12 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="overline text-copper leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-sm leading-tight">{BRAND.name}</div>
            </div>
          </Link>
          <nav className="flex items-center gap-5">
            <a href="#program" className="text-sm font-medium hover:text-copper" data-testid="link-program">Program</a>
            <a href="#curriculum" className="text-sm font-medium hover:text-copper" data-testid="link-curriculum">Curriculum</a>
            <a href="#values" className="text-sm font-medium hover:text-copper" data-testid="link-values">Values</a>
            <Link to="/helper" className="flex items-center gap-1.5 text-sm font-medium hover:text-copper" data-testid="link-helper">
              <HelpCircle className="w-4 h-4" /> Help Center
            </Link>
            {/* M.O.R.E. — prominent nav button */}
            <Link
              to="/more"
              className="flex items-center gap-2 px-4 py-2 font-bold text-sm uppercase tracking-widest text-ink border-2 border-copper hover:bg-copper transition-colors"
              data-testid="link-more-nav"
            >
              <HandHelping className="w-4 h-4" /> M.O.R.E.
            </Link>
            <Link to="/login" className="text-sm font-bold uppercase tracking-widest" data-testid="link-login">Sign in</Link>
            <Link to="/register" className="btn-copper text-sm" data-testid="btn-enroll">Enroll</Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-paper opacity-40 pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 pt-20 pb-24 grid lg:grid-cols-12 gap-12 items-center relative">
          <div className="lg:col-span-7">
            <div className="flex items-center gap-3 mb-8">
              <span className="badge-signal" data-testid="badge-accredited">Workforce Accreditation Pathway</span>
              <span className="overline text-copper">Est. 2026</span>
            </div>
            <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[0.95] tracking-tight">
              Train Electricians.<br />
              <span className="text-copper">Build Lives.</span><br />
              Power Cities.
            </h1>
            <p className="mt-8 text-lg text-ink/70 max-w-xl leading-relaxed">
              W.A.I. — Workforce Apprentice Institute, in partnership with LCE-WAI — prepares youth, adults, and returning citizens for careers in electrical work through hands-on curriculum, faith-forward mentorship, and the 12-project Camper-to-Classroom build.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Link to="/register" className="btn-primary inline-flex items-center gap-2" data-testid="btn-cta-start">
                Start Training <ArrowRight className="w-4 h-4" />
              </Link>
              <Link to="/login" className="btn-ghost" data-testid="btn-cta-login">Instructor Sign In</Link>
            </div>
            <div className="mt-14 grid grid-cols-3 gap-8 max-w-md">
              <div>
                <div className="font-heading text-4xl font-black text-ink">12</div>
                <div className="overline text-ink/60 mt-1">Build Projects</div>
              </div>
              <div>
                <div className="font-heading text-4xl font-black text-ink">132</div>
                <div className="overline text-ink/60 mt-1">Training Hours</div>
              </div>
              <div>
                <div className="font-heading text-4xl font-black text-ink">3</div>
                <div className="overline text-ink/60 mt-1">Career Tracks</div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="relative">
              <div className="absolute -inset-0.5 bg-copper -rotate-1"></div>
              <img src={HERO} alt="Electrical apprentices working on a residential panel" className="relative w-full h-[520px] object-cover" data-testid="hero-image" />
              <div className="absolute bottom-6 left-6 right-6 bg-ink text-white p-6 border border-signal">
                <div className="overline text-signal">Current Associate</div>
                <div className="font-heading text-xl font-bold mt-1">Camper-to-Classroom: Mobile Off-Grid Build</div>
                <div className="text-sm text-white/70 mt-2">12 apprentices wiring a fully off-grid 48V solar mobile classroom from bare studs to commissioned system.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ───── M.O.R.E. HELP CENTER — full-width, first thing after hero ───── */}
      <section id="more" className="bg-copper text-ink" data-testid="section-more">
        <div className="max-w-7xl mx-auto px-6 py-20">
          {/* Heading block */}
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 bg-ink text-white text-xs font-bold uppercase tracking-widest px-4 py-2 mb-6">
              <HandHelping className="w-4 h-4" /> Free · Community · No Account Needed to Start
            </div>
            <h2 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[0.95] tracking-tight">
              M.O.R.E. Help Center
            </h2>
            <p className="mt-4 font-heading text-xl font-bold">Michael Oliver Resource Exchange</p>
            <p className="mt-5 text-ink/80 text-lg max-w-2xl mx-auto leading-relaxed">
              Trade skills, time, and support. Ask for help. Know your rights. Everything your community needs — free, safe, and judgment-free.
            </p>
            <div className="mt-8">
              <Link
                to="/more"
                className="inline-flex items-center gap-3 bg-ink text-white font-bold text-xl uppercase tracking-widest px-12 py-6 hover:bg-ink/80 transition-colors"
                data-testid="btn-more-main"
              >
                <HandHelping className="w-6 h-6" />
                Open M.O.R.E. Help Center
                <ArrowRight className="w-6 h-6" />
              </Link>
            </div>
          </div>

          {/* Feature cards — each links directly to its destination */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            {[
              { icon: HandHelping, title: "Community Exchange", desc: "Offer skills, ask for help, share stories. Neighbors helping neighbors — no money, no exploitation.", tag: "Free · AI-Moderated", to: "/more" },
              { icon: MessageSquare, title: "Safe Community Chat", desc: "60-minute privacy rooms for real conversations. Auto-purge means no permanent record.", tag: "Auto-Purge · Private", to: "/more" },
              { icon: Scale, title: "Legal Aid Tool", desc: "Universal Litigation Weapon — EEOC filings, federal court docs, damages calculator, evidence checklist.", tag: "Built-In · Free", to: "/more/litigation" },
              { icon: HelpCircle, title: "Personal Help Center", desc: "Plain-language help with letters, bills, eviction notices, medical bills, employment rights.", tag: "No Forms · Instant", to: "/helper" },
            ].map(f => (
              <Link key={f.title} to={f.to} className="bg-ink text-white p-6 flex flex-col gap-3 hover:bg-ink/80 transition-colors group">
                <div className="w-10 h-10 bg-copper flex items-center justify-center shrink-0">
                  <f.icon className="w-5 h-5 text-ink" />
                </div>
                <div>
                  <div className="font-heading font-bold text-lg">{f.title}</div>
                  <div className="text-xs text-signal font-bold uppercase tracking-widest mt-1">{f.tag}</div>
                </div>
                <p className="text-white/70 text-sm leading-relaxed flex-1">{f.desc}</p>
                <div className="flex items-center gap-1 text-copper text-xs font-bold mt-auto pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  Open <ArrowRight className="w-3 h-3" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Pillars */}
      <section id="values" className="border-y border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-20 grid md:grid-cols-4 gap-8">
          {[
            { icon: ShieldCheck, t: "Safety First", d: "NFPA 70E compliant PPE, LOTO, and arc-flash training from day one." },
            { icon: Wrench, t: "Hands-On", d: "Every module ends at a tool pouch, not a slideshow. Skills demonstrations mandatory." },
            { icon: Sun, t: "Solar & Off-Grid", d: "Design and commission 48V solar systems on the mobile classroom itself." },
            { icon: Award, t: "Certifications", d: "Stackable, printable certificates aligned to apprenticeship competencies." },
          ].map((p, i) => (
            <div key={p.t} className="card-flat p-8" data-testid={`pillar-${i}`}>
              <div className="w-12 h-12 bg-ink text-signal flex items-center justify-center mb-5">
                <p.icon className="w-6 h-6" strokeWidth={2.5} />
              </div>
              <div className="font-heading text-xl font-bold">{p.t}</div>
              <div className="text-sm text-ink/70 mt-2 leading-relaxed">{p.d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Help Center banner */}
      <section className="bg-ink text-white">
        <div className="max-w-7xl mx-auto px-6 py-14 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-start gap-5">
            <div className="w-14 h-14 shrink-0 flex items-center justify-center" style={{ background: "linear-gradient(135deg,#2563eb,#7c3aed)" }}>
              <HelpCircle className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="overline text-signal">Free · No Account Needed</div>
              <h2 className="font-heading text-2xl font-bold mt-1">Personal Help Center</h2>
              <p className="text-white/70 text-sm mt-2 max-w-xl leading-relaxed">
                Get plain-language help understanding letters, bills, legal notices, eviction paperwork, medical bills, employment rights, and more. Ask in your own words — no judgment, no forms, completely free.
              </p>
            </div>
          </div>
          <Link
            to="/helper"
            className="shrink-0 inline-flex items-center gap-2 px-7 py-3 font-bold text-sm uppercase tracking-widest text-ink transition-all"
            style={{ background: "linear-gradient(135deg,#2563eb,#7c3aed)", color: "#fff" }}
            data-testid="btn-help-center"
          >
            Open Help Center <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Curriculum preview */}
      <section id="curriculum" className="max-w-7xl mx-auto px-6 py-24">
        <div className="grid lg:grid-cols-12 gap-12">
          <div className="lg:col-span-5">
            <span className="badge-copper">The Curriculum</span>
            <h2 className="font-heading text-4xl lg:text-5xl font-bold mt-6 tracking-tight leading-tight">
              12 projects. One mobile classroom. A journeyman-ready apprentice.
            </h2>
            <p className="mt-6 text-ink/70 leading-relaxed">
              Each module pairs learning objectives, safety protocols, tool lists, step-by-step tasks, and a scripture tie-in. Apprentices document every build, pass a mastery quiz at 70%+, and earn hours toward their certificate.
            </p>
            <div className="mt-8">
              <img src={LAB} alt="Hands wiring a circuit" className="w-full h-64 object-cover hard-shadow-copper" />
            </div>
          </div>
          <div className="lg:col-span-7">
            <div className="grid sm:grid-cols-2 gap-4">
              {[
                "01 — Electrical Safety & LOTO",
                "02 — Tools & Apprentice Kit",
                "03 — DC Circuit Fundamentals",
                "04 — AC Circuit Fundamentals",
                "05 — Splices & Terminations",
                "06 — Switches & Receptacles",
                "07 — Subpanel & Load Calc",
                "08 — Conduit Bending",
                "09 — Grounding & Bonding",
                "10 — Off-Grid Solar Design",
                "11 — Battery & Inverter",
                "12 — Commissioning Capstone",
              ].map((m, i) => (
                <div key={m} className="card-flat p-5 flex items-center justify-between group" data-testid={`module-preview-${i}`}>
                  <div className="font-heading font-semibold text-ink">{m}</div>
                  <ArrowRight className="w-4 h-4 text-copper opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Program CTA */}
      <section id="program" className="bg-ink text-white">
        <div className="max-w-7xl mx-auto px-6 py-24 grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7">
            <span className="badge-signal">Who We Serve</span>
            <h2 className="font-heading text-4xl lg:text-5xl font-bold mt-6 leading-tight">
              Youth. Adults. Returning citizens. Anyone ready to work with their hands and build a life.
            </h2>
            <p className="mt-6 text-white/70 max-w-2xl leading-relaxed">
              Our mission is workforce development through the dignity of a skilled trade. We combine rigorous electrical training with faith-forward mentorship — because the work you do matters, and so do you.
            </p>
            <div className="mt-10 flex gap-4">
              <Link to="/register" className="btn-copper" data-testid="btn-bottom-enroll">Enroll Today</Link>
              <Link to="/login" className="btn-ghost border-white text-white hover:bg-white hover:text-ink" data-testid="btn-bottom-login">Sign In</Link>
            </div>
          </div>
          <div className="lg:col-span-5">
            <img src={SOLAR} alt="Technician installing solar panels" className="w-full h-80 object-cover grayscale hover:grayscale-0 transition-all duration-500" />
          </div>
        </div>
      </section>

      <footer className="bg-bone border-t border-ink/10">
        <div className="max-w-7xl mx-auto px-6 py-10 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span className="font-heading font-bold">W.A.I. — Workforce Apprentice Institute · LCE-WAI</span>
          </div>
          <div className="text-xs text-ink/60 italic">"Whatever you do, work at it with all your heart." — Colossians 3:23</div>
        </div>
      </footer>
    </div>
  );
}
