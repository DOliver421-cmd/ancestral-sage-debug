import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import { WAI_LOGO, BRAND } from "../lib/brand";
import {
  PlusCircle, Heart, HandHelping, BookOpen, Users, Shield,
  Clock, MessageSquare, Flag, Loader2, RefreshCw, Scale,
  ArrowRight, HelpCircle, LogIn, UserPlus, X,
} from "lucide-react";
import { toast } from "sonner";

const CATEGORY_META = {
  skill_offer: { label: "Skill Offer", color: "bg-signal/10 text-signal border-signal/30", icon: BookOpen },
  need:        { label: "Need",        color: "bg-copper/10 text-copper border-copper/30", icon: HandHelping },
  community:   { label: "Community",  color: "bg-blue-100 text-blue-700 border-blue-200", icon: Users },
  story:       { label: "Story",      color: "bg-purple-100 text-purple-700 border-purple-200", icon: Heart },
};

// ── Auth Gate Modal ───────────────────────────────────────────────────────────
function AuthGate({ action, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-sm shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-copper" />
            <span className="font-heading font-bold">Registered Users Only</span>
          </div>
          <button onClick={onClose} className="text-ink/40 hover:text-ink"><X className="w-4 h-4" /></button>
        </div>
        <div className="px-6 py-5">
          <p className="text-sm text-ink/70 leading-relaxed">
            <span className="font-semibold text-ink">{action}</span> is available to registered community members.
            Create a free account or sign in to continue.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <Link
              to="/register"
              className="btn-copper w-full text-sm flex items-center justify-center gap-2"
              data-testid="auth-gate-register"
            >
              <UserPlus className="w-4 h-4" /> Create Free Account
            </Link>
            <Link
              to="/login"
              className="btn-ghost w-full text-sm flex items-center justify-center gap-2"
              data-testid="auth-gate-login"
            >
              <LogIn className="w-4 h-4" /> Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Oliver Guardian warning banner ────────────────────────────────────────────
function OliverBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 p-4 mb-4">
      <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <p className="flex-1 text-sm text-amber-800">
        <span className="font-bold">Oliver Guardian: </span>{message}
      </p>
      <button onClick={onDismiss} className="text-amber-500 hover:text-amber-700 text-xs font-bold">✕</button>
    </div>
  );
}

// ── Post card ─────────────────────────────────────────────────────────────────
function PostCard({ post, onFlag }) {
  const meta = CATEGORY_META[post.category] || CATEGORY_META.community;
  const Icon = meta.icon;
  const daysLeft = Math.max(0, Math.ceil(
    (new Date(post.expires_at) - Date.now()) / 86400000
  ));
  return (
    <div className="card-flat p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border ${meta.color}`}>
          <Icon className="w-3 h-3" />{meta.label}
        </span>
        <div className="flex items-center gap-1 text-xs text-ink/40">
          <Clock className="w-3 h-3" />{daysLeft}d left
        </div>
      </div>
      <p className="text-sm text-ink/80 leading-relaxed whitespace-pre-wrap">{post.content}</p>
      <div className="flex items-center justify-between pt-2 border-t border-ink/5">
        <span className="text-xs text-ink/50">{post.author_name}</span>
        <button onClick={() => onFlag(post.id, "post")}
          className="flex items-center gap-1 text-xs text-ink/30 hover:text-red-500 transition-colors">
          <Flag className="w-3 h-3" /> Flag
        </button>
      </div>
    </div>
  );
}

// ── Need card ─────────────────────────────────────────────────────────────────
function NeedCard({ need, onFlag }) {
  const daysLeft = Math.max(0, Math.ceil(
    (new Date(need.expires_at) - Date.now()) / 86400000
  ));
  return (
    <div className="card-flat p-5 border-l-4 border-copper">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-heading font-bold text-ink">{need.title}</h3>
        <div className="flex items-center gap-1 text-xs text-ink/40 shrink-0">
          <Clock className="w-3 h-3" />{daysLeft}d
        </div>
      </div>
      <p className="text-sm text-ink/70 leading-relaxed">{need.description}</p>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-ink/5">
        <span className="text-xs text-ink/50">{need.author_name} · {need.category}</span>
        <button onClick={() => onFlag(need.id, "need")}
          className="flex items-center gap-1 text-xs text-ink/30 hover:text-red-500 transition-colors">
          <Flag className="w-3 h-3" /> Flag
        </button>
      </div>
    </div>
  );
}

