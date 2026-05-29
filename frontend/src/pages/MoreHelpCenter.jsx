import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Heart, BookOpen, MessageSquare, ArrowRight, Phone, Shield, Users, Globe, ShieldCheck, GraduationCap, Briefcase, Home as HomeIcon } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

const SUPPORT_EMAIL = "poetgames@gmail.com";
const GOLD = "#e8b83e";
const TEAL = "#0d7377";
const TEAL_DARK = "#095b5e";
const BG_WARM = "#f9f5f0";

const PUBLIC_CATEGORIES = [
  { icon: HomeIcon, title: "Community Resources", desc: "Find food, shelter, legal support, and direct mutual aid services.", to: "/more" },
  { icon: ShieldCheck, title: "Legal Support", desc: "Plain-language legal help, paperwork guidance, and advocacy resources.", to: "/more/litigation" },
  { icon: Briefcase, title: "Jobs & Training", desc: "Explore workforce-ready courses, internships, and skills pathways.", to: "/courses" },
  { icon: GraduationCap, title: "Education", desc: "Free and low-cost learning programs designed for community uplift.", to: "/courses" },
  { icon: Users, title: "Community", desc: "Community support, forums, and helpers for mutual aid coordination.", to: "/community" },
  { icon: Globe, title: "Creators", desc: "Creators, media makers, and partners share offerings and services.", to: "/creators" },
];

const SUPERVISOR_TOGGLES = [
  { label: "Visitor Access", href: "/more-help-center", description: "Browse public help resources and community support without signing in.", bg: "#f6d06d", color: "#1a1a2e" },
  { label: "Supervisor Login", href: "/supervisor/login", description: "Authenticate as an executive supervisor to access secure MORE Help Center controls.", bg: "#0d7377", color: "white" },
];

const PANEL_MODES = [
  { id: "exec", label: "Exec Mode", description: "Executive controls, monitoring, and audit-ready command links." },
  { id: "greeter", label: "Greeter Mode", description: "Warm public greeting flow for visitors and guided help navigation." },
  { id: "decoy", label: "Decoy Mode", description: "Fallback content and messaging when the main experience is down." },
];

const MODE_DETAILS = {
  exec: {
    title: "Executive Command Mode",
    summary: "This mode surfaces executive oversight workflows, live status, and privileged admin actions.",
    action: "Review platform health, audit pipelines, and secure escalation workflows.",
    links: [
      { label: "Admin System", to: "/admin/system" },
      { label: "M.O.R.E. Admin", to: "/more/admin" },
      { label: "M.O.R.E. Ops", to: "/more/ops" },
      { label: "Audit Log", to: "/admin/audit" },
    ],
  },
  greeter: {
    title: "Greeter / Visitor Mode",
    summary: "Use this mode to welcome visitors, route them to help resources, and keep the page calm and clear.",
    action: "Guide people to the MORE Help Center, community support, and public learning paths.",
    links: [
      { label: "MORE Help Center", to: "/more-help-center" },
      { label: "Courses", to: "/courses" },
      { label: "Community", to: "/community" },
    ],
  },
  decoy: {
    title: "Decoy / Fallback Mode",
    summary: "Activate this mode when the main experience is unavailable so the page still looks alive and helpful.",
    action: "Offer a credible fallback experience, point users to core resources, and preserve trust.",
    links: [
      { label: "MORE Help Center", to: "/more-help-center" },
      { label: "Supervisor Login", to: "/supervisor/login" },
      { label: "Help Desk", to: "/help-center" },
    ],
  },
};

