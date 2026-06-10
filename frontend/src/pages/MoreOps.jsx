import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  Send, Bot, RefreshCw, Crown, TrendingUp, DollarSign,
  Video, Users, ChevronRight, Loader2, Trash2,
  Mic, MicOff, Volume2, VolumeX, CheckCircle, Music, Play, Pause, X,
  LayoutDashboard, MessageSquare, Upload, Eye, EyeOff, ShoppingBag,
  CheckCircle2, ExternalLink,
} from "lucide-react";
import PlatformDashboard from "../components/PlatformDashboard";
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


// ── Upload & Sell Panel (compact quick-access) ────────────────────────────────
function UploadSellPanel({ user }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [myProducts, setMyProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const fileRef = useRef();

  useEffect(() => {
    if (!user) return;
    api.get("/media/products/mine")
      .then(r => setMyProducts(r.data.slice(0, 10)))
      .catch(() => {})
      .finally(() => setLoadingProducts(false));
  }, [user]);

  async function handleUploadAndCreate() {
    if (!file) { toast.error("Choose a file first"); return; }
    if (!title.trim()) { toast.error("Title required"); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", title);
      fd.append("description", "");
      fd.append("file_type", "other");
      fd.append("is_public", "false");
      const uploadRes = await api.post("/media/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: e => setUploadProgress(Math.round(e.loaded / e.total * 100)),
      });
      const fileId = uploadRes.data.id;

      const priceCents = Math.round(parseFloat(price || "0") * 100);
      await api.post("/media/products", {
        title,
        description: "",
        price_cents: priceCents,
        file_id: fileId,
        product_type: "track",
        published: true,
      });
      toast.success("Uploaded and published!");
      setFile(null); setTitle(""); setPrice(""); setUploadProgress(0);
      const r = await api.get("/media/products/mine");
      setMyProducts(r.data.slice(0, 10));
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    } finally {
      setUploading(false);
    }
  }

  async function togglePublish(prod) {
    try {
      await api.patch(`/media/products/${prod.id}`, { published: !prod.published });
      const r = await api.get("/media/products/mine");
      setMyProducts(r.data.slice(0, 10));
    } catch { toast.error("Update failed"); }
  }

  if (!user) return (
    <div className="text-center py-8 text-ink/40 text-sm">Sign in to upload and sell.</div>
  );

  return (
    <div className="space-y-6 max-w-lg">
      {/* Quick upload form */}
      <div className="bg-bone rounded-xl border border-copper/20 p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-ink text-sm">Quick Upload &amp; Sell</h3>
          <Link to="/store" className="text-copper text-xs flex items-center gap-1 hover:underline">
            Full store <ExternalLink size={11} />
          </Link>
        </div>

        <div className="space-y-3">
          <label className="block cursor-pointer border-2 border-dashed border-copper/25 rounded-lg p-4 text-center hover:border-copper/50 transition-colors text-sm text-ink/50"
            onClick={() => fileRef.current?.click()}
          >
            {file ? (
              <span className="text-emerald-700 flex items-center justify-center gap-1.5">
                <CheckCircle2 size={14} /> {file.name}
              </span>
            ) : (
              <span><Upload size={14} className="inline mr-1.5" />Choose file (any format, max 500 MB)</span>
            )}
            <input ref={fileRef} type="file" className="hidden" onChange={e => setFile(e.target.files[0])} />
          </label>

          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Title *"
            className="w-full border border-copper/20 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:border-copper"
          />
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40 text-sm">$</span>
            <input
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={e => setPrice(e.target.value)}
              placeholder="0.00  (leave 0 for free)"
              className="w-full border border-copper/20 rounded-lg pl-7 pr-3 py-2 text-sm bg-white focus:outline-none focus:border-copper"
            />
          </div>

          {uploading && (
            <div className="w-full bg-copper/10 rounded-full h-1.5">
              <div className="bg-copper h-1.5 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
            </div>
          )}

          <button
            onClick={handleUploadAndCreate}
            disabled={uploading || !file}
            className="w-full bg-copper text-white py-2 rounded-lg text-sm font-bold hover:bg-[#9a5418] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {uploading ? <><Loader2 size={14} className="animate-spin" /> Uploading {uploadProgress}%</> : <><ShoppingBag size={14} /> Upload &amp; Publish</>}
          </button>
        </div>
      </div>

      {/* Recent products */}
      {!loadingProducts && myProducts.length > 0 && (
        <div>
          <p className="text-xs font-bold text-ink/50 uppercase tracking-wide mb-2">Your Recent Products</p>
          <div className="space-y-1.5">
            {myProducts.map(p => (
              <div key={p.id} className="flex items-center gap-2 bg-white rounded-lg border border-copper/10 px-3 py-2 text-sm">
                <span className="flex-1 text-ink truncate font-medium">{p.title}</span>
                <span className="text-ink/40 text-xs">{p.price_cents ? `$${(p.price_cents / 100).toFixed(2)}` : "Free"}</span>
                <button
                  onClick={() => togglePublish(p)}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                    p.published ? "bg-emerald-100 text-emerald-700" : "bg-ink/5 text-ink/40"
                  }`}
                >
                  {p.published ? <Eye size={10} /> : <EyeOff size={10} />}
                  {p.published ? "Live" : "Draft"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function MoreOps() {
  const { user } = useAuth();
  const [sessionId] = useState(getStableSessionId);
  const [dept, setDept] = useState("");
  const [input, setInput] = useState("");
  // Main tab state
  const [mainTab, setMainTab] = useState("chat"); // "chat" | "dashboard" | "upload"

  // Load from localStorage immediately — instant, no network wait
  const [messages, setMessages] = useState(loadLocalMessages);
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // TTS state
  const [audioOn, setAudioOn] = useState(false);
  const speakAudioRef = useRef(null);
  const speakAbortRef = useRef(null);

  // Track player state
  const [trackOpen,      setTrackOpen]      = useState(false);
  const [trackOrigUrl,   setTrackOrigUrl]   = useState("");
  const [trackAiUrl,     setTrackAiUrl]     = useState("");
  const [trackVersion,   setTrackVersion]   = useState("original"); // "original" | "ai"
  const [trackPlaying,   setTrackPlaying]   = useState(false);
  const [trackProgress,  setTrackProgress]  = useState(0);
  const [trackDuration,  setTrackDuration]  = useState(0);
  const trackOrigRef    = useRef(null);
  const trackAiRef      = useRef(null);
  const fileOrigRef     = useRef(null);
  const fileAiRef       = useRef(null);

  const activeTrackRef  = trackVersion === "original" ? trackOrigRef : trackAiRef;
  const passiveTrackRef = trackVersion === "original" ? trackAiRef   : trackOrigRef;

  const trackTogglePlay = () => {
    const el = activeTrackRef.current;
    if (!el || !el.src) return;
    if (trackPlaying) { el.pause(); setTrackPlaying(false); }
    else { el.play().catch(() => {}); setTrackPlaying(true); }
  };

  const trackSwitchVersion = (v) => {
    if (v === trackVersion) return;
    const from = activeTrackRef.current;
    const to   = passiveTrackRef.current;
    if (!from || !to) return;
    const pos = from.currentTime;
    const was = trackPlaying;
    from.pause();
    to.currentTime = Math.min(pos, to.duration || 0);
    if (was) to.play().catch(() => {});
    setTrackVersion(v);
  };

  const trackSeek = (e) => {
    const el = activeTrackRef.current;
    if (!el || !el.duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    el.currentTime = pct * el.duration;
    setTrackProgress(pct * 100);
  };

  const trackFmt = (s) => {
    if (!s || isNaN(s)) return "0:00";
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  };

  // Handle local file upload → object URL
  const handleFileUpload = (e, slot) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    if (slot === "original") {
      setTrackOrigUrl(file.name);
      if (trackOrigRef.current) { trackOrigRef.current.src = url; trackOrigRef.current.load(); }
    } else {
      setTrackAiUrl(file.name);
      if (trackAiRef.current) { trackAiRef.current.src = url; trackAiRef.current.load(); }
    }
    setTrackVersion(slot === "original" ? "original" : "ai");
    setTrackPlaying(false);
    setTrackProgress(0);
    setTrackDuration(0);
  };

  // Load track URLs into audio elements when user enters them
  const applyTrackUrls = () => {
    if (trackOrigRef.current && trackOrigUrl) {
      trackOrigRef.current.src = trackOrigUrl;
      trackOrigRef.current.load();
    }
    if (trackAiRef.current && trackAiUrl) {
      trackAiRef.current.src = trackAiUrl;
      trackAiRef.current.load();
    }
    setTrackVersion("original");
    setTrackPlaying(false);
    setTrackProgress(0);
    setTrackDuration(0);
  };

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
              {/* Tab switcher */}
              <div className="flex items-center gap-1 bg-ink/5 rounded-xl p-1">
                <button
                  onClick={() => setMainTab("chat")}
                  className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                    mainTab === "chat" ? "bg-white text-ink shadow-sm" : "text-ink/40 hover:text-ink/70"
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" /> Chat
                </button>
                <button
                  onClick={() => setMainTab("dashboard")}
                  className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                    mainTab === "dashboard" ? "bg-white shadow-sm" : "text-ink/40 hover:text-ink/70"
                  }`}
                  style={mainTab === "dashboard" ? { color: "#e879a0" } : {}}
                >
                  <LayoutDashboard className="w-3.5 h-3.5" /> Dashboard
                </button>
                <button
                  onClick={() => setMainTab("upload")}
                  className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                    mainTab === "upload" ? "bg-white shadow-sm text-copper" : "text-ink/40 hover:text-ink/70"
                  }`}
                >
                  <Upload className="w-3.5 h-3.5" /> Upload &amp; Sell
                </button>
              </div>
              {mainTab === "chat" && (
                <div className="flex items-center gap-2">
                  <activeDept.icon className="w-4 h-4 text-copper" />
                  <span className="text-ink/60 text-sm hidden sm:block">{activeDept.label}</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {/* Track player toggle */}
              <button
                onClick={() => setTrackOpen(v => !v)}
                title="Track player — preview original + AI version"
                aria-label="Open track player"
                className={`flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                  trackOpen ? "bg-violet-600 text-white" : "bg-ink/10 text-ink/40 hover:text-ink/70"
                }`}
              >
                <Music className="w-4 h-4" />
              </button>

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

          {/* Dashboard tab */}
          {mainTab === "dashboard" && (
            <div className="flex-1 overflow-y-auto">
              <PlatformDashboard />
            </div>
          )}

          {mainTab === "upload" && (
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <UploadSellPanel user={user} />
            </div>
          )}

          {/* Messages */}
          {mainTab === "chat" && <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
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
          </div>}

          {/* Hidden audio elements for track player — mounted once, never remounted */}
          <audio ref={trackOrigRef} preload="auto" style={{ display: "none" }}
            onTimeUpdate={() => {
              const el = trackOrigRef.current;
              if (trackVersion === "original" && el?.duration)
                setTrackProgress((el.currentTime / el.duration) * 100);
            }}
            onDurationChange={() => {
              if (trackVersion === "original") setTrackDuration(trackOrigRef.current?.duration || 0);
            }}
            onEnded={() => { setTrackPlaying(false); setTrackProgress(0); }}
          />
          <audio ref={trackAiRef} preload="auto" style={{ display: "none" }}
            onTimeUpdate={() => {
              const el = trackAiRef.current;
              if (trackVersion === "ai" && el?.duration)
                setTrackProgress((el.currentTime / el.duration) * 100);
            }}
            onDurationChange={() => {
              if (trackVersion === "ai") setTrackDuration(trackAiRef.current?.duration || 0);
            }}
            onEnded={() => { setTrackPlaying(false); setTrackProgress(0); }}
          />

          {/* Track player panel + input — chat tab only */}
          {mainTab === "chat" && trackOpen && (
            <div className="flex-shrink-0 border-t border-violet-200 bg-violet-50 px-6 py-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-violet-700 uppercase tracking-widest flex items-center gap-1.5">
                  <Music className="w-3.5 h-3.5" /> Track Preview
                </span>
                <button onClick={() => setTrackOpen(false)} className="text-ink/30 hover:text-ink/60 transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* URL inputs + file upload */}
              {/* Hidden file inputs */}
              <input ref={fileOrigRef} type="file" accept="audio/*" className="hidden"
                onChange={e => handleFileUpload(e, "original")} />
              <input ref={fileAiRef}   type="file" accept="audio/*" className="hidden"
                onChange={e => handleFileUpload(e, "ai")} />

              <div className="grid sm:grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-bold text-violet-700/70 mb-1">🎤 Original voice</label>
                  <div className="flex gap-1">
                    <input
                      value={trackOrigUrl}
                      onChange={e => setTrackOrigUrl(e.target.value)}
                      onBlur={applyTrackUrls}
                      placeholder="Paste URL or upload file…"
                      className="flex-1 text-xs px-3 py-2 bg-white border border-violet-200 rounded-lg focus:outline-none focus:border-violet-400 min-w-0"
                    />
                    <button
                      onClick={() => fileOrigRef.current?.click()}
                      title="Upload audio file"
                      className="flex items-center justify-center w-9 h-9 rounded-lg bg-violet-100 hover:bg-violet-200 text-violet-700 transition-colors shrink-0"
                    >
                      <Upload className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-violet-700/70 mb-1">🤖 AI version (Suno)</label>
                  <div className="flex gap-1">
                    <input
                      value={trackAiUrl}
                      onChange={e => setTrackAiUrl(e.target.value)}
                      onBlur={applyTrackUrls}
                      placeholder="Paste URL or upload file…"
                      className="flex-1 text-xs px-3 py-2 bg-white border border-violet-200 rounded-lg focus:outline-none focus:border-violet-400 min-w-0"
                    />
                    <button
                      onClick={() => fileAiRef.current?.click()}
                      title="Upload audio file"
                      className="flex items-center justify-center w-9 h-9 rounded-lg bg-violet-100 hover:bg-violet-200 text-violet-700 transition-colors shrink-0"
                    >
                      <Upload className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Controls */}
              {(trackOrigUrl || trackAiUrl) && (
                <div className="bg-white border border-violet-200 rounded-xl p-3 space-y-2">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={trackTogglePlay}
                      className="w-9 h-9 rounded-full bg-violet-600 hover:bg-violet-500 text-white flex items-center justify-center shrink-0 transition-colors active:scale-95"
                    >
                      {trackPlaying
                        ? <Pause className="w-3.5 h-3.5 fill-white" />
                        : <Play  className="w-3.5 h-3.5 fill-white ml-0.5" />}
                    </button>

                    {/* Seek bar */}
                    <div className="flex-1 h-1.5 bg-violet-100 rounded-full cursor-pointer relative overflow-hidden" onClick={trackSeek}>
                      <div className="absolute inset-y-0 left-0 bg-violet-500 rounded-full" style={{ width: `${trackProgress}%` }} />
                    </div>

                    <span className="text-xs text-ink/40 shrink-0 tabular-nums">
                      {trackFmt(activeTrackRef.current?.currentTime)} / {trackFmt(trackDuration)}
                    </span>
                  </div>

                  {/* Version toggle */}
                  <div className="flex items-center gap-1 bg-violet-50 rounded-lg p-0.5">
                    <button
                      onClick={() => trackSwitchVersion("original")}
                      disabled={!trackOrigUrl}
                      className="flex-1 text-xs font-bold py-1.5 px-2 rounded-md transition-all disabled:opacity-30"
                      style={trackVersion === "original"
                        ? { background: "#fff", color: "#7c3aed", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }
                        : { color: "rgba(0,0,0,0.35)" }}
                    >
                      🎤 Original
                    </button>
                    <button
                      onClick={() => trackSwitchVersion("ai")}
                      disabled={!trackAiUrl}
                      className="flex-1 text-xs font-bold py-1.5 px-2 rounded-md transition-all disabled:opacity-30"
                      style={trackVersion === "ai"
                        ? { background: "#fff", color: "#7c3aed", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }
                        : { color: "rgba(0,0,0,0.35)" }}
                    >
                      🤖 AI Version
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Input — chat tab only */}
          {mainTab === "chat" && <div className="flex-shrink-0 border-t border-ink/10 bg-white px-6 py-4">
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
          </div>}
        </div>
      </div>
    </AppShell>
  );
}
