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
import FlagModal from "../components/FlagModal";

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

// ── Crisis Resources Panel ─────────────────────────────────────────────────────
function CrisisPanel({ oliverMessage, resources, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-900 to-blue-700 p-6 text-white">
          <div className="flex items-center gap-3 mb-3">
            <Heart className="w-6 h-6 text-blue-300 shrink-0" />
            <div className="font-heading font-extrabold text-lg">Oliver Guardian — We See You</div>
          </div>
          <p className="text-white/90 text-sm leading-relaxed">{oliverMessage}</p>
        </div>
        <div className="p-6">
          <p className="text-sm font-bold text-slate-800 mb-4">Free resources available right now:</p>
          <div className="space-y-3">
            {(resources || []).map((r, i) => (
              <div key={i} className="flex gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
                <Shield className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-sm text-blue-900">{r.name}</div>
                  <div className="text-xs text-slate-600 mt-0.5">{r.description}</div>
                  <div className="text-xs font-bold text-blue-700 mt-1">{r.contact}</div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-4 text-center italic">
            If you're in immediate danger, call 911. You are not alone.
          </p>
        </div>
        <div className="px-6 pb-6">
          <button onClick={onClose}
            className="w-full py-3 bg-blue-700 hover:bg-blue-600 text-white font-bold rounded-xl transition-colors">
            I understand — close this
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Oliver Guardian Message ────────────────────────────────────────────────────
function OliverMessage({ message, postId, postType, onDismiss }) {
  const [appealing, setAppealing] = useState(false);
  const [appealReason, setAppealReason] = useState("");
  const [appealSent, setAppealSent] = useState(false);
  const [appealLoading, setAppealLoading] = useState(false);

  const submitAppeal = async () => {
    if (!appealReason.trim() || !postId) return;
    setAppealLoading(true);
    try {
      await api.post(`/more/appeal?target_id=${postId}&reason=${encodeURIComponent(appealReason.trim())}`);
      setAppealSent(true);
      toast.success("Appeal submitted — a real human will review within 48 hours.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not submit appeal");
    } finally { setAppealLoading(false); }
  };

  return (
    <div className="rounded-2xl overflow-hidden border-2 border-amber-300 bg-amber-50">
      <div className="flex items-start gap-3 p-4">
        <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-bold text-sm text-amber-900 mb-1">Oliver Guardian</div>
          <p className="text-sm text-amber-800 leading-relaxed">{message}</p>
        </div>
        <button onClick={onDismiss} className="text-amber-400 hover:text-amber-600 text-xs font-bold shrink-0">✕</button>
      </div>
      {postId && !appealSent && (
        <div className="border-t border-amber-200 px-4 pb-4 pt-3">
          {!appealing ? (
            <button onClick={() => setAppealing(true)}
              className="text-xs font-bold text-amber-700 hover:text-amber-900 underline underline-offset-2">
              Think this was a mistake? Appeal this decision →
            </button>
          ) : (
            <div className="space-y-2">
              <textarea value={appealReason} onChange={e => setAppealReason(e.target.value)} rows={2}
                placeholder="Explain why your post should be approved…"
                className="w-full border border-amber-300 rounded-lg px-3 py-2 text-xs resize-none outline-none focus:border-amber-500" />
              <div className="flex gap-2">
                <button onClick={() => setAppealing(false)}
                  className="text-xs text-amber-600 hover:text-amber-800 font-medium">Cancel</button>
                <button onClick={submitAppeal} disabled={!appealReason.trim() || appealLoading}
                  className="flex-1 py-1.5 bg-amber-500 hover:bg-amber-400 text-ink font-bold text-xs rounded-lg disabled:opacity-50 transition-colors">
                  {appealLoading ? "Submitting…" : "Submit Appeal"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      {appealSent && (
        <div className="border-t border-amber-200 px-4 pb-4 pt-3">
          <p className="text-xs text-green-700 font-medium">✓ Appeal submitted. We'll review within 48 hours.</p>
        </div>
      )}
    </div>
  );
}

// ── New Post Modal ────────────────────────────────────────────────────────────
function NewPostModal({ onClose, onSuccess }) {
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("community");
  const [loading, setLoading] = useState(false);
  const [oliver, setOliver] = useState(null);
  const [oliverPostId, setOliverPostId] = useState(null);
  const [crisis, setCrisis] = useState(null);
  const [pendingReview, setPendingReview] = useState(false);

  const submit = async () => {
    if (!content.trim()) return;
    setLoading(true); setOliver(null); setOliverPostId(null); setCrisis(null); setPendingReview(false);
    try {
      const r = await api.post("/more/post", { content: content.trim(), category });
      if (r.data.crisis) {
        setCrisis({ message: r.data.oliver_response, resources: r.data.crisis_resources });
      } else if (r.data.pending_review) {
        setPendingReview(true);
        setOliver(r.data.oliver_response);
        setOliverPostId(r.data.post?.id || null);
      } else if (r.data.oliver_response) {
        setOliver(r.data.oliver_response);
        setOliverPostId(r.data.post?.id || null);
      } else {
        toast.success("Posted to M.O.R.E.!");
        onSuccess();
        onClose();
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      setOliver(msg);
    } finally { setLoading(false); }
  };

  const cats = [
    { k: "skill_offer", emoji: "🛠️", label: "Skill Offer", sub: "I can teach or help with…" },
    { k: "need",        emoji: "🙏", label: "Need",        sub: "I need help with…" },
    { k: "community",   emoji: "🤝", label: "Community",   sub: "General post" },
    { k: "story",       emoji: "✨", label: "Story",       sub: "Share a win or story" },
  ];

  if (crisis) {
    return <CrisisPanel oliverMessage={crisis.message} resources={crisis.resources} onClose={onClose} />;
  }

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-5 text-white flex items-center justify-between">
          <div className="font-heading font-extrabold text-lg">Share with the Community</div>
          <button onClick={onClose} className="text-white/60 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-4">
          {pendingReview && !oliver && (
            <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <Clock className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800">
                <span className="font-bold">Held for review.</span> Oliver Guardian flagged this for a quick human check.
                It'll be up within 48 hours if it looks good.
              </p>
            </div>
          )}
          {oliver && (
            <OliverMessage
              message={oliver}
              postId={oliverPostId}
              postType="post"
              onDismiss={() => { setOliver(null); setOliverPostId(null); }}
            />
          )}
          {!pendingReview && (
            <>
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
              <p className="text-xs text-ink/40 italic text-center">
                Reviewed by Oliver Guardian · Auto-deletes in 30 days · <span className="text-blue-600 cursor-default" title="No money. No personal contact info. No harassment. Skills and community only.">Community rules</span>
              </p>
            </>
          )}
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5 transition-colors">
            {pendingReview ? "Close" : "Cancel"}
          </button>
          {!pendingReview && (
            <button onClick={submit} disabled={loading || !content.trim()}
              className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Post It
            </button>
          )}
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
  const [oliver, setOliver] = useState(null);
  const [oliverNeedId, setOliverNeedId] = useState(null);
  const [crisis, setCrisis] = useState(null);
  const [pendingReview, setPendingReview] = useState(false);
  const CATS = ["general","transportation","housing","household","meals","companionship","tutoring","mentorship","job_search","other"];

  const submit = async () => {
    if (!title.trim() || !desc.trim()) return;
    setLoading(true); setOliver(null); setOliverNeedId(null); setCrisis(null); setPendingReview(false);
    try {
      const r = await api.post("/more/need", { title: title.trim(), description: desc.trim(), category });
      if (r.data.crisis) {
        setCrisis({ message: r.data.oliver_response, resources: r.data.crisis_resources });
      } else if (r.data.pending_review) {
        setPendingReview(true);
        setOliver(r.data.oliver_response);
        setOliverNeedId(r.data.need?.id || null);
      } else {
        toast.success("Need posted — the community will see it.");
        onSuccess();
        onClose();
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      setOliver(msg);
    } finally { setLoading(false); }
  };

  if (crisis) {
    return <CrisisPanel oliverMessage={crisis.message} resources={crisis.resources} onClose={onClose} />;
  }

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
          {pendingReview && (
            <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <Clock className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800">
                <span className="font-bold">Held for review.</span> A real person will check this within 48 hours. If it's legitimate, it'll go live.
              </p>
            </div>
          )}
          {oliver && (
            <OliverMessage
              message={oliver}
              postId={oliverNeedId}
              postType="need"
              onDismiss={() => { setOliver(null); setOliverNeedId(null); }}
            />
          )}
          {!pendingReview && (
            <>
              <input value={title} onChange={e => setTitle(e.target.value)} maxLength={120}
                placeholder="What do you need? (brief title)"
                className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors font-medium" />
              <textarea value={desc} onChange={e => setDesc(e.target.value)} maxLength={1000} rows={4}
                placeholder="Describe your need — no money, no personal contact info."
                className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm resize-none outline-none transition-colors" />
              <select value={category} onChange={e => setCategory(e.target.value)}
                className="w-full border-2 border-ink/10 focus:border-amber-400 rounded-xl px-4 py-3 text-sm outline-none transition-colors bg-white">
                {CATS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.replace(/_/g, " ").slice(1)}</option>)}
              </select>
            </>
          )}
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="flex-1 py-3 border-2 border-ink/10 rounded-xl font-bold text-sm hover:bg-ink/5 transition-colors">
            {pendingReview ? "Close" : "Cancel"}
          </button>
          {!pendingReview && (
            <button onClick={submit} disabled={loading || !title.trim() || !desc.trim()}
              className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 text-ink font-bold rounded-xl text-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-colors">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HandHelping className="w-4 h-4" />} Post My Need
            </button>
          )}
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
  const [flagTarget, setFlagTarget] = useState(null);

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
    requireAuth("Flagging content", () => setFlagTarget({ targetId, targetType }));
  };

  const filteredPosts = catFilter === "all" ? posts : posts.filter(p => p.category === catFilter);

  return (
    <>
      {/* ── Sticky navbar ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-ink/10 shadow-sm">
        <div className="max-w-6xl mx-auto px-5 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <img src={WAI_LOGO} alt="W.A.I." className="w-8 h-8 object-contain" style={{ mixBlendMode: "multiply" }} />
            <span className="font-heading font-bold text-sm hidden sm:block">{BRAND.short}</span>
          </Link>
          <div className="flex items-center gap-2 font-heading font-extrabold text-base">
            <HandHelping className="w-5 h-5 text-amber-500" />
            <span>M.O.R.E.</span>
            <span className="hidden sm:inline text-ink/40 font-normal text-sm">Michael Oliver Resource Exchange</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link to="/helper" className="hidden sm:flex items-center gap-1.5 text-sm font-semibold text-ink/60 hover:text-amber-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-amber-50">
              <HelpCircle className="w-4 h-4" /> Help AI
            </Link>
            {user ? (
              <Link to="/app/more" className="flex items-center gap-1.5 bg-amber-500 hover:bg-amber-400 text-ink font-bold text-sm px-4 py-2 rounded-xl transition-colors shadow-sm">
                Full Hub <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            ) : (
              <>
                <Link to="/login" className="text-sm font-bold text-ink/70 hover:text-ink transition-colors px-3 py-2">Sign In</Link>
                <Link to="/register" className="bg-amber-500 hover:bg-amber-400 text-ink font-extrabold text-sm px-5 py-2 rounded-xl transition-colors shadow-sm">Join Free</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <div className="min-h-screen bg-slate-50">

        {/* ── HERO — full dark section, not a gradient trick ─────────────── */}
        <div style={{ background: "linear-gradient(135deg,#0b1f3a 0%,#1e1b4b 60%,#0b203f 100%)" }}>
          <div className="max-w-6xl mx-auto px-5 pt-12 pb-14 text-white">

            {/* Eyebrow */}
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 text-sm font-semibold mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Community Exchange — Open Now
            </div>

            {/* Headlines */}
            <h1 className="font-heading font-extrabold leading-[0.92] mb-4" style={{ fontSize: "clamp(2.8rem,7vw,5.5rem)" }}>
              Give a skill.<br />
              <span style={{ color: "#f59e0b" }}>Ask for help.</span><br />
              <span style={{ color: "#93c5fd" }}>Build together.</span>
            </h1>

            {/* Mission statement — the investor pitch */}
            <p className="text-white/80 max-w-2xl text-lg leading-relaxed mb-3">
              M.O.R.E. is a community-powered exchange where <strong className="text-white">no money changes hands</strong> — only skills, time, and knowledge.
              Named in honor of <strong className="text-amber-300">Michael Oliver</strong>, a community organizer who believed that ordinary people, given the right structure, take extraordinary care of each other.
            </p>
            <p className="text-white/55 max-w-xl text-sm leading-relaxed mb-10">
              No exploitation. No judgment. No gatekeeping. Share what you know. Ask for what you need. Show up for your neighbor.
            </p>

            {/* Action buttons — all on the dark background, all clearly readable */}
            <div className="flex flex-wrap gap-3 mb-12">
              <button onClick={() => requireAuth("Sharing with the community", () => setShowPost(true))}
                className="flex items-center gap-2 font-extrabold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100 shadow-lg"
                style={{ background: "#f59e0b", color: "#0b1f3a" }}
                data-testid="btn-share">
                <PlusCircle className="w-5 h-5" /> Share a Skill or Story
              </button>
              <button onClick={() => requireAuth("Posting a need", () => setShowNeed(true))}
                className="flex items-center gap-2 font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100"
                style={{ background: "rgba(255,255,255,0.12)", border: "1.5px solid rgba(255,255,255,0.35)", color: "#fff" }}
                data-testid="btn-post-need">
                <HandHelping className="w-5 h-5" /> Post a Need
              </button>
              <button onClick={() => requireAuth("Community Chat", () => navigate("/more/chat"))}
                className="flex items-center gap-2 font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100"
                style={{ background: "rgba(96,165,250,0.18)", border: "1.5px solid rgba(147,197,253,0.45)", color: "#bfdbfe" }}>
                <MessageSquare className="w-5 h-5" /> Community Chat
              </button>
              <Link to="/more/litigation"
                className="flex items-center gap-2 font-bold text-base px-6 py-3.5 rounded-2xl transition-all hover:scale-105 active:scale-100"
                style={{ background: "rgba(52,211,153,0.18)", border: "1.5px solid rgba(110,231,183,0.45)", color: "#a7f3d0" }}>
                <Scale className="w-5 h-5" /> Legal Help Tool
              </Link>
            </div>

            {/* Stat strip */}
            <div className="flex flex-wrap gap-8 border-t border-white/10 pt-8">
              <div>
                <div className="font-heading font-extrabold text-3xl text-amber-400">{postsTotal > 0 ? postsTotal.toLocaleString() : "—"}</div>
                <div className="text-white/50 text-sm mt-0.5">skills &amp; stories shared</div>
              </div>
              <div>
                <div className="font-heading font-extrabold text-3xl text-amber-400">{needsTotal > 0 ? needsTotal.toLocaleString() : "—"}</div>
                <div className="text-white/50 text-sm mt-0.5">community needs posted</div>
              </div>
              <div>
                <div className="font-heading font-extrabold text-3xl text-emerald-400">100%</div>
                <div className="text-white/50 text-sm mt-0.5">AI-moderated before publishing</div>
              </div>
              <div>
                <div className="font-heading font-extrabold text-3xl text-blue-300">Free</div>
                <div className="text-white/50 text-sm mt-0.5">always — no subscriptions, ever</div>
              </div>
            </div>
          </div>
        </div>

        {/* ── WHY M.O.R.E. — mission pillars ────────────────────────────────── */}
        <div className="bg-white border-b border-slate-100">
          <div className="max-w-6xl mx-auto px-5 py-12">
            <div className="text-center mb-10">
              <div className="inline-block text-xs font-bold tracking-widest text-amber-600 uppercase mb-2 px-3 py-1 bg-amber-50 rounded-full border border-amber-200">The Mission</div>
              <h2 className="font-heading font-extrabold text-2xl lg:text-3xl text-slate-900 mt-2">
                Built for the communities institutions forgot.
              </h2>
              <p className="text-slate-500 max-w-xl mx-auto mt-3 leading-relaxed">
                Every neighborhood has people who know things, people who need things, and people willing to help — they just need the right place to meet.
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  icon: "🤝",
                  color: "#f59e0b",
                  bg: "#fffbeb",
                  border: "#fde68a",
                  title: "Skill Exchange, Not Charity",
                  body: "This is not a handout platform. Every member both gives and receives. The electrician teaches. The cook feeds. The accountant explains. Dignity is built into the structure."
                },
                {
                  icon: "🛡️",
                  color: "#0284c7",
                  bg: "#f0f9ff",
                  border: "#bae6fd",
                  title: "Oliver Guardian Protects Everyone",
                  body: "Every post passes through our AI moderation layer before it goes live. No scams, no exploitation, no personal info exposed. The community stays safe by design."
                },
                {
                  icon: "⚖️",
                  color: "#059669",
                  bg: "#f0fdf4",
                  border: "#bbf7d0",
                  title: "Legal Tools — No Lawyer Required",
                  body: "Understand your rights. Read a letter. Respond to a notice. Our plain-language Legal Help Tool turns intimidating documents into clear action steps."
                },
              ].map(({ icon, color, bg, border, title, body }) => (
                <div key={title} className="rounded-2xl p-6 border-2" style={{ background: bg, borderColor: border }}>
                  <div className="text-4xl mb-4">{icon}</div>
                  <h3 className="font-heading font-extrabold text-lg mb-2" style={{ color }}>{title}</h3>
                  <p className="text-slate-600 text-sm leading-relaxed">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Feed area ─────────────────────────────────────────────────────── */}
        <div className="max-w-6xl mx-auto px-5 pb-20 pt-8">

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

          {/* Featured creator spotlight */}
          <div className="mt-8 bg-gradient-to-r from-amber-50 to-amber-100/50 border-2 border-amber-200 rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center gap-5">
            <div className="w-14 h-14 rounded-full bg-amber-500/20 border-2 border-amber-300 flex items-center justify-center text-3xl shrink-0">🌊</div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-1">Featured Community Creator</div>
              <div className="font-heading font-extrabold text-xl text-ink leading-tight">NAM Oshun</div>
              <p className="text-sm text-ink/60 mt-0.5">Poet · Spoken Word Artist · Community Organizer · M.O.R.E. Founding Member</p>
            </div>
            <Link to="/creator/nam-oshun"
              className="shrink-0 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-ink font-bold px-5 py-2.5 rounded-xl transition-all hover:scale-105 text-sm">
              View Profile <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Oliver footer — character introduction */}
          <div className="mt-8 bg-ink rounded-2xl overflow-hidden">
            {/* Header band */}
            <div className="bg-gradient-to-r from-blue-700 to-blue-900 px-6 py-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-white/10 border-2 border-white/20 flex items-center justify-center shrink-0">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-heading font-extrabold text-white text-base tracking-wide">Meet Oliver Guardian</div>
                <div className="text-blue-200 text-xs font-medium">Community Protector · M.O.R.E. Help Center</div>
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4">
              {/* Who he is */}
              <p className="text-white/80 text-sm leading-relaxed">
                Oliver is named after <span className="text-white font-semibold">Michael Oliver</span> — the British disability rights activist and sociologist who argued that society, not the individual, is the source of barriers that exclude people from full participation.
                That principle lives here. Oliver Guardian exists to remove barriers, not add them.
              </p>

              {/* What he does */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { icon: "🛡️", label: "He reviews every post", sub: "Before anything goes live, Oliver reads it. Fast, consistent, no favoritism." },
                  { icon: "🤝", label: "He leads with grace", sub: "First-time missteps get a gentle correction — not an instant ban. Community first." },
                  { icon: "📋", label: "He keeps a record", sub: "Every decision is logged. You can appeal. Admins can audit. Nothing is hidden." },
                ].map(({ icon, label, sub }) => (
                  <div key={label} className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <div className="text-2xl mb-2">{icon}</div>
                    <div className="text-white font-semibold text-xs mb-1">{label}</div>
                    <div className="text-white/50 text-xs leading-relaxed">{sub}</div>
                  </div>
                ))}
              </div>

              {/* Rules summary */}
              <div className="bg-white/5 rounded-xl px-5 py-4 border border-white/10">
                <div className="text-white/60 text-xs font-bold uppercase tracking-widest mb-2">Community Rules Oliver Enforces</div>
                <ul className="text-white/60 text-xs space-y-1 leading-relaxed list-none">
                  {[
                    "No money, payments, or financial solicitation of any kind",
                    "No personal contact information (phone, address, email) in posts",
                    "No exploitation, scams, or predatory offers",
                    "No hate speech, slurs, or targeted harassment",
                    "Skills, stories, needs, and community — that's what belongs here",
                  ].map(rule => (
                    <li key={rule} className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5 shrink-0">·</span>
                      <span>{rule}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Footer line */}
              <div className="flex items-center justify-between pt-1 border-t border-white/10">
                <p className="text-white/30 text-xs">
                  Oliver is powered by AI · All decisions are human-reviewable · Content auto-expires in 30 days
                </p>
                <Link to="/" className="text-blue-400 text-xs font-semibold hover:text-blue-300 transition-colors whitespace-nowrap ml-4">
                  Back to home →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {authGate && <AuthGate action={authGate} onClose={() => setAuthGate(null)} />}
      {showPost && <NewPostModal onClose={() => setShowPost(false)} onSuccess={() => { if (tab === "posts") loadPosts(); }} />}
      {showNeed && <NewNeedModal onClose={() => setShowNeed(false)} onSuccess={() => { if (tab === "needs") loadNeeds(); }} />}
      {flagTarget && <FlagModal targetId={flagTarget.targetId} targetType={flagTarget.targetType} onClose={() => setFlagTarget(null)} />}
    </>
  );
}
