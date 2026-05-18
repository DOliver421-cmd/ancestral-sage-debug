import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import { WAI_LOGO, BRAND } from "../lib/brand";
import {
  PlusCircle, HandHelping, BookOpen, Users, Heart, Shield,
  Clock, MessageSquare, Flag, Loader2, Scale, LogIn, UserPlus,
  X, Zap, ChevronRight, HelpCircle, RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

// ── Category config ───────────────────────────────────────────────────────────
const CAT = {
  skill_offer: { label: "Skill Offer",  icon: BookOpen,    bg: "bg-emerald-500",   ring: "ring-emerald-400",  pill: "bg-emerald-500/15 text-emerald-700 border-emerald-300" },
  need:        { label: "Need",         icon: HandHelping, bg: "bg-amber-500",     ring: "ring-amber-400",    pill: "bg-amber-500/15 text-amber-700 border-amber-300" },
  community:   { label: "Community",   icon: Users,       bg: "bg-blue-500",      ring: "ring-blue-400",     pill: "bg-blue-500/15 text-blue-700 border-blue-300" },
  story:       { label: "Story",       icon: Heart,       bg: "bg-purple-500",    ring: "ring-purple-400",   pill: "bg-purple-500/15 text-purple-700 border-purple-300" },
};

// ── Auth Gate ─────────────────────────────────────────────────────────────────
function AuthGate({ action, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-sm shadow-2xl rounded-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="font-heading font-extrabold text-xl">Join the Exchange</div>
            <button onClick={onClose} className="text-white/60 hover:text-white"><X className="w-5 h-5" /></button>
          </div>
          <p className="text-white/80 text-sm mt-2 leading-relaxed">
            <span className="font-semibold text-white">{action}</span> is for registered community members. It's free — always.
          </p>
        </div>
        <div className="p-6 flex flex-col gap-3">
          <Link to="/register" className="flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold py-3 rounded-xl transition-colors" data-testid="auth-gate-register">
            <UserPlus className="w-4 h-4" /> Create Free Account
          </Link>
          <Link to="/login" className="flex items-center justify-center gap-2 border-2 border-ink/20 hover:border-ink font-bold py-3 rounded-xl transition-colors text-sm" data-testid="auth-gate-login">
            <LogIn className="w-4 h-4" /> Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Post card ─────────────────────────────────────────────────────────────────
function PostCard({ post, onFlag }) {
  const cfg = CAT[post.category] || CAT.community;
  const Icon = cfg.icon;
  const daysLeft = Math.max(0, Math.ceil((new Date(post.expires_at) - Date.now()) / 86400000));
  return (
    <div className={`relative bg-white rounded-2xl shadow-sm border-2 border-transparent hover:border-amber-300 hover:shadow-md transition-all overflow-hidden group`}>
      <div className={`h-1.5 ${cfg.bg}`} />
      <div className="p-5">
        <div className="flex items-start justify-between gap-2 mb-3">
          <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full border ${cfg.pill}`}>
            <Icon className="w-3 h-3" />{cfg.label}
          </span>
          <span className="text-xs text-ink/30 flex items-center gap-1"><Clock className="w-3 h-3" />{daysLeft}d</span>
        </div>
        <p className="text-sm text-ink/85 leading-relaxed whitespace-pre-wrap font-medium">{post.content}</p>
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/5">
          <span className="text-xs font-semibold text-ink/50">{post.author_name}</span>
          <button onClick={() => onFlag(post.id, "post")}
            className="flex items-center gap-1 text-xs text-ink/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
            <Flag className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Need card ─────────────────────────────────────────────────────────────────
function NeedCard({ need, onFlag }) {
  const daysLeft = Math.max(0, Math.ceil((new Date(need.expires_at) - Date.now()) / 86400000));
  return (
    <div className="relative bg-white rounded-2xl shadow-sm border-2 border-transparent hover:border-amber-300 hover:shadow-md transition-all overflow-hidden group">
      <div className="h-1.5 bg-amber-500" />
      <div className="p-5">
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full bg-amber-500/15 text-amber-700 border border-amber-300">
            <HandHelping className="w-3 h-3" />Need
          </span>
          <span className="text-xs text-ink/30 flex items-center gap-1"><Clock className="w-3 h-3" />{daysLeft}d</span>
        </div>
        <h3 className="font-heading font-extrabold text-ink text-base mt-2">{need.title}</h3>
        <p className="text-sm text-ink/70 leading-relaxed mt-1">{need.description}</p>
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-ink/5">
          <span className="text-xs font-semibold text-ink/50">{need.author_name} · {need.category}</span>
          <button onClick={() => onFlag(need.id, "need")}
            className="flex items-center gap-1 text-xs text-ink/20 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
            <Flag className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── New Post Modal ────────────────────────────────────────────────────────────
function NewPostModal({ onClose, onSuccess }) {
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("community");
  const [loading, setLoading] = useState(false);
  const [oliver, setOliver] = useState(null);

  const submit = async () => {
    if (!content.trim()) return;
    setLoading(true); setOliver(null);
    try {
      const r = await api.post("/more/post", { content: content.trim(), category });
      if (r.data.oliver_response) setOliver(r.data.oliver_response);
      else { toast.success("Posted to M.O.R.E.!"); onSuccess(); onClose(); }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      toast.error(msg); setOliver(msg);
    } finally { setLoading(false); }
  };

  const cats = [
    { k: "skill_offer", emoji: "🛠️", label: "Skill Offer", sub: "I can teach or help with…" },
    { k: "need",        emoji: "🙏", label: "Need",        sub: "I need help with…" },
    { k: "community",   emoji: "🤝", label: "Community",   sub: "General post" },
    { k: "story",       emoji: "✨", label: "Story",       sub: "Share a win or story" },
  ];

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-5 text-white flex items-center justify-between">
          <div className="font-heading font-extrabold text-lg">Share with the Community</div>
          <button onClick={onClose} className="text-white/60 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-4">
          {oliver && (
            <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 rounded-xl p-4">
              <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <p className="flex-1 text-sm text-amber-800"><span className="font-bold">Oliver Guardian: </span>{oliver}</p>
              <button onClick={() => setOliver(null)} className="text-amber-500 text-xs font-bold">✕</button>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            {cats.map(c => (
              <button key={c.k} onClick={() => setCategory(c.k)}
                className={`rounded-xl p-3 border-2 text-left transition-all ${category === c.k ? "border-blue-500 bg-blue-50" : "border-ink/10 hover:border-ink/30"}`}>
                <div className="text-xl mb-1">{c.emoji}</div>
                <div className="font-bold text-sm">{c.label}</div>
                <div className="text-xs text-ink/50">{c.sub}</div>
              </button>
            ))}
          </div>
          <textarea value={content} onChange={e => setContent(e.target.value)} maxLength={2000} rows={4}
            placeholder="Share skills, support, or community stories — no money, no personal info."
            className="w-full border-2 border-ink/10 focus:border-blue-400 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors" />
          <p className="text-xs text-ink/40 italic text-center">Reviewed by Oliver Guardian · Auto-deletes in 30 days</p>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5 transition-colors">Cancel</button>
          <button onClick={submit} disabled={loading || !content.trim()}
            className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Post It
          </button>
        </div>
      </div>
    </div>
  );
}

// ── New Need Modal ────────────────────────────────────────────────────────────
function NewNeedModal({ onClose, onSuccess }) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [category, setCategory] = useState("general");
  const [loading, setLoading] = useState(false);
  const CATS = ["general","transportation","household","meals","companionship","tutoring","mentorship","other"];

  const submit = async () => {
    if (!title.trim() || !desc.trim()) return;
    setLoading(true);
    try {
      await api.post("/more/need", { title: title.trim(), description: desc.trim(), category });
      toast.success("Need posted — community will see it."); onSuccess(); onClose();
    } catch (err) { toast.error(err?.response?.data?.detail || "Could not post"); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-5 text-white flex items-center justify-between">
          <div>
            <div className="font-heading font-extrabold text-lg">Post a Need</div>
            <div className="text-white/80 text-sm">Ask the community — someone is ready to help</div>
          </div>
          <button onClick={onClose} className="text-white/60 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-3">
          <input value={title} onChange={e => setTitle(e.target.value)} maxLength={120}
            placeholder="What do you need? (brief title)"
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors font-medium" />
          <textarea value={desc} onChange={e => setDesc(e.target.value)} maxLength={1000} rows={4}
            placeholder="Describe your need — no money, no personal contact info."
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors" />
          <select value={category} onChange={e => setCategory(e.target.value)}
            className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors bg-white">
            {CATS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
          </select>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5 transition-colors">Cancel</button>
          <button onClick={submit} disabled={loading || !title.trim() || !desc.trim()}
            className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HandHelping className="w-4 h-4" />} Post My Need
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function More() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState("posts");
  const [posts, setPosts] = useState([]);
  const [needs, setNeeds] = useState([]);
  const [postsTotal, setPostsTotal] = useState(0);
  const [needsTotal, setNeedsTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showPost, setShowPost] = useState(false);
  const [showNeed, setShowNeed] = useState(false);
  const [authGate, setAuthGate] = useState(null);
  const [catFilter, setCatFilter] = useState("all");

  const fetchPublic = useCallback(async (url) => {
    const r = await fetch(`${BACKEND_URL}/api${url}`);
    if (!r.ok) throw new Error("fetch failed");
    return r.json();
  }, []);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try { const d = await fetchPublic("/more/posts?limit=30"); setPosts(d.posts || []); setPostsTotal(d.total || 0); }
    catch { toast.error("Could not load posts"); }
    finally { setLoading(false); }
  }, [fetchPublic]);

  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try { const d = await fetchPublic("/more/needs?limit=30"); setNeeds(d.needs || []); setNeedsTotal(d.total || 0); }
    catch { toast.error("Could not load needs"); }
    finally { setLoading(false); }
  }, [fetchPublic]);

  useEffect(() => { if (tab === "posts") loadPosts(); else loadNeeds(); }, [tab, loadPosts, loadNeeds]);

  const requireAuth = (action, fn) => { if (!user) { setAuthGate(action); return; } fn(); };

  const handleFlag = (targetId, targetType) => {
    requireAuth("Flagging content", async () => {
      const reason = window.prompt("Why are you flagging this?") ?? "No reason";
      try { await api.post("/more/flag", { target_id: targetId, target_type: targetType, reason }); toast.success("Flagged — thank you."); }
      catch { toast.error("Could not submit flag"); }
    });
  };

  const filteredPosts = catFilter === "all" ? posts : posts.filter(p => p.category === catFilter);

  return (
    <>
      {/* Sticky navbar */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-ink/10">
        <div className="max-w-6xl mx-auto px-5 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span className="font-heading font-bold text-sm hidden sm:block">{BRAND.short}</span>
          </Link>
          <div className="flex items-center gap-2 font-heading font-extrabold text-base">
            <HandHelping className="w-5 h-5 text-amber-500" />
            <span>M.O.R.E.</span>
            <span className="hidden sm:inline text-ink/50 font-normal text-sm">Michael Oliver Resource Exchange</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link to="/helper" className="hidden sm:flex items-center gap-1 text-sm font-medium hover:text-amber-500 transition-colors">
              <HelpCircle className="w-4 h-4" /> Help AI
            </Link>
            {user ? (
              <Link to="/app/more" className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-ink font-bold text-sm px-4 py-2 rounded-xl transition-colors">
                Full Hub <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-sm font-bold hover:text-amber-500 transition-colors">Sign In</Link>
                <Link to="/register" className="bg-amber-500 hover:bg-amber-400 text-ink font-bold text-sm px-4 py-2 rounded-xl transition-colors">Join Free</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <div className="min-h-screen" style={{ background: "linear-gradient(180deg,#0f172a 0%,#1e1b4b 280px,#f8f7f4 280px)" }}>

        {/* ── Hero ──────────────────────────────────────────────────────────── */}
        <div className="max-w-6xl mx-auto px-5 pt-10 pb-16 text-white">
          <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 text-sm font-semibold mb-5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Community Exchange — Open Now
          </div>
          <h1 className="font-heading text-5xl lg:text-7xl font-extrabold leading-[0.95] mb-5">
            Give a skill.<br />
            <span className="text-amber-400">Ask for help.</span><br />
            <span className="text-blue-400">Build together.</span>
          </h1>
          <p className="text-white/70 max-w-xl text-lg leading-relaxed mb-8">
            M.O.R.E. is a community exchange — no money changes hands, no exploitation, no judgment.
            Share what you know. Ask for what you need. Show up for each other.
          </p>

          {/* Stat strip */}
          <div className="flex flex-wrap gap-6 mb-8 text-sm">
            {[
              ["🛠️", postsTotal, "skills &amp; stories shared"],
              ["🙏", needsTotal, "needs on the board"],
              ["🛡️", "100%", "moderated by Oliver Guardian"],
            ].map(([icon, val, label]) => (
              <div key={label} className="flex items-center gap-2">
                <span>{icon}</span>
                <span className="font-heading font-extrabold text-amber-400 text-xl">{val}</span>
                <span className="text-white/50" dangerouslySetInnerHTML={{ __html: label }} />
              </div>
            ))}
          </div>

          {/* Big action buttons */}
          <div className="flex flex-wrap gap-3">
            <button onClick={() => requireAuth("Sharing with the community", () => setShowPost(true))}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-extrabold text-base px-6 py-3.5 rounded-2xl shadow-lg shadow-amber-500/30 transition-all hover:scale-105 active:scale-100"
              data-testid="btn-share">
              <PlusCircle className="w-5 h-5" /> Share a Skill or Story
            </button>
            <button onClick={() => requireAuth("Posting a need", () => setShowNeed(true))}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100"
              data-testid="btn-post-need">
              <HandHelping className="w-5 h-5" /> Post a Need
            </button>
            <button onClick={() => requireAuth("Community Chat", () => navigate("/more/chat"))}
              className="flex items-center gap-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/40 text-blue-200 font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100">
              <MessageSquare className="w-5 h-5" /> Community Chat
            </button>
            <Link to="/more/litigation"
              className="flex items-center gap-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 text-emerald-200 font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100">
              <Scale className="w-5 h-5" /> Legal Help Tool
            </Link>
          </div>
        </div>

        {/* ── Feed area ─────────────────────────────────────────────────────── */}
        <div className="max-w-6xl mx-auto px-5 pb-20">

          {/* Tab + filter bar */}
          <div className="bg-white rounded-2xl shadow-lg p-4 mb-6 flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex gap-2">
              {[{ k: "posts", label: `Community (${postsTotal})` }, { k: "needs", label: `Needs (${needsTotal})` }].map(t => (
                <button key={t.k} onClick={() => setTab(t.k)}
                  className={`px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${tab === t.k ? "bg-ink text-white" : "text-ink/50 hover:text-ink hover:bg-ink/5"}`}>
                  {t.label}
                </button>
              ))}
            </div>

            {tab === "posts" && (
              <div className="flex gap-2 flex-wrap sm:ml-auto">
                {[["all", "All"], ["skill_offer", "🛠️ Skills"], ["community", "🤝 Community"], ["story", "✨ Stories"]].map(([k, label]) => (
                  <button key={k} onClick={() => setCatFilter(k)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all ${catFilter === k ? "bg-amber-500 text-ink" : "bg-ink/5 text-ink/60 hover:bg-ink/10"}`}>
                    {label}
                  </button>
                ))}
              </div>
            )}

            <button onClick={tab === "posts" ? loadPosts : loadNeeds}
              className="sm:ml-auto text-ink/30 hover:text-copper transition-colors p-1.5" title="Refresh">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
                <span className="text-ink/40 text-sm">Loading community…</span>
              </div>
            </div>
          ) : tab === "posts" ? (
            filteredPosts.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-16 text-center">
                <div className="text-5xl mb-4">{catFilter === "all" ? "🌱" : "🔍"}</div>
                <div className="font-heading text-2xl font-bold">Be the first to share</div>
                <p className="text-ink/50 mt-2 max-w-sm mx-auto">This community is ready for you. Drop a skill offer, share a win, or just say hello.</p>
                <button onClick={() => requireAuth("Sharing with the community", () => setShowPost(true))}
                  className="mt-6 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-3 rounded-xl transition-colors inline-flex items-center gap-2">
                  <PlusCircle className="w-4 h-4" /> Share Something
                </button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredPosts.map(p => <PostCard key={p.id} post={p} onFlag={handleFlag} />)}
              </div>
            )
          ) : (
            needs.length === 0 ? (
              <div className="bg-white rounded-2xl shadow p-16 text-center">
                <div className="text-5xl mb-4">🙌</div>
                <div className="font-heading text-2xl font-bold">No open needs right now</div>
                <p className="text-ink/50 mt-2 max-w-sm mx-auto">If you need something, ask. This community shows up.</p>
                <button onClick={() => requireAuth("Posting a need", () => setShowNeed(true))}
                  className="mt-6 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-8 py-3 rounded-xl transition-colors inline-flex items-center gap-2">
                  <HandHelping className="w-4 h-4" /> Post a Need
                </button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {needs.map(n => <NeedCard key={n.id} need={n} onFlag={handleFlag} />)}
              </div>
            )
          )}

          {/* Member upgrade CTA */}
          {!user && (
            <div className="mt-12 rounded-2xl overflow-hidden shadow-xl"
              style={{ background: "linear-gradient(135deg,#1e1b4b,#312e81,#1e3a8a)" }}>
              <div className="p-8 sm:p-10 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div className="text-white">
                  <div className="font-heading font-extrabold text-3xl mb-2">Members get the full experience.</div>
                  <p className="text-white/70 max-w-lg leading-relaxed">
                    Post, share skills, chat in community rooms, access the Legal Aid tool, and get AI Help Center support — all 100% free. No catch.
                  </p>
                </div>
                <div className="flex flex-col gap-3 shrink-0 w-full sm:w-auto">
                  <Link to="/register"
                    className="flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-extrabold py-3.5 px-8 rounded-2xl transition-all hover:scale-105 shadow-lg shadow-amber-500/30">
                    <UserPlus className="w-5 h-5" /> Create Free Account
                  </Link>
                  <Link to="/login"
                    className="flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-bold py-3 px-8 rounded-2xl transition-colors">
                    <LogIn className="w-4 h-4" /> Sign In
                  </Link>
                </div>
              </div>
            </div>
          )}

          {user && (
            <div className="mt-10 bg-white rounded-2xl shadow p-6 flex items-center justify-between gap-4 border-2 border-amber-200">
              <div>
                <div className="font-heading font-bold text-lg">You're in the exchange.</div>
                <p className="text-sm text-ink/60 mt-0.5">Unlock all M.O.R.E. features — chat rooms, legal tools, AI help, and more.</p>
              </div>
              <Link to="/app/more"
                className="shrink-0 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-6 py-3 rounded-xl transition-all hover:scale-105">
                Full Hub <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          )}

          {/* Oliver footer */}
          <div className="mt-8 bg-ink rounded-2xl p-5 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-signal/20 flex items-center justify-center shrink-0">
              <Shield className="w-5 h-5 text-signal" />
            </div>
            <div>
              <div className="font-heading font-bold text-white text-sm">Protected by Oliver Guardian</div>
              <p className="text-white/50 text-xs mt-0.5 leading-relaxed">
                All content is AI-moderated before publishing. No money, no personal info, no exploitation — ever.
              </p>
            </div>
          </div>
        </div>
      </div>

      {authGate && <AuthGate action={authGate} onClose={() => setAuthGate(null)} />}
      {showPost && <NewPostModal onClose={() => setShowPost(false)} onSuccess={() => { if (tab === "posts") loadPosts(); }} />}
      {showNeed && <NewNeedModal onClose={() => setShowNeed(false)} onSuccess={() => { if (tab === "needs") loadNeeds(); }} />}
    </>
  );
}
