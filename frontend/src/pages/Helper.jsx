import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import { Send, HelpCircle, ShieldCheck, Loader2 } from "lucide-react";
import { toast } from "sonner";

// Public helper — no auth required, uses public endpoints
function PublicHelper() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setLoading(true);
    try {
      const r = await fetch("/api/public/helper/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
      const data = await r.json();
      setMsgs((m) => [...m, { role: "assistant", text: data.answer || data.reply || "No response received." }]);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", text: "Sorry — I couldn't reach the help service. Please try again in a moment." }]);
      toast.error("Help service unavailable. Try again shortly.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone flex flex-col">
      {/* Header */}
      <div className="bg-ink text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <HelpCircle className="w-6 h-6 text-copper" />
          <div>
            <div className="font-heading font-bold text-lg">W.A.I. Help Center</div>
            <div className="text-xs text-white/60">Public — no login required</div>
          </div>
        </div>
        <button
          onClick={() => navigate("/login")}
          className="text-xs font-bold uppercase tracking-widest border border-white/30 px-4 py-2 hover:border-white flex items-center gap-2"
        >
          <ShieldCheck className="w-4 h-4" /> Sign in for full access
        </button>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-y-auto p-6 max-w-3xl mx-auto w-full space-y-4">
        {msgs.length === 0 && (
          <div className="text-center text-ink/40 py-20">
            <HelpCircle className="w-10 h-10 mx-auto text-copper/50" />
            <div className="mt-3 text-sm">Ask any question about W.A.I. programs, enrollment, or apprenticeship requirements.</div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-ink text-white" : "bg-white border border-ink/10"}`}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-sm text-ink/50 italic flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking…
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="border-t border-ink/10 p-4 max-w-3xl mx-auto w-full">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask a question…"
            className="flex-1 px-4 py-3 bg-white border border-ink/20 focus:outline-none focus:border-ink focus:ring-2 focus:ring-copper/30 text-sm"
          />
          <button
            onClick={send}
            disabled={loading}
            className="bg-ink text-white px-5 py-3 font-bold uppercase tracking-widest text-xs hover:bg-ink/90 disabled:opacity-50 inline-flex items-center gap-2"
          >
            <Send className="w-4 h-4" /> Send
          </button>
        </div>
      </div>
    </div>
  );
}

// Authenticated helper — requires WAI session, uses auth endpoints
function AuthHelper() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setLoading(true);
    try {
      const r = await api.post("/helper/ask", { question });
      const reply = r.data.answer || r.data.reply || "No response received.";
      setMsgs((m) => [...m, { role: "assistant", text: reply }]);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", text: "Sorry — I couldn't reach the help service. Please try again in a moment." }]);
      toast.error("Help service unavailable. Try again shortly.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-4xl">
        <div className="flex items-center gap-3 mb-6">
          <HelpCircle className="w-8 h-8 text-copper" />
          <div>
            <h1 className="font-heading text-4xl font-bold">Help Center</h1>
            <p className="text-ink/60 mt-1">Ask anything about your coursework, labs, credentials, or program.</p>
          </div>
        </div>

        <div className="card-flat h-[500px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {msgs.length === 0 && (
              <div className="text-center text-ink/40 py-16">
                <HelpCircle className="w-10 h-10 mx-auto text-copper/50" />
                <div className="mt-3 text-sm">Ask about modules, labs, credentials, attendance, or anything else.</div>
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-ink text-white" : "bg-bone border border-ink/10"}`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="text-sm text-ink/50 italic flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking…
              </div>
            )}
            <div ref={endRef} />
          </div>
          <div className="border-t border-ink/10 p-4 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask a question…"
              className="flex-1 px-4 py-3 bg-white border border-ink/20 focus:outline-none focus:border-ink focus:ring-2 focus:ring-copper/30 text-sm"
            />
            <button
              onClick={send}
              disabled={loading}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Send className="w-4 h-4" /> Send
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

// Route decider — /helper shows public, /app/helper shows auth version
export default function Helper({ requireAuth = false }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-ink font-heading">Loading…</div>;
  if (requireAuth && !user) {
    // Redirect to login if auth required but not logged in
    window.location.href = "/login";
    return null;
  }
  if (requireAuth) return <AuthHelper />;
  return <PublicHelper />;
}
