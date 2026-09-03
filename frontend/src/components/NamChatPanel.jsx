import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Loader2, Send, MessageSquare } from "lucide-react";

/**
 * NamChatPanel — real Hybrid NAM conversation on the /nam page.
 *
 * POSTs to /api/nam/chat, which runs the full Hybrid NAM stack:
 * designation + Knowledge Forge + memory engine + LLM gateway
 * (backend/routers/nam.py nam_chat). Not a mock: the backend answers from
 * provider models when funded (staff platform AI or BYOK) and degrades
 * gracefully to the keyword KB otherwise — never a canned fake reply.
 */
export default function NamChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [degraded, setDegraded] = useState(false);
  const [provider, setProvider] = useState("");
  const listRef = useRef(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { data } = await api.get("/nam/chat/history", { params: { session_id: "default" } });
        if (!alive) return;
        const history = Array.isArray(data?.history) ? data.history : [];
        setMessages(
          history.flatMap((h) =>
            h?.user_msg
              ? [
                  { role: "user", content: h.user_msg, at: h.created_at },
                  { role: "assistant", content: h.assistant_msg, at: h.created_at },
                ]
              : []
          )
        );
      } catch {
        // History is best-effort; the chat itself still works.
      } finally {
        if (alive) setLoadingHistory(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, sending]);

  const send = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const { data } = await api.post("/nam/chat", {
        message: text,
        session_id: "default",
        history: messages.slice(-8).map((m) => ({ role: m.role, content: m.content })),
      });
      setDegraded(Boolean(data?.degraded));
      setProvider(data?.provider || "");
      setMessages((m) => [...m, { role: "assistant", content: data?.reply || "(empty reply)" }]);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Chat request failed.");
    } finally {
      setSending(false);
    }
  };

  return (
    <section aria-label="Hybrid NAM chat" className="border border-ink/10 rounded-xl bg-white flex flex-col h-[520px]">
      <header className="shrink-0 border-b border-ink/10 px-4 py-3 flex items-center gap-2">
        <MessageSquare className="w-4 h-4 text-ink" />
        <h2 className="text-sm font-bold text-ink">Talk to Hybrid NAM</h2>
        {degraded && (
          <span className="ml-auto text-[10px] font-bold uppercase tracking-widest text-amber-700 bg-amber-100 border border-amber-300 rounded px-2 py-0.5">
            {provider === "kb_fallback" ? "Knowledge Base mode — no live AI key" : `Degraded (${provider || "fallback"})`}
          </span>
        )}
      </header>

      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {loadingHistory ? (
          <div className="h-full flex items-center justify-center text-ink/50 text-sm gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading history…
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <p className="text-sm text-ink/50 max-w-xs">
              Ask Hybrid NAM anything about the institution. When a live AI provider is
              funded — or you bring your own key — answers come from the provider model.
              Otherwise answers come from the knowledge base and are clearly labeled.
            </p>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={
                  m.role === "user"
                    ? "max-w-[85%] rounded-lg px-3 py-2 text-sm bg-ink text-white"
                    : "max-w-[85%] rounded-lg px-3 py-2 text-sm bg-bone text-ink border border-ink/10"
                }
              >
                {m.content}
              </div>
            </div>
          ))
        )}
        {degraded && (
          <div className="shrink-0 border-t border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800 flex items-center gap-2 flex-wrap">
            <span>Live AI needs a provider key. Bring your own key for provider-powered answers:</span>
            <a href="/byok" className="font-bold text-amber-900 underline">BYOK setup →</a>
          </div>
        )}
        {sending && (
          <div className="flex justify-start">
            <div className="rounded-lg px-3 py-2 text-sm bg-bone text-ink border border-ink/10 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Hybrid NAM is thinking…
            </div>
          </div>
        )}
      </div>

      <form onSubmit={send} className="shrink-0 border-t border-ink/10 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm text-ink focus:outline-none focus:border-copper"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-bold bg-ink text-white hover:bg-ink/90 disabled:opacity-40"
        >
          {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Send
        </button>
      </form>
    </section>
  );
}
