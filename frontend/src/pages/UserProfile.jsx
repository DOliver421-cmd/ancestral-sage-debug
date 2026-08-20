import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Edit2, Lock, ChevronDown, ChevronRight, ExternalLink, Tag, Search, Sparkles, ArrowRight } from "lucide-react";
import PartnershipCard from "../components/PartnershipCard";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Ascension Protocols Phase Data ────────────────────────────────────────────
const ASCENSION_PHASES = [
  {
    id: "intro",
    label: "Introduction",
    tier: "Foundation",
    description: "The Kemetic Frame & Lunar Calendar",
    icon: "𓂀",
    color: "#92400e",
  },
  {
    id: "tier1",
    label: "Tier 1 · 7 Days",
    tier: "Baseline",
    description: "Reclaiming the Organic Signal",
    icon: "☀",
    color: "#E8A51E",
    duration: "7 days",
    steps: ["Dawn Alignment", "Midday Anchor", "Night Dissolve"],
  },
  {
    id: "tier2",
    label: "Tier 2 · 30 Days",
    tier: "Forge",
    description: "Clearing the Conditioning",
    icon: "𓋹",
    color: "#b5651d",
    duration: "30 days",
    steps: ["Subconscious Clearing", "Somatic Intelligence", "Spatial Sovereignty", "Autonomous Creation"],
  },
  {
    id: "tier3",
    label: "Tier 3 · 90 Days",
    tier: "Reckoning",
    description: "The Unbroken Blueprint",
    icon: "𓋴",
    color: "#1B4332",
    duration: "90 days",
    steps: ["Akhet · Inundation", "Peret · Emergence", "Shemu · Harvest"],
  },
  {
    id: "phase4",
    label: "The Guild",
    tier: "Veteran",
    description: "Community & Legacy",
    icon: "𓊝",
    color: "#E8A51E",
  },
];

const ASCENSION_BADGES = [
  { name: "Baseline", icon: "☀", desc: "Completed Tier 1", tier: "tier1" },
  { name: "Forge", icon: "🔥", desc: "Completed Tier 2", tier: "tier2" },
  { name: "Reckoning", icon: "⚖", desc: "Completed Tier 3", tier: "tier3" },
  { name: "Arena Veteran", icon: "🏛", desc: "Full spiral completed", tier: "phase4" },
];

// ── Deals data (client-side curated for now) ──────────────────────────────────
const DEAL_CATEGORIES = [
  { id: "groceries", label: "Groceries", icon: "🛒", color: "#16a34a" },
  { id: "household", label: "Household", icon: "🏠", color: "#2563eb" },
  { id: "health", label: "Health & Wellness", icon: "💚", color: "#7c3aed" },
  { id: "education", label: "Education", icon: "📚", color: "#E8A51E" },
  { id: "tech", label: "Tech & Tools", icon: "💻", color: "#0891b2" },
  { id: "community", label: "Community", icon: "🤝", color: "#b5651d" },
];

const SAMPLE_DEALS = [
  { id: 1, title: "Fresh Market Weekly", brand: "Local Co-op", category: "groceries", discount: "15% off", code: "FRESH15", expires: "2026-09-01", description: "Fresh produce & pantry staples from community co-ops" },
  { id: 2, title: "Back to School Bundle", brand: "Office Supply Co", category: "education", discount: "$10 off $50+", code: "SCHOOL10", expires: "2026-09-15", description: "Notebooks, pens, and learning supplies" },
  { id: 3, title: "Wellness Wednesday", brand: "GreenLife", category: "health", discount: "20% off", code: "WELLNESS20", expires: "2026-08-31", description: "Vitamins, supplements, and organic wellness products" },
  { id: 4, title: "Smart Home Starter", brand: "TechHome", category: "tech", discount: "25% off first order", code: "SMART25", expires: "2026-10-01", description: "Energy-efficient smart home devices" },
  { id: 5, title: "Community Garden Kit", brand: "Grow Together", category: "community", discount: "Free shipping", code: "GROWFREE", expires: "2026-09-30", description: "Seeds, soil, and tools for community garden projects" },
  { id: 6, title: "Cleaning Essentials", brand: "CleanHome", category: "household", discount: "Buy 2 Get 1", code: "CLEAN3", expires: "2026-08-28", description: "Eco-friendly cleaning supplies for the whole home" },
];

