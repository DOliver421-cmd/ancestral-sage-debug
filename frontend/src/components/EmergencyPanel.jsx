import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import {
  Zap, AlertTriangle, CheckCircle2, XCircle, RefreshCw,
  ArrowLeftRight, Server, Database, Wifi, Activity,
} from "lucide-react";

// ── helpers ──────────────────────────────────────────────────────────────────────
function ts(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

const STATUS_COLORS = {
  on:       "#10b981",
  standby:  "#f59e0b",
  off:      "#6b7280",
  tripped:  "#ef4444",
  fault:    "#7f1d1d",
};

const STATUS_LABELS = {
  on:       "ON",
  standby:  "STANDBY",
  off:      "OFF",
  tripped:  "TRIPPED",
  fault:    "FAULT",
};

const ORIGIN_LABELS = {
  primary:   "Primary (Railway)",
  backup:    "Backup (Home Server)",
  emergency: "Emergency (Standalone UI)",
};

const ORIGIN_COLORS = {
  primary:   "#10b981",
  backup:    "#f59e0b",
  emergency: "#ef4444",
};

// ── Breaker Switch ───────────────────────────────────────────────────────────────
function BreakerSwitch({ status, onClick }) {
  const isOn = status === "on";
  const isTripped = status === "tripped" || status === "fault";
  return (
    <button
      onClick={onClick}
      title={`Click to toggle (currently ${status})`}
      className="relative w-10 h-14 rounded-sm border-2 cursor-pointer transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-amber-400"
      style={{
        background: isOn
          ? "linear-gradient(180deg, #1e3a1e 0%, #2d5a2d 40%, #1e3a1e 100%)"
          : isTripped
          ? "linear-gradient(180deg, #3a1a1a 0%, #5a2d2d 40%, #3a1a1a 100%)"
          : "linear-gradient(180deg, #2a2a2a 0%, #3d3d3d 40%, #2a2a2a 100%)",
        borderColor: isOn ? "#10b981" : isTripped ? "#ef4444" : "#6b7280",
        boxShadow: isOn
          ? "inset 0 2px 4px rgba(0,0,0,0.3), 0 0 6px rgba(16,185,129,0.3)"
          : "inset 0 2px 4px rgba(0,0,0,0.3)",
      }}
    >
      {/* Toggle handle */}
      <div
        className="absolute left-1/2 w-6 h-3 rounded-sm transition-all duration-200"
        style={{
          background: isOn
            ? "linear-gradient(180deg, #10b981, #059669)"
            : "linear-gradient(180deg, #6b7280, #4b5563)",
          top: isOn ? "6px" : "calc(100% - 14px)",
          left: "calc(50% - 12px)",
          boxShadow: isOn ? "0 0 4px rgba(16,185,129,0.5)" : "none",
        }}
      />
      {/* Trip indicator */}
      {isTripped && (
        <div className="absolute inset-0 flex items-center justify-center">
          <AlertTriangle className="w-4 h-4 text-red-500" />
        </div>
      )}
    </button>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────────
export default function EmergencyPanel({ onClose }) {
  const [panel, setPanel] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(null);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [panelR, healthR] = await Promise.allSettled([
        api.get("/exec/panel"),
        api.get("/exec/panel/health"),
      ]);
      if (panelR.status === "fulfilled") setPanel(panelR.value.data);
      if (healthR.status === "fulfilled") setHealth(healthR.value.data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Failed to load panel");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggle = async (breakerId) => {
    setToggling(breakerId);
    setMessage(null);
    setError(null);
    try {
      const r = await api.post("/exec/panel/toggle", { breaker_id: breakerId });
      setMessage(`${breakerId}: ${r.data.status}`);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || "Toggle failed");
    } finally {
      setToggling(null);
    }
  };

  const doFailover = async (target) => {
    setToggling("failover");
    setMessage(null);
    setError(null);
    try {
      const r = await api.post("/exec/failover", { target, reason: "Manual from panel" });
      setMessage(`Failover → ${r.data.active}`);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || "Failover failed");
    } finally {
      setToggling(null);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  const breakers = panel?.breakers || {};
  const gateway = panel?.gateway || {};
  const sortedBreakers = Object.entries(breakers).sort((a, b) => a[1].order - b[1].order);

  return (
    <div className="rounded-2xl overflow-hidden border shadow-lg"
      style={{ background: "#1a1a1a", borderColor: "#333", color: "#e5e5e5" }}>

      {/* ── Panel Header ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-3 border-b"
        style={{ background: "#2a2a2a", borderColor: "#444" }}>
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-amber-400" />
          <div>
            <span className="font-heading font-extrabold text-base text-amber-400 tracking-wider">
              EMERGENCY BREAKER PANEL
            </span>
            <span className="text-xs ml-3 opacity-60">Gateway: {ORIGIN_LABELS[gateway.active_origin] || gateway.active_origin}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {health && (
            <span className="text-xs font-bold font-mono px-2 py-1 rounded"
              style={{
                background: health.health_pct >= 80 ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)",
                color: health.health_pct >= 80 ? "#10b981" : "#ef4444",
              }}>
              {health.health_pct}% HEALTHY
            </span>
          )}
          <button onClick={load} disabled={loading}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
            style={{ background: "#333", color: "#aaa" }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* ── Body ───────────────────────────────────────────────────────────── */}
      <div className="p-5">
        {error && (
          <div className="mb-4 p-3 rounded-lg text-sm font-medium flex items-center gap-2"
            style={{ background: "rgba(239,68,68,0.15)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}>
            <XCircle className="w-4 h-4 shrink-0" /> {error}
          </div>
        )}
        {message && (
          <div className="mb-4 p-3 rounded-lg text-sm font-medium flex items-center gap-2"
            style={{ background: "rgba(16,185,129,0.15)", color: "#10b981", border: "1px solid rgba(16,185,129,0.3)" }}>
            <CheckCircle2 className="w-4 h-4 shrink-0" /> {message}
          </div>
        )}

        {loading && !panel ? (
          <div className="flex items-center justify-center py-12 opacity-60">
            <Activity className="w-6 h-6 animate-pulse mr-2" /> Loading panel…
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-6">

            {/* ── Breakers Grid ────────────────────────────────────────────── */}
            <div className="rounded-xl p-4 border"
              style={{ background: "#222", borderColor: "#3a3a3a" }}>
              <div className="text-xs font-bold uppercase tracking-widest mb-4 opacity-60 flex items-center gap-2">
                <Server className="w-3.5 h-3.5" /> System Breakers
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {sortedBreakers.map(([id, breaker]) => {
                  const color = STATUS_COLORS[breaker.status] || "#6b7280";
                  const isTripped = breaker.status === "tripped" || breaker.status === "fault";
                  return (
                    <div key={id}
                      className="flex items-center gap-3 p-3 rounded-lg border transition-all"
                      style={{
                        background: isTripped ? "rgba(239,68,68,0.08)" : "rgba(255,255,255,0.03)",
                        borderColor: isTripped ? "rgba(239,68,68,0.3)" : "#333",
                      }}>
                      <BreakerSwitch status={breaker.status} onClick={() => toggle(id)} />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold truncate">{breaker.label}</div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs font-bold font-mono px-1.5 py-0.5 rounded"
                            style={{
                              background: `${color}22`,
                              color: color,
                            }}>
                            {STATUS_LABELS[breaker.status] || breaker.status.toUpperCase()}
                          </span>
                          <span className="text-[10px] uppercase opacity-40">{breaker.type}</span>
                        </div>
                      </div>
                      {toggling === id && (
                        <RefreshCw className="w-4 h-4 animate-spin shrink-0" style={{ color }} />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Gateway & Failover ────────────────────────────────────────── */}
            <div className="space-y-4">
              {/* Gateway Status */}
              <div className="rounded-xl p-4 border" style={{ background: "#222", borderColor: "#3a3a3a" }}>
                <div className="text-xs font-bold uppercase tracking-widest mb-4 opacity-60 flex items-center gap-2">
                  <Wifi className="w-3.5 h-3.5" /> Gateway Status
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Origin</span>
                    <span className="text-sm font-bold font-mono px-2 py-0.5 rounded"
                      style={{
                        background: `${ORIGIN_COLORS[gateway.active_origin] || "#6b7280"}22`,
                        color: ORIGIN_COLORS[gateway.active_origin] || "#6b7280",
                      }}>
                      {(gateway.active_origin || "primary").toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Auto Failover</span>
                    <span className={`text-sm font-bold ${gateway.auto_failover ? "text-emerald-500" : "text-gray-500"}`}>
                      {gateway.auto_failover ? "ENABLED" : "DISABLED"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Backup Server</span>
                    <span className={`text-sm font-bold ${gateway.backup_last_seen ? "text-emerald-500" : "text-gray-500"}`}>
                      {gateway.backup_last_seen ? "ALIVE" : "SILENT"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Last Failover</span>
                    <span className="text-xs font-mono opacity-60">{ts(gateway.last_failover)}</span>
                  </div>
                  {gateway.last_failover_reason && (
                    <div className="text-xs opacity-50 italic pt-1 border-t" style={{ borderColor: "#333" }}>
                      Reason: {gateway.last_failover_reason}
                    </div>
                  )}
                </div>
              </div>

              {/* Failover Controls */}
              <div className="rounded-xl p-4 border" style={{ background: "#222", borderColor: "#3a3a3a" }}>
                <div className="text-xs font-bold uppercase tracking-widest mb-4 opacity-60 flex items-center gap-2">
                  <ArrowLeftRight className="w-3.5 h-3.5" /> Manual Failover
                </div>
                <div className="space-y-2">
                  <FailoverButton
                    label="Primary (Railway)"
                    target="primary"
                    active={gateway.active_origin === "primary"}
                    color="#10b981"
                    onClick={doFailover}
                    disabled={toggling === "failover"}
                  />
                  <FailoverButton
                    label="Backup (Home Server)"
                    target="backup"
                    active={gateway.active_origin === "backup"}
                    color="#f59e0b"
                    onClick={doFailover}
                    disabled={toggling === "failover"}
                  />
                  <FailoverButton
                    label="Emergency (Standalone UI)"
                    target="emergency"
                    active={gateway.active_origin === "emergency"}
                    color="#ef4444"
                    onClick={doFailover}
                    disabled={toggling === "failover"}
                  />
                </div>
              </div>

              {/* Health Summary */}
              {health && (
                <div className="rounded-xl p-4 border" style={{ background: "#222", borderColor: "#3a3a3a" }}>
                  <div className="text-xs font-bold uppercase tracking-widest mb-3 opacity-60 flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5" /> Systems Health
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="relative w-16 h-16">
                      <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="#333" strokeWidth="2.5" />
                        <circle cx="18" cy="18" r="15.5" fill="none"
                          stroke={health.health_pct >= 80 ? "#10b981" : health.health_pct >= 50 ? "#f59e0b" : "#ef4444"}
                          strokeWidth="2.5" strokeDasharray={`${health.health_pct} 100`}
                          strokeLinecap="round" />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-sm font-black">
                        {health.health_pct}%
                      </span>
                    </div>
                    <div className="text-xs space-y-1 opacity-70">
                      <div>{health.online} / {health.total} breakers online</div>
                      <div>Origin: {health.active_origin}</div>
                      {health.tripped_breakers?.length > 0 && (
                        <div className="text-red-400 font-bold">
                          Tripped: {health.tripped_breakers.join(", ")}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

// ── Failover Button ──────────────────────────────────────────────────────────────
function FailoverButton({ label, target, active, color, onClick, disabled }) {
  return (
    <button
      onClick={() => onClick(target)}
      disabled={disabled || active}
      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 text-sm font-bold transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
      style={{
        borderColor: active ? color : "#333",
        background: active ? `${color}15` : "transparent",
        color: active ? color : "#aaa",
      }}
    >
      <div className="w-3 h-3 rounded-full" style={{ background: color }} />
      {label}
      {active && <span className="ml-auto text-[10px] uppercase tracking-wider">ACTIVE</span>}
    </button>
  );
}
