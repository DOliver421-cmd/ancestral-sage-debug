import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  PlusCircle, Heart, HandHelping, BookOpen, Users, Shield,
  Clock, AlertCircle, MessageSquare, Flag, ChevronRight,
  Loader2, RefreshCw, Scale,
} from "lucide-react";
import { toast } from "sonner";

const CATEGORY_META = {
  skill_offer: { label: "Skill Offer", color: "bg-signal/10 text-signal border-signal/30", icon: BookOpen },
  need: { label: "Need", color: "bg-copper/10 text-copper border-copper/30", icon: HandHelping },
  community: { label: "Community", color: "bg-blue-100 text-blue-700 border-blue-200", icon: Users },
  story: { label: "Story", color: "bg-purple-100 text-purple-700 border-purple-200", icon: Heart },
};

const PURGE_NOTE = "Posts auto-purge after 30 days · Chats auto-purge after 60 minutes";

function OliverBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 p-4 rounded-none mb-4">
      <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm text-amber-800">
        <span className="font-bold">Oliver Guardian: </span>{message}
      </div>
      <button onClick={onDismiss} className="text-amber-500 hover:text-amber-700 text-xs font-bold">✕</button>
    </div>
  );
}

function PostCard({ post, onFlag }) {
  const meta = CATEGORY_META[post.category] || CATEGORY_META.community;
  const Icon = meta.icon;
  const daysLeft = Math.max(0, Math.ceil(
    (new Date(post.expires_at) - Date.now()) / (1000 * 60 * 60 * 24)
  ));

  return (
    <div className="card-flat p-5 flex flex-col gap-3" data-testid="more-post-card">
      <div className="flex items-start justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border ${meta.color}`}>
          <Icon className="w-3 h-3" />
          {meta.label}
        </span>
        <div className="flex items-center gap-1 text-xs text-ink/40">
          <Clock className="w-3 h-3" />
          {daysLeft}d left
        </div>
      </div>
      <p className="text-sm text-ink/80 leading-relaxed whitespace-pre-wrap">{post.content}</p>
      <div className="flex items-center justify-between pt-2 border-t border-ink/5">
        <span className="text-xs text-ink/50">{post.author_name}</span>
        <button
          onClick={() => onFlag(post.id, "post")}
          className="flex items-center gap-1 text-xs text-ink/30 hover:text-red-500 transition-colors"
        >
          <Flag className="w-3 h-3" /> Flag
        </button>
      </div>
    </div>
  );
}

function NeedCard({ need, onFlag }) {
  const daysLeft = Math.max(0, Math.ceil(
    (new Date(need.expires_at) - Date.now()) / (1000 * 60 * 60 * 24)
  ));

  return (
    <div className="card-flat p-5 border-l-4 border-copper" data-testid="more-need-card">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-heading font-bold text-ink">{need.title}</h3>
        <div className="flex items-center gap-1 text-xs text-ink/40 shrink-0">
          <Clock className="w-3 h-3" />
          {daysLeft}d
        </div>
      </div>
      <p className="text-sm text-ink/70 leading-relaxed">{need.description}</p>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-ink/5">
        <span className="text-xs text-ink/50">{need.author_name} · {need.category}</span>
        <button
          onClick={() => onFlag(need.id, "need")}
          className="flex items-center gap-1 text-xs text-ink/30 hover:text-red-500 transition-colors"
        >
          <Flag className="w-3 h-3" /> Flag
        </button>
      </div>
    </div>
  );
}

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
      if (r.data.oliver_response) setOliver(r.data.oliver_response);
      toast.success("Posted to M.O.R.E.");
      onSuccess();
      if (!r.data.oliver_response) onClose();
    } catch (err) {
      const msg = err?.response?.data?.detail || "Could not post";
      toast.error(msg);
      setOliver(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Share with the Community</h2>
          <button onClick={onClose} className="text-ink/40 hover:text-ink">✕</button>
        </div>
        <div className="p-6 space-y-4">
          {oliver && (
            <OliverBanner message={oliver} onDismiss={() => setOliver(null)} />
          )}
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Category</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper"
            >
              <option value="skill_offer">Skill Offer — I can teach or help with...</option>
              <option value="need">Need — I need help with...</option>
              <option value="community">Community — General community post</option>
              <option value="story">Story — Share a community story</option>
            </select>
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Content <span className="normal-case font-normal">({2000 - content.length} chars remaining)</span></label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              maxLength={2000}
              rows={5}
              placeholder="Share skills, needs, or community support — no money, no personal info."
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper"
            />
          </div>
          <p className="text-xs text-ink/40 italic">
            All posts are moderated by Oliver Guardian. Posts auto-delete after 30 days.
          </p>
        </div>
        <div className="px-6 pb-6 flex gap-3 justify-end">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button
            onClick={submit}
            disabled={loading || !content.trim()}
            className="btn-copper text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Post
          </button>
        </div>
      </div>
    </div>
  );
}

