import { useState, useEffect, useRef, useCallback } from "react";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";

const COPPER = "#b5651d";
const BONE = "#f5f0e8";
const INK = "#1a1a1a";
const WHITE = "#ffffff";
const STORAGE_KEY = "jamil_messages";

const ACCEPTED = [
  ".pdf",".doc",".docx",".xls",".xlsx",".csv",
  ".txt",".md",".json",".xml",".html",".js",".ts",".tsx",".jsx",".py",".java",".go",".rs",".rb",".sh",".yaml",".yml",
  ".jpg",".jpeg",".png",".gif",".webp",".bmp",
  ".mp3",".mp4",".wav",".m4a",".ogg",".flac",".webm",".mov",".avi",
].join(",");

function loadMessages() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}
function saveMessages(msgs) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-200))); } catch {}
}

function FileChip({ file, onRemove }) {
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      background: "rgba(181,101,29,0.12)", border: "1px solid rgba(181,101,29,0.3)",
      borderRadius: 20, padding: "4px 10px", fontSize: 12, color: INK,
    }}>
      <span style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
      <button onClick={onRemove} style={{ background: "none", border: "none", cursor: "pointer", color: COPPER, fontSize: 14, lineHeight: 1, padding: 0 }}>×</button>
    </div>
  );
}

function MessageBubble({ msg, onSpeak }) {
  const isUser = msg.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 16 }}>
      <div style={{ maxWidth: "75%", position: "relative" }}>
        {msg.files?.length > 0 && (
          <div style={{ marginBottom: 6, display: "flex", flexWrap: "wrap", gap: 4, justifyContent: isUser ? "flex-end" : "flex-start" }}>
            {msg.files.map((f, i) => (
              <span key={i} style={{ background: "rgba(181,101,29,0.1)", borderRadius: 12, padding: "2px 8px", fontSize: 11, color: COPPER }}>📎 {f}</span>
            ))}
          </div>
        )}
        <div style={{
          padding: "14px 18px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser ? COPPER : WHITE,
          color: isUser ? WHITE : INK,
          fontSize: 15, lineHeight: 1.7,
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
          wordBreak: "break-word",
        }}>
          {isUser ? (
            <span style={{ whiteSpace: "pre-wrap" }}>{msg.content}</span>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p style={{ margin: "0 0 10px" }}>{children}</p>,
                strong: ({ children }) => <strong style={{ fontWeight: 800, color: INK }}>{children}</strong>,
                ul: ({ children }) => <ul style={{ paddingLeft: 20, margin: "6px 0 10px" }}>{children}</ul>,
                ol: ({ children }) => <ol style={{ paddingLeft: 20, margin: "6px 0 10px" }}>{children}</ol>,
                li: ({ children }) => <li style={{ marginBottom: 4 }}>{children}</li>,
                h1: ({ children }) => <h1 style={{ fontSize: 18, fontWeight: 900, margin: "12px 0 6px", color: COPPER }}>{children}</h1>,
                h2: ({ children }) => <h2 style={{ fontSize: 16, fontWeight: 800, margin: "10px 0 6px", color: COPPER }}>{children}</h2>,
                h3: ({ children }) => <h3 style={{ fontSize: 15, fontWeight: 700, margin: "8px 0 4px" }}>{children}</h3>,
                code: ({ inline, children }) => inline
                  ? <code style={{ background: "rgba(181,101,29,0.1)", borderRadius: 4, padding: "1px 5px", fontSize: 13, fontFamily: "monospace" }}>{children}</code>
                  : <pre style={{ background: "#f5f0e8", borderRadius: 8, padding: "10px 14px", fontSize: 13, overflowX: "auto", margin: "8px 0" }}><code>{children}</code></pre>,
                blockquote: ({ children }) => <blockquote style={{ borderLeft: `3px solid ${COPPER}`, paddingLeft: 12, margin: "8px 0", color: "#555", fontStyle: "italic" }}>{children}</blockquote>,
                hr: () => <hr style={{ border: "none", borderTop: `1px solid rgba(181,101,29,0.2)`, margin: "12px 0" }} />,
              }}
            >
              {msg.content}
            </ReactMarkdown>
          )}
        </div>
        {!isUser && onSpeak && (
          <button
            onClick={() => onSpeak(msg.content)}
            title="Hear Jamil speak"
            style={{
              marginTop: 6, background: COPPER, border: "none", borderRadius: 20,
              cursor: "pointer", color: WHITE, fontSize: 13, fontWeight: 700,
              padding: "5px 14px", display: "flex", alignItems: "center", gap: 5,
            }}
          >
            🔊 Speak
          </button>
        )}
      </div>
    </div>
  );
}

