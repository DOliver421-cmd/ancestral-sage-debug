import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { Loader2, Ban, RefreshCw } from "lucide-react";

export default function ConsentTab() {
  const [rows, setRows] = useState(null);
  const [identity, setIdentity] = useState(null);

  const load = useCallback(async () => {
    try {
      const r = await api.get("/iam/consent");
      setRows(r.data?.consent || []);
      setIdentity(r.data?.identity || null);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load your consent history.");
      setRows([]);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const revoke = async (id) => {
    try {
      await api.post(`/iam/delegations/${id}/revoke`);
      toast.success("Revoked.");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Revoke failed.");
    }
  };

  const active = (rows || []).filter((r) => r.active);
  const past = (rows || []).filter((r) => !r.active);

  return (
    <div className="bg-white border border-ink/10 rounded-sm">
      <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between">
        <div>
          <h2 className="font-heading font-bold text-lg">What have I authorized?</h2>
          <p className="text-sm text-ink/50">
            Every delegation you (or an admin on your behalf) have granted — and everything is revocable.
          </p>
        </div>
        <button onClick={load} className="btn-ghost text-sm inline-flex items-center gap-1.5"><RefreshCw className="w-4 h-4" /></button>
      </div>

      {rows === null ? (
        <div className="p-12 text-center text-ink/50 flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading consent…</div>
      ) : (
        <div className="p-5 space-y-6">
          <div>
            <div className="overline text-copper text-[10px] mb-2">Active ({active.length})</div>
            {active.length === 0 ? (
              <div className="text-sm text-ink/40 border border-dashed border-ink/20 rounded-sm p-4">You have not authorized any AI agent or service. Nothing is acting on your behalf.</div>
            ) : (
              <div className="space-y-2">
                {active.map((d) => (
                  <div key={d.id} className="border border-ink/10 rounded-sm px-4 py-3 flex items-center justify-between gap-3 flex-wrap">
                    <div className="min-w-0">
                      <div className="font-bold text-sm">{d.delegate_name || d.delegate_id} <span className="text-ink/40 text-xs">({d.delegate_kind})</span></div>
                      <div className="text-xs text-ink/50 mt-0.5 flex flex-wrap gap-1">
                        {(d.authorities || []).map((a) => <span key={a} className="font-black uppercase text-[10px] bg-ink/5 px-1.5 py-0.5 rounded-sm">{a}</span>)}
                      </div>
                      <div className="text-[11px] text-ink/50 mt-1">
                        {d.purpose || "no purpose"} · scope: {d.scope_all_owned ? "all my resources" : (d.resources || []).map((r) => `${r.resource_type}:${r.resource_key}`).join(", ")}
                        {d.expires_at ? ` · expires ${new Date(d.expires_at).toLocaleDateString()}` : " · no expiry"}
                      </div>
                    </div>
                    <button onClick={() => revoke(d.id)} className="inline-flex items-center gap-1.5 text-xs font-bold text-destructive border border-destructive/30 rounded-sm px-3 py-1.5 hover:bg-destructive/5">
                      <Ban className="w-3.5 h-3.5" /> Revoke
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {past.length > 0 && (
            <div>
              <div className="overline text-copper text-[10px] mb-2">Revoked / expired ({past.length})</div>
              <div className="space-y-2">
                {past.map((d) => (
                  <div key={d.id} className="border border-ink/5 bg-bone/40 rounded-sm px-4 py-2.5 text-sm flex items-center justify-between gap-3">
                    <div className="text-ink/60">
                      <span className="font-bold">{d.delegate_name || d.delegate_id}</span>
                      <span className="text-xs"> · {(d.authorities || []).join(", ")} · {d.purpose || "no purpose"}</span>
                    </div>
                    <span className="text-[10px] font-black text-ink/40">{d.revoked_at ? "REVOKED" : "EXPIRED"}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
