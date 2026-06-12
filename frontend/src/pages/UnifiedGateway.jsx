import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { BRAND, WAI_LOGO } from "../lib/brand";
import PublicNav from "../components/PublicNav";

export default function UnifiedGateway() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-bone font-body">
      <PublicNav />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden"
        style={{ background: "linear-gradient(160deg, #0a0a0f 0%, #1a0a00 50%, #0d1a0a 100%)", minHeight: "90vh" }}>

        {/* Grain texture overlay */}
        <div className="absolute inset-0 opacity-20"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.4'/%3E%3C/svg%3E\")" }} />

        {/* Accent glow */}
        <div className="absolute top-0 left-1/3 w-96 h-96 rounded-full opacity-10 blur-3xl"
          style={{ background: "#E8A51E" }} />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 rounded-full opacity-8 blur-3xl"
          style={{ background: "#2D6A4F" }} />

        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 flex flex-col items-start">

          <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full border"
            style={{ borderColor: "rgba(232,165,30,0.3)", background: "rgba(232,165,30,0.08)" }}>
            <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse" />
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.2em", textTransform: "uppercase", color: "#E8A51E" }}>
              W.A.I. Institute
            </span>
          </div>

          <h1 style={{
            fontFamily: "'Cabinet Grotesk', 'Plus Jakarta Sans', sans-serif",
            fontSize: "clamp(2.8rem, 7vw, 5.5rem)",
            fontWeight: 900, lineHeight: 1.05,
            color: "#fff", marginBottom: "1.5rem", maxWidth: 800,
          }}>
            Creator economy.<br />
            <span style={{ color: "#E8A51E" }}>Cultural expression.</span><br />
            Economic dignity.
          </h1>

          <p style={{ fontSize: "clamp(1rem, 2.2vw, 1.25rem)", color: "rgba(255,255,255,0.6)", maxWidth: 560, lineHeight: 1.7, marginBottom: "2.5rem" }}>
            A platform built for invisible communities — artists, poets, builders, and
            workers who deserve real tools, real ownership, and real support.
          </p>

          <div className="flex flex-wrap gap-4">
            {!user ? (
              <>
                <Link to="/register"
                  className="font-black text-sm px-8 py-4 rounded-xl"
                  style={{ background: "#E8A51E", color: "#0a0a0a", fontSize: 15 }}>
                  Join Free →
                </Link>
                <Link to="/subscribe?plan=sanctuary_trial"
                  className="font-bold text-sm px-8 py-4 rounded-xl border"
                  style={{ borderColor: "rgba(232,165,30,0.4)", color: "#E8A51E", background: "rgba(232,165,30,0.08)", fontSize: 15 }}>
                  Try Everything — $3 for 3 Days
                </Link>
                <Link to="/login"
                  style={{ color: "rgba(255,255,255,0.4)", fontSize: 14, fontWeight: 600, display: "flex", alignItems: "center", paddingTop: 14 }}>
                  Log in →
                </Link>
              </>
            ) : (
              <>
                <Link to="/profile"
                  className="font-black text-sm px-8 py-4 rounded-xl"
                  style={{ background: "#E8A51E", color: "#0a0a0a", fontSize: 15 }}>
                  My Profile →
                </Link>
                <Link to="/dashboard"
                  className="font-bold text-sm px-8 py-4 rounded-xl border"
                  style={{ borderColor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.8)", fontSize: 15 }}>
                  Dashboard
                </Link>
              </>
            )}
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-8 mt-16 pt-8 border-t w-full"
            style={{ borderColor: "rgba(255,255,255,0.08)" }}>
            {[
              { n: "5",       label: "Membership tiers"         },
              { n: "$3",      label: "All-access trial"         },
              { n: "6",       label: "Social platforms, one post" },
              { n: "100%",    label: "Creator-owned content"    },
            ].map(({ n, label }) => (
              <div key={label}>
                <div style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "2rem", fontWeight: 900, color: "#E8A51E", lineHeight: 1 }}>{n}</div>
                <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.1em" }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── WHAT IT IS ───────────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-copper mb-3 text-center">The Platform</div>
          <h2 className="font-heading font-black text-4xl text-ink text-center mb-4">
            Everything a creator needs.<br />Nothing they don't.
          </h2>
          <p className="text-ink/50 text-center max-w-2xl mx-auto mb-16 text-lg leading-relaxed">
            Learn, create, publish, earn, and connect — all from one profile.
            Your dashboard. Your tools. Your tier.
          </p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: "🎓", title: "Learn & Certify",       desc: "Curriculum, AI tutor, compliance courses, lab simulations, and verifiable credentials.",          to: "/modules" },
              { icon: "🎨", title: "Create & Publish",      desc: "Ghost Producer AI, Creator Studio, Social Blast to 6 platforms, Band on a Page, Lyric Forge.",   to: "/studio" },
              { icon: "💰", title: "Earn & Get Paid",       desc: "Sell courses, manage earnings, request payouts. 70% creator / 30% platform split.",               to: "/creator/earnings" },
              { icon: "🤝", title: "Community & M.O.R.E.",  desc: "Members' Palace, Elder Council, legal tools, mutual aid matching, community chat.",               to: "/app/more" },
              { icon: "🤖", title: "AI Tools Suite",        desc: "AI Tutor, Sovereign Chat, Ghost Publicist, Ghost Legal, Ghost Marketer — all on platform.",       to: "/ai" },
              { icon: "🏛️", title: "WAI Institute",         desc: "Accredited-track courses, workforce credentials, instructor-led labs, and placement support.",   to: "/wai-institute" },
            ].map(({ icon, title, desc, to }) => (
              <Link key={title} to={to}
                className="card-flat p-6 flex flex-col gap-3 hover:border-copper transition-all group no-underline">
                <div style={{ fontSize: 32 }}>{icon}</div>
                <div className="font-heading font-bold text-lg text-ink group-hover:text-copper transition-colors">{title}</div>
                <div className="text-ink/55 text-sm leading-relaxed flex-1">{desc}</div>
                <div className="text-copper text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity">Explore →</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── $3 TRIAL BANNER ──────────────────────────────────────────────── */}
      {!user && (
        <section className="py-16 px-6" style={{ background: "#0a0a0f" }}>
          <div className="max-w-4xl mx-auto text-center">
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚡</div>
            <h2 style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "clamp(1.8rem,4vw,3rem)", fontWeight: 900, color: "#fff", marginBottom: 12 }}>
              Try the whole platform for{" "}
              <span style={{ color: "#E8A51E" }}>$3</span>
            </h2>
            <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "1.1rem", marginBottom: 32, lineHeight: 1.7 }}>
              3 days · 33 minutes · 33 seconds of full Pro access.<br />
              Every tool. Every course. Every AI feature. No recurring charge unless you choose a plan.
            </p>
            <Link to="/subscribe?plan=sanctuary_trial"
              className="inline-block font-black text-base px-10 py-4 rounded-xl"
              style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              Start My $3 Trial →
            </Link>
            <div className="mt-4">
              <Link to="/plans" style={{ color: "rgba(255,255,255,0.3)", fontSize: 13, textDecoration: "none" }}>
                See all membership plans
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* ── CREATOR PROFILES ─────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-bone">
        <div className="max-w-6xl mx-auto">
          <div className="overline text-copper mb-3">Creators & Partners</div>
          <div className="flex items-end justify-between mb-12">
            <h2 className="font-heading font-black text-4xl text-ink">The voices of<br />the movement</h2>
            <Link to="/creators" className="text-copper font-bold text-sm hover:underline">
              View all creators →
            </Link>
          </div>
          <CreatorPreview />
        </div>
      </section>

      {/* ── MEMBERSHIP TIERS ─────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-copper mb-3 text-center">Membership</div>
          <h2 className="font-heading font-black text-4xl text-ink text-center mb-4">Start free.<br />Grow on your terms.</h2>
          <p className="text-ink/50 text-center mb-12 max-w-xl mx-auto">Every tier keeps the doors open for someone who can't pay yet.</p>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
            {[
              { name: "Free",    price: "$0",   color: "#6b7280", features: ["Community access", "Browse courses", "Daily XP puzzle"] },
              { name: "Member",  price: "$9",   color: "#3b82f6", features: ["Full M.O.R.E.", "AI Tutor", "Creator basics"] },
              { name: "Plus",    price: "$15",  color: "#8b5cf6", features: ["Ghost Producer", "Creator Studio", "Course selling"] },
              { name: "Pro",     price: "$29",  color: "#b5651d", features: ["Full AI suite", "Advanced labs", "Earnings dashboard"], highlight: true },
              { name: "Patron",  price: "$59",  color: "#E8A51E", features: ["Founder's circle", "Fund free access", "Direct line"] },
            ].map(({ name, price, color, features, highlight }) => (
              <div key={name}
                className="card-flat p-5 flex flex-col"
                style={highlight ? { borderColor: color, borderWidth: 2 } : {}}>
                {highlight && <div className="text-xs font-black uppercase tracking-widest mb-2" style={{ color }}>Most Popular</div>}
                <div className="font-heading font-black text-2xl text-ink">{price}<span className="text-sm font-medium text-ink/40">/mo</span></div>
                <div className="font-bold text-sm mt-1 mb-3" style={{ color }}>{name}</div>
                <ul className="space-y-1 flex-1">
                  {features.map(f => (
                    <li key={f} className="text-xs text-ink/60 flex items-start gap-1.5">
                      <span style={{ color, marginTop: 2 }}>✓</span> {f}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link to="/plans" className="btn-copper inline-block px-8 py-3 text-sm font-bold">
              Compare all plans →
            </Link>
          </div>
        </div>
      </section>

      {/* ── MISSION STATEMENT ────────────────────────────────────────────── */}
      <section className="py-24 px-6"
        style={{ background: "linear-gradient(135deg, #1B4332 0%, #0a0a0f 60%)" }}>
        <div className="max-w-4xl mx-auto text-center">
          <img src={WAI_LOGO} alt="WAI" className="w-16 h-16 object-contain mx-auto mb-8"
            style={{ mixBlendMode: "screen" }} />
          <h2 style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "clamp(1.6rem,4vw,2.8rem)", fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 20 }}>
            "{BRAND.tagline}"
          </h2>
          <p style={{ color: "rgba(255,255,255,0.55)", fontSize: "1.05rem", lineHeight: 1.8, maxWidth: 560, margin: "0 auto 40px" }}>
            WAI Institute was built because the tools of the creator economy were never
            designed for us. We changed that. Every feature, every tier, every dollar
            — built to serve communities that were meant to be invisible.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/register"
              className="font-black text-sm px-8 py-3 rounded-xl"
              style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              Join the Movement
            </Link>
            <Link to="/donate"
              className="font-bold text-sm px-8 py-3 rounded-xl border"
              style={{ borderColor: "rgba(232,165,30,0.3)", color: "#E8A51E" }}>
              Support the Mission
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="py-12 px-6 bg-ink text-white/40">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mb-8 pb-8 border-b border-white/8">
            <div className="flex items-center gap-3">
              <img src={WAI_LOGO} alt="WAI" className="w-8 h-8 object-contain" style={{ mixBlendMode: "screen" }} />
              <div>
                <div className="text-xs font-black uppercase tracking-widest text-signal">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm text-white">{BRAND.name}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-6 text-xs">
              {[["Plans", "/plans"], ["Creators", "/creators"], ["WAI Institute", "/wai-institute"], ["Donate", "/donate"], ["Privacy", "/privacy"], ["Terms", "/terms"]].map(([l, h]) => (
                <Link key={l} to={h} className="hover:text-white transition-colors">{l}</Link>
              ))}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
            <p>© {new Date().getFullYear()} {BRAND.name}. All rights reserved.</p>
            <p style={{ color: "rgba(255,255,255,0.25)" }}>{BRAND.mission}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ── Live creator preview — pulls from DB ──────────────────────────────────────
