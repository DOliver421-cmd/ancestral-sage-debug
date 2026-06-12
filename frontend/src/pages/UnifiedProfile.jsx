/**
 * UnifiedProfile — one profile template for every user type.
 *
 * Routes:
 *   /u/:username   — public view of any user's profile
 *   /profile       — owner's own profile (redirects to /u/:username once slug set)
 *
 * Feature gates by tier/role:
 *   Public/Free    → Home fully visible. Create locked blur. Publish basic (no AI). Learn + Settings visible.
 *   Member+        → Create unlocked. Publish with AI formatting.
 *   Admin/Exec     → Everything unlocked + Control tab.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import { toast } from "sonner";
import AppShell from "../components/AppShell";
import SharePanel from "../components/SharePanel";
import {
  Music, BookOpen, Users, Edit3, Camera, Send, Mic, MicOff,
  Volume2, VolumeX, Play, Pause, Settings, ExternalLink,
  Zap, Lock, Globe, Radio, Megaphone, BarChart2, ShoppingBag,
  Upload, Image, FileText, Award, CheckCircle, Eye, EyeOff,
  Twitter, Instagram, Facebook, Linkedin, Youtube,
} from "lucide-react";
import { useMic } from "../hooks/useMic";

// ── Tier gate logic ───────────────────────────────────────────────────────────
// feature_tier is set by admin via ExecControlPanel → /exec/control/user/tier
// Values: free (0) · premium (2) · executive (4)
const FEATURE_TIER_RANK = { free: 0, premium: 2, executive: 4 };
const FEATURE_TIER_LABEL = { free: "Free", premium: "Premium", executive: "Executive" };

function canAccess(user, _status, feature) {
  if (!user) return false;
  const role = user.role || "student";
  const isAdmin = ["admin", "executive_admin"].includes(role);
  const isInstructor = role === "instructor";
  const tierIdx = FEATURE_TIER_RANK[user.feature_tier] ?? 0;

  switch (feature) {
    case "profile":       return true;
    case "ai_chat":       return true;
    case "posts":         return tierIdx >= 1 || isAdmin;
    case "courses":       return tierIdx >= 2 || isInstructor || isAdmin;
    case "tracks":        return tierIdx >= 2 || isInstructor || isAdmin;
    case "ghost":         return tierIdx >= 2 || isAdmin;
    case "band":          return tierIdx >= 2 || isAdmin;
    case "publisher":     return tierIdx >= 2 || isAdmin;
    case "publisher_ai":  return tierIdx >= 1 || isAdmin;
    case "artist_mgmt":   return tierIdx >= 4 || isAdmin;
    case "mass_post":     return tierIdx >= 4 || isAdmin;
    case "sovereign":     return isAdmin;
    default:              return false;
  }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function LockedFeature({ name, requiredTier, compact = false, children }) {
  if (compact) return (
    <div className="flex items-center gap-1.5 text-xs text-ink/30">
      <Lock className="w-3 h-3" />
      <span>{name} — {requiredTier}+</span>
    </div>
  );
  return (
    <div className="relative rounded-2xl overflow-hidden">
      {/* Blurred preview of children */}
      {children && (
        <div className="pointer-events-none select-none" style={{ filter: "blur(4px)", opacity: 0.4 }}>
          {children}
        </div>
      )}
      {/* Overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-bone/80 backdrop-blur-sm">
        <Lock className="w-8 h-8 text-ink/30" />
        <div className="font-heading font-bold text-ink/50">{name}</div>
        <p className="text-xs text-ink/40">Unlock with {requiredTier}+ plan</p>
        <Link to="/plans" className="btn-copper text-xs px-4 py-2 rounded-lg font-bold">Upgrade →</Link>
      </div>
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
  { id: "linkedin",  label: "💼 LinkedIn",  limit: 3000,  shareUrl: (t) => `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(t)}` },
  { id: "facebook",  label: "👥 Facebook",  limit: 63000, shareUrl: (t, l) => l ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(l)}&quote=${encodeURIComponent(t)}` : `https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(t)}` },
  { id: "instagram", label: "📸 Instagram", limit: 2200,  shareUrl: null },
  { id: "tiktok",    label: "🎵 TikTok",    limit: 2200,  shareUrl: null },
];

function InlineSocialPublisher({ canUseAI }) {
  const [text, setText]         = useState("");
  const [link, setLink]         = useState("");
  const [selected, setSelected] = useState(["twitter", "instagram"]);
  const [results, setResults]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [copied, setCopied]     = useState(null);

  const toggle = (id) => setSelected(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id]);

  async function generate() {
    if (!text.trim() || !selected.length) return;
    setLoading(true); setResults(null);
    const platforms = SOCIAL_PLATFORMS.filter(p => selected.includes(p.id));
    try {
      const res = await api.post("/ai/chat", {
        messages: [{ role: "user", content: `Base post: ${text}${link ? `\nLink: ${link}` : ""}\nPlatforms: ${selected.join(", ")}\nReturn JSON only.` }],
        system: `You are a social media manager. Rewrite the post for each platform: ${platforms.map(p => `${p.id} (adapt for platform, max ${p.limit < 10000 ? p.limit + " chars" : "unlimited"})`).join("; ")}. Return ONLY a JSON object with platform IDs as keys.`,
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
        {!canUseAI && <span className="ml-auto text-xs bg-ink/5 border border-ink/10 text-ink/40 px-2 py-0.5 rounded-full">Manual copy only</span>}
      </div>

      <textarea value={text} onChange={e => setText(e.target.value)} rows={3}
        placeholder={canUseAI ? "Write your post — AI will adapt it for each platform…" : "Write your post and copy it manually to each platform…"}
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

      {canUseAI ? (
        <button onClick={generate} disabled={loading || !text.trim() || !selected.length}
          className="w-full btn-copper text-sm disabled:opacity-40 flex items-center justify-center gap-2">
          {loading ? "Formatting…" : `✦ Format for ${selected.length} Platform${selected.length !== 1 ? "s" : ""}`}
        </button>
      ) : (
        <div className="space-y-2">
          {SOCIAL_PLATFORMS.filter(p => selected.includes(p.id)).map(p => (
            <div key={p.id} className="flex items-center justify-between px-3 py-2 border border-ink/10 rounded-xl">
              <span className="text-xs font-bold text-ink/60">{p.label}</span>
              <div className="flex gap-2">
                <button
                  disabled={!text.trim()}
                  onClick={() => copy(p.id + "_manual", text + (link ? `\n${link}` : ""))}
                  className="text-xs font-bold px-3 py-1 border border-ink/15 rounded-lg hover:border-copper transition-colors disabled:opacity-30">
                  {copied === p.id + "_manual" ? "✓ Copied" : "Copy"}
                </button>
                {p.shareUrl && text.trim() && (
                  <a href={p.shareUrl(text, link)} target="_blank" rel="noopener noreferrer"
                    className="text-xs font-bold px-3 py-1 bg-ink text-white rounded-lg hover:bg-ink/80 transition-colors">
                    Open
                  </a>
                )}
              </div>
            </div>
          ))}
          <div className="text-xs text-ink/30 text-center pt-1">
            <Link to="/plans" className="text-copper font-bold hover:underline">Upgrade to Member</Link> for AI-formatted posts
          </div>
        </div>
      )}

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

// ── Media Upload ──────────────────────────────────────────────────────────────
function MediaUploadSection() {
  const [preview, setPreview]     = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver]   = useState(false);
  const fileRef = useRef(null);

  function handleFile(file) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setPreview({ url, name: file.name, file });
  }

  function onDrop(e) {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  }

  async function upload() {
    if (!preview?.file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", preview.file);
      await api.post("/upload/media", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("Media uploaded!");
      setPreview(null);
    } catch (err) {
      if (err?.response?.status === 404) {
        toast.info("Media hosting coming soon — file not uploaded");
      } else {
        toast.error("Upload failed — try again");
      }
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="card-flat p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Image className="w-4 h-4 text-copper" />
        <span className="font-heading font-bold">Media Upload</span>
      </div>

      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        className={`cursor-pointer border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragOver ? "border-copper bg-copper/5" : "border-ink/15 hover:border-copper/50"
        }`}
      >
        <Upload className="w-7 h-7 text-ink/25 mx-auto mb-2" />
        <p className="text-sm text-ink/40">Drag & drop or <span className="text-copper font-bold">click to browse</span></p>
        <p className="text-xs text-ink/25 mt-1">Images, audio, video</p>
        <input ref={fileRef} type="file" className="hidden" accept="image/*,audio/*,video/*"
          onChange={e => handleFile(e.target.files?.[0])} />
      </div>

      {preview && (
        <div className="border border-ink/10 rounded-xl overflow-hidden">
          {preview.file.type.startsWith("image/") && (
            <img src={preview.url} alt={preview.name} className="w-full max-h-48 object-cover" />
          )}
          <div className="flex items-center justify-between px-3 py-2 bg-ink/3">
            <span className="text-xs text-ink/60 truncate max-w-[60%]">{preview.name}</span>
            <div className="flex gap-2">
              <button onClick={() => setPreview(null)} className="text-xs text-ink/30 hover:text-red-500">Remove</button>
              <button onClick={upload} disabled={uploading}
                className="text-xs font-bold px-3 py-1 bg-copper text-white rounded-lg disabled:opacity-50">
                {uploading ? "Uploading…" : "Upload"}
              </button>
            </div>
          </div>
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

function InlineGhostProducer() {
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

// ── Settings Tab ──────────────────────────────────────────────────────────────
function SettingsTab({ profile, onSaved }) {
  const EMPTY_SOCIAL   = { platform: "", handle: "", url: "", note: "" };
  const EMPTY_OFFERING = { icon: "✨", title: "", desc: "" };
  const EMPTY_COMMERCE = { label: "", desc: "", url: "" };

  const [form, setForm] = useState({
    slug:           profile?.slug          || "",
    display_name:   profile?.display_name  || "",
    title:          profile?.title         || "",
    tagline:        profile?.tagline       || "",
    bio:            profile?.bio           || "",
    pronouns:       profile?.pronouns      || "",
    location:       profile?.location      || "",
    avatar:         profile?.avatar        || "✨",
    socials:        profile?.socials       || [],
    more_offerings: profile?.more_offerings || [],
    commerce:       profile?.commerce      || [],
  });
  const [saving, setSaving]     = useState(false);
  const [pwForm, setPwForm]     = useState({ current: "", next: "", confirm: "" });
  const [savingPw, setSavingPw] = useState(false);
  const [showPw, setShowPw]     = useState(false);

  const inputClass = "w-full text-sm px-3 py-2.5 rounded-lg border border-ink/15 bg-white focus:outline-none focus:border-copper";
  const f = (key) => ({ value: form[key], onChange: e => setForm(p => ({ ...p, [key]: e.target.value })) });

  function updateList(field, idx, key, val) {
    setForm(p => { const a = [...p[field]]; a[idx] = { ...a[idx], [key]: val }; return { ...p, [field]: a }; });
  }
  function addItem(field, empty)    { setForm(p => ({ ...p, [field]: [...p[field], { ...empty }] })); }
  function removeItem(field, idx)   { setForm(p => ({ ...p, [field]: p[field].filter((_, i) => i !== idx) })); }

  async function saveProfile(e) {
    e.preventDefault();
    if (!form.slug.trim() || !form.display_name.trim()) { toast.error("Profile URL and display name are required"); return; }
    if (!/^[a-z0-9-]+$/.test(form.slug)) { toast.error("Profile URL: lowercase letters, numbers, and hyphens only"); return; }
    setSaving(true);
    try {
      await api.put("/creator/profile", {
        slug:           form.slug.trim(),
        display_name:   form.display_name.trim(),
        title:          form.title.trim(),
        tagline:        form.tagline.trim(),
        bio:            form.bio.trim(),
        pronouns:       form.pronouns.trim(),
        location:       form.location.trim(),
        avatar:         form.avatar.trim() || "✨",
        socials:        form.socials.filter(s => s.platform && s.url),
        more_offerings: form.more_offerings.filter(o => o.title),
        commerce:       form.commerce.filter(c => c.label && c.url),
      });
      toast.success("Profile saved!");
      onSaved?.();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) { toast.error("Passwords don't match"); return; }
    if (pwForm.next.length < 8) { toast.error("Minimum 8 characters"); return; }
    setSavingPw(true);
    try {
      await api.post("/auth/change-password", { current_password: pwForm.current, new_password: pwForm.next });
      toast.success("Password changed!");
      setPwForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Password change failed");
    } finally {
      setSavingPw(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">

      <form onSubmit={saveProfile} className="space-y-6">

        {/* ── Identity ── */}
        <div className="card-flat p-5 space-y-4">
          <div className="font-heading font-bold text-base">Identity</div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Profile URL <span className="text-copper">*</span></label>
              <div className="flex items-center">
                <span className="text-xs text-ink/40 mr-1">/u/</span>
                <input {...f("slug")} placeholder="your-name" className={inputClass} />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Display Name <span className="text-copper">*</span></label>
              <input {...f("display_name")} placeholder="Your name" className={inputClass} />
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Title / Role</label>
              <input {...f("title")} placeholder="Poet · Artist · Builder" className={inputClass} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Pronouns</label>
              <input {...f("pronouns")} placeholder="they/them" className={inputClass} />
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Location</label>
              <input {...f("location")} placeholder="City, State" className={inputClass} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink/50">Avatar (emoji or image URL)</label>
              <input {...f("avatar")} placeholder="✨ or https://…" className={inputClass} />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-ink/50">Tagline</label>
            <input {...f("tagline")} placeholder="One sentence that says everything" className={inputClass} />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-ink/50">Bio</label>
            <textarea {...f("bio")} rows={4} placeholder="Your story in your words…"
              className={`${inputClass} resize-none`} />
          </div>
        </div>

        {/* ── Social Links ── */}
        <div className="card-flat p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-heading font-bold text-base">Social Links</div>
            <button type="button" onClick={() => addItem("socials", EMPTY_SOCIAL)}
              className="text-xs font-bold text-copper hover:text-copper/70">+ Add</button>
          </div>
          {form.socials.map((s, i) => (
            <div key={i} className="grid grid-cols-2 sm:grid-cols-4 gap-2 items-end">
              <input value={s.platform} onChange={e => updateList("socials", i, "platform", e.target.value)}
                placeholder="Platform" className={inputClass} />
              <input value={s.handle} onChange={e => updateList("socials", i, "handle", e.target.value)}
                placeholder="@handle" className={inputClass} />
              <input value={s.url} onChange={e => updateList("socials", i, "url", e.target.value)}
                placeholder="URL" className={inputClass} />
              <button type="button" onClick={() => removeItem("socials", i)}
                className="text-xs text-red-400 hover:text-red-600 font-bold">Remove</button>
            </div>
          ))}
          {form.socials.length === 0 && <p className="text-xs text-ink/30">No social links yet. Add one above.</p>}
        </div>

        {/* ── M.O.R.E. Offerings ── */}
        <div className="card-flat p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-heading font-bold text-base">M.O.R.E. Offerings</div>
            <button type="button" onClick={() => addItem("more_offerings", EMPTY_OFFERING)}
              className="text-xs font-bold text-copper hover:text-copper/70">+ Add</button>
          </div>
          {form.more_offerings.map((o, i) => (
            <div key={i} className="space-y-2 pb-3 border-b border-ink/5 last:border-0">
              <div className="grid grid-cols-2 gap-2">
                <input value={o.icon} onChange={e => updateList("more_offerings", i, "icon", e.target.value)}
                  placeholder="Icon (emoji)" className={inputClass} />
                <input value={o.title} onChange={e => updateList("more_offerings", i, "title", e.target.value)}
                  placeholder="Title" className={inputClass} />
              </div>
              <div className="flex gap-2">
                <textarea value={o.desc} onChange={e => updateList("more_offerings", i, "desc", e.target.value)}
                  placeholder="Description" rows={2} className={`${inputClass} resize-none flex-1`} />
                <button type="button" onClick={() => removeItem("more_offerings", i)}
                  className="text-xs text-red-400 hover:text-red-600 font-bold self-start mt-1">✕</button>
              </div>
            </div>
          ))}
          {form.more_offerings.length === 0 && <p className="text-xs text-ink/30">No offerings yet. Add what you offer the community.</p>}
        </div>

        {/* ── Products & Links ── */}
        <div className="card-flat p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="font-heading font-bold text-base">Products & Links</div>
            <button type="button" onClick={() => addItem("commerce", EMPTY_COMMERCE)}
              className="text-xs font-bold text-copper hover:text-copper/70">+ Add</button>
          </div>
          {form.commerce.map((c, i) => (
            <div key={i} className="grid sm:grid-cols-3 gap-2 items-end">
              <input value={c.label} onChange={e => updateList("commerce", i, "label", e.target.value)}
                placeholder="Label" className={inputClass} />
              <input value={c.url} onChange={e => updateList("commerce", i, "url", e.target.value)}
                placeholder="URL" className={inputClass} />
              <div className="flex gap-2">
                <input value={c.desc} onChange={e => updateList("commerce", i, "desc", e.target.value)}
                  placeholder="Description" className={`${inputClass} flex-1`} />
                <button type="button" onClick={() => removeItem("commerce", i)}
                  className="text-xs text-red-400 hover:text-red-600 font-bold">✕</button>
              </div>
            </div>
          ))}
          {form.commerce.length === 0 && <p className="text-xs text-ink/30">No products or links yet.</p>}
        </div>

        <button type="submit" disabled={saving} className="btn-copper w-full text-sm disabled:opacity-50">
          {saving ? "Saving…" : "Save Profile"}
        </button>
      </form>

      {/* ── Password ── */}
      <form onSubmit={changePassword} className="card-flat p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="font-heading font-bold text-base">Change Password</div>
          <button type="button" onClick={() => setShowPw(v => !v)}
            className="text-xs text-ink/40 hover:text-copper flex items-center gap-1">
            {showPw ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            {showPw ? "Hide" : "Show"}
          </button>
        </div>
        {[
          { key: "current", label: "Current password",      ph: "Current password" },
          { key: "next",    label: "New password",           ph: "At least 8 characters" },
          { key: "confirm", label: "Confirm new password",   ph: "Repeat new password" },
        ].map(({ key, label, ph }) => (
          <div key={key} className="space-y-1">
            <label className="text-xs font-bold text-ink/50">{label}</label>
            <input type={showPw ? "text" : "password"} value={pwForm[key]}
              onChange={e => setPwForm(p => ({ ...p, [key]: e.target.value }))}
              placeholder={ph} className={inputClass} />
          </div>
        ))}
        <button type="submit" disabled={savingPw || !pwForm.current || !pwForm.next}
          className="w-full text-sm font-bold py-2.5 rounded-lg border border-ink/20 hover:border-copper transition-colors disabled:opacity-40">
          {savingPw ? "Changing…" : "Change Password"}
        </button>
      </form>
    </div>
  );
}

