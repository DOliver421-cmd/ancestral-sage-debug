import { useEffect, useState } from "react";
import { Heart, BookOpen, MessageSquare, ArrowRight, Phone, Shield, Users, Globe } from "lucide-react";
import { api } from "../lib/api";

const SUPPORT_EMAIL = "poetgames@gmail.com";
const GOLD = "#e8b83e";
const TEAL = "#0d7377";
const TEAL_DARK = "#095b5e";
const BG_WARM = "#f9f5f0";

export default function MoreHelpCenter() {
  const [freeModules, setFreeModules] = useState([]);

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
              <div className="font-heading font-extrabold text-sm tracking-tight" style={{ color: TEAL }}>MoreHelp Center</div>
              <div className="text-[10px] font-semibold tracking-widest uppercase" style={{ color: "#8a7e72" }}>Goodwill Wing</div>
            </div>
          </div>
          <nav className="flex items-center gap-3 sm:gap-5">
            <a href="#modules" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Learn Free</a>
            <a href="#resources" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Resources</a>
            <a href="#support" className="text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4e42" }}>Get Help</a>
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
          <h2 className="mt-6 text-3xl font-black text-[#1a1a2e]">Seshat’s Hub is now live</h2>
          <p className="mt-4 max-w-3xl mx-auto text-sm leading-7 text-[#5a4e42]">
            Experience the Supervisor landing page, visit the finance-driven marketplace, and discover the support services that frame the M.O.R.E. Help Center.
          </p>
          <a href="/seshats-hub" className="mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-[#0d7377] px-8 py-4 text-sm font-bold uppercase tracking-[0.15em] text-white transition hover:bg-[#095b5e]">
            Visit Seshat’s Hub <ArrowRight className="w-4 h-4" />
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
            MoreHelp Center is the{" "}
            <span style={{ color: GOLD }}>goodwill wing</span>
            {" "}of WAI Institute
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
            <span>MoreHelp Center — Goodwill Wing of WAI Institute</span>
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
