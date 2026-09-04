import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { BRAND, WAI_LOGO } from "../lib/brand";
import PublicNav from "../components/PublicNav";
import SharePanel from "../components/SharePanel";
import { PublicHelper } from "./Helper";
import { Lock, Share2, ArrowRight } from "lucide-react";

// The WAI Institute community group on Facebook — the mission's home on FB.
export const FACEBOOK_GROUP_URL = "https://www.facebook.com/groups/waiinstitute";

// The logo D. Oliver provided — kept as a direct public asset reference so it
// is actually placed on the page instead of only the generated SVG mark.
const FOUNDER_LOGO = "/WAI_Logo.jpg";

// ── Tier badges — every paid feature is visibly not free ─────────────────────
// Matches the membership colors used further down this page so the signals agree.
const TIER_STYLE = {
  free:   { label: "Free",   color: "#6b7280" },
  member: { label: "Member", color: "#3b82f6" },
  plus:   { label: "Plus",   color: "#8b5cf6" },
  pro:    { label: "Pro",    color: "#b5651d" },
  patron: { label: "Patron", color: "#E8A51E" },
};

function TierBadge({ tier }) {
  const s = TIER_STYLE[tier] || TIER_STYLE.free;
  const paid = tier !== "free";
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider"
      style={{ color: s.color, background: `${s.color}1a`, border: `1px solid ${s.color}40` }}
      title={paid ? `Requires ${s.label} membership (or the $3 all-access trial)` : "Included free"}
    >
      {paid && <Lock className="w-2.5 h-2.5" />}
      {s.label}
    </span>
  );
}

