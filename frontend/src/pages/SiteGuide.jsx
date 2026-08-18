/**
 * SiteGuide — the Site Guide persona.
 *
 * A warm front-desk guide that knows the whole site. Gated to:
 *   - any paid membership tier (Member+), OR
 *   - an active $3 BYOK entitlement, OR
 *   - admin / executive_admin (bypass).
 *
 * The backend enforces the gate (POST /api/site-guide/chat). This page reads
 * GET /api/site-guide/status to render the right experience and shows clear
 * upgrade paths when the user doesn't qualify yet.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  Compass, Send, Loader2, Sparkles, KeyRound, ArrowRight,
  Bot, RefreshCw, ShieldCheck, Zap, Landmark,
} from "lucide-react";
import { toast } from "sonner";

const GREETING = {
  role: "assistant",
  content:
    "Welcome to M.O.R.E. Help Center. I'm the Site Guide — I know my way around every corner of this place. Ask me where to find anything, what a plan includes, or how a feature works.",
};

const SUGGESTIONS = [
  "Where do I find my courses and modules?",
  "What's the difference between Member, Plus, Pro, and Patron?",
  "How does the $3 All-Access Trial work?",
  "What is BYOK and how do I set it up?",
  "How do I get help with housing, legal, or food resources?",
  "How do I start creating with the Creator Studio?",
];

export default function SiteGuide() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const { data } = await api.get("/site-guide/status");
        if (mounted) setStatus(data);
      } catch {
        if (mounted) setStatus({ access: false, reason: "signed_out", tier: "free", byok_enabled: false });
      } finally {
        if (mounted) setLoadingStatus(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = useCallback(
    async (text) => {
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
        if (err?.response?.status === 403) {
          toast.error(detail || "The Site Guide is a member benefit.");
          setStatus((s) => ({ ...s, access: false, reason: "none" }));
        } else {
          toast.error(detail || "The Site Guide hit a snag — try again in a moment.");
        }
      } finally {
        setSending(false);
      }
    },
    [input, sending, messages]
  );

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // ── Gate (no access yet) ──────────────────────────────────────────────────
  const showGate = !loadingStatus && !status?.access;

  // Instructor tier and above get BYOK free; everyone below pays $3 one-time.
  const byokFree = status?.byok_free_for_role || status?.byok_price_usd === 0;
  const byokLabel = byokFree ? "Unlock with BYOK — free for instructors" : `Unlock with BYOK — $${status?.byok_price_usd ?? 3}`;

  const gate = (
    <div className="min-h-[100vh] flex items-center justify-center px-6 py-16 bg-bone">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 text-center shadow-xl border-2"
        style={{ borderColor: "rgba(232,165,30,0.35)" }}>
        <div className="w-16 h-16 mx-auto rounded-2xl flex items-center justify-center"
          style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
          <Compass className="w-8 h-8" style={{ color: "#E8A51E" }} />
        </div>
        <h1 className="font-heading text-2xl font-bold text-ink mt-5">Meet the Site Guide</h1>
        <p className="text-ink/60 text-sm mt-3 leading-relaxed">
          An AI guide that knows the whole building — where things live, what each plan includes,
          and how every feature works. It runs on AI API keys: unlock it with any paid plan, the{" "}
          <strong className="text-ink">$3 All-Access Trial</strong>, or{" "}
          <strong className="text-ink">BYOK</strong> —{" "}
          {byokFree ? (
            <strong className="text-ink">free for instructors and above</strong>
          ) : (
            <>a one-time <strong className="text-ink">${status?.byok_price_usd ?? 3}</strong> fee</>
          )}.
        </p>

        <div className="mt-6 flex flex-col gap-2.5">
          {user ? (
            <>
              <Link to="/subscribe?plan=member_monthly"
                className="btn-copper w-full text-center text-sm font-black py-3 rounded-xl">
                Become a Member — $9/mo
              </Link>
              <Link to="/subscribe?plan=sanctuary_trial"
                className="w-full text-center text-sm font-bold py-3 rounded-xl"
                style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                ⚡ Try everything for $3
              </Link>
              <Link to="/byok"
                className="w-full text-center text-sm font-bold py-3 rounded-xl border-2"
                style={{ borderColor: "#1B4332", color: "#1B4332" }}>
                <KeyRound className="w-3.5 h-3.5 inline mr-1" /> {byokLabel}
              </Link>
              <Link to="/plans" className="w-full text-center text-xs text-ink/50 font-semibold py-1 hover:text-copper">
                Compare all plans →
              </Link>
            </>
          ) : (
            <>
              <Link to="/register" className="btn-copper w-full text-center text-sm font-black py-3 rounded-xl">
                Create a free account
              </Link>
              <Link to="/login" className="w-full text-center text-xs text-ink/50 font-semibold py-1 hover:text-copper">
                Already have an account? Sign in →
              </Link>
            </>
          )}
        </div>

        <div className="mt-6 pt-5 border-t border-ink/10 text-left">
          <p className="text-[11px] font-black uppercase tracking-widest text-ink/40 mb-2">What you get</p>
          <ul className="space-y-1.5 text-xs text-ink/60">
            <li className="flex items-center gap-2"><ShieldCheck className="w-3.5 h-3.5 text-copper" /> Direct answers about every part of the site</li>
            <li className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 text-copper" /> Plan-by-plan guidance and upgrade help</li>
            <li className="flex items-center gap-2"><Bot className="w-3.5 h-3.5 text-copper" /> BYOK users run the guide on their own key</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // ── Chat (access granted) ─────────────────────────────────────────────────
  const chat = (
    <AppShell>
      <div className="flex flex-col min-h-screen">
        {/* Header */}
        <div className="border-b border-ink/10 bg-ink text-white px-6 py-5">
          <div className="max-w-3xl mx-auto flex items-center gap-4">
            <div className="w-11 h-11 rounded-2xl flex items-center justify-center shrink-0"
              style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E" }}>
              <Compass className="w-6 h-6" style={{ color: "#E8A51E" }} />
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="font-heading font-bold text-lg flex items-center gap-2">
                Site Guide
                <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full"
                  style={{ background: "rgba(232,165,30,0.15)", color: "#E8A51E" }}>
                  <Sparkles className="w-3 h-3" /> Member
                </span>
              </h1>
              <p className="text-xs text-white/50">Knows the whole site · answers in plain language</p>
            </div>
            <Link to="/search" className="text-xs font-bold text-white/70 hover:text-white flex items-center gap-1.5 border border-white/20 rounded-lg px-3 py-1.5">
              <Compass className="w-3.5 h-3.5" /> Search
            </Link>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                {m.role === "assistant" && (
                  <div className="w-8 h-8 rounded-xl shrink-0 flex items-center justify-center"
                    style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
                    <Compass className="w-4 h-4" style={{ color: "#E8A51E" }} />
                  </div>
                )}
                <div className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed rounded-2xl ${
                  m.role === "user"
                    ? "bg-ink text-white rounded-tr-sm"
                    : "bg-white border border-ink/10 text-ink rounded-tl-sm"
                }`}>
                  {m.content}
                </div>
              </div>
            ))}

            {sending && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-xl shrink-0 flex items-center justify-center"
                  style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>
                  <Compass className="w-4 h-4" style={{ color: "#E8A51E" }} />
                </div>
                <div className="bg-white border border-ink/10 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-ink/40 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-copper" /> Thinking…
                </div>
              </div>
            )}

            {/* Suggestions */}
            {messages.length <= 1 && !sending && (
              <div className="pt-2">
                <p className="text-[10px] font-black uppercase tracking-widest text-ink/35 mb-2">Try asking</p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="text-xs font-bold text-ink/70 bg-white border border-ink/15 rounded-full px-3.5 py-2 hover:border-copper hover:text-copper transition-colors text-left"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {/* Hire the Office — the revenue loop the mission runs on */}
            <div className="pt-3">
              <div className="rounded-2xl p-4 flex items-center justify-between gap-3 flex-wrap"
                style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)", border: "1.5px solid #E8A51E" }}>
                <div className="flex items-center gap-3 min-w-[220px] flex-1">
                  <div className="w-9 h-9 rounded-xl shrink-0 flex items-center justify-center" style={{ background: "#E8A51E" }}>
                    <Landmark className="w-4 h-4" style={{ color: "#0a0a0a" }} />
                  </div>
                  <div>
                    <div className="font-heading font-bold text-white text-sm">Hire the AI Business Office</div>
                    <div className="text-white/70 text-xs mt-0.5 leading-snug">
                      Social media management, audits, micro-SaaS tools, persona builds — the AI drafts the plan,
                      a human approves it, and you approve before anything ships.
                    </div>
                  </div>
                </div>
                <Link to="/business-office"
                  className="shrink-0 flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-black no-underline"
                  style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                  Open a deal <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-ink/10 bg-white px-6 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-3 items-end">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                maxLength={4000}
                rows={2}
                placeholder="Where do you want to go? e.g. “How do I publish a course?”"
                className="flex-1 border border-ink/20 bg-bone px-4 py-2.5 text-sm rounded-xl resize-none focus:outline-none focus:border-copper"
              />
              <button
                onClick={() => send()}
                disabled={sending || !input.trim()}
                className="btn-copper p-3.5 rounded-xl flex items-center justify-center disabled:opacity-50"
                aria-label="Send"
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[11px] text-ink/35 mt-2 flex items-center gap-1.5">
              <RefreshCw className="w-3 h-3" />
              {status?.reason === "byok"
                ? "Running on your own BYOK key — the platform pays nothing for this."
                : "Member benefit · part of your M.O.R.E. membership."}
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );

  if (loadingStatus) {
    return (
      <div className="min-h-screen bg-bone flex items-center justify-center">
        <div className="flex items-center gap-3 text-ink/50">
          <Loader2 className="w-5 h-5 animate-spin text-copper" />
          <span className="text-sm font-medium">Checking your access…</span>
        </div>
      </div>
    );
  }

  return showGate ? gate : chat;
}
