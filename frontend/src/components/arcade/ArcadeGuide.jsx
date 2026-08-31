import { useState, useRef, useEffect } from "react";
import { api } from "../../lib/api";
import { Send, Bot } from "lucide-react";

export default function ArcadeGuide({ gameSlug }) {
  const [messages, setMessages] = useState([
    { role: "guide", text: "What's good. Ask me anything — history, money, music, faith. Or just chill." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const r = await api.post("/arcade/chat", { message: msg, game_slug: gameSlug || null });
      setMessages((m) => [...m, { role: "guide", text: r.data.reply }]);
    } catch {
      setMessages((m) => [...m, { role: "guide", text: "I'm offline for a sec. Try again in a moment." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: "#0a0a0f", border: "1px solid rgba(184,134,11,0.4)", fontFamily: "monospace" }}>
      <div style={{ padding: "0.75rem 1rem", borderBottom: "1px solid rgba(184,134,11,0.2)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <Bot style={{ width: 14, height: 14, color: "#ffd700" }} />
        <span style={{ color: "#ffd700", fontSize: "0.7rem", fontWeight: 900, letterSpacing: "0.08em" }}>ARCADE GUIDE · FREE AI</span>
        <span style={{ marginLeft: "auto", fontSize: "0.6rem", color: "rgba(184,134,11,0.6)" }}>no cost · always on</span>
      </div>

      <div style={{ height: "180px", overflowY: "auto", padding: "0.75rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{
              maxWidth: "80%",
              padding: "0.4rem 0.75rem",
              fontSize: "0.78rem",
              lineHeight: 1.5,
              background: m.role === "user" ? "rgba(184,134,11,0.2)" : "rgba(255,255,255,0.05)",
              border: `1px solid ${m.role === "user" ? "rgba(184,134,11,0.4)" : "rgba(255,255,255,0.1)"}`,
              color: m.role === "user" ? "#ffd700" : "rgba(255,255,255,0.8)",
            }}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex" }}>
            <div style={{ padding: "0.4rem 0.75rem", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.3)", fontSize: "0.75rem" }}>
              ...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: "0.5rem", borderTop: "1px solid rgba(184,134,11,0.2)", display: "flex", gap: "0.5rem" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask anything..."
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(184,134,11,0.3)",
            padding: "0.4rem 0.6rem",
            color: "white",
            fontFamily: "monospace",
            fontSize: "0.78rem",
            outline: "none",
          }}
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          style={{
            background: input.trim() && !loading ? "#b8860b" : "rgba(184,134,11,0.2)",
            border: "none",
            padding: "0.4rem 0.75rem",
            cursor: input.trim() && !loading ? "pointer" : "default",
            display: "flex",
            alignItems: "center",
          }}
        >
          <Send style={{ width: 13, height: 13, color: "#0a0a0f" }} />
        </button>
      </div>
    </div>
  );
}
