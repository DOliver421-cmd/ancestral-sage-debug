import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Brain, Check, Lightbulb, X } from "lucide-react";

// Daily puzzle wired to the real backend:
//   GET  /api/puzzles/next   -> { done, level, solved_count, requires_login_to_earn, puzzle:{id,level,points,question,hints_shown[],hints_available} }
//   POST /api/puzzles/answer -> correct: { correct, points_awarded, duplicate, status, next_level }
//                               wrong:   { correct:false, try_again, hint, hints_shown[] }
// Backend uses free-text answers + progressive hints (NOT multiple choice).
// Points vary per puzzle (10–75). On a correct, points-earning solve we cycle to
// the next puzzle after 3.2s and tell the parent to refresh partnership status.
export default function PuzzleCard({ onSolved }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [hints, setHints] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    setResult(null);
    setAnswer("");
    setHints([]);
    api
      .get("/puzzles/next")
      .then((r) => {
        setData(r.data);
        setHints(r.data?.puzzle?.hints_shown || []);
      })
      .catch(() => setData(null));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!answer.trim() || submitting || !data?.puzzle) return;
    setSubmitting(true);
    try {
      const r = await api.post("/puzzles/answer", { puzzle_id: data.puzzle.id, answer });
      setResult(r.data);
      if (r.data.correct) {
        if (r.data.points_awarded > 0 && onSolved) onSolved();
        setTimeout(load, 3200);
      } else {
        if (r.data.hints_shown) setHints(r.data.hints_shown);
        setAnswer("");
      }
    } catch {
      /* global axios interceptor surfaces errors */
    } finally {
      setSubmitting(false);
    }
  };

  if (!data) return null;

  if (data.done) {
    return (
      <div className="card-flat p-6" data-testid="puzzle-card">
        <div className="overline text-copper flex items-center gap-2">
          <Brain className="w-4 h-4" /> Daily Puzzle
        </div>
        <div className="font-heading text-xl font-bold mt-3">
          {data.message || "You've solved them all."}
        </div>
      </div>
    );
  }

  const p = data.puzzle;
  return (
    <div className="card-flat p-6" data-testid="puzzle-card">
      <div className="flex items-center justify-between">
        <div className="overline text-copper flex items-center gap-2">
          <Brain className="w-4 h-4" /> Daily Puzzle · Level {p.level}
        </div>
        <span className="badge-copper">+{p.points} pts</span>
      </div>

      <div className="font-heading text-lg font-semibold mt-4 leading-snug">{p.question}</div>

      {hints.length > 0 && (
        <div className="mt-4 space-y-1">
          {hints.map((h, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-ink/70">
              <Lightbulb className="w-4 h-4 text-signal mt-0.5 shrink-0" />
              <span>{h}</span>
            </div>
          ))}
        </div>
      )}

      {result?.correct ? (
        <div
          className="mt-5 p-4 bg-signal/20 border border-signal flex items-center gap-3"
          data-testid="puzzle-correct"
        >
          <Check className="w-5 h-5 text-ink shrink-0" />
          <div className="font-bold text-ink">
            {result.points_awarded > 0
              ? `Correct! +${result.points_awarded} points${result.status?.tier ? ` — now ${result.status.tier}.` : "."}`
              : result.requires_login_to_earn
              ? "Correct! Create a free account to bank these points toward membership."
              : "Correct!"}
          </div>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-5">
          {result && result.correct === false && (
            <div
              className="mb-3 flex items-center gap-2 text-sm text-destructive"
              data-testid="puzzle-wrong"
            >
              <X className="w-4 h-4 shrink-0" /> Not quite — here's another hint. Try again.
            </div>
          )}
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Your answer…"
            data-testid="puzzle-input"
            className="border border-ink/20 px-4 py-3 w-full"
          />
          <div className="flex items-center justify-between mt-3">
            <div className="text-xs text-ink/60 font-mono">Solved: {data.solved_count ?? 0}</div>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-sm disabled:opacity-50"
              data-testid="puzzle-submit"
            >
              {submitting ? "Checking…" : "Submit"}
            </button>
          </div>
          {!user && (
            <div className="text-xs text-ink/60 mt-3">
              Playing as a guest —{" "}
              <a className="text-copper font-bold" href="/register">
                create a free account
              </a>{" "}
              to earn points.
            </div>
          )}
        </form>
      )}
    </div>
  );
}
