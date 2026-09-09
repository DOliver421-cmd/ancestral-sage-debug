/**
 * /arena — The Arena: Unified Competition + Synthesis Workflow
 *
 * 4 personas go through 5 graded rounds of self-competition on a project.
 * A Commissioner scores each round. 2 of 4 personas can be swapped.
 * The highest-scoring output is handed to Hybrid NAM for mission alignment.
 *
 * Phases: SETUP → SELECT_PERSONAS → ROUNDS → SCORING → RESULTS → HANDOFF
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import {
  Loader2, Swords, Gavel, Send, RefreshCw, Shuffle, Save, FolderPlus,
  Trash2, Users, FileText, ChevronDown, Award, Target, ArrowRight,
  CheckCircle2, AlertTriangle, Zap, Crown,
} from "lucide-react";

const PHASES = {
  SETUP: "SETUP",
  SELECT: "SELECT_PERSONAS",
  ROUNDS: "ROUNDS",
  SCORING: "SCORING",
  RESULTS: "RESULTS",
  HANDOFF: "HANDOFF",
};

const MAX_ROUNDS = 5;
const MAX_PERSONAS = 4;
const SWAPPABLE = 2;

function explain(err) {
  const d = err?.response?.data?.detail;
  return typeof d === "string" ? d : err?.message || "Request failed";
}

export default function CompetitionArena() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-24 text-ink/40">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading the Arena…
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return (
      <AppShell>
        <GateCard
          icon={<Swords className="w-8 h-8 text-copper" />}
          title="Sign in to use the Arena"
          body="The Arena puts 4 AI personas through 5 rounds of self-competition on your project, then hands the best output to Hybrid NAM for mission alignment."
        />
      </AppShell>
    );
  }

  const role = String(user.role || "").toLowerCase();
  const isStaff = ["instructor", "admin", "executive_admin", "support_staff", "oversight"].includes(role);
  const isPatron = ["patron", "platinum", "executive"].includes(user.feature_tier);
  if (!isStaff && !isPatron) {
    return (
      <AppShell>
        <GateCard
          icon={<Gavel className="w-8 h-8 text-copper" />}
          title="Patron access required"
          body="The Arena requires a staff role or Patron tier."
        >
          <Link to="/store" className="btn-primary mt-4 inline-flex">See Patron benefits</Link>
        </GateCard>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <BackButton />
      <ArenaWorkspace user={user} />
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

function ArenaWorkspace({ user }) {
  const [phase, setPhase] = useState(PHASES.SETUP);
  const [personas, setPersonas] = useState([]);
  const [project, setProject] = useState(null);
  const [session, setSession] = useState(null);
  const [rounds, setRounds] = useState([]);
  const [results, setResults] = useState(null);
  const [handoff, setHandoff] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showSwap, setShowSwap] = useState(false);
  const [swapSlot, setSwapSlot] = useState(null);
  const [scoreInput, setScoreInput] = useState({});
  const bottomRef = useRef(null);

  // Load available personas
  useEffect(() => {
    api.get("/arena/personas")
      .then(r => setPersonas(r.data.personas || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [rounds, results, phase]);

  // ── Phase: SETUP ─────────────────────────────────────────────────────────
  const createProject = async (title, description, criteria) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.post("/arena/projects", {
        title,
        description,
        success_criteria: criteria,
        assigned_by: "human",
      });
      setProject(r.data);
      setPhase(PHASES.SELECT);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  // ── Phase: SELECT_PERSONAS ───────────────────────────────────────────────
  const startSession = async (personaIds) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.post("/arena/sessions", {
        project_id: project.id,
        persona_ids: personaIds,
      });
      setSession(r.data);
      setPhase(PHASES.ROUNDS);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  const swapPersona = async (slotIndex, newPersonaId) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.patch(`/arena/sessions/${session.id}/swap`, {
        slot_index: slotIndex,
        new_persona_id: newPersonaId,
      });
      setSession(s => ({ ...s, personas: r.data.personas }));
      setShowSwap(false);
      setSwapSlot(null);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  // ── Phase: ROUNDS ────────────────────────────────────────────────────────
  const runRound = async () => {
    setBusy(true);
    setError("");
    try {
      const r = await api.post(`/arena/sessions/${session.id}/rounds`);
      setRounds(prev => [...prev, ...r.data.rounds]);
      setSession(s => ({
        ...s,
        current_round: r.data.round,
        status: r.data.status,
        best_score: r.data.best_score,
        best_persona_id: r.data.best_persona,
      }));
      if (r.data.status === "COMPLETED") {
        setPhase(PHASES.RESULTS);
        loadResults();
      }
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  // ── Phase: SCORING ───────────────────────────────────────────────────────
  const submitScore = async (roundId, score, note, scorer) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.post("/arena/scores", {
        round_id: roundId,
        score,
        note,
        scorer,
      });
      setRounds(prev => prev.map(rd =>
        rd.id === roundId
          ? { ...rd, final_score: r.data.final_score, [`${scorer}_score`]: { score, note } }
          : rd
      ));
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  // ── Phase: RESULTS ───────────────────────────────────────────────────────
  const loadResults = async () => {
    try {
      const r = await api.get(`/arena/sessions/${session.id}/results`);
      setResults(r.data);
    } catch (e) {
      setError(explain(e));
    }
  };

  // ── Phase: HANDOFF ───────────────────────────────────────────────────────
  const handoffToNAM = async (notes) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.post("/arena/handoff", {
        session_id: session.id,
        mission_alignment_notes: notes,
      });
      setHandoff(r.data);
      setPhase(PHASES.HANDOFF);
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  // ── Load existing session ────────────────────────────────────────────────
  const loadSession = async (sessionId) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.get(`/arena/sessions/${sessionId}`);
      setSession(r.data);
      setRounds(r.data.rounds || []);
      setProject({ id: r.data.project_id, title: r.data.project_title });
      if (r.data.status === "COMPLETED") {
        setPhase(PHASES.RESULTS);
        loadResults();
      } else if (r.data.status === "HANDED_OFF") {
        setPhase(PHASES.HANDOFF);
      } else if (r.data.rounds_completed > 0) {
        setPhase(PHASES.ROUNDS);
      }
    } catch (e) {
      setError(explain(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="font-heading font-bold text-3xl text-ink mb-2 flex items-center gap-3">
        <Swords className="w-8 h-8 text-copper" /> The Arena
      </h1>
      <p className="text-ink/60 mb-8">
        4 personas · 5 rounds of self-competition · Commissioner scoring · Hybrid NAM synthesis
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Phase indicator */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {Object.values(PHASES).map(p => (
          <span
            key={p}
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
              phase === p
                ? "bg-copper text-white"
                : "bg-ink/5 text-ink/40"
            }`}
          >
            {p.replace("_", " ")}
          </span>
        ))}
      </div>

      {/* ── SETUP PHASE ──────────────────────────────────────────────────── */}
      {phase === PHASES.SETUP && (
        <ProjectSetup onSubmit={createProject} busy={busy} />
      )}

      {/* ── SELECT PERSONAS PHASE ────────────────────────────────────────── */}
      {phase === PHASES.SELECT && (
        <PersonaSelect
          personas={personas}
          onSubmit={startSession}
          busy={busy}
        />
      )}

      {/* ── ROUNDS PHASE ─────────────────────────────────────────────────── */}
      {phase === PHASES.ROUNDS && (
        <RoundsPhase
          session={session}
          rounds={rounds}
          onRunRound={runRound}
          onSwap={swapPersona}
          showSwap={showSwap}
          setShowSwap={setShowSwap}
          swapSlot={swapSlot}
          setSwapSlot={setSwapSlot}
          personas={personas}
          busy={busy}
        />
      )}

      {/* ── RESULTS PHASE ────────────────────────────────────────────────── */}
      {phase === PHASES.RESULTS && (
        <ResultsPhase
          results={results}
          rounds={rounds}
          onHandoff={() => setPhase(PHASES.SCORING)}
          busy={busy}
        />
      )}

      {/* ── SCORING PHASE ────────────────────────────────────────────────── */}
      {phase === PHASES.SCORING && (
        <ScoringPhase
          rounds={rounds}
          scoreInput={scoreInput}
          setScoreInput={setScoreInput}
          onSubmitScore={submitScore}
          onComplete={() => { setPhase(PHASES.RESULTS); loadResults(); }}
          busy={busy}
        />
      )}

      {/* ── HANDOFF PHASE ────────────────────────────────────────────────── */}
      {phase === PHASES.HANDOFF && (
        <HandoffPhase handoff={handoff} session={session} />
      )}

      <div ref={bottomRef} />
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ProjectSetup({ onSubmit, busy }) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [criteria, setCriteria] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() || !desc.trim()) return;
    onSubmit(title.trim(), desc.trim(), criteria.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="card-flat p-6 space-y-4">
      <h2 className="font-heading font-bold text-xl text-ink flex items-center gap-2">
        <FileText className="w-5 h-5 text-copper" /> Assign a Project
      </h2>
      <p className="text-sm text-ink/60">
        Define what the personas will work on. You or Hybrid NAM assigns the project.
      </p>
      <div>
        <label className="block text-sm font-bold text-ink mb-1">Project Title</label>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm"
          placeholder="e.g. Community impact strategy for Q4"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-bold text-ink mb-1">Description</label>
        <textarea
          value={desc}
          onChange={e => setDesc(e.target.value)}
          className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm h-24"
          placeholder="What is this project about? What should the personas focus on?"
          required
        />
      </div>
      <div>
        <label className="block text-sm font-bold text-ink mb-1">Success Criteria (optional)</label>
        <textarea
          value={criteria}
          onChange={e => setCriteria(e.target.value)}
          className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm h-16"
          placeholder="How will you judge if the output is good?"
        />
      </div>
      <button
        type="submit"
        disabled={busy || !title.trim() || !desc.trim()}
        className="btn-primary flex items-center gap-2"
      >
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
        Create Project & Select Personas
      </button>
    </form>
  );
}

function PersonaSelect({ personas, onSubmit, busy }) {
  const [selected, setSelected] = useState([]);

  const toggle = (id) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : prev.length < MAX_PERSONAS ? [...prev, id] : prev
    );
  };

  return (
    <div className="card-flat p-6">
      <h2 className="font-heading font-bold text-xl text-ink flex items-center gap-2 mb-2">
        <Users className="w-5 h-5 text-copper" /> Select 4 Personas
      </h2>
      <p className="text-sm text-ink/60 mb-4">
        The first 2 are locked. The last 2 can be swapped between rounds.
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {personas.map(p => {
          const isSelected = selected.includes(p.id);
          const idx = selected.indexOf(p.id);
          const isLocked = idx >= 0 && idx < SWAPPABLE;
          return (
            <button
              key={p.id}
              onClick={() => toggle(p.id)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                isSelected
                  ? isLocked
                    ? "border-copper bg-copper/5"
                    : "border-green-600 bg-green-50"
                  : "border-ink/10 hover:border-ink/30"
              } ${selected.length >= MAX_PERSONAS && !isSelected ? "opacity-40" : ""}`}
            >
              <div className="text-sm font-bold text-ink">{p.label}</div>
              {isSelected && (
                <div className="text-xs text-ink/50 mt-1">
                  {isLocked ? "🔒 Locked" : `Slot ${idx + 1} (swappable)`}
                </div>
              )}
            </button>
          );
        })}
      </div>
      <button
        onClick={() => onSubmit(selected)}
        disabled={busy || selected.length < 2}
        className="btn-primary flex items-center gap-2"
      >
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Swords className="w-4 h-4" />}
        Start Arena ({selected.length}/{MAX_PERSONAS} selected)
      </button>
    </div>
  );
}

