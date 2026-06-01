import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";

const ROLE_RANK = { student: 1, instructor: 2, admin: 3, executive_admin: 4 };

const CATEGORIES = [
  { key: "revenue_restored",  label: "Revenue Restored",   color: "#16a34a" },
  { key: "risk_eliminated",   label: "Risk Eliminated",    color: "#0369a1" },
  { key: "cost_avoided",      label: "Cost Avoided",       color: "#7c3aed" },
  { key: "debt_repaid",       label: "Technical Debt",     color: "#b45309" },
  { key: "governance",        label: "Governance",         color: "#0891b2" },
];

const STATUSES = ["PASS", "FAIL", "UNVERIFIED", "INCOMPLETE", "NO_EVIDENCE"];
const RISKS    = ["none", "low", "medium", "high", "critical"];

const STATUS_STYLE = {
  PASS:        { bg: "#dcfce7", color: "#166534", label: "PASS" },
  FAIL:        { bg: "#fee2e2", color: "#991b1b", label: "FAIL" },
  UNVERIFIED:  { bg: "#fef9c3", color: "#92400e", label: "UNVERIFIED — requires correction" },
  INCOMPLETE:  { bg: "#fed7aa", color: "#9a3412", label: "INCOMPLETE — requires self-correction" },
  NO_EVIDENCE: { bg: "#f1f5f9", color: "#475569", label: "NO EVIDENCE — value not counted" },
};

const RISK_STYLE = {
  none:     { color: "#6b7280" },
  low:      { color: "#16a34a" },
  medium:   { color: "#d97706" },
  high:     { color: "#dc2626" },
  critical: { color: "#7f1d1d", fontWeight: 800 },
};

