import { useState, useEffect, useRef, useCallback } from "react";
import { api, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

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
          padding: "12px 16px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          background: isUser ? COPPER : WHITE,
          color: isUser ? WHITE : INK,
          fontSize: 15, lineHeight: 1.65,
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
          whiteSpace: "pre-wrap", wordBreak: "break-word",
        }}>
          {msg.content}
        </div>
        {!isUser && onSpeak && (
          <button
            onClick={() => onSpeak(msg.content)}
            title="Hear Jamil speak"
            style={{
              marginTop: 4, background: "none", border: "none", cursor: "pointer",
              color: COPPER, fontSize: 18, padding: "2px 4px", opacity: 0.7,
            }}
          >
            🔊
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

      <style>{`@keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.5 } }`}</style>
    </div>
  );
}