// ── Ascension Progress Widget ─────────────────────────────────────────────────

function AscensionProgress({ activePhase, setActivePhase }) {
  return (
    <div className="bg-white border border-ink/10 rounded-lg overflow-hidden">
      <div className="p-6" style={{ background: "linear-gradient(135deg,#0d0a06,#241a08)", color: "#fff" }}>
        <div className="text-xs font-bold uppercase tracking-widest" style={{ color: "#E8A51E" }}>Ascension Protocols</div>
        <h3 className="font-heading font-black text-xl mt-1">Your Journey</h3>
        <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.6)" }}>
          Track your progress through the 4 phases of ancestral remembrance.
        </p>
      </div>

      {/* Phase stepper */}
      <div className="p-6">
        <div className="space-y-3">
          {ASCENSION_PHASES.map((phase, idx) => {
            const isActive = activePhase === phase.id;
            const isCompleted = ASCENSION_PHASES.findIndex(p => p.id === activePhase) > idx;
            return (
              <button
                key={phase.id}
                onClick={() => setActivePhase(phase.id)}
                className="w-full text-left rounded-xl p-4 transition-all"
                style={{
                  background: isActive ? `${phase.color}10` : "#faf9f7",
                  border: isActive ? `2px solid ${phase.color}` : "1px solid #eee7db",
                }}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{phase.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-ink">{phase.label}</span>
                      {isCompleted && <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">✓ Done</span>}
                      {isActive && <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: `${phase.color}20`, color: phase.color }}>Current</span>}
                    </div>
                    <div className="text-xs text-ink/60 mt-0.5">{phase.description}</div>
                  </div>
                  {phase.duration && <span className="text-xs text-ink/40">{phase.duration}</span>}
                  <ChevronRight className="w-4 h-4 text-ink/30" />
                </div>
                {isActive && phase.steps && (
                  <div className="mt-3 ml-8 space-y-1">
                    {phase.steps.map((step, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-ink/70">
                        <span style={{ color: phase.color }}>◆</span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Badges */}
        <div className="mt-6 pt-4 border-t border-ink/10">
          <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-3">Badges Earned</div>
          <div className="flex flex-wrap gap-2">
            {ASCENSION_BADGES.map((b) => {
              const earned = ASCENSION_PHASES.findIndex(p => p.id === activePhase) >= ASCENSION_PHASES.findIndex(p => p.id === b.tier);
              return (
                <div
                  key={b.name}
                  className="flex items-center gap-2 rounded-lg px-3 py-2"
                  style={{
                    background: earned ? "#faf9f7" : "#f5f5f5",
                    border: earned ? "1px solid #E8A51E" : "1px solid #eee",
                    opacity: earned ? 1 : 0.4,
                  }}
                >
                  <span style={{ fontSize: 16 }}>{b.icon}</span>
                  <div>
                    <div className="text-xs font-bold" style={{ color: earned ? "#1c1917" : "#999" }}>{b.name}</div>
                    <div className="text-[10px]" style={{ color: earned ? "#8a5a00" : "#bbb" }}>{b.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Continue button */}
        <div className="mt-6">
          <Link
            to="/ascension-protocols"
            className="w-full flex items-center justify-center gap-2 font-bold text-sm px-6 py-3 rounded-xl"
            style={{ background: "#E8A51E", color: "#0a0a0a" }}
          >
            Continue Your Ascension <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Deals Finder Widget ───────────────────────────────────────────────────────

function DealsFinder() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState(null);
  const [expandedDeal, setExpandedDeal] = useState(null);

  const filteredDeals = SAMPLE_DEALS.filter((deal) => {
    const matchesSearch = !search ||
      deal.title.toLowerCase().includes(search.toLowerCase()) ||
      deal.brand.toLowerCase().includes(search.toLowerCase()) ||
      deal.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !activeCategory || deal.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="bg-white border border-ink/10 rounded-lg overflow-hidden">
      <div className="p-6" style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", color: "#fff" }}>
        <div className="text-xs font-bold uppercase tracking-widest" style={{ color: "#E8A51E" }}>Everyday Savings</div>
        <h3 className="font-heading font-black text-xl mt-1">Deals Finder</h3>
        <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.6)" }}>
          AI-curated discounts for your household. Grocery, wellness, tech, and more.
        </p>
      </div>

      <div className="p-6">
        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search deals... (e.g., 'cleaning supplies')"
            className="w-full pl-10 pr-4 py-2.5 border border-ink/20 rounded-xl text-sm focus:outline-none focus:border-copper"
          />
        </div>

        {/* Category filters */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={() => setActiveCategory(null)}
            className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
            style={{
              background: !activeCategory ? "#1c1917" : "#f5f0e8",
              color: !activeCategory ? "#fff" : "#1c1917",
            }}
          >
            All
          </button>
          {DEAL_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(activeCategory === cat.id ? null : cat.id)}
              className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1"
              style={{
                background: activeCategory === cat.id ? cat.color : "#f5f0e8",
                color: activeCategory === cat.id ? "#fff" : "#1c1917",
              }}
            >
              <span>{cat.icon}</span> {cat.label}
            </button>
          ))}
        </div>

        {/* Deals list */}
        <div className="space-y-3">
          {filteredDeals.length === 0 ? (
            <div className="text-center py-8 text-ink/50 text-sm">
              No deals found. Try a different search or category.
            </div>
          ) : (
            filteredDeals.map((deal) => {
              const isExpanded = expandedDeal === deal.id;
              const cat = DEAL_CATEGORIES.find(c => c.id === deal.category);
              return (
                <div
                  key={deal.id}
                  className="rounded-xl border transition-all"
                  style={{
                    borderColor: isExpanded ? "#E8A51E" : "#eee7db",
                    background: isExpanded ? "#faf9f7" : "#fff",
                  }}
                >
                  <button
                    onClick={() => setExpandedDeal(isExpanded ? null : deal.id)}
                    className="w-full text-left p-4 flex items-center gap-3"
                  >
                    <span className="text-xl">{cat?.icon || "🏷"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-sm text-ink">{deal.title}</div>
                      <div className="text-xs text-ink/60">{deal.brand}</div>
                    </div>
                    <span className="text-sm font-black px-3 py-1 rounded-lg" style={{ background: `${cat?.color || "#E8A51E"}15`, color: cat?.color || "#E8A51E" }}>
                      {deal.discount}
                    </span>
                    <ChevronDown className={`w-4 h-4 text-ink/30 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
                  </button>
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-ink/5 pt-3">
                      <p className="text-sm text-ink/70 mb-3">{deal.description}</p>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 bg-ink/5 rounded-lg px-3 py-2">
                          <Tag className="w-3.5 h-3.5 text-copper" />
                          <span className="font-mono font-bold text-sm text-ink">{deal.code}</span>
                        </div>
                        <span className="text-xs text-ink/50">Expires {new Date(deal.expires).toLocaleDateString()}</span>
                      </div>
                      <button
                        className="mt-3 w-full flex items-center justify-center gap-2 text-xs font-bold px-4 py-2 rounded-lg border border-ink/20 hover:border-copper hover:text-copper transition-colors"
                        onClick={() => {
                          navigator.clipboard?.writeText(deal.code);
                          alert(`Copied: ${deal.code}`);
                        }}
                      >
                        <Tag className="w-3 h-3" /> Copy Code & Shop
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        <div className="mt-4 text-center">
          <Link to="/deals" className="inline-flex items-center gap-2 text-xs font-bold text-copper hover:underline">
            View all deals <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Main Profile Component ────────────────────────────────────────────────────

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
  const [ascensionPhase, setAscensionPhase] = useState("intro");

  const isOwnProfile = !id || id === authUser?.id;

  useEffect(() => {
    const userReq = isOwnProfile
      ? api.get("/auth/me").then(r => r.data)
      : api.get(`/auth/me`).then(r => r.data);

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

  if (loading) return <div className="min-h-screen bg-bone flex items-center justify-center"><p className="text-ink/60">Loading profile...</p></div>;
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

  // Role-based tab set
  const baseTabs = [
    { id: "overview", label: "Overview" },
    { id: "learning", label: "Learning" },
    { id: "ascension", label: "Ascension" },
    { id: "deals", label: "Deals" },
  ];
  if (isOwnProfile) baseTabs.push({ id: "settings", label: "Settings" });

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
                      {status.tier}
                    </span>
                  )}
                  {status?.membership_unlocked && (
                    <span className="px-3 py-1 bg-green-100 border border-green-400 text-green-700 rounded-full text-xs font-bold">
                      Basic Membership Unlocked
                    </span>
                  )}
                  {completedModules > 0 && (
                    <span className="px-3 py-1 bg-blue-100 border border-blue-400 text-blue-700 rounded-full text-xs font-bold">
                      {completedModules} Module{completedModules !== 1 ? "s" : ""} Done
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
        <div className="max-w-7xl mx-auto px-6 flex gap-8 overflow-x-auto">
          {baseTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 font-bold text-sm border-b-2 transition-all whitespace-nowrap ${
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
        {/* ═══════ OVERVIEW ═══════ */}
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

        {/* ═══════ LEARNING ═══════ */}
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

        {/* ═══════ ASCENSION ═══════ */}
        {activeTab === "ascension" && (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <AscensionProgress activePhase={ascensionPhase} setActivePhase={setAscensionPhase} />
            </div>
            <div className="lg:col-span-1">
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 text-ink">Quick Actions</h3>
                <div className="space-y-3">
                  <Link to="/ascension-protocols" className="flex items-center gap-3 p-3 rounded-xl border border-ink/10 hover:border-copper transition-colors">
                    <Sparkles className="w-5 h-5 text-copper" />
                    <div>
                      <div className="font-bold text-sm text-ink">Open Full Course</div>
                      <div className="text-xs text-ink/60">Continue your ascension journey</div>
                    </div>
                  </Link>
                  <Link to="/store" className="flex items-center gap-3 p-3 rounded-xl border border-ink/10 hover:border-copper transition-colors">
                    <Tag className="w-5 h-5 text-copper" />
                    <div>
                      <div className="font-bold text-sm text-ink">Get the Workbook</div>
                      <div className="text-xs text-ink/60">$9.99 · All phases included</div>
                    </div>
                  </Link>
                  <Link to="/courses" className="flex items-center gap-3 p-3 rounded-xl border border-ink/10 hover:border-copper transition-colors">
                    <ExternalLink className="w-5 h-5 text-copper" />
                    <div>
                      <div className="font-bold text-sm text-ink">All Courses</div>
                      <div className="text-xs text-ink/60">Browse the full catalog</div>
                    </div>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═══════ DEALS ═══════ */}
        {activeTab === "deals" && (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <DealsFinder />
            </div>
            <div className="lg:col-span-1">
              <div className="bg-white border border-ink/10 rounded-lg p-6">
                <h3 className="font-bold text-lg mb-4 text-ink">Your Savings</h3>
                <div className="space-y-4">
                  <div className="text-center p-4 rounded-xl" style={{ background: "#faf9f7" }}>
                    <div className="text-3xl font-black text-copper">$0</div>
                    <div className="text-xs text-ink/60 mt-1">Total saved this month</div>
                  </div>
                  <div className="text-center p-4 rounded-xl" style={{ background: "#faf9f7" }}>
                    <div className="text-3xl font-black text-ink">{SAMPLE_DEALS.length}</div>
                    <div className="text-xs text-ink/60 mt-1">Active deals available</div>
                  </div>
                </div>
                <div className="mt-4 p-3 rounded-xl text-xs text-ink/60" style={{ background: "#fef3c7", border: "1px solid #fde68a" }}>
                  <strong className="text-ink">How it works:</strong> Deals are curated from community partners and affiliate networks. Copy a code, shop, and save.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═══════ SETTINGS ═══════ */}
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
                      {saving ? "Saving..." : "Save Changes"}
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
