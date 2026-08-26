import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  TicketPercent, Plus, Trash2, Loader2, Copy, Power, KeyRound,
  ArrowLeft, CheckCircle2,
} from "lucide-react";

const TIERS = [
  { value: "free", label: "Free" },
  { value: "member", label: "Member" },
  { value: "plus", label: "Plus" },
  { value: "pro", label: "Pro" },
  { value: "patron", label: "Patron" },
];

const inputCls = "w-full px-3 py-2 text-sm border border-ink/15 rounded-lg focus:border-copper focus:outline-none focus:ring-2 focus:ring-copper/30 transition-all bg-white";
const labelCls = "block text-[11px] font-black uppercase tracking-widest text-ink/50 mb-1.5";

export default function AdminPromoCodes() {
  const [codes, setCodes] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    code: "", granted_tier: "member", label: "",
    max_uses: "", duration_days: "365", note: "",
  });

  const load = useCallback(() => {
    api.get("/admin/promo-codes")
      .then(({ data }) => setCodes(Array.isArray(data) ? data : []))
      .catch(() => toast.error("Could not load promo codes."));
  }, []);

  useEffect(load, [load]);

  const create = async (e) => {
    e.preventDefault();
    if (!form.code.trim()) { toast.error("Enter a code (at least 3 characters)."); return; }
    setBusy(true);
    try {
      await api.post("/admin/promo-codes", {
        code: form.code,
        granted_tier: form.granted_tier,
        label: form.label.trim() || null,
        max_uses: form.max_uses === "" ? null : Number(form.max_uses),
        duration_days: form.duration_days === "" ? null : Number(form.duration_days),
        note: form.note.trim() || null,
      });
      toast.success(`Promo code ${form.code.trim().toUpperCase()} created.`);
      setForm({ code: "", granted_tier: "member", label: "", max_uses: "", duration_days: "365", note: "" });
      setShowForm(false);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not create the code.");
    } finally { setBusy(false); }
  };

  const toggleActive = async (code) => {
    const target = codes.find((c) => c.code === code);
    if (!target) return;
    try {
      await api.patch(`/admin/promo-codes/${code}`, { active: !target.active });
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not update the code.");
    }
  };

  const remove = async (code) => {
    if (!window.confirm(`Delete promo code ${code}? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/promo-codes/${code}`);
      toast.success(`${code} deleted.`);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not delete the code.");
    }
  };

  const copy = async (code) => {
    try {
      await navigator.clipboard.writeText(code);
      toast.success(`Copied ${code}.`);
    } catch { toast.error("Clipboard unavailable — copy it manually."); }
  };

  const fmtDate = (iso) => {
    if (!iso) return "Never";
    try { return new Date(iso).toLocaleDateString(); } catch { return iso; }
  };

  const usedLabel = (c) => {
    if (c.max_uses == null) return `${c.uses_count ?? 0} used · unlimited`;
    return `${c.uses_count ?? 0} / ${c.max_uses} used`;
  };

  return (
    <AppShell>
      <div className="px-4 sm:px-8 py-8 max-w-5xl">
        <Link to="/admin" className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-ink/50 hover:text-copper transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Admin Overview
        </Link>

        <div className="mt-4 flex flex-wrap items-center gap-3 justify-between">
          <div>
            <div className="overline text-copper">Commerce</div>
            <h1 className="font-heading text-2xl sm:text-3xl font-black text-ink mt-1 flex items-center gap-2">
              <TicketPercent className="w-6 h-6 text-copper" /> Promo Codes
            </h1>
            <p className="text-sm text-ink/50 mt-1 max-w-xl">
              Codes grant a membership tier when entered at signup. Hand them out to
              testers, legacy students, and partners.
            </p>
          </div>
          <button
            onClick={() => setShowForm(s => !s)}
            className="inline-flex items-center gap-2 text-sm font-bold bg-copper text-white px-4 py-2.5 rounded-xl hover:bg-copper/90 transition-colors"
          >
            {showForm ? "Close form" : <><Plus className="w-4 h-4" /> New promo code</>}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <form onSubmit={create} className="mt-6 card-flat rounded-2xl p-5 space-y-4">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className={labelCls}>Code</label>
                <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })}
                  placeholder="e.g. SUMMER2026" className={inputCls} data-testid="promo-input-code" />
              </div>
              <div>
                <label className={labelCls}>Grants tier</label>
                <select value={form.granted_tier} onChange={(e) => setForm({ ...form, granted_tier: e.target.value })}
                  className={inputCls} data-testid="promo-input-tier">
                  {TIERS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Label <span className="normal-case font-medium text-ink/30">(optional)</span></label>
                <input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}
                  placeholder="e.g. Legacy Student" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Max uses <span className="normal-case font-medium text-ink/30">(blank = unlimited)</span></label>
                <input type="number" min="1" value={form.max_uses} onChange={(e) => setForm({ ...form, max_uses: e.target.value })}
                  placeholder="Unlimited" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Days of access <span className="normal-case font-medium text-ink/30">(blank = permanent)</span></label>
                <input type="number" min="1" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })}
                  placeholder="Permanent" className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Note <span className="normal-case font-medium text-ink/30">(internal)</span></label>
                <input value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })}
                  placeholder="Who is this for?" className={inputCls} />
              </div>
            </div>
            <button type="submit" disabled={busy}
              className="inline-flex items-center gap-2 text-sm font-bold bg-ink text-bone px-5 py-2.5 rounded-xl disabled:opacity-50">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <KeyRound className="w-4 h-4" />}
              Create code
            </button>
          </form>
        )}

        {/* List */}
        <div className="mt-8 space-y-3">
          {codes === null ? (
            <div className="flex items-center gap-2 text-ink/40 text-sm py-10 justify-center">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading…
            </div>
          ) : codes.length === 0 ? (
            <div className="card-flat rounded-2xl p-10 text-center">
              <KeyRound className="w-10 h-10 text-ink/20 mx-auto mb-3" />
              <p className="text-ink/50 text-sm">No promo codes yet. Create your first one above.</p>
            </div>
          ) : (
            codes.map((c) => {
              const tierStyle = TIERS.find((t) => t.value === c.granted_tier);
              return (
                <div key={c.code} className={`card-flat rounded-2xl p-4 flex flex-wrap items-center gap-3 ${!c.active ? "opacity-60" : ""}`}>
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="font-mono font-black text-sm text-ink bg-bone border border-ink/10 rounded-lg px-3 py-2">
                      {c.code}
                    </div>
                    <span className="badge-signal text-[10px]" style={{ background: tierStyle ? "#FFD100" : "#eee", color: "#2e1065" }}>
                      {tierStyle ? tierStyle.label : c.granted_tier}
                    </span>
                    <div className="min-w-0">
                      {c.label && c.label !== c.code && (
                        <div className="text-xs font-bold text-ink truncate">{c.label}</div>
                      )}
                      <div className="text-[11px] text-ink/45">
                        {usedLabel(c)} · Expires {fmtDate(c.expires_at)}
                        {c.duration_days ? ` · ${c.duration_days}d access` : ""}
                      </div>
                      {c.note && <div className="text-[11px] text-ink/40 italic truncate max-w-xs">“{c.note}”</div>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button onClick={() => copy(c.code)} title="Copy code"
                      className="p-2 rounded-lg text-ink/40 hover:text-copper hover:bg-copper/10 transition-colors">
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => toggleActive(c.code)}
                      title={c.active ? "Deactivate" : "Activate"}
                      className={`p-2 rounded-lg transition-colors ${c.active ? "text-green-600 hover:bg-green-50" : "text-ink/30 hover:bg-ink/5"}`}
                    >
                      <Power className="w-4 h-4" />
                    </button>
                    <button onClick={() => remove(c.code)} title="Delete"
                      className="p-2 rounded-lg text-ink/30 hover:text-red-600 hover:bg-red-50 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {c.active ? (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-widest text-green-600 ml-1">
                        <CheckCircle2 className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-widest text-ink/30 ml-1">
                        <Power className="w-3 h-3" /> Off
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </AppShell>
  );
}
