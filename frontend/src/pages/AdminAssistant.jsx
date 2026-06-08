import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { WAI_LOGO } from "../lib/brand";
import { v4 as uuidv4 } from "uuid";
import {
  Send, Bot, Loader2, Mail, FileText, Calendar,
  CheckSquare, ArrowRight, Sparkles, RefreshCw, Users,
} from "lucide-react";

const SESSION_KEY = "assistant_session_id";
const HISTORY_KEY = "assistant_history";

const MAX_HISTORY = 40;

function getSession() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) { id = uuidv4(); localStorage.setItem(SESSION_KEY, id); }
  return id;
}

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch { return []; }
}

function saveHistory(msgs) {
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs.slice(-MAX_HISTORY))); } catch {}
}

const CAPABILITIES = [
  { icon: Mail,       label: "Send Emails",       desc: "Draft and send professional emails instantly" },
  { icon: FileText,   label: "Write Documents",    desc: "Proposals, letters, reports, templates" },
  { icon: Calendar,   label: "Organize Tasks",     desc: "Schedules, follow-ups, action item lists" },
  { icon: CheckSquare,label: "Business Strategy",  desc: "Community outreach, marketing, workflows" },
];

const STARTERS = [
  "Draft a professional follow-up email for a client meeting",
  "Write an outreach letter to community organizations",
  "Create a weekly task checklist for my team",
  "Help me write a service proposal for a new client",
];

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-copper flex items-center justify-center shrink-0 mt-1 shadow-sm">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
      <div
        className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-ink text-white rounded-tr-sm"
            : "bg-white border border-ink/10 text-ink rounded-tl-sm shadow-sm"
        }`}
      >
        {msg.content}
      </div>
    </div>
  );
}

export default function AdminAssistant() {
  const { user } = useAuth();
  const [messages,  setMessages]  = useState(loadHistory);
  const [input,     setInput]     = useState("");
  const [busy,      setBusy]      = useState(false);
  const sessionId = useRef(getSession());
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => { saveHistory(messages); }, [messages]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || busy) return;
    setInput("");

    const history = messages.map(m => ({ role: m.role, content: m.content }));
    const userMsg = { role: "user", content: msg };
    setMessages(prev => [...prev, userMsg]);
    setBusy(true);

    try {
      const { data } = await api.post("/api/assistant/chat", {
        message: msg,
        history,
        session_id: sessionId.current,
      });
      setMessages(prev => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong. Please try again.";
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `I'm having trouble connecting right now. Error: ${detail}\n\n— Admin Assistant, M.O.R.E. Help Center`,
      }]);
    } finally {
      setBusy(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [input, messages, busy]);

  const clearSession = () => {
    localStorage.removeItem(HISTORY_KEY);
    localStorage.removeItem(SESSION_KEY);
    sessionId.current = uuidv4();
    localStorage.setItem(SESSION_KEY, sessionId.current);
    setMessages([]);
    setInput("");
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="min-h-screen bg-bone flex flex-col">

      {/* ── Header ── */}
      <header className="border-b border-ink/10 bg-white sticky top-0 z-40 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <img src={WAI_LOGO} alt="M.O.R.E." className="w-9 h-9 object-contain" style={{ mixBlendMode: "multiply" }} />
            <div>
              <div className="text-xs font-bold uppercase tracking-widest text-copper leading-none">M.O.R.E. Help Center</div>
              <div className="font-heading font-extrabold text-sm leading-tight">Admin Assistant</div>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-emerald-700">Online</span>
            </div>
            {messages.length > 0 && (
              <button
                onClick={clearSession}
                className="flex items-center gap-1.5 text-xs text-ink/40 hover:text-ink/70 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" /> New session
              </button>
            )}
            {!user && (
              <Link to="/login" className="text-xs font-bold bg-copper text-white px-4 py-2 rounded-xl hover:bg-copper/90 transition-colors">
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full px-4 py-6">

        {/* Intro / Empty state */}
        {isEmpty && (
          <div className="flex-1 flex flex-col items-center justify-center py-8 space-y-8">

            {/* Hero */}
            <div className="text-center space-y-3 max-w-xl">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-amber-400 to-copper shadow-lg flex items-center justify-center mx-auto">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h1 className="font-heading text-3xl font-extrabold">Admin Assistant</h1>
              <p className="text-ink/60 text-base leading-relaxed">
                Your professional AI assistant for emails, documents, task management,
                and business communication. Ready to work.
              </p>
            </div>

            {/* Capabilities */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full">
              {CAPABILITIES.map(c => {
                const Icon = c.icon;
                return (
                  <div key={c.label} className="bg-white border border-ink/10 rounded-2xl p-4 text-center hover:border-copper/30 hover:shadow-sm transition-all">
                    <Icon className="w-6 h-6 text-copper mx-auto mb-2" />
                    <div className="font-bold text-xs mb-1">{c.label}</div>
                    <div className="text-ink/50 text-xs leading-snug">{c.desc}</div>
                  </div>
                );
              })}
            </div>

            {/* Starter prompts */}
            <div className="w-full space-y-2">
              <p className="text-xs font-bold uppercase tracking-widest text-ink/40 text-center">Try one of these</p>
              <div className="grid sm:grid-cols-2 gap-2">
                {STARTERS.map(s => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-left text-sm px-4 py-3 bg-white border border-ink/10 rounded-xl hover:border-copper/40 hover:bg-amber-50/50 transition-all text-ink/70 flex items-center gap-2 group"
                  >
                    <ArrowRight className="w-3.5 h-3.5 text-copper shrink-0 group-hover:translate-x-0.5 transition-transform" />
                    {s}
                  </button>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* Messages */}
        {!isEmpty && (
          <div className="flex-1 space-y-4 pb-4 overflow-y-auto">
            {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
            {busy && (
              <div className="flex justify-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-copper flex items-center justify-center shrink-0 mt-1 shadow-sm">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white border border-ink/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 text-ink/50 text-sm shadow-sm">
                  <Loader2 className="w-4 h-4 animate-spin" /> Working on it…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Input bar */}
        <div className="sticky bottom-0 bg-bone pt-3 pb-2">
          <div className="bg-white border border-ink/20 rounded-2xl shadow-sm flex items-end gap-3 px-4 py-3 focus-within:border-copper focus-within:shadow-md transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
              }}
              placeholder="Ask me to draft an email, write a document, organize tasks…"
              rows={2}
              className="flex-1 resize-none bg-transparent text-sm placeholder:text-ink/30 focus:outline-none leading-relaxed"
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || busy}
              className="flex-shrink-0 w-10 h-10 rounded-xl bg-copper text-white flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed hover:bg-copper/90 transition-colors"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-center text-xs text-ink/30 mt-2">
            Enter to send · Shift+Enter for new line · Powered by M.O.R.E. Help Center
          </p>
        </div>

      </div>

      {/* ── Footer ── */}
      <footer className="border-t border-ink/10 bg-white py-6">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-center sm:text-left">
              <div className="font-bold text-sm">M.O.R.E. Help Center</div>
              <div className="text-xs text-ink/50">Admin Assistant · Powered by WAI-Institute AI</div>
            </div>
            <div className="flex items-center gap-4 text-xs text-ink/40">
              <a href="mailto:morehelpcenter@gmail.com" className="hover:text-copper transition-colors">
                morehelpcenter@gmail.com
              </a>
              <Link to="/terms"   className="hover:text-ink/70 transition-colors">Terms</Link>
              <Link to="/privacy" className="hover:text-ink/70 transition-colors">Privacy</Link>
              <Link to="/"        className="hover:text-ink/70 transition-colors">Home</Link>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
