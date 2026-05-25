import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Shield, ThumbsUp, AlertTriangle, Ban, Clock, RefreshCw } from "lucide-react";

export default function ModerationAnalytics() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(true);

  const load = async () => {
    setBusy(true);
    try {
      const r = await api.get("/more/admin/moderation-stats");
      setData(r.data);
    } catch {
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-6 h-6 text-copper" />
              <span className="overline text-copper">M.O.R.E.</span>
            </div>
            <h1 className="font-heading text-4xl font-bold">Moderation Analytics</h1>
            <p className="text-ink/60 mt-2">Oliver Guardian moderation activity and trends.</p>
          </div>
          <button onClick={load} className="btn-primary inline-flex items-center gap-2 text-sm">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {busy && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => <div key={i} className="h-24 bg-ink/5 rounded-xl animate-pulse" />)}
          </div>
        )}

        {!busy && data && (
          <>
            {/* Summary cards */}
            <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: "Total Moderated", value: data.total_moderated || 0, icon: Shield, color: "text-blue-600", bg: "bg-blue-50" },
                { label: "Approved", value: data.approved || 0, icon: ThumbsUp, color: "text-green-600", bg: "bg-green-50" },
                { label: "Flagged", value: data.flagged || 0, icon: AlertTriangle, color: "text-orange-600", bg: "bg-orange-50" },
                { label: "Blocked", value: data.blocked || 0, icon: Ban, color: "text-red-600", bg: "bg-red-50" },
              ].map((s) => (
                <div key={s.label} className="bg-white rounded-xl border border-ink/10 p-5">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${s.bg}`}>
                      <s.icon className={`w-5 h-5 ${s.color}`} />
                    </div>
                    <div>
                      <p className="text-xs text-ink/50 uppercase">{s.label}</p>
                      <p className="text-2xl font-bold font-mono text-ink">{s.value}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Recent moderation log */}
            {data.recent_log?.length > 0 && (
              <div className="mt-8">
                <h2 className="font-heading text-xl font-bold mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-copper" /> Recent Moderation Actions
                </h2>
                <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                  <div className="divide-y divide-ink/10">
                    {data.recent_log.map((entry, i) => (
                      <div key={i} className="flex items-center justify-between p-4 text-sm">
                        <div className="flex items-center gap-3 min-w-0">
                          <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                            entry.decision === "approve" ? "bg-green-50 text-green-700" :
                            entry.decision === "block" ? "bg-red-50 text-red-700" :
                            entry.decision === "warn" ? "bg-orange-50 text-orange-700" :
                            "bg-ink/10 text-ink/60"
                          }`}>
                            {entry.decision || entry.action || "—"}
                          </span>
                          <span className="text-ink/70 truncate">{entry.content_type || entry.type || "content"}</span>
                        </div>
                        <span className="text-xs text-ink/50 shrink-0">
                          {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Pending queue */}
            {data.pending_count > 0 && (
              <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-xl flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                <p className="text-sm text-orange-800">
                  <strong>{data.pending_count}</strong> item{data.pending_count !== 1 ? "s" : ""} pending review in the moderation queue.
                </p>
              </div>
            )}
          </>
        )}

        {!busy && !data && (
          <div className="mt-12 text-center text-ink/50">
            <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>Moderation data unavailable.</p>
            <p className="text-sm mt-1">The moderation stats endpoint may not be available.</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}
