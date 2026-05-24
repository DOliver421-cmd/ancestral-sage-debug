import { useState } from "react";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import SovereignAvatar from "./SovereignAvatar";
import { Send, X } from "lucide-react";

// Executive-only "Summon The Sovereign" launcher + resizable chat panel.
// Wired to POST /api/sovereign/chat (exec-gated on the backend). Renders nothing
// for non-exec users — members use the AI Tutor instead. Floats bottom-left so it
// never collides with the bottom-anchored Director widget.
export default function SovereignChat() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  if (user?.role !== "executive_admin") return null;

  const send = async (e) => {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || sending) return;
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setSending(true);
    try {
      const r = await api.post("/sovereign/chat", { message: msg });
      setMessages((m) => [...m, { role: "sovereign", text: r.data?.reply || "…" }]);
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
      <div className="flex items-center justify-between px-4 py-3" style={{ background: "var(--wai-emerald)" }}>
        <div className="flex items-center gap-2" style={{ color: "var(--wai-gold-light)" }}>
          <SovereignAvatar size={32} />
          <span className="font-heading font-bold">The Sovereign</span>
        </div>
        <button onClick={() => setOpen(false)} aria-label="Close" style={{ color: "var(--wai-gold-light)" }}>
          <X className="w-5 h-5" />
        </button>
      </div>

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
            </div>
          </div>
        ))}
        {sending && <div className="text-xs" style={{ color: "var(--wai-muted)" }}>The Sovereign is considering…</div>}
      </div>

      <form onSubmit={send} className="p-3 flex gap-2" style={{ borderTop: "1px solid var(--wai-border)" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask The Sovereign…"
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
