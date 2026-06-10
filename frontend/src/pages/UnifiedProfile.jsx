/**
 * UnifiedProfile — one profile template for every user type.
 *
 * Routes:
 *   /u/:username   — public view of any user's profile
 *   /profile       — owner's own profile (redirects to /u/:username once slug set)
 *
 * Feature gates by tier/role:
 *   Public/Free    → profile, bio, share, AI chat (Tutor)
 *   Member         → + posts, M.O.R.E. feed, community
 *   Plus           → + courses, portfolio, tracks
 *   Pro            → + Ghost Producer, Band on a Page, Publisher
 *   Patron/Creator → + Artist Management, mass social posting
 *   Admin/Exec     → all features + Sovereign
 */

import { useState, useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import { toast } from "sonner";
import SharePanel from "../components/SharePanel";
import {
  Music, BookOpen, Users, Edit3, Camera, Send, Mic, MicOff,
  Volume2, VolumeX, Play, Pause, Settings, ExternalLink,
  Zap, Lock, Globe, Radio, Megaphone, BarChart2, ShoppingBag,
} from "lucide-react";
import { useMic } from "../hooks/useMic";

// ── Tier gate logic ──────────────────────────────────────────────────────────
const TIER_ORDER = ["Public", "Member", "Plus", "Pro", "Patron"];

function tierGte(userTier, required) {
  const ADMIN_ROLES = ["admin", "executive_admin", "instructor"];
  return true; // roles checked separately; tier from API
}

function canAccess(user, status, feature) {
  if (!user) return false;
  const role = user.role || "student";
  const tier = status?.tier || "Public";
  const isAdmin = ["admin", "executive_admin"].includes(role);
  const isInstructor = role === "instructor";
  const tierIdx = TIER_ORDER.indexOf(tier);

  switch (feature) {
    case "profile":       return true;
    case "ai_chat":       return true;
    case "posts":         return tierIdx >= 1 || isAdmin;
    case "courses":       return tierIdx >= 2 || isInstructor || isAdmin;
    case "tracks":        return tierIdx >= 2 || isInstructor || isAdmin;
    case "ghost":         return tierIdx >= 3 || isAdmin;
    case "band":          return tierIdx >= 3 || isAdmin;
    case "publisher":     return tierIdx >= 3 || isAdmin;
    case "artist_mgmt":   return tierIdx >= 4 || isAdmin;
    case "mass_post":     return tierIdx >= 4 || isAdmin;
    case "sovereign":     return isAdmin;
    default:              return false;
  }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function LockedFeature({ name, requiredTier, compact = false }) {
  if (compact) return (
    <div className="flex items-center gap-1.5 text-xs text-ink/30">
      <Lock className="w-3 h-3" />
      <span>{name} — {requiredTier}+</span>
    </div>
  );
  return (
    <div className="card-flat p-6 flex flex-col items-center text-center gap-3">
      <Lock className="w-8 h-8 text-ink/20" />
      <div className="font-heading font-bold text-ink/40">{name}</div>
      <p className="text-xs text-ink/30">Unlock with {requiredTier} plan</p>
      <Link to="/plans" className="btn-copper text-xs">Upgrade</Link>
    </div>
  );
}

function AIAssistantPanel({ user, status }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [audioOn, setAudioOn] = useState(false);
  const endRef = useRef(null);
  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => setInput(p => p ? `${p} ${t}` : t),
    onError: () => {},
  });

  // Sovereign is private — accessible only through his dedicated widget, not here.
  // Profile AI assistant always uses the public supervisor endpoint.
  const endpoint = "/supervisor/public-chat";

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  async function send(e) {
    e?.preventDefault();
    const msg = input.trim();
    if (!msg || sending) return;
    setMsgs(m => [...m, { role: "user", text: msg }]);
    setInput("");
    setSending(true);
    try {
      const r = await api.post(endpoint, { message: msg });
      setMsgs(m => [...m, { role: "ai", text: r.data?.reply || "…" }]);
    } catch {
      setMsgs(m => [...m, { role: "ai", text: "Unavailable right now — try again shortly." }]);
    } finally {
      setSending(false);
    }
  }

  const aiName = canAccess(user, status, "sovereign") ? "The Sovereign" : "WAI Assistant";

  return (
    <div className="card-flat overflow-hidden flex flex-col" style={{ height: 320 }}>
      <div className="px-4 py-3 border-b border-ink/10 flex items-center justify-between" style={{ background: "var(--wai-navy, #050814)" }}>
        <span className="text-xs font-bold text-copper uppercase tracking-widest">{aiName}</span>
        <button onClick={() => setAudioOn(v => !v)} className="text-ink/30 hover:text-copper transition-colors">
          {audioOn ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-ink/2">
        {msgs.length === 0 && (
          <p className="text-xs text-ink/30 italic">Ask anything — courses, services, resources…</p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span className={`inline-block px-3 py-1.5 rounded-xl text-xs whitespace-pre-wrap max-w-[90%] ${
              m.role === "user"
                ? "bg-copper text-white"
                : "bg-white border border-ink/10 text-ink/80"
            }`}>{m.text}</span>
          </div>
        ))}
        {sending && <div className="text-xs text-ink/30">Thinking…</div>}
        <div ref={endRef} />
      </div>
      <form onSubmit={send} className="p-2 flex gap-1.5 border-t border-ink/10">
        <button type="button" onClick={toggleMic}
          className={`p-1.5 rounded-lg transition-colors ${listening ? "bg-red-500 text-white" : "text-ink/30 hover:text-copper"}`}>
          {listening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
        </button>
        <input
          value={input} onChange={e => setInput(e.target.value)}
          placeholder={listening ? "Listening…" : "Ask…"}
          className="flex-1 text-xs px-2 py-1.5 rounded-lg border border-ink/15 bg-white focus:outline-none focus:border-copper"
        />
        <button type="submit" disabled={sending || !input.trim()}
          className="p-1.5 bg-copper text-white rounded-lg disabled:opacity-40">
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}

// ── Inline Social Publisher ───────────────────────────────────────────────────
const SOCIAL_PLATFORMS = [
  { id: "twitter",   label: "𝕏 Twitter",   limit: 280,   shareUrl: (t) => `https://twitter.com/intent/tweet?text=${encodeURIComponent(t)}` },
  { id: "threads",   label: "🧵 Threads",   limit: 500,   shareUrl: (t) => `https://www.threads.net/intent/post?text=${encodeURIComponent(t)}` },
  { id: "linkedin",  label: "💼 LinkedIn",  limit: 3000,  shareUrl: (t, l) => `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(t)}` },
  { id: "facebook",  label: "👥 Facebook",  limit: 63000, shareUrl: (t, l) => l ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(l)}&quote=${encodeURIComponent(t)}` : `https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(t)}` },
  { id: "instagram", label: "📸 Instagram", limit: 2200,  shareUrl: null },
  { id: "tiktok",    label: "🎵 TikTok",    limit: 2200,  shareUrl: null },
];

function InlineSocialPublisher() {
  const [text, setText]       = useState("");
  const [link, setLink]       = useState("");
  const [selected, setSelected] = useState(["twitter", "instagram"]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied]   = useState(null);

  const toggle = (id) => setSelected(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id]);

  async function generate() {
    if (!text.trim() || !selected.length) return;
    setLoading(true); setResults(null);
    const platforms = SOCIAL_PLATFORMS.filter(p => selected.includes(p.id));
    try {
      const res = await api.post("/ai/chat", {
        messages: [{ role: "user", content: `Base post: ${text}${link ? `\nLink: ${link}` : ""}\nPlatforms: ${selected.join(", ")}\nReturn JSON only.` }],
        system: `You are a social media manager. Rewrite the post for each platform: ${platforms.map(p => `${p.id} (${p.hint || "adapt for platform"}, max ${p.limit < 10000 ? p.limit + " chars" : "unlimited"})`).join("; ")}. Return ONLY a JSON object with platform IDs as keys.`,
        persona_label: "social_publisher",
        max_tokens: 1200,
      });
      const raw = res.data?.response || res.data?.text || "";
      const match = raw.match(/\{[\s\S]*\}/);
      if (match) setResults(JSON.parse(match[0]));
      else toast.error("Try again — format issue");
    } catch { toast.error("Generation failed"); }
    finally { setLoading(false); }
  }

  function copy(id, txt) {
    navigator.clipboard?.writeText(txt);
    setCopied(id); setTimeout(() => setCopied(null), 2000);
    toast.success("Copied!");
  }

  return (
    <div className="card-flat p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Megaphone className="w-4 h-4 text-copper" />
        <span className="font-heading font-bold">Social Publisher</span>
      </div>

      <textarea value={text} onChange={e => setText(e.target.value)} rows={3}
        placeholder="Write your post — AI will adapt it for each platform…"
        className="w-full text-sm px-3 py-2.5 rounded-lg border border-ink/15 bg-white focus:outline-none focus:border-copper resize-none" />

      <input value={link} onChange={e => setLink(e.target.value)}
        placeholder="Optional link to include (https://…)"
        className="w-full text-sm px-3 py-2 rounded-lg border border-ink/15 bg-white focus:outline-none focus:border-copper" />

      <div className="flex gap-2 flex-wrap">
        {SOCIAL_PLATFORMS.map(p => (
          <button key={p.id} onClick={() => toggle(p.id)}
            className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-colors ${
              selected.includes(p.id) ? "border-copper bg-copper text-white" : "border-ink/15 text-ink/40 hover:border-copper"
            }`}>{p.label}</button>
        ))}
      </div>

      <button onClick={generate} disabled={loading || !text.trim() || !selected.length}
        className="w-full btn-copper text-sm disabled:opacity-40 flex items-center justify-center gap-2">
        {loading ? "Formatting…" : `✦ Format for ${selected.length} Platform${selected.length !== 1 ? "s" : ""}`}
      </button>

      {results && (
        <div className="space-y-3 pt-2">
          {SOCIAL_PLATFORMS.filter(p => selected.includes(p.id) && results[p.id]).map(p => (
            <div key={p.id} className="border border-ink/10 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 bg-ink/3 border-b border-ink/8">
                <span className="text-xs font-bold text-ink/60">{p.label}</span>
                <span className="text-xs text-ink/30">{results[p.id]?.length}{p.limit < 10000 ? `/${p.limit}` : ""}</span>
              </div>
              <pre className="px-3 py-2.5 text-sm leading-relaxed whitespace-pre-wrap break-words font-inherit text-ink/80 max-h-32 overflow-y-auto">{results[p.id]}</pre>
              <div className="flex gap-2 px-3 py-2 border-t border-ink/8">
                <button onClick={() => copy(p.id, results[p.id])}
                  className="flex-1 text-xs font-bold py-1.5 border border-ink/15 rounded-lg hover:border-copper transition-colors">
                  {copied === p.id ? "✓ Copied" : "Copy"}
                </button>
                {p.shareUrl && (
                  <a href={p.shareUrl(results[p.id], link)} target="_blank" rel="noopener noreferrer"
                    className="flex-1 text-xs font-bold py-1.5 bg-ink text-white rounded-lg text-center hover:bg-ink/80 transition-colors">
                    Open {p.label.split(" ")[1]}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Inline Ghost Clone launcher ───────────────────────────────────────────────
const GHOST_CLONES = [
  { id: "editor",    icon: "📝", label: "Ghost Editor",    color: "#00ffcc", system: "You are the Ghost Editor — fix grammar, sharpen prose, improve flow, cut dead weight. Return the edited version then briefly note key changes.", placeholder: "Paste your text, lyrics, or script…", btn: "Edit This" },
  { id: "publicist", icon: "📢", label: "Ghost Publicist", color: "#a855f7", system: "You are the Ghost Publicist. Generate: a press release, social post package (X, Instagram, TikTok, LinkedIn), and a playlist/blog pitch email. Make the artist sound legendary.", placeholder: "Describe your release or project…", btn: "Generate Press Kit" },
  { id: "legal",     icon: "⚖️", label: "Ghost Legal",     color: "#ffaa00", system: "You are the Ghost Legal advisor. Give clear practical guidance on music copyright, publishing rights, sampling, and contract basics. Remind user this is informational, not legal representation.", placeholder: "Describe your situation — ownership, samples, contracts…", btn: "Get Guidance" },
  { id: "marketer",  icon: "📈", label: "Ghost Marketer",  color: "#ff0066", system: "You are the Ghost Marketer. Create a release strategy, rollout timeline, visual art direction brief, and audience targeting plan. Think 3 moves ahead.", placeholder: "Describe your music, brand, and goals…", btn: "Build Strategy" },
];

function InlineGhostProducer({ canUse }) {
  const [activeClone, setActiveClone] = useState(null);
  const [input, setInput]   = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  function selectClone(c) { setActiveClone(c); setInput(""); setOutput(""); }

  async function run() {
    if (!input.trim()) return;
    setLoading(true); setOutput("");
    try {
      const res = await api.post("/ai/chat", {
        messages: [{ role: "user", content: input }],
        system: activeClone.system,
        persona_label: `ghost_${activeClone.id}`,
        max_tokens: 1200,
      });
      setOutput(res.data?.response || res.data?.text || "No response.");
    } catch (e) { setOutput("⚠️ " + (e?.response?.data?.detail || "Request failed")); }
    finally { setLoading(false); }
  }

  if (!canUse) return (
    <div className="card-flat p-5 flex flex-col items-center text-center gap-3">
      <Lock className="w-7 h-7 text-ink/20" />
      <div className="font-heading font-bold text-ink/40">Ghost Producer</div>
      <p className="text-xs text-ink/30">Unlock with Pro plan</p>
      <Link to="/plans" className="btn-copper text-xs">Upgrade</Link>
    </div>
  );

  return (
    <div className="card-flat p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Music className="w-4 h-4 text-copper" />
        <span className="font-heading font-bold">Ghost Producer</span>
      </div>

      {!activeClone ? (
        <div className="grid grid-cols-2 gap-3">
          {GHOST_CLONES.map(c => (
            <button key={c.id} onClick={() => selectClone(c)}
              className="text-left p-3 rounded-xl border border-ink/10 hover:border-copper transition-all bg-white hover:bg-bone">
              <div className="text-xl mb-1.5">{c.icon}</div>
              <div className="font-bold text-sm" style={{ color: c.color }}>{c.label}</div>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <button onClick={() => { setActiveClone(null); setOutput(""); }}
              className="text-xs text-ink/40 hover:text-copper">← Back</button>
            <span className="text-sm font-bold" style={{ color: activeClone.color }}>{activeClone.icon} {activeClone.label}</span>
          </div>
          <textarea value={input} onChange={e => setInput(e.target.value)} rows={4}
            placeholder={activeClone.placeholder}
            className="w-full text-sm px-3 py-2.5 rounded-lg border border-ink/15 bg-white focus:outline-none focus:border-copper resize-none" />
          <button onClick={run} disabled={loading || !input.trim()}
            className="w-full text-sm font-bold py-2.5 rounded-lg border transition-colors disabled:opacity-40"
            style={{ background: loading ? "#f5f5f5" : activeClone.color, color: loading ? "#999" : "#000" }}>
            {loading ? "Working…" : activeClone.btn}
          </button>
          {output && (
            <div className="bg-ink/3 rounded-xl p-4 border border-ink/8">
              <pre className="text-sm leading-relaxed whitespace-pre-wrap break-words font-inherit text-ink/80 max-h-60 overflow-y-auto">{output}</pre>
              <button onClick={() => navigator.clipboard?.writeText(output)}
                className="mt-3 text-xs font-bold text-copper hover:underline">📋 Copy output</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ServiceCard({ icon: Icon, title, desc, to, locked, requiredTier }) {
  if (locked) return (
    <Link to="/plans" className="card-flat p-4 flex items-center gap-3 opacity-40 hover:opacity-60 transition-opacity">
      <div className="w-9 h-9 rounded-lg bg-ink/5 flex items-center justify-center shrink-0">
        <Lock className="w-4 h-4 text-ink/30" />
      </div>
      <div className="min-w-0">
        <div className="font-bold text-sm text-ink/40 truncate">{title}</div>
        <div className="text-xs text-ink/30">{requiredTier}+ plan</div>
      </div>
    </Link>
  );
  return (
    <Link to={to} className="card-flat p-4 flex items-center gap-3 hover:border-copper transition-colors group">
      <div className="w-9 h-9 rounded-lg bg-copper/10 flex items-center justify-center shrink-0 group-hover:bg-copper/20 transition-colors">
        <Icon className="w-4 h-4 text-copper" />
      </div>
      <div className="min-w-0">
        <div className="font-bold text-sm truncate">{title}</div>
        <div className="text-xs text-ink/50 truncate">{desc}</div>
      </div>
      <ExternalLink className="w-3.5 h-3.5 text-ink/20 group-hover:text-copper shrink-0 ml-auto transition-colors" />
    </Link>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function UnifiedProfile() {
  const { username } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [coverInput, setCoverInput] = useState(null);
  const [activeTab, setActiveTab] = useState("home");

  // Determine if viewer is the owner
  const isOwner = user && profile && (profile.user_id === user.id || profile.slug === username);
  const viewerStatus = status;

  useEffect(() => {
    if (!username) {
      // /profile route — redirect to own profile or setup
      if (user) {
        api.get("/creator/profile/me").then(r => {
          const p = r.data?.profile;
          if (p?.slug) navigate(`/u/${p.slug}`, { replace: true });
          else navigate("/creator/profile/edit", { replace: true });
        }).catch(() => navigate("/creator/profile/edit", { replace: true }));
      }
      return;
    }

    async function load() {
      setLoading(true);
      try {
        const [profRes] = await Promise.allSettled([
          api.get(`/creator/profile/${username}`),
        ]);
        if (profRes.status === "fulfilled") {
          setProfile(profRes.value.data.profile);
        }
        if (user) {
          const [statusRes, coursesRes] = await Promise.allSettled([
            api.get("/partnership/status"),
            api.get("/creator/courses"),
          ]);
          if (statusRes.status === "fulfilled") setStatus(statusRes.value.data);
          if (coursesRes.status === "fulfilled") setCourses(coursesRes.value.data.courses || []);
        }
      } catch (_e) {}
      finally { setLoading(false); }
    }
    load();
  }, [username, user, navigate]);

  if (!username) return null;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-copper border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!profile) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4">
      <div className="font-heading text-2xl font-bold text-ink/40">Profile not found</div>
      <p className="text-sm text-ink/30">@{username} hasn't published their profile yet.</p>
      {user && <Link to="/creator/profile/edit" className="btn-copper text-sm">Set up your profile</Link>}
    </div>
  );

  const coverBg = profile.cover_url
    ? `url(${profile.cover_url}) center/cover no-repeat`
    : "linear-gradient(135deg, #1a0a00 0%, #3d1a00 40%, #c87941 100%)";

  const isExec = ["admin", "executive_admin"].includes(user?.role);

  const TABS = [
    { key: "home",    label: "Home" },
    { key: "content", label: "Content" },
    ...(isOwner ? [{ key: "creator", label: "Create & Publish" }] : []),
    ...(isOwner && isExec ? [
      { key: "team",     label: "Team" },
      { key: "revenue",  label: "Revenue" },
      { key: "platform", label: "Platform" },
    ] : []),
  ];

  const publishedCourses = courses.filter(c => c.status === "published");

  return (
    <div className="min-h-screen bg-bone">

      {/* ── Cover ── */}
      <div className="relative h-52 sm:h-64" style={{ background: coverBg }}>
        {isOwner && (
          <button
            onClick={() => toast.info("Cover photo upload — coming via profile edit")}
            className="absolute top-3 right-3 flex items-center gap-1.5 text-xs font-bold bg-black/40 text-white px-3 py-1.5 rounded-full hover:bg-black/60 transition-colors"
          >
            <Camera className="w-3.5 h-3.5" /> Edit Cover
          </button>
        )}
      </div>

      {/* ── Avatar + name bar ── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-end gap-5 -mt-14 mb-4 relative z-10">
          <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full border-4 border-white shadow-xl overflow-hidden bg-copper/20 shrink-0 flex items-center justify-center">
            {profile.avatar
              ? <img src={profile.avatar} alt={profile.display_name} className="w-full h-full object-cover" />
              : <span className="font-heading font-extrabold text-3xl text-copper">{(profile.display_name || "?")[0]}</span>
            }
          </div>
          <div className="pb-2 flex-1 min-w-0">
            <h1 className="font-heading font-extrabold text-2xl sm:text-3xl text-ink truncate">{profile.display_name}</h1>
            <div className="text-sm text-ink/50">@{profile.slug} {profile.title && `· ${profile.title}`}</div>
          </div>
          <div className="pb-2 flex items-center gap-2 shrink-0">
            {isOwner && (
              <Link to="/creator/profile/edit" className="flex items-center gap-1.5 text-xs font-bold border border-ink/20 px-3 py-1.5 rounded-full hover:border-copper transition-colors">
                <Edit3 className="w-3.5 h-3.5" /> Edit
              </Link>
            )}
            <SharePanel compact url={`/u/${profile.slug}`} title={`${profile.display_name} — WAI-Institute`} embed />
          </div>
        </div>

        {/* Tier badge */}
        {viewerStatus?.tier && (
          <div className="inline-flex items-center gap-1.5 text-xs font-bold bg-copper/10 text-copper border border-copper/20 px-3 py-1 rounded-full mb-4">
            <Zap className="w-3 h-3" /> {viewerStatus.tier} Member
          </div>
        )}

        {/* Bio */}
        {profile.bio && (
          <p className="text-sm text-ink/70 max-w-2xl mb-5 leading-relaxed">{profile.bio}</p>
        )}

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-ink/10 mb-6">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2.5 text-sm font-bold border-b-2 transition-colors ${
                activeTab === t.key
                  ? "border-copper text-copper"
                  : "border-transparent text-ink/40 hover:text-ink/70"
              }`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Main layout ── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pb-16">
        <div className="grid lg:grid-cols-3 gap-6">

          {/* ── Left / main column ── */}
          <div className="lg:col-span-2 space-y-6">

            {/* HOME tab */}
            {activeTab === "home" && (
              <>
                {/* Tracks / music */}
                {canAccess(user, viewerStatus, "tracks") && profile.tracks?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Music className="w-4 h-4 text-copper" />
                      <span className="font-heading font-bold">Music</span>
                    </div>
                    <div className="space-y-2">
                      {profile.tracks.map((t, i) => (
                        <div key={i} className="card-flat p-4 flex items-center gap-3">
                          <button className="w-9 h-9 rounded-full bg-copper flex items-center justify-center shrink-0">
                            <Play className="w-4 h-4 fill-white text-white ml-0.5" />
                          </button>
                          <div className="flex-1 min-w-0">
                            <div className="font-bold text-sm truncate">{t.title}</div>
                            {t.artist && <div className="text-xs text-ink/40">{t.artist}</div>}
                          </div>
                          <SharePanel compact url={t.share_url || `/u/${profile.slug}`} title={t.title} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Courses */}
                {canAccess(user, viewerStatus, "courses") && publishedCourses.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <BookOpen className="w-4 h-4 text-copper" />
                      <span className="font-heading font-bold">Courses</span>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {publishedCourses.slice(0, 4).map(c => (
                        <div key={c.course_id} className="card-flat p-4">
                          <div className="text-xs text-copper font-bold uppercase tracking-wider mb-1">{c.category}</div>
                          <div className="font-heading font-bold text-sm mb-1 line-clamp-2">{c.title}</div>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs text-ink/40">
                              {c.price_cents === 0 ? "Free" : `$${(c.price_cents / 100).toFixed(2)}`}
                            </span>
                            <SharePanel compact url={`/courses?highlight=${c.course_id}`} title={c.title} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* M.O.R.E. offerings */}
                {profile.more_offerings?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Users className="w-4 h-4 text-copper" />
                      <span className="font-heading font-bold">Community Offerings</span>
                    </div>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {profile.more_offerings.map((o, i) => (
                        <div key={i} className="card-flat p-4">
                          <div className="font-bold text-sm">{o.title}</div>
                          <div className="text-xs text-ink/50 mt-1">{o.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* CONTENT tab */}
            {activeTab === "content" && (
              <div className="space-y-4">
                <div className="font-heading font-bold text-lg">All Content</div>
                {publishedCourses.length === 0 && (
                  <div className="card-flat p-8 text-center text-ink/30 text-sm">
                    No published content yet.
                    {isOwner && <Link to="/creator/courses" className="block mt-2 text-copper font-bold">Create a course →</Link>}
                  </div>
                )}
                {publishedCourses.map(c => (
                  <div key={c.course_id} className="card-flat p-5 flex gap-4 items-start">
                    <div className="w-12 h-12 rounded-lg bg-copper/10 flex items-center justify-center shrink-0">
                      <BookOpen className="w-5 h-5 text-copper" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-heading font-bold">{c.title}</div>
                      <div className="text-xs text-ink/50 mt-0.5">{c.category} · {c.sections?.length || 0} sections · {c.price_cents === 0 ? "Free" : `$${(c.price_cents / 100).toFixed(2)}`}</div>
                      {c.description && <p className="text-sm text-ink/60 mt-2 line-clamp-2">{c.description}</p>}
                    </div>
                    <SharePanel compact url={`/courses?highlight=${c.course_id}`} title={c.title} />
                  </div>
                ))}
              </div>
            )}

            {/* CREATOR tab (was services + publish combined) */}
            {activeTab === "creator" && isOwner && (
              <div className="space-y-6">
                <InlineSocialPublisher />
                <InlineGhostProducer canUse={canAccess(user, viewerStatus, "ghost")} />
              </div>
            )}

            {/* TEAM tab (exec/admin only) */}
            {activeTab === "team" && isExec && (
              <div className="space-y-4">
                <div className="font-heading font-bold text-lg">Team Operations</div>
                <div className="grid sm:grid-cols-2 gap-3">
                  <ServiceCard icon={Users} title="Team Ops" desc="All 17 personas, task board" to="/team/ops" locked={false} />
                  <ServiceCard icon={BarChart2} title="Director Dashboard" desc="Platform pulse, metrics" to="/admin" locked={false} />
                  <ServiceCard icon={Settings} title="Provider Gateway" desc="LLM keys, AI routing" to="/admin/providers" locked={false} />
                  <ServiceCard icon={Globe} title="Site Control" desc="Platform-wide settings" to="/admin/control" locked={false} />
                </div>
              </div>
            )}

            {/* REVENUE tab (exec/admin only) */}
            {activeTab === "revenue" && isExec && (
              <div className="space-y-4">
                <div className="font-heading font-bold text-lg">Revenue</div>
                <div className="grid sm:grid-cols-2 gap-3">
                  <ServiceCard icon={BarChart2} title="Revenue Division" desc="35/5/25/20/10 split view" to="/revenue" locked={false} />
                  <ServiceCard icon={ShoppingBag} title="Creator Earnings" desc="Course + content revenue" to="/creator/earnings" locked={false} />
                  <ServiceCard icon={Megaphone} title="Sovereign" desc="Booking, pipeline, counsel" to="#" locked={false} />
                  <ServiceCard icon={Globe} title="Gumroad" desc="Book + digital product sales" to="/store" locked={false} />
                </div>
              </div>
            )}

            {/* PLATFORM tab (exec/admin only) */}
            {activeTab === "platform" && isExec && (
              <div className="space-y-4">
                <div className="font-heading font-bold text-lg">Platform</div>
                <div className="grid sm:grid-cols-2 gap-3">
                  <ServiceCard icon={BarChart2} title="Analytics" desc="Users, engagement, trends" to="/analytics" locked={false} />
                  <ServiceCard icon={Settings} title="System Health" desc="Uptime, errors, services" to="/admin/health" locked={false} />
                  <ServiceCard icon={Users} title="User Management" desc="Roles, accounts, access" to="/admin/users" locked={false} />
                  <ServiceCard icon={Globe} title="Audit Log" desc="Full platform activity trail" to="/admin/audit" locked={false} />
                </div>
              </div>
            )}
          </div>

          {/* ── Right rail ── */}
          <div className="space-y-5">

            {/* AI Assistant */}
            <AIAssistantPanel user={user} status={viewerStatus} />

            {/* Socials */}
            {profile.socials?.length > 0 && (
              <div className="card-flat p-4 space-y-2">
                <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-2">Connect</div>
                {profile.socials.map((s, i) => (
                  <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-ink/60 hover:text-copper transition-colors">
                    <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                    <span className="font-bold">{s.platform}</span>
                    <span className="text-xs text-ink/40 truncate">{s.handle}</span>
                  </a>
                ))}
              </div>
            )}

            {/* Share */}
            <div className="card-flat p-4">
              <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-3">Share Profile</div>
              <SharePanel url={`/u/${profile.slug}`} title={`${profile.display_name} — WAI-Institute`} embed />
            </div>

            {/* Settings shortcut (owner only) */}
            {isOwner && (
              <Link to="/settings" className="card-flat p-4 flex items-center gap-3 hover:border-copper transition-colors text-ink/50 hover:text-copper group">
                <Settings className="w-4 h-4" />
                <span className="text-sm font-bold">Account Settings</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
