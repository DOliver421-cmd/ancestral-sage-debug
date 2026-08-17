/**
 * plans.js — single source of truth for every purchasable plan.
 *
 * Both /plans and /subscribe render from this catalog, so the marketing copy
 * and the checkout flow can never drift apart again. Product keys here match
 * PAYMENT_PRODUCTS in backend/routers/payments.py — keep them in sync.
 *
 * Ladder (what a purchase grants as feature_tier):
 *   member_monthly      -> member
 *   plus_monthly        -> plus
 *   pro_monthly         -> pro
 *   patron_monthly      -> patron
 *   sanctuary_trial     -> pro (3 days . 33 min . 33 sec, then reverts)
 *   sanctuary_paid      -> member
 *   sanctuary_creator   -> plus
 *   sanctuary_mod       -> pro
 */

export const MEMBERSHIP_PLANS = [
  {
    key: "free",
    name: "Public",
    price: 0,
    period: "/mo",
    tagline: "Explore freely",
    features: [
      "Free public resources",
      "Browse the M.O.R.E. community",
      "Daily puzzle — earn points",
      "One free basic course",
    ],
    cta: "Start Free",
    to: "/register",
  },
  {
    key: "member_monthly",
    name: "Member",
    price: 9,
    period: "/mo",
    tagline: "Join in fully",
    color: "#94a3b8",
    features: [
      "Everything in Public",
      "Full M.O.R.E. — post & connect",
      "AI Tutor (standard)",
      "Member badge",
      "Cancel anytime",
    ],
    cta: "Choose Member",
    to: "/subscribe?plan=member_monthly",
  },
  {
    key: "plus_monthly",
    name: "Plus",
    price: 15,
    period: "/mo",
    tagline: "More tools",
    color: "#d4af37",
    features: [
      "Everything in Member",
      "Priority resource matching",
      "Expanded course library",
      "Portfolio tools",
    ],
    cta: "Choose Plus",
    to: "/subscribe?plan=plus_monthly",
    highlight: true,
  },
  {
    key: "pro_monthly",
    name: "Pro",
    price: 29,
    period: "/mo",
    tagline: "Go further",
    color: "#4ade80",
    features: [
      "Everything in Plus",
      "Advanced courses + labs",
      "Full AI tools suite",
      "Mentor support hours",
    ],
    cta: "Choose Pro",
    to: "/subscribe?plan=pro_monthly",
  },
  {
    key: "patron_monthly",
    name: "Patron",
    price: 59,
    period: "/mo",
    tagline: "Fund the mission",
    color: "#f97316",
    features: [
      "Everything in Pro",
      "Founder's circle",
      "You fund free access for others",
      "Direct line to the team",
    ],
    cta: "Become a Patron",
    to: "/subscribe?plan=patron_monthly",
  },
];

// Creator's Sanctuary — creator-focused tiers. Each grants the matching
// membership level (so creator perks sit on top of a real membership) plus
// creator privileges: higher payouts, course publishing, moderation rights.
export const CREATOR_PLANS = [
  {
    key: "sanctuary_trial",
    name: "3-Day All-Access Trial",
    price: "$3",
    period: " once",
    tagline: "Everything through the Pro level",
    features: [
      "Every tool in Pro unlocked",
      "3 days · 33 min · 33 sec",
      "No auto-charge unless you choose a plan",
      "Reverts automatically after the trial",
    ],
    to: "/subscribe?plan=sanctuary_trial",
    trial: true,
  },
  {
    key: "sanctuary_paid",
    name: "Paid Creator",
    price: "$7",
    period: "/mo",
    tagline: "Member-level creator lane",
    features: [
      "Full Sanctuary access",
      "Course publishing",
      "90% payout on tips & courses",
      "Cancel anytime",
    ],
    to: "/subscribe?plan=sanctuary_paid",
  },
  {
    key: "sanctuary_creator",
    name: "Advanced Creator",
    price: "$11",
    period: "/mo",
    tagline: "Plus-level creator lane",
    features: [
      "Everything in Paid Creator",
      "Advanced tools suite",
      "80% payout rate",
      "Priority support",
    ],
    to: "/subscribe?plan=sanctuary_creator",
  },
  {
    key: "sanctuary_mod",
    name: "Certified Moderator",
    price: "$15",
    period: "/mo",
    tagline: "Pro-level creator lane",
    features: [
      "Everything in Advanced Creator",
      "Moderator privileges",
      "85% payout + 1.5% mod bonus",
      "Governance voting rights",
    ],
    to: "/subscribe?plan=sanctuary_mod",
  },
];

// Everything purchasable on the single /subscribe -> checkout flow.
export const ALL_PLANS = [...MEMBERSHIP_PLANS, ...CREATOR_PLANS];

/** Look up any plan (membership or creator lane) by product key. */
export function planByKey(key) {
  return ALL_PLANS.find((p) => p.key === key) || null;
}

/** The tier a product key grants (mirrors backend _PRODUCT_TIER_MAP). */
export function tierForPlanKey(key) {
  const map = {
    member_monthly: "member",
    plus_monthly: "plus",
    pro_monthly: "pro",
    patron_monthly: "patron",
    sanctuary_trial: "pro",
    sanctuary_paid: "member",
    sanctuary_creator: "plus",
    sanctuary_mod: "pro",
  };
  return map[key] || "free";
}