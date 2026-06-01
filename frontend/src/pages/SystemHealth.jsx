import { useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Activity, Database, Cpu, DollarSign, Users, AlertCircle, CheckCircle, XCircle } from "lucide-react";

export default function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [costs, setCosts] = useState(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [h, c] = await Promise.allSettled([
          api.get("/health"),
          api.get("/admin/ai-costs?days=7"),
        ]);
        if (h.status === "fulfilled") setHealth(h.value.data);
        if (c.status === "fulfilled") setCosts(c.value.data);
      } catch {
        // partial data still useful
      } finally {
        setBusy(false);
      }
    })();
  }, []);

  const StatCard = ({ label, value, icon: Icon, good }) => (
    <div className="bg-white rounded-xl border border-ink/10 p-5">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${good !== false ? "bg-green-50" : "bg-red-50"}`}>
          <Icon className={`w-5 h-5 ${good !== false ? "text-green-600" : "text-red-600"}`} />
        </div>
        <div>
          <p className="text-xs text-ink/50 uppercase tracking-wider">{label}</p>
          <p className="text-lg font-bold font-mono text-ink">{value ?? "—"}</p>
        </div>
      </div>
    </div>
  );

  const healthChecks = health ? [
    { label: "API Status", value: health.status || health.app || "ok", good: true },
    { label: "Database", value: health.db || "ok", good: health.db !== "error" },
    { label: "AI Services", value: health.ai || "unknown", good: health.ai !== "error" },
    { label: "Stripe", value: health.stripe || "unknown", good: health.stripe !== "error" },
    { label: "Email", value: health.email || "unknown", good: health.email !== "error" },
  ] : [];

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-6 h-6 text-copper" />
          <span className="overline text-copper">Operations</span>
        </div>
        <h1 className="font-heading text-4xl font-bold">System Health</h1>
        <p className="text-ink/60 mt-2">Real-time platform health and AI cost overview.</p>

        {busy && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1,2,3,4,5,6].map(i => <div key={i} className="h-24 bg-ink/5 rounded-xl animate-pulse" />)}
          </div>
        )}

        {!busy && (
          <>
            {/* Health checks */}
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {healthChecks.map((c) => (
                <StatCard key={c.label} {...c} icon={c.good ? CheckCircle : XCircle} />
              ))}
            </div>

            {/* Cost summary */}
            {costs && (
              <div className="mt-8">
                <h2 className="font-heading text-xl font-bold flex items-center gap-2 mb-4">
                  <DollarSign className="w-5 h-5 text-copper" /> AI Cost Summary (7 days)
                </h2>
                <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
                  {costs.total && (
                    <div className="p-4 border-b border-ink/10 bg-ink/5">
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-xs text-ink/50 uppercase">Total Cost</p>
                          <p className="text-lg font-bold font-mono text-ink">${(costs.total.total_cost || 0).toFixed(4)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-ink/50 uppercase">Total Calls</p>
                          <p className="text-lg font-bold font-mono text-ink">{costs.total.total_calls || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-ink/50 uppercase">Total Tokens</p>
                          <p className="text-lg font-bold font-mono text-ink">{(costs.total.total_tokens || 0).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  {costs.costs?.length > 0 && (
                    <div className="divide-y divide-ink/10">
                      {costs.costs.map((c) => (
                        <div key={c._id} className="flex items-center justify-between p-4 text-sm">
                          <div>
                            <p className="font-medium text-ink capitalize">{c._id}</p>
                            <p className="text-xs text-ink/50">{c.models?.join(", ") || "—"}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-mono text-ink font-bold">${c.total_cost?.toFixed(4) || "0"}</p>
                            <p className="text-xs text-ink/50">{c.total_calls} calls · {(c.total_tokens || 0).toLocaleString()} tokens</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* No data */}
            {!health && !costs && (
              <div className="mt-12 text-center text-ink/50">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>Could not load health data.</p>
                <p className="text-sm mt-1">Check that the backend is running.</p>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
