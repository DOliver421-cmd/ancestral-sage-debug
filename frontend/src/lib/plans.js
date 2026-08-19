/**
 * plans.js — single source of truth for every purchasable plan.
 *
 * Both /plans and /subscribe render from this catalog, so the marketing copy
 * and the checkout flow can never drift apart again. Product keys here match
 * PAYMENT_PRODUCTS in backend/routers/payments.py — keep them in sync.
 *
 * The old "M.O.R.E. Creators" lanes (sanctuary_paid / sanctuary_creator /
 * sanctuary_mod) have been FOLDED into the main ladder: their creator perks
 * (course publishing, payouts, advanced tools, moderation rights) now sit on
 * the matching basic tiers below. Those product keys remain server-side as
 * deprecated items so existing subscribers' renewals keep granting tier.
 *
 * Ladder (what a purchase grants as feature_tier):
 *   member_monthly      -> member
 *   plus_monthly        -> plus
 *   pro_monthly         -> pro
 *   patron_monthly      -> patron
 *   sanctuary_trial     -> pro (3 days . 33 min . 33 sec, then reverts)
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
    tagline: "More tools, more reach",
    color: "#d4af37",
    features: [
      "Everything in Member",
      "Priority resource matching",
      "Course publishing + creator payouts (90%)",
      "Expanded course library & portfolio tools",
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
      "Advanced creator tools & priority support",
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
      "Moderator privileges & governance voting",
      "You fund free access for others",
      "Direct line to the team",
    ],
    cta: "Become a Patron",
    to: "/subscribe?plan=patron_monthly",
  },
];

// The $3 entry point — full access through the Pro tier for a short window.
// It grants feature_tier "pro" with a 3 days . 33 min . 33 sec clock, then
// reverts to the user's previous tier (backend routers/payments.py).
export const TRIAL_PLAN = {
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
};

// Everything purchasable on the single /subscribe -> checkout flow.
export const ALL_PLANS = [...MEMBERSHIP_PLANS, TRIAL_PLAN];

/** Look up any plan (membership or trial) by product key. */
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
  };
  return map[key] || "free";
}