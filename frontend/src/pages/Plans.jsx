import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { MEMBERSHIP_PLANS } from "../lib/plans";
import { Check, Zap } from "lucide-react";
import PaymentsComingSoon, { usePaymentsEnabled } from "../components/PaymentsComingSoon";

/**
 * /plans — the five-level membership ladder (free/member/plus/pro/patron)
 * plus the $3 all-access trial. Every CTA routes to the real /subscribe
 * checkout for that exact product key — no dead ends. Creator perks
 * (course publishing, payouts, moderation) are built into the tiers above.
 */
export default function Plans() {
  const { user } = useAuth();
  const paymentsEnabled = usePaymentsEnabled();
  return (
    <AppShell>
    <div className="min-h-screen bg-bone">
      <div className="relative py-12 px-6"
        style={{ backgroundImage: "linear-gradient(rgba(10,10,15,0.74), rgba(10,10,15,0.84)), url('https://images.pexels.com/photos/8044096/pexels-photo-8044096.jpeg?auto=compress&cs=tinysrgb&w=1600')", backgroundSize: "cover", backgroundPosition: "center" }}>
        <div className="max-w-6xl mx-auto">
          <div className="overline text-signal">Join the Mission</div>
        </div>
      </div>
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

        <div className="max-w-4xl mx-auto mt-8">
          <PaymentsComingSoon context="memberships can't be purchased online yet" />
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
            Unlock everything through Pro — Creator Studio, Ghost Producer, every course, and AI-ready tools —
            for one low trial price. AI runs on your own key via the $3 BYOK unlock (the platform doesn't fund
            customer AI). It reverts automatically when the trial ends; no recurring charge unless you choose a plan after.
          </div>
          <Link to="/subscribe?plan=sanctuary_trial"
            className="shrink-0 font-black text-sm px-6 py-3 rounded-xl whitespace-nowrap"
            style={{ background: "#E8A51E", color: "#0a0a0a", opacity: paymentsEnabled ? 1 : 0.7 }}
            title={paymentsEnabled ? undefined : "Online payments are coming soon"}
          >
            {paymentsEnabled ? "Try Everything for $3 →" : "$3 Trial — Coming Soon →"}
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
                title={p.price === 0 || paymentsEnabled ? undefined : "Online payments are coming soon"}
              >
                {p.price === 0 || paymentsEnabled ? p.cta : `${p.cta} — Coming Soon`}
              </Link>
            </div>
          ))}
        </div>

        <p className="text-xs text-ink/40 text-center mt-8 max-w-2xl mx-auto">
          Creator perks — course publishing, creator payouts, advanced tools, and moderation rights — are built
          into the tiers above. Every tier is a real monthly subscription; the $3 trial never auto-charges and
          reverts when it ends. Program enrollees may qualify for complimentary membership.
        </p>
      </div>
    </div>
    </AppShell>
  );
}