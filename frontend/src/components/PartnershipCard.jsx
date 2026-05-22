import { Flame, TrendingUp, Award } from "lucide-react";

/**
 * Partnership Card Component
 * Shows user's partnership level, progress, and monthly contributions
 * Core UI for partnership concept
 */

const LEVELS = [
  { name: "Seed", minPoints: 0, maxPoints: 100, color: "bg-yellow-100", icon: "🌱" },
  { name: "Rooted", minPoints: 100, maxPoints: 300, color: "bg-green-100", icon: "🌿" },
  { name: "Builder", minPoints: 300, maxPoints: 800, color: "bg-blue-100", icon: "🔨" },
  { name: "Steward", minPoints: 800, maxPoints: 2000, color: "bg-purple-100", icon: "🤝" },
  { name: "Elder", minPoints: 2000, maxPoints: 99999, color: "bg-amber-100", icon: "⭐" },
];

function getLevel(points) {
  return LEVELS.find((level) => points >= level.minPoints && points < level.maxPoints) || LEVELS[4];
}

function getNextLevel(points) {
  const currentLevel = getLevel(points);
  const currentIndex = LEVELS.findIndex((l) => l.name === currentLevel.name);
  return currentIndex < LEVELS.length - 1 ? LEVELS[currentIndex + 1] : null;
}

export default function PartnershipCard({ points = 650, monthlyPoints = 120, streak = 12 }) {
  const level = getLevel(points);
  const nextLevel = getNextLevel(points);
  const progressPercent = ((points - level.minPoints) / (level.maxPoints - level.minPoints)) * 100;
  const pointsToNext = nextLevel ? nextLevel.minPoints - points : 0;

  return (
    <div className="bg-gradient-to-br from-copper/5 to-copper/10 border-2 border-copper rounded-lg p-6 max-w-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-heading font-bold text-lg text-ink">Your Partnership</h3>
        <span className="text-2xl">{level.icon}</span>
      </div>

      {/* Level Badge */}
      <div className="text-center mb-6">
        <div className={`inline-block ${level.color} px-4 py-2 rounded-full mb-3`}>
          <p className="font-heading font-bold text-copper text-lg">{level.name}</p>
        </div>
        <p className="text-sm text-ink/60">Partnership Level {LEVELS.findIndex((l) => l.name === level.name) + 1}</p>
      </div>

      {/* Points Progress */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-bold text-ink">{points} Points</span>
          <span className="text-sm text-ink/60">{Math.round(progressPercent)}%</span>
        </div>
        <div className="w-full bg-ink/10 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-copper to-copper/60 h-full transition-all duration-500"
            style={{ width: `${Math.min(progressPercent, 100)}%` }}
          />
        </div>
      </div>

      {/* Next Level */}
      {nextLevel && (
        <div className="bg-white/50 rounded-lg p-4 mb-6">
          <p className="text-xs font-bold text-copper uppercase mb-2">Next Level</p>
          <p className="font-bold text-ink mb-1">{nextLevel.name}</p>
          <p className="text-sm text-ink/60 mb-3">{pointsToNext} points to unlock</p>
          <ul className="text-xs space-y-1 text-ink/70">
            <li>✓ Featured creator status</li>
            <li>✓ Governance voice</li>
            <li>✓ Early feature access</li>
          </ul>
        </div>
      )}

      {/* Monthly Activity */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white/50 rounded-lg p-3 text-center">
          <div className="flex items-center justify-center gap-1 mb-2">
            <Flame className="w-4 h-4 text-orange-500" />
            <span className="text-lg font-bold text-orange-500">{monthlyPoints}</span>
          </div>
          <p className="text-xs text-ink/60">This Month</p>
        </div>
        <div className="bg-white/50 rounded-lg p-3 text-center">
          <div className="flex items-center justify-center gap-1 mb-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <span className="text-lg font-bold text-green-600">{streak}d</span>
          </div>
          <p className="text-xs text-ink/60">Active Streak</p>
        </div>
      </div>

      {/* CTA */}
      <button className="w-full mt-6 py-2 px-4 bg-copper text-white font-bold rounded-lg hover:bg-copper/80 transition-colors text-sm">
        View Your Contributions
      </button>
    </div>
  );
}
