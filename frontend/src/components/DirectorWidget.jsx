import { useState, useEffect, useRef, useCallback } from "react";
import { api, API } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

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

const SpeechRecognitionImpl = typeof window !== "undefined"
  ? (window.SpeechRecognition || window.webkitSpeechRecognition)
  : null;

const QUICK_ACTIONS = {
  student: [
    { label: "My Progress", msg: "Show me a summary of my learning progress and what I should focus on next." },
    { label: "Help Me Study", msg: "I need help studying. What resources are available to me?" },
    { label: "Find a Course", msg: "What courses are available and which should I take next?" },
  ],
  instructor: [
    { label: "My Students", msg: "Give me a summary of my students and their progress." },
    { label: "Lab Approvals", msg: "Are there any lab submissions pending my review?" },
    { label: "Course Help", msg: "Help me with course and curriculum management." },
  ],
  admin: [
    { label: "System Status", msg: "Give me a quick system status report for WAI-Institute." },
    { label: "Threat Report", msg: "Are there any active threats or incidents I should know about?" },
    { label: "Generate Brief", msg: "Generate an executive brief on current institute operations." },
    { label: "Legal Strategy", msg: "What legal risks or considerations require my attention?" },
  ],
  executive_admin: [
    { label: "System Status", msg: "Give me a full system status and security posture report." },
    { label: "Threat Report", msg: "Are there any active threats or incidents I should know about?" },
    { label: "Generate Brief", msg: "Generate an executive brief on current institute operations." },
    { label: "Legal Strategy", msg: "What legal risks or considerations require my attention?" },
  ],
};

const POLL_INTERVAL = 90_000;

const HEALTH_COLORS = {
  nominal:  "#4CAF50",
  warning:  "#C9A84C",
  critical: "#E53935",
};

// Pixel widths for each size mode (used for position clamping on resize)
const SIZE_PX = { normal: 380, expanded: 580, fullscreen: () => Math.round(window.innerWidth * 0.9) };

// CSS widths
const SIZE_WIDTH = { normal: "380px", expanded: "580px", fullscreen: "min(90vw, 900px)" };

function getDefaultPos() {
  return {
    x: Math.max(0, window.innerWidth - 404),
    y: Math.max(0, window.innerHeight - 540),
  };
}

function buildAlertMessage(pulse, prev) {
  const lines = [];

  if (prev) {
    const m = pulse.metrics;
    const p = prev.metrics;
    if (m.incidents_open > p.incidents_open)
      lines.push(`⚠ ${m.incidents_open - p.incidents_open} new incident(s) opened.`);
    if (m.at_risk_login > p.at_risk_login)
      lines.push(`⚠ ${m.at_risk_login - p.at_risk_login} additional student(s) inactive 7+ days.`);
    if (m.at_risk_quiz > p.at_risk_quiz)
      lines.push(`⚠ ${m.at_risk_quiz - p.at_risk_quiz} additional student(s) struggling with quizzes.`);
    if (m.more_flags_pending > p.more_flags_pending)
      lines.push(`⚠ ${m.more_flags_pending - p.more_flags_pending} new M.O.R.E. content flag(s) require review.`);
    if (m.failed_payments_24h > p.failed_payments_24h)
      lines.push(`⚠ ${m.failed_payments_24h - p.failed_payments_24h} new payment failure(s) detected.`);
    if (m.new_users_24h > p.new_users_24h)
      lines.push(`ℹ ${m.new_users_24h - p.new_users_24h} new user registration(s) in the last 24h.`);
    if (m.pending_labs > p.pending_labs)
      lines.push(`ℹ ${m.pending_labs - p.pending_labs} additional lab submission(s) awaiting review.`);
  } else {
    if (pulse.alerts.length === 0) {
      lines.push("✓ All systems nominal. No action required at this time.");
    } else {
      lines.push("Initial monitoring scan complete:");
      pulse.alerts.forEach(a => lines.push(`${a.level === "high" ? "⚠" : a.level === "warn" ? "⚡" : "ℹ"} ${a.msg}`));
    }
    if (pulse.recent_incidents?.length) {
      lines.push(`\nOpen incidents:`);
      pulse.recent_incidents.forEach(i => lines.push(`  · ${i.title || "Untitled"}`));
    }
  }

  return lines.length ? lines.join("\n") : null;
}

