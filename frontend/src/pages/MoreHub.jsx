import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  HandHelping, MessageSquare, Scale, HelpCircle, Shield, Flag,
  Trash2, PlusCircle, BookOpen, Heart, Users, Clock, Loader2,
  RefreshCw, ArrowRight, X, Layers, Star, Eye,
} from "lucide-react";
import { toast } from "sonner";

// ─── Role config ──────────────────────────────────────────────────────────────
const ROLE_CONFIG = {
  student: {
    label: "Community Member",
    color: "text-signal",
    features: ["browse", "post", "need", "chat", "legal", "helper"],
    welcome: "Welcome to your M.O.R.E. Help Center. Share skills, find support, and know your rights.",
  },
  instructor: {
    label: "Instructor",
    color: "text-copper",
    features: ["browse", "post", "need", "chat", "legal", "helper", "flag_view"],
    welcome: "M.O.R.E. Help Center — Instructor access. You can also view flagged content reports.",
  },
  admin: {
    label: "Administrator",
    color: "text-amber-500",
    features: ["browse", "post", "need", "chat", "legal", "helper", "flag_view", "flag_manage", "purge"],
    welcome: "M.O.R.E. Help Center — Admin access. Full moderation and purge controls available.",
  },
  executive_admin: {
    label: "Executive Director",
    color: "text-red-400",
    features: ["browse", "post", "need", "chat", "legal", "helper", "flag_view", "flag_manage", "purge", "sage_council"],
    welcome: "M.O.R.E. Help Center — Executive access. All tools and oversight controls are active.",
  },
};

const CATEGORY_META = {
  skill_offer: { label: "Skill Offer", color: "bg-signal/10 text-signal border-signal/30", icon: BookOpen },
  need:        { label: "Need",        color: "bg-copper/10 text-copper border-copper/30", icon: HandHelping },
  community:   { label: "Community",  color: "bg-blue-100 text-blue-700 border-blue-200", icon: Users },
  story:       { label: "Story",      color: "bg-purple-100 text-purple-700 border-purple-200", icon: Heart },
};

// ── Oliver banner ─────────────────────────────────────────────────────────────
function OliverBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 p-4 mb-4">
      <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <p className="flex-1 text-sm text-amber-800"><span className="font-bold">Oliver Guardian: </span>{message}</p>
      <button onClick={onDismiss} className="text-amber-500 text-xs font-bold">✕</button>
    </div>
  );
}

