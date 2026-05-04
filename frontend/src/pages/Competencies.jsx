import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import { Target } from "lucide-react";

export default function Competencies() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/competencies").then((r) => setData(r.data)); }, []);
  if (!data) return <LoadingState label="Competencies" />;

  const maxPoints = Math.max(100, ...Object.values(data.progress).map((p) => p.points));

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Skills Matrix</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3"><Target className="w-8 h-8 text-copper" /> Your Competency Matrix</h1>
        <p className="text-ink/60 mt-2 max-w-2xl">Eight competency areas. Every lab you pass deposits skill points into its matching competencies — earning a badge at 100 points.</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mt-8">
          <Stat label="Total Skill Points" value={data.total_points} />
          <Stat label="Labs Completed" value={data.total_labs} />
          <Stat label="Badges Earned" value={Object.values(data.progress).filter((p) => p.points >= 100).length} />
          <Stat label="Competency Areas" value={data.competencies.length} />
        </div>

        <div className="mt-10 space-y-4">
          {data.competencies.map((c) => {
            const p = data.progress[c.key] || { points: 0, labs: 0 };
            const pct = Math.min(100, (p.points / 100) * 100);
            const earned = p.points >= 100;
            return (
              <div key={c.key} className="card-flat p-6" data-testid={`comp-${c.key}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-heading text-xl font-bold flex items-center gap-3">
                      {c.name}
                      {earned && <span className="badge-signal">Badge Earned</span>}
                    </div>
                    <div className="text-sm text-ink/60 mt-1">{c.description}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-heading text-3xl font-black text-copper">{p.points}</div>
                    <div className="overline text-ink/60">points · {p.labs} labs</div>
                  </div>
                </div>
                <div className="mt-4 w-full h-3 bg-ink/10">
                  <div className="h-full bg-copper transition-all duration-500" style={{ width: `${pct}%` }} />
                </div>
                <div className="mt-1 flex justify-between text-xs font-mono text-ink/60">
                  <span>0</span><span className="text-copper font-bold">{p.points}/100 to next badge</span><span>100</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card-flat p-5">
      <div className="font-heading text-3xl font-black">{value}</div>
      <div className="overline text-ink/60 mt-1">{label}</div>
    </div>
  );
}