function RoundsPhase({ session, rounds, onRunRound, onSwap, showSwap, setShowSwap, swapSlot, setSwapSlot, personas, busy }) {
  const currentRound = session?.current_round || 0;
  const isComplete = session?.status === "COMPLETED";

  return (
    <div className="space-y-6">
      {/* Status bar */}
      <div className="card-flat p-4 flex items-center justify-between">
        <div>
          <div className="font-bold text-ink">{session?.project_title}</div>
          <div className="text-sm text-ink/60">
            Round {currentRound}/{MAX_ROUNDS} · {session?.personas?.length || 0} personas
          </div>
        </div>
        <div className="flex gap-2">
          {!isComplete && (
            <button
              onClick={() => setShowSwap(!showSwap)}
              className="btn-outline text-sm flex items-center gap-1"
            >
              <Shuffle className="w-4 h-4" /> Swap Persona
            </button>
          )}
          {!isComplete && (
            <button
              onClick={onRunRound}
              disabled={busy}
              className="btn-primary text-sm flex items-center gap-1"
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Run Round {currentRound + 1}
            </button>
          )}
        </div>
      </div>

      {/* Persona swap panel */}
      {showSwap && (
        <SwapPanel
          session={session}
          personas={personas}
          onSwap={onSwap}
          busy={busy}
          onClose={() => { setShowSwap(false); setSwapSlot(null); }}
          swapSlot={swapSlot}
          setSwapSlot={setSwapSlot}
        />
      )}

      {/* Round cards */}
      {rounds.map((r, i) => (
        <RoundCard key={r.id} round={r} index={i} />
      ))}

      {isComplete && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" /> All 5 rounds complete! View results below.
        </div>
      )}
    </div>
  );
}