function usd(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return "$" + Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function Badge({ status }) {
  const s = STATUS_STYLE[status] || STATUS_STYLE.UNVERIFIED;
  return (
    <span style={{ background: s.bg, color: s.color, fontSize: 10, fontWeight: 800,
      padding: "2px 7px", borderRadius: 4, whiteSpace: "nowrap", letterSpacing: 0.3 }}>
      {s.label}
    </span>
  );
}

function RiskTag({ level }) {
  const s = RISK_STYLE[level] || RISK_STYLE.none;
  return <span style={{ ...s, fontSize: 11, fontWeight: s.fontWeight || 600, textTransform: "uppercase" }}>{level}</span>;
}

// ── Add Entry Modal ────────────────────────────────────────────────────────────
function AddEntryModal({ onSave, onClose }) {
  const [form, setForm] = useState({
    description: "", category: "governance", dollar_value: "",
    evidence: "", status: "PASS", risk_level: "none",
    commit_sha: "", delivery_date: new Date().toISOString().slice(0, 10),
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    if (!form.description.trim()) { toast.error("Description required"); return; }
    if (!form.evidence.trim())    { toast.error("Evidence reference required"); return; }
    if (form.dollar_value === "" || isNaN(Number(form.dollar_value))) {
      toast.error("Dollar value must be a number"); return;
    }
    setSaving(true);
    try {
      await onSave({ ...form, dollar_value: Number(form.dollar_value) });
      onClose();
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.6)" }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between"
          style={{ background: "#0f172a" }}>
          <div>
            <div style={{ color: "white", fontWeight: 800, fontSize: 14 }}>Record Verified Delivery</div>
            <div style={{ color: "rgba(255,255,255,0.45)", fontSize: 11 }}>Director / Finance Director only</div>
          </div>
          <button onClick={onClose} style={{ color: "rgba(255,255,255,0.5)", fontSize: 20, background: "none", border: "none", cursor: "pointer" }}>×</button>
        </div>
        <div className="px-6 py-5 space-y-3">
          {[["Description", "description", "text", "What was delivered"],
            ["Evidence", "evidence", "text", "commit SHA, route, file path, test result"],
            ["Commit SHA (optional)", "commit_sha", "text", "e.g. dcabad0"],
            ["Delivery Date", "delivery_date", "date", ""]
          ].map(([label, key, type, ph]) => (
            <div key={key}>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">{label}</label>
              <input type={type} value={form[key]} onChange={set(key)} placeholder={ph}
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm outline-none focus:border-copper" />
            </div>
          ))}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Category</label>
              <select value={form.category} onChange={set("category")}
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm">
                {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Dollar Value</label>
              <input type="number" value={form.dollar_value} onChange={set("dollar_value")} placeholder="0.00"
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm font-mono outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Status</label>
              <select value={form.status} onChange={set("status")}
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm">
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Risk Level</label>
              <select value={form.risk_level} onChange={set("risk_level")}
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm">
                {RISKS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
        </div>
        <div className="px-6 py-4 border-t border-ink/10 flex justify-end gap-3">
          <button onClick={onClose} className="text-sm text-ink/50 px-4 py-2 hover:text-ink">Cancel</button>
          <button onClick={submit} disabled={saving}
            className="px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50"
            style={{ background: "#0f172a", color: "white" }}>
            {saving ? "Recording…" : "Record Delivery"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Edit Status Modal ──────────────────────────────────────────────────────────
function EditStatusModal({ entry, onSave, onClose }) {
  const [form, setForm] = useState({
    status: entry.status, dollar_value: String(entry.dollar_value),
    evidence: entry.evidence, risk_level: entry.risk_level || "none",
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));
  const submit = async () => {
    setSaving(true);
    try { await onSave(entry.id, { ...form, dollar_value: Number(form.dollar_value) }); onClose(); }
    finally { setSaving(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.6)" }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="px-6 py-4 border-b border-ink/10 flex items-center justify-between">
          <span className="font-bold text-ink text-sm">Correct Entry</span>
          <button onClick={onClose} className="text-ink/40 hover:text-ink text-xl leading-none bg-transparent border-none cursor-pointer">×</button>
        </div>
        <div className="px-6 py-4 space-y-3">
          <div className="text-xs text-ink/50 font-mono bg-stone-50 rounded px-3 py-2">{entry.description}</div>
          {[["Status", "status", STATUSES], ["Risk Level", "risk_level", RISKS]].map(([label, key, opts]) => (
            <div key={key}>
              <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">{label}</label>
              <select value={form[key]} onChange={set(key)}
                className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm">
                {opts.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
          ))}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Dollar Value</label>
            <input type="number" value={form.dollar_value} onChange={set("dollar_value")}
              className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm font-mono outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">Evidence</label>
            <input type="text" value={form.evidence} onChange={set("evidence")}
              className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm outline-none" />
          </div>
        </div>
        <div className="px-6 py-4 border-t border-ink/10 flex justify-end gap-3">
          <button onClick={onClose} className="text-sm text-ink/50 px-4 py-2">Cancel</button>
          <button onClick={submit} disabled={saving}
            className="px-5 py-2 rounded-lg font-bold text-sm disabled:opacity-50"
            style={{ background: "#0f172a", color: "white" }}>
            {saving ? "Saving…" : "Save Correction"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function AuditorDashboard() {
  const { user } = useAuth();
  const isAdmin = ROLE_RANK[user?.role] >= 3;

  const [summary, setSummary]         = useState(null);
  const [entries, setEntries]         = useState([]);
  const [total, setTotal]             = useState(0);
  const [loading, setLoading]         = useState(true);
  const [tab, setTab]                 = useState("ledger"); // ledger | debt | risks | report
  const [filterCat, setFilterCat]     = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRisk, setFilterRisk]   = useState("");
  const [adding, setAdding]           = useState(false);
  const [editing, setEditing]         = useState(null);
  const [debt, setDebt]               = useState(null);
  const [risks, setRisks]             = useState(null);
  const [reportData, setReportData]   = useState(null);
  const [reportStart, setReportStart] = useState("");
  const [reportEnd, setReportEnd]     = useState("");

  const loadSummary = useCallback(async () => {
    try { const r = await api.get("/auditor/summary"); setSummary(r.data); } catch {}
  }, []);

  const loadEntries = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: 200 });
      if (filterCat)    params.set("category", filterCat);
      if (filterStatus) params.set("status", filterStatus);
      if (filterRisk)   params.set("risk_level", filterRisk);
      const r = await api.get(`/auditor/ledger?${params}`);
      setEntries(r.data.entries || []);
      setTotal(r.data.total || 0);
    } catch { toast.error("Failed to load ledger"); }
    finally { setLoading(false); }
  }, [filterCat, filterStatus, filterRisk]);

  const loadDebt = useCallback(async () => {
    try { const r = await api.get("/auditor/debt"); setDebt(r.data); } catch {}
  }, []);

  const loadRisks = useCallback(async () => {
    try { const r = await api.get("/auditor/risks"); setRisks(r.data); } catch {}
  }, []);

  const loadReport = async () => {
    try {
      const params = new URLSearchParams();
      if (reportStart) params.set("start", reportStart);
      if (reportEnd)   params.set("end", reportEnd);
      const r = await api.get(`/auditor/report?${params}`);
      setReportData(r.data);
    } catch { toast.error("Failed to generate report"); }
  };

  useEffect(() => { loadSummary(); loadEntries(); }, [loadSummary, loadEntries]);
  useEffect(() => { if (tab === "debt") loadDebt(); }, [tab, loadDebt]);
  useEffect(() => { if (tab === "risks") loadRisks(); }, [tab, loadRisks]);

  const addEntry = async (data) => {
    try {
      await api.post("/auditor/ledger", data);
      toast.success("Delivery recorded");
      loadSummary(); loadEntries();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); throw e; }
  };

  const updateEntry = async (id, data) => {
    try {
      await api.patch(`/auditor/ledger/${id}`, data);
      toast.success("Entry corrected");
      loadSummary(); loadEntries();
      if (tab === "debt") loadDebt();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); throw e; }
  };

  if (!user) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/dashboard" replace />;

  const INK = "#0f172a";
  const TABS = [
    { key: "ledger",  label: "Ledger" },
    { key: "debt",    label: "Debt & Incomplete" },
    { key: "risks",   label: "Risk Items" },
    { key: "report",  label: "On-Demand Report" },
  ];

  const totalVerified = summary?.verified_dollar_value ?? 0;
  const totalAll      = summary?.total_dollar_value ?? 0;

  return (
    <div className="min-h-screen" style={{ background: "#f8fafc" }}>
      {/* Header */}
      <div style={{ background: INK, color: "white", padding: "20px 28px 0" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <div style={{ width: 32, height: 32, background: "#fbbf24", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 900, fontSize: 14, color: INK }}>A</div>
                <div>
                  <div style={{ fontWeight: 900, fontSize: 18, letterSpacing: -0.3 }}>The Auditor</div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", fontWeight: 600 }}>Read-only · Evidence-based · No system modifications</div>
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button onClick={() => { loadSummary(); loadEntries(); }}
                style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "white", padding: "6px 14px", borderRadius: 7, fontSize: 12, cursor: "pointer", fontWeight: 700 }}>
                ↻ Refresh
              </button>
              <button onClick={() => setAdding(true)}
                style={{ background: "#fbbf24", border: "none", color: INK, padding: "6px 14px", borderRadius: 7, fontSize: 12, cursor: "pointer", fontWeight: 800 }}>
                + Record Delivery
              </button>
            </div>
          </div>

          {/* Summary row */}
          {summary && (
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap", paddingBottom: 4, borderBottom: "1px solid rgba(255,255,255,0.08)", marginBottom: 0 }}>
              {[
                ["Total Value Delivered", usd(totalAll), "#fbbf24"],
                ["Verified (PASS)", usd(totalVerified), "#4ade80"],
                ["Unverified", `${summary.unverified_count} item${summary.unverified_count !== 1 ? "s" : ""}`, "#f87171"],
                ["High/Critical Risk", `${(summary.risk_distribution?.high || 0) + (summary.risk_distribution?.critical || 0)}`, "#f97316"],
              ].map(([label, val, color]) => (
                <div key={label} style={{ paddingBottom: 16 }}>
                  <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
                  <div style={{ color, fontSize: 20, fontWeight: 900, marginTop: 2 }}>{val}</div>
                </div>
              ))}
            </div>
          )}

          {/* Tab bar */}
          <div style={{ display: "flex", gap: 0 }}>
            {TABS.map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                style={{
                  background: "none", border: "none", color: tab === t.key ? "#fbbf24" : "rgba(255,255,255,0.5)",
                  fontWeight: tab === t.key ? 800 : 600, fontSize: 13, padding: "12px 18px",
                  borderBottom: tab === t.key ? "2px solid #fbbf24" : "2px solid transparent",
                  cursor: "pointer", transition: "color 0.15s",
                }}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 28px" }}>

        {/* ── LEDGER TAB ── */}
        {tab === "ledger" && (
          <div>
            {/* Category breakdown */}
            {summary?.by_category?.length > 0 && (
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 20 }}>
                {summary.by_category.map(c => {
                  const meta = CATEGORIES.find(x => x.key === c._id) || { color: "#6b7280", label: c._id };
                  return (
                    <div key={c._id} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 10, padding: "10px 16px", minWidth: 150 }}>
                      <div style={{ color: meta.color, fontWeight: 800, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>{meta.label}</div>
                      <div style={{ fontWeight: 900, fontSize: 18, color: INK, marginTop: 2 }}>{usd(c.total_value)}</div>
                      <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>{c.count} entr{c.count !== 1 ? "ies" : "y"} · {usd(c.verified_value)} verified</div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Filters */}
            <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
              <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
                className="border border-ink/15 rounded-lg px-3 py-2 text-sm">
                <option value="">All Categories</option>
                {CATEGORIES.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
              </select>
              <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
                className="border border-ink/15 rounded-lg px-3 py-2 text-sm">
                <option value="">All Statuses</option>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={filterRisk} onChange={e => setFilterRisk(e.target.value)}
                className="border border-ink/15 rounded-lg px-3 py-2 text-sm">
                <option value="">All Risk Levels</option>
                {RISKS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            {/* Table */}
            <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
              {loading ? (
                <div style={{ padding: 40, textAlign: "center", color: "#94a3b8", fontSize: 13 }}>Loading ledger…</div>
              ) : entries.length === 0 ? (
                <div style={{ padding: 40, textAlign: "center", color: "#94a3b8", fontSize: 13 }}>
                  No entries. Use "Record Delivery" to add the first verified item.
                </div>
              ) : (
                <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #f1f5f9", background: "#f8fafc" }}>
                      {["Date", "Description", "Category", "Dollar Value", "Status", "Risk", "Evidence", ""].map(h => (
                        <th key={h} style={{ textAlign: h === "Dollar Value" ? "right" : "left", padding: "10px 14px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", fontSize: 10, letterSpacing: 0.5 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e, i) => {
                      const catMeta = CATEGORIES.find(c => c.key === e.category) || { color: "#6b7280", label: e.category };
                      return (
                        <tr key={e.id} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
                          <td style={{ padding: "10px 14px", color: "#64748b", whiteSpace: "nowrap" }}>
                            {e.delivery_date ? new Date(e.delivery_date).toLocaleDateString() : "—"}
                          </td>
                          <td style={{ padding: "10px 14px", color: INK, fontWeight: 600, maxWidth: 260 }}>
                            <div>{e.description}</div>
                            {e.commit_sha && <div style={{ fontFamily: "monospace", fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{e.commit_sha.slice(0, 8)}</div>}
                          </td>
                          <td style={{ padding: "10px 14px" }}>
                            <span style={{ color: catMeta.color, fontWeight: 700, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>{catMeta.label}</span>
                          </td>
                          <td style={{ padding: "10px 14px", textAlign: "right", fontFamily: "monospace", fontWeight: 800,
                            color: e.status === "NO_EVIDENCE" ? "#94a3b8" : e.status === "PASS" ? "#16a34a" : INK }}>
                            {e.status === "NO_EVIDENCE" ? <s>{usd(e.dollar_value)}</s> : usd(e.dollar_value)}
                          </td>
                          <td style={{ padding: "10px 14px" }}><Badge status={e.status} /></td>
                          <td style={{ padding: "10px 14px" }}><RiskTag level={e.risk_level || "none"} /></td>
                          <td style={{ padding: "10px 14px", color: "#64748b", fontFamily: "monospace", fontSize: 10, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            <span title={e.evidence}>{e.evidence}</span>
                          </td>
                          <td style={{ padding: "10px 14px" }}>
                            <button onClick={() => setEditing(e)}
                              style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 5, border: "1px solid #e2e8f0", background: "white", cursor: "pointer", color: "#475569" }}>
                              Correct
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr style={{ borderTop: "2px solid #e2e8f0", background: "#f8fafc" }}>
                      <td colSpan={3} style={{ padding: "10px 14px", fontWeight: 700, fontSize: 11, color: "#64748b" }}>
                        {total} entr{total !== 1 ? "ies" : "y"}
                      </td>
                      <td style={{ padding: "10px 14px", textAlign: "right", fontWeight: 900, fontSize: 14, color: INK, fontFamily: "monospace" }}>
                        {usd(entries.reduce((s, e) => s + (e.status !== "NO_EVIDENCE" ? (e.dollar_value || 0) : 0), 0))}
                      </td>
                      <td colSpan={4} />
                    </tr>
                  </tfoot>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── DEBT TAB ── */}
        {tab === "debt" && (
          <div>
            {!debt ? (
              <div style={{ textAlign: "center", color: "#94a3b8", padding: 40 }}>Loading…</div>
            ) : (
              <>
                <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
                  {[
                    ["Outstanding Items", debt.total_debt_count, "#dc2626"],
                    ["Debt Value", usd(debt.total_debt_value), "#b45309"],
                  ].map(([l, v, c]) => (
                    <div key={l} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 10, padding: "12px 20px" }}>
                      <div style={{ color: "#64748b", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>{l}</div>
                      <div style={{ color: c, fontWeight: 900, fontSize: 22, marginTop: 2 }}>{v}</div>
                    </div>
                  ))}
                </div>
                {debt.debt_items.length === 0 ? (
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: 24, textAlign: "center", color: "#166534", fontWeight: 700 }}>
                    ✓ No outstanding debt or incomplete items.
                  </div>
                ) : (
                  <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
                    <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid #f1f5f9", background: "#fef2f2" }}>
                          {["Date", "Description", "Status", "Dollar Value", "Risk", "Evidence", ""].map(h => (
                            <th key={h} style={{ textAlign: "left", padding: "10px 14px", fontWeight: 700, color: "#dc2626", textTransform: "uppercase", fontSize: 10 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {debt.debt_items.map((e, i) => (
                          <tr key={e.id} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
                            <td style={{ padding: "10px 14px", color: "#64748b" }}>{e.delivery_date ? new Date(e.delivery_date).toLocaleDateString() : "—"}</td>
                            <td style={{ padding: "10px 14px", color: INK, fontWeight: 600, maxWidth: 300 }}>{e.description}</td>
                            <td style={{ padding: "10px 14px" }}><Badge status={e.status} /></td>
                            <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 800, color: "#dc2626" }}>{usd(e.dollar_value)}</td>
                            <td style={{ padding: "10px 14px" }}><RiskTag level={e.risk_level || "none"} /></td>
                            <td style={{ padding: "10px 14px", color: "#64748b", fontFamily: "monospace", fontSize: 10 }}>{e.evidence}</td>
                            <td style={{ padding: "10px 14px" }}>
                              <button onClick={() => setEditing(e)}
                                style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 5, border: "1px solid #fecaca", background: "#fef2f2", cursor: "pointer", color: "#dc2626" }}>
                                Correct
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── RISKS TAB ── */}
        {tab === "risks" && (
          <div>
            {!risks ? (
              <div style={{ textAlign: "center", color: "#94a3b8", padding: 40 }}>Loading…</div>
            ) : (
              <>
                <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
                  {[
                    ["Critical", risks.critical_count, "#7f1d1d"],
                    ["High", risks.high_count, "#dc2626"],
                  ].map(([l, v, c]) => (
                    <div key={l} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 10, padding: "12px 20px" }}>
                      <div style={{ color: "#64748b", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5 }}>{l} Risk</div>
                      <div style={{ color: c, fontWeight: 900, fontSize: 22, marginTop: 2 }}>{v}</div>
                    </div>
                  ))}
                </div>
                {risks.risk_items.length === 0 ? (
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, padding: 24, textAlign: "center", color: "#166534", fontWeight: 700 }}>
                    ✓ No high or critical risk items on record.
                  </div>
                ) : (
                  <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
                    <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid #f1f5f9", background: "#fff7ed" }}>
                          {["Date", "Description", "Risk Level", "Category", "Status", "Dollar Value", "Evidence"].map(h => (
                            <th key={h} style={{ textAlign: "left", padding: "10px 14px", fontWeight: 700, color: "#92400e", textTransform: "uppercase", fontSize: 10 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {risks.risk_items.map((e, i) => {
                          const catMeta = CATEGORIES.find(c => c.key === e.category) || { color: "#6b7280", label: e.category };
                          return (
                            <tr key={e.id} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
                              <td style={{ padding: "10px 14px", color: "#64748b" }}>{e.delivery_date ? new Date(e.delivery_date).toLocaleDateString() : "—"}</td>
                              <td style={{ padding: "10px 14px", color: INK, fontWeight: 600, maxWidth: 280 }}>{e.description}</td>
                              <td style={{ padding: "10px 14px" }}><RiskTag level={e.risk_level} /></td>
                              <td style={{ padding: "10px 14px" }}><span style={{ color: catMeta.color, fontWeight: 700, fontSize: 10, textTransform: "uppercase" }}>{catMeta.label}</span></td>
                              <td style={{ padding: "10px 14px" }}><Badge status={e.status} /></td>
                              <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 800 }}>{usd(e.dollar_value)}</td>
                              <td style={{ padding: "10px 14px", color: "#64748b", fontFamily: "monospace", fontSize: 10 }}>{e.evidence}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── REPORT TAB ── */}
        {tab === "report" && (
          <div>
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 12, padding: "20px 24px", marginBottom: 20 }}>
              <div style={{ fontWeight: 800, color: INK, marginBottom: 12 }}>Generate On-Demand Report</div>
              <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
                {[["Start Date", reportStart, setReportStart], ["End Date", reportEnd, setReportEnd]].map(([l, v, s]) => (
                  <div key={l}>
                    <label className="block text-xs font-bold uppercase tracking-wide text-ink/50 mb-1">{l}</label>
                    <input type="date" value={v} onChange={e => s(e.target.value)}
                      className="border border-ink/20 rounded-lg px-3 py-2 text-sm outline-none" />
                  </div>
                ))}
                <button onClick={loadReport}
                  style={{ background: INK, color: "white", border: "none", padding: "8px 20px", borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: "pointer" }}>
                  Generate Report
                </button>
                <span style={{ fontSize: 11, color: "#94a3b8", alignSelf: "center" }}>Leave dates blank for all-time report.</span>
              </div>
            </div>

            {reportData && (
              <div>
                {/* Report header */}
                <div style={{ background: INK, color: "white", borderRadius: 12, padding: "20px 24px", marginBottom: 16 }}>
                  <div style={{ fontWeight: 900, fontSize: 16, marginBottom: 4 }}>The Auditor — Delivery Report</div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)" }}>
                    Period: {reportData.report_period.start} → {reportData.report_period.end} ·
                    Generated: {new Date(reportData.generated_at).toLocaleString()}
                  </div>
                  <div style={{ display: "flex", gap: 24, marginTop: 16, flexWrap: "wrap" }}>
                    {[
                      ["Total Entries", reportData.summary.total_entries, "white"],
                      ["Total Value", usd(reportData.summary.total_dollar_value), "#fbbf24"],
                      ["Verified Value", usd(reportData.summary.verified_dollar_value), "#4ade80"],
                      ["Unverified Value", usd(reportData.summary.unverified_dollar_value), "#f87171"],
                    ].map(([l, v, c]) => (
                      <div key={l}>
                        <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1 }}>{l}</div>
                        <div style={{ color: c, fontWeight: 900, fontSize: 18, marginTop: 2 }}>{v}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* By category */}
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
                  {Object.entries(reportData.by_category).map(([cat, val]) => {
                    const meta = CATEGORIES.find(c => c.key === cat) || { color: "#6b7280", label: cat };
                    return (
                      <div key={cat} style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 10, padding: "10px 16px" }}>
                        <div style={{ color: meta.color, fontWeight: 800, fontSize: 10, textTransform: "uppercase" }}>{meta.label}</div>
                        <div style={{ fontWeight: 900, fontSize: 16, color: INK }}>{usd(val)}</div>
                      </div>
                    );
                  })}
                </div>

                {/* Flags */}
                {(reportData.flags.unverified_count > 0 || reportData.flags.incomplete_count > 0 ||
                  reportData.flags.high_risk_count > 0 || reportData.flags.no_evidence_count > 0) && (
                  <div style={{ background: "#fef9c3", border: "1px solid #fde68a", borderRadius: 10, padding: "12px 18px", marginBottom: 16 }}>
                    <div style={{ fontWeight: 800, color: "#92400e", marginBottom: 8 }}>⚠ Flags</div>
                    {reportData.flags.unverified_count > 0 && <div style={{ color: "#92400e", fontSize: 12 }}>• {reportData.flags.unverified_count} UNVERIFIED — requires correction</div>}
                    {reportData.flags.incomplete_count > 0 && <div style={{ color: "#9a3412", fontSize: 12 }}>• {reportData.flags.incomplete_count} INCOMPLETE — requires self-correction</div>}
                    {reportData.flags.high_risk_count > 0 && <div style={{ color: "#dc2626", fontSize: 12 }}>• {reportData.flags.high_risk_count} high/critical risk items</div>}
                    {reportData.flags.no_evidence_count > 0 && <div style={{ color: "#475569", fontSize: 12 }}>• {reportData.flags.no_evidence_count} NO EVIDENCE — value not counted</div>}
                  </div>
                )}

                {/* Full entry list */}
                <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
                  <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid #f1f5f9", background: "#f8fafc" }}>
                        {["Date", "Description", "Category", "Value", "Status", "Risk", "Evidence"].map(h => (
                          <th key={h} style={{ textAlign: h === "Value" ? "right" : "left", padding: "10px 14px", fontWeight: 700, color: "#64748b", textTransform: "uppercase", fontSize: 10 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.entries.map((e, i) => {
                        const catMeta = CATEGORIES.find(c => c.key === e.category) || { color: "#6b7280", label: e.category };
                        return (
                          <tr key={e.id} style={{ borderBottom: "1px solid #f1f5f9", background: i % 2 === 0 ? "white" : "#fafafa" }}>
                            <td style={{ padding: "8px 14px", color: "#64748b", whiteSpace: "nowrap" }}>{e.delivery_date ? new Date(e.delivery_date).toLocaleDateString() : "—"}</td>
                            <td style={{ padding: "8px 14px", color: INK, fontWeight: 600 }}>{e.description}</td>
                            <td style={{ padding: "8px 14px" }}><span style={{ color: catMeta.color, fontWeight: 700, fontSize: 10, textTransform: "uppercase" }}>{catMeta.label}</span></td>
                            <td style={{ padding: "8px 14px", textAlign: "right", fontFamily: "monospace", fontWeight: 800 }}>{usd(e.dollar_value)}</td>
                            <td style={{ padding: "8px 14px" }}><Badge status={e.status} /></td>
                            <td style={{ padding: "8px 14px" }}><RiskTag level={e.risk_level || "none"} /></td>
                            <td style={{ padding: "8px 14px", color: "#64748b", fontFamily: "monospace", fontSize: 10 }}>{e.evidence}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {adding && <AddEntryModal onSave={addEntry} onClose={() => setAdding(false)} />}
      {editing && <EditStatusModal entry={editing} onSave={updateEntry} onClose={() => setEditing(null)} />}
    </div>
  );
}
