import { useState, useRef, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  Send, Bot, RefreshCw, Crown, TrendingUp, DollarSign,
  Video, Users, ChevronRight, Loader2, Trash2,
  Mic, MicOff, Volume2, VolumeX, CheckCircle,
} from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import { useMic } from "../hooks/useMic";

const LS_SESSION_KEY  = "more_ops_session_id";
const LS_MESSAGES_KEY = "more_ops_messages";
const MAX_LOCAL_MSGS  = 120; // keep last 120 messages in localStorage

function getStableSessionId() {
  let id = localStorage.getItem(LS_SESSION_KEY);
  if (!id) { id = uuidv4(); localStorage.setItem(LS_SESSION_KEY, id); }
  return id;
}

function loadLocalMessages() {
  try {
    const raw = localStorage.getItem(LS_MESSAGES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveLocalMessages(msgs) {
  try {
    localStorage.setItem(LS_MESSAGES_KEY, JSON.stringify(msgs.slice(-MAX_LOCAL_MSGS)));
  } catch {}
}

function recordToMessages(r) {
  const raw = r.assistant_msg || "";
  const lines = raw.split("\n");
  const firstLine = lines[0].trim();
  const displayContent =
    firstLine.startsWith("**") && firstLine.includes("|")
      ? lines.slice(1).join("\n").trimStart()
      : raw;
  return [
    { role: "user", content: r.user_msg },
    {
      role: "assistant",
      rawReply: raw,
      displayContent,
      persona: r.persona || "Department AI",
      department: r.department || "M.O.R.E.",
      mode: r.active_mode || "Balanced",
      isDecline: r.is_decline || false,
    },
  ];
}

const DEPARTMENTS = [
  { id: "",               label: "Auto-Route",       icon: Bot,         desc: "Let the AI choose the right department" },
  { id: "Executive",      label: "Executive",         icon: Crown,       desc: "Governance, crisis, system oversight" },
  { id: "Revenue",        label: "Revenue",           icon: TrendingUp,  desc: "Strategy, pipeline, offers, forecasting" },
  { id: "Finance",        label: "Finance",           icon: DollarSign,  desc: "Budgets, compliance, approvals, risk" },
  { id: "Production",     label: "Production",        icon: Video,       desc: "Video, design, copy, courses, audio, social" },
  { id: "Customer Success", label: "Client Success",  icon: Users,       desc: "Onboarding, retention, relationships" },
];

const MODE_COLORS = {
  Conservative: "bg-blue-100 text-blue-800",
  Balanced:     "bg-green-100 text-green-800",
  Creative:     "bg-purple-100 text-purple-800",
  Aggressive:   "bg-red-100 text-red-800",
  Recovery:     "bg-yellow-100 text-yellow-800",
};

function ModeChip({ mode }) {
  const cls = MODE_COLORS[mode] || "bg-ink/10 text-ink/60";
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wide ${cls}`}>
      {mode}
    </span>
  );
}

function PersonaHeader({ persona, department, mode }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <Bot className="w-4 h-4 text-copper flex-shrink-0" />
      <span className="font-heading font-bold text-sm text-ink">{persona}</span>
      {department && department !== "M.O.R.E." && (
        <>
          <ChevronRight className="w-3 h-3 text-ink/30" />
          <span className="text-xs text-ink/50">{department}</span>
        </>
      )}
      <ModeChip mode={mode} />
    </div>
  );
}

function MessageBubble({ msg, onSpeak }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-copper text-bone rounded-2xl rounded-br-sm px-4 py-3 text-sm whitespace-pre-wrap">
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%]">
        <PersonaHeader persona={msg.persona} department={msg.department} mode={msg.mode} />
        <div className={`rounded-2xl rounded-tl-sm px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed ${
          msg.isDecline
            ? "bg-amber-50 border border-amber-200 text-ink"
            : "bg-white border border-ink/10 text-ink"
        }`}>
          {msg.isDecline && (
            <div className="text-xs font-bold text-amber-700 uppercase tracking-wide mb-2">
              Declined — this is a recorded response
            </div>
          )}
          {msg.displayContent}
          {onSpeak && (
            <button
              onClick={() => onSpeak(msg.displayContent)}
              title="Read aloud"
              className="ml-2 opacity-40 hover:opacity-70 transition-opacity align-middle"
              style={{ background: "none", border: "none", cursor: "pointer", fontSize: 13, padding: 0 }}
            >
              🔊
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MoreOps() {
  const { user } = useAuth();
  const [sessionId] = useState(getStableSessionId);
  const [dept, setDept] = useState("");
  const [input, setInput] = useState("");
  // Load from localStorage immediately — instant, no network wait
  const [messages, setMessages] = useState(loadLocalMessages);
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Audio state
  const [audioOn, setAudioOn] = useState(false);
  const speakAudioRef = useRef(null);
  const speakAbortRef = useRef(null);

  const stopAudio = useCallback(() => {
    speakAbortRef.current?.abort();
    if (speakAudioRef.current) { speakAudioRef.current.pause(); speakAudioRef.current = null; }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  }, []);

  const speak = useCallback(async (text) => {
    if (!audioOn || !text) return;
    stopAudio();
    const controller = new AbortController();
    speakAbortRef.current = controller;
    try {
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${BACKEND_URL}/api/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text: text.slice(0, 1500), voice: "onyx", speed: 1.0, session_id: sessionId }),
        signal: controller.signal,
      });
      if (!r.ok) throw new Error("tts-fail");
      const blob = await r.blob();
      if (!blob.size) throw new Error("empty");
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      speakAudioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); speakAudioRef.current = null; };
      audio.play().catch(() => { URL.revokeObjectURL(url); speakAudioRef.current = null; _browserSpeak(text); });
    } catch (e) {
      if (e?.name !== "AbortError") { speakAudioRef.current = null; _browserSpeak(text); }
    }
  }, [audioOn, sessionId, stopAudio]);

  function _browserSpeak(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text.slice(0, 500));
    utt.rate = 0.95;
    window.speechSynthesis.speak(utt);
  }

  // STT — continuous mode, appends to input
  const { listening: recording, toggle: toggleMic, supported: micSupported } = useMic({
    onResult: (txt) => setInput((cur) => cur ? `${cur} ${txt}` : txt),
    onError:  (msg) => toast.error(msg),
    continuous: true,
    silenceMs: 2000,
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-save to localStorage on every message change
  useEffect(() => {
    if (!messages.length) return;
    saveLocalMessages(messages);
    setSavedAt(new Date());
  }, [messages]);

  // Background sync from backend — fills in history if localStorage was empty or stale
  useEffect(() => {
    api.get("/more/department/history?limit=60")
      .then(({ data }) => {
        const records = data.history || [];
        if (!records.length) return;
        const restored = records.flatMap(recordToMessages);
        // Only replace if backend has more messages than local (don't overwrite newer local state)
        setMessages(prev => restored.length > prev.length ? restored : prev);
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Build history array for API (alternating user/assistant)
  const buildHistory = () => {
    return messages.map((m) => ({
      role: m.role,
      content: m.role === "user" ? m.content : m.rawReply,
    }));
  };

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const { data } = await api.post("/more/department/chat", {
        session_id: sessionId,
        message: text,
        history: buildHistory(),
        department_hint: dept || undefined,
      });

      // Strip the **[PERSONA | DEPT | Mode: X]** header line from display
      const raw = data.reply || "";
      const lines = raw.split("\n");
      const firstLine = lines[0].trim();
      const displayContent =
        firstLine.startsWith("**") && firstLine.includes("|")
          ? lines.slice(1).join("\n").trimStart()
          : raw;

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          rawReply: raw,
          displayContent,
          persona: data.persona,
          department: data.department,
          mode: data.mode,
          isDecline: data.is_decline || false,
        },
      ]);
      speak(displayContent);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Department AI unavailable");
      // Remove optimistically added user message on failure
      setMessages((prev) => prev.slice(0, -1));
      setInput(text);
    } finally {
      setBusy(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const clearSession = () => {
    const newId = uuidv4();
    localStorage.setItem(LS_SESSION_KEY, newId);
    localStorage.removeItem(LS_MESSAGES_KEY);
    setMessages([]);
    setInput("");
    setSavedAt(null);
  };

  const activeDept = DEPARTMENTS.find((d) => d.id === dept) || DEPARTMENTS[0];

  return (
    <AppShell>
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {/* Sidebar — department selector */}
        <aside className="w-64 flex-shrink-0 border-r border-ink/10 flex flex-col bg-bone overflow-y-auto">
          <div className="p-4 border-b border-ink/10">
            <div className="overline text-copper text-xs">M.O.R.E. Ops</div>
            <h2 className="font-heading font-bold text-lg mt-0.5">Department AI</h2>
            <p className="text-xs text-ink/50 mt-1">13 specialized personas. One intelligence.</p>
          </div>
          <nav className="flex-1 p-3 space-y-1">
            {DEPARTMENTS.map((d) => {
              const Icon = d.icon;
              const active = dept === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setDept(d.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg flex items-start gap-3 transition-colors ${
                    active
                      ? "bg-copper/10 border border-copper/30"
                      : "hover:bg-ink/5 border border-transparent"
                  }`}
                >
                  <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${active ? "text-copper" : "text-ink/40"}`} />
                  <div>
                    <div className={`text-sm font-bold ${active ? "text-copper" : "text-ink"}`}>{d.label}</div>
                    <div className="text-xs text-ink/40 leading-snug mt-0.5">{d.desc}</div>
                  </div>
                </button>
              );
            })}
          </nav>
          <div className="p-3 border-t border-ink/10">
            <button
              onClick={clearSession}
              disabled={messages.length === 0}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ink/50 hover:text-ink/80 hover:bg-ink/5 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Trash2 className="w-4 h-4" /> Clear session
            </button>
          </div>
        </aside>

        {/* Main chat area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-ink/10 bg-white/50 flex-shrink-0">
            <div className="flex items-center gap-3">
              <activeDept.icon className="w-5 h-5 text-copper" />
              <div>
                <span className="font-heading font-bold">{activeDept.label}</span>
                <span className="text-ink/40 text-sm ml-2">— {activeDept.desc}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Speaker / TTS toggle */}
              <button
                onClick={() => { setAudioOn((v) => !v); if (audioOn) stopAudio(); }}
                title={audioOn ? "Voice output ON — click to mute" : "Voice output OFF — click to enable"}
                aria-label={audioOn ? "Mute voice output" : "Enable voice output"}
                className={`flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                  audioOn ? "bg-copper text-bone" : "bg-ink/10 text-ink/40 hover:text-ink/70"
                }`}
              >
                {audioOn ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </button>
              <button
                onClick={clearSession}
                disabled={messages.length === 0}
                className="flex items-center gap-1.5 text-xs text-ink/40 hover:text-ink/70 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-3.5 h-3.5" /> New session
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
                <Bot className="w-12 h-12 text-copper/50" />
                <div className="font-heading font-bold text-lg text-ink/80">M.O.R.E. Department AI</div>
                <p className="text-sm max-w-sm text-ink/60">
                  Ask anything across Finance, Revenue, Production, Customer Success, or Executive
                  governance. The system routes your message to the right specialist.
                </p>
                <div className="text-xs text-ink/50 mt-2">
                  Signed in as <span className="font-mono">{user?.full_name}</span>
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} onSpeak={msg.role === "assistant" ? speak : null} />
            ))}
            {busy && (
              <div className="flex justify-start">
                <div className="bg-white border border-ink/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 text-ink/70 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" /> Routing to department…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex-shrink-0 border-t border-ink/10 bg-white px-6 py-4">
            <div className="flex items-end gap-3">
              {/* Mic button */}
              <button
                type="button"
                onClick={micSupported ? toggleMic : () => toast.error("Voice input requires Chrome or Edge.")}
                title={!micSupported ? "Voice input not supported in this browser" : recording ? "Stop listening (click or wait for silence)" : "Start voice input"}
                aria-label={recording ? "Stop dictation" : "Dictate message"}
                className={`flex-shrink-0 flex items-center justify-center w-11 h-11 rounded-xl transition-all ${
                  !micSupported
                    ? "bg-ink/5 text-ink/25 cursor-not-allowed"
                    : recording
                    ? "bg-red-500 text-white shadow-lg shadow-red-500/30 animate-pulse"
                    : "bg-ink/10 text-ink/50 hover:bg-copper/10 hover:text-copper"
                }`}
              >
                {recording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder={recording ? "Listening — speak now…" : `Message ${activeDept.label} department…`}
                rows={2}
                className={`flex-1 resize-none px-4 py-3 bg-bone border rounded-xl focus:outline-none focus:ring-2 text-sm placeholder:text-ink/30 transition-colors ${
                  recording
                    ? "border-red-400 focus:ring-red-300 focus:border-red-400"
                    : "border-ink/20 focus:ring-copper/30 focus:border-copper"
                }`}
              />
              <button
                onClick={send}
                disabled={!input.trim() || busy}
                className="flex-shrink-0 btn-primary px-4 py-3 rounded-xl flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-ink/40">
                {recording
                  ? <span className="text-red-500 font-medium">● Recording — speak now. Click mic or wait 2s to stop.</span>
                  : "Enter to send · Shift+Enter for new line · Mic for voice input"}
              </p>
              {savedAt && (
                <span className="text-xs text-ink/30 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  Saved {savedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