function RoundCard({ round, index }) {
  const [expanded, setExpanded] = useState(false);
  const score = round.final_score || round.commissioner_score?.total || 0;

  return (
    <div className="card-flat p-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className="bg-copper text-white text-xs font-bold px-2 py-1 rounded">
            R{round.round_num}
          </span>
          <span className="font-bold text-ink text-sm">{round.persona_label}</span>
          <span className="text-xs text-ink/50">
            {round.output?.split(" ").length || 0} words
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold ${score >= 70 ? "text-green-600" : score >= 40 ? "text-amber-600" : "text-red-600"}`}>
            {score}
          </span>
          {expanded ? <ChevronDown className="w-4 h-4 text-ink/40" /> : <ChevronDown className="w-4 h-4 text-ink/40 rotate-[-90deg]" />}
        </div>
      </div>
      {expanded && (
        <div className="mt-4 border-t border-ink/5 pt-4">
          <div className="bg-ink/[0.02] rounded-lg p-4 text-sm text-ink/80 whitespace-pre-wrap max-h-64 overflow-y-auto">
            {round.output}
          </div>
          {round.commissioner_score && (
            <div className="mt-3 text-xs text-ink/50">
              Commissioner: {round.commissioner_score.total} · Clarity: {round.commissioner_score.clarity} · Criteria: {round.commissioner_score.criteria_alignment} · Improvement: {round.commissioner_score.improvement}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SwapPanel({ session, personas, onSwap, busy, onClose, swapSlot, setSwapSlot }) {
  const swappablePersonas = session?.personas?.filter(p => !p.locked) || [];
  const existingIds = new Set(session?.personas?.map(p => p.persona_id) || []);
  const available = personas.filter(p => !existingIds.has(p.id));

  return (
    <div className="card-flat p-4 border-copper/30">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-ink flex items-center gap-2">
          <Shuffle className="w-4 h-4 text-copper" /> Swap a Persona
        </h3>
        <button onClick={onClose} className="text-ink/40 hover:text-ink text-sm">✕</button>
      </div>
      <p className="text-xs text-ink/50 mb-3">Pick which slot to replace, then choose a new persona.</p>
      <div className="grid grid-cols-2 gap-3 mb-3">
        {swappablePersonas.map(p => (
          <button
            key={p.persona_id}
            onClick={() => setSwapSlot(p)}
            className={`p-3 rounded-lg border text-left text-sm ${
              swapSlot?.persona_id === p.persona_id
                ? "border-copper bg-copper/5"
                : "border-ink/10 hover:border-ink/20"
            }`}
          >
            <div className="font-bold">{p.label}</div>
            <div className="text-xs text-ink/40">Slot {session.personas.indexOf(p) + 1}</div>
          </button>
        ))}
      </div>
      {swapSlot && (
        <div>
          <div className="text-xs text-ink/50 mb-2">Replace with:</div>
          <div className="grid grid-cols-3 gap-2">
            {available.map(p => (
              <button
                key={p.id}
                onClick={() => onSwap(session.personas.indexOf(swapSlot), p.id)}
                disabled={busy}
                className="p-2 rounded border border-ink/10 hover:border-green-500 text-xs text-left"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ResultsPhase({ results, rounds, onHandoff, busy }) {
  if (!results) {
    return (
      <div className="card-flat p-6 text-center">
        <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
        <p className="text-sm text-ink/60">Loading results…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card-flat p-6">
        <h2 className="font-heading font-bold text-xl text-ink flex items-center gap-2 mb-4">
          <Award className="w-5 h-5 text-copper" /> Ranked Results
        </h2>
        <div className="space-y-3">
          {results.ranked_outputs?.map((r, i) => (
            <div key={r.id} className={`p-4 rounded-lg border ${i === 0 ? "border-copper bg-copper/5" : "border-ink/10"}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`text-lg font-bold ${i === 0 ? "text-copper" : "text-ink/40"}`}>
                    #{i + 1}
                  </span>
                  <div>
                    <div className="font-bold text-ink text-sm">{r.persona_label}</div>
                    <div className="text-xs text-ink/50">Round {r.round_num} · {r.output?.split(" ").length || 0} words</div>
                  </div>
                </div>
                <span className={`text-lg font-bold ${r.final_score >= 70 ? "text-green-600" : r.final_score >= 40 ? "text-amber-600" : "text-red-600"}`}>
                  {r.final_score}
                </span>
              </div>
              {i === 0 && (
                <div className="mt-3 bg-ink/[0.02] rounded p-3 text-sm text-ink/70 max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {r.output}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {results.can_handoff && (
        <button
          onClick={onHandoff}
          disabled={busy}
          className="btn-primary flex items-center gap-2"
        >
          <Crown className="w-4 h-4" /> Score & Hand Off to Hybrid NAM
        </button>
      )}
    </div>
  );
}

