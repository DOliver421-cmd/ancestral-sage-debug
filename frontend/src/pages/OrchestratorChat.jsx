import { useRef, useState, useCallback, useEffect } from "react";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  Send, Mic, MicOff, Volume2, VolumeX, Loader2, ChevronDown,
  ChevronUp, Layers, Shield, BookOpen, Compass, Users, Star,
  AlertTriangle, Zap, Download, Square, Paperclip, X, FileText,
  Image as ImageIcon, FileCode,
} from "lucide-react";
import { toast } from "sonner";

// ── Role metadata ────────────────────────────────────────────────────────────

const ROLE_META = {
  student: {
    label: "Learner",
    color: "text-signal",
    personas: ["Ancestral Sage", "Savant Scholar"],
    icon: BookOpen,
    description: "Cultural wisdom + educational guidance tailored to your learning journey.",
  },
  instructor: {
    label: "Instructor",
    color: "text-copper",
    personas: ["Ancestral Sage", "Savant Scholar", "Product & Experience Designer"],
    icon: Users,
    description: "Above + UX and curriculum design support.",
  },
  admin: {
    label: "Administrator",
    color: "text-amber-400",
    personas: [
      "Ancestral Sage", "Savant Scholar", "Product & Experience Designer",
      "Risk & Compliance Officer", "Strategic Navigator", "Assistant Director",
    ],
    icon: Shield,
    description: "Full team — threat classification, strategic planning, compliance.",
  },
  executive_admin: {
    label: "Executive Director",
    color: "text-purple-400",
    personas: [
      "Ancestral Sage", "Savant Scholar", "Product & Experience Designer",
      "Risk & Compliance Officer", "Strategic Navigator", "Assistant Director",
      "Confidentiality Sentinel",
    ],
    council: true,
    icon: Star,
    description: "Full 7-Persona Team + Council of 24 Elders + Threat Classification Engine.",
  },
};

// ── Protocol options (admin / exec only) ─────────────────────────────────────

const PROTOCOLS = [
  { key: "", label: "Auto-route (recommended)" },
  { key: "rapid_threat_response", label: "Rapid Threat Response" },
  { key: "full_council_session", label: "Full Council Session" },
  { key: "curriculum_design", label: "Curriculum / Design Session" },
  { key: "quiet_checkin", label: "Quiet Check-In (Director support)" },
];

// ── Markdown-lite renderer ───────────────────────────────────────────────────
// Turns **bold**, ## headers, and - bullets into HTML for exec structured output

function RichReply({ text }) {
  const lines = text.split("\n");
  const rendered = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (/^#{1,3}\s/.test(line)) {
      const level = line.match(/^(#+)/)[1].length;
      const content = line.replace(/^#+\s*/, "");
      rendered.push(
        <p key={i} className={`font-heading font-bold mt-4 mb-1 ${level === 1 ? "text-lg" : level === 2 ? "text-base" : "text-sm text-white/80"}`}>
          {content}
        </p>
      );
    } else if (/^[-*•]\s/.test(line)) {
      rendered.push(
        <li key={i} className="ml-4 list-disc text-sm leading-relaxed">
          {formatInline(line.replace(/^[-*•]\s/, ""))}
        </li>
      );
    } else if (line.trim() === "") {
      rendered.push(<div key={i} className="h-2" />);
    } else {
      rendered.push(
        <p key={i} className="text-sm leading-relaxed">
          {formatInline(line)}
        </p>
      );
    }
    i++;
  }
  return <div className="space-y-0.5">{rendered}</div>;
}

function formatInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, idx) =>
    p.startsWith("**") && p.endsWith("**")
      ? <strong key={idx}>{p.slice(2, -2)}</strong>
      : p
  );
}

// ── Speech recognition ───────────────────────────────────────────────────────

const SpeechRecognitionImpl =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

// ── Main component ───────────────────────────────────────────────────────────

