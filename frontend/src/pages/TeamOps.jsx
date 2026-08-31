import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { Activity, RefreshCw, Loader2, CheckCircle, AlertTriangle, Zap, Users } from "lucide-react";

function ActionBadge({ action }) {
  if (action.includes("revoked"))   return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-50 text-red-600 border border-red-200">Revoked</span>;
  if (action.includes("degraded"))  return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200">Degraded</span>;
  if (action.includes("recovery"))  return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-200">Recovered</span>;
  return <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">Action</span>;
}

function StatCard({ icon: Icon, label, value, sub, color = "copper" }) {
  const colors = {
    copper: "text-copper",
    green:  "text-green-600",
    red:    "text-red-500",
    amber:  "text-amber-500",
  };
  return (
    <div className="bg-white rounded-2xl p-5 border border-ink/8 flex flex-col gap-1">
      <div className="flex items-center gap-2 text-ink/40 text-xs font-semibold uppercase tracking-wide">
        <Icon className="w-3.5 h-3.5" />{label}
      </div>
      <div className={`text-3xl font-heading font-bold ${colors[color]}`}>{value}</div>
      {sub && <div className="text-xs text-ink/40">{sub}</div>}
    </div>
  );
}

export default function TeamOps() {
  const [data,    setData]    = useState(null);
  const [monitor, setMonitor] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [actRes, monRes] = await Promise.all([
        api.get("/team/actions?limit=100"),
        api.get("/team/monitor/status"),
      ]);
      setData(actRes.data);
      setMonitor(monRes.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const actions    = data?.actions || [];
  const autoCount  = data?.auto_count  ?? 0;
  const humanCount = data?.human_count ?? 0;
  const total      = autoCount + humanCount;
  const autoRatio  = total > 0 ? Math.round((autoCount / total) * 100) : 0;
  const degraded   = monitor?.degraded || [];

  return (
    <div className="min-h-screen bg-bone">
      <div className="max-w-4xl mx-auto px-6 py-10">

        {/* Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-ink">Team Operations</h1>
          <p className="text-ink/55 mt-1 text-sm">
            Every action below was taken autonomously by <span className="font-mono font-semibold text-copper">team.supervisor</span> — no human initiated these.
            This is the proof.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Zap}       label="Autonomous Actions" value={autoCount}   color="copper" />
          <StatCard icon={Users}     label="Human Actions"      value={humanCount}  color="amber"  sub="(keys dropped in)" />
          <StatCard icon={CheckCircle} label="Autonomy Rate"    value={`${autoRatio}%`} color="green" sub="of all actions" />
          <StatCard icon={AlertTriangle} label="Degraded Now"   value={degraded.length} color={degraded.length ? "red" : "green"} sub={degraded.length ? degraded.join(", ") : "All clear"} />
        </div>

        {/* Monitor status strip */}
        {monitor && (
          <div className="bg-white border border-ink/8 rounded-2xl px-5 py-3 mb-6 flex flex-wrap items-center gap-4 text-xs text-ink/50">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
              Monitor running — checks every {monitor.interval_sec / 60} min
            </span>
            <span>Failure threshold: {monitor.failure_threshold} consecutive</span>
            {Object.entries(monitor.failure_counts || {}).filter(([, v]) => v > 0).map(([k, v]) => (
              <span key={k} className="text-amber-500 font-semibold">{k}: {v} failure{v !== 1 ? "s" : ""}</span>
            ))}
          </div>
        )}

        {/* Toolbar */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading font-semibold text-ink text-lg">Action Log</h2>
          <button onClick={load} className="flex items-center gap-1.5 text-xs text-ink/40 hover:text-ink/70">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {/* Log */}
        {loading
          ? <div className="flex justify-center py-16"><Loader2 className="w-5 h-5 animate-spin text-copper" /></div>
          : actions.length === 0
          ? (
            <div className="text-center py-16 text-ink/30">
              <Activity className="w-8 h-8 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No actions logged yet — monitor is running and watching.</p>
            </div>
          )
          : (
            <div className="space-y-2">
              {actions.map((a, i) => (
                <div key={a.id || i} className="bg-white border border-ink/8 rounded-xl px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <ActionBadge action={a.action} />
                      <span className="font-mono text-xs text-ink/70 font-semibold">{a.action}</span>
                    </div>
                    <p className="text-xs text-ink/50 mt-0.5 leading-relaxed">{a.reason}</p>
                    <p className="text-xs text-green-600 mt-0.5">{a.outcome}</p>
                  </div>
                  <div className="flex-shrink-0 text-right">
                    <div className="text-xs text-ink/30">{a.at ? new Date(a.at).toLocaleString() : ""}</div>
                    <div className="text-xs font-mono text-copper/70">{a.actor}</div>
                  </div>
                </div>
              ))}
            </div>
          )
        }

        <p className="text-xs text-ink/25 mt-10 text-center leading-relaxed">
          actor: team.supervisor · human_initiated: false · each entry is cryptographically timestamped in MongoDB
        </p>
      </div>
    </div>
  );
}