function ScoringPhase({ rounds, scoreInput, setScoreInput, onSubmitScore, onComplete, busy }) {
  const [notes, setNotes] = useState("");

  const handleSubmit = async () => {
    // Submit human scores for all rounds
    for (const r of rounds) {
      const val = parseInt(scoreInput[r.id]) || 50;
      await onSubmitScore(r.id, val, notes, "human");
    }
    onComplete();
  };

  return (
    <div className="card-flat p-6 space-y-4">
      <h2 className="font-heading font-bold text-xl text-ink flex items-center gap-2">
        <Gavel className="w-5 h-5 text-copper" /> Score Each Round
      </h2>
      <p className="text-sm text-ink/60">
        Commissioner auto-scores are already applied. Add your scores to refine the ranking.
      </p>
      <div className="space-y-3">
        {rounds.map(r => (
          <div key={r.id} className="flex items-center gap-3 p-3 rounded-lg border border-ink/10">
            <span className="text-xs font-bold text-ink/50 w-16">R{r.round_num} {r.persona_label?.split(" ")[0]}</span>
            <input
              type="range"
              min="0"
              max="100"
              value={scoreInput[r.id] || 50}
              onChange={e => setScoreInput(prev => ({ ...prev, [r.id]: e.target.value }))}
              className="flex-1"
            />
            <span className="text-sm font-bold text-ink w-8 text-right">{scoreInput[r.id] || 50}</span>
          </div>
        ))}
      </div>
      <div>
        <label className="block text-sm font-bold text-ink mb-1">Your Notes (optional)</label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm h-16"
          placeholder="What did you notice? What improved?"
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={busy}
        className="btn-primary flex items-center gap-2"
      >
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
        Submit Scores & View Results
      </button>
    </div>
  );
}

