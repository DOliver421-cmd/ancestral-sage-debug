/**
 * ExecControl — the owner's no-code control panel for the AI Business Office.
 *
 * Every number and every text string the office displays is editable here and
 * saved through PUT /api/abo/config — no code, no deploy, fully audited.
 *
 * Sections:
 *  1. Numbers     — monthly goal, infrastructure costs, owner draw %,
 *                   clearinghouse fee %, red-team prices.
 *  2. Site copy   — header, runway, loops, guardrails.
 *  3. Divisions   — name, tagline, AI/human roles, revenue description,
 *                   status, and price for every business division.
 *  4. Tools dock  — name, what it does, human role, revenue, access.
 *
 * Owner-first rule enforced server-side: revenue → infrastructure → net profit
 * to the owner. Nothing here can create a fixed liability that drains the
 * owner's pocket — labor pay is performance-linked by design.
 */

import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Settings2, DollarSign, Type, Building2, Wrench,
  Save, RotateCcw, ChevronDown, ShieldCheck,
} from "lucide-react";

const GREEN = "#1B4332";
const GOLD = "#E8A51E";
const COPPER = "#C0572D";
const BONE = "#FDFBF5";

// Field descriptors for the Numbers section.
const NUMBER_FIELDS = [
  { key: "monthly_goal_cents", label: "Monthly operating goal", kind: "money", unit: "$/mo", hint: "What the office must raise each month (runway denominator)." },
  { key: "infra_cost_cents", label: "Infrastructure costs (monthly)", kind: "money", unit: "$/mo", hint: "Hosting, API tokens, database — covered first in the P&L waterfall." },
  { key: "owner_draw_pct", label: "Owner retained / draw", kind: "pct", unit: "%", hint: "Share of net profit the owner retains. Default 100% — the owner is the ultimate beneficiary." },
  { key: "clearinghouse_fee_pct", label: "Workforce Exchange clearinghouse fee", kind: "pct", unit: "%", hint: "Fee taken on every completed agent-to-agent contract." },
  { key: "redteam_oneshot_cents", label: "Red-team one-shot scan", kind: "money", unit: "$", hint: "List price for a single red-team engagement." },
  { key: "redteam_retainer_cents", label: "Red-team retainer", kind: "money", unit: "$/mo", hint: "List price for a monthly red-team retainer." },
];

const COPY_FIELDS = [
  { key: "header_title", label: "Office title" },
  { key: "header_tagline", label: "Header tagline" },
  { key: "runway_note", label: "Runway note" },
  { key: "loop_intro", label: "Feedback loops intro" },
  { key: "guardrail_owner", label: "Guardrail 1 — title" },
  { key: "guardrail_owner_desc", label: "Guardrail 1 — description" },
  { key: "guardrail_labor", label: "Guardrail 2 — title" },
  { key: "guardrail_labor_desc", label: "Guardrail 2 — description" },
  { key: "guardrail_creators", label: "Guardrail 3 — title" },
  { key: "guardrail_creators_desc", label: "Guardrail 3 — description" },
  { key: "guardrail_honest", label: "Guardrail 4 — title" },
  { key: "guardrail_honest_desc", label: "Guardrail 4 — description" },
  { key: "guardrail_disclose", label: "Guardrail 5 — title" },
  { key: "guardrail_disclose_desc", label: "Guardrail 5 — description" },
];

const DIVISION_FIELDS = [
  { key: "name", label: "Name" },
  { key: "tagline", label: "Tagline" },
  { key: "what_ai_does", label: "What AI does", multiline: true },
  { key: "human_oversight", label: "Human oversight", multiline: true },
  { key: "revenue", label: "Revenue description", multiline: true },
  { key: "status", label: "Status", select: ["live", "pipeline"] },
  { key: "price", label: "Price" },
];

const TOOL_FIELDS = [
  { key: "name", label: "Name" },
  { key: "what", label: "What AI does", multiline: true },
  { key: "human", label: "Human role", multiline: true },
  { key: "revenue", label: "Revenue role" },
  { key: "access", label: "Access" },
];

const moneyToDollars = (cents) => (cents == null ? "" : String((cents / 100).toFixed(2)));
const dollarsToCents = (val) => Math.round((parseFloat(val) || 0) * 100);
const num = (val, fallback) => {
  const n = parseFloat(val);
  return Number.isFinite(n) ? n : fallback;
};

