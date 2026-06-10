import { useState, useRef, useCallback, useEffect } from "react";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import SovereignAvatar from "./SovereignAvatar";
import { Send, X, Mic, MicOff, Volume2, VolumeX, Paperclip, Music, FileText, Image, Trash2, RefreshCw, Plus, ChevronRight } from "lucide-react";
import { useMic } from "../hooks/useMic";
import { toast } from "sonner";

const STORAGE_KEY = "sovereign_chat_history";
const MAX_STORED  = 40;

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}
function saveHistory(msgs) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-MAX_STORED))); } catch (_e) {}
}

function FileChip({ file, onRemove, onPlay, playing }) {
  const isAudio = file.is_audio || file.content_type?.startsWith("audio/");
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 6, padding: "4px 10px",
      background: "rgba(212,175,55,0.12)", border: "1px solid var(--wai-gold)",
      borderRadius: 20, fontSize: 12, color: "var(--wai-gold-light)", maxWidth: "100%",
    }}>
      {isAudio ? <Music style={{ width: 12, height: 12, flexShrink: 0 }} />
        : file.content_type?.startsWith("image/") ? <Image style={{ width: 12, height: 12, flexShrink: 0 }} />
        : <FileText style={{ width: 12, height: 12, flexShrink: 0 }} />}
      <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 140 }}>{file.filename}</span>
      {isAudio && (
        <button type="button" onClick={() => onPlay(file)}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--wai-gold)", padding: 0, fontSize: 13 }}
          title={playing ? "Pause" : "Play"}>
          {playing ? "⏸" : "▶"}
        </button>
      )}
      <button type="button" onClick={() => onRemove(file.file_id)}
        style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.4)", padding: 0 }}>
        <X style={{ width: 11, height: 11 }} />
      </button>
    </div>
  );
}

const STAGE_ORDER = ["Prospecting","Outreach","Conversation","Proposal","Negotiation","Confirmed","Delivered","Lost"];
const VERTICALS = ["Corporate","University","PAC/Museum/Library","Nonprofit"];
const STAGE_COLORS = {
  Prospecting: "#6b7280",
  Outreach: "#3b82f6",
  Conversation: "#8b5cf6",
  Proposal: "#f59e0b",
  Negotiation: "#ef4444",
  Confirmed: "var(--wai-emerald)",
  Delivered: "#10b981",
  Lost: "#4b5563",
};