export default function DirectorWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [persona, setPersona] = useState("assistant_director");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [audioOn, setAudioOn] = useState(true);
  const [recording, setRecording] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Passive monitoring state
  const [pulse, setPulse] = useState(null);
  const [unread, setUnread] = useState(0);
  const prevPulseRef = useRef(null);
  const pollTimerRef = useRef(null);

  // ── Position & size ────────────────────────────────────────────────────────

  const [pos, setPos] = useState(() => {
    try {
      const saved = localStorage.getItem("director_widget_pos");
      if (saved) return JSON.parse(saved);
    } catch {}
    return getDefaultPos();
  });
  const [widgetSize, setWidgetSize] = useState("normal");

  const widgetRef = useRef(null);
  const dragging = useRef(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const hasDragged = useRef(false);
  // Mirror pos into a ref so mousemove/mouseup closures always see the latest value
  const posRef = useRef(pos);
  useEffect(() => { posRef.current = pos; }, [pos]);

  // Clamp position when size changes so the widget stays on screen
  useEffect(() => {
    const w = typeof SIZE_PX[widgetSize] === "function" ? SIZE_PX[widgetSize]() : SIZE_PX[widgetSize];
    setPos(p => ({
      x: Math.max(0, Math.min(window.innerWidth - w, p.x)),
      y: Math.max(0, Math.min(window.innerHeight - 50, p.y)),
    }));
  }, [widgetSize]);

  const onHeaderMouseDown = useCallback((e) => {
    // Only drag on primary button; controls stop propagation themselves
    if (e.button !== 0) return;
    dragging.current = true;
    hasDragged.current = false;
    const rect = widgetRef.current.getBoundingClientRect();
    dragOffset.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    e.preventDefault();
  }, []);

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      hasDragged.current = true;
      const w = widgetRef.current?.offsetWidth || 380;
      const newX = Math.max(0, Math.min(window.innerWidth - w, e.clientX - dragOffset.current.x));
      const newY = Math.max(0, Math.min(window.innerHeight - 50, e.clientY - dragOffset.current.y));
      setPos({ x: newX, y: newY });
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      try { localStorage.setItem("director_widget_pos", JSON.stringify(posRef.current)); } catch {}
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const cycleSize = useCallback((e) => {
    e.stopPropagation();
    setWidgetSize(s => s === "normal" ? "expanded" : s === "expanded" ? "fullscreen" : "normal");
  }, []);

  // ── Other refs ─────────────────────────────────────────────────────────────

  const bottomRef = useRef(null);
  const isMonitor = user?.role === "admin" || user?.role === "executive_admin";

  // ── Greeting + initial pulse ───────────────────────────────────────────────

  useEffect(() => {
    if (!user) { setOpen(false); setMsgs([]); setPulse(null); return; }
    const isExec = user.role === "admin" || user.role === "executive_admin";
    setPersona(isExec ? "director" : "assistant_director");
    const fallback = isExec
      ? `Welcome back, ${user.full_name}. I am The Director. Initiating monitoring scan…`
      : `Welcome back, ${user.full_name}. I am the Assistant Director. How can I guide you today?`;
    setMsgs([{ role: "assistant", text: fallback }]);
    setOpen(true);

    api.get("/ai/director/greeting")
      .then(r => {
        setPersona(r.data.persona);
        setMsgs([{ role: "assistant", text: r.data.greeting }]);
      })
      .catch(() => {});
  }, [user]);

  // ── Passive monitoring poll ────────────────────────────────────────────────

  const poll = useCallback(async () => {
    if (!isMonitor) return;
    try {
      const { data } = await api.get("/ai/director/pulse");
      const prev = prevPulseRef.current;
      const alertMsg = buildAlertMessage(data, prev);

      setPulse(data);
      prevPulseRef.current = data;

      if (alertMsg) {
        setMsgs(m => [...m, {
          role: "assistant",
          text: alertMsg,
          isAlert: true,
          health: data.health,
          pulse: data,
        }]);
        if (minimized) setUnread(u => u + 1);
      }
    } catch {
      // Silent failure
    }
  }, [isMonitor, minimized]);

  useEffect(() => {
    if (!isMonitor) return;
    poll();
    pollTimerRef.current = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(pollTimerRef.current);
  }, [isMonitor, poll]);

  useEffect(() => {
    if (!minimized) setUnread(0);
  }, [minimized]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  // ── TTS ───────────────────────────────────────────────────────────────────

  const speak = async (text) => {
    if (!audioOn) return;
    try {
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${API}/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ text, voice: persona === "director" ? "onyx" : "nova", speed: 1.0, session_id: "director" }),
      });
      if (!r.ok) return;
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play();
    } catch {}
  };

  // ── STT ───────────────────────────────────────────────────────────────────

  const toggleMic = () => {
    if (!SpeechRecognitionImpl) return;
    if (recording) { setRecording(false); return; }
    const rec = new SpeechRecognitionImpl();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = ev => {
      const txt = ev.results?.[0]?.[0]?.transcript?.trim();
      if (txt) setInput(cur => cur ? `${cur} ${txt}` : txt);
    };
    rec.onerror = () => setRecording(false);
    rec.onend = () => setRecording(false);
    rec.start();
    setRecording(true);
  };

  // ── File upload ───────────────────────────────────────────────────────────

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      toast.error("File too large. Maximum size is 5 MB.");
      return;
    }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${API}/ai/director/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Upload failed");
      setAttachedFile({ file_id: data.file_id, filename: data.filename });
      setMsgs(m => [...m, {
        role: "assistant",
        text: `📎 File received: ${data.filename}\nUse it in your next message — I'll read it automatically.`,
      }]);
    } catch (err) {
      toast.error(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // ── Send ──────────────────────────────────────────────────────────────────

  const send = async (overrideMsg) => {
    const userMsg = (overrideMsg || input).trim();
    if (!userMsg || loading) return;
    setInput("");

    const displayMsg = attachedFile
      ? `${userMsg}\n[Attached: ${attachedFile.filename}]`
      : userMsg;

    setMsgs(m => [...m, { role: "user", text: displayMsg }]);
    setLoading(true);

    const payload = {
      message: attachedFile
        ? `${userMsg}\n\n[ATTACHED FILE — use read_file tool with file_id: ${attachedFile.file_id}]`
        : userMsg,
      session_id: "director_session",
    };
    setAttachedFile(null);

    try {
      const r = await api.post("/ai/director", payload);
      setMsgs(m => [...m, { role: "assistant", text: r.data.reply }]);
      speak(r.data.reply);
      setPersona(r.data.persona);
    } catch {
      setMsgs(m => [...m, { role: "assistant", text: "I am temporarily unavailable. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  const quickActions = QUICK_ACTIONS[user?.role] || QUICK_ACTIONS.student;
  const style = PERSONA_STYLES[persona];
  const healthColor = pulse ? HEALTH_COLORS[pulse.health] : style.color;

  // Dynamic message area height based on size + monitor bar presence
  const msgHeights = {
    normal:     isMonitor && pulse ? "180px" : "200px",
    expanded:   isMonitor && pulse ? "300px" : "320px",
    fullscreen: isMonitor && pulse ? "440px" : "460px",
  };

  if (!open) return null;

  return (
    <div
      ref={widgetRef}
      style={{
        position: "fixed",
        left: `${pos.x}px`,
        top: `${pos.y}px`,
        width: minimized ? "220px" : SIZE_WIDTH[widgetSize],
        zIndex: 1000,
        fontFamily: "inherit",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        border: `1px solid ${style.color}40`,
        borderRadius: "4px",
        overflow: "hidden",
        transition: "width 0.15s ease",
      }}
    >
      {/* Header — drag zone */}
      <div
        onMouseDown={onHeaderMouseDown}
        onClick={() => { if (!hasDragged.current) setMinimized(m => !m); }}
        style={{
          background: style.bg,
          color: style.color,
          padding: "10px 14px",
          cursor: dragging.current ? "grabbing" : "grab",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          userSelect: "none",
        }}
      >
        {/* Title + health dot */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {isMonitor && (
            <span style={{
              width: "8px", height: "8px", borderRadius: "50%",
              background: healthColor,
              display: "inline-block",
              boxShadow: pulse?.health !== "nominal" ? `0 0 6px ${healthColor}` : "none",
              animation: pulse?.health !== "nominal" ? "pulse-dot 1.5s infinite" : "none",
            }} title={pulse ? `System: ${pulse.health}` : "Monitoring…"} />
          )}
          <div>
            <div style={{ fontSize: "10px", letterSpacing: "2px", fontWeight: "700" }}>
              {style.title}
            </div>
            <div style={{ fontSize: "9px", opacity: 0.7, letterSpacing: "1px" }}>
              {pulse && isMonitor
                ? `${pulse.health.toUpperCase()} · ${pulse.alerts.length} alert${pulse.alerts.length !== 1 ? "s" : ""}`
                : style.subtitle}
            </div>
          </div>
        </div>

        {/* Controls — stop mousedown propagation so they don't start a drag */}
        <div
          onMouseDown={e => e.stopPropagation()}
          style={{ display: "flex", gap: "8px", alignItems: "center" }}
        >
          {/* Unread badge */}
          {unread > 0 && minimized && (
            <span style={{
              background: "#E53935", color: "#fff",
              borderRadius: "50%", width: "16px", height: "16px",
              fontSize: "9px", fontWeight: "900",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>{unread > 9 ? "9+" : unread}</span>
          )}

          {/* Expand/shrink button */}
          {!minimized && (
            <span
              onClick={cycleSize}
              title={widgetSize === "fullscreen" ? "Shrink" : widgetSize === "expanded" ? "Fullscreen" : "Expand"}
              style={{
                fontSize: "13px", opacity: 0.7, cursor: "pointer",
                lineHeight: 1, padding: "2px",
              }}
            >
              {widgetSize === "fullscreen" ? "⊟" : "⊞"}
            </span>
          )}

          <span style={{ fontSize: "12px", opacity: 0.7 }}>{minimized ? "▲" : "▼"}</span>
          <span
            onClick={e => { e.stopPropagation(); setOpen(false); }}
            style={{ fontSize: "14px", opacity: 0.7, cursor: "pointer" }}
          >
            ✕
          </span>
        </div>
      </div>

      {!minimized && (
        <>
          {/* Live metrics bar (admin/exec only) */}
          {isMonitor && pulse && (
            <div style={{
              background: "#0A0A0A", borderBottom: `1px solid ${style.color}20`,
              padding: "6px 10px", display: "flex", gap: "10px", flexWrap: "wrap",
            }}>
              {[
                { label: "INCIDENTS", val: pulse.metrics.incidents_open, warn: pulse.metrics.incidents_open > 0 },
                { label: "AT RISK", val: pulse.metrics.at_risk_login + pulse.metrics.at_risk_quiz, warn: (pulse.metrics.at_risk_login + pulse.metrics.at_risk_quiz) > 0 },
                { label: "LABS PENDING", val: pulse.metrics.pending_labs, warn: pulse.metrics.pending_labs > 0 },
                { label: "USERS", val: pulse.metrics.total_users },
                { label: "NEW TODAY", val: pulse.metrics.new_users_24h },
              ].map(item => (
                <div key={item.label} style={{ textAlign: "center", minWidth: "48px" }}>
                  <div style={{
                    fontSize: "13px", fontWeight: "900", fontFamily: "monospace",
                    color: item.warn ? HEALTH_COLORS.warning : "#AAA",
                  }}>{item.val}</div>
                  <div style={{ fontSize: "7px", color: "#555", letterSpacing: "0.5px" }}>{item.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Messages */}
          <div style={{
            background: "#0D0D0D",
            height: msgHeights[widgetSize],
            overflowY: "auto",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            transition: "height 0.15s ease",
          }}>
            {msgs.map((m, i) => (
              <div key={i}>
                <div style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "90%",
                  background: m.isAlert
                    ? (m.health === "critical" ? "#2A0A0A" : m.health === "warning" ? "#1A1500" : "#0A1A0A")
                    : m.role === "user" ? style.color + "20" : "#1A1A1A",
                  border: `1px solid ${m.isAlert
                    ? HEALTH_COLORS[m.health] + "60"
                    : m.role === "user" ? style.color + "40" : "#333"}`,
                  borderLeft: m.isAlert ? `3px solid ${HEALTH_COLORS[m.health]}` : undefined,
                  borderRadius: "4px", padding: "8px 10px",
                  fontSize: "11.5px", color: "#E8E8E8", lineHeight: "1.6",
                  whiteSpace: "pre-wrap",
                }}>
                  {m.isAlert && (
                    <div style={{ fontSize: "8px", color: HEALTH_COLORS[m.health], letterSpacing: "1px", fontWeight: "900", marginBottom: "4px" }}>
                      ◉ DIRECTOR MONITORING ALERT
                    </div>
                  )}
                  {m.text}
                </div>
                {m.isAlert && m.pulse?.alerts?.length > 0 && (
                  <div style={{ marginTop: "4px", display: "flex", gap: "4px" }}>
                    <button
                      onClick={() => send(`Brief me on the current alerts: ${m.pulse.alerts.map(a => a.msg).join("; ")}`)}
                      style={{
                        background: "transparent", border: `1px solid ${style.color}40`,
                        color: style.color, padding: "2px 8px", fontSize: "9px",
                        cursor: "pointer", borderRadius: "2px", letterSpacing: "0.5px",
                      }}
                    >
                      Brief me →
                    </button>
                    <button
                      onClick={() => send(`What actions should I take immediately given: ${m.pulse.alerts.map(a => a.msg).join("; ")}`)}
                      style={{
                        background: "transparent", border: `1px solid ${style.color}30`,
                        color: style.color + "90", padding: "2px 8px", fontSize: "9px",
                        cursor: "pointer", borderRadius: "2px", letterSpacing: "0.5px",
                      }}
                    >
                      Action plan →
                    </button>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: "flex-start", color: style.color, fontSize: "11px", padding: "4px 8px" }}>
                Processing…
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick actions */}
          <div style={{
            background: "#0D0D0D", borderTop: `1px solid ${style.color}20`,
            padding: "6px 8px", display: "flex", gap: "4px", flexWrap: "wrap",
          }}>
            {quickActions.map(action => (
              <button key={action.label} onClick={() => setInput(action.msg)} style={{
                background: "transparent", border: `1px solid ${style.color}40`,
                color: style.color, padding: "3px 8px",
                fontSize: "10px", cursor: "pointer",
                borderRadius: "2px", letterSpacing: "0.5px",
              }}>
                {action.label}
              </button>
            ))}
            {isMonitor && (
              <button onClick={poll} style={{
                background: "transparent", border: `1px solid #444`,
                color: "#666", padding: "3px 8px",
                fontSize: "10px", cursor: "pointer",
                borderRadius: "2px", letterSpacing: "0.5px",
                marginLeft: "auto",
              }} title="Force a monitoring scan now">
                ↺ Scan
              </button>
            )}
          </div>

          {/* Input */}
          <div style={{
            background: "#111", borderTop: `1px solid ${style.color}30`,
            padding: "8px", display: "flex", gap: "6px", alignItems: "center",
          }}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.json,.csv,.py,.js,.jsx,.ts,.tsx,.html,.xml,.yaml,.yml,.log,.pdf"
              style={{ display: "none" }}
              onChange={handleFileSelect}
            />
            <button onClick={toggleMic} style={{
              background: recording ? style.color : "#1A1A1A",
              border: `1px solid ${style.color}30`,
              color: recording ? "#000" : style.color,
              padding: "6px 8px", fontSize: "14px", cursor: "pointer", borderRadius: "2px",
            }} title={recording ? "Stop" : "Mic"}>
              {recording ? "⏹" : "🎤"}
            </button>
            <button onClick={() => setAudioOn(!audioOn)} style={{
              background: audioOn ? style.color : "#1A1A1A",
              border: `1px solid ${style.color}30`,
              color: audioOn ? "#000" : style.color,
              padding: "6px 8px", fontSize: "14px", cursor: "pointer", borderRadius: "2px",
            }} title={audioOn ? "Voice ON" : "Voice OFF"}>
              {audioOn ? "🔊" : "🔇"}
            </button>
            {isMonitor && (
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                style={{
                  background: attachedFile ? style.color : "#1A1A1A",
                  border: `1px solid ${style.color}30`,
                  color: attachedFile ? "#000" : style.color,
                  padding: "6px 8px", fontSize: "14px", cursor: "pointer", borderRadius: "2px",
                  opacity: uploading ? 0.5 : 1,
                }}
                title={attachedFile ? `Attached: ${attachedFile.filename}` : "Attach file"}
              >
                {uploading ? "⏳" : attachedFile ? "📎" : "📂"}
              </button>
            )}
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send()}
              placeholder={attachedFile ? `File attached — add a message…` : "Ask The Director..."}
              style={{
                flex: 1, background: "#1A1A1A", border: `1px solid ${style.color}30`,
                color: "#E8E8E8", padding: "6px 10px", fontSize: "12px",
                borderRadius: "2px", outline: "none",
              }}
            />
            <button onClick={() => send()} disabled={loading} style={{
              background: style.color, color: "#000",
              border: "none", padding: "6px 12px",
              fontSize: "11px", fontWeight: "700",
              cursor: "pointer", borderRadius: "2px", letterSpacing: "1px",
            }}>
              SEND
            </button>
          </div>
        </>
      )}

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
