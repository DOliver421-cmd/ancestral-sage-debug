import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { Loader2, RefreshCw, Ban } from "lucide-react";

export default function WhoHasAccessTab() {
  const [data, setData] = useState(null);
  const [userId, setUserId] = useState("");

  const load = useCallback(async () => {
    try {
      const r = await api.get("/iam/who-has-access-to-me", { params: userId ? { user_id: userId } : {} });
      setData(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load access overview.");
      setData(null);
    }
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const revoke = async (id) => {
    try {
      await api.post(`/iam/delegations/${id}/revoke`);
      toast.success("Access revoked.");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Revoke failed.");
    }
  };

  return (
    <div className="bg-white border border-ink/10 rounded-sm">
      <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h2 className="font-heading font-bold text-lg">Who Has Access to Me?</h2>
          <p className="text-sm text-ink/50">
            The inverse view — which humans, AI agents, services, and applications can touch your information. Transparency runs both ways.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="User id (admins only, optional)"
            className="px-3 py-2 border border-ink/15 rounded-sm text-sm font-mono w-56"
          />
          <button onClick={load} className="btn-ghost text-sm inline-flex items-center gap-1.5"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {data === null ? (
        <div className="p-12 text-center text-ink/50 flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Loading…</div>
      ) : (
        <div className="p-5">
          <div className="text-sm text-ink/60 mb-4">
            <span className="font-bold text-ink">{data.user_id}</span> — {data.total} grant{data.total === 1 ? "" : "s"} touching this account.
          </div>
          {data.access.length === 0 ? (
            <div className="text-sm text-ink/40 border border-dashed border-ink/20 rounded-sm p-6 text-center">
              Nothing has access to you. No agents, no services, no external identities.
            </div>
          ) : (
            <div className="space-y-2">
              {data.access.map((a) => (
                <div key={a.delegation_id} className="border border-ink/10 rounded-sm px-4 py-3 flex items-center justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-sm">{a.identity_name}</span>
                      <span className="text-[10px] font-black uppercase px-1.5 py-0.5 rounded-sm bg-ink/5">{a.identity_kind}</span>
                      <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-sm ${a.active ? "bg-emerald-100 text-emerald-800" : "bg-ink/5 text-ink/40"}`}>
                        {a.active ? "ACTIVE" : a.revoked_at ? "REVOKED" : "EXPIRED"}
                      </span>
                    </div>
                    <div className="text-xs text-ink/50 mt-1 flex flex-wrap gap-1">
                      {(a.authorities || []).map((x) => <span key={x} className="font-black uppercase text-[10px] bg-ink/5 px-1.5 py-0.5 rounded-sm">{x}</span>)}
                    </div>
                    <div className="text-[11px] text-ink/50 mt-1">
                      {a.purpose || "no purpose"} · scope: {a.scope_all_owned ? "all my resources" : (a.resources || []).map((r) => `${r.resource_type}:${r.resource_key}`).join(", ")}
                      {a.expires_at ? ` · expires ${new Date(a.expires_at).toLocaleDateString()}` : " · no expiry"}
                    </div>
                  </div>
                  {a.active && a.revocable !== false ? (
                    <button onClick={() => revoke(a.delegation_id)} className="inline-flex items-center gap-1.5 text-xs font-bold text-destructive border border-destructive/30 rounded-sm px-3 py-1.5 hover:bg-destructive/5">
                      <Ban className="w-3.5 h-3.5" /> Revoke
                    </button>
                  ) : <span className="text-[10px] text-ink/30">pinned</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
