import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import { Brain, ArrowRight, Lock, Sparkles, Flame, Snowflake, Sun } from "lucide-react";

const LEVEL_COLOR = { hot: "bg-signal text-ink", warm: "bg-copper text-white", cold: "bg-ink/10 text-ink/60" };
const LEVEL_ICON = { hot: Flame, warm: Sun, cold: Snowflake };

export default function Adaptive() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/adaptive/me").then((r) => setData(r.data)); }, []);
  if (!data) return <LoadingState label="Personalized Path" />;

  const heatmapEntries = Object.entries(data.heatmap);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Adaptive Learning Engine</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><Brain className="w-8 h-8 text-copper" /> Your Learning Path</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">A live read on your strengths and gaps — and the next four moves that will earn you the most ground.</p>

        {/* Heatmap */}
        <div className="card-flat p-6 mt-8" data-testid="heatmap">
          <div className="overline text-copper mb-4">Skill Heatmap</div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {heatmapEntries.map(([key, h]) => {
              const Icon = LEVEL_ICON[h.level];
              return (
                <div key={key} className={`p-4 ${LEVEL_COLOR[h.level]}`} data-testid={`heat-${key}`}>
                  <div className="flex items-center gap-2"><Icon className="w-4 h-4" /><span className="overline text-xs">{h.level}</span></div>
                  <div className="font-heading font-bold mt-2 text-sm">{h.name}</div>
                  <div className="font-mono text-2xl font-black mt-1">{h.points}</div>
                  <div className="text-xs opacity-80 mt-1">{h.labs_passed} labs</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recommendations */}
        <div className="mt-10">
          <h2 className="font-heading text-2xl font-bold mb-4">Recommended Next Moves</h2>
          {data.recommendations.length === 0 ? (
            <div className="card-flat p-8 text-center text-ink/60 text-sm">You're up to date — keep going on your current track.</div>
          ) : (
            <div className="space-y-3">
              {data.recommendations.map((r, i) => (
                <Link key={i} to={r.type === "module_review" ? `/modules/${r.slug}` : `/labs/${r.slug}`}
                  className="card-flat p-5 flex items-center justify-between group" data-testid={`rec-${r.slug || i}`}>
                  <div>
                    <div className="overline text-copper">
                      {r.type === "lab" ? `LAB · ${r.track.toUpperCase()}` : "MODULE REVIEW"} {r.skill_points ? `· ${r.skill_points}pts` : ""}
                    </div>
                    <div className="font-heading text-lg font-bold mt-1 group-hover:text-copper transition-colors">{r.title}</div>
                    <div className="text-sm text-ink/60 mt-1">{r.reason}</div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-copper" />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* AI topic */}
        {data.ai_topic && (
          <Link to="/ai" className="block card-flat p-5 mt-6 bg-ink text-white hover:bg-ink/90 transition-colors" data-testid="ai-suggest">
            <div className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-signal" />
              <div>
                <div className="overline text-signal">AI Tutor Suggestion</div>
                <div className="font-heading font-bold mt-1">{data.ai_topic.title}</div>
                <div className="text-xs text-white/70 mt-1">{data.ai_topic.reason}</div>
              </div>
            </div>
          </Link>
        )}

        {/* Locked labs */}
        {data.locked_labs.length > 0 && (
          <div className="mt-10">
            <h2 className="font-heading text-2xl font-bold mb-4">Locked — Prerequisites Required</h2>
            <div className="space-y-2">
              {data.locked_labs.map((l) => (
                <div key={l.slug} className="card-flat p-4 flex items-center gap-4 opacity-70" data-testid={`locked-${l.slug}`}>
                  <Lock className="w-5 h-5 text-ink/50" />
                  <div className="flex-1">
                    <div className="font-heading font-bold">{l.title}</div>
                    <div className="text-xs text-ink/60 mt-1 font-mono">Requires: {l.missing_prereqs.join(", ")}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