export default function UnifiedGateway() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen font-body" style={{ background: "#fff", color: "#111111" }}>
      <PublicNav />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden border-b border-[#e3ddd2]"
        style={{ minHeight: "80vh", background: "#fff" }}>
        <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-16 grid lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)] gap-12 xl:gap-20 items-center">

          <div className="min-w-0">
          <div className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full border"
            style={{ borderColor: "rgba(154,101,0,0.35)", background: "#fff8e7" }}>
            <img src={FOUNDER_LOGO} alt="M.O.R.E."
              style={{ width: 26, height: 26, borderRadius: "50%", objectFit: "cover", border: "1px solid rgba(232,165,30,0.4)" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-signal animate-pulse" />
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.2em", textTransform: "uppercase", color: "#7a4d00" }}>
              M.O.R.E. Help Center
            </span>
          </div>

          <h1 style={{
            fontFamily: "'Cabinet Grotesk', 'Plus Jakarta Sans', sans-serif",
            fontSize: "clamp(2.8rem, 7vw, 5.5rem)",
            fontWeight: 900, lineHeight: 1.05,
            color: "#111111", marginBottom: "1.5rem", maxWidth: 800,
          }}>
            Creator economy.<br />
            <span style={{ color: "#8a5a00" }}>Cultural expression.</span><br />
            Economic dignity.
          </h1>

          <p style={{ fontSize: "clamp(1rem, 2.2vw, 1.25rem)", color: "#3f3a34", maxWidth: 560, lineHeight: 1.7, marginBottom: "2.5rem" }}>
            A platform built for invisible communities — artists, poets, builders, and
            workers who deserve real tools, real ownership, and real support.
          </p>

          <div className="flex flex-wrap gap-4">
            {!user ? (
              <>
                <Link to="/register"
                  className="font-black text-sm px-8 py-4 rounded-xl"
                  style={{ background: "#b8860b", color: "#111111", fontSize: 15 }}>
                  Join Free →
                </Link>
                <Link to="/subscribe?plan=sanctuary_trial"
                  className="font-bold text-sm px-8 py-4 rounded-xl border"
                  style={{ borderColor: "rgba(154,101,0,0.45)", color: "#7a4d00", background: "#fff8e7", fontSize: 15 }}>
                  Try Everything — $3 for 3 Days
                </Link>
                <Link to="/login"
                  style={{ color: "#4a4238", fontSize: 14, fontWeight: 600, display: "flex", alignItems: "center", paddingTop: 14 }}>
                  Log in →
                </Link>
                <SharePanel
                  compact
                  url="/"
                  title="M.O.R.E. Help Center — Creator economy. Cultural expression. Economic dignity."
                  trigger={
                    <span className="inline-flex items-center gap-2 font-bold text-sm px-8 py-4 rounded-xl border"
                      style={{ borderColor: "#c9c0b2", color: "#2b2722", fontSize: 15 }}>
                      <Share2 size={16} /> Share
                    </span>
                  }
                />
              </>
            ) : (
              <>
                <Link to="/profile"
                  className="font-black text-sm px-8 py-4 rounded-xl"
                  style={{ background: "#b8860b", color: "#111111", fontSize: 15 }}>
                  My Profile →
                </Link>
                <Link to="/dashboard"
                  className="font-bold text-sm px-8 py-4 rounded-xl border"
                  style={{ borderColor: "#c9c0b2", color: "#2b2722", fontSize: 15 }}>
                  Dashboard
                </Link>
              </>
            )}
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-8 mt-16 pt-8 border-t w-full"
            style={{ borderColor: "#e3ddd2" }}>
            {[
              { n: "5",       label: "Membership tiers"         },
              { n: "$3",      label: "All-access trial"         },
              { n: "6",       label: "Social platforms, one post" },
              { n: "100%",    label: "Creator-owned content"    },
            ].map(({ n, label }) => (
              <div key={label}>
                <div style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "2rem", fontWeight: 900, color: "#8a5a00", lineHeight: 1 }}>{n}</div>
                <div style={{ fontSize: 12, color: "#4a4238", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.1em" }}>{label}</div>
              </div>
            ))}
          </div>
          </div>

          <figure className="w-full max-w-md mx-auto lg:justify-self-end">
            <div className="overflow-hidden rounded-[2rem] border border-[#d9d0c4] bg-[#f6f2eb] shadow-[12px_12px_0_#e8dcc7]">
              <img
                src="https://images.pexels.com/photos/3856027/pexels-photo-3856027.jpeg?auto=compress&cs=tinysrgb&w=1200"
                alt="A diverse group gathered for community learning and collaboration"
                className="block aspect-[4/5] w-full object-cover"
                loading="eager"
                referrerPolicy="no-referrer"
              />
            </div>
            <figcaption className="mt-4 text-center text-xs leading-relaxed text-[#5a5045]">
              Community learning and collaboration · free stock photo from Pexels
            </figcaption>
          </figure>
        </div>
      </section>

      {/* ── MY HELPER — THE WORKING MODULE, BELOW M.O.R.E. HELP CENTER ───── */}
      <section className="relative overflow-hidden"
        style={{ background: "#fff", borderBottom: "1px solid #e3ddd2" }}>
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          {/* Header row: founder logo + copy + full-page link */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 sm:gap-5 mb-5 sm:mb-8">
            <img src={FOUNDER_LOGO} alt="M.O.R.E. Logo"
              className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl object-cover shrink-0"
              style={{ border: "2px solid rgba(154,101,0,0.35)", boxShadow: "0 8px 24px rgba(76,55,20,0.12)" }} />
            <div className="flex-1">
              <div className="overline" style={{ color: "#7a4d00" }}>My Helper — built for our elders</div>
              <h2 style={{
                fontFamily: "'Cabinet Grotesk', 'Plus Jakarta Sans', sans-serif",
                fontSize: "clamp(1.35rem, 3.5vw, 2.4rem)", fontWeight: 900,
                color: "#111111", lineHeight: 1.15, margin: "4px 0 6px",
              }}>
                I am here to be your <span style={{ color: "#8a5a00" }}>HELPER.</span>
              </h2>
              <p style={{ color: "#4a4238", maxWidth: 640, lineHeight: 1.6, fontSize: "0.95rem", margin: 0 }}>
                Read mail, understand bills, explain legal papers, check for scams, and remember
                appointments — in plain, simple words, in your own language. Free, no login required.
                Named in honor of <strong style={{ color: "#111111" }}>Michael Oliver</strong> — the M.O.R.E. in M.O.R.E. Help Center.
              </p>
            </div>
            <Link to="/helper"
              className="inline-flex items-center gap-2 font-bold text-sm px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl border shrink-0 self-start"
              style={{ borderColor: "rgba(154,101,0,0.45)", color: "#7a4d00", background: "#fff8e7", fontSize: 14 }}>
              Open full page →
            </Link>
          </div>

          {/* The actual working helper — all functions, live right on the landing page */}
          <div className="rounded-2xl overflow-hidden" style={{ height: "min(88dvh, 760px)", boxShadow: "0 16px 40px rgba(76,55,20,0.12)" }}>
            <PublicHelper embedded />
          </div>

          {user ? (
            <div className="mt-5 flex flex-wrap justify-center gap-3">
              <Link to="/app/helper"
                className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl"
                style={{ background: "#b8860b", color: "#111111", fontSize: 14 }}>
                Open My Personal Helper
              </Link>
            </div>
          ) : (
            <div className="mt-5 flex flex-wrap justify-center gap-3">
              <Link to="/helper"
                className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl"
                style={{ background: "#b8860b", color: "#111111", fontSize: 14 }}>
                Try My Helper on its own page — Free
              </Link>
              <Link to="/register"
                className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border"
                style={{ borderColor: "#c9c0b2", color: "#2b2722", fontSize: 14 }}>
                Join free for saved notes
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* ── WHAT IT IS ───────────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "#fff" }}>
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
              { icon: "🎓", title: "Learn & Certify",       tier: "free", desc: "Curriculum, AI tutor, compliance courses, lab simulations, and verifiable credentials.",          to: "/modules" },
              { icon: "🎨", title: "Create & Publish",      tier: "plus", desc: "Ghost Producer AI, Creator Studio, Social Blast to 6 platforms, Band on a Page, Lyric Forge.",   to: "/studio" },
              { icon: "💰", title: "Earn & Get Paid",       tier: "plus", desc: "Sell courses, manage earnings, request payouts. 70% creator / 30% platform split.",               to: "/creator/earnings" },
              { icon: "🤝", title: "Community & M.O.R.E.",  tier: "free", desc: "Members' Palace, Elder Council, legal tools, mutual aid matching, community chat.",               to: "/more" },
              { icon: "🤖", title: "AI Tools Suite",        tier: "free", desc: "AI Tutor, Ghost Producer, and more — run on your own key via the $3 BYOK unlock. The platform doesn't fund customer AI.",       to: "/byok" },
              { icon: "🏛️", title: "M.O.R.E. Institute",    tier: "free", desc: "Accredited-track courses, workforce credentials, instructor-led labs, and placement support.",   to: "/wai-institute" },
            ].map(({ icon, title, desc, to, tier }) => (
              <Link key={title} to={to}
                className="card-flat p-6 flex flex-col gap-3 hover:border-copper transition-all group no-underline">
                <div style={{ fontSize: 32 }}>{icon}</div>
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="font-heading font-bold text-lg text-ink group-hover:text-copper transition-colors">{title}</div>
                  <TierBadge tier={tier} />
                </div>
                <div className="text-ink/55 text-sm leading-relaxed flex-1">{desc}</div>
                <div className="text-copper text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity">Explore →</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── WAI INSTITUTE PREMIUM SERVICES — live embed + full-page link ── */}
      <section className="relative overflow-hidden"
        style={{ background: "#fff", borderBottom: "1px solid #e3ddd2" }}>
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          {/* Header row: copy + full-page link */}
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 sm:gap-5 mb-5 sm:mb-8">
            <div className="flex-1">
              <div className="overline" style={{ color: "#8a5a00" }}>WAI Institute Premium Services</div>
              <h2 style={{
                fontFamily: "'Cabinet Grotesk', 'Plus Jakarta Sans', sans-serif",
                fontSize: "clamp(1.35rem, 3.5vw, 2.4rem)", fontWeight: 900,
                color: "#111111", lineHeight: 1.15, margin: "4px 0 6px",
              }}>
                Payment rails for <span style={{ color: "#8a5a00" }}>platforms &amp; creators.</span>
              </h2>
              <p style={{ color: "#4a4238", maxWidth: 640, lineHeight: 1.6, fontSize: "0.95rem", margin: 0 }}>
                We help other platforms and creators integrate payment systems through our ecosystem —
                a Stripe-integrated store and SaaS for checkout, memberships, subscriptions, and payouts.
              </p>
            </div>
            <a href="https://waiinstitutepremiumservices.bolt.host/services" target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-bold text-sm px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl border shrink-0 self-start"
              style={{ borderColor: "rgba(154,101,0,0.45)", color: "#7a4d00", background: "#fff8e7", fontSize: 14 }}>
              Open full page →
            </a>
          </div>

          {/* The live Premium Services site, embedded */}
          <div className="rounded-2xl overflow-hidden" style={{ height: "min(85vh, 720px)", border: "1px solid rgba(181,101,29,0.35)", boxShadow: "0 30px 80px rgba(0,0,0,0.45)" }}>
            <iframe
              title="WAI Institute Premium Services"
              src="https://waiinstitutepremiumservices.bolt.host/"
              className="w-full h-full"
              style={{ border: 0, display: "block" }}
              loading="lazy"
              referrerPolicy="no-referrer"
            />
          </div>
          <div className="mt-5 text-center">
            <Link to="/premium"
              className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl"
              style={{ background: "#8a5a00", color: "#fff", fontSize: 14 }}>
              Visit the Premium Services page →
            </Link>
          </div>
        </div>
      </section>

      {/* ── READY TO GO DEEPER? — the WAI pathway (M.O.R.E. funnels to the institution door) ── */}
      <section className="relative overflow-hidden py-24 px-6"
        style={{ background: "#fff", borderBottom: "1px solid #e3ddd2" }}>
        <div className="relative max-w-6xl mx-auto text-center">
          <div className="overline mb-4" style={{ color: "#8a5a00" }}>The WAI Institute · Electrical Education & Credentials</div>
          <h2 style={{
            fontFamily: "'Cabinet Grotesk', 'Plus Jakarta Sans', sans-serif",
            fontSize: "clamp(1.9rem, 4.5vw, 3.2rem)", fontWeight: 900,
            color: "#111111", lineHeight: 1.1, margin: "0 0 1.25rem",
          }}>
            Ready to go deeper?
          </h2>
          <p style={{ fontSize: "clamp(1rem, 2vw, 1.2rem)", color: "#3f3a34", maxWidth: 640, margin: "0 auto 0.5rem", lineHeight: 1.6 }}>
            M.O.R.E. helps you <strong style={{ color: "#111111" }}>do</strong>. WAI Institute helps you become capable of doing more.
          </p>
          <p style={{ fontSize: "0.95rem", color: "#5a5045", maxWidth: 600, margin: "0 auto 2.25rem", lineHeight: 1.6 }}>
            Learn through structured education, develop verified skills, and build toward credentials through WAI Institute.
          </p>
          <Link to="/wai-institute"
            className="inline-flex items-center gap-2 font-black text-sm px-8 py-4 rounded-xl"
            style={{ background: "#8a5a00", color: "#fff", fontSize: 15 }}>
            Explore WAI Institute <ArrowRight size={16} />
          </Link>

          <div className="grid sm:grid-cols-3 gap-5 mt-16 text-left">
            {[
              { icon: "📘", title: "LEARN", desc: "Build real knowledge — structured electrical curriculum and AI Tutor guidance." },
              { icon: "🛠️", title: "DEVELOP", desc: "Turn knowledge into capability — labs, simulations, and verified skill practice." },
              { icon: "🎖️", title: "CREDENTIAL", desc: "Demonstrate what you know and can do — certificates and verified credentials." },
            ].map(({ icon, title, desc }) => (
              <div key={title}
                className="rounded-2xl p-6 border"
                style={{ borderColor: "#d9d0c4", background: "#fffdf8" }}>
                <div style={{ fontSize: 30, marginBottom: 10 }}>{icon}</div>
                <div style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontWeight: 900, fontSize: "0.95rem", letterSpacing: "0.18em", color: "#8a5a00", marginBottom: 6 }}>{title}</div>
                <div style={{ fontSize: "0.9rem", color: "#4a4238", lineHeight: 1.6 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── $3 TRIAL BANNER ──────────────────────────────────────────────── */}
      {!user && (
        <section className="py-16 px-6 border-y border-[#e3ddd2]" style={{ background: "#fff" }}>
          <div className="max-w-4xl mx-auto text-center">
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚡</div>
            <h2 style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "clamp(1.8rem,4vw,3rem)", fontWeight: 900, color: "#111111", marginBottom: 12 }}>
              Try the whole platform for{" "}
              <span style={{ color: "#8a5a00" }}>$3</span>
            </h2>
            <p style={{ color: "#4a4238", fontSize: "1.1rem", marginBottom: 32, lineHeight: 1.7 }}>
              3 days · 33 minutes · 33 seconds of full Pro access.<br />
              Every tool. Every course. Every AI feature. No recurring charge unless you choose a plan.
            </p>
            <Link to="/subscribe?plan=sanctuary_trial"
              className="inline-block font-black text-base px-10 py-4 rounded-xl"
              style={{ background: "#b8860b", color: "#111111" }}>
              Start My $3 Trial →
            </Link>
            <div className="mt-4">
              <Link to="/plans" style={{ color: "#5a5045", fontSize: 13, textDecoration: "none" }}>
                See all membership plans
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* ── VOICE OF MOVEMENT — VONN ─────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "#fff" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-copper mb-3">Hear the movement</div>
          <h2 className="font-heading font-black text-4xl text-ink mb-8">
            Voice of Movement = <span style={{ color: "#C96A35" }}>VONN</span>
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex justify-center">
              <iframe
                title="My Ole Kentucky Roots by VONN"
                className="w-full max-w-[350px]"
                style={{ border: 0, height: 442 }}
                src="https://bandcamp.com/EmbeddedPlayer/track=2837268270/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/transparent=true/"
                seamless
              >
                <a href="https://vonnsangs.bandcamp.com/track/my-ole-kentucky-roots">My Ole Kentucky Roots by VONN</a>
              </iframe>
            </div>
            <div className="flex justify-center">
              <iframe
                title="AM I Dreaming by VONN"
                className="w-full max-w-[350px]"
                style={{ border: 0, height: 442 }}
                src="https://bandcamp.com/EmbeddedPlayer/track=792480361/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/transparent=true/"
                seamless
              >
                <a href="https://vonnsangs.bandcamp.com/track/am-i-dreaming">AM I Dreaming by VONN</a>
              </iframe>
            </div>
          </div>
          <div className="mt-10 text-center">
            <a
              href="https://namoshun.gumroad.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block font-black text-sm px-8 py-3 rounded-xl"
              style={{ background: "#b8860b", color: "#111111" }}
            >
              NAM OSHUN's Gumroad Store →
            </a>
            <div className="mt-3 text-sm text-ink/50">namoshun.gumroad.com</div>
          </div>
        </div>
      </section>

      {/* ── MEMBERSHIP TIERS ─────────────────────────────────────────────── */}
      <section className="py-24 px-6" style={{ background: "#fff" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-copper mb-3 text-center">Membership</div>
          <h2 className="font-heading font-black text-4xl text-ink text-center mb-4">Start free.<br />Grow on your terms.</h2>
          <p className="text-ink/50 text-center mb-12 max-w-xl mx-auto">Every tier keeps the doors open for someone who can't pay yet.</p>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
            {[
              { name: "Free",    price: "$0",   color: "#6b7280", to: "/register",                              cta: "Start Free",      features: ["Community access", "Browse courses", "Daily XP puzzle"] },
              { name: "Member",  price: "$9",   color: "#3b82f6", to: "/subscribe?plan=member_monthly",       cta: "Choose Member — $9",  features: ["Full M.O.R.E.", "AI via your own key", "Creator basics"] },
              { name: "Plus",    price: "$15",  color: "#8b5cf6", to: "/subscribe?plan=plus_monthly",         cta: "Choose Plus — $15",   features: ["Ghost Producer", "Creator Studio", "Course selling"] },
              { name: "Pro",     price: "$29",  color: "#b5651d", to: "/subscribe?plan=pro_monthly",          cta: "Choose Pro — $29",    features: ["AI via your own key", "Advanced labs", "Earnings dashboard"], highlight: true },
              { name: "Patron",  price: "$59",  color: "#E8A51E", to: "/subscribe?plan=patron_monthly",       cta: "Become a Patron — $59", features: ["Founder's circle", "Fund free access", "Direct line"] },
            ].map(({ name, price, color, to, cta, features, highlight }) => (
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
                <Link to={to}
                  className="mt-4 w-full text-center text-xs font-black py-2.5 rounded-xl"
                  style={{ background: color, color: color === "#E8A51E" ? "#0a0a0a" : "#fff" }}>
                  {cta}
                </Link>
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
      <section className="py-24 px-6 border-t border-[#e3ddd2]"
        style={{ background: "#fff" }}>
        <div className="max-w-4xl mx-auto text-center">
          <img src={WAI_LOGO} alt="M.O.R.E." className="w-16 h-16 object-contain mx-auto mb-8" />
          <h2 style={{ fontFamily: "'Cabinet Grotesk',sans-serif", fontSize: "clamp(1.6rem,4vw,2.8rem)", fontWeight: 900, color: "#111111", lineHeight: 1.2, marginBottom: 20 }}>
            "{BRAND.tagline}"
          </h2>
          <p style={{ color: "#4a4238", fontSize: "1.05rem", lineHeight: 1.8, maxWidth: 560, margin: "0 auto 40px" }}>
            M.O.R.E. Help Center was built because the tools of the creator economy were never
            designed for us. We changed that. Every feature, every tier, every dollar
            — built to serve communities that were meant to be invisible.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/register"
              className="font-black text-sm px-8 py-3 rounded-xl"
              style={{ background: "#b8860b", color: "#111111" }}>
              Join the Movement
            </Link>
            <Link to="/donate"
              className="font-bold text-sm px-8 py-3 rounded-xl border"
              style={{ borderColor: "rgba(154,101,0,0.45)", color: "#7a4d00" }}
            >
              Make a Donation to the Mission
            </Link>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────────────────── */}
      <footer className="py-12 px-6 border-t border-[#e3ddd2]" style={{ background: "#fff", color: "#4a4238" }}>
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mb-8 pb-8 border-b border-[#e3ddd2]">
            <div className="flex items-center gap-3">
              <img src={WAI_LOGO} alt="M.O.R.E." className="w-8 h-8 object-contain" />
              <div>
                <div className="text-xs font-black uppercase tracking-widest text-copper">{BRAND.short}</div>
                <div className="font-heading font-bold text-sm text-ink">{BRAND.name}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-6 text-xs">
            {[["Plans", "/plans"], ["Creators", "/creators"], ["Courses", "/courses"], ["Community", "/community"], ["Helper", "/helper"], ["Store", "/store"]].map(([l, h]) => (
              <Link key={l} to={h} className="hover:text-copper transition-colors">{l}</Link>
            ))}
            {[
              ["WAI Institute Premium Services", "/premium"],
              ["Facebook Group", "https://www.facebook.com/groups/waiinstitute"],
              ["Donate", "/donate"],
              ["Privacy", "/privacy"],
              ["Terms", "/terms"],
              ["Refund Policy", "/refund-policy"],
            ].map(([l, h]) => (
              h.startsWith("http") ? (
                <a key={l} href={h} target="_blank" rel="noopener noreferrer" className="hover:text-copper transition-colors">{l}</a>
              ) : (
                <Link key={l} to={h} className="hover:text-copper transition-colors">{l}</Link>
              )
            ))}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
            <p>© {new Date().getFullYear()} {BRAND.legal}. All rights reserved.</p>
            <p style={{ color: "#5a5045" }}>{BRAND.mission}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