function NewNeedModal({ onClose, onSuccess }) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [category, setCategory] = useState("general");
  const [loading, setLoading] = useState(false);

  const NEED_CATEGORIES = ["general", "transportation", "household", "meals", "companionship", "tutoring", "mentorship", "other"];

  const submit = async () => {
    if (!title.trim() || !desc.trim()) return;
    setLoading(true);
    try {
      await api.post("/more/need", { title: title.trim(), description: desc.trim(), category });
      toast.success("Need posted — community will see it.");
      onSuccess();
      onClose();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not post need");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-bone w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink/10">
          <h2 className="font-heading font-bold text-lg">Post a Need</h2>
          <button onClick={onClose} className="text-ink/40 hover:text-ink">✕</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">What do you need?</label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={120}
              placeholder="Brief title for your need"
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper"
            />
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Details</label>
            <textarea
              value={desc}
              onChange={e => setDesc(e.target.value)}
              maxLength={1000}
              rows={4}
              placeholder="Describe what you need — no money, no personal contact info."
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm resize-none focus:outline-none focus:border-copper"
            />
          </div>
          <div>
            <label className="overline text-xs text-ink/60 mb-1 block">Category</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full border border-ink/20 bg-white px-3 py-2 text-sm focus:outline-none focus:border-copper"
            >
              {NEED_CATEGORIES.map(c => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3 justify-end">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button
            onClick={submit}
            disabled={loading || !title.trim() || !desc.trim()}
            className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Post Need
          </button>
        </div>
      </div>
    </div>
  );
}

export default function More() {
  const { user } = useAuth();
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
    try {
      const r = await api.get("/more/posts?limit=20");
      setPosts(r.data.posts || []);
      setPostsTotal(r.data.total || 0);
    } catch {
      toast.error("Could not load posts");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/more/needs?limit=20");
      setNeeds(r.data.needs || []);
      setNeedsTotal(r.data.total || 0);
    } catch {
      toast.error("Could not load needs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === "posts") loadPosts();
    else if (tab === "needs") loadNeeds();
  }, [tab, loadPosts, loadNeeds]);

  const handleFlag = async (targetId, targetType) => {
    const reason = window.prompt("Briefly describe why you're flagging this (optional):") ?? "No reason given";
    try {
      await api.post("/more/flag", { target_id: targetId, target_type: targetType, reason });
      toast.success("Flagged for review — thank you.");
    } catch {
      toast.error("Could not submit flag");
    }
  };

  const isAdmin = ["admin", "executive_admin"].includes(user?.role);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-6 py-10">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="overline text-copper mb-1">Michael Oliver Resource Exchange</div>
              <h1 className="font-heading text-4xl font-extrabold">M.O.R.E.</h1>
              <p className="text-ink/60 mt-2 text-sm max-w-lg leading-relaxed">
                Community-powered mutual aid. Trade skills, time, and support — no money, no judgment, no exploitation.
              </p>
            </div>
            <div className="flex flex-col gap-2 shrink-0">
              <button onClick={() => setShowPost(true)} className="btn-copper text-sm flex items-center gap-2">
                <PlusCircle className="w-4 h-4" /> Share
              </button>
              <button onClick={() => setShowNeed(true)} className="btn-primary text-sm flex items-center gap-2">
                <HandHelping className="w-4 h-4" /> Post Need
              </button>
            </div>
          </div>

          {/* Quick links */}
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              to="/more/chat"
              className="flex items-center gap-2 px-4 py-2 border border-ink/20 text-sm font-medium hover:bg-ink hover:text-white transition-colors"
            >
              <MessageSquare className="w-4 h-4" /> Community Chat
              <span className="text-xs text-ink/40 ml-1">(60 min rooms)</span>
            </Link>
            <Link
              to="/more/litigation"
              className="flex items-center gap-2 px-4 py-2 border border-signal/40 bg-signal/5 text-sm font-medium text-ink hover:bg-signal hover:text-ink transition-colors"
            >
              <Scale className="w-4 h-4 text-signal" /> Legal Help Tool
            </Link>
            {isAdmin && (
              <Link
                to="/more/admin"
                className="flex items-center gap-2 px-4 py-2 border border-ink/20 text-sm font-medium hover:bg-ink hover:text-white transition-colors"
              >
                <Shield className="w-4 h-4" /> Admin / Flags
              </Link>
            )}
          </div>
        </div>

        {/* Auto-purge notice */}
        <div className="flex items-center gap-2 text-xs text-ink/40 mb-6">
          <Clock className="w-3.5 h-3.5" />
          {PURGE_NOTE}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-ink/10 mb-6">
          {[
            { key: "posts", label: `Community (${postsTotal})` },
            { key: "needs", label: `Needs Board (${needsTotal})` },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${tab === t.key ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}
            >
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
              <p>No community posts yet. Be the first to share.</p>
              <button onClick={() => setShowPost(true)} className="mt-4 btn-copper text-sm">
                Share with the Community
              </button>
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
              <p>No needs posted yet. Ask the community for help — that's what we're here for.</p>
              <button onClick={() => setShowNeed(true)} className="mt-4 btn-primary text-sm">
                Post a Need
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {needs.map(n => <NeedCard key={n.id} need={n} onFlag={handleFlag} />)}
            </div>
          )
        )}

        {/* Oliver Guardian info banner */}
        <div className="mt-12 border border-ink/10 p-5 bg-ink text-white">
          <div className="flex items-start gap-4">
            <Shield className="w-8 h-8 text-signal shrink-0 mt-0.5" />
            <div>
              <div className="font-heading font-bold">Protected by Oliver Guardian</div>
              <p className="text-white/60 text-xs mt-1 leading-relaxed">
                All content is reviewed by our AI moderator before publishing. No money, no personal info, no exploitation — ever.
                The Oliver Guardian has seen every trick in the book and is not impressed.
              </p>
            </div>
          </div>
        </div>
      </div>

      {showPost && (
        <NewPostModal
          onClose={() => setShowPost(false)}
          onSuccess={() => { if (tab === "posts") loadPosts(); }}
        />
      )}
      {showNeed && (
        <NewNeedModal
          onClose={() => setShowNeed(false)}
          onSuccess={() => { if (tab === "needs") loadNeeds(); }}
        />
      )}
    </AppShell>
  );
}