function PipelineTab({ userId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState({
    institution: "", vertical: "Corporate", stage: "Prospecting",
    fee_offered: "", contact_name: "",
  });

  const fetchPipeline = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/sovereign/pipeline");
      setData(r.data);
    } catch (e) {
      toast.error("Could not load pipeline");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPipeline(); }, [fetchPipeline]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!addForm.institution.trim()) return toast.error("Institution required");
    try {
      const payload = {
        institution: addForm.institution.trim(),
        vertical: addForm.vertical,
        stage: addForm.stage,
        fee_offered: addForm.fee_offered ? Math.round(parseFloat(addForm.fee_offered) * 100) : 0,
        contact_name: addForm.contact_name,
      };
      await api.post("/sovereign/pipeline", payload);
      toast.success(`${addForm.institution} added to pipeline`);
      setAddForm({ institution: "", vertical: "Corporate", stage: "Prospecting", fee_offered: "", contact_name: "" });
      setShowAdd(false);
      fetchPipeline();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to add record");
    }
  };

  const advanceStage = async (record) => {
    const idx = STAGE_ORDER.indexOf(record.stage);
    if (idx < 0 || idx >= STAGE_ORDER.length - 2) return; // don't advance past Delivered
    const nextStage = STAGE_ORDER[idx + 1];
    try {
      await api.patch(`/sovereign/pipeline/${record.id}`, { stage: nextStage });
      toast.success(`${record.institution} → ${nextStage}`);
      fetchPipeline();
    } catch (e) {
      toast.error("Update failed");
    }
  };

  const markLost = async (record) => {
    if (!window.confirm(`Mark ${record.institution} as Lost?`)) return;
    try {
      await api.patch(`/sovereign/pipeline/${record.id}`, { stage: "Lost" });
      toast.success(`${record.institution} marked Lost`);
      fetchPipeline();
    } catch (e) {
      toast.error("Update failed");
    }
  };

  const summary = data?.summary;
  const records = data?.records || [];

  // Group by stage
  const byStage = {};
  for (const r of records) {
    if (!byStage[r.stage]) byStage[r.stage] = [];
    byStage[r.stage].push(r);
  }

  const formatFee = (cents) => {
    if (!cents) return null;
    return `$${(cents / 100).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Summary bar */}
      {summary && (
        <div style={{
          display: "flex", gap: 8, padding: "8px 12px", flexShrink: 0,
          borderBottom: "1px solid var(--wai-border)", flexWrap: "wrap",
        }}>
          <div style={{ flex: 1, minWidth: 100, background: "rgba(16,185,129,0.12)", borderRadius: 8, padding: "6px 10px", textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "var(--wai-muted)" }}>Confirmed</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#10b981" }}>{formatFee(summary.confirmed_revenue) || "$0"}</div>
          </div>
          <div style={{ flex: 1, minWidth: 100, background: "rgba(212,175,55,0.10)", borderRadius: 8, padding: "6px 10px", textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "var(--wai-muted)" }}>Weighted</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--wai-gold)" }}>{formatFee(summary.weighted_pipeline) || "$0"}</div>
          </div>
          <div style={{ flex: 1, minWidth: 80, background: "rgba(255,255,255,0.05)", borderRadius: 8, padding: "6px 10px", textAlign: "center" }}>
            <div style={{ fontSize: 11, color: "var(--wai-muted)" }}>Total</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--wai-text)" }}>{summary.total_count}</div>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div style={{ display: "flex", gap: 8, padding: "8px 12px", flexShrink: 0, alignItems: "center" }}>
        <button
          onClick={() => setShowAdd((v) => !v)}
          style={{ display: "flex", alignItems: "center", gap: 4, background: "var(--wai-gold)", color: "#1a1100", border: "none", borderRadius: 6, padding: "4px 10px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
          <Plus style={{ width: 12, height: 12 }} /> Add
        </button>
        <button
          onClick={fetchPipeline}
          disabled={loading}
          title="Refresh"
          style={{ background: "rgba(255,255,255,0.08)", border: "none", borderRadius: 6, padding: "4px 8px", cursor: "pointer", color: "var(--wai-muted)" }}>
          <RefreshCw style={{ width: 12, height: 12 }} />
        </button>
        {loading && <span style={{ fontSize: 11, color: "var(--wai-muted)" }}>Loading…</span>}
      </div>

      {/* Add form */}
      {showAdd && (
        <form onSubmit={handleAdd} style={{ padding: "0 12px 8px", flexShrink: 0, borderBottom: "1px solid var(--wai-border)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <input
              placeholder="Institution name *"
              value={addForm.institution}
              onChange={e => setAddForm(f => ({ ...f, institution: e.target.value }))}
              style={{ background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 6, padding: "5px 8px", fontSize: 12 }}
            />
            <div style={{ display: "flex", gap: 6 }}>
              <select value={addForm.vertical} onChange={e => setAddForm(f => ({ ...f, vertical: e.target.value }))}
                style={{ flex: 1, background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 6, padding: "5px 6px", fontSize: 11 }}>
                {VERTICALS.map(v => <option key={v}>{v}</option>)}
              </select>
              <select value={addForm.stage} onChange={e => setAddForm(f => ({ ...f, stage: e.target.value }))}
                style={{ flex: 1, background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 6, padding: "5px 6px", fontSize: 11 }}>
                {STAGE_ORDER.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <input
                placeholder="Contact name"
                value={addForm.contact_name}
                onChange={e => setAddForm(f => ({ ...f, contact_name: e.target.value }))}
                style={{ flex: 1, background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 6, padding: "5px 8px", fontSize: 12 }}
              />
              <input
                placeholder="Fee ($)"
                value={addForm.fee_offered}
                onChange={e => setAddForm(f => ({ ...f, fee_offered: e.target.value }))}
                type="number"
                min="0"
                style={{ width: 90, background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 6, padding: "5px 8px", fontSize: 12 }}
              />
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button type="submit" style={{ flex: 1, background: "var(--wai-gold)", color: "#1a1100", border: "none", borderRadius: 6, padding: "5px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Add Institution</button>
              <button type="button" onClick={() => setShowAdd(false)} style={{ background: "rgba(255,255,255,0.08)", color: "var(--wai-muted)", border: "none", borderRadius: 6, padding: "5px 10px", fontSize: 12, cursor: "pointer" }}>Cancel</button>
            </div>
          </div>
        </form>
      )}

      {/* Records grouped by stage */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px" }}>
        {records.length === 0 && !loading && (
          <div style={{ color: "var(--wai-muted)", fontSize: 13, textAlign: "center", padding: "24px 0" }}>
            No institutions in pipeline yet. Add your first one above.
          </div>
        )}
        {STAGE_ORDER.map(stage => {
          const recs = byStage[stage];
          if (!recs?.length) return null;
          return (
            <div key={stage} style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: STAGE_COLORS[stage] || "var(--wai-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>
                {stage} ({recs.length})
              </div>
              {recs.map(r => (
                <div key={r.id} style={{
                  background: "rgba(255,255,255,0.04)", border: "1px solid var(--wai-border)",
                  borderRadius: 8, padding: "8px 10px", marginBottom: 6,
                }}>
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 6 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 13, color: "var(--wai-text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {r.institution}
                      </div>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 3 }}>
                        {r.vertical && (
                          <span style={{ fontSize: 10, background: "rgba(212,175,55,0.15)", color: "var(--wai-gold)", borderRadius: 10, padding: "1px 7px" }}>{r.vertical}</span>
                        )}
                        {formatFee(r.fee_offered) && (
                          <span style={{ fontSize: 10, color: "#10b981", fontWeight: 600 }}>{formatFee(r.fee_offered)}</span>
                        )}
                        {r.hos_score > 0 && (
                          <span style={{ fontSize: 10, color: "var(--wai-muted)" }}>HOS {r.hos_score.toFixed(1)}</span>
                        )}
                      </div>
                      {r.contact_name && (
                        <div style={{ fontSize: 11, color: "var(--wai-muted)", marginTop: 2 }}>{r.contact_name}</div>
                      )}
                      {r.notes && (
                        <div style={{ fontSize: 11, color: "var(--wai-muted)", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.notes}</div>
                      )}
                    </div>
                    {stage !== "Confirmed" && stage !== "Delivered" && stage !== "Lost" && (
                      <div style={{ display: "flex", flexDirection: "column", gap: 4, flexShrink: 0 }}>
                        <button
                          onClick={() => advanceStage(r)}
                          title={`Move to ${STAGE_ORDER[STAGE_ORDER.indexOf(stage) + 1]}`}
                          style={{ background: "rgba(212,175,55,0.15)", border: "1px solid var(--wai-gold)", borderRadius: 5, padding: "3px 6px", cursor: "pointer", color: "var(--wai-gold)", fontSize: 11, display: "flex", alignItems: "center", gap: 2 }}>
                          <ChevronRight style={{ width: 11, height: 11 }} /> Next
                        </button>
                        <button
                          onClick={() => markLost(r)}
                          title="Mark as Lost"
                          style={{ background: "rgba(255,100,100,0.1)", border: "1px solid rgba(255,100,100,0.3)", borderRadius: 5, padding: "3px 6px", cursor: "pointer", color: "#f87171", fontSize: 11 }}>
                          Lost
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function SovereignChat() {
  const { user, loading } = useAuth();
  const [open, setOpen]         = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [messages, setMessages] = useState(loadHistory);
  const [input, setInput]       = useState("");
  const [sending, setSending]   = useState(false);
  const [audioOn, setAudioOn]   = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [playingId, setPlayingId] = useState(null);

  const speakAudioRef  = useRef(null);
  const speakAbortRef  = useRef(null);
  const trackAudioRef  = useRef(null);
  const fileInputRef   = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => { saveHistory(messages); }, [messages]);
  useEffect(() => {
    if (open) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  // ── TTS ─────────────────────────────────────────────────────────────────────
  const speak = useCallback(async (text) => {
    if (!audioOn || !text) return;
    speakAbortRef.current?.abort();
    if (speakAudioRef.current) { speakAudioRef.current.pause(); speakAudioRef.current = null; }
    const controller = new AbortController();
    speakAbortRef.current = controller;
    try {
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${BACKEND_URL}/api/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text: text.slice(0, 1500), voice: "onyx", speed: 1.0, session_id: "sovereign" }),
        signal: controller.signal,
      });
      if (!r.ok) { _browserSpeak(text); return; }
      const blob = await r.blob();
      if (!blob.size) { _browserSpeak(text); return; }
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      speakAudioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); speakAudioRef.current = null; };
      audio.play().catch(() => { URL.revokeObjectURL(url); speakAudioRef.current = null; _browserSpeak(text); });
    } catch (e) {
      if (e?.name !== "AbortError") { speakAudioRef.current = null; _browserSpeak(text); }
    }
  }, [audioOn]);

  function _browserSpeak(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text.slice(0, 500));
    utt.rate = 0.95;
    window.speechSynthesis.speak(utt);
  }

  const stopAudio = useCallback(() => {
    speakAbortRef.current?.abort();
    if (speakAudioRef.current) { speakAudioRef.current.pause(); speakAudioRef.current = null; }
  }, []);

  // ── Track playback ───────────────────────────────────────────────────────────
  const playTrack = useCallback((file) => {
    if (playingId === file.file_id) {
      trackAudioRef.current?.pause();
      setPlayingId(null);
      return;
    }
    if (trackAudioRef.current) { trackAudioRef.current.pause(); trackAudioRef.current = null; }
    if (!file.objectUrl) { toast.error("Track URL not available — re-upload to play."); return; }
    const audio = new Audio(file.objectUrl);
    trackAudioRef.current = audio;
    setPlayingId(file.file_id);
    audio.onended = () => setPlayingId(null);
    audio.onerror = () => { setPlayingId(null); toast.error("Could not play track."); };
    audio.play().catch(() => setPlayingId(null));
  }, [playingId]);

  // ── STT ─────────────────────────────────────────────────────────────────────
  const { listening: recording, toggle: toggleMic } = useMic({
    onResult: (txt) => setInput((cur) => cur ? `${cur} ${txt}` : txt),
    onError:  () => {},
  });

  // ── File upload ──────────────────────────────────────────────────────────────
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      // Do NOT set Content-Type manually — browser must set it with the multipart boundary
      const r = await api.post("/sovereign/upload", form);
      const data = r.data;
      const fileEntry = { ...data };
      if (data.is_audio) {
        fileEntry.objectUrl = URL.createObjectURL(file);
      }
      setAttachedFiles((prev) => [...prev, fileEntry]);
      toast.success(`${data.filename} attached`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeFile = (file_id) => {
    setAttachedFiles((prev) => {
      const f = prev.find(x => x.file_id === file_id);
      if (f?.objectUrl) URL.revokeObjectURL(f.objectUrl);
      return prev.filter(x => x.file_id !== file_id);
    });
    if (playingId === file_id) { trackAudioRef.current?.pause(); setPlayingId(null); }
  };

  // Not rendered until auth is confirmed — prevents flash-of-null on load
  if (loading || user?.role !== "executive_admin") return null;

  // ── Send ─────────────────────────────────────────────────────────────────────
  const send = async (e) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || sending) return;

    const fileNote = attachedFiles.length
      ? `\n\n[Attached: ${attachedFiles.map(f => f.filename).join(", ")}]`
      : "";
    const displayMsg = msg + fileNote;

    setMessages((m) => [...m, { role: "user", text: displayMsg }]);
    setInput("");
    setSending(true);

    const payload = {
      message: attachedFiles.length
        ? `${msg}\n\n[FILES: ${attachedFiles.map(f => `${f.filename} (id:${f.file_id}${f.is_audio ? ", AUDIO TRACK" : ""})`).join("; ")}]`
        : msg,
    };
    setAttachedFiles([]);

    try {
      const r = await api.post("/sovereign/chat", payload);
      const reply = r.data?.reply || "…";
      setMessages((m) => [...m, { role: "sovereign", text: reply }]);
      speak(reply);
    } catch (_e) {
      setMessages((m) => [...m, { role: "sovereign", text: "(The Sovereign is unavailable right now — try again shortly.)" }]);
    } finally {
      setSending(false);
    }
  };

  const clearHistory = () => {
    if (window.confirm("Clear conversation history?")) {
      setMessages([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        data-testid="summon-sovereign"
        className="fixed bottom-6 left-6 flex items-center gap-2 px-4 py-3 rounded-full font-bold shadow-lg"
        style={{ zIndex: 1400, background: "var(--wai-emerald)", color: "var(--wai-gold-light)", border: "1px solid var(--wai-gold)" }}
      >
        <SovereignAvatar size={28} /> Summon The Sovereign
      </button>
    );
  }

  return (
    <div
      className="fixed bottom-6 left-6 flex flex-col rounded-2xl overflow-hidden shadow-2xl"
      style={{
        zIndex: 1400,
        width: "min(480px, calc(100vw - 3rem))",
        height: "min(640px, calc(100vh - 3rem))",
        background: "var(--wai-navy)",
        border: "1px solid var(--wai-gold)",
        resize: "both",
      }}
      data-testid="sovereign-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3" style={{ background: "var(--wai-emerald)", flexShrink: 0 }}>
        <div className="flex items-center gap-2" style={{ color: "var(--wai-gold-light)" }}>
          <SovereignAvatar size={32} />
          <span className="font-heading font-bold">The Sovereign</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearHistory} title="Clear history"
            style={{ background: "rgba(255,255,255,0.1)", border: "none", borderRadius: "50%", width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "var(--wai-gold-light)" }}>
            <Trash2 style={{ width: 13, height: 13 }} />
          </button>
          <button
            onClick={() => { setAudioOn((v) => !v); if (audioOn) stopAudio(); }}
            title={audioOn ? "Voice ON — click to mute" : "Voice OFF"}
            style={{ background: audioOn ? "var(--wai-gold)" : "rgba(255,255,255,0.15)", border: "none", borderRadius: "50%", width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: audioOn ? "#1a1100" : "var(--wai-gold-light)" }}>
            {audioOn ? <Volume2 style={{ width: 14, height: 14 }} /> : <VolumeX style={{ width: 14, height: 14 }} />}
          </button>
          <button onClick={() => { setOpen(false); stopAudio(); }} aria-label="Close" style={{ color: "var(--wai-gold-light)", background: "none", border: "none", cursor: "pointer" }}>
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--wai-border)", flexShrink: 0 }}>
        {["chat", "pipeline"].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1, padding: "8px 0", fontSize: 13, fontWeight: activeTab === tab ? 700 : 400,
              background: "none", border: "none", cursor: "pointer",
              color: activeTab === tab ? "var(--wai-gold)" : "var(--wai-muted)",
              borderBottom: activeTab === tab ? "2px solid var(--wai-gold)" : "2px solid transparent",
              textTransform: "capitalize",
            }}
          >
            {tab === "chat" ? "Chat" : "Pipeline"}
          </button>
        ))}
      </div>

      {/* Pipeline tab */}
      {activeTab === "pipeline" && (
        <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <PipelineTab userId={user?.id} />
        </div>
      )}

      {/* Chat tab */}
      {activeTab === "chat" && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ color: "var(--wai-text)" }}>
            {messages.length === 0 && (
              <div>
                <div className="text-sm mb-3" style={{ color: "var(--wai-muted)" }}>
                  Your sovereign self — booking, revenue, counsel, and catalog management. Speak or send files.
                </div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { label: "📊 Morning Report", msg: "Morning report" },
                    { label: "💼 Pipeline Status", msg: "Give me the full pipeline status" },
                    { label: "📅 Next Actions", msg: "What are my action items this week?" },
                    { label: "💰 Revenue Summary", msg: "Revenue summary — confirmed and projected" },
                  ].map(({ label, msg }) => (
                    <button key={msg} type="button"
                      onClick={() => setInput(msg)}
                      style={{
                        background: "rgba(212,175,55,0.12)", border: "1px solid var(--wai-gold)",
                        borderRadius: 20, padding: "4px 12px", fontSize: 12,
                        color: "var(--wai-gold-light)", cursor: "pointer",
                      }}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div
                  className="inline-block px-3 py-2 rounded-xl text-sm whitespace-pre-wrap"
                  style={
                    m.role === "user"
                      ? { background: "var(--wai-purple)", color: "#fff", maxWidth: "85%" }
                      : { background: "rgba(212,175,55,0.12)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", maxWidth: "85%" }
                  }
                >
                  {m.text}
                  {m.role === "sovereign" && (
                    <button onClick={() => speak(m.text)} title="Read aloud"
                      style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, opacity: 0.5, marginLeft: 6, padding: 0, verticalAlign: "middle" }}>
                      🔊
                    </button>
                  )}
                </div>
              </div>
            ))}
            {sending && <div className="text-xs" style={{ color: "var(--wai-muted)" }}>The Sovereign is considering…</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* Attached files */}
          {attachedFiles.length > 0 && (
            <div style={{ padding: "6px 12px", borderTop: "1px solid var(--wai-border)", display: "flex", flexWrap: "wrap", gap: 6, flexShrink: 0 }}>
              {attachedFiles.map((f) => (
                <FileChip key={f.file_id} file={f} onRemove={removeFile} onPlay={playTrack} playing={playingId === f.file_id} />
              ))}
            </div>
          )}

          {/* Input bar */}
          <form onSubmit={send} className="p-3 flex gap-2" style={{ borderTop: "1px solid var(--wai-border)", flexShrink: 0 }}>
            {/* File upload */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md,.jpg,.jpeg,.png,.webp,.mp3,.m4a,.wav,.ogg"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title="Attach file (PDF, TXT, image, MP3)"
              style={{ background: uploading ? "rgba(212,175,55,0.3)" : "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: "0 10px", cursor: "pointer", color: "var(--wai-gold-light)", flexShrink: 0 }}>
              {uploading ? "⏳" : <Paperclip style={{ width: 15, height: 15 }} />}
            </button>

            {/* Mic */}
            <button
              type="button"
              onClick={toggleMic}
              title={recording ? "Stop dictation" : "Voice input"}
              style={{ background: recording ? "#dc2626" : "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: "0 10px", cursor: "pointer", color: recording ? "#fff" : "var(--wai-gold-light)", flexShrink: 0 }}>
              {recording ? <MicOff style={{ width: 15, height: 15 }} /> : <Mic style={{ width: 15, height: 15 }} />}
            </button>

            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={recording ? "Listening…" : "Ask The Sovereign…"}
              data-testid="sovereign-input"
              style={{ background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 8, padding: "0.5rem 0.75rem", flex: 1, minWidth: 0 }}
            />
            <button
              type="submit"
              disabled={sending}
              data-testid="sovereign-send"
              className="px-3 rounded-lg font-bold disabled:opacity-50"
              style={{ background: "var(--wai-gold)", color: "#1a1100", flexShrink: 0 }}>
              <Send className="w-4 h-4" />
            </button>
          </form>
        </>
      )}
    </div>
  );
}
