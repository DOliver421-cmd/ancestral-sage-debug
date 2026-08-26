import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { RefreshCw, Loader2, Bot, ShieldCheck, Power, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const TIER_LABEL = {
  governance: "Governance",
  director: "Director",
  executive: "Executive",
  assistant: "Assistant",
  production: "Production",
};

const levelColor = {
  governance: "#7f1d1d",
  director: "#92400e",
  executive: "#1e40af",
  assistant: "#15803d",
  production: "#6d28d9",
};

/**
 * Personas — an IAM surface to see, enable/disable, and read live source status
 * for every system persona. Backed by /ai/personas/exec (source of truth =
 * load_personas() + PERSONA_META). Hybrid Nam, Conspiracy Brother, Griot and
 * the Unified Mind are all real, chaired prompts here — nothing is a decoy.
 */
export default function PersonasTab() {
  const { user } = useAuth();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(null);
  const isExec = user?.role === "executive_admin" || user?.role === "admin";

  const load = useCallback(() => {
    setError(null);
    setRows(null);
    api.get("/ai/personas/exec")
      .then((r) => setRows(Array.isArray(r.data?.personas) ? r.data.personas : []))
      .catch((e) => {
        setError(e?.response?.data?.detail || "Could not load the persona roster.");
        setRows([]);
      });
  }, []);

  useEffect(() => { load(); }, [load]);

  async function toggle(row) {
    if (!isExec) return;
    setSaving(row.slug);
    try {
      await api.post(`/ai/personas/${row.slug}/toggle`, { enabled: !row.enabled });
      toast.success(`${row.name} ${row.enabled ? "disabled" : "enabled"}`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not update persona state");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs text-ink/60">
            The system's authored personas, read live from <code className="font-mono">persona_loader</code>.
            Each entry is a chaired prompt with a source status — enabling/disabling persists server-side.
          </p>
        </div>
        <button onClick={load} className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-sm border border-ink/20 hover:border-copper transition-colors bg-white text-ink">
          <RefreshCw className="w-3.5 h-3.5" /> Reload
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {!rows ? (
        <div className="flex items-center justify-center py-16 text-ink/40">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading personas…
        </div>
      ) : rows.length === 0 ? (
        <div className="rounded-lg border border-ink/10 bg-white px-4 py-10 text-center text-sm text-ink/50">
          No personas matched the source registry.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {rows.map((row) => (
            <div key={row.slug} className="rounded-lg border border-ink/10 bg-white p-4 flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: levelColor[row.level] || "#6b7280" }} />
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <Bot className="w-3.5 h-3.5 text-copper flex-shrink-0" />
                      <span className="font-heading font-bold text-ink truncate">{row.name}</span>
                    </div>
                    <span className="text-[10px] text-ink/40 font-mono uppercase tracking-wider">{row.slug}</span>
                  </div>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap ${row.enabled ? "bg-green-50 text-green-700 border border-green-200" : "bg-ink/5 text-ink/40 border border-ink/10"}`}>
                  {row.enabled ? "● Active" : "○ Disabled"}
                </span>
              </div>

              <p className="text-xs text-ink/60 leading-relaxed line-clamp-2">{row.domain || "No domain description."}</p>

              <div className="flex flex-wrap gap-1.5">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-ink/5" style={{ color: levelColor[row.level] }}>
                  {TIER_LABEL[row.level] || row.level}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-ink/5 text-ink/60">{row.department}</span>
                {row.source_status === "active" ? (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-green-50 text-green-700">Source: loaded</span>
                ) : (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-destructive/10 text-destructive">Source: missing</span>
                )}
              </div>

              {Array.isArray(row.capabilities) && row.capabilities.length > 0 && (
                <div className="text-[10px] text-ink/45">
                  <span className="font-bold uppercase tracking-wider mr-1">Caps:</span>
                  {row.capabilities.join(" · ")}
                </div>
              )}

              {isExec && (
                <button
                  onClick={() => toggle(row)}
                  disabled={saving === row.slug}
                  className={`mt-auto inline-flex items-center justify-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-sm border transition-colors ${
                    row.enabled
                      ? "border-ink/15 text-ink/50 hover:text-destructive hover:border-destructive/40"
                      : "bg-copper text-bone border-copper hover:bg-copper/90"
                  } disabled:opacity-50`}
                >
                  {saving === row.slug ? <Loader2 className="w-3 h-3 animate-spin" /> : row.enabled ? <Power className="w-3 h-3" /> : <CheckCircle2 className="w-3 h-3" />}
                  {row.enabled ? "Disable" : "Enable"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="mt-4 text-[11px] text-ink/40 flex items-center gap-1.5">
        <ShieldCheck className="w-3.5 h-3.5" />
        Enable/disable requires executive admin. State persists in the platform config database and survives redeploys.
      </p>
    </div>
  );
}