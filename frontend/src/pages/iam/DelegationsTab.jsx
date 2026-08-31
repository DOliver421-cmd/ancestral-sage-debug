import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { Loader2, RefreshCw, Plus, Ban, KeyRound } from "lucide-react";

const AUTHORITIES = [
  { key: "read", label: "Read", desc: "Read resources" },
  { key: "write", label: "Write", desc: "Edit existing resources" },
  { key: "create", label: "Create", desc: "Create new resources" },
  { key: "delete", label: "Delete", desc: "Delete resources" },
  { key: "execute", label: "Execute", desc: "Run actions / workflows" },
  { key: "manage", label: "Manage", desc: "Manage & grant (highest)" },
];

export default function DelegationsTab() {
  const [rows, setRows] = useState(null);
  const [identities, setIdentities] = useState([]);
  const [resources, setResources] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({
    delegate_id: "",
    authorities: ["read"],
    scope_all_owned: true,
    resource_ids: [],
    purpose: "",
    expires_at: "",
    revocable: true,
  });

  const load = useCallback(async () => {
    try {
      const params = filter === "active" ? { active_only: true } : {};
      const r = await api.get("/iam/delegations", { params });
      setRows(r.data?.delegations || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load delegations.");
      setRows([]);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const loadOptions = useCallback(async () => {
    try {
      const [i, res] = await Promise.all([
        api.get("/iam/identities"),
        api.get("/iam/resources"),
      ]);
      setIdentities((i.data?.identities || []).filter((x) => x.kind !== "human"));
      setResources(res.data?.resources || []);
    } catch { /* options are secondary */ }
  }, []);

  useEffect(() => { loadOptions(); }, [loadOptions]);

  const revoke = async (id) => {
    try {
      await api.post(`/iam/delegations/${id}/revoke`);
      toast.success("Delegation revoked.");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Revoke failed.");
    }
  };

  const toggleAuth = (k) => {
    setForm((f) => ({
      ...f,
      authorities: f.authorities.includes(k) ? f.authorities.filter((a) => a !== k) : [...f.authorities, k],
    }));
  };

  const toggleResource = (rid) => {
    setForm((f) => ({
      ...f,
      resource_ids: f.resource_ids.includes(rid) ? f.resource_ids.filter((r) => r !== rid) : [...f.resource_ids, rid],
    }));
  };

  const create = async () => {
    if (!form.delegate_id) { toast.error("Choose a delegate identity."); return; }
    if (!form.authorities.length) { toast.error("Pick at least one authority."); return; }
    if (!form.scope_all_owned && !form.resource_ids.length) { toast.error("Pick resources or delegate all owned."); return; }
    setCreating(true);
    try {
      const resourcesBody = form.scope_all_owned ? [] : resources.filter((r) => form.resource_ids.includes(r.id)).map((r) => ({ resource_type: r.resource_type, resource_key: r.resource_key }));
      await api.post("/iam/delegations", {
        delegate_id: form.delegate_id,
        authorities: form.authorities,
        resources: resourcesBody,
        scope_all_owned: form.scope_all_owned,
        purpose: form.purpose,
        expires_at: form.expires_at || null,
        revocable: form.revocable,
      });
      toast.success("Delegation created.");
      setShowCreate(false);
      setForm({ delegate_id: "", authorities: ["read"], scope_all_owned: true, resource_ids: [], purpose: "", expires_at: "", revocable: true });
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Create failed.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <button onClick={() => setFilter("")} className={`px-3 py-1.5 text-xs font-bold rounded-sm border ${filter === "" ? "bg-ink text-white border-ink" : "bg-white border-ink/20"}`}>All</button>
          <button onClick={() => setFilter("active")} className={`px-3 py-1.5 text-xs font-bold rounded-sm border ${filter === "active" ? "bg-ink text-white border-ink" : "bg-white border-ink/20"}`}>Active</button>
          <button onClick={load} className="btn-ghost text-xs inline-flex items-center gap-1.5"><RefreshCw className="w-3.5 h-3.5" /></button>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-copper text-sm inline-flex items-center gap-1.5"><Plus className="w-4 h-4" /> New Delegation</button>
      </div>

      {rows === null ? (
        <div className="bg-white border border-ink/10 rounded-sm p-12 text-center text-ink/50 flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading delegations…
        </div>
      ) : rows.length === 0 ? (
        <div className="bg-white border border-ink/10 rounded-sm p-12 text-center text-ink/50">
          No delegations yet. Delegation is how an owner authorizes an agent — without creating a role.
        </div>
      ) : (
        <div className="bg-white border border-ink/10 rounded-sm overflow-hidden">
          <div className="grid grid-cols-[1fr_1fr_auto_auto] gap-3 px-4 py-2.5 bg-ink text-white text-[10px] font-black uppercase tracking-widest">
            <span>Principal → Delegate</span>
            <span>Authority / Scope</span>
            <span>Status</span>
            <span className="text-right">Revoke</span>
          </div>
          <div className="divide-y divide-ink/5">
            {rows.map((d) => (
              <div key={d.id} className="grid grid-cols-[1fr_1fr_auto_auto] gap-3 px-4 py-3 items-center">
                <div>
                  <div className="font-bold text-sm truncate">{d.principal_id} → <span className="text-copper">{d.delegate_id}</span></div>
                  <div className="text-xs text-ink/50 truncate">{d.purpose || "—"}</div>
                </div>
                <div>
                  <div className="flex flex-wrap gap-1 mb-1">
                    {(d.authorities || []).map((a) => (
                      <span key={a} className="text-[10px] font-black px-1.5 py-0.5 rounded-sm bg-ink/5 uppercase">{a}</span>
                    ))}
                  </div>
                  <div className="text-[11px] text-ink/50">
                    {d.scope_all_owned ? "All owned resources" : (d.resources || []).map((r) => `${r.resource_type}:${r.resource_key}`).join(", ") || "—"}
                  </div>
                </div>
                <div className="text-xs">
                  <span className={`font-black px-2 py-1 rounded-sm ${d.active ? "bg-emerald-100 text-emerald-800" : "bg-ink/5 text-ink/40"}`}>
                    {d.active ? "ACTIVE" : d.revoked_at ? "REVOKED" : "EXPIRED"}
                  </span>
                  <div className="text-[10px] text-ink/40 mt-1">exp {d.expires_at ? new Date(d.expires_at).toLocaleDateString() : "never"}</div>
                </div>
                <div className="text-right">
                  {d.active && d.revocable !== false ? (
                    <button onClick={() => revoke(d.id)} className="p-1.5 border border-destructive/30 text-destructive rounded-sm hover:bg-destructive/5" title="Revoke">
                      <Ban className="w-3.5 h-3.5" />
                    </button>
                  ) : <span className="text-[10px] text-ink/30">{d.revocable === false ? "PINNED" : "—"}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-5 h-5 text-copper" />
              <h3 className="font-heading font-bold text-lg">Authorize a delegate</h3>
            </div>

            <label className="block text-xs font-bold text-ink/60 mb-1">Delegate (identity)</label>
            <select value={form.delegate_id} onChange={(e) => setForm({ ...form, delegate_id: e.target.value })}
              className="w-full mb-4 py-2 px-3 border border-ink/15 rounded-sm text-sm">
              <option value="">Choose an AI agent / service…</option>
              {identities.map((i) => <option key={i.id} value={i.id}>{i.name} ({i.kind})</option>)}
            </select>

            <label className="block text-xs font-bold text-ink/60 mb-2">Authorities</label>
            <div className="grid sm:grid-cols-2 gap-2 mb-4">
              {AUTHORITIES.map((a) => (
                <label key={a.key} className={`flex items-start gap-2 border rounded-sm px-3 py-2 text-sm cursor-pointer ${form.authorities.includes(a.key) ? "border-copper bg-copper/5" : "border-ink/15"}`}>
                  <input type="checkbox" checked={form.authorities.includes(a.key)} onChange={() => toggleAuth(a.key)} className="mt-0.5" />
                  <span>
                    <span className="font-bold block uppercase text-xs">{a.label}</span>
                    <span className="text-xs text-ink/50">{a.desc}</span>
                  </span>
                </label>
              ))}
            </div>

            <label className="flex items-center gap-2 text-sm font-bold text-ink/70 mb-3">
              <input type="checkbox" checked={form.scope_all_owned} onChange={(e) => setForm({ ...form, scope_all_owned: e.target.checked })} />
              Delegate ALL resources I own
            </label>

            {!form.scope_all_owned && (
              <div className="mb-4">
                <label className="block text-xs font-bold text-ink/60 mb-1">Specific resources</label>
                {resources.length === 0 ? (
                  <div className="text-xs text-ink/40 border border-dashed border-ink/20 rounded-sm p-3">No registered resources — register ownership first.</div>
                ) : (
                  <div className="grid sm:grid-cols-2 gap-1.5 max-h-40 overflow-y-auto">
                    {resources.map((r) => (
                      <label key={r.id} className={`flex items-center gap-2 border rounded-sm px-2.5 py-1.5 text-xs cursor-pointer ${form.resource_ids.includes(r.id) ? "border-copper bg-copper/5" : "border-ink/15"}`}>
                        <input type="checkbox" checked={form.resource_ids.includes(r.id)} onChange={() => toggleResource(r.id)} />
                        <span className="truncate"><span className="font-bold">{r.resource_type}</span> · {r.resource_key}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}

            <label className="block text-xs font-bold text-ink/60 mb-1">Purpose</label>
            <input value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })}
              className="w-full mb-3 py-2 px-3 border border-ink/15 rounded-sm text-sm" placeholder="Research assistance for Project Aurora" />

            <div className="grid sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-bold text-ink/60 mb-1">Expires (ISO, optional)</label>
                <input type="datetime-local" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                  className="w-full py-2 px-3 border border-ink/15 rounded-sm text-sm" />
              </div>
              <label className="flex items-end gap-2 text-sm font-bold text-ink/70 pb-2">
                <input type="checkbox" checked={form.revocable} onChange={(e) => setForm({ ...form, revocable: e.target.checked })} />
                Revocable
              </label>
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="btn-ghost text-sm">Cancel</button>
              <button onClick={create} disabled={creating} className="btn-copper text-sm inline-flex items-center gap-1.5">
                {creating && <Loader2 className="w-4 h-4 animate-spin" />} Create Delegation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