function HandoffPhase({ handoff, session }) {
  if (!handoff) {
    return (
      <div className="card-flat p-6 text-center">
        <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
        <p className="text-sm text-ink/60">Hybrid NAM is evaluating mission alignment…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center gap-2">
        <CheckCircle2 className="w-5 h-5" /> Handoff complete! Hybrid NAM has evaluated mission alignment.
      </div>

      <div className="card-flat p-6">
        <h2 className="font-heading font-bold text-xl text-ink flex items-center gap-2 mb-4">
          <Crown className="w-5 h-5 text-copper" /> Mission-Aligned Output
        </h2>
        <div className="text-sm text-ink/60 mb-3">
          Best persona: <strong>{handoff.best_persona_label}</strong> · Score: <strong>{handoff.best_score}</strong>
        </div>
        <div className="bg-ink/[0.02] rounded-lg p-4 text-sm text-ink/80 whitespace-pre-wrap max-h-96 overflow-y-auto">
          {handoff.nam_mission_aligned_output}
        </div>
      </div>

      <div className="card-flat p-6">
        <h3 className="font-bold text-ink mb-2">Original Best Output</h3>
        <div className="bg-ink/[0.02] rounded-lg p-4 text-sm text-ink/70 whitespace-pre-wrap max-h-64 overflow-y-auto">
          {handoff.original_output}
        </div>
      </div>

      <div className="flex gap-3">
        <Link to="/nam" className="btn-outline flex items-center gap-2">
          <Crown className="w-4 h-4" /> Open Hybrid NAM
        </Link>
        <Link to="/my-projects" className="btn-outline flex items-center gap-2">
          <FolderPlus className="w-4 h-4" /> View Projects
        </Link>
      </div>
    </div>
  );
}

// Named export for embedded use in BusinessOffice
export function CompetitionArenaContent({ embedded }) {
  const { user, loading } = useAuth();
  if (loading || !user) return null;
  return <ArenaWorkspace user={user} />;
}
