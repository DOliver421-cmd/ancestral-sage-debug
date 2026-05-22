import { useState, useEffect } from "react";
import { Edit2, Settings, Share2, Heart, BookOpen, Users, TrendingUp, Award, Lock } from "lucide-react";
import PartnershipCard from "../components/PartnershipCard";

/**
 * User Profile Page
 * Shows different content based on user role and partnership level
 * Handles student, creator, mentor profiles differently
 */

export default function UserProfile({ userId = "user_123", isOwnProfile = true }) {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock user data - would be fetched from backend
    const mockUser = {
      id: userId,
      username: "Maya Johnson",
      role: "creator", // student, creator, mentor, steward, elder
      partnershipLevel: "builder",
      partnershipPoints: 650,
      profileImage: "/images/creators/creator-1-poet.jpg",
      bio: "Poet, healer, and community builder. Teaching trauma recovery through verse.",
      joinDate: "2025-01-15",
      location: "Oakland, CA",
      website: "https://mayajohnson.com",
      socialLinks: {
        twitter: "@mayajohns",
        instagram: "@mayaheals",
      },
      badges: ["Early Adopter", "Teacher", "Life Changer", "Movement Builder"],
      // Creator-specific stats
      coursesPublished: 3,
      coursesEnrolled: 12,
      studentsReached: 342,
      totalEarnings: 1240,
      avgCourseRating: 4.8,
      mentees: 2,
      // Community activity
      postsCreated: 47,
      commentsWritten: 230,
      helpfulnessScore: 4.7,
      // Milestones
      latestMilestones: [
        { date: "May 20", title: "Reached Builder Level", icon: "🔨" },
        { date: "May 15", title: "Published 3rd Course", icon: "📚" },
        { date: "May 10", title: "Unlocked Mentorship", icon: "🤝" },
      ],
    };

    setUser(mockUser);
    setLoading(false);
  }, [userId]);

  if (loading) return <div className="text-center py-12">Loading profile...</div>;
  if (!user) return <div className="text-center py-12">Profile not found</div>;

  const isCreator = user.role === "creator" || user.role === "mentor";

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Profile Header */}
      <div className="bg-white border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Profile Picture & Basic Info */}
            <div className="md:col-span-1 text-center">
              <img
                src={user.profileImage}
                alt={user.username}
                className="w-32 h-32 rounded-full object-cover mx-auto mb-4 border-4 border-copper"
              />
              <h1 className="font-heading text-2xl font-bold text-ink mb-1">{user.username}</h1>
              <p className="text-sm text-copper font-bold uppercase mb-3">
                {user.role === "creator" ? "Creator" : user.role === "student" ? "Student" : user.role === "mentor" ? "Mentor" : "Community Member"}
              </p>
              <div className="flex gap-2 justify-center mb-4">
                <span className="text-lg">{["🌱", "🌿", "🔨", "🤝", "⭐"][["seed", "rooted", "builder", "steward", "elder"].indexOf(user.partnershipLevel)]}</span>
                <span className="text-sm font-bold text-ink">{user.partnershipLevel}</span>
              </div>

              {isOwnProfile && (
                <button className="w-full py-2 px-4 bg-copper text-white rounded font-bold mb-2 hover:bg-copper/80 transition-colors flex items-center justify-center gap-2">
                  <Edit2 className="w-4 h-4" />
                  Edit Profile
                </button>
              )}
            </div>

            {/* Stats Grid */}
            <div className="md:col-span-3">
              <p className="text-ink/70 mb-6">{user.bio}</p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {isCreator ? (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-blue-600">{user.coursesPublished}</p>
                      <p className="text-xs text-blue-700">Courses</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-green-600">{user.studentsReached}</p>
                      <p className="text-xs text-green-700">Students</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-purple-600">${user.totalEarnings}</p>
                      <p className="text-xs text-purple-700">Earned</p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-yellow-600">{user.avgCourseRating}★</p>
                      <p className="text-xs text-yellow-700">Rating</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-blue-600">{user.coursesEnrolled}</p>
                      <p className="text-xs text-blue-700">Courses</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-green-600">{user.postsCreated}</p>
                      <p className="text-xs text-green-700">Posts</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-purple-600">{user.commentsWritten}</p>
                      <p className="text-xs text-purple-700">Helpful</p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                      <p className="text-3xl font-bold text-yellow-600">{user.partnershipPoints}</p>
                      <p className="text-xs text-yellow-700">Points</p>
                    </div>
                  </>
                )}
              </div>

              {/* Badges */}
              <div>
                <p className="text-sm font-bold text-ink/60 mb-2">ACHIEVEMENTS</p>
                <div className="flex flex-wrap gap-2">
                  {user.badges.map((badge, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-copper/10 border border-copper text-copper rounded-full text-xs font-bold"
                    >
                      ✨ {badge}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-ink/10 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 flex gap-8">
          {isCreator ? (
            <>
              <button
                onClick={() => setActiveTab("overview")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "overview"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab("courses")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "courses"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Courses
              </button>
              <button
                onClick={() => setActiveTab("community")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "community"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Community
              </button>
              {isOwnProfile && (
                <button
                  onClick={() => setActiveTab("settings")}
                  className={`py-4 font-bold text-sm border-b-2 transition-all ${
                    activeTab === "settings"
                      ? "border-copper text-copper"
                      : "border-transparent text-ink/60 hover:text-ink"
                  }`}
                >
                  Settings
                </button>
              )}
            </>
          ) : (
            <>
              <button
                onClick={() => setActiveTab("overview")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "overview"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab("learning")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "learning"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Learning
              </button>
              <button
                onClick={() => setActiveTab("activity")}
                className={`py-4 font-bold text-sm border-b-2 transition-all ${
                  activeTab === "activity"
                    ? "border-copper text-copper"
                    : "border-transparent text-ink/60 hover:text-ink"
                }`}
              >
                Activity
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {activeTab === "overview" && (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <PartnershipCard
                points={user.partnershipPoints}
                monthlyPoints={120}
                streak={12}
              />
            </div>

            <div className="lg:col-span-2 space-y-8">
              {/* Recent Milestones */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h2 className="font-bold text-lg mb-6 text-ink">Recent Milestones</h2>
                <div className="space-y-4">
                  {user.latestMilestones.map((milestone, idx) => (
                    <div
                      key={idx}
                      className="p-4 border border-ink/10 rounded-lg hover:border-copper hover:bg-copper/5 transition-all"
                    >
                      <div className="flex items-center gap-4">
                        <span className="text-2xl">{milestone.icon}</span>
                        <div>
                          <p className="font-bold text-ink">{milestone.title}</p>
                          <p className="text-sm text-ink/60">{milestone.date}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* About */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h2 className="font-bold text-lg mb-4 text-ink">About</h2>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-ink/60">Member Since</p>
                    <p className="font-bold text-ink">{new Date(user.joinDate).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-ink/60">Location</p>
                    <p className="font-bold text-ink">{user.location}</p>
                  </div>
                  {user.website && (
                    <div>
                      <p className="text-sm text-ink/60">Website</p>
                      <a href={user.website} className="font-bold text-copper hover:underline">
                        {user.website}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "courses" && isCreator && (
          <div>
            <h2 className="font-bold text-2xl mb-6 text-ink">My Courses</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white border border-ink/10 rounded-lg p-6 hover:border-copper hover:shadow-lg transition-all">
                  <div className="w-full h-40 bg-copper/10 rounded-lg mb-4" />
                  <h3 className="font-bold text-lg text-ink mb-2">Course Title {i}</h3>
                  <p className="text-sm text-ink/60 mb-4">Course description</p>
                  <div className="flex justify-between text-sm">
                    <span className="font-bold text-ink">342 students</span>
                    <span className="font-bold text-copper">4.8★</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "settings" && isOwnProfile && (
          <div className="max-w-2xl">
            <h2 className="font-bold text-2xl mb-8 text-ink">Account Settings</h2>

            <div className="space-y-6">
              {/* Security */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  Security
                </h3>
                <button className="py-2 px-4 border border-ink/20 rounded font-bold hover:border-copper hover:text-copper transition-colors">
                  Change Password
                </button>
              </div>

              {/* Privacy */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4">Privacy Settings</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-ink">Make profile public</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-ink">Show earnings publicly</span>
                  </label>
                </div>
              </div>

              {/* Notifications */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4">Notifications</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-ink">New student enrolled</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-ink">Course review posted</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                    <span className="text-ink">Partnership milestone reached</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
