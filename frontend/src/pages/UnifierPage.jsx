/**
 * /unifier — The Unifier (Arena rebrand).
 *
 * Two personas take independent passes on the user's prompt, then Hybrid NAM
 * (the unified judge model) reviews both and produces one improved answer.
 * The user can swap either competitor persona, save results as plans, and
 * hand a plan off into a real member project (My Projects).
 *
 * All data comes from the real /api/unifier/* endpoints (backend/routers/
 * unifier.py — mounted and server-side gated). No mocks anywhere.
 *
 * Access (mirrors security/unifier_access.py): staff role AND patron+ tier.
 * The same rule is enforced server-side on every endpoint, so the gate here
 * is UX courtesy — the backend is the real gate.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { tierRank } from "../lib/tiers";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import {
  Loader2, Swords, Gavel, Send, RefreshCw, Shuffle, Save, FolderPlus,
  Trash2, MessageSquare, Users, FileText, ChevronDown,
} from "lucide-react";

// Must match backend/security/unifier_access.py.
const UNIFIER_STAFF_ROLES = ["support_staff", "oversight", "admin", "executive_admin"];
const UNIFIER_MIN_TIER = "patron";

function canUseUnifier(user) {
  if (!user) return false;
  const role = String(user.role || "student").toLowerCase();
  if (UNIFIER_STAFF_ROLES.includes(role)) {
    return tierRank(user.feature_tier) >= tierRank(UNIFIER_MIN_TIER);
  }
  return false;
}

export default function UnifierPage() {
  const { user, loading } = useAuth();
  const allowed = canUseUnifier(user);

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-24 text-ink/40">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading the Unifier…
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return (
      <AppShell>
        <GateCard
          icon={<Swords className="w-8 h-8 text-copper" />}
          title="Sign in to use the Unifier"
          body="The Unifier puts two AI personas head-to-head on your idea, then Hybrid NAM judges both and returns one stronger answer. Sign in to continue."
        />
      </AppShell>
    );
  }

  if (!allowed) {
    return (
      <AppShell>
        <GateCard
          icon={<Gavel className="w-8 h-8 text-copper" />}
          title="Patron access required"
          body="The Unifier is a Patron-tier and staff capability: two personas compete on your prompt and Hybrid NAM synthesizes the winning answer. Upgrade to Patron to use it."
        >
          <Link to="/store" className="btn-primary mt-4 inline-flex">See Patron benefits</Link>
        </GateCard>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <BackButton />
      <UnifierWorkspace user={user} />
    </AppShell>
  );
}

function GateCard({ icon, title, body, children }) {
  return (
    <div className="max-w-xl mx-auto mt-16 card-flat p-8 text-center">
      <div className="flex justify-center mb-3">{icon}</div>
      <h1 className="font-heading font-bold text-xl text-ink">{title}</h1>
      <p className="text-sm text-ink/60 mt-2 leading-relaxed">{body}</p>
      {children}
    </div>
  );
}

const FORMATS = [
  ["news", "News segment"],
  ["ai_view", "AI viewpoint"],
  ["soap", "Soap opera"],
  ["gameshow", "Game show"],
  ["programming", "Programming"],
  ["other", "Other"],
];

function UnifierWorkspace({ user }) {
  const [session, setSession] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [plans, setPlans] = useState([]);
  const [exchanges, setExchanges] = useState([]);
  const [message, setMessage] = useState("");
  const [audioOn, setAudioOn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [swapping, setSwapping] = useState(false);
  const [error, setError] = useState("");
  const [showSwap, setShowSwap] = useState(false);
  const [plansPanel, setPlansPanel] = useState(false);
  const bottomRef = useRef(null);

  const loadPlans = useCallback(async () => {
    try {
      const r = await api.get("/unifier/plans");
      setPlans(Array.isArray(r.data) ? r.data : []);
    } catch { /* non-fatal */ }
  }, []);

  const newSession = useCallback(async () => {
    setError("");
    setBusy(true);
    try {
      const r = await api.post("/unifier/sessions");
      setSession(r.data);
      setExchanges([]);
      setShowSwap(false);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const p = await api.get("/unifier/personas");
        setPersonas(p.data.personas || []);
      } catch { /* gate will show instead on 403 */ }
      await loadPlans();
      await newSession();
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [exchanges, busy]);

  const send = async () => {
    const msg = message.trim();
    if (!msg || busy || !session) return;
    setMessage("");
    setBusy(true);
    setError("");
    // Optimistic user bubble; real A/B/judge replies replace it on response.
    const optimistic = { user_message: msg, pending: true };
    setExchanges((prev) => [...prev, optimistic]);
    try {
      const r = await api.post(`/unifier/sessions/${session.id}/chat`, {
        message: msg,
        audio_response: audioOn,
      });
      setExchanges((prev) => {
        const next = [...prev];
        next[next.length - 1] = r.data;
        return next;
      });
    } catch (e) {
      setExchanges((prev) => prev.slice(0, -1));
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  const swapPersonas = async (aId, bId) => {
    if (!session) return;
    setSwapping(true);
    setError("");
    try {
      const r = await api.patch(`/unifier/sessions/${session.id}`, {
        competitor_a: { persona_id: aId },
        competitor_b: { persona_id: bId },
      });
      setSession((s) => ({ ...s, competitor_a: r.data.competitor_a, competitor_b: r.data.competitor_b }));
      setShowSwap(false);
    } catch (e) {
      setError(explain(e));
    } finally {
      setSwapping(false);
    }
  };

  const savePlan = async (exchange) => {
    setError("");
    try {
      await api.post(`/unifier/sessions/${session.id}/plans`, {
        title: (exchange.user_message || "Unifier synthesis").slice(0, 80),
        objective: exchange.judge || exchange.user_message || "",
        notes: `Competitor A (${exchange.competitor_a_label}): ${exchange.competitor_a?.slice(0, 500)}\n\nCompetitor B (${exchange.competitor_b_label}): ${exchange.competitor_b?.slice(0, 500)}`,
        format: "other",
      });
      await loadPlans();
      setPlansPanel(true);
    } catch (e) {
      setError(explain(e));
    }
  };

  const planToProject = async (plan) => {
    setError("");
    try {
      await api.post(`/unifier/plans/${plan.id}/to-project`, {
        category: "launch",
        priority: "normal",
      });
      await loadPlans();
    } catch (e) {
      setError(explain(e));
    }
  };

  const deletePlan = async (plan) => {
    setError("");
    try {
      await api.delete(`/unifier/plans/${plan.id}`);
      await loadPlans();
    } catch (e) {
      setError(explain(e));
    }
  };

  const competitorOptions = personas.filter((p) => !p.locked);
  const activeA = session?.competitor_a?.id;
  const activeB = session?.competitor_b?.id;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <h1 className="font-heading font-bold text-2xl text-ink flex items-center gap-2">
            <Swords className="w-6 h-6 text-copper" /> The Unifier
          </h1>
          <p className="text-sm text-ink/50 mt-0.5">
            Two personas compete. Hybrid NAM judges. One stronger answer comes out.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setPlansPanel((v) => !v)} className="btn-ghost text-sm inline-flex items-center gap-1.5">
            <FileText className="w-4 h-4" /> Plans ({plans.length})
          </button>
          <button onClick={newSession} disabled={busy} className="btn-ghost text-sm inline-flex items-center gap-1.5">
            <RefreshCw className="w-4 h-4" /> New session
          </button>
        </div>
      </div>

      {error && (
        <div className="card-flat p-3 mb-4 text-sm text-red-700 bg-red-50 border border-red-200">{error}</div>
      )}

      {/* Competitor lineup */}
      <div className="card-flat p-4 mb-5 flex flex-wrap items-center gap-3">
        <Users className="w-4 h-4 text-copper" />
        <div className="text-sm">
          <span className="font-semibold text-ink">{session?.competitor_a?.label || "—"}</span>
          <span className="text-ink/40 mx-2">vs</span>
          <span className="font-semibold text-ink">{session?.competitor_b?.label || "—"}</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <label className="text-xs text-ink/50 flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={audioOn} onChange={(e) => setAudioOn(e.target.checked)} />
            Speak the verdict
          </label>
          <button onClick={() => setShowSwap((v) => !v)} className="btn-ghost text-sm inline-flex items-center gap-1.5">
            <Shuffle className="w-4 h-4" /> Swap personas
          </button>
        </div>
        {showSwap && (
          <div className="w-full grid md:grid-cols-2 gap-3 pt-3 border-t border-ink/10">
            {["competitor_a", "competitor_b"].map((slot) => (
              <label key={slot} className="text-sm">
                <span className="block text-xs font-semibold uppercase tracking-wide text-ink/50 mb-1">
                  {slot === "competitor_a" ? "Competitor A" : "Competitor B"}
                </span>
                <div className="relative">
                  <select
                    value={slot === "competitor_a" ? activeA : activeB}
                    onChange={(e) => {
                      const other = slot === "competitor_a" ? activeB : activeA;
                      const mine = e.target.value;
                      if (mine === other) { setError("Pick two different personas."); return; }
                      swapPersonas(slot === "competitor_a" ? mine : other, slot === "competitor_a" ? other : mine);
                    }}
                    disabled={swapping}
                    className="w-full appearance-none rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink pr-8"
                  >
                    {competitorOptions.map((p) => (
                      <option key={p.id} value={p.id}>{p.label}</option>
                    ))}
                  </select>
                  <ChevronDown className="w-4 h-4 text-ink/40 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </label>
            ))}
            {swapping && <span className="text-xs text-ink/40 self-center"><Loader2 className="w-3.5 h-3.5 animate-spin inline mr-1" />Swapping…</span>}
          </div>
        )}
      </div>

      {/* Plans panel */}
      {plansPanel && (
        <div className="card-flat p-4 mb-5">
          <h2 className="font-heading font-bold text-sm uppercase tracking-wide text-ink/60 mb-3">Saved plans</h2>
          {plans.length === 0 && <p className="text-sm text-ink/40">No plans saved yet. Save a verdict below to create one.</p>}
          <div className="space-y-3">
            {plans.map((plan) => (
              <div key={plan.id} className="border border-ink/10 rounded-lg p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-semibold text-sm text-ink truncate">{plan.title}</div>
                    <div className="text-xs text-ink/70 mt-0.5" style={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{plan.objective}</div>
                    <div className="text-xs mt-1">
                      <span className={plan.status === "in_project" ? "text-green-700 font-medium" : "text-ink/40"}>
                        {plan.status === "in_project" ? "In My Projects" : "Draft"}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {plan.status !== "in_project" && (
                      <button onClick={() => planToProject(plan)} className="btn-primary text-xs inline-flex items-center gap-1">
                        <FolderPlus className="w-3.5 h-3.5" /> Make project
                      </button>
                    )}
                    <button onClick={() => deletePlan(plan)} title="Delete plan" className="p-1.5 text-ink/40 hover:text-red-600">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {plan.project_id && (
                  <Link to="/my-projects" className="text-xs text-copper hover:underline mt-1 inline-block">
                    Open in My Projects →
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      <div className="space-y-5 min-h-[200px]">
        {exchanges.length === 0 && !busy && (
          <div className="card-flat p-8 text-center text-sm text-ink/40">
            <MessageSquare className="w-6 h-6 mx-auto mb-2 text-ink/20" />
            Put a topic on the table. Both personas answer it, then Hybrid NAM hands down the improved verdict.
          </div>
        )}
        {exchanges.map((x, i) => (
          <ExchangeCard key={i} x={x} onSave={savePlan} canSave={!x.pending} />
        ))}
        {busy && (
          <div className="card-flat p-4 flex items-center gap-2 text-sm text-ink/50">
            <Loader2 className="w-4 h-4 animate-spin text-copper" />
            Both personas are answering and Hybrid NAM is judging — this takes a few seconds…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div className="sticky bottom-4 mt-5">
        <div className="card-flat p-3 flex items-end gap-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={2}
            maxLength={4000}
            placeholder="Put a topic on the table…"
            className="flex-1 resize-none rounded-md border border-ink/15 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-copper/40"
          />
          <button onClick={send} disabled={busy || !message.trim()} className="btn-primary inline-flex items-center gap-1.5 disabled:opacity-40">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Send
          </button>
        </div>
        <p className="text-[11px] text-ink/30 mt-1 px-1">Enter to send · Shift+Enter for a new line · 4,000 characters max</p>
      </div>
    </div>
  );
}

function ExchangeCard({ x, onSave, canSave }) {
  return (
    <div className="card-flat p-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="text-sm font-semibold text-ink flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-copper" />
          {x.user_message}
        </div>
        {canSave && (
          <button onClick={() => onSave(x)} className="btn-ghost text-xs inline-flex items-center gap-1 shrink-0">
            <Save className="w-3.5 h-3.5" /> Save as plan
          </button>
        )}
      </div>
      {x.pending ? (
        <div className="text-sm text-ink/40 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Working…</div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 gap-3 mb-3">
            <PersonaBubble label={x.competitor_a_label} text={x.competitor_a} tone="a" />
            <PersonaBubble label={x.competitor_b_label} text={x.competitor_b} tone="b" />
          </div>
          <div className="border-t border-ink/10 pt-3">
            <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-copper mb-1.5">
              <Gavel className="w-3.5 h-3.5" /> Hybrid NAM — Verdict
            </div>
            <p className="text-sm text-ink/80 whitespace-pre-wrap leading-relaxed">{x.judge}</p>
            {x.audio_url && <audio controls src={x.audio_url} className="mt-2 w-full max-w-md" />}
          </div>
        </>
      )}
    </div>
  );
}

function PersonaBubble({ label, text, tone }) {
  return (
    <div className={`rounded-lg p-3 text-sm leading-relaxed ${tone === "a" ? "bg-ink/5" : "bg-copper/5"}`}>
      <div className="text-xs font-bold uppercase tracking-wide text-ink/40 mb-1">{label || "Persona"}</div>
      <p className="text-ink/80 whitespace-pre-wrap">{text}</p>
    </div>
  );
}

function explain(e) {
  return e?.response?.data?.detail || e?.message || "Something went wrong. Try again.";
}
