import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

const PERSONA_STYLES = {
  director: {
    title: "THE DIRECTOR",
    subtitle: "Executive Intelligence",
    color: "#C9A84C",
    bg: "#0A0F1E",
  },
  assistant_director: {
    title: "ASSISTANT DIRECTOR",
    subtitle: "Your Institute Guide",
    color: "#4C9AC9",
    bg: "#0A1A2E",
  },
};

export default function DirectorWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [persona, setPersona] = useState("assistant_director");
  const [greeting, setGreeting] = useState("");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
      setOpen(false);
      setMsgs([]);
      return;
    }
    const isExec = user.role === "admin" || user.role === "executive_admin";
    const defaultPersona = isExec ? "director" : "assistant_director";
    const defaultGreeting = isExec
      ? `Welcome back, ${user.full_name || user.email}. I am The Director. All systems are active. What requires your attention?`
      : `Welcome back, ${user.full_name || user.email}. I am the Assistant Director. How can I guide you today?`;
    setPersona(defaultPersona);
    setMsgs([{ role: "assistant", text: defaultGreeting }]);
    setOpen(true);
    api.get("/ai/director/greeting")
      .then((r) => {
        setPersona(r.data.persona);
        setMsgs([{ role: "assistant", text: r.data.greeting }]);
      })
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);


  const SpeechRecognitionImpl = typeof window !== "undefined"
    ? (window.SpeechRecognition || window.webkitSpeechRecognition)
    : null;

  const speak = async (text) => {
    if (!audioOn) return;
    try {
      const { API } = await import("../lib/api");
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${API}/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ text, voice: "onyx", speed: 1.0, session_id: "director" }),
      });
      if (!r.ok) return;
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play();
    } catch {}
  };

  const toggleMic = () => {
    if (!SpeechRecognitionImpl) return;
    if (recording) {
      setRecording(false);
      return;
    }
    const rec = new SpeechRecognitionImpl();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (ev) => {
      const txt = ev.results?.[0]?.[0]?.transcript?.trim();
      if (txt) setInput((cur) => cur ? `${cur} ${txt}` : txt);
    };
    rec.onerror = () => setRecording(false);
    rec.onend = () => setRecording(false);
    rec.start();
    setRecording(true);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: userMsg }]);
    setLoading(true);
    try {
      const r = await api.post("/ai/director", {
        message: userMsg,
        session_id: "director_session",
      });
      setMsgs((m) => [...m, { role: "assistant", text: r.data.reply }]);
      speak(r.data.reply);
      setPersona(r.data.persona);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", text: "I am temporarily unavailable. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const style = PERSONA_STYLES[persona];

  if (!open) return null;

  return (
    <div style={{
      position: "fixed", bottom: "24px", right: "24px",
      width: minimized ? "220px" : "360px",
      zIndex: 1000, fontFamily: "inherit",
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      border: `1px solid ${style.color}40`,
      borderRadius: "4px", overflow: "hidden",
    }}>
      {/* Header */}
      <div
        onClick={() => setMinimized(!minimized)}
        style={{
          background: style.bg, color: style.color,
          padding: "10px 14px", cursor: "pointer",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "10px", letterSpacing: "2px", fontWeight: "700" }}>
            {style.title}
          </div>
          <div style={{ fontSize: "9px", opacity: 0.7, letterSpacing: "1px" }}>
            {style.subtitle}
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span onClick={(e) => { e.stopPropagation(); setAudioOn(!audioOn); }} style={{ fontSize: "12px", opacity: audioOn ? 1 : 0.4, cursor: "pointer" }} title={audioOn ? "Voice ON" : "Voice OFF"}>🔊</span>
          <span style={{ fontSize: "12px", opacity: 0.7 }}>{minimized ? "▲" : "▼"}</span>
          <span
            onClick={(e) => { e.stopPropagation(); setOpen(false); }}
            style={{ fontSize: "14px", opacity: 0.7, cursor: "pointer" }}
          >✕</span>
        </div>
      </div>

      {/* Body */}
      {!minimized && (
        <>
          <div style={{
            background: "#0D0D0D", height: "240px",
            overflowY: "auto", padding: "12px",
            display: "flex", flexDirection: "column", gap: "8px",
          }}>
            {msgs.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "85%",
                background: m.role === "user" ? style.color + "20" : "#1A1A1A",
                border: `1px solid ${m.role === "user" ? style.color + "40" : "#333"}`,
                borderRadius: "4px", padding: "8px 10px",
                fontSize: "12px", color: "#E8E8E8", lineHeight: "1.5",
              }}>
                {m.text}
              </div>
            ))}
            {loading && (
              <div style={{
                alignSelf: "flex-start", color: style.color,
                fontSize: "11px", padding: "4px 8px",
              }}>
                Processing...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{
            background: "#111", borderTop: `1px solid ${style.color}30`,
            padding: "8px", display: "flex", gap: "6px", alignItems: "center",
          }}>
            <button
              onClick={toggleMic}
              style={{
                background: recording ? style.color : "#1A1A1A",
                border: `1px solid ${style.color}30`,
                color: recording ? "#000" : style.color,
                padding: "6px 8px", fontSize: "14px",
                cursor: "pointer", borderRadius: "2px",
              }}
              title={recording ? "Stop listening" : "Start listening"}
            >
              {recording ? "⏹" : "🎤"}
            </button>
            <button
              onClick={() => setAudioOn(!audioOn)}
              style={{
                background: audioOn ? style.color : "#1A1A1A",
                border: `1px solid ${style.color}30`,
                color: audioOn ? "#000" : style.color,
                padding: "6px 8px", fontSize: "14px",
                cursor: "pointer", borderRadius: "2px",
              }}
              title={audioOn ? "Voice ON" : "Voice OFF"}
            >
              {audioOn ? "🔊" : "🔇"}
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask The Director..."
              style={{
                flex: 1, background: "#1A1A1A", border: `1px solid ${style.color}30`,
                color: "#E8E8E8", padding: "6px 10px", fontSize: "12px",
                borderRadius: "2px", outline: "none",
              }}
            />
            <button
              onClick={send}
              disabled={loading}
              style={{
                background: style.color, color: "#000",
                border: "none", padding: "6px 12px",
                fontSize: "11px", fontWeight: "700",
                cursor: "pointer", borderRadius: "2px",
                letterSpacing: "1px",
              }}
            >
              SEND
            </button>
          </div>
        </>
      )}
    </div>
  );
}