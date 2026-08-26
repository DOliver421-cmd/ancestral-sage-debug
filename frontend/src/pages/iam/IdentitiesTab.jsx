import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
import { RefreshCw, Loader2, Plus, KeyRound, Ban, CircleCheck, UserCircle, Bot, Server, Building2, Globe } from "lucide-react";

const KIND_META = {
  human: { label: "Human", icon: UserCircle, cls: "bg-emerald-100 text-emerald-800" },
  ai_agent: { label: "AI Agent", icon: Bot, cls: "bg-purple-100 text-purple-800" },
  system_service: { label: "System Service", icon: Server, cls: "bg-blue-100 text-blue-800" },
  organization: { label: "Organization", icon: Building2, cls: "bg-amber-100 text-amber-800" },
  external: { label: "External", icon: Globe, cls: "bg-rose-100 text-rose-800" },
};

export default function IdentitiesTab() {
  const [rows, setRows] = useState(null);
  const [selected, setSelected] = useState(null); // profile detail
  const [q, setQ] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newToken, setNewToken] = useState(null);
  const [form, setForm] = useState({ kind: "ai_agent", name: "", description: "", purpose: "", parent_id: "" });

  const load = useCallback(async () => {
    try {
      const params = {};
      if (q.trim()) params.q = q.trim();
      if (kindFilter) params.kind = kindFilter;
      const r = await api.get("/iam/identities", { params });
      setRows(r.data?.identities || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load identities.");
      setRows([]);
    }
  }, [q, kindFilter]);

  useEffect(() => { load(); }, [load]);

  const openProfile = async (id) => {
    try {
      const r = await api.get(`/iam/identities/${id}`);
      setSelected(r.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load profile.");
    }
  };

  const create = async () => {
    if (!form.name.trim()) { toast.error("Name is required."); return; }
    setCreating(true);
    try {
      const r = await api.post("/iam/identities", {
        kind: form.kind,
        name: form.name,
        description: form.description,
        purpose: form.purpose,
        parent_id: form.parent_id || null,
      });
      if (r.data?.identity?.token) setNewToken(r.data.identity.token);
      toast.success("Identity registered.");
      setShowCreate(false);
      setForm({ kind: "ai_agent", name: "", description: "", purpose: "", parent_id: "" });
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Create failed.");
    } finally {
      setCreating(false);
    }
  };

  const toggleStatus = async (id, current) => {
    const next = current === "suspended" ? "active" : "suspended";
    try {
      await api.patch(`/iam/identities/${id}`, { status: next });
      toast.success(next === "suspended" ? "Identity suspended." : "Identity activated.");
      load();
      if (selected?.identity?.id === id) openProfile(id);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Update failed.");
    }
  };

  const rotate = async (id) => {
    try {
      const r = await api.post(`/iam/identities/${id}/rotate-token`);
      setNewToken(r.data.token);
      toast.success("New token issued (shown once).");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Rotation failed.");
    }
  };

  return (
    <div className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
      {/* Registry */}
      <div className="bg-white border border-ink/10 rounded-sm">
        <div className="px-5 py-4 border-b border-ink/10 flex items-center justify-between gap-3 flex-wrap">
          <div>
            <h2 className="font-heading font-bold text-lg">Identity Registry</h2>
            <p className="text-sm text-ink/50">Humans, AI agents, system services, organizations, external identities.</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowCreate(true)} className="btn-copper text-sm inline-flex items-center gap-1.5">
              <Plus className="w-4 h-4" /> New Identity
            </button>
            <button onClick={load} className="btn-ghost text-sm inline-flex items-center gap-1.5">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-5 py-3 flex gap-3 items-center flex-wrap border-b border-ink/10">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search identities…"
            className="flex-1 min-w-[200px] px-3 py-2 border border-ink/15 rounded-sm text-sm focus:outline-none focus:border-copper"
          />
          <select value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}
            className="py-2 px-3 border border-ink/15 rounded-sm text-sm">
            <option value="">All kinds</option>
            {Object.entries(KIND_META).map(([k, m]) => <option key={k} value={k}>{m.label}</option>)}
          </select>
        </div>

        {rows === null ? (
          <div className="p-12 text-center text-ink/50 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading identities…
          </div>
        ) : rows.length === 0 ? (
          <div className="p-12 text-center text-ink/50">No identities found.</div>
        ) : (
          <div className="divide-y divide-ink/5">
            {rows.map((it) => {
              const meta = KIND_META[it.kind] || KIND_META.external;
              const Icon = meta.icon;
              return (
                <button key={it.id} onClick={() => openProfile(it.id)}
                  className="w-full flex items-center gap-3 px-5 py-3 hover:bg-bone/60 text-left">
                  <span className={`p-2 rounded-lg ${meta.cls}`}><Icon className="w-4 h-4" /></span>
                  <span className="flex-1 min-w-0">
                    <span className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-sm">{it.name}</span>
                      <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-sm ${meta.cls}`}>{meta.label}</span>
                      {it.status === "suspended" && <span className="text-[10px] font-bold text-destructive">SUSPENDED</span>}
                      {it.has_token && <span className="text-[10px] font-bold text-copper">TOKEN</span>}
                    </span>
                    <span className="block text-xs text-ink/50 truncate">{it.description || it.purpose || it.id}</span>
                  </span>
                  <span className="text-[10px] text-ink/40 font-mono">{it.id.slice(0, 12)}…</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Profile / detail */}
      <div className="bg-white border border-ink/10 rounded-sm">
        {selected ? (
          <div className="p-5">
            <div className="flex items-center justify-between gap-2 mb-4">
              <h3 className="font-heading font-bold text-base">{selected.identity?.name}</h3>
              <button onClick={() => setSelected(null)} className="text-xs text-ink/40 hover:text-ink">Close</button>
            </div>
            <dl className="space-y-2 text-sm mb-4">
              <div className="flex justify-between"><dt className="text-ink/50">Kind</dt><dd className="font-bold">{selected.identity?.kind}</dd></div>
              <div className="flex justify-between"><dt className="text-ink/50">Owner</dt><dd className="font-bold">{selected.identity?.owner_id || "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-ink/50">Status</dt><dd className="font-bold">{selected.identity?.status}</dd></div>
              <div className="flex justify-between"><dt className="text-ink/50">Purpose</dt><dd className="text-right max-w-[200px]">{selected.identity?.purpose || "—"}</dd></div>
            </dl>

            <div className="mb-4">
              <div className="overline text-copper text-[10px] mb-1">Authority chain</div>
              {selected.chain?.length ? (
                <div className="flex items-center gap-1 flex-wrap text-xs">
                  {selected.chain.map((c, i) => (
                    <span key={c.id} className="flex items-center gap-1">
                      {i > 0 && <span className="text-ink/30">↓</span>}
                      <span className="px-2 py-0.5 rounded-sm bg-bone border border-ink/10">{c.name} <span className="text-ink/40">({c.kind})</span></span>
                    </span>
                  ))}
                </div>
              ) : <span className="text-xs text-ink/40">Root identity — no creator chain.</span>}
            </div>

            <div className="mb-4">
              <div className="overline text-copper text-[10px] mb-1">Delegations received ({selected.delegations?.length || 0})</div>
              {selected.delegations?.length ? (
                <div className="space-y-2">
                  {selected.delegations.map((d) => (
                    <div key={d.id} className="text-xs border border-ink/10 rounded-sm px-3 py-2">
                      <div className="flex justify-between">
                        <span className="font-bold">{d.authorities?.join(", ") || "—"}</span>
                        <span className={d.active ? "text-emerald-700 font-bold" : "text-ink/40"}>{d.active ? "ACTIVE" : d.revoked_at ? "REVOKED" : "EXPIRED"}</span>
                      </div>
                      <div className="text-ink/50 mt-0.5">{d.purpose || "no purpose"} · expires {d.expires_at ? new Date(d.expires_at).toLocaleDateString() : "never"}</div>
                    </div>
                  ))}
                </div>
              ) : <span className="text-xs text-ink/40">No delegations yet.</span>}
            </div>

            {(selected.identity?.kind === "ai_agent" || selected.identity?.kind === "system_service") && (
              <button onClick={() => rotate(selected.identity.id)}
                className="btn-ghost text-xs w-full inline-flex items-center justify-center gap-1.5 mb-3">
                <KeyRound className="w-3.5 h-3.5" /> Rotate token
              </button>
            )}
            <button onClick={() => toggleStatus(selected.identity.id, selected.identity.status)}
              className={`text-xs w-full inline-flex items-center justify-center gap-1.5 border rounded-sm py-2 ${selected.identity?.status === "suspended" ? "border-emerald-700 text-emerald-700" : "border-destructive text-destructive"}`}>
              {selected.identity?.status === "suspended" ? <><CircleCheck className="w-3.5 h-3.5" /> Activate</> : <><Ban className="w-3.5 h-3.5" /> Suspend</>}
            </button>
          </div>
        ) : (
          <div className="p-10 text-center text-ink/40 text-sm">Select an identity to see its profile, delegations, and authority chain.</div>
        )}
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="font-heading font-bold text-lg mb-4">Register a new identity</h3>
            {newToken && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded-sm text-sm">
                <div className="font-black text-amber-900 mb-1">Agent token — copy it now, shown once:</div>
                <code className="break-all font-mono text-xs bg-white px-2 py-1 rounded-sm border border-amber-200">{newToken}</code>
                <div className="text-xs text-amber-800 mt-1">The agent authenticates to /api/iam/actions with X-Agent-ID + X-Agent-Token.</div>
              </div>
            )}
            <label className="block text-xs font-bold text-ink/60 mb-1">Kind</label>
            <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}
              className="w-full mb-3 py-2 px-3 border border-ink/15 rounded-sm text-sm">
              {Object.entries(KIND_META).filter(([k]) => k !== "human").map(([k, m]) => <option key={k} value={k}>{m.label}</option>)}
            </select>
            <label className="block text-xs font-bold text-ink/60 mb-1">Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full mb-3 py-2 px-3 border border-ink/15 rounded-sm text-sm" placeholder="e.g. Research AI" />
            <label className="block text-xs font-bold text-ink/60 mb-1">Purpose</label>
            <input value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })}
              className="w-full mb-3 py-2 px-3 border border-ink/15 rounded-sm text-sm" placeholder="Research assistance" />
            <label className="block text-xs font-bold text-ink/60 mb-1">Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full mb-3 py-2 px-3 border border-ink/15 rounded-sm text-sm" rows={2} />
            <label className="block text-xs font-bold text-ink/60 mb-1">Created by (parent identity id — optional, forms the authority chain)</label>
            <input value={form.parent_id} onChange={(e) => setForm({ ...form, parent_id: e.target.value })}
              className="w-full mb-4 py-2 px-3 border border-ink/15 rounded-sm text-sm font-mono" placeholder="identity id or empty" />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setShowCreate(false); setNewToken(null); }} className="btn-ghost text-sm">Cancel</button>
              <button onClick={create} disabled={creating} className="btn-copper text-sm inline-flex items-center gap-1.5">
                {creating && <Loader2 className="w-4 h-4 animate-spin" />} Register
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
