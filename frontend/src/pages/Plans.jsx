import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { Check, Zap, Clock } from "lucide-react";

// Public membership plans — the corrected 5-tier monthly ladder ($0/9/15/29/59).
// Free tier is fully actionable (register); paid tiers route to the existing
// /subscribe checkout. Honest note below re: tier billing rollout (no dead ends,
// no fake checkout — every CTA goes somewhere real).
const PLANS = [
  {
    name: "Public",
    price: 0,
    tagline: "Explore freely",
    features: ["Free public resources", "Browse the M.O.R.E. community", "Daily puzzle — earn points", "One free basic course"],
    cta: "Start Free",
    to: "/register",
  },
  {
    name: "Member",
    price: 9,
    tagline: "Join in fully",
    features: ["Everything in Public", "Full M.O.R.E. — post & connect", "AI Tutor (standard)", "Member badge"],
    cta: "Choose Member",
    to: "/subscribe?plan=member_monthly",
  },
  {
    name: "Plus",
    price: 15,
    tagline: "More tools",
    features: ["Everything in Member", "Priority resource matching", "Expanded course library", "Portfolio tools"],
    cta: "Choose Plus",
    to: "/subscribe?plan=plus_monthly",
    highlight: true,
  },
  {
    name: "Pro",
    price: 29,
    tagline: "Go further",
    features: ["Everything in Plus", "Advanced courses + labs", "Full AI tools suite", "Mentor support hours"],
    cta: "Choose Pro",
    to: "/subscribe?plan=pro_monthly",
  },
  {
    name: "Patron",
    price: 59,
    tagline: "Fund the mission",
    features: ["Everything in Pro", "Founder's circle", "You fund free access for others", "Direct line to the team"],
    cta: "Become a Patron",
    to: "/subscribe?plan=patron_monthly",
  },
];

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
              <div className="text-white/70 text-sm">3 days · 33 minutes · 33 seconds of everything</div>
            </div>
          </div>
          <div className="flex-1 text-sm text-white/80 leading-relaxed">
            Unlock every feature on the platform — Creator Studio, Ghost Producer, AI tools, all courses — for one low trial price.
            No recurring charge unless you choose a plan after.
          </div>
          <Link to="/subscribe?plan=sanctuary_trial"
            className="shrink-0 font-black text-sm px-6 py-3 rounded-xl whitespace-nowrap"
            style={{ background: "#E8A51E", color: "#0a0a0a" }}>
            Try Everything for $3 →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-10">
          {PLANS.map((p) => (
            <div key={p.name} className={`card-flat p-6 flex flex-col ${p.highlight ? "border-copper" : ""}`}>
              {p.highlight && <span className="badge-copper self-start mb-2">Popular</span>}
              <div className="overline text-ink/40">{p.name}</div>
              <div className="flex items-end gap-1 mt-1">
                <span className="font-heading font-black text-4xl text-ink">${p.price}</span>
                <span className="text-ink/50 text-sm mb-1">/mo</span>
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

        <p className="text-xs text-ink/40 text-center mt-8 max-w-2xl mx-auto">
          Paid tiers are rolling out — at checkout you'll be guided to our current membership option while full monthly
          billing for every tier comes online. Program enrollees may qualify for complimentary membership.
        </p>
      </div>
    </div>
    </AppShell>
  );
}