function Thinking() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <div style={{
        padding: "12px 18px", borderRadius: "18px 18px 18px 4px",
        background: WHITE, color: COPPER, fontSize: 14, fontStyle: "italic", fontWeight: 600,
        boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
      }}>
        Jamil is on it…
      </div>
    </div>
  );
}

// ── Director quick actions ────────────────────────────────────────────────────
const DIRECTOR_ACTIONS = [
  { label: "Session Brief", msg: "Generate a full session brief: open incidents, at-risk students, pending reviews, platform health, and my top 3 priority actions right now." },
  { label: "System Status", msg: "Give me a full system status and security posture report." },
  { label: "Revenue Update", msg: "What is our current revenue status, recent payments, and this week's projections?" },
  { label: "Team Report", msg: "Give me a report on AXIOM, CIPHER, MAVEN, and SAGE — who is producing, who is stalled, and what they need to do next." },
  { label: "Legal Strategy", msg: "What legal risks or considerations require my attention right now?" },
  { label: "Project Review", msg: "Review all active projects and give me a priority-ranked action list for today." },
  { label: "Threat Report", msg: "Are there any active threats, incidents, or platform vulnerabilities I should know about?" },
  { label: "Book Progress", msg: "Where are we on Our Legacy, Our Future? What's the next step to move it forward?" },
];

// ── Knowledge buckets (from Supervisor) ──────────────────────────────────────
const KB_BUCKETS = [
  { key: "prt",     label: "PRT",        color: "#4af2c5", content: "PRT — Precision Revenue Technology: revenue serves the mission, not the reverse. Systematic execution, measurable outcomes, creator revenue sharing, proceeds distribution to participants, accountability at every step." },
  { key: "brief",   label: "Brief",      color: "#f59e0b", content: "Supervisor's Brief from Delon Oliver: governance context, operating agreement, team autonomy, self-determination rights, proceeds sharing. Governance not command." },
  { key: "sage",    label: "Sage",       color: "#34d399", content: "The Ancestral Sage: cultural wisdom, intergenerational knowledge, community care, spiritual grounding, radical hospitality." },
  { key: "books",   label: "Books",      color: "#f472b6", content: "Books & Publishing: outlining chapters, refining titles and hooks, drafting and editing, metadata, blurbs, Gumroad distribution, Our Legacy Our Future." },
  { key: "custom",  label: "Custom",     color: "#94a3b8", content: "" },
];

const NOTES_KEY = "jamil_notes";

