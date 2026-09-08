import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { HelpCircle, X, Search, ArrowRight, ExternalLink, Send, Compass, BookOpen, MessagesSquare } from "lucide-react";
import useDraggablePosition from "../hooks/useDraggablePosition";

/* HelpGuide — THE combined Site Guide + Help feature.

   One floating widget on every page:
     • "This Page" tab  — context-aware help for the current route (from
       /help/guide, now including every Homeschool Academy page)
     • "Ask the Guide" tab — the Site Guide persona chat (gated server-side to
       member+ / BYOK / staff; the free FAQ + page-index KB answers for free)

   The old standalone /site-guide page redirects here (see App.js), so there is
   exactly one help/guide feature across the whole site. */

const GREETING = {
  role: "assistant",
  content:
    "Hi! I'm the Site Guide — I know my way around every corner of MoreHelp, including the Homeschool Academy. Ask me where to find anything or how something works.",
};

const GUIDE_SUGGESTIONS = [
  "How does Homeschool work here?",
  "Where do I find my courses?",
  "What's free and what's paid?",
  "How do I get the Florida homeschool paperwork?",
];

export default function HelpGuide() {
  const { user } = useAuth();
  const location = useLocation();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("page"); // "page" | "guide"
  const [help, setHelp] = useState(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);

  // Guide chat state
  const [guideStatus, setGuideStatus] = useState(null);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const panelRef = useRef(null);
  const bottomRef = useRef(null);
  const fab = useDraggablePosition("mhc_help_fab", { x: 16, y: 16 });

  const fetchHelp = useCallback(async (path, q) => {
    setBusy(true);
    try {
      const r = await api.post("/help/guide", { path, query: q || null, anon: !user });
      setHelp(r.data);
    } catch {
      setHelp(null);
    } finally {
      setBusy(false);
    }
  }, [user]);

  useEffect(() => {
    if (open) fetchHelp(location.pathname, query);
  }, [open, location.pathname, query, fetchHelp]);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  useEffect(() => {
    if (!open || !panelRef.current) return;
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target) && !e.target.closest("[data-help-toggle]")) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (open && tab === "guide" && !guideStatus) {
      api.get("/site-guide/status")
        .then((r) => setGuideStatus(r.data))
        .catch(() => setGuideStatus({ access: false, reason: "signed_out", tier: "free", byok_enabled: false }));
    }
  }, [open, tab, guideStatus]);

  useEffect(() => {
    if (tab === "guide") bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, tab]);

  const sendGuide = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: msg }]);
    setSending(true);
    try {
      const history = messages.map(({ role, content }) => ({ role, content })).slice(-12);
      const { data } = await api.post("/site-guide/chat", { message: msg, history });
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setMessages((m) => [...m, {
        role: "assistant",
        content: detail === "Site Guide access required"
          ? "The Guide chat needs a paid membership or the $3 BYOK unlock — but the This Page tab and site search are always free. Visit /plans or /byok to upgrade."
          : (detail || "The Guide is unavailable right now. Try the This Page tab or site search."),
      }]);
    } finally {
      setSending(false);
    }
  }, [input, sending, messages]);

  // Deep-link support: /site-guide?chat=1 opens the widget on the guide tab.
  useEffect(() => {
    if (location.pathname === "/site-guide") {
      setOpen(true);
      setTab("guide");
      nav("/", { replace: true });
    }
  }, [location.pathname, nav]);

  return (
    <>
      {/* Floating help button — compact pill with label, bottom-left to avoid blocking content */}
      <button
        data-help-toggle
        onClick={(e) => { if (fab.dragged) { e.preventDefault(); return; } setOpen(!open); }}
        onPointerDown={fab.onPointerDown}
        className="fixed z-50 flex items-center gap-2 px-4 py-2 bg-ink text-white rounded-full shadow-lg hover:bg-ink/90 transition-all text-sm font-semibold touch-none select-none"
        style={{
          left: fab.pos ? fab.pos.x : undefined,
          top: fab.pos ? fab.pos.y : undefined,
          ...(fab.pos ? {} : { bottom: 16, left: 176 }),
          cursor: fab.dragged ? "grabbing" : "grab",
        }}
        aria-label="Get help with this page"
        title="Help & Site Guide — drag to move"
      >
        {open ? <X className="w-4 h-4" /> : <HelpCircle className="w-4 h-4" />}
        <span>{open ? "Close" : "Help"}</span>
      </button>

      {/* Combined Help + Guide panel */}
      {open && (
        <div
          ref={panelRef}
          className="fixed z-50 w-80 sm:w-96 max-h-[75vh] bg-white rounded-2xl shadow-2xl border border-ink/10 flex flex-col overflow-hidden animate-fade-in"
          style={fab.pos ? { left: fab.pos.x, top: Math.max(8, fab.pos.y - 60) } : { bottom: 64, left: 176 }}
        >
          {/* Header with tabs */}
          <div className="bg-ink text-white px-5 py-4">
            <div className="flex items-center justify-between">
              <h3 className="font-heading font-bold text-sm uppercase tracking-wider flex items-center gap-2">
                <Compass className="w-4 h-4 text-signal" /> Site Guide
              </h3>
              <button onClick={() => setOpen(false)} aria-label="Close help" className="text-white/50 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            {/* Tab switcher */}
            <div className="mt-3 grid grid-cols-2 gap-1 bg-white/10 rounded-lg p-1">
              <button
                onClick={() => setTab("page")}
                className={`flex items-center justify-center gap-1.5 py-1.5 text-xs font-bold rounded-md transition-colors ${tab === "page" ? "bg-white text-ink" : "text-white/70 hover:text-white"}`}
              >
                <BookOpen className="w-3.5 h-3.5" /> This Page
              </button>
              <button
                onClick={() => setTab("guide")}
                className={`flex items-center justify-center gap-1.5 py-1.5 text-xs font-bold rounded-md transition-colors ${tab === "guide" ? "bg-white text-ink" : "text-white/70 hover:text-white"}`}
              >
                <MessagesSquare className="w-3.5 h-3.5" /> Ask the Guide
              </button>
            </div>
          </div>

          {/* ── Tab: This Page (context help + search) ── */}
          {tab === "page" && (
            <>
              <div className="px-5 pt-4 pb-3 bg-white border-b border-ink/10">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search this page's help…"
                    className="w-full pl-10 pr-4 py-2 text-sm bg-ink/5 border border-ink/15 rounded-lg text-ink placeholder-ink/40 focus:outline-none focus:ring-2 focus:ring-copper/50"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {busy && (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-6 h-6 border-2 border-copper border-t-transparent rounded-full animate-spin" />
                  </div>
                )}

                {!busy && help && (
                  <>
                    <div>
                      <h4 className="font-heading font-bold text-lg text-ink">{help.title}</h4>
                      <p className="text-sm text-ink/70 mt-1">{help.summary}</p>
                    </div>

                    {help.tip && (
                      <div className="bg-copper/5 border-l-4 border-copper rounded-r-lg px-4 py-3">
                        <p className="text-xs font-bold text-copper uppercase tracking-wider">Tip for you</p>
                        <p className="text-sm text-ink/80 mt-1">{help.tip}</p>
                      </div>
                    )}

                    {help.details && help.details.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Key Info</p>
                        <ul className="space-y-2">
                          {help.details.map((d, i) => (
                            <li key={i} className="text-sm text-ink/70 flex items-start gap-2">
                              <span className="text-copper mt-1 shrink-0">•</span>
                              {d}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {help.common_tasks && help.common_tasks.length > 0 && (
                      <div>
                        <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Quick Actions</p>
                        <div className="flex flex-wrap gap-2">
                          {help.common_tasks.map((task, i) => (
                            <button
                              key={i}
                              onClick={() => nav(task)}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-copper/10 text-copper rounded-lg hover:bg-copper/20 transition-colors"
                            >
                              <ArrowRight className="w-3 h-3" /> {task.replace("/", "").replace("-", " ") || "Home"}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {help.related && help.related.length > 0 && (
                      <div className="pt-2 border-t border-ink/10">
                        <p className="text-xs font-bold text-ink/50 uppercase tracking-wider mb-2">Related Pages</p>
                        <div className="flex flex-wrap gap-2">
                          {help.related.map((link, i) => (
                            <button
                              key={i}
                              onClick={() => nav(link)}
                              className="inline-flex items-center gap-1 text-xs text-ink/60 hover:text-copper transition-colors"
                            >
                              <ExternalLink className="w-3 h-3" /> {link}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}

                {!busy && !help && (
                  <div className="text-center py-8 text-sm text-ink/50">
                    <p>{user ? "No specific help for this page yet — try Ask the Guide." : "Sign in for personalized help, or try Ask the Guide."}</p>
                    <button onClick={() => setTab("guide")} className="mt-3 text-xs font-bold text-copper hover:text-ink transition-colors">
                      Ask the Guide →
                    </button>
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── Tab: Ask the Guide (persona chat) ── */}
          {tab === "guide" && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: "260px" }}>
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                        m.role === "user"
                          ? "bg-copper text-white rounded-br-sm"
                          : "bg-ink/5 text-ink rounded-bl-sm border border-ink/10"
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="bg-ink/5 border border-ink/10 rounded-2xl rounded-bl-sm px-4 py-2.5">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce" />
                        <span className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {messages.length <= 1 && (
                <div className="px-4 pb-2 flex flex-wrap gap-1.5">
                  {GUIDE_SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendGuide(s)}
                      className="text-[11px] font-bold text-copper bg-copper/10 hover:bg-copper/20 border border-copper/25 rounded-full px-2.5 py-1 transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              <form
                onSubmit={(e) => { e.preventDefault(); sendGuide(); }}
                className="border-t border-ink/10 p-3 flex items-center gap-2"
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={
                    guideStatus && guideStatus.access === false
                      ? "Guide chat needs Member+ or BYOK — This Page is free"
                      : "Ask the Guide anything…"
                  }
                  className="flex-1 px-3.5 py-2 text-sm bg-ink/5 border border-ink/15 rounded-lg text-ink placeholder-ink/40 focus:outline-none focus:ring-2 focus:ring-copper/50"
                />
                <button
                  type="submit"
                  disabled={sending || !input.trim()}
                  className="shrink-0 w-9 h-9 flex items-center justify-center bg-copper text-white rounded-lg hover:bg-copper/85 transition-colors disabled:opacity-40"
                  aria-label="Send"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </>
          )}

          {/* Footer */}
          <div className="border-t border-ink/10 px-5 py-2.5 bg-ink/5 flex items-center justify-between">
            <button onClick={() => nav("/more-help-center")} className="text-xs text-copper hover:underline flex items-center gap-1">
              <ExternalLink className="w-3 h-3" /> MORE Help Center
            </button>
            <span className="text-[10px] text-ink/35 font-bold uppercase tracking-wider">Help + Guide · one feature</span>
          </div>
        </div>
      )}
    </>
  );
}
