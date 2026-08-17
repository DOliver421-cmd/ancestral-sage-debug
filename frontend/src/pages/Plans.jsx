import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { MEMBERSHIP_PLANS, CREATOR_PLANS } from "../lib/plans";
import { Check, Zap, Crown } from "lucide-react";

/**
 * /plans — the five-level membership ladder (free/member/plus/pro/patron),
 * the $3 trial, and the Creator's Sanctuary lane. Every CTA routes to the
 * real /subscribe checkout for that exact product key — no dead ends.
 */
export default function Plans() {
  const { user } = useAuth();
  return (
    <AppShell>
    <div className="min-h-screen bg-bone">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <BackButton to={user ? "/dashboard" : "/"} />

        <div className="mt-6 text-center">
          <div className="overline text-copper">Membership</div>
          <h1 className="font-heading text-4xl font-bold text-ink mt-2">Choose your level of partnership</h1>
          <p className="text-ink/60 mt-3 max-w-2xl mx-auto">
            Start free and earn your way up — or become a member and help fund the mission. Every tier keeps the doors
            open for someone who can't pay yet.
          </p>
        </div>

        {/* ── $3 Trial Banner ── highest conversion CTA, shown first ── */}
        <div className="mt-8 rounded-2xl p-6 flex flex-col sm:flex-row items-center gap-5"
          style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "2px solid #E8A51E" }}>
          <div className="flex items-center gap-3 shrink-0">
            <span style={{ fontSize: 36 }}>⚡</span>
            <div>
              <div className="font-heading font-black text-2xl text-signal">$3 All-Access Trial</div>
              <div className="text-white/70 text-sm">3 days · 33 minutes · 33 seconds</div>
            </div>
          </div>
          <div className="flex-1 text-sm text-white/80 leading-relaxed">
            Unlock everything through Pro — Creator Studio, Ghost Producer, the full AI suite, and every course —
            for one low trial price. It reverts automatically when the trial ends; no recurring charge unless you
            choose a plan after.
          </div>
          <Link to="/subscribe?plan=sanctuary_trial"
            className="shrink-0 font-black text-sm px-6 py-3 rounded-xl whitespace-nowrap"
            style={{ background: "#E8A51E", color: "#0a0a0a" }}>
            Try Everything for $3 →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-10">
          {MEMBERSHIP_PLANS.map((p) => (
            <div key={p.key} className={`card-flat p-6 flex flex-col ${p.highlight ? "border-copper" : ""}`}>
              {p.highlight && <span className="badge-copper self-start mb-2">Popular</span>}
              <div className="overline text-ink/40">{p.name}</div>
              <div className="flex items-end gap-1 mt-1">
                <span className="font-heading font-black text-4xl text-ink">${p.price}</span>
                <span className="text-ink/50 text-sm mb-1">{p.period}</span>
              </div>
              <div className="text-sm text-ink/60 mt-1">{p.tagline}</div>
              <ul className="space-y-2 mt-4 flex-1">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-ink/80">
                    <Check className="w-4 h-4 text-copper mt-0.5 shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <Link
                to={p.to}
                data-testid={`plan-${p.name.toLowerCase()}`}
                className={`mt-5 text-center text-sm ${p.price === 0 ? "btn-primary" : "btn-copper"}`}
              >
                {p.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* ── Creator's Sanctuary ── */}
        <div className="mt-14 rounded-2xl p-8"
          style={{ background: "linear-gradient(160deg,#14101f,#0d0818)", border: "1px solid rgba(168,85,247,0.25)" }}>
          <div className="flex items-center gap-2.5 mb-1">
            <Crown className="w-5 h-5 text-purple-400" />
            <h2 className="font-heading font-black text-2xl" style={{ color: "#d8b4fe" }}>Creator's Sanctuary</h2>
          </div>
          <p className="text-sm text-white/60 max-w-2xl">
            Specialized creator lanes — each includes the matching membership level plus higher payouts,
            course publishing, advanced tools, and moderation rights.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            {CREATOR_PLANS.map((p) => (
              <div key={p.key} className="rounded-2xl p-5 flex flex-col"
                style={{ background: "rgba(168,85,247,0.07)", border: "1px solid rgba(168,85,247,0.25)" }}>
                {p.trial ? (
                  <span className="self-start text-[10px] font-black tracking-widest uppercase px-2 py-1 rounded-full mb-2"
                    style={{ background: "rgba(232,165,30,0.15)", color: "#E8A51E", border: "1px solid rgba(232,165,30,0.4)" }}>
                    ⚡ Best value
                  </span>
                ) : (
                  <span className="self-start text-[10px] font-bold tracking-widest uppercase text-white/40 mb-2">
                    {p.name.includes("Certified") ? "Moderation lane" : "Creator lane"}
                  </span>
                )}
                <div className="font-heading font-bold text-lg text-white">{p.name}</div>
                <div className="flex items-end gap-1 mt-1">
                  <span className="font-heading font-black text-3xl text-white">{p.price}</span>
                  <span className="text-white/40 text-sm mb-1">{p.period}</span>
                </div>
                <div className="text-xs text-white/50 mt-1">{p.tagline}</div>
                <ul className="space-y-2 mt-4 flex-1">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-xs text-white/75">
                      <Check className="w-3.5 h-3.5 text-purple-400 mt-0.5 shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to={p.to}
                  className="mt-5 text-center text-sm font-black py-2.5 rounded-xl"
                  style={p.trial
                    ? { background: "#E8A51E", color: "#0a0a0a" }
                    : { background: "rgba(168,85,247,0.15)", color: "#c4b5fd", border: "1px solid rgba(168,85,247,0.4)" }}
                >
                  {p.trial ? "Start $3 Trial" : `Choose ${p.name}`}
                </Link>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-ink/40 text-center mt-8 max-w-2xl mx-auto">
          Every tier above is a real monthly subscription. The $3 trial never auto-charges and reverts when it ends.
          Program enrollees may qualify for complimentary membership.
        </p>
      </div>
    </div>
    </AppShell>
  );
}