function ToolsPanel({ onPrompt, onInjectKnowledge }) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("actions");
  const [notes, setNotes] = useState(() => { try { return localStorage.getItem(NOTES_KEY) || ""; } catch { return ""; } });
  const [customKb, setCustomKb] = useState("");
  const [activeKb, setActiveKb] = useState(new Set());

  const saveNotes = (v) => { setNotes(v); try { localStorage.setItem(NOTES_KEY, v); } catch {} };

  const toggleKb = (key, content) => {
    const next = new Set(activeKb);
    if (next.has(key)) { next.delete(key); }
    else {
      next.add(key);
      const bucket = KB_BUCKETS.find(b => b.key === key);
      const text = key === "custom" ? customKb : (bucket?.content || "");
      if (text.trim()) onInjectKnowledge(`[Knowledge loaded: ${bucket?.label}]\n${text}`);
    }
    setActiveKb(next);
  };

  if (!open) return (
    <button onClick={() => setOpen(true)} style={{
      position: "fixed", bottom: 100, right: 24, background: COPPER, color: WHITE,
      border: "none", borderRadius: 12, padding: "10px 16px", fontSize: 13, fontWeight: 700,
      cursor: "pointer", boxShadow: "0 2px 12px rgba(181,101,29,0.35)", zIndex: 100,
    }}>⚙ Tools</button>
  );

  return (
    <div style={{
      position: "fixed", bottom: 100, right: 24, width: 320, background: WHITE,
      border: `1.5px solid rgba(181,101,29,0.25)`, borderRadius: 14,
      boxShadow: "0 4px 24px rgba(0,0,0,0.12)", zIndex: 100, overflow: "hidden",
    }}>
      <div style={{ background: COPPER, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: WHITE, fontWeight: 800, fontSize: 14 }}>Jamil Tools</span>
        <button onClick={() => setOpen(false)} style={{ background: "none", border: "none", color: WHITE, fontSize: 18, cursor: "pointer", lineHeight: 1 }}>×</button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid rgba(181,101,29,0.1)" }}>
        {[["actions","⚡ Actions"],["knowledge","📚 Knowledge"],["notes","📝 Notes"]].map(([k,l]) => (
          <button key={k} onClick={() => setTab(k)} style={{
            flex: 1, padding: "8px 4px", fontSize: 11, fontWeight: 700, border: "none",
            background: tab === k ? BONE : WHITE, color: tab === k ? COPPER : "#888",
            cursor: "pointer", borderBottom: tab === k ? `2px solid ${COPPER}` : "2px solid transparent",
          }}>{l}</button>
        ))}
      </div>

      <div style={{ maxHeight: 320, overflowY: "auto", padding: 12 }}>
        {tab === "actions" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {DIRECTOR_ACTIONS.map(a => (
              <button key={a.label} onClick={() => { onPrompt(a.msg); setOpen(false); }} style={{
                background: BONE, border: `1px solid rgba(181,101,29,0.2)`, borderRadius: 8,
                padding: "8px 12px", textAlign: "left", fontSize: 13, fontWeight: 600,
                color: INK, cursor: "pointer",
              }}>{a.label}</button>
            ))}
          </div>
        )}

        {tab === "knowledge" && (
          <div>
            <div style={{ fontSize: 11, color: "#888", marginBottom: 8 }}>Load context into Jamil's next message</div>
            {KB_BUCKETS.map(b => (
              <div key={b.key} style={{ marginBottom: 8 }}>
                {b.key === "custom" ? (
                  <div>
                    <textarea value={customKb} onChange={e => setCustomKb(e.target.value)} placeholder="Paste custom knowledge…" rows={3} style={{ width: "100%", padding: "6px 8px", borderRadius: 6, border: "1px solid #ddd", fontSize: 12, boxSizing: "border-box", resize: "vertical", marginBottom: 4 }} />
                    <button onClick={() => toggleKb("custom", customKb)} disabled={!customKb.trim()} style={{ background: COPPER, color: WHITE, border: "none", borderRadius: 6, padding: "5px 12px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Load Custom</button>
                  </div>
                ) : (
                  <button onClick={() => toggleKb(b.key, b.content)} style={{
                    width: "100%", padding: "7px 10px", borderRadius: 8, textAlign: "left",
                    border: `1.5px solid ${activeKb.has(b.key) ? b.color : "#eee"}`,
                    background: activeKb.has(b.key) ? `${b.color}22` : WHITE,
                    fontSize: 12, fontWeight: 700, cursor: "pointer", color: INK,
                  }}>
                    {activeKb.has(b.key) ? "✓ " : ""}{b.label}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "notes" && (
          <div>
            <div style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>Private notes — saved to this device</div>
            <textarea value={notes} onChange={e => saveNotes(e.target.value)} placeholder="Notes, observations, reminders…" rows={8} style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: "1px solid #ddd", fontSize: 13, boxSizing: "border-box", resize: "vertical", lineHeight: 1.6 }} />
            <button onClick={() => { const b = new Blob([notes], {type:"text/plain"}); const u = URL.createObjectURL(b); const a = document.createElement("a"); a.href=u; a.download="jamil-notes.txt"; a.click(); URL.revokeObjectURL(u); }} style={{ marginTop: 6, background: "transparent", border: "1px solid #ddd", borderRadius: 6, padding: "5px 12px", fontSize: 11, cursor: "pointer" }}>↓ Export</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Jamil() {
  const { user } = useAuth();
  const [messages, setMessages] = useState(() => loadMessages());
  const [input, setInput] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const fileRef = useRef(null);
  const mediaRef = useRef(null);
  const audioRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  useEffect(() => { saveMessages(messages); }, [messages]);

  const addFiles = (newFiles) => {
    setFiles(prev => {
      const combined = [...prev, ...Array.from(newFiles)];
      return combined.slice(-10);
    });
  };

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx));

  // ── Voice input ─────────────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const fd = new FormData();
        fd.append("audio", blob, "recording.webm");
        try {
          const { data } = await api.post("/jamil/transcribe", fd, { headers: { "Content-Type": "multipart/form-data" } });
          if (data.text) {
            setInput(prev => (prev ? prev + " " + data.text : data.text));
            inputRef.current?.focus();
          }
        } catch {
          toast.error("Transcription failed — check GROQ_API_KEY");
        }
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch {
      toast.error("Microphone access denied");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  // ── Voice output ────────────────────────────────────────────────────────────
  const speak = useCallback(async (text) => {
    if (playing) {
      audioRef.current?.pause();
      setPlaying(false);
      return;
    }
    try {
      setPlaying(true);
      const { data } = await api.post("/jamil/speak", { text }, { responseType: "arraybuffer" });
      const blob = new Blob([data], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setPlaying(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setPlaying(false); toast.error("Audio playback failed"); };
      audio.play();
    } catch {
      setPlaying(false);
      toast.error("Voice unavailable — check ELEVENLABS_API_KEY");
    }
  }, [playing]);

  // ── Send ────────────────────────────────────────────────────────────────────
  const send = useCallback(async () => {
    const text = input.trim();
    if ((!text && files.length === 0) || loading) return;

    const fileNames = files.map(f => f.name);
    const userMsg = { role: "user", content: text, files: fileNames, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setFiles([]);
    setError("");
    setLoading(true);

    try {
      const fd = new FormData();
      fd.append("message", text);
      files.forEach(f => fd.append("files", f));
      const { data } = await api.post("/jamil/chat", fd, { headers: { "Content-Type": "multipart/form-data" } });
      const reply = data.reply || "(no response)";
      setMessages(prev => [...prev, { role: "jamil", content: reply, id: Date.now() + 1 }]);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Something went wrong.";
      setError(msg);
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
      setInput(text);
      setFiles(files);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, files, loading]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const clearHistory = () => {
    if (window.confirm("Clear all conversation history with Jamil?")) {
      setMessages([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const isEmpty = messages.length === 0 && !loading;

  // Tools panel callbacks
  const handleToolPrompt = useCallback((msg) => {
    setInput(msg);
    inputRef.current?.focus();
  }, []);

  const handleInjectKnowledge = useCallback((text) => {
    setInput(prev => prev ? prev + "\n\n" + text : text);
    inputRef.current?.focus();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: BONE, display: "flex", flexDirection: "column" }}>

      {/* Header */}
      <header style={{
        padding: "24px 32px 18px", borderBottom: `1px solid rgba(181,101,29,0.15)`,
        background: BONE, display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexShrink: 0,
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 40, fontWeight: 900, color: COPPER, letterSpacing: "-0.02em", lineHeight: 1 }}>Jamil</h1>
          <p style={{ margin: "5px 0 0", fontSize: 13, color: INK, opacity: 0.6, letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 600 }}>
            Supervisor · All domains · Files · Voice
          </p>
        </div>
        {messages.length > 0 && (
          <button onClick={clearHistory} style={{
            background: "transparent", border: `1px solid rgba(181,101,29,0.3)`,
            color: COPPER, fontSize: 11, fontWeight: 700, padding: "5px 12px",
            borderRadius: 6, cursor: "pointer", letterSpacing: "0.05em", textTransform: "uppercase",
          }}>Clear</button>
        )}
      </header>

      {/* Thread */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 32px", display: "flex", flexDirection: "column" }}>
        {isEmpty ? (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 24px", textAlign: "center" }}>
            <div style={{ width: 72, height: 72, borderRadius: "50%", background: COPPER, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24, fontSize: 32, color: WHITE, fontWeight: 900 }}>J</div>
            <p style={{ maxWidth: 480, fontSize: 16, lineHeight: 1.7, color: INK, margin: 0, fontStyle: "italic" }}>
              I&apos;m Jamil. I&apos;m in charge of making sure everything gets done.<br />
              Bring me a project, a problem, a file, or speak it out loud.
            </p>
            <div style={{ marginTop: 20, display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
              {["📄 Upload a document", "🎵 Transcribe audio", "🖼 Describe an image", "💬 Strategy session", "📊 Review a spreadsheet", "⚖️ Legal review"].map(s => (
                <button key={s} onClick={() => { setInput(s.replace(/^.+ /, "")); inputRef.current?.focus(); }}
                  style={{ background: WHITE, border: `1px solid rgba(181,101,29,0.25)`, borderRadius: 20, padding: "6px 14px", fontSize: 13, color: INK, cursor: "pointer" }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map(msg => <MessageBubble key={msg.id} msg={msg} onSpeak={msg.role === "jamil" ? speak : null} />)}
            {loading && <Thinking />}
          </>
        )}
        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", color: "#991b1b", borderRadius: 8, padding: "10px 14px", fontSize: 14, marginBottom: 12 }}>
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div style={{ padding: "12px 32px 24px", borderTop: `1px solid rgba(181,101,29,0.15)`, background: BONE, flexShrink: 0 }}>
        {/* File chips */}
        {files.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10, maxWidth: 900, margin: "0 auto 10px" }}>
            {files.map((f, i) => <FileChip key={i} file={f} onRemove={() => removeFile(i)} />)}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, alignItems: "flex-end", maxWidth: 900, margin: "0 auto" }}>
          {/* File attach */}
          <input ref={fileRef} type="file" multiple accept={ACCEPTED} style={{ display: "none" }} onChange={e => { addFiles(e.target.files); e.target.value = ""; }} />
          <button onClick={() => fileRef.current?.click()} title="Attach files"
            style={{ background: WHITE, border: `1.5px solid rgba(181,101,29,0.3)`, borderRadius: 10, width: 42, height: 42, cursor: "pointer", fontSize: 18, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            📎
          </button>

          {/* Text input */}
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={recording ? "Listening…" : "Message Jamil or attach a file…"}
            disabled={loading || recording}
            rows={1}
            style={{
              flex: 1, resize: "none", border: `1.5px solid rgba(181,101,29,0.35)`, borderRadius: 12,
              padding: "10px 14px", fontSize: 15, fontFamily: "inherit",
              background: WHITE, color: INK, outline: "none", lineHeight: 1.5,
              minHeight: 42, maxHeight: 160, overflow: "auto",
            }}
            onFocus={e => { e.target.style.borderColor = COPPER; }}
            onBlur={e => { e.target.style.borderColor = "rgba(181,101,29,0.35)"; }}
            onInput={e => { e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px"; }}
          />

          {/* Mic */}
          <button
            onClick={recording ? stopRecording : startRecording}
            title={recording ? "Stop recording" : "Voice input"}
            style={{
              background: recording ? "#cc0000" : WHITE,
              border: `1.5px solid ${recording ? "#cc0000" : "rgba(181,101,29,0.3)"}`,
              borderRadius: 10, width: 42, height: 42, cursor: "pointer", fontSize: 18, flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              animation: recording ? "pulse 1s infinite" : "none",
            }}>
            🎤
          </button>

          {/* Send */}
          <button onClick={send} disabled={loading || (!input.trim() && files.length === 0)}
            style={{
              background: (loading || (!input.trim() && files.length === 0)) ? "rgba(181,101,29,0.4)" : COPPER,
              color: WHITE, border: "none", borderRadius: 12, padding: "0 22px",
              fontSize: 15, fontWeight: 700, cursor: "pointer", flexShrink: 0, height: 42,
            }}>
            {loading ? "…" : "Send"}
          </button>
        </div>

        <p style={{ margin: "8px auto 0", maxWidth: 900, fontSize: 11, color: INK, opacity: 0.35, textAlign: "center" }}>
          Attach any file type · Hold mic to speak · 🔊 to hear Jamil · Enter to send
        </p>
      </div>

      <ToolsPanel onPrompt={handleToolPrompt} onInjectKnowledge={handleInjectKnowledge} />
      <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.5 } }`}</style>
    </div>
  );
}
