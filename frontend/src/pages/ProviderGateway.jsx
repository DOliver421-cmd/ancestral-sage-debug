/**
 * Provider Gateway — executive dashboard for managing AI providers and API keys.
 * Routes: GET/POST /providers, PATCH /providers/{id}/status
 *         GET/POST /providers/keys, DELETE /providers/keys/{id}, POST /providers/keys/{id}/test
 *         GET /providers/usage-log
 */
import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import {
  Plus, Trash2, FlaskConical, CheckCircle, XCircle,
  RefreshCw, ChevronDown, ChevronUp, Activity,
} from "lucide-react";

const STATUS_COLORS = {
  active:   "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-600",
  error:    "bg-red-100 text-red-700",
};

export default function ProviderGateway() {
  const { user } = useAuth();
  const [tab, setTab]               = useState("providers");
  const [providers, setProviders]   = useState([]);
  const [keys, setKeys]             = useState([]);
  const [usageLog, setUsageLog]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [expanded, setExpanded]     = useState(null);
  const [testing, setTesting]       = useState({});

  // new provider form
  const [newProvider, setNewProvider] = useState({ name: "", provider_type: "openai", base_url: "", notes: "" });
  const [addingProvider, setAddingProvider] = useState(false);
  const [savingProvider, setSavingProvider] = useState(false);

  // new key form
  const [newKey, setNewKey] = useState({ provider_id: "", label: "", plaintext_key: "", scope: "chat" });
  const [addingKey, setAddingKey] = useState(false);
  const [savingKey, setSavingKey] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, k] = await Promise.all([
        api.get("/providers").then(r => r.data),
        api.get("/providers/keys").then(r => r.data),
      ]);
      setProviders(Array.isArray(p) ? p : p.providers || []);
      setKeys(Array.isArray(k) ? k : k.keys || []);
    } catch (e) {
      toast.error("Failed to load providers");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUsage = useCallback(async () => {
    try {
      const r = await api.get("/providers/usage-log");
      setUsageLog(Array.isArray(r.data) ? r.data : r.data.logs || []);
    } catch { setUsageLog([]); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (tab === "usage") loadUsage(); }, [tab, loadUsage]);

  const toggleStatus = async (p) => {
    const next = p.status === "active" ? "inactive" : "active";
    try {
      await api.patch(`/providers/${p._id || p.id}/status`, { status: next });
      toast.success(`${p.name} set to ${next}`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to update status");
    }
  };

  const addProvider = async (e) => {
    e.preventDefault();
    setSavingProvider(true);
    try {
      await api.post("/providers", newProvider);
      toast.success("Provider added");
      setNewProvider({ name: "", provider_type: "openai", base_url: "", notes: "" });
      setAddingProvider(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to add provider");
    } finally { setSavingProvider(false); }
  };

  const addKey = async (e) => {
    e.preventDefault();
    setSavingKey(true);
    try {
      await api.post("/providers/keys", newKey);
      toast.success("API key saved (encrypted at rest)");
      setNewKey({ provider_id: "", label: "", plaintext_key: "", scope: "chat" });
      setAddingKey(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to save key");
    } finally { setSavingKey(false); }
  };

  const deleteKey = async (keyId, label) => {
    if (!window.confirm(`Delete key "${label}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/providers/keys/${keyId}`);
      toast.success("Key deleted");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to delete key");
    }
  };

  const testKey = async (keyId) => {
    setTesting(t => ({ ...t, [keyId]: true }));
    try {
      const r = await api.post(`/providers/keys/${keyId}/test`);
      if (r.data.ok) {
        toast.success(`Key OK — ${r.data.latency_ms}ms`);
      } else {
        toast.error(`Key failed: ${r.data.error || "unknown error"}`);
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Test failed");
    } finally {
      setTesting(t => ({ ...t, [keyId]: false }));
    }
  };

  const inp = "w-full border border-ink/20 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold";

  return (
    <div className="min-h-screen bg-bone">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-ink">Provider Gateway</h1>
          <p className="text-ink/60 mt-1 text-sm">Manage AI providers and encrypted API keys. Executive access only.</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-ink/10">
          {[["providers","Providers"], ["keys","API Keys"], ["usage","Usage Log"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${tab === id ? "border-gold text-ink" : "border-transparent text-ink/50 hover:text-ink"}`}>
              {label}
            </button>
          ))}
        </div>

        {loading && <p className="text-ink/50 text-sm py-8 text-center">Loading…</p>}

        {/* ── PROVIDERS TAB ── */}
        {!loading && tab === "providers" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => setAddingProvider(!addingProvider)}
                className="flex items-center gap-2 bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gold/90">
                <Plus className="w-4 h-4" /> Add Provider
              </button>
            </div>

            {addingProvider && (
              <form onSubmit={addProvider} className="bg-white border border-ink/10 rounded-xl p-5 space-y-3">
                <h3 className="font-bold text-sm">New Provider</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">Name *</label>
                    <input required value={newProvider.name} onChange={e => setNewProvider(p => ({...p, name: e.target.value}))} className={inp} placeholder="e.g. OpenAI Primary" /></div>
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">Type</label>
                    <select value={newProvider.provider_type} onChange={e => setNewProvider(p => ({...p, provider_type: e.target.value}))} className={inp}>
                      {["openai","anthropic","elevenlabs","groq","cohere","custom"].map(t => <option key={t}>{t}</option>)}
                    </select></div>
                </div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Base URL (optional)</label>
                  <input value={newProvider.base_url} onChange={e => setNewProvider(p => ({...p, base_url: e.target.value}))} className={inp} placeholder="https://api.openai.com/v1" /></div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Notes</label>
                  <input value={newProvider.notes} onChange={e => setNewProvider(p => ({...p, notes: e.target.value}))} className={inp} /></div>
                <div className="flex gap-2">
                  <button type="submit" disabled={savingProvider} className="bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
                    {savingProvider ? "Saving…" : "Save Provider"}
                  </button>
                  <button type="button" onClick={() => setAddingProvider(false)} className="text-sm px-4 py-2 rounded-lg border border-ink/20">Cancel</button>
                </div>
              </form>
            )}

            {providers.length === 0 && <p className="text-ink/50 text-sm text-center py-10">No providers yet. Add one above.</p>}
            {providers.map(p => (
              <div key={p._id || p.id} className="bg-white border border-ink/10 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-5 py-4 cursor-pointer" onClick={() => setExpanded(expanded === p._id ? null : p._id)}>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${STATUS_COLORS[p.status] || STATUS_COLORS.inactive}`}>{p.status || "inactive"}</span>
                    <div>
                      <p className="font-semibold text-ink">{p.name}</p>
                      <p className="text-xs text-ink/50">{p.provider_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button onClick={e => { e.stopPropagation(); toggleStatus(p); }}
                      className={`text-xs font-semibold px-3 py-1 rounded-full border transition ${p.status === "active" ? "border-red-200 text-red-600 hover:bg-red-50" : "border-green-200 text-green-700 hover:bg-green-50"}`}>
                      {p.status === "active" ? "Deactivate" : "Activate"}
                    </button>
                    {expanded === p._id ? <ChevronUp className="w-4 h-4 text-ink/40" /> : <ChevronDown className="w-4 h-4 text-ink/40" />}
                  </div>
                </div>
                {expanded === p._id && (
                  <div className="border-t border-ink/5 px-5 py-4 text-sm text-ink/70 space-y-1">
                    {p.base_url && <p><span className="font-medium text-ink">URL:</span> {p.base_url}</p>}
                    {p.notes    && <p><span className="font-medium text-ink">Notes:</span> {p.notes}</p>}
                    <p><span className="font-medium text-ink">Keys:</span> {keys.filter(k => k.provider_id === (p._id || p.id)).length} registered</p>
                    <p><span className="font-medium text-ink">Created:</span> {p.created_at ? new Date(p.created_at).toLocaleDateString() : "—"}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── API KEYS TAB ── */}
        {!loading && tab === "keys" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => setAddingKey(!addingKey)}
                className="flex items-center gap-2 bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gold/90">
                <Plus className="w-4 h-4" /> Add Key
              </button>
            </div>

            {addingKey && (
              <form onSubmit={addKey} className="bg-white border border-ink/10 rounded-xl p-5 space-y-3">
                <h3 className="font-bold text-sm">New API Key <span className="font-normal text-ink/50">(stored encrypted — plaintext never returned)</span></h3>
                <div className="grid grid-cols-2 gap-3">
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">Provider *</label>
                    <select required value={newKey.provider_id} onChange={e => setNewKey(k => ({...k, provider_id: e.target.value}))} className={inp}>
                      <option value="">Select provider…</option>
                      {providers.map(p => <option key={p._id || p.id} value={p._id || p.id}>{p.name}</option>)}
                    </select></div>
                  <div><label className="text-xs font-medium text-ink/60 mb-1 block">Label *</label>
                    <input required value={newKey.label} onChange={e => setNewKey(k => ({...k, label: e.target.value}))} className={inp} placeholder="e.g. Production key" /></div>
                </div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">API Key *</label>
                  <input required type="password" value={newKey.plaintext_key} onChange={e => setNewKey(k => ({...k, plaintext_key: e.target.value}))} className={inp} placeholder="sk-…" /></div>
                <div><label className="text-xs font-medium text-ink/60 mb-1 block">Scope</label>
                  <select value={newKey.scope} onChange={e => setNewKey(k => ({...k, scope: e.target.value}))} className={inp}>
                    {["chat","tts","embeddings","images","all"].map(s => <option key={s}>{s}</option>)}
                  </select></div>
                <div className="flex gap-2">
                  <button type="submit" disabled={savingKey} className="bg-gold text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
                    {savingKey ? "Saving…" : "Save Key"}
                  </button>
                  <button type="button" onClick={() => setAddingKey(false)} className="text-sm px-4 py-2 rounded-lg border border-ink/20">Cancel</button>
                </div>
              </form>
            )}

            {keys.length === 0 && <p className="text-ink/50 text-sm text-center py-10">No keys registered.</p>}
            {keys.map(k => {
              const provider = providers.find(p => (p._id || p.id) === k.provider_id);
              return (
                <div key={k._id || k.id} className="bg-white border border-ink/10 rounded-xl px-5 py-4 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-ink">{k.label}</p>
                    <p className="text-xs text-ink/50">{provider?.name || k.provider_id} · scope: {k.scope} · added {k.created_at ? new Date(k.created_at).toLocaleDateString() : "—"}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => testKey(k._id || k.id)} disabled={testing[k._id || k.id]}
                      className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-ink/20 hover:bg-ink/5 disabled:opacity-50">
                      {testing[k._id || k.id] ? <RefreshCw className="w-3 h-3 animate-spin" /> : <FlaskConical className="w-3 h-3" />}
                      Test
                    </button>
                    <button onClick={() => deleteKey(k._id || k.id, k.label)}
                      className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50">
                      <Trash2 className="w-3 h-3" /> Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── USAGE LOG TAB ── */}
        {tab === "usage" && (
          <div className="bg-white border border-ink/10 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-ink/5 flex items-center justify-between">
              <h2 className="font-bold text-sm flex items-center gap-2"><Activity className="w-4 h-4" /> Usage Log</h2>
              <button onClick={loadUsage} className="text-xs text-ink/50 hover:text-ink flex items-center gap-1"><RefreshCw className="w-3 h-3" /> Refresh</button>
            </div>
            <div className="divide-y divide-ink/5 max-h-[600px] overflow-y-auto">
              {usageLog.length === 0 && <p className="text-center py-8 text-ink/50 text-sm">No usage recorded yet.</p>}
              {usageLog.map((entry, i) => (
                <div key={i} className="px-5 py-3 flex items-start justify-between gap-4 text-sm">
                  <div>
                    <p className="font-medium text-ink">{entry.action || entry.provider_id || "—"}</p>
                    <p className="text-xs text-ink/50 mt-0.5">{entry.actor_id || entry.user_id || "system"} · {entry.model || ""}</p>
                  </div>
                  <div className="text-right shrink-0">
                    {entry.tokens_used && <p className="text-xs font-mono text-ink/70">{entry.tokens_used} tokens</p>}
                    <p className="text-xs text-ink/40">{entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
