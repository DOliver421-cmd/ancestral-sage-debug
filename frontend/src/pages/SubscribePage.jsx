import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { HandHelping, CheckCircle, ExternalLink, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

const MORE_PLANS = [
  {
    key: "more_monthly",
    label: "Monthly",
    price: "$9.99",
    period: "/month",
    features: [
      "Full M.O.R.E. community access",
      "Post needs & connect with helpers",
      "AI-guided resource matching",
      "Cancel anytime",
    ],
  },
  {
    key: "more_annual",
    label: "Annual",
    price: "$79.99",
    period: "/year",
    badge: "Save 33%",
    features: [
      "Everything in Monthly",
      "Priority community support",
      "Annual member badge",
      "Best value",
    ],
  },
];

const TIER_PLANS = {
  member_monthly:  { name: "Member",  price: "$9",  period: "/mo", color: "border-ink/20",    features: ["Full M.O.R.E. — post & connect", "AI Tutor (standard)", "Member badge", "Cancel anytime"] },
  plus_monthly:    { name: "Plus",    price: "$15", period: "/mo", color: "border-copper",    features: ["Everything in Member", "Priority resource matching", "Expanded course library", "Portfolio tools"] },
  pro_monthly:     { name: "Pro",     price: "$29", period: "/mo", color: "border-signal",    features: ["Everything in Plus", "Advanced courses + labs", "Full AI tools suite", "Mentor support hours"] },
  patron_monthly:  { name: "Patron",  price: "$59", period: "/mo", color: "border-amber-500", features: ["Everything in Pro", "Founder's circle", "You fund free access for others", "Direct line to the team"] },
};

export default function SubscribePage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);

  const planParam = searchParams.get("plan");
  const tierPlan = planParam && TIER_PLANS[planParam] ? { key: planParam, ...TIER_PLANS[planParam] } : null;

  const isAlreadyMember = user?.more_member;

  async function subscribe(key) {
    setLoading(key);
    try {
      const { data } = await api.post("/payments/checkout", { product_key: key, quantity: 1 });
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start checkout.");
      setLoading(null);
    }
  }

  async function openPortal() {
    setPortalLoading(true);
    try {
      const { data } = await api.get("/payments/portal");
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "No billing account found. Complete a purchase first.");
      setPortalLoading(false);
    }
  }

  // ── Tier-specific view (coming from Plans.jsx with ?plan=xxx) ───────────
  if (tierPlan) {
    return (
      <div className="p-8 max-w-lg mx-auto">
        <Link to="/plans" className="inline-flex items-center gap-1.5 text-sm text-ink/50 hover:text-ink mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to plans
        </Link>
        <div className={`bg-white border-2 rounded-2xl p-8 shadow-sm ${tierPlan.color}`}>
          <div className="overline text-ink/40 mb-1">WAI Institute — {tierPlan.name} Tier</div>
          <div className="flex items-end gap-1 mb-1">
            <span className="font-heading font-black text-5xl text-ink">{tierPlan.price}</span>
            <span className="text-ink/50 text-sm mb-2">{tierPlan.period}</span>
          </div>
          <ul className="space-y-3 my-6">
            {tierPlan.features.map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm text-ink/80">
                <CheckCircle className="w-4 h-4 text-copper shrink-0" /> {f}
              </li>
            ))}
          </ul>
          <button
            onClick={() => subscribe(tierPlan.key)}
            disabled={!!loading}
            className="w-full py-4 text-sm font-bold rounded-xl btn-copper disabled:opacity-50"
          >
            {loading === tierPlan.key ? "Redirecting to checkout…" : `Start ${tierPlan.name} — ${tierPlan.price}${tierPlan.period}`}
          </button>
          <p className="text-xs text-ink/40 text-center mt-4">
            Secure checkout via Stripe. Cancel anytime from your account.
          </p>
        </div>
      </div>
    );
  }

  // ── Default M.O.R.E. membership view ─────────────────────────────────────
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <HandHelping className="w-8 h-8 text-signal" />
        <h1 className="font-heading text-3xl font-bold text-ink">M.O.R.E. Membership</h1>
      </div>
      <p className="text-ink/60 mb-8 max-w-xl">
        M.O.R.E. (Michael Oliver Resource Exchange) connects learners and community members
        with real support — housing, legal help, tools, and more. Membership funds the platform and
        keeps it free for those who need it most.
      </p>

      {isAlreadyMember && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3 mb-8">
          <CheckCircle className="w-5 h-5 text-green-600 shrink-0" />
          <div>
            <div className="font-semibold text-green-800">You're an active M.O.R.E. member</div>
            <div className="text-green-700 text-sm">Manage or cancel your subscription below.</div>
          </div>
          <button
            onClick={openPortal}
            disabled={portalLoading}
            className="ml-auto flex items-center gap-2 px-4 py-2 border border-green-400 text-green-700 text-sm font-bold rounded-lg hover:bg-green-100 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            {portalLoading ? "Loading…" : "Manage Subscription"}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {MORE_PLANS.map((plan) => (
          <div key={plan.key}
            className={`relative bg-white border-2 rounded-2xl p-6 flex flex-col gap-4 shadow-sm ${plan.key === "more_annual" ? "border-signal" : "border-ink/10"}`}
          >
            {plan.badge && (
              <span className="absolute top-4 right-4 bg-signal text-ink text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest">
                {plan.badge}
              </span>
            )}
            <div>
              <div className="text-xs font-black uppercase tracking-widest text-ink/40 mb-1">{plan.label}</div>
              <div className="flex items-end gap-1">
                <span className="font-heading font-bold text-4xl text-ink">{plan.price}</span>
                <span className="text-ink/50 text-sm mb-1">{plan.period}</span>
              </div>
            </div>
            <ul className="space-y-2 flex-1">
              {plan.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-ink/80">
                  <CheckCircle className="w-4 h-4 text-signal shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => subscribe(plan.key)}
              disabled={!!loading}
              className={`w-full py-3 text-sm font-bold rounded-lg transition-colors disabled:opacity-50 ${
                plan.key === "more_annual"
                  ? "bg-signal text-ink hover:bg-signal/80"
                  : "bg-ink text-white hover:bg-ink/80"
              }`}
            >
              {loading === plan.key ? "Redirecting…" : isAlreadyMember ? "Switch Plan" : "Subscribe"}
            </button>
          </div>
        ))}
      </div>

      {!isAlreadyMember && (
        <p className="text-xs text-ink/40 text-center mt-6">
          Program enrollees may qualify for complimentary membership — contact your instructor.
        </p>
      )}

      {isAlreadyMember || (
        <div className="mt-6 text-center">
          <button
            onClick={openPortal}
            disabled={portalLoading}
            className="text-sm text-ink/50 underline hover:text-ink transition-colors"
          >
            {portalLoading ? "Loading…" : "Manage existing subscription"}
          </button>
        </div>
      )}
    </div>
  );
}
