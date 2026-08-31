import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { Loader2, RefreshCw, ShieldAlert, ShieldCheck } from "lucide-react";

export default function ActionsTab() {
  const [rows, setRows] = useState(null);
  const [onlyDenied, setOnlyDenied] = useState(false);
  const [limit, setLimit] = useState(100);

  const load = useCallback(async () => {
    try {
      const params = { limit };
      if (onlyDenied) params.allowed = false;
      const r = await api.get("/iam/actions", { params });
      setRows(r.data?.actions || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load the action history.");
      setRows([]);
    }
  }, [onlyDenied, limit]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="bg-white border border-ink/10 rounded-sm">
      <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="font-heading font-bold text-lg">Action History</h2>
          <p className="text-sm text-ink/50">Every action carries its authorization — or its denial, with the reason.</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs font-bold text-ink/60">
            <input type="checkbox" checked={onlyDenied} onChange={(e) => setOnlyDenied(e.target.checked)} />
            Denied only
          </label>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))} className="py-1.5 px-2 border border-ink/15 rounded-sm text-xs">
            {[50, 100, 250, 500].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          <button onClick={load} className="btn-ghost text-xs inline-flex items-center gap-1.5"><RefreshCw className="w-3.5 h-3.5" /></button>
        </div>
      </div>

      {rows === null ? (
        <div className="p-12 text-center text-ink/50 flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading actions…</div>
      ) : rows.length === 0 ? (
        <div className="p-12 text-center text-ink/50">No actions recorded yet.</div>
      ) : (
        <div className="divide-y divide-ink/5">
          {rows.map((a) => (
            <div key={a.id} className="px-5 py-3 flex items-start gap-3">
              <span className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${a.allowed ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
                {a.allowed ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-sm">{a.actor_name || a.actor_id}</span>
                  <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded-sm bg-ink/5">{a.actor_kind}</span>
                  <span className={`text-[10px] font-black uppercase px-1.5 py-0.5 rounded-sm ${a.allowed ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                    {a.allowed ? "ALLOWED" : "DENIED"}
                  </span>
                  <span className="text-xs text-ink/40 font-mono">{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</span>
                </div>
                <div className="text-sm mt-1">
                  <span className="font-bold">{a.action}</span>
                  <span className="text-ink/50"> on </span>
                  <span className="font-mono text-xs bg-bone px-1.5 py-0.5 rounded-sm">{a.resource_type}:{a.resource_key || "*"}</span>
                </div>
                <div className="text-xs text-ink/50 mt-1">
                  {a.allowed ? (
                    <>Authorized by: <span className="font-mono">{a.delegation_id ? `Delegation #${a.delegation_id.slice(0, 10)}` : a.reason || "platform role"}</span></>
                  ) : (
                    <span className="text-destructive font-semibold">Reason: {a.reason || "denied"}</span>
                  )}
                  {a.note && <span className="text-ink/40"> · {a.note}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
