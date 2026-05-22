import { Sparkles, Award } from "lucide-react";

/**
 * Partnership Journey Component
 * Shows user's progression through partnership levels
 * Timeline visualization of key milestones
 */

export default function PartnershipJourney({
  currentLevel = 3,
  currentPoints = 650,
  milestones = [
    { date: "Jan 15", type: "join", title: "Joined WAI", description: "Started your partnership journey" },
    { date: "Feb 2", type: "publish", title: "Published First Course", description: "Went from Seed to Rooted" },
    { date: "Mar 20", type: "students", title: "First 100 Students", description: "Your work is reaching people" },
    { date: "Apr 15", type: "mentor", title: "Became Mentor", description: "Started guiding other creators" },
    { date: "May 1", type: "levelup", title: "Reached Builder Level", description: "Your governance voice unlocked" },
  ],
}) {
  const LEVELS = [
    { name: "Seed", points: 100 },
    { name: "Rooted", points: 300 },
    { name: "Builder", points: 800 },
    { name: "Steward", points: 2000 },
    { name: "Elder", points: 99999 },
  ];

  const getMilestoneIcon = (type) => {
    const icons = {
      join: "🌱",
      publish: "📚",
      students: "👥",
      mentor: "🤝",
      levelup: "⭐",
      milestone: "✨",
    };
    return icons[type] || "✨";
  };

  return (
    <div className="max-w-3xl">
      {/* Header */}
      <div className="mb-8">
        <h2 className="font-heading font-bold text-2xl mb-2 text-ink">Your Partnership Journey</h2>
        <p className="text-ink/60">Watch how your partnership deepened over time</p>
      </div>

      {/* Level Progress Visual */}
      <div className="mb-12">
        <div className="flex justify-between items-center mb-6">
          {LEVELS.map((level, idx) => (
            <div
              key={idx}
              className={`text-center transition-all ${
                idx < currentLevel ? "opacity-100" : idx === currentLevel ? "opacity-100" : "opacity-40"
              }`}
            >
              <div
                className={`w-12 h-12 rounded-full mx-auto mb-3 flex items-center justify-center font-bold text-lg transition-all ${
                  idx < currentLevel
                    ? "bg-copper text-white"
                    : idx === currentLevel
                      ? "bg-copper/20 border-2 border-copper text-copper"
                      : "bg-ink/5 border-2 border-ink/20 text-ink/40"
                }`}
              >
                {idx + 1}
              </div>
              <p className={`text-sm font-bold ${idx <= currentLevel ? "text-ink" : "text-ink/40"}`}>{level.name}</p>
              <p className="text-xs text-ink/50 mt-1">{level.points === 99999 ? "∞" : level.points} pts</p>
            </div>
          ))}
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-ink/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-copper to-copper/60 transition-all duration-500"
            style={{
              width: `${((currentLevel + 1) / LEVELS.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Milestones Timeline */}
      <div className="relative mb-12">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-copper/20" />

        {/* Milestones */}
        <div className="space-y-8">
          {milestones.map((milestone, idx) => (
            <div key={idx} className="relative pl-20">
              {/* Milestone dot */}
              <div
                className={`absolute left-0 top-1 w-12 h-12 rounded-full flex items-center justify-center text-xl border-4 ${
                  idx < milestones.length - 1
                    ? "bg-white border-copper/40 text-copper"
                    : "bg-white border-copper text-copper"
                }`}
              >
                {getMilestoneIcon(milestone.type)}
              </div>

              {/* Content */}
              <div className={`p-4 rounded-lg ${idx === milestones.length - 1 ? "bg-copper/10 border border-copper" : "bg-ink/5 border border-ink/10"}`}>
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-bold text-ink">{milestone.title}</h4>
                  <span className="text-xs font-bold text-copper whitespace-nowrap ml-4">{milestone.date}</span>
                </div>
                <p className="text-sm text-ink/60">{milestone.description}</p>
              </div>
            </div>
          ))}

          {/* Future milestone */}
          <div className="relative pl-20 opacity-50">
            <div className="absolute left-0 top-1 w-12 h-12 rounded-full flex items-center justify-center text-xl border-4 bg-white border-copper/20 text-copper/40">
              🚀
            </div>
            <div className="p-4 rounded-lg bg-ink/5 border border-ink/10 border-dashed">
              <h4 className="font-bold text-ink/60">Next: Steward Level</h4>
              <p className="text-sm text-ink/50 mt-1">150 points to go. Keep building. ✨</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-6">
        <p className="text-sm font-bold text-copper uppercase mb-4">Partnership Stats</p>

        <div className="grid grid-cols-4 gap-4">
          <div>
            <p className="text-2xl font-heading font-bold text-ink">5</p>
            <p className="text-xs text-ink/60">Milestones</p>
          </div>
          <div>
            <p className="text-2xl font-heading font-bold text-ink">3</p>
            <p className="text-xs text-ink/60">Levels</p>
          </div>
          <div>
            <p className="text-2xl font-heading font-bold text-ink">550</p>
            <p className="text-xs text-ink/60">Points Earned</p>
          </div>
          <div>
            <p className="text-2xl font-heading font-bold text-ink">4mo</p>
            <p className="text-xs text-ink/60">Active</p>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-copper/30">
          <p className="text-sm text-ink/70">
            <strong>You're 5 months into building with us.</strong> The work you're doing matters. The community you're building is real. Keep going.
          </p>
        </div>
      </div>
    </div>
  );
}
