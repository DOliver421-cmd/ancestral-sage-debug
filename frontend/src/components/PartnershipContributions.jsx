import { CheckCircle, BookOpen, Users, MessageSquare, Award, Heart } from "lucide-react";

/**
 * Partnership Contributions Component
 * Shows breakdown of user's contributions to the partnership
 */

const CONTRIBUTION_CATEGORIES = {
  knowledge: {
    icon: BookOpen,
    color: "text-blue-600",
    bg: "bg-blue-50",
    label: "Knowledge Built",
  },
  economic: {
    icon: Heart,
    color: "text-red-600",
    bg: "bg-red-50",
    label: "Economic Impact",
  },
  community: {
    icon: Users,
    color: "text-green-600",
    bg: "bg-green-50",
    label: "Community Care",
  },
};

export default function PartnershipContributions({
  contributions = {
    knowledge: [
      { action: "3 courses published", points: 150 },
      { action: "47 community posts", points: 235 },
      { action: "Mentored 2 creators", points: 200 },
    ],
    economic: [
      { action: "$1,240 earned for creators", points: 100 },
      { action: "45 students enrolled", points: 450 },
      { action: "12 course completions", points: 300 },
    ],
    community: [
      { action: "Helped 23 students", points: 230 },
      { action: "Attended 4 events", points: 100 },
      { action: "Gave feedback on 3 features", points: 75 },
    ],
  },
  totalPoints = 650,
  livesTouched = 42,
}) {
  const totalContributions = Object.values(contributions).flat().length;

  return (
    <div className="max-w-2xl">
      {/* Header */}
      <div className="mb-8">
        <h2 className="font-heading font-bold text-2xl mb-2 text-ink">Your Partnership Contributions</h2>
        <p className="text-ink/60">Everything you've done to build this with us</p>
      </div>

      {/* Categories */}
      <div className="space-y-6">
        {Object.entries(contributions).map(([key, items]) => {
          const category = CONTRIBUTION_CATEGORIES[key];
          const Icon = category.icon;
          const categoryPoints = items.reduce((sum, item) => sum + item.points, 0);

          return (
            <div key={key} className={`${category.bg} border border-ink/10 rounded-lg p-6`}>
              <div className="flex items-center gap-3 mb-4">
                <Icon className={`w-6 h-6 ${category.color}`} />
                <h3 className="font-bold text-lg text-ink">{category.label}</h3>
              </div>

              <div className="space-y-3">
                {items.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-white/60 rounded">
                    <div className="flex items-center gap-3">
                      <CheckCircle className={`w-5 h-5 ${category.color}`} />
                      <span className="text-ink text-sm">{item.action}</span>
                    </div>
                    <span className={`font-bold ${category.color}`}>+{item.points} pts</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-ink/10">
                <p className="text-sm text-ink/60">
                  Subtotal: <span className="font-bold text-ink">+{categoryPoints} points</span>
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-8 bg-gradient-to-r from-copper/10 to-copper/5 border-2 border-copper rounded-lg p-6">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-3xl font-heading font-bold text-copper">{totalPoints}</p>
            <p className="text-sm text-ink/60 mt-1">Total Partnership Points</p>
          </div>
          <div>
            <p className="text-3xl font-heading font-bold text-copper">{livesTouched}</p>
            <p className="text-sm text-ink/60 mt-1">Lives Touched</p>
          </div>
          <div>
            <p className="text-3xl font-heading font-bold text-copper">{totalContributions}</p>
            <p className="text-sm text-ink/60 mt-1">Actions</p>
          </div>
        </div>

        <p className="text-center text-sm text-ink/70 mt-6 border-t border-copper/30 pt-6">
          You're not just using WAI—you're building it. Keep going. 💪
        </p>
      </div>

      {/* Ways to Grow */}
      <div className="mt-8">
        <h3 className="font-bold text-lg mb-4 text-ink">Ways to Grow Your Partnership</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { action: "Create a course", points: 50 },
            { action: "Mentor someone", points: 100 },
            { action: "Lead a workshop", points: 75 },
            { action: "Help in community", points: 10, note: "(daily cap: 50)" },
            { action: "Write a guide", points: 50 },
            { action: "Attend an event", points: 25 },
            { action: "Give feedback", points: 5 },
            { action: "Refer a friend", points: 20 },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-4 border border-ink/10 rounded-lg hover:border-copper hover:shadow-sm transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-bold text-ink group-hover:text-copper transition-colors">{item.action}</p>
                  {item.note && <p className="text-xs text-ink/60 mt-1">{item.note}</p>}
                </div>
                <span className="font-bold text-copper whitespace-nowrap">+{item.points}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
