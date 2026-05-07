import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { Compass, ShieldAlert, Lock, RefreshCcw, AlertTriangle, MessageSquare, FileWarning, ScrollText } from "lucide-react";
import { toast } from "sonner";

const LEVELS = ["conservative", "standard", "exploratory", "extreme"];

const KIND_META = {
  chat: { icon: MessageSquare, label: "Chat", className: "text-ink/80" },
  refusal: { icon: FileWarning, label: "Refusal", className: "text-copper" },
  crisis: { icon: AlertTriangle, label: "Crisis", className: "text-red-700" },
  consent: { icon: Lock, label: "Consent", className: "text-signal" },
};

export default function SageAudit() {
  const [tab, setTab] = useState("sessions");

  return (
    <AppShell>
      <div className="px-10 py-10 max-w-6xl">
        <div className="overline text-copper">Executive Admin · Governance</div>
        <h1 className="font-heading text-4xl font-bold mt-2 flex items-center gap-3">
          <Compass className="w-8 h-8 text-copper" /> Sage Sessions
        </h1>
        <p className="text-ink/60 mt-2">
          Audit Ancestral Sage activity and govern the maximum safety level any
          user may reach. Per-user overrides take precedence over the global cap.
        </p>

        <div className="flex gap-2 mt-6 border-b border-ink/10" data-testid="sage-audit-tabs">
          <TabButton active={tab === "sessions"} onClick={() => setTab("sessions")} testid="tab-sessions" icon={ScrollText} label="Sessions" />
          <TabButton active={tab === "controls"} onClick={() => setTab("controls")} testid="tab-controls" icon={ShieldAlert} label="Level Controls" />
        </div>

        <div className="mt-8">
          {tab === "sessions" ? <SessionsTab /> : <LevelControlsTab />}
        </div>
      </div>
    </AppShell>
  );
}