// ── New Post Modal (auth-required action) ─────────────────────────────────────
function NewPostModal({ onClose, onSuccess }) {
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("community");
  const [loading, setLoading] = useState(false);
  const [oliver, setOliver] = useState(null);

  const submit = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setOliver(null);
    try {
      const r = await api.post("/more/post", { content: content.trim(), category });
      if (r.data.oliver_response) { setOliver(r.data.oliver_response); }
      else { toast.success("Posted to M.O.R.E."); onSuccess(); onClose(); }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      toast.error(msg);
      setOliver(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Share with the Community</h2>
          <button onClick={onClose} className="text-ink/40 hover:text-ink"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-6 space-y-4">
          {oliver && <OliverBanner message={oliver} onDismiss={() => setOliver(null)} />}
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper">
              <option value="skill_offer">Skill Offer — I can teach or help with...</option>
              <option value="need">Need — I need help with...</option>
              <option value="community">Community — General post</option>
              <option value="story">Story — Share a community story</option>
            </select>
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">
              Content <span className="normal-case font-normal">({2000 - content.length} left)</span>
            </label>
            <textarea value={content} onChange={e => setContent(e.target.value)} maxLength={2000} rows={5}
              placeholder="Share skills, needs, or community support — no money, no personal info."
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper" />
          </div>
          <p className="text-xs text-ink/40 italic">All posts reviewed by Oliver Guardian. Auto-deletes after 30 days.</p>
        </div>
        <div className="px-6 pb-6 flex gap-3 justify-end">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button onClick={submit} disabled={loading || !content.trim()}
            className="btn-copper text-sm flex items-center gap-2 disabled:opacity-50">
            {loading && <Loader2 className="w-4 h-4 animate-spin" />} Post
          </button>
        </div>
      </div>
    </div>
  );
}

// ── New Need Modal ─────────────────────────────────────────────────────────────
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
      toast.success("Need posted — community will see it.");
      onSuccess(); onClose();
    } catch (err) { toast.error(err?.response?.data?.detail || "Could not post need"); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Post a Need</h2>
          <button onClick={onClose} className="text-ink/40 hover:text-ink"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">What do you need?</label>
            <input value={title} onChange={e => setTitle(e.target.value)} maxLength={120}
              placeholder="Brief title for your need"
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper" />
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Details</label>
            <textarea value={desc} onChange={e => setDesc(e.target.value)} maxLength={1000} rows={4}
              placeholder="Describe what you need — no money, no personal contact info."
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper" />
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper">
              {CATS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
            </select>
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3 justify-end">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button onClick={submit} disabled={loading || !title.trim() || !desc.trim()}
            className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50">
            {loading && <Loader2 className="w-4 h-4 animate-spin" />} Post Need
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
  const [authGate, setAuthGate] = useState(null); // string describing the action

  // Public fetch — no auth token needed
  const fetchPublic = useCallback(async (url) => {
    const r = await fetch(`${BACKEND_URL}/api${url}`);
    if (!r.ok) throw new Error("fetch failed");
    return r.json();
  }, []);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPublic("/more/posts?limit=20");
      setPosts(data.posts || []); setPostsTotal(data.total || 0);
    } catch { toast.error("Could not load posts"); }
    finally { setLoading(false); }
  }, [fetchPublic]);

  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPublic("/more/needs?limit=20");
      setNeeds(data.needs || []); setNeedsTotal(data.total || 0);
    } catch { toast.error("Could not load needs"); }
    finally { setLoading(false); }
  }, [fetchPublic]);

  useEffect(() => {
    if (tab === "posts") loadPosts(); else loadNeeds();
  }, [tab, loadPosts, loadNeeds]);

  // Gate actions behind auth
  const requireAuth = (action, fn) => {
    if (!user) { setAuthGate(action); return; }
    fn();
  };

  const handleFlag = (targetId, targetType) => {
    requireAuth("Flagging content", async () => {
      const reason = window.prompt("Why are you flagging this?") ?? "No reason";
      try {
        await api.post("/more/flag", { target_id: targetId, target_type: targetType, reason });
        toast.success("Flagged for review — thank you.");
      } catch { toast.error("Could not submit flag"); }
    });
  };

  const isAdmin = ["admin", "executive_admin"].includes(user?.role);

  return (
    <>
      {/* Public top bar (no AppShell — this is a public page) */}
      <header className="border-b border-ink/10 bg-bone sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="W.A.I." className="w-9 h-9 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div className="hidden sm:block">
              <div className="overline text-copper text-xs leading-none">{BRAND.short}</div>
              <div className="font-heading font-bold text-xs leading-tight">{BRAND.name}</div>
            </div>
          </Link>

          <div className="flex items-center gap-2 font-heading font-extrabold text-lg">
            <HandHelping className="w-5 h-5 text-copper" />
            M.O.R.E. Help Center
          </div>

          <nav className="flex items-center gap-3">
            <Link to="/helper" className="flex items-center gap-1.5 text-sm font-medium hover:text-copper">
              <HelpCircle className="w-4 h-4" /><span className="hidden sm:inline">Help Center</span>
            </Link>
            {user ? (
              <Link to="/dashboard" className="btn-copper text-sm">Dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="text-sm font-bold uppercase tracking-widest hover:text-copper">Sign In</Link>
                <Link to="/register" className="btn-copper text-sm">Join Free</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <div className="min-h-screen bg-bone text-ink">
        <div className="max-w-5xl mx-auto px-6 py-10">

          {/* Page header */}
          <div className="mb-8">
            <div className="overline text-copper mb-1">Michael Oliver Resource Exchange</div>
            <h1 className="font-heading text-4xl font-extrabold">Community Exchange</h1>
            <p className="text-ink/60 mt-2 text-sm max-w-lg leading-relaxed">
              Browse what the community is offering and asking for. Sign in to share, post needs, or join the chat.
            </p>

            {/* Action buttons — gated */}
            <div className="mt-5 flex flex-wrap gap-3">
              <button
                onClick={() => requireAuth("Sharing with the community", () => setShowPost(true))}
                className="btn-copper text-sm flex items-center gap-2"
                data-testid="btn-share"
              >
                <PlusCircle className="w-4 h-4" /> Share Something
              </button>
              <button
                onClick={() => requireAuth("Posting a need", () => setShowNeed(true))}
                className="btn-primary text-sm flex items-center gap-2"
                data-testid="btn-post-need"
              >
                <HandHelping className="w-4 h-4" /> Post a Need
              </button>
              <button
                onClick={() => requireAuth("Community Chat", () => navigate("/more/chat"))}
                className="flex items-center gap-2 px-4 py-2 border border-ink/20 text-sm font-medium hover:bg-ink hover:text-white transition-colors"
              >
                <MessageSquare className="w-4 h-4" /> Community Chat
                <span className="text-xs text-ink/40 ml-1">(60 min rooms)</span>
              </button>
              <Link
                to="/more/litigation"
                className="flex items-center gap-2 px-4 py-2 border border-signal/40 bg-signal/5 text-sm font-medium hover:bg-signal hover:text-ink transition-colors"
              >
                <Scale className="w-4 h-4 text-signal" /> Legal Help Tool
              </Link>
              {isAdmin && (
                <Link to="/more/admin"
                  className="flex items-center gap-2 px-4 py-2 border border-ink/20 text-sm font-medium hover:bg-ink hover:text-white transition-colors">
                  <Shield className="w-4 h-4" /> Admin
                </Link>
              )}
            </div>
          </div>

          {/* Purge notice */}
          <div className="flex items-center gap-2 text-xs text-ink/40 mb-6">
            <Clock className="w-3.5 h-3.5" />
            Posts auto-purge after 30 days · Chats auto-purge after 60 minutes
          </div>

          {/* Tabs */}
          <div className="flex border-b border-ink/10 mb-6">
            {[
              { key: "posts", label: `Community (${postsTotal})` },
              { key: "needs", label: `Needs Board (${needsTotal})` },
            ].map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={`px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${tab === t.key ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}>
                {t.label}
              </button>
            ))}
            <div className="ml-auto flex items-center">
              <button onClick={tab === "posts" ? loadPosts : loadNeeds} className="p-2 text-ink/40 hover:text-copper transition-colors">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-copper" />
            </div>
          ) : tab === "posts" ? (
            posts.length === 0 ? (
              <div className="text-center py-16 text-ink/40">
                <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No posts yet. Be the first to share with the community.</p>
                <button onClick={() => requireAuth("Sharing with the community", () => setShowPost(true))}
                  className="mt-4 btn-copper text-sm">Share Something</button>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {posts.map(p => <PostCard key={p.id} post={p} onFlag={handleFlag} />)}
              </div>
            )
          ) : (
            needs.length === 0 ? (
              <div className="text-center py-16 text-ink/40">
                <HandHelping className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p>No needs posted yet. Ask for help — that's what we're here for.</p>
                <button onClick={() => requireAuth("Posting a need", () => setShowNeed(true))}
                  className="mt-4 btn-primary text-sm">Post a Need</button>
              </div>
            ) : (
              <div className="space-y-4">
                {needs.map(n => <NeedCard key={n.id} need={n} onFlag={handleFlag} />)}
              </div>
            )
          )}

          {/* Oliver Guardian footer */}
          <div className="mt-12 border border-ink/10 p-5 bg-ink text-white">
            <div className="flex items-start gap-4">
              <Shield className="w-8 h-8 text-signal shrink-0 mt-0.5" />
              <div>
                <div className="font-heading font-bold">Protected by Oliver Guardian</div>
                <p className="text-white/60 text-xs mt-1 leading-relaxed">
                  All posted content is reviewed by our AI moderator before publishing. No money, no personal info, no exploitation — ever.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Auth Gate */}
      {authGate && <AuthGate action={authGate} onClose={() => setAuthGate(null)} />}

      {/* Action modals (only reach here if user is logged in) */}
      {showPost && (
        <NewPostModal onClose={() => setShowPost(false)} onSuccess={() => { if (tab === "posts") loadPosts(); }} />
      )}
      {showNeed && (
        <NewNeedModal onClose={() => setShowNeed(false)} onSuccess={() => { if (tab === "needs") loadNeeds(); }} />
      )}
    </>
  );
}