// ── Post card ─────────────────────────────────────────────────────────────────
function PostCard({ post, onFlag }) {
  const meta = CATEGORY_META[post.category] || CATEGORY_META.community;
  const Icon = meta.icon;
  const daysLeft = Math.max(0, Math.ceil((new Date(post.expires_at) - Date.now()) / 86400000));
  return (
    <div className="card-flat p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border ${meta.color}`}>
          <Icon className="w-3 h-3" />{meta.label}
        </span>
        <div className="flex items-center gap-1 text-xs text-ink/40"><Clock className="w-3 h-3" />{daysLeft}d</div>
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

// ── New Post Modal ─────────────────────────────────────────────────────────────
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
      else { toast.success("Posted!"); onSuccess(); onClose(); }
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      toast.error(msg); setOliver(msg);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Share with the Community</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-ink/40" /></button>
        </div>
        <div className="p-6 space-y-4">
          {oliver && <OliverBanner message={oliver} onDismiss={() => setOliver(null)} />}
          <select value={category} onChange={e => setCategory(e.target.value)}
            className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper">
            <option value="skill_offer">Skill Offer — I can teach or help with…</option>
            <option value="need">Need — I need help with…</option>
            <option value="community">Community — General post</option>
            <option value="story">Story — Share a community story</option>
          </select>
          <textarea value={content} onChange={e => setContent(e.target.value)} maxLength={2000} rows={5}
            placeholder="No money · No personal info · No exploitation"
            className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper" />
          <p className="text-xs text-ink/40 italic">Reviewed by Oliver Guardian · Auto-deletes in 30 days</p>
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
  const [title, setTitle] = useState(""); const [desc, setDesc] = useState(""); const [category, setCategory] = useState("general"); const [loading, setLoading] = useState(false);
  const CATS = ["general","transportation","household","meals","companionship","tutoring","mentorship","other"];
  const submit = async () => {
    if (!title.trim() || !desc.trim()) return; setLoading(true);
    try { await api.post("/more/need", { title: title.trim(), description: desc.trim(), category }); toast.success("Need posted!"); onSuccess(); onClose(); }
    catch (err) { toast.error(err?.response?.data?.detail || "Could not post"); }
    finally { setLoading(false); }
  };
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Post a Need</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-ink/40" /></button>
        </div>
        <div className="p-6 space-y-4">
          <input value={title} onChange={e => setTitle(e.target.value)} maxLength={120} placeholder="What do you need? (brief title)"
            className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper" />
          <textarea value={desc} onChange={e => setDesc(e.target.value)} maxLength={1000} rows={4} placeholder="Describe your need — no money, no personal info"
            className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper" />
          <select value={category} onChange={e => setCategory(e.target.value)}
            className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper">
            {CATS.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
          </select>
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

// ── Admin Panel ───────────────────────────────────────────────────────────────
function AdminPanel({ hasFeature }) {
  const [flags, setFlags] = useState([]);
  const [flagTotal, setFlagTotal] = useState(0);
  const [purging, setPurging] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadFlags = useCallback(async () => {
    if (!hasFeature("flag_view")) return;
    setLoading(true);
    try { const r = await api.get("/more/admin/flags"); setFlags(r.data.flags || []); setFlagTotal(r.data.total || 0); }
    catch { toast.error("Could not load flags"); }
    finally { setLoading(false); }
  }, [hasFeature]);

  useEffect(() => { loadFlags(); }, [loadFlags]);

  const purge = async () => {
    if (!window.confirm("Run manual purge? Deletes all expired M.O.R.E. content now.")) return;
    setPurging(true);
    try {
      const r = await api.post("/more/purge");
      const { posts, chats, flags: f } = r.data.purged;
      toast.success(`Purged: ${posts} posts · ${chats} chats · ${f} flags`);
      loadFlags();
    } catch { toast.error("Purge failed"); }
    finally { setPurging(false); }
  };

  return (
    <div className="border border-ink/10 mt-8">
      <div className="px-6 py-4 bg-ink text-white flex items-center justify-between">
        <div className="flex items-center gap-2 font-heading font-bold">
          <Shield className="w-5 h-5 text-signal" /> Moderation Panel
        </div>
        <div className="flex gap-3">
          <button onClick={loadFlags} className="text-xs text-white/60 hover:text-white flex items-center gap-1">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          {hasFeature("purge") && (
            <button onClick={purge} disabled={purging}
              className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 disabled:opacity-50">
              <Trash2 className="w-3.5 h-3.5" /> Run Purge
            </button>
          )}
        </div>
      </div>
      <div className="p-6">
        {loading ? <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-copper" /></div> :
          flagTotal === 0 ? <p className="text-sm text-ink/40 text-center py-4">No pending flags — community is clean.</p> : (
            <div className="space-y-3">
              <div className="overline text-xs text-ink/60 mb-2">Pending Flags ({flagTotal})</div>
              {flags.slice(0, 10).map(f => (
                <div key={f.id} className="flex items-start gap-3 p-3 border border-ink/10">
                  <Flag className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium capitalize">{f.target_type} flagged</div>
                    <div className="text-xs text-ink/50">{f.reason}</div>
                  </div>
                  <div className="text-xs text-ink/30">{new Date(f.created_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          )
        }
      </div>
    </div>
  );
}

// ── Main hub ──────────────────────────────────────────────────────────────────
export default function MoreHub() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const role = user?.role || "student";
  const config = ROLE_CONFIG[role] || ROLE_CONFIG.student;
  const hasFeature = (f) => config.features.includes(f);

  const [tab, setTab] = useState("posts");
  const [posts, setPosts] = useState([]);
  const [needs, setNeeds] = useState([]);
  const [postsTotal, setPostsTotal] = useState(0);
  const [needsTotal, setNeedsTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showPost, setShowPost] = useState(false);
  const [showNeed, setShowNeed] = useState(false);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/more/posts?limit=30"); setPosts(r.data.posts || []); setPostsTotal(r.data.total || 0); }
    catch { toast.error("Could not load posts"); }
    finally { setLoading(false); }
  }, []);

  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try { const r = await api.get("/more/needs?limit=30"); setNeeds(r.data.needs || []); setNeedsTotal(r.data.total || 0); }
    catch { toast.error("Could not load needs"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { if (tab === "posts") loadPosts(); else loadNeeds(); }, [tab, loadPosts, loadNeeds]);

  const handleFlag = async (targetId, targetType) => {
    const reason = window.prompt("Why are you flagging this?") ?? "No reason";
    try { await api.post("/more/flag", { target_id: targetId, target_type: targetType, reason }); toast.success("Flagged — thank you."); }
    catch { toast.error("Could not submit flag"); }
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* Welcome banner */}
        <div className="bg-ink text-white px-6 py-5 mb-8 flex items-start justify-between gap-4">
          <div>
            <div className={`overline text-xs ${config.color} mb-1`}>{config.label}</div>
            <h1 className="font-heading text-2xl font-extrabold">M.O.R.E. Help Center</h1>
            <p className="text-white/60 text-sm mt-1 max-w-xl">{config.welcome}</p>
          </div>
          <HandHelping className="w-10 h-10 text-copper shrink-0 opacity-60" />
        </div>

        {/* Quick action grid — role-gated */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-10">
          {hasFeature("post") && (
            <button onClick={() => setShowPost(true)}
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors group text-left">
              <PlusCircle className="w-5 h-5 text-copper" />
              <div className="font-heading font-bold text-sm">Share</div>
              <div className="text-xs text-ink/50">Post skills or stories</div>
            </button>
          )}
          {hasFeature("need") && (
            <button onClick={() => setShowNeed(true)}
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors group text-left">
              <HandHelping className="w-5 h-5 text-signal" />
              <div className="font-heading font-bold text-sm">Post a Need</div>
              <div className="text-xs text-ink/50">Ask the community</div>
            </button>
          )}
          {hasFeature("chat") && (
            <Link to="/more/chat"
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors">
              <MessageSquare className="w-5 h-5 text-blue-500" />
              <div className="font-heading font-bold text-sm">Community Chat</div>
              <div className="text-xs text-ink/50">60-min private rooms</div>
            </Link>
          )}
          {hasFeature("legal") && (
            <Link to="/more/litigation"
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors">
              <Scale className="w-5 h-5 text-signal" />
              <div className="font-heading font-bold text-sm">Legal Aid Tool</div>
              <div className="text-xs text-ink/50">Know your rights</div>
            </Link>
          )}
          {hasFeature("helper") && (
            <Link to="/app/helper"
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors">
              <HelpCircle className="w-5 h-5 text-purple-500" />
              <div className="font-heading font-bold text-sm">Help Center AI</div>
              <div className="text-xs text-ink/50">Bills, letters, rights</div>
            </Link>
          )}
          {hasFeature("sage_council") && (
            <Link to="/council"
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-signal transition-colors">
              <Layers className="w-5 h-5 text-signal" />
              <div className="font-heading font-bold text-sm">Council (Sage)</div>
              <div className="text-xs text-ink/50">AI advisor council</div>
            </Link>
          )}
          {hasFeature("flag_view") && (
            <Link to="/more/admin"
              className="card-flat p-4 flex flex-col items-start gap-2 hover:border-red-400 transition-colors">
              <Shield className="w-5 h-5 text-red-400" />
              <div className="font-heading font-bold text-sm">Moderation</div>
              <div className="text-xs text-ink/50">Flags &amp; admin tools</div>
            </Link>
          )}
          <Link to="/more"
            className="card-flat p-4 flex flex-col items-start gap-2 hover:border-copper transition-colors">
            <Eye className="w-5 h-5 text-ink/40" />
            <div className="font-heading font-bold text-sm">Public View</div>
            <div className="text-xs text-ink/50">See what visitors see</div>
          </Link>
        </div>

        {/* Feed tabs */}
        <div className="flex border-b border-ink/10 mb-6">
          {[{ key: "posts", label: `Community (${postsTotal})` }, { key: "needs", label: `Needs Board (${needsTotal})` }].map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${tab === t.key ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}>
              {t.label}
            </button>
          ))}
          <div className="ml-auto flex items-center">
            <button onClick={tab === "posts" ? loadPosts : loadNeeds} className="p-2 text-ink/40 hover:text-copper">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-copper" /></div>
        ) : tab === "posts" ? (
          posts.length === 0 ? (
            <div className="text-center py-16 text-ink/40">
              <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No posts yet — be the first to share.</p>
              <button onClick={() => setShowPost(true)} className="mt-4 btn-copper text-sm">Share Something</button>
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
              <p>No needs posted yet.</p>
              <button onClick={() => setShowNeed(true)} className="mt-4 btn-primary text-sm">Post a Need</button>
            </div>
          ) : (
            <div className="space-y-4">
              {needs.map(n => (
                <div key={n.id} className="card-flat p-5 border-l-4 border-copper">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-heading font-bold text-ink">{n.title}</h3>
                    <div className="text-xs text-ink/40 flex items-center gap-1 shrink-0">
                      <Clock className="w-3 h-3" />
                      {Math.max(0, Math.ceil((new Date(n.expires_at) - Date.now()) / 86400000))}d
                    </div>
                  </div>
                  <p className="text-sm text-ink/70">{n.description}</p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-ink/5">
                    <span className="text-xs text-ink/50">{n.author_name} · {n.category}</span>
                    <button onClick={() => handleFlag(n.id, "need")}
                      className="flex items-center gap-1 text-xs text-ink/30 hover:text-red-500">
                      <Flag className="w-3 h-3" /> Flag
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Admin panel for eligible roles */}
        {hasFeature("flag_view") && <AdminPanel hasFeature={hasFeature} />}
      </div>

      {showPost && <NewPostModal onClose={() => setShowPost(false)} onSuccess={() => { if (tab === "posts") loadPosts(); }} />}
      {showNeed && <NewNeedModal onClose={() => setShowNeed(false)} onSuccess={() => { if (tab === "needs") loadNeeds(); }} />}
    </AppShell>
  );
}
