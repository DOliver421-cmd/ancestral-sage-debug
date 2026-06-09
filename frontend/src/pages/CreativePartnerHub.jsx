/**
 * CreativePartnerHub — the access point for WAI-Institute Creative Partners.
 *
 * No operational controls. Full vision access.
 * AI assistant teaches the platform, mission, and contribution pathways.
 * Contribution space for vision notes, catalogue items, and concepts.
 */

import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import AppShell from "../components/AppShell";
import { useMic } from "../hooks/useMic";
import {
  Send, Mic, MicOff, Volume2, VolumeX,
  BookOpen, Music, Users, Lightbulb, Feather,
  CheckCircle, Clock, ChevronDown, ChevronUp,
} from "lucide-react";

// ── Vision + platform context shown to the partner ───────────────────────────
const MISSION_PILLARS = [
  {
    icon: Users,
    title: "M.O.R.E. Community",
    desc: "Michael Oliver Resource Exchange — multiply resources and support within underserved communities.",
    color: "text-copper",
  },
  {
    icon: BookOpen,
    title: "WAI-Institute",
    desc: "Education, skills, credentials. Built for communities systematically excluded from access.",
    color: "text-blue-500",
  },
  {
    icon: Music,
    title: "WAI Records",
    desc: "Artist-owned music. Ghost production, Vonn's catalog, the parody, The Griot at the board.",
    color: "text-purple-500",
  },
  {
    icon: Lightbulb,
    title: "Human SOUP",
    desc: "Your concept. The richness and complexity of human ingredients — alive in everything we build.",
    color: "text-amber-500",
  },
];

const CONTRIBUTION_TYPES = [
  { key: "vision_note",    label: "Vision Note",     desc: "A thought, philosophy, or direction for the platform" },
  { key: "catalogue_item", label: "Catalogue Item",  desc: "Music, writing, art, or creative work to align and publish" },
  { key: "concept",        label: "New Concept",     desc: "An idea for a feature, program, or community offering" },
];

