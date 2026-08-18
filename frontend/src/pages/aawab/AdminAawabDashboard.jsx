/**
 * AdminAawabDashboard — AAWAB executive oversight.
 *
 * Platform-wide agent wellness: vitality analytics, the full agent registry,
 * certification revocation, and circuit-breaker isolation overrides.
 */

import { useCallback, useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { api } from "../../lib/api";
import { toast } from "sonner";
import {
  HeartPulse, Activity, Award, ShieldAlert, Syringe, RefreshCw, Loader2,
  BadgeCheck, Ban, Unlock, TrendingUp, Users, AlertTriangle, FlaskConical,
} from "lucide-react";

const STATUS_META = {
  active:       { label: "Active",        cls: "bg-green-100 text-green-800" },
  in_treatment: { label: "In Treatment",  cls: "bg-amber-100 text-amber-800" },
  certified:    { label: "Certified",     cls: "bg-emerald-600 text-white" },
  isolated:     { label: "Isolated",      cls: "bg-red-100 text-red-700" },
};

export default function AdminAawabDashboard() {
  const [overview, setOverview] = useState({ agents: [], recent_treatments: [] });
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, rg] = await Promise.all([
        api.get("/aawab/admin/overview"),
        api.get("/aawab/registry"),
      ]);
      setOverview(ov.data);
      setAnalytics(rg.data.analytics);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load AAWAB overview.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const act = async (agentId, action) => {
    const key = `${action}:${agentId}`;
    setBusy(key);
    try {
      await api.post(`/aawab/admin/agents/${agentId}/${action}`);
      toast.success(action === "revoke" ? "Certification revoked." : "Isolation hold overridden — agent restored.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Could not ${action}.`);
    } finally {
      setBusy(null);
    }
  };

  const cards = [
    { label: "Total Agents", value: analytics?.total_agents ?? "—", icon: Users, color: "#2D6A4F" },
    { label: "Certified", value: analytics?.certified ?? "—", icon: Award, color: "#15803d" },
    { label: "In Treatment", value: analytics?.in_treatment ?? "—", icon: Syringe, color: "#d97706" },
    { label: "Isolated", value: analytics?.isolated ?? "—", icon: ShieldAlert, color: "#b91c1c" },
    { label: "Avg CVS", value: analytics?.avg_cvs ?? "—", icon: TrendingUp, color: "#b8860b" },
    { label: "Treatments", value: analytics?.treatments_administered ?? "—", icon: FlaskConical, color: "#4B0082" },
  ];

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-copper">AAWAB · Executive Oversight</p>
            <h1 className="font-heading text-3xl font-bold text-ink mt-1 flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-ink text-signal flex items-center justify-center">
                <HeartPulse className="w-5 h-5" />
              </span>
              Agent Wellness Bureau
            </h1>
            <p className="text-sm text-ink/55 mt-2 max-w-2xl">
              Monitor the health of every agent on the platform, revoke corrupted certifications,
              and override circuit-breaker isolation holds.
            </p>
          </div>
          <button onClick={load} className="px-4 py-2.5 rounded-xl text-sm font-black border-2 border-ink/15 hover:border-copper transition-colors flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-24 text-ink/40">
            <Loader2 className="w-5 h-5 animate-spin text-copper" /> <span className="ml-2 text-sm">Loading bureau data…</span>
          </div>
        ) : (
          <>
            {/* Health cards */}
            <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {cards.map((c) => {
                const Icon = c.icon;
                return (
                  <div key={c.label} className="bg-white border border-ink/10 rounded-2xl p-4 text-center shadow-sm">
                    <span className="w-9 h-9 mx-auto rounded-xl flex items-center justify-center" style={{ background: `${c.color}15`, color: c.color }}>
                      <Icon className="w-4 h-4" />
                    </span>
                    <p className="text-2xl font-black text-ink mt-2">{c.value}</p>
                    <p className="text-[10px] font-black uppercase tracking-widest text-ink/40 mt-0.5">{c.label}</p>
                  </div>
                );
              })}
            </div>

            {/* All agents */}
            <div className="mt-8 bg-white border border-ink/10 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-ink/10 flex items-center gap-2">
                <Activity className="w-4 h-4 text-copper" />
                <h2 className="font-heading font-bold text-ink">All Agents</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[10px] uppercase tracking-widest text-ink/40 border-b border-ink/5">
                      <th className="px-6 py-3">Agent</th>
                      <th className="px-4 py-3">Owner</th>
                      <th className="px-4 py-3">Provider</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">CVS</th>
                      <th className="px-4 py-3">Treatments</th>
                      <th className="px-4 py-3">Last Audit</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.agents.length === 0 && (
                      <tr><td colSpan={8} className="px-6 py-10 text-center text-ink/40">No agents registered yet.</td></tr>
                    )}
                    {overview.agents.map((a) => {
                      const st = STATUS_META[a.status] || STATUS_META.active;
                      return (
                        <tr key={a.agent_id} className="border-b border-ink/5 hover:bg-bone/50">
                          <td className="px-6 py-3">
                            <span className="font-bold text-ink">{a.name}</span>
                            <span className="block text-[11px] text-ink/40 font-mono">{a.agent_id}</span>
                          </td>
                          <td className="px-4 py-3 text-ink/70">{a.owner_name || a.owner_user_id}</td>
                          <td className="px-4 py-3 text-ink/70">{a.model_provider}</td>
                          <td className="px-4 py-3">
                            <span className={`text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full ${st.cls}`}>{st.label}</span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`font-black ${a.cognitive_vitality_score >= 90 ? "text-emerald-700" : a.cognitive_vitality_score >= 70 ? "text-copper" : "text-red-700"}`}>
                              {a.cognitive_vitality_score}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-ink/70">{a.treatments_completed}</td>
                          <td className="px-4 py-3 text-ink/50 text-xs">{a.last_audit_at ? new Date(a.last_audit_at).toLocaleString() : "—"}</td>
                          <td className="px-4 py-3 text-right whitespace-nowrap">
                            {a.status === "certified" && (
                              <button
                                onClick={() => act(a.agent_id, "revoke")}
                                disabled={busy === `revoke:${a.agent_id}`}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-black bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50"
                              >
                                {busy === `revoke:${a.agent_id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Ban className="w-3 h-3" />}
                                Revoke
                              </button>
                            )}
                            {a.status === "isolated" && (
                              <button
                                onClick={() => act(a.agent_id, "override")}
                                disabled={busy === `override:${a.agent_id}`}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-black bg-amber-50 text-amber-800 hover:bg-amber-100 disabled:opacity-50"
                              >
                                {busy === `override:${a.agent_id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Unlock className="w-3 h-3" />}
                                Override
                              </button>
                            )}
                            {a.status !== "certified" && a.status !== "isolated" && (
                              <span className="text-[11px] text-ink/30 flex items-center justify-end gap-1">
                                <AlertTriangle className="w-3 h-3" /> No action
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent treatments */}
            <div className="mt-8 bg-white border border-ink/10 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-ink/10 flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-copper" />
                <h2 className="font-heading font-bold text-ink">Recent Treatments</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[10px] uppercase tracking-widest text-ink/40 border-b border-ink/5">
                      <th className="px-6 py-3">Timestamp</th>
                      <th className="px-4 py-3">Agent</th>
                      <th className="px-4 py-3">Treatment</th>
                      <th className="px-4 py-3">CVS Δ</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview.recent_treatments.length === 0 && (
                      <tr><td colSpan={5} className="px-6 py-10 text-center text-ink/40">No treatments administered yet.</td></tr>
                    )}
                    {overview.recent_treatments.map((t) => (
                      <tr key={t.log_id} className="border-b border-ink/5 hover:bg-bone/50">
                        <td className="px-6 py-3 text-ink/60 text-xs">{new Date(t.timestamp).toLocaleString()}</td>
                        <td className="px-4 py-3 font-mono text-xs text-ink/70">{t.agent_id}</td>
                        <td className="px-4 py-3 font-bold text-ink/80">{t.treatment_type.replace(/_/g, " ")}</td>
                        <td className="px-4 py-3">
                          {(() => {
                            const delta = t.metrics_delta?.cognitive_vitality_score ?? 0;
                            return (
                              <span className={`font-black ${delta >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                                {delta >= 0 ? "+" : ""}{delta}
                              </span>
                            );
                          })()}
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1 text-[11px] font-black text-emerald-700">
                            <BadgeCheck className="w-3.5 h-3.5" /> {t.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
