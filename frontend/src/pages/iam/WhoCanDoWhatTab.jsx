import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { Loader2, RefreshCw, ShieldCheck, ArrowDown } from "lucide-react";

const AUTHORITY_ORDER = ["read", "write", "create", "delete", "execute", "manage"];
const AUTHORITY_SHORT = { read: "READ", write: "WRITE", create: "CREATE", delete: "DELETE", execute: "EXECUTE", manage: "MANAGE" };
const AUTHORITY_COLOR = { read: "bg-emerald-100 text-emerald-800", write: "bg-blue-100 text-blue-800", create: "bg-purple-100 text-purple-800", delete: "bg-rose-100 text-rose-800", execute: "bg-amber-100 text-amber-800", manage: "bg-ink text-signal" };

export default function WhoCanDoWhatTab() {
  const [data, setData] = useState(null);
  const [selectedId, setSelectedId] = useState(null);

  const load = useCallback(async () => {
    try {
      const r = await api.get("/iam/who-can-do-what");
      setData(r.data?.identities || []);
      if (!selectedId && r.data?.identities?.length) setSelectedId(r.data.identities[0].identity.id);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load the authority matrix.");
      setData([]);
    }
  }, [selectedId]);

  useEffect(() => { load(); }, [load]);

  const selected = data?.find((d) => d.identity?.id === selectedId) || data?.[0];
  const domains = selected?.domains?.length ? selected.domains : Object.keys(selected?.authority_by_domain || {});
  const allDomains = [...new Set([...(domains || []), ...Object.keys(selected?.authority_by_domain || {})])];

  return (
    <div className="grid lg:grid-cols-[320px_1fr] gap-6 items-start">
      {/* Identity picker */}
      <div className="bg-white border border-ink/10 rounded-sm">
        <div className="px-4 py-3 border-b border-ink/10 flex items-center justify-between">
          <h2 className="font-heading font-bold text-base">Select an identity</h2>
          <button onClick={load} className="text-ink/40 hover:text-ink"><RefreshCw className="w-4 h-4" /></button>
        </div>
        {data === null ? (
          <div className="p-8 text-center text-ink/50 flex items-center justify-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /></div>
        ) : data.length === 0 ? (
          <div className="p-8 text-center text-ink/50 text-sm">No non-human identities registered yet. Create one in the Identities tab.</div>
        ) : (
          <div className="divide-y divide-ink/5">
            {data.map((d) => (
              <button key={d.identity.id} onClick={() => setSelectedId(d.identity.id)}
                className={`w-full text-left px-4 py-3 flex items-center justify-between gap-2 hover:bg-bone/60 ${selected?.identity?.id === d.identity.id ? "bg-bone" : ""}`}>
                <span>
                  <span className="block font-bold text-sm">{d.identity.name}</span>
                  <span className="block text-xs text-ink/50">{d.identity.kind}</span>
                </span>
                <span className="text-[10px] font-black px-1.5 py-0.5 rounded-sm bg-ink/5">
                  {(Object.values(d.authority_by_domain || {}).flat().length) || 0} grants
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Authority card — the "Who Can Do What?" screen */}
      {selected ? (
        <div className="bg-white border border-ink/10 rounded-sm p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap mb-5">
            <div>
              <div className="overline text-copper text-[10px] mb-1">Who Can Do What?</div>
              <h2 className="font-heading font-bold text-2xl">{selected.identity.name}</h2>
              <div className="text-sm text-ink/50 mt-1">
                Owner: <span className="font-bold text-ink">{selected.owner_id || "System"}</span>
                {selected.acting_for?.length > 0 && (
                  <span className="block mt-0.5">Acting for: {selected.acting_for.map((a) => a.principal_name).join(", ")}</span>
                )}
              </div>
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-sm bg-ink text-signal">{selected.identity.kind}</span>
          </div>

          {/* Authority by domain */}
          <div className="mb-6">
            <div className="overline text-copper text-[10px] mb-2">Authority</div>
            {allDomains.length === 0 ? (
              <div className="text-sm text-ink/40 border border-dashed border-ink/20 rounded-sm p-4">No grants yet — this identity has no authority until a delegation is created.</div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-2">
                {allDomains.map((dom) => {
                  const auths = selected.authority_by_domain[dom] || [];
                  return (
                    <div key={dom} className="border border-ink/10 rounded-sm px-3 py-2.5">
                      <div className="text-xs font-black uppercase tracking-widest text-ink/60 mb-1.5">{dom === "*" ? "All resources" : dom}</div>
                      <div className="flex flex-wrap gap-1">
                        {auths.length ? AUTHORITY_ORDER.filter((a) => auths.includes(a)).map((a) => (
                          <span key={a} className={`text-[10px] font-black px-1.5 py-0.5 rounded-sm ${AUTHORITY_COLOR[a]}`}>{AUTHORITY_SHORT[a]}</span>
                        )) : <span className="text-[10px] font-bold text-ink/30">NONE</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Delegations */}
          <div className="mb-6">
            <div className="overline text-copper text-[10px] mb-2">Delegations</div>
            {selected.acting_for?.length ? (
              <div className="space-y-2">
                {selected.acting_for.map((a) => (
                  <div key={a.delegation_id} className="border border-ink/10 rounded-sm px-3 py-2 text-sm flex items-center justify-between gap-2 flex-wrap">
                    <div>
                      <span className="font-bold">{a.principal_name}</span>
                      <span className="text-ink/40"> → {selected.identity.name}</span>
                      <div className="text-xs text-ink/50">{a.purpose || "no purpose"} · expires {a.expires_at ? new Date(a.expires_at).toLocaleDateString() : "never"}</div>
                    </div>
                    <span className="text-[10px] font-mono text-ink/40">{a.delegation_id.slice(0, 10)}…</span>
                  </div>
                ))}
              </div>
            ) : <div className="text-sm text-ink/40 border border-dashed border-ink/20 rounded-sm p-4">No active delegations.</div>}
          </div>

          {/* Authority chain */}
          <div>
            <div className="overline text-copper text-[10px] mb-2">Authority chain</div>
            {selected.chain?.length ? (
              <div className="flex items-center gap-1.5 flex-wrap text-xs">
                {selected.chain.map((c, i) => (
                  <span key={c.id} className="flex items-center gap-1.5">
                    {i > 0 && <ArrowDown className="w-3 h-3 text-ink/30" />}
                    <span className="px-2 py-1 rounded-sm bg-bone border border-ink/10">{c.name} <span className="text-ink/40">({c.kind})</span></span>
                  </span>
                ))}
                <span className="text-ink/40 ml-1">— authority never auto-propagates; every hop needs its own delegation.</span>
              </div>
            ) : <span className="text-xs text-ink/40">No creator chain.</span>}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-ink/10 rounded-sm p-10 text-center text-ink/40 text-sm flex items-center justify-center gap-2">
          <ShieldCheck className="w-4 h-4" /> Select an identity to see its authority.
        </div>
      )}
    </div>
  );
}