import { useEffect, useState } from "react";
import { api } from "../lib/api";

function CreatorPreview() {
  const [creators, setCreators] = useState([]);

  useEffect(() => {
    api.get("/creator/profiles/public")
      .then(r => setCreators((r.data.profiles || []).slice(0, 3)))
      .catch(() => {});
  }, []);

  if (creators.length === 0) return (
    <div className="grid sm:grid-cols-3 gap-4">
      {[1,2,3].map(i => (
        <div key={i} className="card-flat p-6 animate-pulse">
          <div className="w-12 h-12 rounded-full bg-ink/10 mx-auto mb-3" />
          <div className="h-4 bg-ink/10 rounded w-3/4 mx-auto mb-2" />
          <div className="h-3 bg-ink/5 rounded w-1/2 mx-auto" />
        </div>
      ))}
    </div>
  );

  return (
    <div className="grid sm:grid-cols-3 gap-4">
      {creators.map(c => (
        <Link key={c.slug} to={`/u/${c.slug}`}
          className="card-flat p-6 text-center hover:border-copper transition-colors group no-underline block">
          <div style={{ fontSize: 44, marginBottom: 12 }}>{c.avatar || "🎨"}</div>
          <div className="font-heading font-bold text-ink text-lg group-hover:text-copper transition-colors">
            {c.display_name || c.name}
          </div>
          <div className="overline text-copper mt-1">{c.title || c.role}</div>
          {c.bio && <div className="text-xs text-ink/50 mt-2 line-clamp-2">{c.bio}</div>}
          <div className="text-xs font-bold text-copper mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            View Profile →
          </div>
        </Link>
      ))}
    </div>
  );
}
