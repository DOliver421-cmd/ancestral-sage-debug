import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Brain, Check, X, Flame, Trophy, Star } from "lucide-react";

// Daily puzzle — A/B/C/D multiple choice. Choices come from the backend
// (GET /puzzles/next), the answer is verified server-side (POST /puzzles/answer),
// and partnership points are awarded on a correct, logged-in solve. Wrong answers
// reveal the correct one and deduct nothing. Cycles to the next puzzle after 3.2s.
export default function PuzzleCard({ onSolved }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [result, setResult] = useState(null);
  const [picked, setPicked] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [stats, setStats] = useState({ streak: 0, correct: 0, points: 0 });

  const load = useCallback(() => {
    setResult(null);
    setPicked(null);
    setSubmitting(false);
    api.get("/puzzles/next").then((r) => setData(r.data)).catch(() => setData(null));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const choose = async (choice) => {
    if (submitting || result || !data?.puzzle) return;
    setPicked(choice);
    setSubmitting(true);
    try {
      const r = await api.post("/puzzles/answer", { puzzle_id: data.puzzle.id, answer: choice });
      setResult(r.data);
      setStats((s) =>
        r.data.correct
          ? { streak: s.streak + 1, correct: s.correct + 1, points: s.points + (r.data.points_awarded || 0) }
          : { streak: 0, correct: s.correct, points: s.points }
      );
      if (r.data.correct && r.data.points_awarded > 0 && onSolved) onSolved();
      setTimeout(load, 3200);
    } catch {
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
        <div className="font-heading text-xl font-bold mt-3">{data.message || "You've solved them all."}</div>
      </div>
    );
  }

  const p = data.puzzle;
  const choices = data.choices || [];
  const letters = ["A", "B", "C", "D", "E"];

  return (
    <div className="card-flat p-6" data-testid="puzzle-card">
      <div className="flex items-center justify-between">
        <div className="overline text-copper flex items-center gap-2">
          <Brain className="w-4 h-4" /> Daily Puzzle · Level {p.level}
        </div>
        <span className="badge-copper">+{p.points} pts</span>
      </div>

      <div className="font-heading text-lg font-semibold mt-4 leading-snug">{p.question}</div>

      <div className="grid gap-2 mt-4">
        {choices.map((c, i) => {
          const isPicked = picked === c;
          const isCorrectChoice =
            result &&
            (result.correct
              ? isPicked
              : result.correct_answer && c.toLowerCase() === String(result.correct_answer).toLowerCase());
          const isWrongPick = result && isPicked && !result.correct;
          let cls = "border-ink/15 hover:border-copper";
          if (isCorrectChoice) cls = "border-signal bg-signal/20";
          else if (isWrongPick) cls = "border-destructive bg-destructive/10";
          return (
            <button
              key={i}
              onClick={() => choose(c)}
              disabled={!!result || submitting}
              data-testid={`puzzle-choice-${i}`}
              className={`text-left px-4 py-3 border rounded transition-colors flex items-center gap-3 disabled:cursor-default ${cls}`}
            >
              <span className="font-heading font-black text-copper w-5 shrink-0">{letters[i]}</span>
              <span className="text-sm text-ink">{c}</span>
              {isCorrectChoice && <Check className="w-4 h-4 text-ink ml-auto shrink-0" />}
              {isWrongPick && <X className="w-4 h-4 text-destructive ml-auto shrink-0" />}
            </button>
          );
        })}
      </div>

      {result && (
        <div className="mt-4 text-sm font-bold" data-testid="puzzle-result">
          {result.correct ? (
            <span className="text-ink">
              Correct!{" "}
              {result.points_awarded > 0
                ? `+${result.points_awarded} pts`
                : result.requires_login_to_earn
                ? "— sign in to bank points"
                : ""}{" "}
              {result.status?.tier ? `· ${result.status.tier}` : ""}
            </span>
          ) : (
            <span className="text-ink/70">
              Answer: <span className="text-ink">{result.correct_answer}</span>. Next one coming…
            </span>
          )}
        </div>
      )}

      <div className="flex items-center gap-4 mt-5 pt-4 border-t border-ink/10 text-xs">
        <span className="flex items-center gap-1 text-ink/70"><Flame className="w-3.5 h-3.5 text-copper" /> Streak {stats.streak}</span>
        <span className="flex items-center gap-1 text-ink/70"><Trophy className="w-3.5 h-3.5 text-copper" /> Correct {stats.correct}</span>
        <span className="flex items-center gap-1 text-ink/70"><Star className="w-3.5 h-3.5 text-copper" /> {stats.points} pts</span>
        {!user && (
          <span className="ml-auto text-ink/50">
            Guest — <a href="/register" className="text-copper font-bold">join</a> to earn
          </span>
        )}
      </div>
    </div>
  );
}
