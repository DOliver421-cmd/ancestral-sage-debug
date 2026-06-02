import { useState, useRef, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { api, BACKEND_URL } from "../lib/api";
import SovereignAvatar from "./SovereignAvatar";
import { Send, X, Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { useMic } from "../hooks/useMic";

// Executive-only "Summon The Sovereign" launcher + resizable chat panel.
// Wired to POST /api/sovereign/chat (exec-gated on the backend). Renders nothing
// for non-exec users — members use the AI Tutor instead. Floats bottom-left so it
// never collides with the bottom-anchored Director widget.
export default function SovereignChat() {
  const { user } = useAuth();
  const [open, setOpen]       = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput]     = useState("");
  const [sending, setSending] = useState(false);

  // Audio state
  const [audioOn, setAudioOn] = useState(false);

  // Refs
  const speakAudioRef = useRef(null);
  const speakAbortRef = useRef(null);

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
      if (!r.ok) {
        _browserSpeak(text);
        return;
      }
      const blob = await r.blob();
      if (!blob.size) { _browserSpeak(text); return; }
      const url  = URL.createObjectURL(blob);
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

  // ── STT ─────────────────────────────────────────────────────────────────────
  const { listening: recording, toggle: toggleMic } = useMic({
    onResult: (txt) => setInput((cur) => cur ? `${cur} ${txt}` : txt),
    onError:  () => {},
  });

  if (user?.role !== "executive_admin") return null;

  // ── Send ─────────────────────────────────────────────────────────────────────
  const send = async (e) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || sending) return;
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setSending(true);
    try {
      const r = await api.post("/sovereign/chat", { message: msg });
      const reply = r.data?.reply || "…";
      setMessages((m) => [...m, { role: "sovereign", text: reply }]);
      speak(reply);
    } catch {
      setMessages((m) => [...m, { role: "sovereign", text: "(The Sovereign is unavailable right now — try again shortly.)" }]);
    } finally {
      setSending(false);
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
        width: "min(420px, calc(100vw - 3rem))",
        height: "min(560px, calc(100vh - 3rem))",
        background: "var(--wai-navy)",
        border: "1px solid var(--wai-gold)",
        resize: "both",
      }}
      data-testid="sovereign-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3" style={{ background: "var(--wai-emerald)" }}>
        <div className="flex items-center gap-2" style={{ color: "var(--wai-gold-light)" }}>
          <SovereignAvatar size={32} />
          <span className="font-heading font-bold">The Sovereign</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Voice output toggle */}
          <button
            onClick={() => { setAudioOn((v) => !v); if (audioOn) stopAudio(); }}
            title={audioOn ? "Voice ON — click to mute" : "Voice OFF — click to unmute"}
            aria-label={audioOn ? "Mute voice output" : "Enable voice output"}
            style={{
              background: audioOn ? "var(--wai-gold)" : "rgba(255,255,255,0.15)",
              border: "none",
              borderRadius: "50%",
              width: 30,
              height: 30,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: audioOn ? "#1a1100" : "var(--wai-gold-light)",
            }}
          >
            {audioOn ? <Volume2 style={{ width: 14, height: 14 }} /> : <VolumeX style={{ width: 14, height: 14 }} />}
          </button>
          <button onClick={() => { setOpen(false); stopAudio(); }} aria-label="Close" style={{ color: "var(--wai-gold-light)" }}>
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ color: "var(--wai-text)" }}>
        {messages.length === 0 && (
          <div className="text-sm" style={{ color: "var(--wai-muted)" }}>
            Your sovereign self — booking, revenue, and counsel. Speak, and he answers.
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
                <button
                  onClick={() => speak(m.text)}
                  title="Read aloud"
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, opacity: 0.5, marginLeft: 6, padding: 0, verticalAlign: "middle" }}
                >
                  🔊
                </button>
              )}
            </div>
          </div>
        ))}
        {sending && <div className="text-xs" style={{ color: "var(--wai-muted)" }}>The Sovereign is considering…</div>}
      </div>

      {/* Input bar */}
      <form onSubmit={send} className="p-3 flex gap-2" style={{ borderTop: "1px solid var(--wai-border)" }}>
        {/* Mic button */}
        <button
          type="button"
          onClick={toggleMic}
          title={recording ? "Stop dictation" : "Voice input"}
          aria-label={recording ? "Stop dictation" : "Dictate message"}
          style={{
            background: recording ? "#dc2626" : "rgba(255,255,255,0.1)",
            border: "none",
            borderRadius: 8,
            padding: "0 10px",
            cursor: "pointer",
            color: recording ? "#fff" : "var(--wai-gold-light)",
            flexShrink: 0,
          }}
        >
          {recording
            ? <MicOff style={{ width: 15, height: 15 }} />
            : <Mic    style={{ width: 15, height: 15 }} />}
        </button>

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={recording ? "Listening…" : "Ask The Sovereign…"}
          data-testid="sovereign-input"
          style={{ background: "var(--wai-dark)", color: "var(--wai-text)", border: "1px solid var(--wai-border)", borderRadius: 8, padding: "0.5rem 0.75rem", flex: 1 }}
        />
        <button
          type="submit"
          disabled={sending}
          data-testid="sovereign-send"
          className="px-3 rounded-lg font-bold disabled:opacity-50"
          style={{ background: "var(--wai-gold)", color: "#1a1100" }}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
