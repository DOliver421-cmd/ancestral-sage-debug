/**
 * PersonaManagementConsole — Admin CRUD for AI personas.
 *
 * Executive-only control panel for managing platform AI personas.
 * Every change writes to the immutable audit log.
 */

import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Plus, Save, Trash2, RefreshCw, ChevronUp, ChevronDown,
  CheckCircle2, XCircle, Loader2,
} from "lucide-react";

const COPPER = "#C0572D";
const GREEN = "#1B4332";
const BONE = "#FDFBF5";

const EMPTY = {
  persona_id: "",
  name: "",
  system_prompt: "",
  priority: 100,
  active: true,
  allowed_roles: ["admin", "executive_admin"],
  model_override: "",
};

export default function PersonaManagementConsole() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ ...EMPTY });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/personas");
      setList(data || []);
    } catch {
      toast.error("Could not load personas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const startCreate = () => {
    setEditing("create");
    setForm({ ...EMPTY });
    setError("");
  };

  const startEdit = (p) => {
    setEditing(p.persona_id);
    setForm({
      persona_id: p.persona_id,
      name: p.name,
      system_prompt: p.system_prompt,
      priority: p.priority,
      active: p.active,
      allowed_roles: p.allowed_roles || [],
      model_override: p.model_override || "",
    });
    setError("");
  };

  const cancel = () => {
    setEditing(null);
    setForm({ ...EMPTY });
    setError("");
  };

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      if (!form.persona_id.trim() || !form.name.trim() || !form.system_prompt.trim()) {
        throw new Error("persona_id, name, and system_prompt are required.");
      }
      if (editing === "create") {
        await api.post("/personas", form);
        toast.success("Persona created.");
      } else {
        await api.put(`/personas/${form.persona_id}`, form);
        toast.success("Persona updated.");
      }
      await load();
      cancel();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Save failed.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const archive = async (p) => {
    if (!confirm(`Archive persona "${p.name}"? This sets active=false.`)) return;
    try {
      await api.delete(`/personas/${p.persona_id}`);
      toast.success("Persona archived.");
      await load();
    } catch {
      toast.error("Archive failed.");
    }
  };

  const movePriority = async (p, delta) => {
    const newPriority = Math.max(0, p.priority + delta);
    try {
      await api.put(`/personas/${p.persona_id}/priority`, { priority: newPriority });
      await load();
    } catch {
      toast.error("Priority update failed.");
    }
  };

  const setField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-bone">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
          <div>
            <div className="overline text-copper text-xs tracking-widest">AI Governance</div>
            <h1 className="font-heading text-3xl font-bold mt-1">Persona Management</h1>
            <p className="text-sm text-ink/50 mt-1">
              Create, edit, reorder, and archive AI personas. Every change is audit-logged.
            </p>
          </div>
          <button
            onClick={startCreate}
            className="flex items-center gap-2 text-xs font-black uppercase tracking-widest px-5 py-2.5 rounded-xl text-white"
            style={{ background: GREEN }}
          >
            <Plus className="w-4 h-4" /> New Persona
          </button>
        </div>

        {/* Editor */}
        {editing && (
          <div className="card-flat rounded-2xl p-6 border bg-white mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-heading font-bold text-lg">
                {editing === "create" ? "Create Persona" : `Edit: ${form.persona_id}`}
              </h2>
              <button onClick={cancel} className="text-xs text-ink/50 hover:text-ink">Cancel</button>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <label className="block">
                <span className="text-xs font-bold text-ink/60">Persona ID (slug)</span>
                <input
                  value={form.persona_id}
                  onChange={(e) => setField("persona_id", e.target.value)}
                  disabled={editing !== "create"}
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm disabled:bg-ink/5"
                  placeholder="e.g. revenue_director"
                />
              </label>

              <label className="block">
                <span className="text-xs font-bold text-ink/60">Name</span>
                <input
                  value={form.name}
                  onChange={(e) => setField("name", e.target.value)}
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm"
                  placeholder="Display name"
                />
              </label>

              <label className="block md:col-span-2">
                <span className="text-xs font-bold text-ink/60">System Prompt</span>
                <textarea
                  value={form.system_prompt}
                  onChange={(e) => setField("system_prompt", e.target.value)}
                  rows={8}
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm font-mono"
                  placeholder="Full markdown directive text..."
                />
              </label>

              <label className="block">
                <span className="text-xs font-bold text-ink/60">Priority</span>
                <input
                  type="number"
                  value={form.priority}
                  onChange={(e) => setField("priority", parseInt(e.target.value || "0", 10))}
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm"
                />
              </label>

              <label className="block">
                <span className="text-xs font-bold text-ink/60">Model Override (optional)</span>
                <input
                  value={form.model_override}
                  onChange={(e) => setField("model_override", e.target.value)}
                  className="mt-1 w-full px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm"
                  placeholder="e.g. claude-3-opus"
                />
              </label>

              <label className="block flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(e) => setField("active", e.target.checked)}
                  className="accent-[#1B4332]"
                />
                <span className="text-xs font-bold text-ink/60">Active</span>
              </label>
            </div>

            {error && (
              <div className="mt-4 text-xs font-bold text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <div className="mt-4 flex items-center gap-3">
              <button
                onClick={save}
                disabled={saving}
                className="flex items-center gap-2 text-xs font-black uppercase tracking-widest px-5 py-2.5 rounded-xl text-white disabled:opacity-50"
                style={{ background: GREEN }}
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save
              </button>
            </div>
          </div>
        )}

        {/* List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-copper" />
          </div>
        ) : (
          <div className="space-y-3">
            {list.map((p) => (
              <div key={p.persona_id} className="card-flat rounded-2xl p-5 border bg-white">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-bold text-lg">{p.name}</span>
                      <span className="text-xs font-mono text-ink/40">/{p.persona_id}</span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${p.active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {p.active ? "Active" : "Archived"}
                      </span>
                      <span className="text-xs text-ink/40">priority: {p.priority}</span>
                    </div>
                    <p className="text-xs text-ink/40 mt-1 line-clamp-2 font-mono">
                      {p.system_prompt.slice(0, 160)}...
                    </p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button onClick={() => movePriority(p, -1)} className="p-2 rounded-lg hover:bg-bone" title="Increase priority">
                      <ChevronUp className="w-4 h-4 text-ink/50" />
                    </button>
                    <button onClick={() => movePriority(p, 1)} className="p-2 rounded-lg hover:bg-bone" title="Decrease priority">
                      <ChevronDown className="w-4 h-4 text-ink/50" />
                    </button>
                    <button onClick={() => startEdit(p)} className="p-2 rounded-lg hover:bg-bone text-xs font-bold" style={{ color: GREEN }}>
                      Edit
                    </button>
                    <button onClick={() => archive(p)} className="p-2 rounded-lg hover:bg-bone" title="Archive">
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {list.length === 0 && (
              <p className="text-sm text-ink/40 italic py-8 text-center">No personas defined. Click "New Persona" to create one.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