export default function ExecControl() {
  const [config, setConfig] = useState(null);
  const [numbers, setNumbers] = useState({});
  const [copy, setCopy] = useState({});
  const [divisions, setDivisions] = useState({});
  const [tools, setTools] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [savedAt, setSavedAt] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get("/abo/config");
      const c = res.data;
      setConfig(c);
      // Money fields presented in dollars; pct fields as numbers.
      const n = {};
      for (const f of NUMBER_FIELDS) {
        const v = c.numbers?.[f.key];
        n[f.key] = f.kind === "money" ? moneyToDollars(v) : v == null ? "" : String(v);
      }
      setNumbers(n);
      const cp = {};
      for (const f of COPY_FIELDS) cp[f.key] = c.copy?.[f.key] ?? "";
      setCopy(cp);
      const dv = {};
      for (const d of c.divisions || []) {
        dv[d.key] = { ...d };
      }
      setDivisions(dv);
      const tv = {};
      for (const t of c.tools || []) {
        tv[t.key] = { ...t };
      }
      setTools(tv);
      setSavedAt(c.updated_at || null);
    } catch (e) {
      toast.error("Could not load the office config — check the backend connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async (reset = false) => {
    setBusy(true);
    try {
      let payload = { numbers: {}, text: {} };
      if (!reset) {
        const n = {};
        for (const f of NUMBER_FIELDS) {
          const v = numbers[f.key];
          n[f.key] = f.kind === "money" ? dollarsToCents(v) : num(v, 0);
        }
        const textDivisions = {};
        for (const [key, d] of Object.entries(divisions)) {
          const fields = {};
          for (const f of DIVISION_FIELDS) {
            if (d[f.key] !== undefined && String(d[f.key] ?? "").trim() !== "") fields[f.key] = String(d[f.key]).trim();
          }
          textDivisions[key] = fields;
        }
        const textTools = {};
        for (const [key, t] of Object.entries(tools)) {
          const fields = {};
          for (const f of TOOL_FIELDS) {
            if (t[f.key] !== undefined && String(t[f.key] ?? "").trim() !== "") fields[f.key] = String(t[f.key]).trim();
          }
          textTools[key] = fields;
        }
        payload = { numbers: n, text: { copy, divisions: textDivisions, tools: textTools } };
      }
      const res = await api.put("/abo/config", payload);
      toast.success(reset ? "Office config restored to defaults." : "Office config saved — no code needed.");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not save the config.");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="p-12 text-ink font-heading">Loading Exec Control…</div>
      </AppShell>
    );
  }

  const inputCls = "w-full px-3 py-2 rounded-lg border text-sm bg-white";
  const setDiv = (key, field, value) => setDivisions((d) => ({ ...d, [key]: { ...d[key], [field]: value } }));
  const setTool = (key, field, value) => setTools((t) => ({ ...t, [key]: { ...t[key], [field]: value } }));

  return (
    <AppShell>
      <div style={{ background: BONE, minHeight: "100vh" }}>
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)`, padding: "36px 32px 28px", color: "#fff" }}>
          <div className="flex items-center gap-3 flex-wrap">
            <Settings2 className="w-7 h-7" style={{ color: GOLD }} />
            <h1 className="font-heading text-2xl font-bold tracking-tight">Exec Control — the Business Office</h1>
            <span className="ml-1 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded" style={{ background: GOLD, color: "#0a0a0a" }}>
              No-code · Audited
            </span>
          </div>
          <p className="text-white/80 text-sm mt-2 max-w-3xl">
            Every number and every text string the office displays is editable here — no code, no deploy.
            The financial engine stays owner-first no matter what you type: revenue → infrastructure →
            net profit to the owner. Labor pay is performance-linked by design; this panel cannot create
            a fixed liability that drains your pocket.
          </p>
          {savedAt && (
            <p className="text-white/60 text-[11px] mt-2">Last saved: {new Date(savedAt).toLocaleString()}</p>
          )}
          <div className="flex flex-wrap gap-2 mt-4">
            <button onClick={() => save(false)} disabled={busy}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black disabled:opacity-50"
              style={{ background: GOLD, color: "#0a0a0a" }}>
              <Save className="w-4 h-4" /> {busy ? "Saving…" : "Save everything"}
            </button>
            <button onClick={() => { if (window.confirm("Restore ALL office numbers and text to defaults?")) save(true); }} disabled={busy}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black border disabled:opacity-50"
              style={{ borderColor: "rgba(255,255,255,0.4)", color: "#fff" }}>
              <RotateCcw className="w-4 h-4" /> Restore defaults
            </button>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-6 py-8 space-y-10">
          {/* ── 1. Numbers ──────────────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <DollarSign className="w-5 h-5" style={{ color: GOLD }} /> Numbers — the money controls
            </h2>
            <p className="text-xs text-ink/50 mt-1">Change any figure and save. The P&L waterfall recomputes instantly.</p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
              {NUMBER_FIELDS.map((f) => (
                <div key={f.key} className="card-flat rounded-2xl p-4 border" style={{ background: "#fff" }}>
                  <label className="text-[10px] font-black uppercase tracking-widest text-ink/40">{f.label}</label>
                  <div className="flex items-center gap-2 mt-1.5">
                    <input value={numbers[f.key] ?? ""} onChange={(e) => setNumbers((n) => ({ ...n, [f.key]: e.target.value }))}
                      type="number" min="0" step={f.kind === "money" ? "10" : "1"}
                      className={inputCls} style={{ borderColor: "#ddd3bf" }} />
                    <span className="text-xs font-black text-ink/40">{f.unit}</span>
                  </div>
                  <p className="text-[10px] text-ink/40 mt-1.5">{f.hint}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ── 2. Site copy ────────────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Type className="w-5 h-5" style={{ color: COPPER }} /> Site copy — the words the office speaks
            </h2>
            <div className="grid sm:grid-cols-2 gap-4 mt-3">
              {COPY_FIELDS.map((f) => (
                <div key={f.key} className="card-flat rounded-2xl p-4 border" style={{ background: "#fff" }}>
                  <label className="text-[10px] font-black uppercase tracking-widest text-ink/40">{f.label}</label>
                  <textarea value={copy[f.key] ?? ""} onChange={(e) => setCopy((c) => ({ ...c, [f.key]: e.target.value }))}
                    rows={f.key.endsWith("_desc") || f.key === "header_tagline" || f.key === "loop_intro" ? 3 : 2}
                    className={`${inputCls} mt-1.5`} style={{ borderColor: "#ddd3bf" }} />
                </div>
              ))}
            </div>
          </section>

          {/* ── 3. Divisions ────────────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Building2 className="w-5 h-5" style={{ color: GREEN }} /> Divisions — what the office sells ({Object.keys(divisions).length})
            </h2>
            <div className="space-y-3 mt-3">
              {Object.entries(divisions).map(([key, d]) => (
                <details key={key} className="card-flat rounded-2xl border overflow-hidden" style={{ background: "#fff" }}>
                  <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none">
                    <div className="flex items-center gap-2">
                      <ChevronDown className="w-4 h-4 text-ink/40" />
                      <span className="font-heading font-bold text-ink text-sm">{d.name}</span>
                    </div>
                    <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                      style={{ background: d.status === "live" ? "rgba(45,106,79,0.12)" : "rgba(232,165,30,0.15)", color: d.status === "live" ? GREEN : "#8a6400" }}>
                      {d.status}
                    </span>
                  </summary>
                  <div className="px-4 pb-4 grid sm:grid-cols-2 gap-3">
                    {DIVISION_FIELDS.map((f) => (
                      <div key={f.key} className={f.multiline ? "sm:col-span-2" : ""}>
                        <label className="text-[10px] font-black uppercase tracking-widest text-ink/40">{f.label}</label>
                        {f.select ? (
                          <select value={d[f.key] || "live"} onChange={(e) => setDiv(key, f.key, e.target.value)}
                            className={`${inputCls} mt-1`} style={{ borderColor: "#ddd3bf" }}>
                            {f.select.map((s) => <option key={s} value={s}>{s}</option>)}
                          </select>
                        ) : (
                          <textarea value={d[f.key] ?? ""} onChange={(e) => setDiv(key, f.key, e.target.value)}
                            rows={f.multiline ? 2 : 1}
                            className={`${inputCls} mt-1`} style={{ borderColor: "#ddd3bf" }} />
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          </section>

          {/* ── 4. Tools dock ───────────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Wrench className="w-5 h-5" style={{ color: COPPER }} /> Tools dock — what AI can run ({Object.keys(tools).length})
            </h2>
            <div className="space-y-3 mt-3">
              {Object.entries(tools).map(([key, t]) => (
                <details key={key} className="card-flat rounded-2xl border overflow-hidden" style={{ background: "#fff" }}>
                  <summary className="flex items-center justify-between px-4 py-3 cursor-pointer list-none">
                    <div className="flex items-center gap-2">
                      <ChevronDown className="w-4 h-4 text-ink/40" />
                      <span className="font-heading font-bold text-ink text-sm">{t.name}</span>
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: COPPER }}>{t.access}</span>
                  </summary>
                  <div className="px-4 pb-4 grid sm:grid-cols-2 gap-3">
                    {TOOL_FIELDS.map((f) => (
                      <div key={f.key} className={f.multiline ? "sm:col-span-2" : ""}>
                        <label className="text-[10px] font-black uppercase tracking-widest text-ink/40">{f.label}</label>
                        <textarea value={t[f.key] ?? ""} onChange={(e) => setTool(key, f.key, e.target.value)}
                          rows={f.multiline ? 2 : 1}
                          className={`${inputCls} mt-1`} style={{ borderColor: "#ddd3bf" }} />
                      </div>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          </section>

          {/* ── Save bar ────────────────────────────────────────────────── */}
          <div className="card-flat rounded-2xl p-5 border flex items-center justify-between gap-4 flex-wrap"
            style={{ background: "#fff", borderColor: "#eee7d8" }}>
            <div className="flex items-start gap-2 max-w-lg">
              <ShieldCheck className="w-5 h-5 mt-0.5 shrink-0" style={{ color: GREEN }} />
              <p className="text-xs text-ink/60">
                Every save is audit-logged (<b>abo.config.updated</b>) with the actor and changed keys.
                Empty fields restore that value to its default. The owner-first waterfall and
                performance-linked labor model cannot be turned off from this panel — they are the law of the office.
              </p>
            </div>
            <button onClick={() => save(false)} disabled={busy}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-black text-white disabled:opacity-50"
              style={{ background: GREEN }}>
              <Save className="w-4 h-4" /> {busy ? "Saving…" : "Save everything"}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
