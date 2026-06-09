import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ARCADE_GAMES, CATEGORY_COLORS } from "../lib/arcadeGames";
import { Trophy, Zap } from "lucide-react";
import ArcadeGuide from "../components/arcade/ArcadeGuide";

const CATEGORIES = ["All", "Culture", "Finance", "Music", "Faith", "Trades"];

export default function ArcadeLanding() {
  const { user } = useAuth();
  const [category, setCategory] = useState("All");
  const [leaderboard, setLeaderboard] = useState([]);
  const [userScores, setUserScores] = useState({});

  useEffect(() => {
    if (user) {
      api.get("/arcade/leaderboard").then((r) => setLeaderboard(r.data?.top || [])).catch(() => {});
      api.get("/arcade/my-scores").then((r) => setUserScores(r.data || {})).catch(() => {});
    }
  }, [user]);

  const filtered = category === "All" ? ARCADE_GAMES : ARCADE_GAMES.filter((g) => g.category === category);
  const featured = ARCADE_GAMES.find((g) => g.featured);

  return (
    <AppShell>
      <div className="px-6 lg:px-10 py-10 max-w-6xl">

        {/* Hero */}
        <div
          className="relative overflow-hidden p-8 mb-10"
          style={{
            background: "linear-gradient(135deg, #0a0a0f 0%, #1a0a00 50%, #0a0a0f 100%)",
            border: "2px solid #b8860b",
            boxShadow: "0 0 40px rgba(184,134,11,0.3), inset 0 0 60px rgba(184,134,11,0.05)",
          }}
        >
          {/* Scanline overlay */}
          <div className="absolute inset-0 pointer-events-none" style={{
            backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px)",
          }} />
          <div className="relative z-10">
            <div className="font-mono text-xs tracking-widest mb-3" style={{ color: "#b8860b" }}>
              ▶ INSERT COIN · FREE TO PLAY · WAI INSTITUTE
            </div>
            <h1
              className="font-heading font-black leading-none mb-3"
              style={{
                fontSize: "clamp(2.5rem, 6vw, 5rem)",
                color: "#ffd700",
                textShadow: "0 0 20px rgba(255,215,0,0.6), 0 0 40px rgba(255,215,0,0.3), 3px 3px 0 #b8860b",
                letterSpacing: "0.05em",
              }}
            >
              THE ARCADE
            </h1>
            <p className="text-white/70 max-w-xl text-sm leading-relaxed">
              Mission-aligned games built for the community. Learn. Play. Earn XP. Every game sharpens something real.
            </p>
            {user && (
              <div className="mt-4 flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded" style={{ background: "rgba(184,134,11,0.2)", border: "1px solid #b8860b" }}>
                  <Zap className="w-4 h-4" style={{ color: "#ffd700" }} />
                  <span className="font-mono text-xs font-bold" style={{ color: "#ffd700" }}>PLAY TO EARN XP</span>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">

            {/* Featured game */}
            {featured && (
              <div className="mb-8">
                <div className="overline text-copper mb-3">Featured Game</div>
                <Link
                  to={`/arcade/${featured.slug}`}
                  className="block group"
                  data-testid={`arcade-featured-${featured.slug}`}
                >
                  <div
                    className="p-6 transition-all"
                    style={{
                      background: "linear-gradient(135deg, #0f0f1a, #1a0f00)",
                      border: "2px solid #b8860b",
                      boxShadow: "0 0 20px rgba(184,134,11,0.2)",
                    }}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="text-4xl mb-3">{featured.emoji}</div>
                        <div className="font-heading text-2xl font-black text-white group-hover:text-yellow-400 transition-colors">
                          {featured.title}
                        </div>
                        <p className="text-white/60 text-sm mt-2 max-w-md leading-relaxed">{featured.description}</p>
                        <div className="flex items-center gap-3 mt-4">
                          <span className={CATEGORY_COLORS[featured.category]}>{featured.category}</span>
                          <span className="font-mono text-xs font-bold text-signal">+{featured.xpReward} XP</span>
                        </div>
                      </div>
                      <div
                        className="shrink-0 px-6 py-3 font-mono font-black text-sm uppercase tracking-widest transition-all"
                        style={{
                          background: "#b8860b",
                          color: "#0a0a0f",
                          boxShadow: "0 4px 0 #7a5c0a",
                          transform: "translateY(0)",
                        }}
                      >
                        PLAY NOW ▶
                      </div>
                    </div>
                  </div>
                </Link>
              </div>
            )}

            {/* Category filter */}
            <div className="flex gap-2 flex-wrap mb-6">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  onClick={() => setCategory(c)}
                  className={`font-mono text-xs font-bold px-3 py-1.5 uppercase tracking-widest border transition-colors ${
                    category === c
                      ? "bg-copper text-white border-copper"
                      : "border-ink/20 text-ink/60 hover:border-copper hover:text-copper"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>

            {/* Game grid */}
            <div className="grid sm:grid-cols-2 gap-4">
              {filtered.map((game) => (
                <Link
                  key={game.slug}
                  to={`/arcade/${game.slug}`}
                  className="block group"
                  data-testid={`arcade-card-${game.slug}`}
                >
                  <div
                    className="p-5 h-full transition-all"
                    style={{
                      background: "#0f0f1a",
                      border: "1px solid rgba(184,134,11,0.3)",
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#b8860b"; e.currentTarget.style.boxShadow = "0 0 12px rgba(184,134,11,0.2)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(184,134,11,0.3)"; e.currentTarget.style.boxShadow = "none"; }}
                  >
                    <div className="text-3xl mb-3">{game.emoji}</div>
                    <div className="font-heading font-bold text-white group-hover:text-yellow-400 transition-colors">{game.title}</div>
                    <p className="text-white/50 text-xs mt-2 leading-relaxed line-clamp-2">{game.description}</p>
                    <div className="flex items-center justify-between mt-4 pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                      <span className={CATEGORY_COLORS[game.category]}>{game.category}</span>
                      <span className="font-mono text-xs font-bold text-signal">+{game.xpReward} XP</span>
                    </div>
                    {userScores[game.slug] !== undefined && (
                      <div className="mt-2 font-mono text-xs text-white/40">
                        Best: {userScores[game.slug].toLocaleString()} pts
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Leaderboard sidebar */}
          <aside className="space-y-4">
            <div
              className="p-5"
              style={{ background: "#0f0f1a", border: "1px solid rgba(184,134,11,0.4)" }}
              data-testid="arcade-leaderboard"
            >
              <div className="flex items-center gap-2 mb-4">
                <Trophy className="w-4 h-4 text-yellow-500" />
                <div className="font-mono font-black text-xs uppercase tracking-widest text-yellow-500">High Scores</div>
              </div>
              {leaderboard.length === 0 ? (
                <div className="text-white/30 text-xs font-mono">No scores yet. Be first.</div>
              ) : (
                <ol className="space-y-2">
                  {leaderboard.slice(0, 10).map((entry, i) => (
                    <li key={entry.user_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-black w-5" style={{ color: i === 0 ? "#ffd700" : i === 1 ? "#c0c0c0" : i === 2 ? "#cd7f32" : "rgba(255,255,255,0.3)" }}>
                          {i + 1}
                        </span>
                        <span className="text-white/70 text-xs truncate max-w-28">{entry.full_name}</span>
                      </div>
                      <span className="font-mono text-xs font-bold text-signal">{entry.total_score.toLocaleString()}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <ArcadeGuide />

            <div
              className="p-5"
              style={{ background: "#0f0f1a", border: "1px solid rgba(184,134,11,0.4)" }}
            >
              <div className="font-mono text-xs font-black uppercase tracking-widest text-yellow-500 mb-3">More Games Coming</div>
              <ul className="space-y-2 text-white/40 text-xs font-mono">
                <li>⬜ Black History Trivia</li>
                <li>⬜ Fix Your Block (sim)</li>
                <li>⬜ Budget Challenge</li>
                <li>⬜ Tool ID Speed Round</li>
                <li>⬜ Beat the Sample</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
