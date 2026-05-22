import { useState } from "react";
import { Users, TrendingUp, Award, BookOpen } from "lucide-react";
import PartnershipCard from "../components/PartnershipCard";
import PartnershipContributions from "../components/PartnershipContributions";
import PartnershipJourney from "../components/PartnershipJourney";

/**
 * Partnership Dashboard Page
 * Central hub for users to understand their role in building WAI
 * Shows partnership level, contributions, journey, and community impact
 */

export default function PartnershipDashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  // Mock user data
  const userData = {
    points: 650,
    monthlyPoints: 120,
    streak: 12,
    level: 3,
    livesTouched: 42,
  };

  const tabs = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "contributions", label: "Contributions", icon: "💪" },
    { id: "journey", label: "Your Journey", icon: "🗺️" },
    { id: "leaderboard", label: "Community", icon: "👥" },
  ];

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="font-heading text-4xl font-bold mb-2">Your Partnership</h1>
          <p className="text-lg text-ink/60">You're not a user. You're building this with us.</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-ink/10 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 flex gap-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 font-bold text-sm border-b-2 transition-all ${
                activeTab === tab.id
                  ? "border-copper text-copper"
                  : "border-transparent text-ink/60 hover:text-ink"
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div>
            <div className="grid lg:grid-cols-3 gap-8 mb-12">
              {/* Main Partnership Card */}
              <div className="lg:col-span-1">
                <PartnershipCard
                  points={userData.points}
                  monthlyPoints={userData.monthlyPoints}
                  streak={userData.streak}
                />
              </div>

              {/* Quick Stats */}
              <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Users className="w-6 h-6 text-blue-600" />
                    <h4 className="font-bold text-ink">Lives Impacted</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-blue-600 mb-2">{userData.livesTouched}</p>
                  <p className="text-sm text-ink/60">Students, mentees, and community members</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <BookOpen className="w-6 h-6 text-green-600" />
                    <h4 className="font-bold text-ink">Courses Created</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-green-600 mb-2">3</p>
                  <p className="text-sm text-ink/60">Teaching, healing, creating</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                    <h4 className="font-bold text-ink">Revenue Shared</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-purple-600 mb-2">$1.2K</p>
                  <p className="text-sm text-ink/60">You earned 70%, we earned 30%</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Award className="w-6 h-6 text-amber-600" />
                    <h4 className="font-bold text-ink">Avg Rating</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-amber-600 mb-2">4.8★</p>
                  <p className="text-sm text-ink/60">From 87 reviews</p>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white border border-ink/10 rounded-lg p-8">
              <h2 className="font-heading font-bold text-2xl mb-6 text-ink">Recent Partnership Activity</h2>
              <div className="space-y-4">
                {[
                  { date: "Today", action: "Helped student in forum", points: 10, icon: "💬" },
                  { date: "Today", action: "Attended community call", points: 25, icon: "📞" },
                  { date: "Yesterday", action: "Course completion (+25 pts)", points: 25, icon: "✅" },
                  { date: "2 days ago", action: "Wrote course review", points: 10, icon: "⭐" },
                  { date: "3 days ago", action: "Mentored new creator", points: 100, icon: "🤝" },
                ].map((activity, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border border-ink/10 rounded-lg hover:border-copper hover:bg-copper/5 transition-all">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">{activity.icon}</span>
                      <div>
                        <p className="font-bold text-ink">{activity.action}</p>
                        <p className="text-sm text-ink/60">{activity.date}</p>
                      </div>
                    </div>
                    <span className="font-bold text-copper text-lg">+{activity.points}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Contributions Tab */}
        {activeTab === "contributions" && <PartnershipContributions />}

        {/* Journey Tab */}
        {activeTab === "journey" && <PartnershipJourney />}

        {/* Community/Leaderboard Tab */}
        {activeTab === "leaderboard" && (
          <div>
            <h2 className="font-heading font-bold text-2xl mb-8 text-ink">Partnership Community</h2>

            {/* Leaderboard Sections */}
            <div className="grid lg:grid-cols-3 gap-8">
              {/* Top Knowledge Builders */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 text-ink">📚 Top Knowledge Builders</h3>
                <div className="space-y-3">
                  {[
                    { name: "Maya", detail: "8 courses, 156 mentees", medal: "🥇" },
                    { name: "James", detail: "5 courses, 200+ students", medal: "🥈" },
                    { name: "Sophia", detail: "200 community posts", medal: "🥉" },
                  ].map((person, idx) => (
                    <div key={idx} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="font-bold text-ink flex items-center gap-2">
                        <span>{person.medal}</span>
                        {person.name}
                      </p>
                      <p className="text-sm text-ink/60">{person.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Community Stewards */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 text-ink">💪 Top Community Stewards</h3>
                <div className="space-y-3">
                  {[
                    { name: "Ahmed", detail: "340 community answers", medal: "🥇" },
                    { name: "Keisha", detail: "Led 4 workshops", medal: "🥈" },
                    { name: "David", detail: "Mentored 8 creators", medal: "🥉" },
                  ].map((person, idx) => (
                    <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <p className="font-bold text-ink flex items-center gap-2">
                        <span>{person.medal}</span>
                        {person.name}
                      </p>
                      <p className="text-sm text-ink/60">{person.detail}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Economic Catalysts */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 text-ink">💰 Top Economic Catalysts</h3>
                <div className="space-y-3">
                  {[
                    { name: "Amara", detail: "$4,200 earned, 89 students", medal: "🥇" },
                    { name: "Darius", detail: "$3,100 earned, 156 students", medal: "🥈" },
                    { name: "Nia", detail: "$2,450 earned, 78 students", medal: "🥉" },
                  ].map((person, idx) => (
                    <div key={idx} className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <p className="font-bold text-ink flex items-center gap-2">
                        <span>{person.medal}</span>
                        {person.name}
                      </p>
                      <p className="text-sm text-ink/60">{person.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Note */}
            <div className="mt-8 p-6 bg-copper/10 border border-copper rounded-lg text-center">
              <p className="text-ink/70">
                <strong>We celebrate all types of partnership.</strong> Knowledge building, community stewardship, and economic impact all matter equally. You're not competing—you're building together.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
