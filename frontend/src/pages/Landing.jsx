import { Link } from "react-router-dom";
import { Zap, ShieldCheck, BookOpen, Sun, Award, Wrench, ArrowRight } from "lucide-react";

const HERO = "https://static.prod-images.emergentagent.com/jobs/bb805589-57e1-4a69-a20a-634e662786be/images/d54fa6bbf1da1d71103863bd3913c37f5be9ce27915ab3d46073050a7ae47b90.png";
const LAB = "https://static.prod-images.emergentagent.com/jobs/bb805589-57e1-4a69-a20a-634e662786be/images/400ae5d82048afd5dbdcd20dc360b9e2cb437b23f2460b0009bbb0a0f6875b7c.png";
const SOLAR = "https://images.pexels.com/photos/9875448/pexels-photo-9875448.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940";

export default function Landing() {
  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Top bar */}
      <header className="border-b border-ink/10 bg-bone">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid="landing-logo">
            <div className="w-10 h-10 bg-ink flex items-center justify-center">
              <Zap className="w-5 h-5 text-signal" strokeWidth={3} />
            </div>
            <div>
              <div className="overline text-copper leading-none">LCE-WAI</div>
              <div className="font-heading font-bold text-sm leading-tight">Lightning City Electric</div>
            </div>
          </Link>
          <nav className="flex items-center gap-6">
            <a href="#program" className="text-sm font-medium hover:text-copper" data-testid="link-program">Program</a>
            <a href="#curriculum" className="text-sm font-medium hover:text-copper" data-testid="link-curriculum">Curriculum</a>
            <a href="#values" className="text-sm font-medium hover:text-copper" data-testid="link-values">Values</a>
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
              Lightning City Electric Workforce & Apprenticeship Institute prepares youth, adults, and returning citizens for careers in electrical work through hands-on curriculum, faith-forward mentorship, and the 12-project Camper-to-Classroom build.
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

      {/* Pillars */}
      <section id="values" className="border-y border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-20 grid md:grid-cols-4 gap-8">
          {[
            { icon: ShieldCheck, t: "Safety First", d: "NFPA 70E compliant PPE, LOTO, and arc-flash training from day one." },
            { icon: Wrench, t: "Hands-On", d: "Every module ends at a tool pouch, not a slideshow. Skills demonstrations mandatory." },
            { icon: Sun, t: "Solar & Off-Grid", d: "Design and commission 48V solar systems on the mobile classroom itself." },
            { icon: Award, t: "Certifications", d: "Stackable, printable certificates aligned to apprenticeship competencies." },
          ].map((p, i) => (
            <div key={i} className="card-flat p-8" data-testid={`pillar-${i}`}>
              <div className="w-12 h-12 bg-ink text-signal flex items-center justify-center mb-5">
                <p.icon className="w-6 h-6" strokeWidth={2.5} />
              </div>
              <div className="font-heading text-xl font-bold">{p.t}</div>
              <div className="text-sm text-ink/70 mt-2 leading-relaxed">{p.d}</div>
            </div>
          ))}
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
                <div key={i} className="card-flat p-5 flex items-center justify-between group" data-testid={`module-preview-${i}`}>
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
            <div className="w-8 h-8 bg-ink flex items-center justify-center">
              <Zap className="w-4 h-4 text-signal" strokeWidth={3} />
            </div>
            <span className="font-heading font-bold">Lightning City Electric Workforce & Apprenticeship Institute</span>
          </div>
          <div className="text-xs text-ink/60 italic">"Whatever you do, work at it with all your heart." — Colossians 3:23</div>
        </div>
      </footer>
    </div>
  );
}
