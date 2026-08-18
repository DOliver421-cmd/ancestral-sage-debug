import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { MEMBERSHIP_PLANS, TRIAL_PLAN, planByKey } from "../lib/plans";
import { tierRank } from "../lib/tiers";
import { CheckCircle, ExternalLink, ArrowLeft, Zap } from "lucide-react";
import { toast } from "sonner";

function priceLabel(price) {
  return typeof price === "number" ? `$${price}` : price;
}

export default function SubscribePage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);

  const planParam = searchParams.get("plan");
  const sanctuaryPlan = planParam && TRIAL_PLAN.key === planParam ? planByKey(planParam) : null;
  const tierPlan = planParam && !sanctuaryPlan
    ? MEMBERSHIP_PLANS.find(p => p.key === planParam) || null
    : null;

  async function subscribe(key) {
    if (!user) { toast.error("Sign in to subscribe"); return; }
    setLoading(key);
    try {
      const { data } = await api.post("/payments/checkout", { product_key: key, quantity: 1 });
      window.location.href = data.url;
    } catch (e) {
      const detail = e?.response?.data?.detail || "";
      // Payments not configured yet (no Lemon Squeezy / Gumroad API keys):
      // don't leave the visitor at a dead 501 — route them to the live
      // storefront so the purchase can actually happen.
      if (
        e?.response?.status === 501 ||
        /not configured|payments are not configured/i.test(String(detail))
      ) {
        toast.info("Checkout is being set up — redirected to our live storefront.");
        window.location.href = "/merch";
        return;
      }
      toast.error(detail || "Could not start checkout.");
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

  /* ── Single-plan checkout view ── */
  if (sanctuaryPlan || tierPlan) {
    const plan = sanctuaryPlan || tierPlan;
    const isTrial = plan.key === "sanctuary_trial";
    return (
      <AppShell>
        <div style={{ background: "#08060f", minHeight: "100vh", padding: "48px 24px" }}>
          <div style={{ maxWidth: 480, margin: "0 auto" }}>
            <Link to="/plans" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13, color: "#6b6480", marginBottom: 32, textDecoration: "none" }}>
              <ArrowLeft size={14} /> Back to plans
            </Link>

            {isTrial && (
              <div style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "2px solid #E8A51E", borderRadius: 16, padding: "16px 20px", marginBottom: 24, display: "flex", alignItems: "center", gap: 12 }}>
                <Zap size={20} style={{ color: "#E8A51E", flexShrink: 0 }} />
                <div style={{ fontSize: 13, color: "rgba(255,255,255,0.85)", lineHeight: 1.5 }}>
                  <strong style={{ color: "#E8A51E" }}>$3 All-Access Trial</strong> — everything through Pro for 3 days, 33 minutes, 33 seconds. It reverts automatically; no recurring charge unless you choose a plan after.
                </div>
              </div>
            )}

            <div style={{ background: "#100e1a", border: "1.5px solid rgba(255,255,255,0.1)", borderRadius: 18, padding: 32 }}>
              <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: "#6b6480", marginBottom: 8 }}>
                M.O.R.E. Help Center — {plan.name}
              </div>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 4, marginBottom: 24 }}>
                <span style={{ fontFamily: "monospace", fontSize: "3rem", fontWeight: 900, color: "#e0d8f0", lineHeight: 1 }}>
                  {priceLabel(plan.price)}
                </span>
                <span style={{ fontSize: 13, color: "#6b6480", marginBottom: 8 }}>{plan.period}</span>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: "0 0 28px", display: "flex", flexDirection: "column", gap: 12 }}>
                {plan.features.map(f => (
                  <li key={f} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: "#c4b5fd" }}>
                    <CheckCircle size={15} style={{ color: "#d4af37", flexShrink: 0 }} /> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => subscribe(plan.key)}
                disabled={!!loading}
                style={{
                  width: "100%", padding: "16px", border: "none", borderRadius: 12,
                  background: isTrial ? "#E8A51E" : "linear-gradient(135deg,#7c3aed,#6d28d9)",
                  color: isTrial ? "#0a0a0a" : "#fff",
                  fontSize: 15, fontWeight: 900, fontFamily: "monospace", letterSpacing: "0.06em",
                  cursor: loading ? "default" : "pointer", opacity: loading ? 0.6 : 1,
                }}
              >
                {loading === plan.key
                  ? "Redirecting to checkout…"
                  : isTrial
                    ? "Start $3 Trial →"
                    : `Subscribe — ${priceLabel(plan.price)}${plan.period}`}
              </button>
              <p style={{ fontSize: 11, color: "#6b6480", textAlign: "center", marginTop: 14 }}>
                Manage or cancel anytime from your account.
              </p>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  /* ── Full membership page ── */
  const currentTier = user?.feature_tier || "free";
  const isActiveMember = tierRank(currentTier) > 0 || user?.more_member;

  return (
    <AppShell>
      <div style={{ background: "#08060f", minHeight: "100vh", color: "#e0d8f0" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 24px 80px" }}>

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div style={{ fontSize: "0.65rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.15em", color: "#d4af37", marginBottom: 10 }}>
              M.O.R.E. Help Center Membership
            </div>
            <h1 style={{ fontFamily: "monospace", fontSize: "clamp(1.8rem,4vw,3rem)", fontWeight: 900, color: "#e0d8f0", margin: "0 0 12px", lineHeight: 1.1 }}>
              Choose your level of partnership
            </h1>
            <p style={{ color: "#6b6480", fontSize: 15, maxWidth: 560, margin: "0 auto", lineHeight: 1.7 }}>
              Start free and earn your way up — or become a member and help fund the mission. Every tier keeps the doors open for someone who can't pay yet.
            </p>
          </div>

          {/* $3 Trial banner */}
          <div style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "2px solid #E8A51E", borderRadius: 18, padding: "20px 28px", display: "flex", flexWrap: "wrap", alignItems: "center", gap: 20, marginBottom: 40 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, flexShrink: 0 }}>
              <span style={{ fontSize: 36 }}>⚡</span>
              <div>
                <div style={{ fontFamily: "monospace", fontWeight: 900, fontSize: "1.4rem", color: "#E8A51E" }}>$3 All-Access Trial</div>
                <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 12 }}>3 days · 33 minutes · 33 seconds</div>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 200, fontSize: 13, color: "rgba(255,255,255,0.75)", lineHeight: 1.6 }}>
              Everything through Pro — Creator Studio, Ghost Producer, the full AI suite, and every course — for one low trial price. It reverts automatically when the trial ends; no recurring charge unless you choose a plan.
            </div>
            <button
              onClick={() => subscribe("sanctuary_trial")}
              disabled={!!loading}
              style={{ flexShrink: 0, background: "#E8A51E", color: "#0a0a0a", border: "none", borderRadius: 12, padding: "12px 24px", fontFamily: "monospace", fontWeight: 900, fontSize: 14, cursor: "pointer" }}
            >
              {loading === "sanctuary_trial" ? "Redirecting…" : "Try Everything for $3 →"}
            </button>
          </div>

          {/* Active member banner */}
          {isActiveMember && (
            <div style={{ background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.3)", borderRadius: 14, padding: "16px 22px", display: "flex", alignItems: "center", gap: 14, marginBottom: 32 }}>
              <CheckCircle size={20} style={{ color: "#4ade80", flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: "#4ade80" }}>
                  {currentTier === "free" ? "You're in the M.O.R.E. community" : `You're a member — ${currentTier} tier`}
                </div>
                <div style={{ fontSize: 13, color: "#6b6480" }}>Upgrade, downgrade, or manage billing below.</div>
              </div>
              <button
                onClick={openPortal}
                disabled={portalLoading}
                style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 18px", background: "transparent", border: "1px solid rgba(74,222,128,0.4)", borderRadius: 10, color: "#4ade80", fontSize: 13, fontWeight: 700, cursor: "pointer" }}
              >
                <ExternalLink size={13} /> {portalLoading ? "Loading…" : "Manage Subscription"}
              </button>
            </div>
          )}

          {/* 5-tier grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 48 }}>
            {MEMBERSHIP_PLANS.filter(p => p.key !== "free").map(plan => {
              const isCurrent = currentTier === plan.key.replace("_monthly", "");
              return (
                <div key={plan.key} style={{
                  background: plan.highlight ? "linear-gradient(160deg,#1a0e30,#0d0818)" : "#100e1a",
                  border: `1.5px solid ${plan.highlight ? plan.color + "60" : "rgba(255,255,255,0.08)"}`,
                  borderRadius: 16, padding: "24px 20px",
                  display: "flex", flexDirection: "column",
                  boxShadow: plan.highlight ? `0 0 30px ${plan.color}15` : "none",
                  position: "relative",
                }}>
                  {plan.highlight && (
                    <span style={{ position: "absolute", top: -10, left: "50%", transform: "translateX(-50%)", background: plan.color, color: "#0a0a0a", fontSize: 10, fontWeight: 900, fontFamily: "monospace", padding: "3px 12px", borderRadius: 99, whiteSpace: "nowrap" }}>
                      MOST POPULAR
                    </span>
                  )}
                  {isCurrent && (
                    <span style={{ position: "absolute", top: 12, right: 12, background: "rgba(74,222,128,0.15)", border: "1px solid rgba(74,222,128,0.4)", color: "#4ade80", fontSize: 9, fontWeight: 700, fontFamily: "monospace", padding: "2px 8px", borderRadius: 99 }}>
                      CURRENT
                    </span>
                  )}
                  <div style={{ fontSize: "0.6rem", fontFamily: "monospace", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: plan.color, marginBottom: 6 }}>
                    {plan.name}
                  </div>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 4, marginBottom: 4 }}>
                    <span style={{ fontFamily: "monospace", fontSize: "2.2rem", fontWeight: 900, color: "#e0d8f0", lineHeight: 1 }}>${plan.price}</span>
                    <span style={{ fontSize: 12, color: "#6b6480", marginBottom: 6 }}>{plan.period}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#6b6480", marginBottom: 16 }}>{plan.tagline}</div>
                  <ul style={{ listStyle: "none", padding: 0, margin: "0 0 20px", flex: 1, display: "flex", flexDirection: "column", gap: 9 }}>
                    {plan.features.map(f => (
                      <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 12, color: "#c4b5fd", lineHeight: 1.4 }}>
                        <CheckCircle size={12} style={{ color: plan.color, flexShrink: 0, marginTop: 1 }} /> {f}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => subscribe(plan.key)}
                    disabled={!!loading || isCurrent}
                    style={{
                      width: "100%", padding: "11px", border: `1.5px solid ${plan.color}60`,
                      borderRadius: 10, background: plan.highlight ? `${plan.color}20` : "transparent",
                      color: plan.color, fontSize: 12, fontWeight: 900, fontFamily: "monospace",
                      letterSpacing: "0.06em", cursor: isCurrent ? "default" : "pointer",
                      opacity: (loading && loading !== plan.key) || isCurrent ? 0.5 : 1,
                    }}
                  >
                    {isCurrent ? "Current Plan" : loading === plan.key ? "Redirecting…" : `Choose ${plan.name}`}
                  </button>
                </div>
              );
            })}
          </div>


          {/* Footer */}
          <div style={{ textAlign: "center" }}>
            <button
              onClick={openPortal}
              disabled={portalLoading}
              style={{ background: "none", border: "none", color: "#6b6480", fontSize: 13, cursor: "pointer", textDecoration: "underline" }}
            >
              {portalLoading ? "Loading…" : "Manage existing subscription"}
            </button>
            <p style={{ fontSize: 11, color: "#6b6480", marginTop: 12 }}>
              Every tier above is a real monthly subscription. The $3 trial never auto-charges and reverts when it ends.
              Program enrollees may qualify for complimentary membership.
            </p>
          </div>

        </div>
      </div>
    </AppShell>
  );
}