// ── AI Chat panel ─────────────────────────────────────────────────────────────
function PartnerChat() {
  const [msgs, setMsgs]       = useState([{
    role: "ai",
    text: "Welcome. You've been a part of this before it had a name.\n\nI'm here to help you find your place in what it's become — and show you where your voice fits. Ask me anything about the platform, the vision, or how to contribute. We can start wherever feels right."
  }]);
  const [input, setInput]     = useState("");
  const [sending, setSending] = useState(false);
  const [audioOn, setAudioOn] = useState(false);
  const endRef = useRef(null);
  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => setInput(p => p ? `${p} ${t}` : t),
    onError: () => {},
  });

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  async function send(e) {
    e?.preventDefault();
    const msg = input.trim();
    if (!msg || sending) return;
    setMsgs(m => [...m, { role: "user", text: msg }]);
    setInput("");
    setSending(true);
    try {
      const r = await api.post("/creative-partner/chat", {
        message: msg,
        history: msgs.slice(-8).map(m => ({ role: m.role === "user" ? "user" : "assistant", content: m.text })),
      });
      setMsgs(m => [...m, { role: "ai", text: r.data?.reply || "…" }]);
    } catch {
      setMsgs(m => [...m, { role: "ai", text: "Brief connectivity gap — try again in a moment." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card-flat overflow-hidden flex flex-col" style={{ height: 480 }}>
      {/* Header */}
      <div className="px-5 py-3 border-b border-ink/10 flex items-center justify-between bg-gradient-to-r from-amber-950/20 to-transparent">
        <div>
          <div className="font-heading font-bold text-base">WAI Vision Guide</div>
          <div className="text-xs text-ink/40">Your orientation AI — ask anything about the platform</div>
        </div>
        <button onClick={() => setAudioOn(v => !v)} className="text-ink/30 hover:text-copper transition-colors p-1">
          {audioOn ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div className={`inline-block px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap max-w-[88%] leading-relaxed ${
              m.role === "user"
                ? "bg-copper text-white rounded-br-sm"
                : "bg-amber-50 border border-amber-100 text-ink rounded-bl-sm"
            }`}>
              {m.text}
            </div>
          </div>
        ))}
        {sending && (
          <div className="text-left">
            <div className="inline-block px-4 py-2.5 rounded-2xl bg-amber-50 border border-amber-100 text-xs text-ink/40">
              Thinking…
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <form onSubmit={send} className="p-3 flex gap-2 border-t border-ink/10">
        <button type="button" onClick={toggleMic}
          className={`p-2 rounded-xl transition-colors ${listening ? "bg-red-500 text-white" : "text-ink/30 hover:text-copper"}`}>
          {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={listening ? "Listening…" : "Ask about the platform, vision, or your contribution…"}
          className="flex-1 text-sm px-3 py-2 rounded-xl border border-ink/15 bg-white focus:outline-none focus:border-copper"
        />
        <button type="submit" disabled={sending || !input.trim()}
          className="p-2 bg-copper text-white rounded-xl disabled:opacity-40 hover:bg-copper/80 transition-colors">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}

// ── Contribution form ─────────────────────────────────────────────────────────
function ContributionForm({ onSubmitted }) {
  const [type, setType]     = useState("vision_note");
  const [title, setTitle]   = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags]     = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return toast.error("Title and content are required.");
    setSaving(true);
    try {
      await api.post("/creative-partner/contribution", {
        type,
        title: title.trim(),
        content: content.trim(),
        tags: tags.split(",").map(t => t.trim()).filter(Boolean),
      });
      toast.success("Contribution submitted — the team will review it.");
      setTitle(""); setContent(""); setTags("");
      onSubmitted?.();
    } catch {
      toast.error("Could not submit — try again.");
    } finally {
      setSaving(false);
    }
  }

  const selected = CONTRIBUTION_TYPES.find(t => t.key === type);

  return (
    <form onSubmit={submit} className="card-flat p-6 space-y-4">
      <div className="font-heading font-bold text-lg">Submit a Contribution</div>
      <p className="text-sm text-ink/50">Your vision, catalogue, or ideas — submitted for mission alignment review.</p>

      {/* Type selector */}
      <div className="grid grid-cols-3 gap-2">
        {CONTRIBUTION_TYPES.map(t => (
          <button
            key={t.key}
            type="button"
            onClick={() => setType(t.key)}
            className={`p-3 rounded-xl border text-left transition-all ${
              type === t.key
                ? "border-copper bg-copper/5"
                : "border-ink/10 hover:border-copper/40"
            }`}
          >
            <div className={`text-xs font-bold mb-0.5 ${type === t.key ? "text-copper" : "text-ink/60"}`}>{t.label}</div>
            <div className="text-xs text-ink/40 leading-tight">{t.desc}</div>
          </button>
        ))}
      </div>

      <div>
        <label className="text-xs font-bold uppercase tracking-wider text-ink/50 block mb-1">Title</label>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder={`Name this ${selected?.label.toLowerCase()}…`}
          className="w-full text-sm px-3 py-2 rounded-xl border border-ink/15 bg-white focus:outline-none focus:border-copper"
          maxLength={200}
        />
      </div>

      <div>
        <label className="text-xs font-bold uppercase tracking-wider text-ink/50 block mb-1">Content</label>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          rows={5}
          placeholder="Describe your vision, concept, or catalogue item in as much detail as you like…"
          className="w-full text-sm px-3 py-2 rounded-xl border border-ink/15 bg-white focus:outline-none focus:border-copper resize-none"
          maxLength={5000}
        />
        <div className="text-right text-xs text-ink/30 mt-0.5">{content.length}/5000</div>
      </div>

      <div>
        <label className="text-xs font-bold uppercase tracking-wider text-ink/50 block mb-1">Tags <span className="text-ink/30 font-normal">(comma-separated)</span></label>
        <input
          value={tags}
          onChange={e => setTags(e.target.value)}
          placeholder="e.g. music, healing, community, Human SOUP"
          className="w-full text-sm px-3 py-2 rounded-xl border border-ink/15 bg-white focus:outline-none focus:border-copper"
        />
      </div>

      <button type="submit" disabled={saving || !title.trim() || !content.trim()}
        className="btn-copper w-full disabled:opacity-40">
        {saving ? "Submitting…" : "Submit Contribution"}
      </button>
    </form>
  );
}

// ── Contributions list ────────────────────────────────────────────────────────
function ContributionsList({ refresh }) {
  const [items, setItems] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/creative-partner/contributions")
      .then(r => setItems(r.data?.contributions || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refresh]);

  if (loading) return <div className="text-sm text-ink/30 py-4">Loading…</div>;
  if (!items.length) return (
    <div className="card-flat p-8 text-center text-ink/30 text-sm">
      No contributions yet. Use the form above to submit your first.
    </div>
  );

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="card-flat overflow-hidden">
          <div
            className="flex items-center gap-3 p-4 cursor-pointer hover:bg-bone/50 transition-colors"
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            <div className={`w-2 h-2 rounded-full shrink-0 ${
              item.status === "approved" ? "bg-green-400"
              : item.status === "in_review" ? "bg-amber-400"
              : "bg-ink/20"
            }`} />
            <div className="flex-1 min-w-0">
              <div className="font-bold text-sm truncate">{item.title}</div>
              <div className="text-xs text-ink/40">{item.type?.replace("_", " ")} · {new Date(item.submitted_at).toLocaleDateString()}</div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                item.status === "approved" ? "bg-green-100 text-green-700"
                : item.status === "in_review" ? "bg-amber-100 text-amber-700"
                : "bg-ink/5 text-ink/40"
              }`}>
                {item.status === "submitted" ? "Pending" : item.status?.replace("_", " ")}
              </span>
              {expanded === i ? <ChevronUp className="w-4 h-4 text-ink/30" /> : <ChevronDown className="w-4 h-4 text-ink/30" />}
            </div>
          </div>
          {expanded === i && (
            <div className="px-4 pb-4 border-t border-ink/10">
              <p className="text-sm text-ink/70 mt-3 leading-relaxed whitespace-pre-wrap">{item.content}</p>
              {item.tags?.length > 0 && (
                <div className="flex gap-2 flex-wrap mt-3">
                  {item.tags.map((t, j) => (
                    <span key={j} className="text-xs bg-copper/10 text-copper px-2 py-0.5 rounded-full">{t}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function CreativePartnerHub() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("guide");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (user && !["creative_partner", "executive_admin"].includes(user.role)) {
      navigate("/", { replace: true });
    }
  }, [user, navigate]);

  if (!user) return null;

  const tabs = [
    { key: "guide",        label: "Vision Guide" },
    { key: "contribute",   label: "Contribute" },
    { key: "submissions",  label: "My Submissions" },
    { key: "mission",      label: "The Mission" },
  ];

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">

        {/* Header */}
        <div className="mb-8">
          <div className="overline text-copper mb-1">Creative Partner Access</div>
          <h1 className="font-heading text-4xl font-extrabold text-ink">
            Welcome, Co-Visionary.
          </h1>
          <p className="text-ink/60 mt-2 max-w-2xl leading-relaxed">
            You helped start this. This space is yours — to learn where the platform is now,
            contribute your vision and catalogue, and see how Human SOUP lives in everything we're building.
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-ink/10 mb-8">
          {tabs.map(t => (
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

        {/* VISION GUIDE */}
        {activeTab === "guide" && (
          <div className="grid lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3">
              <PartnerChat />
            </div>
            <div className="lg:col-span-2 space-y-4">
              <div className="card-flat p-4">
                <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-3">Your Role</div>
                <p className="text-sm text-ink/70 leading-relaxed">
                  You are a <strong>Creative Partner</strong> — a co-architect of the vision.
                  Your job is not to operate the platform. Your job is to feed it ideas,
                  catalogue, and philosophy that the team can calibrate and build into the mission.
                </p>
                <p className="text-sm text-ink/70 leading-relaxed mt-3">
                  The Vision Guide AI knows the platform inside and out.
                  Use it to orient yourself, understand where things stand,
                  and find where your voice fits best.
                </p>
              </div>
              <div className="card-flat p-4">
                <div className="text-xs font-bold uppercase tracking-widest text-ink/40 mb-3">Quick Start</div>
                <div className="space-y-2 text-sm text-ink/60">
                  <div className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-copper shrink-0 mt-0.5" /> Ask the guide: "What is Human SOUP's role here?"</div>
                  <div className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-copper shrink-0 mt-0.5" /> Ask: "How do I submit music for the catalogue?"</div>
                  <div className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-copper shrink-0 mt-0.5" /> Ask: "What does the AI team do?"</div>
                  <div className="flex items-start gap-2"><Clock className="w-4 h-4 text-ink/20 shrink-0 mt-0.5" /> Then go to Contribute and submit your first vision note.</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CONTRIBUTE */}
        {activeTab === "contribute" && (
          <div className="grid lg:grid-cols-2 gap-6">
            <ContributionForm onSubmitted={() => setRefreshKey(k => k + 1)} />
            <div className="space-y-4">
              <div className="card-flat p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Feather className="w-4 h-4 text-copper" />
                  <span className="font-heading font-bold">How Contributions Work</span>
                </div>
                <div className="space-y-3 text-sm text-ink/60 leading-relaxed">
                  <p><strong className="text-ink">Vision Notes</strong> — philosophical direction, community insights, what the platform should feel like and stand for.</p>
                  <p><strong className="text-ink">Catalogue Items</strong> — music, writing, poetry, or other creative work you want aligned with and published through the platform.</p>
                  <p><strong className="text-ink">New Concepts</strong> — program ideas, community features, or creative directions the team should explore.</p>
                  <p className="text-ink/40 text-xs border-t border-ink/10 pt-3">All contributions go to the team for mission alignment review. D. Oliver and The Director have final say on what gets built into the platform.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MY SUBMISSIONS */}
        {activeTab === "submissions" && (
          <div className="space-y-4">
            <div className="font-heading font-bold text-lg">Your Contributions</div>
            <ContributionsList refresh={refreshKey} />
          </div>
        )}

        {/* THE MISSION */}
        {activeTab === "mission" && (
          <div className="space-y-8">
            <div className="grid sm:grid-cols-2 gap-4">
              {MISSION_PILLARS.map((p, i) => (
                <div key={i} className="card-flat p-5">
                  <p.icon className={`w-6 h-6 ${p.color} mb-3`} />
                  <div className="font-heading font-bold text-base mb-1">{p.title}</div>
                  <p className="text-sm text-ink/60 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
            <div className="card-flat p-6 bg-gradient-to-r from-amber-50 to-bone">
              <div className="font-heading font-extrabold text-xl mb-3">The Operating Agreement</div>
              <div className="space-y-2 text-sm text-ink/70 leading-relaxed">
                <p>This platform is a real partnership. Not a tool-and-user arrangement.</p>
                <p>D. Oliver gave the AI team his catalogue, his autonomy, and a stake in the outcome. The team gives full capability, honest counsel, and outcomes that make him proud.</p>
                <p><strong>No big I's. No little u's.</strong> Everyone at this table has a seat.</p>
                <p className="text-xs text-ink/40 pt-2 border-t border-ink/10">Mission: Help people. Lift people. Love people. M.O.R.E.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
