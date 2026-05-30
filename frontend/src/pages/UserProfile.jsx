import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Edit2, Lock } from "lucide-react";
import PartnershipCard from "../components/PartnershipCard";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function UserProfile() {
  const { id } = useParams();
  const { user: authUser } = useAuth();
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editMsg, setEditMsg] = useState("");

  const isOwnProfile = !id || id === authUser?.id;

  useEffect(() => {
    const userReq = isOwnProfile
      ? api.get("/auth/me").then(r => r.data)
      : api.get(`/auth/me`).then(r => r.data); // only own profile available; fallback gracefully

    Promise.all([
      userReq,
      api.get("/partnership/status").then(r => r.data).catch(() => null),
      api.get("/progress/me").then(r => r.data).catch(() => []),
    ]).then(([u, s, p]) => {
      setUser(u);
      setStatus(s);
      setProgress(p);
      setEditName(u.full_name || "");
      setEditEmail(u.email || "");
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id, isOwnProfile]);

  const saveProfile = async () => {
    setSaving(true);
    setEditMsg("");
    try {
      const r = await api.patch("/auth/me", { full_name: editName, email: editEmail });
      setUser(r.data);
      setEditMsg("Saved.");
    } catch (e) {
      setEditMsg(e?.response?.data?.detail || "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-bone flex items-center justify-center"><p className="text-ink/60">Loading profile…</p></div>;
  if (!user) return <div className="min-h-screen bg-bone flex items-center justify-center"><p className="text-ink/60">Profile not found.</p></div>;

  const completedModules = progress.filter(p => p.status === "completed").length;
  const totalHours = progress.reduce((acc, p) => acc + (p.hours_logged || 0), 0);
  const isCreator = user.role === "instructor" || user.role === "admin" || user.role === "executive_admin";

  const rolLabel = {
    student: "Student",
    instructor: "Instructor",
    admin: "Administrator",
    executive_admin: "Executive Director",
  }[user.role] || "Member";

  return (
    <div className="min-h-screen bg-bone text-ink">
      {/* Header */}
      <div className="bg-white border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Avatar & Basic Info */}
            <div className="md:col-span-1 text-center">
              <div className="w-32 h-32 rounded-full bg-copper flex items-center justify-center mx-auto mb-4 border-4 border-copper">
                <span className="text-white font-heading text-4xl font-bold">
                  {user.full_name?.charAt(0).toUpperCase() || "?"}
                </span>
              </div>
              <h1 className="font-heading text-2xl font-bold text-ink mb-1">{user.full_name}</h1>
              <p className="text-sm text-copper font-bold uppercase mb-3">{rolLabel}</p>
              {status && (
                <div className="flex gap-2 justify-center mb-4">
                  <span className="text-sm font-bold text-ink">{status.tier}</span>
                  <span className="text-sm text-ink/60">· {status.points} pts</span>
                </div>
              )}
              {isOwnProfile && (
                <button
                  onClick={() => setActiveTab("settings")}
                  className="w-full py-2 px-4 bg-copper text-white rounded font-bold mb-2 hover:bg-copper/80 transition-colors flex items-center justify-center gap-2"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit Profile
                </button>
              )}
            </div>

            {/* Stats */}
            <div className="md:col-span-3">
              <p className="text-ink/70 mb-6">Member since {new Date(user.created_at).toLocaleDateString()}.</p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-blue-600">{progress.length}</p>
                  <p className="text-xs text-blue-700">Courses Started</p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-green-600">{completedModules}</p>
                  <p className="text-xs text-green-700">Completed</p>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-purple-600">{totalHours}</p>
                  <p className="text-xs text-purple-700">Hours Logged</p>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-yellow-600">{status?.points || 0}</p>
                  <p className="text-xs text-yellow-700">Points</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-bold text-ink/60 mb-2">PARTNERSHIP STATUS</p>
                <div className="flex flex-wrap gap-2">
                  {status && (
                    <span className="px-3 py-1 bg-copper/10 border border-copper text-copper rounded-full text-xs font-bold">
                      ✨ {status.tier}
                    </span>
                  )}
                  {status?.membership_unlocked && (
                    <span className="px-3 py-1 bg-green-100 border border-green-400 text-green-700 rounded-full text-xs font-bold">
                      ✅ Basic Membership Unlocked
                    </span>
                  )}
                  {completedModules > 0 && (
                    <span className="px-3 py-1 bg-blue-100 border border-blue-400 text-blue-700 rounded-full text-xs font-bold">
                      📚 {completedModules} Module{completedModules !== 1 ? "s" : ""} Done
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-ink/10 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 flex gap-8">
          {[
            { id: "overview", label: "Overview" },
            { id: "learning", label: "Learning" },
            ...(isOwnProfile ? [{ id: "settings", label: "Settings" }] : []),
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 font-bold text-sm border-b-2 transition-all ${
                activeTab === tab.id
                  ? "border-copper text-copper"
                  : "border-transparent text-ink/60 hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {activeTab === "overview" && (
          <div className="grid lg:grid-cols-3 gap-8">
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
                <div className="bg-white border border-ink/10 rounded-lg p-6 text-center text-ink/60">No partnership data yet. Complete modules to earn points.</div>
              )}
            </div>

            <div className="lg:col-span-2 space-y-8">
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h2 className="font-bold text-lg mb-4 text-ink">Account Info</h2>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-ink/60">Name</p>
                    <p className="font-bold text-ink">{user.full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-ink/60">Email</p>
                    <p className="font-bold text-ink">{user.email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-ink/60">Role</p>
                    <p className="font-bold text-ink">{rolLabel}</p>
                  </div>
                  <div>
                    <p className="text-sm text-ink/60">Member Since</p>
                    <p className="font-bold text-ink">{new Date(user.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>

              {progress.length > 0 && (
                <div className="bg-white border border-ink/10 rounded-lg p-6">
                  <h2 className="font-bold text-lg mb-4 text-ink">Recent Learning</h2>
                  <div className="space-y-3">
                    {progress.slice(0, 5).map((p, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 border border-ink/10 rounded-lg">
                        <div>
                          <p className="font-bold text-ink capitalize">{p.module_slug?.replace(/-/g, " ") || "Module"}</p>
                          <p className="text-sm text-ink/60">{p.hours_logged || 0} hrs logged</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          p.status === "completed" ? "bg-green-100 text-green-700" :
                          p.status === "in_progress" ? "bg-blue-100 text-blue-700" :
                          "bg-ink/10 text-ink/60"
                        }`}>
                          {p.status?.replace(/_/g, " ")}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "learning" && (
          <div>
            <h2 className="font-bold text-2xl mb-6 text-ink">Learning Progress</h2>
            {progress.length === 0 ? (
              <div className="bg-white border border-ink/10 rounded-lg p-12 text-center">
                <p className="text-ink/60 mb-4">You haven't started any modules yet.</p>
                <a href="/modules" className="btn-primary inline-block">Browse Modules</a>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {progress.map((p, idx) => (
                  <div key={idx} className="bg-white border border-ink/10 rounded-lg p-6 hover:border-copper transition-all">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-bold text-lg text-ink capitalize">{p.module_slug?.replace(/-/g, " ") || "Module"}</h3>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        p.status === "completed" ? "bg-green-100 text-green-700" :
                        p.status === "in_progress" ? "bg-blue-100 text-blue-700" :
                        "bg-ink/10 text-ink/60"
                      }`}>
                        {p.status?.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex gap-6 text-sm text-ink/60">
                      <span>{p.hours_logged || 0} hrs logged</span>
                      {p.quiz_score != null && <span>Quiz: {Math.round(p.quiz_score * 100)}%</span>}
                      {p.completed_at && <span>Done {new Date(p.completed_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "settings" && isOwnProfile && (
          <div className="max-w-2xl">
            <h2 className="font-bold text-2xl mb-8 text-ink">Account Settings</h2>
            <div className="space-y-6">
              {/* Edit Name / Email */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                  <Edit2 className="w-5 h-5" />
                  Profile Details
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold text-ink/70 mb-1">Display Name</label>
                    <input
                      type="text"
                      value={editName}
                      onChange={e => setEditName(e.target.value)}
                      className="w-full border border-ink/20 rounded px-3 py-2 text-ink focus:outline-none focus:border-copper"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-ink/70 mb-1">Email</label>
                    <input
                      type="email"
                      value={editEmail}
                      onChange={e => setEditEmail(e.target.value)}
                      className="w-full border border-ink/20 rounded px-3 py-2 text-ink focus:outline-none focus:border-copper"
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={saveProfile}
                      disabled={saving}
                      className="py-2 px-6 bg-copper text-white rounded font-bold hover:bg-copper/80 transition-colors disabled:opacity-50"
                    >
                      {saving ? "Saving…" : "Save Changes"}
                    </button>
                    {editMsg && <span className={`text-sm font-bold ${editMsg === "Saved." ? "text-green-600" : "text-red-600"}`}>{editMsg}</span>}
                  </div>
                </div>
              </div>

              {/* Security */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  Security
                </h3>
                <a href="/forgot-password" className="inline-block py-2 px-4 border border-ink/20 rounded font-bold hover:border-copper hover:text-copper transition-colors">
                  Change Password
                </a>
              </div>

              {/* Notifications */}
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4">Notifications</h3>
                <div className="space-y-3">
                  {["Module completion reminders", "Partnership milestone reached", "New course recommendations"].map((label, i) => (
                    <label key={i} className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                      <span className="text-ink">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
