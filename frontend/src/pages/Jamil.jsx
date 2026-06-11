import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Design tokens ─────────────────────────────────────────────────────────────
const COPPER = "#b5651d";
const BONE = "#f5f0e8";
const INK = "#1a1a1a";
const WHITE = "#ffffff";

// ── Local storage key ─────────────────────────────────────────────────────────
const STORAGE_KEY = "jamil_messages";

function loadMessages() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveMessages(msgs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-200)));
  } catch {
    // storage full — silently ignore
  }
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState() {
  return (
    <div style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "48px 24px",
      textAlign: "center",
    }}>
      <div style={{
        width: 72,
        height: 72,
        borderRadius: "50%",
        background: COPPER,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 24,
        fontSize: 32,
      }}>
        J
      </div>
      <p style={{
        maxWidth: 480,
        fontSize: 16,
        lineHeight: 1.7,
        color: INK,
        margin: 0,
        fontStyle: "italic",
      }}>
        I&apos;m Jamil. Named to carry purpose. Ask me anything — strategy,
        creative, finance, music, legal, wellness, or anything else you need.
      </p>
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 16,
    }}>
      <div style={{
        maxWidth: "72%",
        padding: "12px 16px",
        borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
        background: isUser ? COPPER : WHITE,
        color: isUser ? WHITE : INK,
        fontSize: 15,
        lineHeight: 1.65,
        boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
      }}>
        {msg.content}
      </div>
    </div>
  );
}

// ── Loading indicator ─────────────────────────────────────────────────────────
function Thinking() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <div style={{
        padding: "12px 18px",
        borderRadius: "18px 18px 18px 4px",
        background: WHITE,
        color: COPPER,
        fontSize: 14,
        fontStyle: "italic",
        fontWeight: 600,
        boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
      }}>
        Jamil is working…
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Jamil() {
  const { user } = useAuth();
  const [messages, setMessages] = useState(() => loadMessages());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  // Persist messages to localStorage
  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text, id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const data = await api.post("/jamil/chat", { message: text });
      const reply = data.reply || "(no response)";
      setMessages(prev => [...prev, { role: "jamil", content: reply, id: Date.now() + 1 }]);
    } catch (err) {
      const msg = err?.detail || err?.message || "Something went wrong. Try again.";
      setError(msg);
      // Remove the optimistic user message on failure
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
      setInput(text);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, loading]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const clearHistory = () => {
    if (window.confirm("Clear all conversation history with Jamil?")) {
      setMessages([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: BONE,
      display: "flex",
      flexDirection: "column",
    }}>

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <header style={{
        padding: "28px 32px 20px",
        borderBottom: `1px solid rgba(181,101,29,0.15)`,
        background: BONE,
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "space-between",
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{
            margin: 0,
            fontSize: 42,
            fontWeight: 900,
            color: COPPER,
            letterSpacing: "-0.02em",
            lineHeight: 1,
          }}>
            Jamil
          </h1>
          <p style={{
            margin: "6px 0 0",
            fontSize: 14,
            color: INK,
            opacity: 0.65,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            fontWeight: 600,
          }}>
            Your unified AI — all domains, one voice
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            style={{
              background: "transparent",
              border: `1px solid rgba(181,101,29,0.3)`,
              color: COPPER,
              fontSize: 12,
              fontWeight: 700,
              padding: "6px 14px",
              borderRadius: 6,
              cursor: "pointer",
              letterSpacing: "0.05em",
              textTransform: "uppercase",
            }}
          >
            Clear History
          </button>
        )}
      </header>

      {/* ── Message thread ───────────────────────────────────────────────────── */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "24px 32px",
        display: "flex",
        flexDirection: "column",
      }}>
        {messages.length === 0 && !loading ? (
          <EmptyState />
        ) : (
          <>
            {messages.map(msg => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {loading && <Thinking />}
          </>
        )}
        {error && (
          <div style={{
            background: "#fef2f2",
            border: "1px solid #fca5a5",
            color: "#991b1b",
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 14,
            marginBottom: 12,
          }}>
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input area ───────────────────────────────────────────────────────── */}
      <div style={{
        padding: "16px 32px 24px",
        borderTop: `1px solid rgba(181,101,29,0.15)`,
        background: BONE,
        flexShrink: 0,
      }}>
        <div style={{
          display: "flex",
          gap: 12,
          alignItems: "flex-end",
          maxWidth: 900,
          margin: "0 auto",
        }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Jamil anything…"
            disabled={loading}
            rows={1}
            style={{
              flex: 1,
              resize: "none",
              border: `1.5px solid rgba(181,101,29,0.35)`,
              borderRadius: 12,
              padding: "12px 16px",
              fontSize: 15,
              fontFamily: "inherit",
              background: WHITE,
              color: INK,
              outline: "none",
              lineHeight: 1.5,
              minHeight: 48,
              maxHeight: 180,
              overflow: "auto",
              transition: "border-color 0.15s",
            }}
            onFocus={e => { e.target.style.borderColor = COPPER; }}
            onBlur={e => { e.target.style.borderColor = "rgba(181,101,29,0.35)"; }}
            onInput={e => {
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 180) + "px";
            }}
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            style={{
              background: loading || !input.trim() ? "rgba(181,101,29,0.4)" : COPPER,
              color: WHITE,
              border: "none",
              borderRadius: 12,
              padding: "12px 24px",
              fontSize: 15,
              fontWeight: 700,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              flexShrink: 0,
              height: 48,
              transition: "background 0.15s",
              letterSpacing: "0.03em",
            }}
          >
            {loading ? "…" : "Send"}
          </button>
        </div>
        <p style={{
          margin: "8px auto 0",
          maxWidth: 900,
          fontSize: 11,
          color: INK,
          opacity: 0.4,
          textAlign: "center",
        }}>
          Shift+Enter for new line · Enter to send · Messages persist between sessions
        </p>
      </div>
    </div>
  );
}