// ── Learn Tab ─────────────────────────────────────────────────────────────────
function LearnTab({ user, status }) {
  const [enrolled, setEnrolled]   = useState([]);
  const [certs, setCerts]         = useState([]);
  const [creds, setCreds]         = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [meRes, certsRes, credsRes] = await Promise.allSettled([
          api.get("/auth/me"),
          api.get("/certificates"),
          api.get("/credentials"),
        ]);
        if (meRes.status === "fulfilled") {
          setEnrolled(meRes.value.data?.enrolled_modules || meRes.value.data?.enrollments || []);
        }
        if (certsRes.status === "fulfilled") {
          setCerts(certsRes.value.data?.certificates || certsRes.value.data || []);
        }
        if (credsRes.status === "fulfilled") {
          setCreds(credsRes.value.data?.credentials || credsRes.value.data || []);
        }
      } catch (_) {}
      finally { setLoading(false); }
    }
    load();
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <div className="w-5 h-5 border-2 border-copper border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="font-heading font-bold">Enrolled Modules</div>
          <Link to="/modules" className="text-xs text-copper font-bold hover:underline">View all →</Link>
        </div>
        {enrolled.length === 0 ? (
          <div className="card-flat p-8 text-center text-ink/30 text-sm">
            No enrollments yet.
            <Link to="/modules" className="block mt-2 text-copper font-bold">Browse modules →</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {enrolled.map((m, i) => (
              <div key={m.module_id || i} className="card-flat p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-copper/10 flex items-center justify-center shrink-0">
                  <BookOpen className="w-5 h-5 text-copper" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-sm truncate">{m.title || m.module_title || "Module"}</div>
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="flex-1 h-1.5 bg-ink/10 rounded-full overflow-hidden">
                      <div className="h-full bg-copper rounded-full transition-all"
                        style={{ width: `${m.progress || 0}%` }} />
                    </div>
                    <span className="text-xs text-ink/40 shrink-0">{m.progress || 0}%</span>
                  </div>
                </div>
                <Link to={`/modules/${m.module_id || m.id}`}
                  className="text-xs font-bold text-copper hover:underline shrink-0">
                  {m.progress >= 100 ? "Review" : "Continue"}
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Certificates */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="font-heading font-bold">Certificates</div>
          <Link to="/certificates" className="text-xs text-copper font-bold hover:underline">View all →</Link>
        </div>
        {certs.length === 0 ? (
          <p className="text-sm text-ink/30">No certificates earned yet.</p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {certs.slice(0, 4).map((c, i) => (
              <div key={c.id || i} className="card-flat p-4 flex items-center gap-3">
                <Award className="w-6 h-6 text-copper shrink-0" />
                <div className="min-w-0">
                  <div className="font-bold text-sm truncate">{c.title || c.course_title || "Certificate"}</div>
                  {c.issued_at && <div className="text-xs text-ink/40">{new Date(c.issued_at).toLocaleDateString()}</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Credentials */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="font-heading font-bold">Credentials</div>
          <Link to="/credentials" className="text-xs text-copper font-bold hover:underline">View all →</Link>
        </div>
        {creds.length === 0 ? (
          <p className="text-sm text-ink/30">No credentials yet.</p>
        ) : (
          <div className="space-y-2">
            {creds.slice(0, 4).map((c, i) => (
              <div key={c.id || i} className="card-flat p-3 flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
                <div className="min-w-0">
                  <div className="font-bold text-sm truncate">{c.title || c.label || "Credential"}</div>
                  {c.issued_at && <div className="text-xs text-ink/40">{new Date(c.issued_at).toLocaleDateString()}</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function UnifiedProfile() {
  const { username } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile]   = useState(null);
  const [courses, setCourses]   = useState([]);
  const [status, setStatus]     = useState(null);
  const [loading, setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState("home");

  // Determine if viewer is the owner
  const isOwner = user && profile && profile.is_owner === true;
  const viewerStatus = status;
  const isAdmin = ["admin", "executive_admin"].includes(user?.role);

  // Reload profile after settings save
  const reloadProfile = useCallback(async () => {
    if (!username) return;
    try {
      const r = await api.get(`/creator/profile/${username}`);
      setProfile(r.data.profile);
    } catch (_) {}
  }, [username]);

  useEffect(() => {
    if (!username) {
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
    <AppShell>
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-copper border-t-transparent rounded-full animate-spin" />
      </div>
    </AppShell>
  );

  if (!profile) return (
    <AppShell>
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4">
        <div className="font-heading text-2xl font-bold text-ink/40">Profile not found</div>
        <p className="text-sm text-ink/30">@{username} hasn't published their profile yet.</p>
        {user && <Link to="/creator/profile/edit" className="btn-copper text-sm">Set up your profile</Link>}
      </div>
    </AppShell>
  );

  const coverBg = profile.cover_url
    ? `url(${profile.cover_url}) center/cover no-repeat`
    : "linear-gradient(135deg, #1a0a00 0%, #3d1a00 40%, #c87941 100%)";

  const publishedCourses = courses.filter(c => c.status === "published");

  // Build tab list — same structure for ALL users, owner-only tabs hidden for non-owners
  const TABS = [
    { key: "home",     label: "Home" },
    { key: "create",   label: "Create",  ownerOnly: true },
    { key: "publish",  label: "Publish", ownerOnly: true },
    { key: "learn",    label: "Learn",   ownerOnly: true },
    { key: "settings", label: "Settings", ownerOnly: true },
    ...(isAdmin && isOwner ? [{ key: "control", label: "Control", ownerOnly: true }] : []),
  ].filter(t => !t.ownerOnly || isOwner);

  const canUsePublisherAI = canAccess(user, viewerStatus, "publisher_ai");
  const canUseGhost       = canAccess(user, viewerStatus, "ghost");

  return (
    <AppShell>
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
              <div className="text-sm text-ink/50">@{profile.slug}{profile.title && ` · ${profile.title}`}</div>
            </div>
            <div className="pb-2 flex items-center gap-2 shrink-0">
              {isOwner && (
                <button onClick={() => setActiveTab("settings")} className="flex items-center gap-1.5 text-xs font-bold border border-ink/20 px-3 py-1.5 rounded-full hover:border-copper transition-colors">
                  <Edit3 className="w-3.5 h-3.5" /> Edit
                </button>
              )}
              <SharePanel compact url={`/u/${profile.slug}`} title={`${profile.display_name} — WAI-Institute`} embed />
            </div>
          </div>

          {/* Tier badge — shows the admin-controlled feature tier */}
          {profile.feature_tier && profile.feature_tier !== "free" && (
            <div className="inline-flex items-center gap-1.5 text-xs font-bold bg-copper/10 text-copper border border-copper/20 px-3 py-1 rounded-full mb-4">
              <Zap className="w-3 h-3" /> {FEATURE_TIER_LABEL[profile.feature_tier] || profile.feature_tier} Member
            </div>
          )}

          {/* Bio */}
          {profile.bio && (
            <p className="text-sm text-ink/70 max-w-2xl mb-5 leading-relaxed">{profile.bio}</p>
          )}

          {/* Tab bar */}
          <div className="flex gap-0.5 border-b border-ink/10 mb-6 overflow-x-auto">
            {TABS.map(t => (
              <button key={t.key} onClick={() => setActiveTab(t.key)}
                className={`px-4 py-2.5 text-sm font-bold border-b-2 whitespace-nowrap transition-colors ${
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

              {/* ══ HOME tab ══ */}
              {activeTab === "home" && (
                <>
                  {/* Tracks */}
                  {profile.tracks?.length > 0 && (
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

                  {/* Published courses */}
                  {publishedCourses.length > 0 && (
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

                  {/* Socials on home (mobile friendly) */}
                  {profile.socials?.length > 0 && (
                    <div className="lg:hidden card-flat p-4 space-y-2">
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
                </>
              )}

              {/* ══ CREATE tab ══ */}
              {activeTab === "create" && isOwner && (
                <div className="space-y-6">
                  {canUseGhost ? (
                    <InlineGhostProducer />
                  ) : (
                    <LockedFeature name="Ghost Producer" requiredTier="Pro">
                      {/* Blurred preview */}
                      <div className="card-flat p-5 space-y-4 pointer-events-none">
                        <div className="flex items-center gap-2">
                          <Music className="w-4 h-4 text-copper" />
                          <span className="font-heading font-bold">Ghost Producer</span>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          {GHOST_CLONES.map(c => (
                            <div key={c.id} className="text-left p-3 rounded-xl border border-ink/10 bg-white">
                              <div className="text-xl mb-1.5">{c.icon}</div>
                              <div className="font-bold text-sm" style={{ color: c.color }}>{c.label}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </LockedFeature>
                  )}
                </div>
              )}

              {/* ══ PUBLISH tab ══ */}
              {activeTab === "publish" && isOwner && (
                <div className="space-y-6">
                  <InlineSocialPublisher canUseAI={canUsePublisherAI} />
                  <MediaUploadSection />
                </div>
              )}

              {/* ══ LEARN tab ══ */}
              {activeTab === "learn" && isOwner && (
                <LearnTab user={user} status={viewerStatus} />
              )}

              {/* ══ SETTINGS tab ══ */}
              {activeTab === "settings" && isOwner && (
                <SettingsTab profile={profile} onSaved={reloadProfile} />
              )}

              {/* ══ CONTROL tab (admin/exec only) ══ */}
              {activeTab === "control" && isOwner && isAdmin && (
                <div className="space-y-4">
                  <div className="font-heading font-bold text-lg">Admin Control</div>
                  <div className="grid sm:grid-cols-2 gap-3">
                    <ServiceCard icon={BarChart2}  title="Admin Dashboard"    desc="Platform overview"         to="/admin" />
                    <ServiceCard icon={Users}       title="User Management"    desc="Roles, accounts, access"   to="/admin/users" />
                    <ServiceCard icon={Settings}    title="System Health"      desc="Uptime, errors, services"  to="/admin/health" />
                    <ServiceCard icon={BarChart2}   title="Analytics"          desc="Users, engagement, trends" to="/admin/analytics" />
                    <ServiceCard icon={Radio}       title="Providers"          desc="LLM keys, AI routing"      to="/admin/providers" />
                    <ServiceCard icon={Globe}       title="Audit Log"          desc="Full platform activity"    to="/admin/audit" />
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
                <div className="card-flat p-4 space-y-2 hidden lg:block">
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

              {/* Quick nav for owner */}
              {isOwner && (
                <div className="card-flat p-4 space-y-2">
                  <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-2">Quick Nav</div>
                  <button onClick={() => setActiveTab("settings")}
                    className="flex items-center justify-between w-full text-sm text-ink/50 hover:text-copper transition-colors py-0.5">
                    <span>Edit Profile</span><Edit3 className="w-3 h-3" />
                  </button>
                  {[
                    { label: "My Courses",   to: "/creator/courses" },
                    { label: "Modules",      to: "/modules" },
                    { label: "Certificates", to: "/certificates" },
                    { label: "Credentials",  to: "/credentials" },
                  ].map(({ label, to }) => (
                    <Link key={to} to={to}
                      className="flex items-center justify-between text-sm text-ink/50 hover:text-copper transition-colors py-0.5">
                      <span>{label}</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
