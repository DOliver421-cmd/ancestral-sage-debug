import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { Navigate } from "react-router-dom";

const ROLE_RANK = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };

function fmt(val) {
  if (val === null || val === undefined) return "—";
  const n = Number(val);
  return isNaN(n) ? String(val) : n % 1 === 0 ? n.toLocaleString() : n.toFixed(2);
}

export default function PlatformPrices() {
  const { user } = useAuth();
  const isAdmin = ROLE_RANK[user?.role] >= 3;
  const isExec  = ROLE_RANK[user?.role] >= 4;

  const [prices, setPrices]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [editing, setEditing]   = useState(null); // { id, key, value, description }
  const [creating, setCreating] = useState(false);
  const [form, setForm]         = useState({ key: "", value: "", description: "" });
  const [saving, setSaving]     = useState(false);
  const [deleting, setDeleting] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get("/admin/prices");
      setPrices(r.data.prices || []);
    } catch {
      toast.error("Failed to load prices");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (!user) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;

  const openCreate = () => {
    setForm({ key: "", value: "", description: "" });
    setCreating(true);
  };

  const openEdit = (p) => {
    setForm({ key: p.key, value: String(p.value), description: p.description || "" });
    setEditing(p);
  };

  const saveCreate = async () => {
    if (!form.key.trim()) { toast.error("Key is required"); return; }
    if (form.value === "" || isNaN(Number(form.value))) { toast.error("Value must be a number"); return; }
    setSaving(true);
    try {
      await api.post("/admin/prices", { key: form.key.trim(), value: Number(form.value), description: form.description });
      toast.success("Price created");
      setCreating(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to create");
    } finally { setSaving(false); }
  };

  const saveEdit = async () => {
    if (!form.key.trim()) { toast.error("Key is required"); return; }
    if (form.value === "" || isNaN(Number(form.value))) { toast.error("Value must be a number"); return; }
    setSaving(true);
    try {
      await api.patch(`/admin/prices/${editing.id}`, {
        key: form.key.trim(),
        value: Number(form.value),
        description: form.description,
      });
      toast.success("Price updated");
      setEditing(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to update");
    } finally { setSaving(false); }
  };

  const confirmDelete = async (p) => {
    if (!window.confirm(`Delete price key "${p.key}"? This cannot be undone.`)) return;
    setDeleting(p.id);
    try {
      await api.delete(`/admin/prices/${p.id}`);
      toast.success("Price deleted");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to delete");
    } finally { setDeleting(null); }
  };

  const filtered = prices.filter(p =>
    p.key.toLowerCase().includes(search.toLowerCase()) ||
    (p.description || "").toLowerCase().includes(search.toLowerCase())
  );

  const modalOpen = creating || !!editing;
  const modalTitle = creating ? "New Price" : "Edit Price";
  const modalSave  = creating ? saveCreate : saveEdit;

  return (
    <div className="min-h-screen bg-stone-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-heading font-bold text-ink">Platform Prices</h1>
            <p className="text-sm text-ink/50 mt-1">
              Manage pricing keys used across the platform. Changes take effect immediately.
            </p>
          </div>
          <button
            onClick={openCreate}
            className="px-4 py-2 rounded-lg font-bold text-sm"
            style={{ background: "#b45309", color: "white" }}
          >
            + New Price
          </button>
        </div>

        {/* Search */}
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by key or description…"
          className="w-full border border-ink/15 rounded-lg px-3 py-2 text-sm mb-4 outline-none focus:border-copper"
        />

        {/* Table */}
        <div className="bg-white rounded-xl border border-ink/10 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-sm text-ink/40">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-sm text-ink/40">
              {prices.length === 0 ? "No prices defined yet. Click '+ New Price' to add one." : "No results match your search."}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink/10 bg-stone-50">
                  <th className="text-left px-4 py-3 font-bold text-ink/60 text-xs uppercase tracking-wide">Key</th>
                  <th className="text-right px-4 py-3 font-bold text-ink/60 text-xs uppercase tracking-wide">Value</th>
                  <th className="text-left px-4 py-3 font-bold text-ink/60 text-xs uppercase tracking-wide hidden md:table-cell">Description</th>
                  <th className="text-left px-4 py-3 font-bold text-ink/60 text-xs uppercase tracking-wide hidden lg:table-cell">Last Modified</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {filtered.map((p, i) => (
                  <tr key={p.id} className={`border-b border-ink/5 hover:bg-stone-50 ${i % 2 === 0 ? "" : "bg-white"}`}>
                    <td className="px-4 py-3 font-mono text-xs font-bold text-ink">{p.key}</td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-copper">{fmt(p.value)}</td>
                    <td className="px-4 py-3 text-ink/60 hidden md:table-cell">{p.description || <span className="text-ink/25 italic">—</span>}</td>
                    <td className="px-4 py-3 text-ink/40 text-xs hidden lg:table-cell">
                      {p.last_modified_at ? new Date(p.last_modified_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => openEdit(p)}
                          className="text-xs font-bold px-3 py-1 rounded border border-ink/15 hover:bg-stone-100"
                        >
                          Edit
                        </button>
                        {isExec && (
                          <button
                            onClick={() => confirmDelete(p)}
                            disabled={deleting === p.id}
                            className="text-xs font-bold px-3 py-1 rounded border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-40"
                          >
                            {deleting === p.id ? "…" : "Delete"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="mt-3 text-xs text-ink/35 text-right">
          {filtered.length} of {prices.length} price{prices.length !== 1 ? "s" : ""}
          {" · "}Edit requires admin · Delete requires executive_admin
        </div>
      </div>

      {/* Create / Edit Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.5)" }}
          onClick={e => e.target === e.currentTarget && (creating ? setCreating(false) : setEditing(null))}
        >
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
              <span className="font-heading font-bold text-ink">{modalTitle}</span>
              <button onClick={() => creating ? setCreating(false) : setEditing(null)} className="text-ink/40 hover:text-ink text-xl leading-none">×</button>
            </div>

            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Key</label>
                <input
                  value={form.key}
                  onChange={e => setForm(f => ({ ...f, key: e.target.value }))}
                  placeholder="e.g. course.basic"
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm font-mono outline-none focus:border-copper"
                />
                <p className="text-xs text-ink/35 mt-1">Use dot notation: course.basic, api.free_tier_limit</p>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Value</label>
                <input
                  type="number"
                  step="any"
                  value={form.value}
                  onChange={e => setForm(f => ({ ...f, value: e.target.value }))}
                  placeholder="e.g. 49.00"
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm font-mono outline-none focus:border-copper"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Description</label>
                <input
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="Human-readable description of this price"
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm outline-none focus:border-copper"
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-ink/10 flex justify-end gap-3">
              <button
                onClick={() => creating ? setCreating(false) : setEditing(null)}
                className="text-sm text-ink/50 px-4 py-2 hover:text-ink"
              >
                Cancel
              </button>
              <button
                onClick={modalSave}
                disabled={saving}
                className="px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50"
                style={{ background: "#b45309", color: "white" }}
              >
                {saving ? "Saving…" : creating ? "Create" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
