import { Suspense, useState } from "react";
import { useParams, Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { ARCADE_GAMES, CATEGORY_COLORS, GAME_COMPONENT_MAP } from "../lib/arcadeGames";
import { ArrowLeft, Zap } from "lucide-react";

export default function ArcadeGame() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const game = ARCADE_GAMES.find((g) => g.slug === slug);
  const GameComponent = GAME_COMPONENT_MAP[slug];

  const handleGameEnd = async ({ score }) => {
    if (!user) {
      toast.info("Sign in to save your score and earn XP.");
      return;
    }
    setSubmitting(true);
    try {
      const r = await api.post("/arcade/scores", { game_slug: slug, score });
      setResult(r.data);
      toast.success(`+${r.data.xp_awarded} XP earned!`);
    } catch {
      toast.error("Score not saved — try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!game || !GameComponent) {
    return (
      <AppShell>
        <div className="px-10 py-20 text-center max-w-lg mx-auto">
          <div className="text-5xl mb-4">👾</div>
          <h2 className="font-heading text-2xl font-bold mb-2">Game not found</h2>
          <Link to="/arcade" className="btn-copper inline-flex items-center gap-2 mt-4">
            <ArrowLeft className="w-4 h-4" /> Back to Arcade
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="px-6 lg:px-10 py-8 max-w-5xl">
        <div className="flex items-center justify-between mb-6">
          <Link to="/arcade" className="inline-flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-ink/60 hover:text-copper">
            <ArrowLeft className="w-4 h-4" /> The Arcade
          </Link>
          <div className="flex items-center gap-3">
            <span className={CATEGORY_COLORS[game.category]}>{game.category}</span>
            <span className="font-mono text-xs font-bold text-signal flex items-center gap-1">
              <Zap className="w-3 h-3" /> +{game.xpReward} XP
            </span>
          </div>
        </div>

        <div className="mb-6">
          <div className="text-3xl mb-2">{game.emoji}</div>
          <h1 className="font-heading text-3xl font-black">{game.title}</h1>
          <p className="text-ink/60 text-sm mt-1">{game.tagline}</p>
        </div>

        {result && (
          <div
            className="mb-6 p-4 flex items-center justify-between"
            style={{ background: "rgba(0,200,100,0.08)", border: "1px solid rgba(0,200,100,0.3)" }}
            data-testid="game-result"
          >
            <div>
              <div className="font-mono font-black text-signal">SCORE: {result.score?.toLocaleString()}</div>
              {submitting && <div className="text-xs text-ink/50 font-mono mt-1">Saving...</div>}
            </div>
            <div className="text-right">
              <div className="font-mono font-black text-yellow-500">+{result.xp_awarded} XP</div>
              <div className="text-xs text-ink/50 font-mono">Total: {result.new_total_xp} XP</div>
            </div>
          </div>
        )}

        <Suspense fallback={<LoadingState label="Game" />}>
          <GameComponent onGameEnd={handleGameEnd} />
        </Suspense>
      </div>
    </AppShell>
  );
}
