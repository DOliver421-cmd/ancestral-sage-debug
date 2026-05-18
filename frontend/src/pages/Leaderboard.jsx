import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Trophy, Zap } from "lucide-react";

const LEVEL_COLOR = {
  Master: "bg-signal text-ink",
  Craftsman: "bg-copper text-white",
  Journeyman: "bg-ink text-white",
  Apprentice: "badge-outline",
};

export default function Leaderboard() {
  const { user } = useAuth();
  const [board, setBoard] = useState([]);
  const [associates, setAssociates] = useState([]);
  const [filter, setFilter] = useState("");
  const [myXp, setMyXp] = useState(null);

  useEffect(() => {
    api.get("/xp/me").then((r) => setMyXp(r.data)).catch(() => {});
    api.get("/admin/users?role=student&limit=1").catch(() => {});
  }, []);

  useEffect(() => {
    const url = filter ? `/xp/leaderboard?associate=${encodeURIComponent(filter)}` : "/xp/leaderboard";
    api.get(url).then((r) => setBoard(r.data)).catch(() => {});
  }, [filter]);

  useEffect(() => {
    api.get("/admin/users").then((r) => {
      const assocs = [...new Set(r.data.filter((u) => u.associate).map((u) => u.associate))].sort();
      setAssociates(assocs);
    }).catch(() => {});
  }, []);

  const myRank = board.findIndex((e) => e.id === user?.id) + 1;

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-4xl">
        <div className="flex items-start justify-between gap-4 flex-wrap mb-8">
          <div>
            <div className="overline text-copper">Gamification</div>
            <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3">
              <Trophy className="w-8 h-8 text-copper" /> XP Leaderboard
            </h1>
            <p className="text-ink/60 mt-2">Earn XP by completing modules and labs. Rankings reset per cohort.</p>
          </div>
          {myXp && (
            <div className="card-flat p-5 text-right">
              <div className="overline text-copper">Your XP</div>
              <div className="font-heading text-3xl font-black flex items-center gap-2 justify-end">
                <Zap className="w-6 h-6 text-signal" />{myXp.total_xp}
              </div>
              <div className="text-sm text-ink/60 mt-1">{myXp.level} · Rank #{myXp.rank_in_cohort} in cohort</div>
              {myXp.next && (
                <div className="mt-2 w-40 ml-auto">
                  <div className="w-full h-1.5 bg-ink/10">
                    <div className="h-full bg-copper"
                      style={{ width: `${Math.round(((myXp.total_xp - myXp.min) / (myXp.next - myXp.min)) * 100)}%` }} />
                  </div>
                  <div className="text-xs text-ink/50 mt-1">{myXp.next - myXp.total_xp} XP to {myXp.next === 500 ? "Journeyman" : myXp.next === 1500 ? "Craftsman" : "Master"}</div>
                </div>
              )}
            </div>
          )}
        </div>

        {associates.length > 0 && (
          <div className="flex gap-2 mb-6 flex-wrap">
            <button onClick={() => setFilter("")}
              className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border ${!filter ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20"}`}>
              All Cohorts
            </button>
            {associates.map((a) => (
              <button key={a} onClick={() => setFilter(a)}
                className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border ${filter === a ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink/20"}`}>
                {a}
              </button>
            ))}
          </div>
        )}

        <div className="space-y-2">
          {board.length === 0 && (
            <div className="card-flat p-12 text-center">
              <Zap className="w-12 h-12 text-ink/20 mx-auto" />
              <div className="font-heading text-xl font-bold mt-4">No XP yet</div>
              <div className="text-sm text-ink/60 mt-2">Complete modules and labs to earn XP and appear here.</div>
            </div>
          )}
          {board.map((entry, idx) => {
            const isMe = entry.id === user?.id;
            const lvlCls = LEVEL_COLOR[entry.level] || "badge-outline";
            return (
              <div key={entry.id}
                className={`card-flat p-4 flex items-center gap-5 ${isMe ? "border-copper border-2 bg-copper/5" : ""}`}
                data-testid={`lb-row-${idx}`}>
                <div className={`w-10 h-10 flex items-center justify-center font-heading font-black text-lg shrink-0
                  ${idx === 0 ? "bg-signal text-ink" : idx === 1 ? "bg-ink/30 text-ink" : idx === 2 ? "bg-copper text-white" : "bg-bone text-ink/50"}`}>
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-heading font-bold truncate">
                    {entry.full_name}{isMe && <span className="ml-2 text-copper text-xs">(you)</span>}
                  </div>
                  <div className="text-xs text-ink/50">{entry.associate || "Independent"}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 font-bold uppercase ${lvlCls}`}>{entry.level}</span>
                <div className="text-right shrink-0">
                  <div className="font-heading font-black text-xl flex items-center gap-1">
                    <Zap className="w-4 h-4 text-signal" />{entry.total_xp}
                  </div>
                  <div className="text-xs text-ink/50">XP</div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-8 card-flat p-5 bg-bone">
          <div className="overline text-copper mb-2">How to earn XP</div>
          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            {[
              ["Module completed (≥70%)", "100 XP + bonus for high scores"],
              ["Online lab passed", "50 XP + 2× skill points"],
              ["In-person lab approved", "100 XP + 3× skill points"],
            ].map(([title, desc]) => (
              <div key={title} className="p-3 bg-white border border-ink/10">
                <div className="font-bold">{title}</div>
                <div className="text-ink/60 mt-1 text-xs">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
