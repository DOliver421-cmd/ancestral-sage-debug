import { Sprout } from "lucide-react";

// Renders a member's partnership points + tier from /api/partnership/status.
// `status` shape: { points, tier, tier_min, next_tier, points_to_next, membership_unlocked }
// Membership unlock threshold mirrors backend partnership/points.MEMBERSHIP_UNLOCK_POINTS.
const MEMBERSHIP_UNLOCK_POINTS = 300;

export default function PartnershipProgress({ status }) {
  if (!status) return null;
  const {
    points = 0,
    tier = "Seed I",
    tier_min = 0,
    next_tier,
    points_to_next = 0,
    membership_unlocked,
  } = status;

  const nextThreshold = next_tier ? points + points_to_next : null;
  const span = nextThreshold ? Math.max(1, nextThreshold - tier_min) : 1;
  const pct = next_tier ? Math.min(100, Math.round(((points - tier_min) / span) * 100)) : 100;

  return (
    <div className="card-flat p-6" data-testid="partnership-progress">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="overline text-copper flex items-center gap-2">
            <Sprout className="w-4 h-4" /> Partnership Tier
          </div>
          <div className="font-heading text-2xl font-black text-ink mt-1">{tier}</div>
        </div>
        <div className="text-right">
          <div className="font-heading text-2xl font-black text-ink">{points}</div>
          <div className="overline text-ink/60">points</div>
        </div>
      </div>

      <div className="w-full h-3 bg-ink/10">
        <div className="h-full bg-copper transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-ink/60 mt-2 font-mono">
        <span>{tier}</span>
        <span>{next_tier ? `${points_to_next} pts → ${next_tier}` : "Highest tier reached"}</span>
      </div>

      {membership_unlocked ? (
        <div className="badge-signal mt-4 inline-block" data-testid="membership-unlocked">
          Free Basic Membership Unlocked
        </div>
      ) : (
        <div className="text-xs text-ink/60 mt-4">
          Earn {Math.max(0, MEMBERSHIP_UNLOCK_POINTS - points)} more points to unlock free Basic membership.
        </div>
      )}
    </div>
  );
}