export default function MoreHelpCenter() {
  const { user } = useAuth();
  const [freeModules, setFreeModules] = useState([]);
  const [mode, setMode] = useState(() => {
    try { return localStorage.getItem("more_help_center_mode") || "greeter"; } catch { return "greeter"; }
  });
  const modeMeta = MODE_DETAILS[mode] || MODE_DETAILS.greeter;

  useEffect(() => {
    try { localStorage.setItem("more_help_center_mode", mode); } catch {}
  }, [mode]);

  useEffect(() => {
    api.get("/modules").then((r) => {
      setFreeModules(r.data.filter((m) => m.free));
    }).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen" style={{ background: BG_WARM, color: "#1a1a2e" }}>
      <div style={{ height: 4, background: `linear-gradient(90deg, ${TEAL} 0%, ${GOLD} 50%, ${TEAL} 100%)` }} />

      <header className="sticky top-0 z-40" style={{ background: "#ffffff", borderBottom: "1px solid #e0d6cc" }}>
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div style={{ width: 36, height: 36, borderRadius: 8, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 900, fontSize: 18, fontFamily: "'Cabinet Grotesk', sans-serif" }}>M</div>
            <div>
              <div className="font-heading font-extrabold text-sm tracking-tight" style={{ color: TEAL }}>MORE Help Center</div>
              <div className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: "#8a7e72" }}>Goodwill Wing</div>
            </div>
          </div>
          <nav className="flex items-center gap-3 sm:gap-5">
            <a href="#modules" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Learn Free</a>
            <a href="#resources" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Resources</a>
            <a href="#support" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Get Help</a>
            <a href="/main" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Main Site</a>
            <a href="/supervisor/login" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Supervisor Login</a>
            <a href="https://www.wai-institute.org" target="_blank" rel="noopener noreferrer" className="text-xs font-bold px-4 py-2 rounded-lg transition-transform hover:scale-105" style={{ background: GOLD, color: "#1a1a2e" }}>
              WAI Institute →
            </a>
          </nav>
        </div>
      </header>

      <section className="relative overflow-hidden py-24 sm:py-32" style={{ background: `linear-gradient(165deg, ${TEAL_DARK} 0%, #0a4e52 50%, ${TEAL} 100%)` }}>
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: "radial-gradient(circle at 25px 25px, white 1px, transparent 0)", backgroundSize: "50px 50px" }} />
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-6" style={{ background: "rgba(255,255,255,0.15)", color: GOLD }}>
            <Heart className="w-3.5 h-3.5" /> 100% Free · Community-Powered
          </div>
          <h1 className="font-heading text-4xl sm:text-6xl font-black leading-tight text-white" style={{ textShadow: "0 2px 20px rgba(0,0,0,0.3)" }}>
            Help is here.
            <br />
            <span style={{ color: GOLD }}>Free, always.</span>
          </h1>
          <p className="text-lg sm:text-xl mt-6 max-w-2xl mx-auto leading-relaxed" style={{ color: "#c8e6e8" }}>
            No paywalls. No sign-ups required for core help. Browse free training, access community support, and find real guidance — no strings attached.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
            <a href="#modules" className="px-8 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105" style={{ background: GOLD, color: "#1a1a2e" }}>
              Start Learning Free
            </a>
            <a href="#support" className="px-8 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105" style={{ border: `2px solid ${GOLD}`, color: "white" }}>
              Get Support
            </a>
          </div>
        </div>
      </section>

      <section id="public-portal" className="py-20 px-6" style={{ background: "#ffffff" }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="overline" style={{ color: TEAL }}>All Public Help Pages</div>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold mt-2" style={{ color: "#1a1a2e" }}>The full public help experience lives inside MORE Help Center</h2>
            <p className="mt-3" style={{ color: "#6b5e52" }}>Browse every public-facing help page, then use the Supervisor toggles below to switch to executive access.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {PUBLIC_CATEGORIES.map((item) => {
              const Icon = item.icon;
              return (
                <a key={item.title} href={item.to} className="block p-6 rounded-xl transition-all hover:-translate-y-1" style={{ background: BG_WARM, border: "1px solid #e0d6cc" }}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-12 w-12 rounded-3xl bg-[#e0f2f1] flex items-center justify-center text-teal-900"><Icon className="w-6 h-6" /></div>
                    <div>
                      <h3 className="font-heading font-bold text-xl" style={{ color: "#1a1a2e" }}>{item.title}</h3>
                      <p className="text-sm mt-1" style={{ color: "#5a4e42" }}>{item.desc}</p>
                    </div>
                  </div>
                  <div className="text-xs font-bold uppercase tracking-[0.2em]" style={{ color: TEAL }}>Open</div>
                </a>
              );
            })}
          </div>
        </div>
      </section>

      <section id="supervisor-controls" className="py-20 px-6" style={{ background: BG_WARM }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="overline" style={{ color: TEAL }}>Supervisor Controls</div>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold mt-2" style={{ color: "#1a1a2e" }}>Choose your permission level</h2>
            <p className="mt-3" style={{ color: "#6b5e52" }}>Public users can browse help resources. Supervisors may sign in and access secure executive controls inside the same MORE Help Center.</p>
          </div>
          <div className="grid gap-6 sm:grid-cols-3">
            {SUPERVISOR_TOGGLES.map((item) => (
              <a key={item.label} href={item.href} className="rounded-[28px] p-6 shadow-[0_20px_45px_rgba(97,64,35,0.08)] transition hover:-translate-y-1" style={{ background: item.bg, color: item.color }}>
                <div className="text-xs uppercase tracking-[0.4em] font-bold mb-3">{item.label}</div>
                <div className="text-sm leading-7">{item.description}</div>
              </a>
            ))}
          </div>

          {user?.role === "executive_admin" && (
            <div className="mt-16 rounded-[32px] border border-[#e7dac5] bg-white p-6 shadow-[0_20px_60px_rgba(97,60,20,0.08)]">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="overline" style={{ color: "#8d5a33" }}>Executive mode</div>
                  <h2 className="font-heading text-3xl font-black text-[#2b1f15] mt-2">Supervisor mode controls</h2>
                  <p className="mt-3 max-w-2xl text-[#5c4c41]">
                    As an executive supervisor, you can switch between the centralized MORE Help Center’s display modes for public greeting, executive oversight, or fallback support.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  {PANEL_MODES.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setMode(item.id)}
                      className={`rounded-full px-5 py-3 text-sm font-bold uppercase tracking-[0.18em] transition ${mode === item.id ? "bg-[#8d5a33] text-white" : "bg-[#f3e8d7] text-[#4f3c28] hover:bg-[#e7d4b2]"}`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-8 rounded-[28px] border border-[#d3b588] bg-[#fbf5ec] p-8">
                <div className="text-sm uppercase tracking-[0.35em] font-bold text-[#8d5a33]">{modeMeta.title}</div>
                <p className="mt-4 text-lg text-[#3d3229]">{modeMeta.summary}</p>
                <p className="mt-4 text-sm text-[#5c4c41]">{modeMeta.action}</p>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {modeMeta.links.map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      className="rounded-3xl border border-[#d3b588] bg-[#fff5e0] px-4 py-4 text-sm font-semibold text-[#2f281f] transition hover:-translate-y-0.5"
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {freeModules.length > 0 && (
        <section id="modules" className="py-20 px-6" style={{ background: "#ffffff" }}>
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <div className="overline" style={{ color: TEAL }}>Free Curriculum</div>
              <h2 className="font-heading text-3xl sm:text-4xl font-bold mt-2" style={{ color: "#1a1a2e" }}>Start Here — No Account Needed</h2>
              <p className="mt-3" style={{ color: "#6b5e52" }}>Complete these free modules and earn Partnership Points toward the full program.</p>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {freeModules.map((m) => (
                <a href={`https://www.wai-institute.org/modules/${m.slug}`} key={m.slug} className="block p-6 rounded-xl transition-all hover:-translate-y-1" style={{ background: BG_WARM, border: "1px solid #e0d6cc" }}>
                  <div className="flex items-start justify-between mb-3">
                    <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest" style={{ background: GOLD, color: "#1a1a2e" }}>FREE</span>
                    {m.points && <span className="text-xs font-bold" style={{ color: TEAL }}>+{m.points} pts</span>}
                  </div>
                  <h3 className="font-heading font-bold text-xl" style={{ color: "#1a1a2e" }}>{m.title}</h3>
                  <p className="text-sm mt-2 leading-relaxed" style={{ color: "#5a4e42" }}>{m.summary}</p>
                  <div className="flex items-center gap-4 mt-4 text-xs font-bold uppercase tracking-widest" style={{ color: TEAL }}>
                    <span>{m.hours}h</span>
                    <span>{m.tasks.length} tasks</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </a>
              ))}
            </div>
            <div className="text-center mt-8">
              <a href="https://www.wai-institute.org/register" target="_blank" rel="noopener noreferrer" className="px-6 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105 inline-flex items-center gap-2" style={{ border: `2px solid ${TEAL}`, color: TEAL }}>
                Create Account for Full Program <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </section>
      )}

      <section id="resources" className="py-20 px-6" style={{ background: BG_WARM }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="overline" style={{ color: TEAL }}>Goodwill Resources</div>
            <h2 className="font-heading text-3xl sm:text-4xl font-bold mt-2" style={{ color: "#1a1a2e" }}>Everything You Need, No Cost</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: BookOpen, title: "Free Modules", desc: "Hands-on training in electrical basics, tools, and safety — free forever.", link: "https://www.wai-institute.org/modules" },
              { icon: MessageSquare, title: "Community Help", desc: "Ask questions, share knowledge, get real answers from real people.", link: "https://www.wai-institute.org/community" },
              { icon: Shield, title: "Support Line", desc: "Email us anytime. No bots, no runaround — just help.", link: `mailto:${SUPPORT_EMAIL}` },
              { icon: Globe, title: "Full Program", desc: "Ready to go deeper? Enroll in the complete WAI Institute curriculum.", link: "https://www.wai-institute.org" },
            ].map((r) => (
              <a key={r.title} href={r.link} target={r.link.startsWith("http") ? "_blank" : undefined} rel={r.link.startsWith("http") ? "noopener noreferrer" : undefined} className="p-6 rounded-xl transition-all hover:-translate-y-1" style={{ background: "#ffffff", border: "1px solid #e0d6cc" }}>
                <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4" style={{ background: TEAL }}>
                  <r.icon className="w-5 h-5" style={{ color: "white" }} />
                </div>
                <h3 className="font-heading font-bold text-lg" style={{ color: "#1a1a2e" }}>{r.title}</h3>
                <p className="text-sm mt-2 leading-relaxed" style={{ color: "#5a4e42" }}>{r.desc}</p>
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-6" style={{ background: "#ffffff" }}>
        <div className="max-w-6xl mx-auto rounded-[32px] border border-[#e0d6cc] bg-[#f6f0e9] p-10 text-center shadow-[0_20px_50px_rgba(97,64,35,0.08)]">
          <div className="inline-flex items-center justify-center gap-2 rounded-full bg-[#e8b83e33] px-4 py-2 text-xs font-bold uppercase tracking-[0.35em] text-[#8d5a33]">
            New hub guided tour
          </div>
          <h2 className="mt-6 text-3xl font-black text-[#1a1a2e]">MORE Help Center is the unified public hub</h2>
          <p className="mt-4 max-w-3xl mx-auto text-sm leading-7 text-[#5a4e42]">
            This is the single centralized help landing experience. Supervisors sign in for executive oversight inside the same MORE Help Center page.
          </p>
          <a href="/supervisor/login" className="mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-[#0d7377] px-8 py-4 text-sm font-bold uppercase tracking-[0.15em] text-white transition hover:bg-[#095b5e]">
            Supervisor Login <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      <section id="support" className="py-20 px-6" style={{ background: "#ffffff" }}>
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-6" style={{ background: BG_WARM, color: TEAL }}>
            <Phone className="w-3.5 h-3.5" /> Get In Touch
          </div>
          <h2 className="font-heading text-3xl sm:text-4xl font-bold" style={{ color: "#1a1a2e" }}>Need Help?</h2>
          <p className="mt-4 text-lg" style={{ color: "#5a4e42" }}>
            Email us at{" "}
            <a href={`mailto:${SUPPORT_EMAIL}`} className="font-bold underline" style={{ color: TEAL }}>{SUPPORT_EMAIL}</a>
            {" "}— we respond within 24 hours. No cost, no account needed.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href={`mailto:${SUPPORT_EMAIL}`} className="px-8 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105" style={{ background: TEAL, color: "white" }}>
              Email Support
            </a>
            <a href="https://www.wai-institute.org/help-center" target="_blank" rel="noopener noreferrer" className="px-8 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105" style={{ border: `2px solid ${TEAL}`, color: TEAL }}>
              Help Center
            </a>
          </div>
        </div>
      </section>

      <section className="py-16 px-6" style={{ background: TEAL_DARK }}>
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Users className="w-5 h-5" style={{ color: GOLD }} />
            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: GOLD }}>WAI Institute</span>
          </div>
          <h2 className="font-heading text-2xl sm:text-3xl font-bold text-white">
            MORE Help Center is the centralized help hub for everyone
          </h2>
          <p className="mt-4 text-base" style={{ color: "#a0d4d6" }}>
            Free resources for everyone. When you're ready for certification, advanced training, and credentials — the full program is one click away.
          </p>
          <a href="https://www.wai-institute.org" target="_blank" rel="noopener noreferrer" className="mt-8 inline-flex items-center gap-2 px-8 py-3 font-bold text-sm uppercase tracking-widest rounded-lg transition-all hover:scale-105" style={{ background: GOLD, color: "#1a1a2e" }}>
            Visit WAI Institute <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      <footer className="py-8 px-6" style={{ background: "#0d2b2d", color: "#7ab8bb" }}>
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2">
            <Heart className="w-3.5 h-3.5" />
            <span>MORE Help Center — Goodwill Wing of WAI Institute</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://www.wai-institute.org/privacy" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Privacy</a>
            <a href="https://www.wai-institute.org/terms" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Terms</a>
            <a href={`mailto:${SUPPORT_EMAIL}`} className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
