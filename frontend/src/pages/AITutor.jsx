import { useEffect, useRef, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Sparkles, Send } from "lucide-react";
import { toast } from "sonner";

const MODES = [
  { key: "tutor", label: "Master Electrician" },
  { key: "scripture", label: "Scripture Mentor" },
  { key: "explain", label: "Explain Like Apprentice" },
  { key: "quiz_gen", label: "Generate Quiz" },
];

export default function AITutor() {
  const [mode, setMode] = useState("tutor");
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `${Date.now()}`);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: userMsg }]);
    setLoading(true);
    try {
      const r = await api.post("/ai/chat", { session_id: sessionId, message: userMsg, mode });
      setMsgs((m) => [...m, { role: "assistant", text: r.data.reply }]);
    } catch (e) {
      toast.error("AI unavailable. Check configuration or try again.");
      setMsgs((m) => [...m, { role: "assistant", text: "Sorry — I couldn't reach the tutor service. Try again in a moment." }]);
    } finally { setLoading(false); }
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-4xl">
        <div className="overline text-copper">Powered by Claude Sonnet 4.5</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><Sparkles className="w-8 h-8 text-copper" /> AI Tutor</h1>
        <p className="text-ink/60 mt-2">Ask questions. Request explanations. Request scripture. Generate a practice quiz.</p>

        <div className="flex gap-2 mt-6 flex-wrap" data-testid="mode-switcher">
          {MODES.map((m) => (
            <button key={m.key} onClick={() => setMode(m.key)}
              className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border transition-colors ${mode === m.key ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20 hover:border-ink"}`}
              data-testid={`mode-${m.key}`}>
              {m.label}
            </button>
          ))}
        </div>

        <div className="card-flat mt-6 h-[500px] flex flex-col" data-testid="chat-window">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {msgs.length === 0 && (
              <div className="text-center text-ink/40 py-16">
                <Sparkles className="w-10 h-10 mx-auto text-copper/50" />
                <div className="mt-3 text-sm">Start by asking: <em>"Explain why neutrals and grounds are only bonded at the service."</em></div>
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-ink text-white" : "bg-bone border border-ink/10"}`} data-testid={`msg-${i}`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && <div className="text-sm text-ink/50 italic">Tutor is thinking…</div>}
            <div ref={endRef} />
          </div>
          <div className="border-t border-ink/10 p-4 flex gap-2">
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask the tutor…"
              className="flex-1 px-4 py-3 bg-white border border-ink/20 focus:outline-none focus:border-ink focus:ring-2 focus:ring-signal"
              data-testid="chat-input" />
            <button onClick={send} disabled={loading} className="btn-primary inline-flex items-center gap-2" data-testid="btn-send">
              <Send className="w-4 h-4" /> Send
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