function TabButton({ active, onClick, label, testid, icon: Icon }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 text-xs font-bold uppercase tracking-widest border-b-2 inline-flex items-center gap-2 transition-colors ${
        active ? "border-copper text-ink" : "border-transparent text-ink/50 hover:text-ink"
      }`}
      data-testid={testid}
    >
      <Icon className="w-4 h-4" /> {label}
    </button>
  );
}

// ---------------------------------------------------------------------------
// SESSIONS TAB
// ---------------------------------------------------------------------------
function SessionsTab() {
  const [kind, setKind] = useState("all");
  const [userId, setUserId] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { kind, limit: 200 };
      if (userId.trim()) params.user_id = userId.trim();
      const r = await api.get("/admin/sage/audit", { params });
      setRows(r.data.rows || []);
    } catch (e) {
      toast.error("Could not load sage audit feed.");
    } finally {
      setLoading(false);
    }
  }, [kind, userId]);

  useEffect(() => { load(); }, [load]);

  // Poll TTS telemetry every 10s.
  useEffect(() => {
    let alive = true;
    const fetchMetrics = async () => {
      try {
        const r = await api.get("/admin/sage/metrics");
        if (alive) setMetrics(r.data);
      } catch { /* tolerate transient errors */ }
    };
    fetchMetrics();
    const t = setInterval(fetchMetrics, 10000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  const counts = useMemo(() => {
    const out = { chat: 0, refusal: 0, crisis: 0, consent: 0 };
    rows.forEach((r) => { if (out[r.kind] !== undefined) out[r.kind] += 1; });
    return out;
  }, [rows]);

  return (
    <div data-testid="sessions-tab">
      <div className="flex items-end gap-3 flex-wrap">
        <div>
          <span className="overline text-ink/60">Kind</span>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="block mt-1 px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
            data-testid="audit-filter-kind"
          >
            {["all", "chat", "refusal", "crisis", "consent"].map((k) => (
              <option key={k} value={k}>{k}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[240px]">
          <span className="overline text-ink/60">Filter by user_id</span>
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Optional — exact user id"
            className="block mt-1 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none font-mono"
            data-testid="audit-filter-userid"
          />
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="btn-secondary inline-flex items-center gap-2"
          data-testid="audit-refresh"
        >
          <RefreshCcw className="w-4 h-4" /> {loading ? "Loading…" : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6" data-testid="audit-counts">
        {["chat", "consent", "refusal", "crisis"].map((k) => {
          const m = KIND_META[k];
          const Icon = m.icon;
          return (
            <div key={k} className="card-flat p-3 bg-white">
              <div className={`text-xs font-bold uppercase tracking-widest ${m.className} flex items-center gap-2`}>
                <Icon className="w-3.5 h-3.5" /> {m.label}
              </div>
              <div className="font-heading text-2xl font-bold mt-1">{counts[k]}</div>
            </div>
          );
        })}
      </div>

      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3" data-testid="telemetry-tile">
          <div className="card-flat p-3 bg-white">
            <div className="text-xs font-bold uppercase tracking-widest text-ink/60">TTS p95</div>
            <div className="font-heading text-2xl font-bold mt-1">{Math.round(metrics.p95_latency_ms)}<span className="text-xs text-ink/40 ml-1">ms</span></div>
          </div>
          <div className="card-flat p-3 bg-white">
            <div className="text-xs font-bold uppercase tracking-widest text-ink/60">Cache hit</div>
            <div className="font-heading text-2xl font-bold mt-1">{Math.round((metrics.cache_hit_ratio || 0) * 100)}<span className="text-xs text-ink/40 ml-1">%</span></div>
          </div>
          <div className="card-flat p-3 bg-white">
            <div className="text-xs font-bold uppercase tracking-widest text-ink/60">Error rate</div>
            <div className={`font-heading text-2xl font-bold mt-1 ${(metrics.error_rate || 0) > 0.05 ? "text-red-700" : ""}`}>
              {Math.round((metrics.error_rate || 0) * 100)}<span className="text-xs text-ink/40 ml-1">%</span>
            </div>
          </div>
          <div className="card-flat p-3 bg-white">
            <div className="text-xs font-bold uppercase tracking-widest text-ink/60">Breaker</div>
            <div className="font-heading text-2xl font-bold mt-1 flex items-center gap-2">
              <span className={`inline-block w-2.5 h-2.5 rounded-full ${
                metrics.breaker === "closed" ? "bg-green-600" :
                metrics.breaker === "half-open" ? "bg-yellow-500" : "bg-red-700"
              }`} />
              <span className="text-sm">{metrics.breaker}</span>
            </div>
          </div>
        </div>
      )}

      <div className="card-flat mt-6 bg-white overflow-hidden">
        <table className="w-full text-sm" data-testid="audit-table">
          <thead className="bg-ink text-white">
            <tr>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">When</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">Kind</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">User</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">Intensity</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">Safety</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">Detail</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="px-3 py-10 text-center text-ink/40">
                  No sage activity yet.
                </td>
              </tr>
            )}
            {rows.map((r) => {
              const m = KIND_META[r.kind] || KIND_META.chat;
              const Icon = m.icon;
              return (
                <tr key={`${r.kind}-${r.id}`} className="border-t border-ink/5" data-testid={`audit-row-${r.id}`}>
                  <td className="px-3 py-2 text-xs text-ink/60 font-mono whitespace-nowrap">
                    {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
                  </td>
                  <td className={`px-3 py-2 text-xs font-bold uppercase tracking-widest ${m.className}`}>
                    <span className="inline-flex items-center gap-1">
                      <Icon className="w-3.5 h-3.5" /> {r.kind}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-xs">
                    {r.email || <span className="font-mono text-ink/40">{r.user_id?.slice(0, 8)}…</span>}
                  </td>
                  <td className="px-3 py-2 text-xs">{r.intensity || "—"}</td>
                  <td className="px-3 py-2 text-xs">{r.safety_level || "—"}</td>
                  <td className="px-3 py-2 text-xs text-ink/70">
                    {r.refusal_reason && (
                      <span className="text-copper font-semibold">{r.refusal_reason}</span>
                    )}
                    {r.user_msg && <div className="line-clamp-2">{r.user_msg}</div>}
                    {r.kind === "consent" && r.expires_at && (
                      <div className="text-ink/50">expires {new Date(r.expires_at).toLocaleString()}</div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// LEVEL CONTROLS TAB
// ---------------------------------------------------------------------------
function LevelControlsTab() {
  const [globalLevel, setGlobalLevel] = useState(""); // "" = inherit (no cap)
  const [overrides, setOverrides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]);
  const [newUserId, setNewUserId] = useState("");
  const [newLevel, setNewLevel] = useState("conservative");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [capR, usersR] = await Promise.all([
        api.get("/admin/sage/cap"),
        api.get("/admin/users"),
      ]);
      setGlobalLevel(capR.data.global_level || "");
      setOverrides(capR.data.overrides || []);
      const u = usersR.data;
      setUsers(Array.isArray(u) ? u : []);
    } catch (e) {
      toast.error("Could not load level controls.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const setGlobal = async (level) => {
    try {
      await api.put("/admin/sage/cap/global", { level: level || null });
      setGlobalLevel(level || "");
      toast.success(level ? `Global cap set to ${level}.` : "Global cap cleared.");
    } catch (e) {
      toast.error("Could not update global cap.");
    }
  };

  const setUserCap = async (uid, level) => {
    try {
      await api.put(`/admin/sage/cap/user/${uid}`, { level: level || null });
      toast.success(level ? `User cap set to ${level}.` : "User override cleared.");
      load();
    } catch (e) {
      toast.error("Could not update user cap.");
    }
  };

  return (
    <div data-testid="controls-tab">
      <div className="card-flat p-5 bg-white border-l-4 border-l-copper">
        <div className="overline text-copper">Global cap</div>
        <h3 className="font-heading text-xl font-bold mt-1">Site-wide safety ceiling</h3>
        <p className="text-sm text-ink/60 mt-2">
          Applies to every user. Per-user overrides below take precedence (more
          restrictive of the two wins). Leave at <strong>No cap</strong> to allow
          all levels (extreme still requires consent).
        </p>
        <div className="mt-4 flex items-center gap-3">
          <select
            value={globalLevel}
            onChange={(e) => setGlobal(e.target.value)}
            className="px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
            data-testid="cap-global-select"
          >
            <option value="">No cap (extreme allowed)</option>
            {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <span className="text-xs text-ink/50">
            Currently: <strong className="text-ink/80">{globalLevel || "no cap"}</strong>
          </span>
        </div>
      </div>

      <div className="card-flat mt-6 bg-white">
        <div className="p-5 border-b border-ink/10">
          <div className="overline text-copper">Per-user overrides</div>
          <h3 className="font-heading text-xl font-bold mt-1">Lock specific users</h3>
          <p className="text-sm text-ink/60 mt-2">
            Use this for trauma-aware accommodations or compliance flags. Set
            <strong> No override</strong> to remove the lock.
          </p>

          <div className="mt-4 grid sm:grid-cols-3 gap-3 items-end">
            <label className="text-xs">
              <span className="overline text-ink/60">Add override — pick user</span>
              <select
                value={newUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                className="block mt-1 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
                data-testid="cap-new-user"
              >
                <option value="">— select —</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>{u.email} · {u.role}</option>
                ))}
              </select>
            </label>
            <label className="text-xs">
              <span className="overline text-ink/60">Cap level</span>
              <select
                value={newLevel}
                onChange={(e) => setNewLevel(e.target.value)}
                className="block mt-1 w-full px-3 py-2 bg-white border border-ink/20 text-sm focus:border-ink focus:outline-none"
                data-testid="cap-new-level"
              >
                {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </label>
            <button
              onClick={() => newUserId && setUserCap(newUserId, newLevel)}
              disabled={!newUserId}
              className="btn-primary"
              data-testid="cap-add-override"
            >
              Apply override
            </button>
          </div>
        </div>

        <table className="w-full text-sm" data-testid="cap-overrides-table">
          <thead className="bg-bone">
            <tr>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">User</th>
              <th className="text-left px-3 py-2 font-bold uppercase tracking-widest text-xs">Override</th>
              <th className="text-right px-3 py-2 font-bold uppercase tracking-widest text-xs">Action</th>
            </tr>
          </thead>
          <tbody>
            {overrides.length === 0 && !loading && (
              <tr>
                <td colSpan={3} className="px-3 py-8 text-center text-ink/40">
                  No per-user overrides. Global cap applies to everyone.
                </td>
              </tr>
            )}
            {overrides.map((o) => (
              <tr key={o.user_id} className="border-t border-ink/5" data-testid={`cap-row-${o.user_id}`}>
                <td className="px-3 py-2 text-xs">{o.email || <span className="font-mono text-ink/40">{o.user_id}</span>}</td>
                <td className="px-3 py-2 text-xs">
                  <select
                    value={o.level}
                    onChange={(e) => setUserCap(o.user_id, e.target.value)}
                    className="px-2 py-1 bg-white border border-ink/20 text-xs focus:border-ink focus:outline-none"
                    data-testid={`cap-edit-${o.user_id}`}
                  >
                    {LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                </td>
                <td className="px-3 py-2 text-xs text-right">
                  <button
                    onClick={() => setUserCap(o.user_id, null)}
                    className="text-signal hover:underline font-semibold"
                    data-testid={`cap-clear-${o.user_id}`}
                  >
                    Clear override
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
