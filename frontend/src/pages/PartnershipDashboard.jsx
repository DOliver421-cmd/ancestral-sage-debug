import { useState, useEffect } from "react";
import { Users, TrendingUp, Award, BookOpen } from "lucide-react";
import PartnershipCard from "../components/PartnershipCard";
import PartnershipContributions from "../components/PartnershipContributions";
import PartnershipJourney from "../components/PartnershipJourney";
import { api } from "../lib/api";

export default function PartnershipDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState([]);
  const [user, setUser] = useState(null);
  const [ledger, setLedger] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/auth/me").then(r => r.data),
      api.get("/partnership/status").then(r => r.data),
      api.get("/progress/me").then(r => r.data),
      api.get("/partnership/ledger").then(r => r.data).catch(() => []),
    ]).then(([u, s, p, l]) => {
      setUser(u);
      setStatus(s);
      setProgress(p);
      setLedger(l);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const tabs = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "contributions", label: "Contributions", icon: "💪" },
    { id: "journey", label: "Your Journey", icon: "🗺️" },
    { id: "leaderboard", label: "Community", icon: "👥" },
  ];

  const completedModules = progress.filter(p => p.status === "completed").length;
  const totalHours = progress.reduce((acc, p) => acc + (p.hours_logged || 0), 0);

  if (loading) return <div className="min-h-screen bg-bone flex items-center justify-center"><p className="text-ink/60">Loading your partnership data…</p></div>;

  return (
    <div className="min-h-screen bg-bone text-ink">
      <div className="border-b border-ink/10 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <h1 className="font-heading text-4xl font-bold mb-2">Your Partnership</h1>
          <p className="text-lg text-ink/60">
            {user ? `Welcome back, ${user.full_name.split(" ")[0]}.` : "You're not a user."} You're building this with us.
          </p>
        </div>
      </div>

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

      <div className="max-w-7xl mx-auto px-6 py-12">
        {activeTab === "overview" && (
          <div>
            <div className="grid lg:grid-cols-3 gap-8 mb-12">
              <div className="lg:col-span-1">
                {status ? (
                  <PartnershipCard
                    points={status.points}
                    monthlyPoints={0}
                    streak={0}
                    tier={status.tier}
                    nextTier={status.next_tier}
                    pointsToNext={status.points_to_next}
                    membershipUnlocked={status.membership_unlocked}
                  />
                ) : (
                  <div className="bg-white border border-ink/10 rounded-lg p-6 text-center text-ink/60">No partnership data yet</div>
                )}
              </div>

              <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <BookOpen className="w-6 h-6 text-green-600" />
                    <h4 className="font-bold text-ink">Modules Completed</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-green-600 mb-2">{completedModules}</p>
                  <p className="text-sm text-ink/60">of {progress.length} started</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                    <h4 className="font-bold text-ink">Hours Logged</h4>
                  </div>
                  <p className="text-4xl font-heading font-bold text-purple-600 mb-2">{totalHours}</p>
                  <p className="text-sm text-ink/60">Across all modules</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Award className="w-6 h-6 text-amber-600" />
                    <h4 className="font-bold text-ink">Partnership Tier</h4>
                  </div>
                  <p className="text-2xl font-heading font-bold text-amber-600 mb-2">{status?.tier || "Seed I"}</p>
                  <p className="text-sm text-ink/60">{status?.points || 0} points total</p>
                </div>

                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Users className="w-6 h-6 text-blue-600" />
                    <h4 className="font-bold text-ink">Next Milestone</h4>
                  </div>
                  {status?.next_tier ? (
                    <>
                      <p className="text-2xl font-heading font-bold text-blue-600 mb-2">{status.points_to_next} pts</p>
                      <p className="text-sm text-ink/60">to reach {status.next_tier}</p>
                    </>
                  ) : (
                    <p className="text-2xl font-heading font-bold text-blue-600 mb-2">Max Tier</p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white border border-ink/10 rounded-lg p-8">
              <h2 className="font-heading font-bold text-2xl mb-6 text-ink">Recent Partnership Activity</h2>
              {ledger.length > 0 ? (
                <div className="space-y-4">
                  {ledger.slice(0, 8).map((entry, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 border border-ink/10 rounded-lg hover:border-copper hover:bg-copper/5 transition-all">
                      <div className="flex items-center gap-4">
                        <span className="text-2xl">⭐</span>
                        <div>
                          <p className="font-bold text-ink">{entry.reason || "Points awarded"}</p>
                          <p className="text-sm text-ink/60">{entry.ts ? new Date(entry.ts).toLocaleDateString() : "—"}</p>
                        </div>
                      </div>
                      <span className="font-bold text-copper text-lg">+{entry.amount}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-ink/60">
                  <p className="mb-2">No activity yet.</p>
                  <p className="text-sm">Complete modules and engage with the community to earn points.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "contributions" && <PartnershipContributions />}
        {activeTab === "journey" && <PartnershipJourney />}

        {activeTab === "leaderboard" && (
          <div>
            <h2 className="font-heading font-bold text-2xl mb-8 text-ink">Partnership Community</h2>

            <div className="grid lg:grid-cols-3 gap-8">
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