export default function OrchestratorChat() {
  const { user } = useAuth();
  const role = user?.role || "student";
  const meta = ROLE_META[role] || ROLE_META.student;
  const isAdmin = role === "admin" || role === "executive_admin";
  const isExec = role === "executive_admin";

  const [msgs, setMsgs] = useState([]);        // {role, content, ts}
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `orch-${Date.now()}`);

  // File attachment state
  const [attachment, setAttachment] = useState(null); // {name, type, b64, preview}
  const fileInputRef = useRef(null);

  // Advanced options (admin+)
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [threatHint, setThreatHint] = useState("");
  const [protocol, setProtocol] = useState("");

  // Audio
  const [audioOn, setAudioOn] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [recording, setRecording] = useState(false);
  const recogRef = useRef(null);
  const audioElRef = useRef(null);
  const audioAbortRef = useRef(null);

  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  // ── TTS ──────────────────────────────────────────────────────────────────

  const playTTS = useCallback(async (text) => {
    if (!audioOn || !text) return;
    try {
      if (audioAbortRef.current) audioAbortRef.current.abort();
      const ctrl = new AbortController();
      audioAbortRef.current = ctrl;
      const r = await api.post(
        "/ai/sage/tts",
        { text: text.slice(0, 2000), voice: "sage", speed: 1.0, session_id: sessionId },
        { responseType: "arraybuffer", signal: ctrl.signal }
      );
      const blob = new Blob([r.data], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      if (audioElRef.current) {
        audioElRef.current.src = url;
        setAudioPlaying(true);
        audioElRef.current.play().catch(() => {});
        audioElRef.current.onended = () => setAudioPlaying(false);
      }
    } catch (e) {
      if (e?.code !== "ERR_CANCELED") {
        toast.error("Voice playback unavailable.");
      }
      setAudioPlaying(false);
    }
  }, [audioOn, sessionId]);

  const stopAudio = useCallback(() => {
    if (audioElRef.current) { audioElRef.current.pause(); audioElRef.current.src = ""; }
    if (audioAbortRef.current) audioAbortRef.current.abort();
    setAudioPlaying(false);
  }, []);

  // ── STT ──────────────────────────────────────────────────────────────────

  const startRecording = useCallback(() => {
    if (!SpeechRecognitionImpl) { toast.error("Speech input not supported in this browser."); return; }
    const r = new SpeechRecognitionImpl();
    r.continuous = false;
    r.interimResults = false;
    r.lang = "en-US";
    r.onresult = (e) => setInput((prev) => prev + e.results[0][0].transcript);
    r.onerror = () => setRecording(false);
    r.onend = () => setRecording(false);
    recogRef.current = r;
    r.start();
    setRecording(true);
  }, []);

  const stopRecording = useCallback(() => {
    recogRef.current?.stop();
    setRecording(false);
  }, []);

  // ── File attachment ───────────────────────────────────────────────────────

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const MAX = 10 * 1024 * 1024; // 10 MB
    if (file.size > MAX) {
      toast.error("File too large — maximum 10 MB.");
      e.target.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      // reader.result is "data:<mime>;base64,<data>" — strip the prefix
      const b64 = reader.result.split(",")[1];
      const isImage = file.type.startsWith("image/");
      setAttachment({ name: file.name, type: file.type, b64, isImage,
                      preview: isImage ? reader.result : null });
    };
    reader.readAsDataURL(file);
    e.target.value = ""; // allow re-selecting same file
  }, []);

  const clearAttachment = useCallback(() => setAttachment(null), []);

  // ── Send ──────────────────────────────────────────────────────────────────

  const send = useCallback(async (overrideText) => {
    const text = (overrideText ?? input).trim();
    if ((!text && !attachment) || loading) return;
    setInput("");
    const currentAttachment = attachment;
    setAttachment(null);
    setLoading(true);

    const displayContent = text + (currentAttachment ? ` 📎 ${currentAttachment.name}` : "");
    const userMsg = { role: "user", content: displayContent, ts: Date.now() };
    setMsgs((prev) => [...prev, userMsg]);

    // Build history from current msgs (exclude the one we just added)
    const history = msgs.map((m) => ({ role: m.role, content: m.content }));

    try {
      const payload = {
        session_id: sessionId,
        message: text,
        history,
        ...(threatHint ? { threat_hint: threatHint } : {}),
        ...(protocol ? { protocol } : {}),
        ...(currentAttachment ? {
          file_b64: currentAttachment.b64,
          file_name: currentAttachment.name,
          file_type: currentAttachment.type,
        } : {}),
      };
      const { data } = await api.post("/ai/orchestrator", payload);
      const assistantMsg = { role: "assistant", content: data.reply, ts: Date.now() };
      setMsgs((prev) => [...prev, assistantMsg]);
      playTTS(data.reply);
    } catch (err) {
      const detail = err?.response?.data?.detail || "The Council is unavailable. Please try again.";
      toast.error(detail);
      setMsgs((prev) => [...prev, {
        role: "assistant",
        content: `⚠ ${detail}`,
        ts: Date.now(),
        error: true,
      }]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, msgs, sessionId, threatHint, protocol, playTTS]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey) { e.preventDefault(); send(); }
  };

  // ── Export transcript ────────────────────────────────────────────────────

  const exportTranscript = () => {
    const lines = msgs.map((m) =>
      `[${m.role.toUpperCase()}] ${new Date(m.ts).toLocaleTimeString()}\n${m.content}`
    ).join("\n\n---\n\n");
    const blob = new Blob([lines], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `council-session-${sessionId}.txt`;
    a.click();
  };

  // ── Render ───────────────────────────────────────────────────────────────

  const MetaIcon = meta.icon;

  return (
    <AppShell>
      <audio ref={audioElRef} style={{ display: "none" }} />

      <div className="flex flex-col h-screen max-h-screen">
        {/* ─── Header ─── */}
        <div className="shrink-0 px-8 py-5 border-b border-ink/10 bg-bone">
          <div className="flex items-start justify-between">
            <div>
              <div className="overline text-copper flex items-center gap-2">
                <MetaIcon className={`w-4 h-4 ${meta.color}`} />
                WAI-Institute Council
              </div>
              <h1 className="font-heading text-2xl font-bold text-ink mt-1 flex items-center gap-2">
                <Layers className="w-6 h-6 text-signal" />
                Ancestral Sage Orchestrator
              </h1>
              <p className="text-ink/50 text-sm mt-1 max-w-xl">{meta.description}</p>
            </div>

            <div className="flex items-center gap-2 mt-1">
              {msgs.length > 0 && (
                <button
                  onClick={exportTranscript}
                  className="flex items-center gap-1.5 text-xs border border-ink/20 px-3 py-1.5 text-ink/60 hover:text-ink hover:border-ink/40 transition-colors"
                  title="Export session transcript"
                >
                  <Download className="w-3.5 h-3.5" /> Export
                </button>
              )}
              <button
                onClick={() => { audioOn ? setAudioOn(false) : setAudioOn(true); }}
                className={`flex items-center gap-1.5 text-xs border px-3 py-1.5 transition-colors ${audioOn ? "border-signal text-signal" : "border-ink/20 text-ink/60 hover:text-ink"}`}
                title={audioOn ? "Disable voice output" : "Enable voice output"}
              >
                {audioOn ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                {audioOn ? "Voice On" : "Voice Off"}
              </button>
            </div>
          </div>

          {/* Active persona chips */}
          <div className="flex flex-wrap gap-2 mt-3">
            {meta.personas.map((p) => (
              <span key={p} className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider bg-ink/5 text-ink/60 px-2 py-0.5 rounded-sm border border-ink/10">
                <Compass className="w-2.5 h-2.5" /> {p}
              </span>
            ))}
            {meta.council && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-sm border border-purple-400/20">
                <Star className="w-2.5 h-2.5" /> Council of 24 Elders
              </span>
            )}
          </div>

          {/* Admin+ options panel */}
          {isAdmin && (
            <div className="mt-3">
              <button
                onClick={() => setOptionsOpen((o) => !o)}
                className="flex items-center gap-1.5 text-xs text-ink/50 hover:text-ink/80 transition-colors"
              >
                {optionsOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                Advanced Options
              </button>
              {optionsOpen && (
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 p-4 bg-ink/3 border border-ink/10 rounded-sm">
                  <div>
                    <label className="text-xs font-semibold text-ink/60 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Threat Hint (optional)
                    </label>
                    <input
                      type="text"
                      value={threatHint}
                      onChange={(e) => setThreatHint(e.target.value)}
                      placeholder="e.g. hostile funding offer, policy attack…"
                      className="w-full text-sm border border-ink/20 bg-white px-3 py-2 text-ink placeholder:text-ink/30 focus:outline-none focus:border-signal"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-ink/60 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                      <Zap className="w-3 h-3" /> Force Protocol
                    </label>
                    <select
                      value={protocol}
                      onChange={(e) => setProtocol(e.target.value)}
                      className="w-full text-sm border border-ink/20 bg-white px-3 py-2 text-ink focus:outline-none focus:border-signal"
                    >
                      {PROTOCOLS.map((p) => (
                        <option key={p.key} value={p.key}>{p.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ─── Messages ─── */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {msgs.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-20">
              <Layers className="w-12 h-12 text-ink/40" />
              <div>
                <p className="font-heading text-xl font-bold text-ink/80">The Council awaits.</p>
                <p className="text-ink/60 text-sm mt-1 max-w-sm">
                  Bring your question, decision, or situation.
                  {isAdmin && " Optionally set a threat hint or protocol above."}
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4 max-w-lg w-full">
                {STARTER_PROMPTS[role]?.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => send(prompt)}
                    className="text-left text-sm text-ink/80 border border-ink/25 px-4 py-3 hover:border-signal hover:text-ink transition-colors leading-relaxed bg-white"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {msgs.map((m, idx) => (
            <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "user" ? (
                <div className="max-w-[70%] bg-signal text-ink px-4 py-3 text-sm leading-relaxed">
                  {m.content}
                </div>
              ) : (
                <div className={`max-w-[82%] bg-ink text-white px-5 py-4 ${m.error ? "border-l-2 border-destructive" : ""}`}>
                  <div className="text-[10px] uppercase tracking-widest text-white/40 mb-2 flex items-center gap-1.5">
                    <Compass className="w-3 h-3" />
                    {isExec ? "Council Response" : "Orchestrator"}
                    {audioPlaying && idx === msgs.length - 1 && (
                      <span className="flex items-center gap-1 ml-auto text-signal">
                        <Volume2 className="w-3 h-3 animate-pulse" /> Speaking
                        <button onClick={stopAudio} className="ml-1 text-white/50 hover:text-white">
                          <Square className="w-2.5 h-2.5" />
                        </button>
                      </span>
                    )}
                  </div>
                  {isExec ? <RichReply text={m.content} /> : (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-ink text-white px-5 py-4 flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-signal" />
                <span className="text-sm text-white/60">
                  {isExec ? "The Council is deliberating…" : "Processing…"}
                </span>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* ─── Input bar ─── */}
        <div className="shrink-0 px-8 py-4 border-t border-ink/10 bg-bone">
          {/* Attachment preview chip */}
          {attachment && (
            <div className="mb-2 flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-2 bg-white border border-signal/40 rounded-lg px-3 py-1.5 max-w-full">
                {attachment.isImage
                  ? <ImageIcon className="w-4 h-4 text-signal shrink-0" />
                  : attachment.type === "application/pdf"
                  ? <FileText className="w-4 h-4 text-red-500 shrink-0" />
                  : <FileCode className="w-4 h-4 text-blue-500 shrink-0" />
                }
                {attachment.preview && (
                  <img src={attachment.preview} alt="" className="w-8 h-8 object-cover rounded" />
                )}
                <span className="text-xs font-medium text-ink truncate max-w-[200px]">{attachment.name}</span>
                <button onClick={clearAttachment} className="text-ink/40 hover:text-red-500 transition-colors ml-1">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,application/pdf,text/*,.csv,.json,.md,.txt,.py,.js,.ts,.jsx,.tsx,.html,.css,.xml,.yaml,.yml"
            onChange={handleFileSelect}
            className="hidden"
          />

          <div className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={
                isExec
                  ? "Bring your situation to the Council…"
                  : isAdmin
                  ? "Ask the team or describe a threat…"
                  : "Ask the Ancestral Sage…"
              }
              rows={2}
              className="flex-1 resize-none border border-ink/20 bg-white px-4 py-3 text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:border-signal"
              disabled={loading}
            />
            <div className="flex flex-col gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
                className="p-3 border border-ink/20 text-ink/50 hover:text-signal hover:border-signal transition-colors disabled:opacity-40"
                title="Attach file (image, PDF, text, code)"
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <button
                onClick={() => recording ? stopRecording() : startRecording()}
                className={`p-3 border transition-colors ${recording ? "border-destructive text-destructive" : "border-ink/20 text-ink/50 hover:text-ink hover:border-ink/40"}`}
                title={recording ? "Stop recording" : "Speak"}
              >
                {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
              <button
                onClick={() => send()}
                disabled={loading || (!input.trim() && !attachment)}
                className="p-3 bg-signal text-ink hover:bg-signal/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Send"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <p className="text-[11px] text-ink/50 mt-2">
            Enter to send · Shift+Enter for new line · 📎 images, PDF, text &amp; code files supported · All sessions are logged for audit.
          </p>
        </div>
      </div>
    </AppShell>
  );
}

// ── Role-specific starter prompts ────────────────────────────────────────────

const STARTER_PROMPTS = {
  student: [
    "I'm struggling to stay motivated in my studies. What would the Sage say?",
    "Help me understand how historical context connects to what I'm learning.",
    "What learning path should I focus on to master the curriculum?",
    "I need help preparing for an upcoming assessment.",
  ],
  instructor: [
    "Help me design a culturally grounded lesson on this topic.",
    "How do I support a student who is disengaged without shaming them?",
    "What assessment methods feel equitable and rigorous at the same time?",
    "Review this module outline and suggest improvements.",
  ],
  admin: [
    "We've received a complaint that needs a strategic response.",
    "A funder is offering money with conditions. Help me evaluate it.",
    "Draft a 72-hour response plan for a reputational situation.",
    "What risks should we address before we scale this program?",
  ],
  executive_admin: [
    "I am calling a Full Council Session on whether to accept this partnership.",
    "Threat Response Mode: ON — we received a hostile government inquiry.",
    "I need a Quiet Check-In — I am feeling close to burnout as Director.",
    "Evaluate the long-term trajectory of our current growth strategy.",
  ],
};
