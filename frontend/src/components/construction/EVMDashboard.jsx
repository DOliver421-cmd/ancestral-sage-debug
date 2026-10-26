import { useState, useEffect } from "react";
import { Activity, TrendingUp, TrendingDown, CheckCircle2, AlertCircle, DollarSign, Clock } from "lucide-react";
import { constructionApi } from "@/lib/construction-pm";
import { toast } from "sonner";

export default function EVMDashboard({ projectId }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const r = await constructionApi.getEvmMetrics(projectId);
        setMetrics(r.data);
      } catch {
        toast.error("Failed to load EVM metrics");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId]);

  if (loading) return <div className="h-64 flex items-center justify-center text-ink/40">Loading EVM…</div>;
  if (!metrics) return null;

  const { spi, cpi, ev, ac, pv, cv, sv, scheduled_percent_complete, items } = metrics;
  const spiStatus = spi != null && spi >= 1 ? "on" : "off";
  const cpiStatus = cpi != null && cpi >= 1 ? "on" : "off";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-copper" />
          <h3 className="font-bold text-lg text-ink">Earned Value Dashboard</h3>
        </div>
        <div className="text-xs text-ink/50">Real-time SPI / CPI performance</div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Schedule Perf. Index (SPI)" value={spi != null ? spi.toFixed(2) : "—"} trend={spiStatus} icon={<TrendingUp className="w-5 h-5" />} />
        <KpiCard title="Cost Perf. Index (CPI)" value={cpi != null ? cpi.toFixed(2) : "—"} trend={cpiStatus} icon={<DollarSign className="w-5 h-5" />} />
        <KpiCard title="Cost Variance (hrs)" value={cv != null ? cv.toFixed(1) : "—"} trend={cv >= 0 ? "on" : "off"} icon={<Clock className="w-5 h-5" />} />
      </div>

      {/* Gauge row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Gauge title="Schedule Variance (hrs)" value={sv != null ? sv.toFixed(1) : "—"} good={sv != null && sv >= 0} />
        <Gauge title="Planned % Complete" value={(scheduled_percent_complete * 100).toFixed(1)} good={true} suffix="%" />
      </div>

      {/* Item-level breakdown */}
      <div className="bg-white border border-ink/10 rounded-xl p-4">
        <h4 className="font-bold text-sm text-ink mb-3">Line-Item Percent Complete</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink/10">
                <th className="px-3 py-2 text-left text-xs font-bold text-ink/60">CSI Code</th>
                <th className="px-3 py-2 text-left text-xs font-bold text-ink/60">Description</th>
                <th className="px-3 py-2 text-right text-xs font-bold text-ink/60">Qty</th>
                <th className="px-3 py-2 text-right text-xs font-bold text-ink/60">Installed</th>
                <th className="px-3 py-2 text-right text-xs font-bold text-ink/60">% Complete</th>
                <th className="px-3 py-2 text-right text-xs font-bold text-ink/60">Earned Hrs</th>
              </tr>
            </thead>
            <tbody>
              {(items || []).map((it) => (
                <tr key={it.item_id} className="border-b border-ink/5">
                  <td className="px-3 py-2 text-xs font-mono text-ink/70">{it.csi_code}</td>
                  <td className="px-3 py-2 text-xs text-ink/70 truncate max-w-[160px]">{it.description}</td>
                  <td className="px-3 py-2 text-right text-xs text-ink/60">{it.quantity}</td>
                  <td className="px-3 py-2 text-right text-xs text-ink/60">{it.installed}</td>
                  <td className="px-3 py-2 text-right text-xs font-medium">
                    <span className={`font-bold ${it.percent_complete >= 1 ? "text-green-700" : it.percent_complete > 0.5 ? "text-amber-700" : "text-ink/60"}`}>
                      {(it.percent_complete * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right text-xs text-ink/60">{it.earned_hours?.toFixed(1) ?? "—"}</td>
                </tr>
              ))}
              {(!items || items.length === 0) && (
                <tr>
                  <td colSpan="6" className="px-3 py-4 text-center text-ink/40 text-xs">No line items logged yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-xs text-ink/40">
        SPI = Earned Value ÷ Planned Value · CPI = Earned Value ÷ Actual Cost · Values above 1.0 = ahead of schedule / under budget.
      </div>
    </div>
  );
}

function KpiCard({ title, value, trend, icon }) {
  const good = trend === "on";
  return (
    <div className="bg-white border border-ink/10 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs text-ink/50">{title}</div>
        {icon}
      </div>
      <div className="text-2xl font-bold text-ink">{value}</div>
      <div className={`text-xs font-bold ${good ? "text-green-700" : "text-red-700"}`}>
        {good ? "On track" : "Below baseline"}
      </div>
    </div>
  );
}

function Gauge({ title, value, good, suffix }) {
  return (
    <div className="bg-white border border-ink/10 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-ink/50">{title}</span>
        {good ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <AlertCircle className="w-4 h-4 text-amber-600" />}
      </div>
      <div className="text-2xl font-bold text-ink">{value}{suffix}</div>
    </div>
  );
}
