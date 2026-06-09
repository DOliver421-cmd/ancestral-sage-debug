import { useState, useRef, useEffect } from "react";
import { api } from "../../lib/api";
import { Send, ChevronRight, ChevronLeft } from "lucide-react";

const GREETINGS = [
  "Boss, what are we building today?",
  "The Sanctuary is live. Where do we start?",
  "Your tools are ready. What's the vision?",
  "I've got everything prepped. Your call.",
];

export default function SovereignVoice({ activeChamber }) {
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState([
    { role: "sovereign", text: GREETINGS[Math.floor(Math.random() * GREETINGS.length)] }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (activeChamber) {
      const notes = {
        lyric: "Lyric Forge is open. What are we writing — hook, verse, bridge?",
        publishing: "Publishing Gate is ready. Drop the title and I'll build the metadata.",
      };
      if (notes[activeChamber]) {
        setMessages(m => [...m, { role: "sovereign", text: notes[activeChamber] }]);
      }
    }
  }, [activeChamber]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const r = await api.post("/sovereign/chat", {
        message: msg,
        context: activeChamber ? `User is in the ${activeChamber} chamber of the Creator's Sanctuary.` : "User is in the Creator's Sanctuary.",
      });
      setMessages(m => [...m, { role: "sovereign", text: r.data.reply || r.data.response || "I'm on it." }]);
    } catch {
      setMessages(m => [...m, { role: "sovereign", text: "Give me a moment — I'll be right back." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed", left: 0, top: 0, bottom: 0, zIndex: 50,
      display: "flex", alignItems: "stretch",
      transition: "all 0.3s ease",
    }}>
      {/* Panel */}
      <div style={{
        width: collapsed ? 0 : 280,
        overflow: "hidden",
        transition: "width 0.3s ease",
        background: "rgba(8,8,16,0.97)",
        borderRight: "1px solid rgba(184,134,11,0.25)",
        display: "flex", flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{ padding: "20px 16px 12px", borderBottom: "1px solid rgba(184,134,11,0.15)" }}>
          <div style={{ color: "#b8860b", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 4 }}>
            Sovereign
          </div>
          <div style={{ color: "rgba(255,255,255,0.9)", fontSize: 13, fontWeight: 700 }}>
            Your Studio Manager
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "85%",
                padding: "8px 12px",
                borderRadius: m.role === "user" ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                fontSize: 12,
                lineHeight: 1.6,
                background: m.role === "user" ? "rgba(184,134,11,0.2)" : "rgba(255,255,255,0.06)",
                border: `1px solid ${m.role === "user" ? "rgba(184,134,11,0.35)" : "rgba(255,255,255,0.08)"}`,
                color: m.role === "user" ? "#ffd700" : "rgba(255,255,255,0.88)",
              }}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: "flex" }}>
              <div style={{ padding: "8px 12px", borderRadius: "12px 12px 12px 2px", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.3)", fontSize: 12 }}>
                ...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: "10px 12px", borderTop: "1px solid rgba(184,134,11,0.15)", display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Talk to Sovereign..."
            style={{
              flex: 1, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(184,134,11,0.25)",
              padding: "7px 10px", color: "white", fontSize: 12, fontFamily: "inherit", outline: "none", borderRadius: 6,
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            style={{ background: input.trim() && !loading ? "#b8860b" : "rgba(184,134,11,0.2)", border: "none", borderRadius: 6, padding: "7px 10px", cursor: input.trim() && !loading ? "pointer" : "default", display: "flex", alignItems: "center" }}
          >
            <Send style={{ width: 13, height: 13, color: "#0a0a0f" }} />
          </button>
        </div>
      </div>

      {/* Toggle tab */}
      <button
        onClick={() => setCollapsed(v => !v)}
        style={{
          width: 20, alignSelf: "center",
          background: "rgba(184,134,11,0.15)",
          border: "1px solid rgba(184,134,11,0.3)",
          borderLeft: "none",
          padding: "12px 0",
          cursor: "pointer",
          color: "#b8860b",
          borderRadius: "0 6px 6px 0",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}
        title={collapsed ? "Open Sovereign" : "Collapse Sovereign"}
      >
        {collapsed ? <ChevronRight style={{ width: 12, height: 12 }} /> : <ChevronLeft style={{ width: 12, height: 12 }} />}
      </button>
    </div>
  );
}
