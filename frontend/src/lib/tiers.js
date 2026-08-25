/**
 * tiers.js — THE single authority for what each membership level unlocks.
 *
 * Ladder:  free(0) → member(1) → plus(2) → pro(3) → patron(4) → platinum(5) → executive(6)
 *
 * feature_tier is granted automatically by the payment webhook (backend
 * routers/payments.py) and can be overridden by admins via the Exec panel.
 * Admins / executive admins bypass every gate; instructors get course/track
 * access regardless of tier. Keep this in sync with `canAccess` semantics —
 * this module is the frontend half of that contract.
 */

import { Link } from "react-router-dom";
import { useAuth } from "./auth";
import { Lock } from "lucide-react";

export const FEATURE_TIER_RANK = {
  free: 0,
  member: 1,
  plus: 2,
  pro: 3,
  patron: 4,
  platinum: 5,
  executive: 6,
};

export const FEATURE_TIER_LABEL = {
  free: "Free",
  member: "Member",
  plus: "Plus",
  pro: "Pro",
  patron: "Patron",
  platinum: "Platinum",
  executive: "Executive",
};

// Feature key → minimum tier name required. Instructors get course/tracks
// regardless of tier (they teach, they get access).
export const TIER_FOR_FEATURE = {
  profile: "free",        // your own profile / basics
  ai_chat: "free",        // AI Tutor (standard)
  posts: "member",        // community
  publisher_ai: "member", // AI-assisted publishing (Social Blast)
  lounge: "member",       // creator lounge / community
  projects: "member",     // "Have your M.O.R.E. team work on it"
  courses: "plus",        // course library
  tracks: "plus",         // learning tracks / adaptive path
  ghost: "plus",          // Ghost Producer
  studio: "plus",         // Creator Studio
  band: "plus",           // Band on a Page
  publisher: "plus",      // full publishing toolkit
  earnings: "plus",       // creator earnings
  payouts: "plus",        // creator payouts
  artist_mgmt: "pro",     // artist management
  mass_post: "patron",    // mass posting
  sovereign: "executive", // platform control - admin/exec role only (bypass above)
};

const FEATURE_INSTRUCTOR_BYPASS = new Set(["courses", "tracks"]);

export function tierRank(tier) {
  return FEATURE_TIER_RANK[tier] ?? 0;
}

export function tierLabel(tier) {
  return FEATURE_TIER_LABEL[tier] || "Free";
}

/**
 * canAccess(user, feature) — true when the user's tier (or role) covers the
 * feature. Mirrors the old UnifiedProfile gate; kept here so every page and
 * route checks the same rule.
 */
export function canAccess(user, feature) {
  if (!user) return false;
  const role = user.role || "student";
  if (role === "admin" || role === "executive_admin") return true;

  const required = TIER_FOR_FEATURE[feature];
  if (!required) return false;
  if (FEATURE_INSTRUCTOR_BYPASS.has(feature) && role === "instructor") return true;

  return tierRank(user.feature_tier) >= tierRank(required);
}

export function minTierForFeature(feature) {
  return TIER_FOR_FEATURE[feature] || "free";
}

/**
 * TierGate — wraps a page/route and renders an upgrade card instead of the
 * children when the user's tier doesn't cover `feature`. Every CTA leads to a
 * real place: the exact tier checkout, the plans page, or the $3 trial.
 */
export function TierGate({ feature, title, children }) {
  const { user, loading } = useAuth();
  const required = minTierForFeature(feature);

  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (canAccess(user, feature)) return children;

  const hasUser = !!user;
  const requiredLabel = FEATURE_TIER_LABEL[required] || required;
  const checkoutLink = `/subscribe?plan=${required}_monthly`;
  const tierPrice = required === "member" ? "$9/mo" : required === "plus" ? "$15/mo" : required === "pro" ? "$29/mo" : "$59/mo";

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-6 py-16">
      <div className="max-w-md w-full card-flat rounded-3xl p-8 text-center border-2"
        style={{ borderColor: "rgba(232,165,30,0.35)", background: "linear-gradient(180deg,#ffffff 0%,#fdfbf5 100%)" }}>
        <div className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
          <Lock className="w-6 h-6" style={{ color: "#E8A51E" }} />
        </div>
        <h1 className="font-heading text-2xl font-bold text-ink mt-5">
          {title || "This is a paid feature"}
        </h1>
        <p className="text-ink/60 text-sm mt-3 leading-relaxed">
          {hasUser
            ? `${requiredLabel} membership unlocks this — plus everything below it. Try it first for $3, or go straight to plans.`
            : `Sign in to unlock ${requiredLabel} membership and everything below it.`}
        </p>

        <div className="mt-6 flex flex-col gap-2.5">
          <Link
            to={hasUser ? checkoutLink : "/register"}
            className="btn-copper w-full text-center text-sm font-black py-3 rounded-xl"
          >
            {hasUser ? `Upgrade to ${requiredLabel} — ${tierPrice}` : "Create a free account"}
          </Link>
          <Link
            to="/subscribe?plan=sanctuary_trial"
            className="w-full text-center text-sm font-bold py-3 rounded-xl"
            style={{ background: "#E8A51E", color: "#0a0a0a" }}
          >
            ⚡ Try everything for $3
          </Link>
          <Link
            to="/plans"
            className="w-full text-center text-xs text-ink/50 font-semibold py-1 hover:text-copper"
          >
            Compare all plans →
          </Link>
        </div>
      </div>
    </div>
  );
}