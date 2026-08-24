import { useState, useEffect, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import PageBack from "../components/PageBack";

// ===========================================================================
// EXECUTIVE COMMAND CENTER — one integrated surface, shared data, no copy/paste
// ---------------------------------------------------------------------------
// Everything the executive needs in one place. All tabs read from the same
// loaded context (users, stats, business office, agenda, gateway, manuals) so
// a number seen in the context bar is the SAME number in every tab. The
// "Copy briefing" button compiles the whole picture into one formatted block —
// no more copying between screens to build a report.
// ===========================================================================

const TABS = [
  { key: "overview", label: "🏛️ Overview" },
  { key: "business", label: "💼 Business" },
  { key: "ai", label: "⚡ AI & Providers" },
  { key: "flags", label: "🚩 Site Flags" },
  { key: "users", label: "👤 User Controls" },
  { key: "reports", label: "📚 Reports & Manuals" },
  { key: "controls", label: "🎛️ All Controls" },
];

const TOOLS = [
  { name: "Provider Gateway", desc: "Platform-wide LLM keys (Groq, Cerebras, Gemini…)", path: "/admin/providers" },
  { name: "Site Control Panel", desc: "Site-wide flags, mode, and toggles", path: "/admin/control" },
  { name: "Sovereign Command", desc: "Exec control panel — panels, failover, heartbeat", path: "/admin/exec-control" },
  { name: "Exec System", desc: "Users, roles, KPIs, emergency breaker panel", path: "/admin/system" },
  { name: "Director Dashboard", desc: "Director-level platform view", path: "/admin/director" },
  { name: "Sage Audit", desc: "Audit & integrity checks", path: "/admin/sage-audit" },
  { name: "Staff Meetings", desc: "Meeting records & agenda history", path: "/admin/staff-meetings" },
  { name: "Executive Site Report", desc: "Deep multi-category public-readiness report", path: "/admin/exec-report" },
  { name: "Business Office", desc: "P&L, runway, divisions, truth test", path: "/business-office" },
  { name: "Office Control", desc: "Exec control for the Business Office", path: "/admin/office-control" },
  { name: "Scholarship Committee", desc: "Applications, awards, pledges, funds", path: "/admin/scholarships" },
  { name: "Revenue Division", desc: "Revenue workspace and projections", path: "/revenue" },
  { name: "Team Operations", desc: "Team ops & escalation", path: "/team/ops" },
  { name: "Payment History", desc: "All platform payments", path: "/admin/payments" },
  { name: "Billing Admin", desc: "Billing administration", path: "/admin/billing" },
  { name: "Audit Log", desc: "Full audit trail", path: "/admin/audit-log" },
  { name: "Exec Report (Audit Bureau)", desc: "Compliance & security audit engine", path: "/admin/exec-report" },
  { name: "Command Center", desc: "You are here — integrated exec surface", path: "/admin/command" },
];

const fmtUsd = (c) => {
  if (c === null || c === undefined) return "—";
  return "$" + (c / 100).toLocaleString(undefined, { maximumFractionDigits: 0 });
};

function Chip({ ok, label, sub }) {
  return (
    <div className="flex items-center gap-2 rounded-xl px-3 py-2" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: ok ? "#16a34a" : "#dc2626" }} />
      <div className="leading-tight">
        <div className="text-xs font-bold text-slate-800">{label}</div>
        {sub && <div className="text-[10px] text-slate-700">{sub}</div>}
      </div>
    </div>
  );
}

export default function ExecutiveCommandCenter() {
  const [tab, setTab] = useState("overview");
  const [sys, setSys] = useState(null);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [abo, setAbo] = useState(null);
  const [agenda, setAgenda] = useState([]);
  const [projects, setProjects] = useState([]);
  const [manuals, setManuals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [controlQuery, setControlQuery] = useState("");
  const [openManual, setOpenManual] = useState(null);
  const [flags, setFlags] = useState(null);
  const [flagBusy, setFlagBusy] = useState({});
  const [flagReason, setFlagReason] = useState("");
  const [flagReasonTarget, setFlagReasonTarget] = useState(null);
  const [siteUsers, setSiteUsers] = useState([]);
  const [roleForm, setRoleForm] = useState({ user_id: "", new_role: "student", reason: "" });
  const [roleBusy, setRoleBusy] = useState(false);
  const [tierForm, setTierForm] = useState({ user_id: "", new_feature_tier: "free", reason: "" });
  const [tierBusy, setTierBusy] = useState(false);
  const [loadErrors, setLoadErrors] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    const [sR, stR, hR, aR, agR, pR, mR, fR, uR] = await Promise.allSettled([
      api.get("/exec/system"),
      api.get("/admin/stats"),
      api.get("/health"),
      api.get("/abo/overview"),
      api.get("/abo/agenda"),
      api.get("/projects"),
      api.get("/exec/manuals"),
      api.get("/admin/control-panel"),
      api.get("/admin/users?limit=200"),
    ]);
    if (sR.status === "fulfilled") setSys(sR.value.data);
    if (stR.status === "fulfilled") setStats(stR.value.data);
    if (hR.status === "fulfilled") setHealth(hR.value.data);
    if (aR.status === "fulfilled") setAbo(aR.value.data);
    if (agR.status === "fulfilled") setAgenda((agR.value.data || []).filter((x) => x.status === "pending" || x.status === "on_agenda"));
    if (pR.status === "fulfilled") setProjects(Array.isArray(pR.value.data) ? pR.value.data.slice(0, 8) : []);
    if (mR.status === "fulfilled") setManuals(mR.value.data.manuals || []);
    if (fR.status === "fulfilled") setFlags(fR.value.data);
    if (uR.status === "fulfilled") setSiteUsers(uR.value.data?.users || uR.value.data || []);
    const labels = ["system overview", "platform stats", "health", "business office", "agenda", "projects", "manuals", "site flags", "users"];
    setLoadErrors([sR, stR, hR, aR, agR, pR, mR, fR, uR]
      .map((result, index) => result.status === "rejected" ? labels[index] : null)
      .filter(Boolean));
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const roleCounts = sys?.role_counts || {};
  const totalUsers = Object.values(roleCounts).reduce((a, b) => a + b, 0);
  const gwBudget = sys?.gateway?.budget || {};
  const aboCounts = abo?.counts || {};

  // ── The briefing — one formatted block compiled from the shared context ──
  const briefing = useMemo(() => {
    const lines = [];
    lines.push("M.O.R.E. HELP CENTER — EXECUTIVE BRIEFING");
    lines.push(`Generated: ${new Date().toLocaleString()}`);
    lines.push("");
    lines.push(`PLATFORM — ${totalUsers || 0} users · ${stats?.students || 0} students · ${stats?.completions || 0} completions · ${stats?.credentials_issued || 0} credentials · ${stats?.incidents_open || 0} open incidents`);
    lines.push(`DB: ${sys?.env?.db_source || "unknown"} · API v${sys?.version || "?"} · audit log ${(sys?.audit_log_total || 0).toLocaleString()} entries`);
    lines.push("");
    lines.push(`BUSINESS — month revenue ${fmtUsd(abo?.runway?.month_revenue_cents)} of goal ${fmtUsd(abo?.runway?.monthly_goal_cents)} (${abo?.runway?.month_pct ?? 0}%) · total ${fmtUsd(abo?.runway?.total_revenue_cents)} · runway ${abo?.runway?.runway_months ?? "—"} months (${abo?.runway?.status || "—"})`);
    lines.push(`Deals ${aboCounts.deals ?? 0} · Jobs ${aboCounts.jobs ?? 0} · contracted ${fmtUsd(abo?.contracted_cents)} · agenda pending ${agenda.length}`);
    lines.push("");
    lines.push(`AI — hourly budget ${gwBudget.tokens_used ?? 0}/${gwBudget.hourly_cap ?? 0} tokens (${gwBudget.budget_pct ?? 0}%) · ${sys?.env?.active_free_providers || 0} free providers active`);
    lines.push(`Keys: Groq ${sys?.env?.groq_key ? "✓" : "✗"} · Cerebras ${sys?.env?.cerebras_key ? "✓" : "✗"} · Gemini ${sys?.env?.gemini_key ? "✓" : "✗"} · payments ${sys?.env?.payments_enabled ? "✓" : "✗"}`);
    if (agenda.length) {
      lines.push("");
      lines.push("OPEN AGENDA:");
      agenda.slice(0, 6).forEach((a) => lines.push(`  • [${a.priority || "normal"}] ${a.title}${a.owner ? " — " + a.owner : ""}`));
    }
    return lines.join("\n");
  // gwBudget is derived from sys (already in deps); individual fields don't need separate tracking
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sys, stats, abo, aboCounts, agenda, totalUsers]);

  async function copyBriefing() {
    try {
      await navigator.clipboard.writeText(briefing);
      toast.success("Briefing copied — paste it anywhere.");
    } catch {
      toast.error("Clipboard unavailable — select the text below.");
    }
  }

  const filteredTools = TOOLS.filter((t) => (t.name + " " + t.desc).toLowerCase().includes(controlQuery.toLowerCase()));

  // Flag toggle handlers
  async function toggleFlag(flag, currentEnabled) {
    const newVal = !currentEnabled;
    if (newVal) {
      setFlagReasonTarget({ flag, value: newVal });
      return;
    }
    await applyFlagDirect(flag, newVal, "");
  }

  async function applyFlagDirect(flag, value, reason) {
    setFlagBusy(b => ({ ...b, [flag]: true }));
    try {
      await api.post(`/admin/platform/flags/${flag}`, { value, reason });
      toast.success(`${flag}: ${value ? "ENABLED" : "DISABLED"}`);
      const { data } = await api.get("/admin/control-panel");
      setFlags(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Flag update failed.");
    } finally {
      setFlagBusy(b => ({ ...b, [flag]: false }));
      setFlagReasonTarget(null);
      setFlagReason("");
    }
  }

  // User role/tier handlers
  async function applyUserRole() {
    if (!roleForm.user_id || !roleForm.reason.trim()) return toast.error("Fill all fields");
    setRoleBusy(true);
    try {
      await api.post("/exec/control/user/role", roleForm);
      toast.success("Role updated");
      setRoleForm(f => ({ ...f, reason: "" }));
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setRoleBusy(false); }
  }

  async function applyUserTier() {
    if (!tierForm.user_id || !tierForm.reason.trim()) return toast.error("Fill all fields");
    setTierBusy(true);
    try {
      await api.post("/exec/control/user/tier", tierForm);
      toast.success("Tier updated");
      setTierForm(f => ({ ...f, reason: "" }));
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); }
    finally { setTierBusy(false); }
  }

  return (
    <AppShell>
      <div className="px-4 sm:px-6 lg:px-10 py-8 max-w-7xl" style={{ background: "linear-gradient(160deg,#06251c,#0a0a0f 70%)", minHeight: "100vh", color: "#e8e4f0" }}>
        <div className="mb-5 [&_*]:!text-slate-800 [&_a]:!text-copper">
          <PageBack to="/admin" label="Admin overview" />
        </div>
        {/* HEADER */}
        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "var(--wai-gold-light)" }}>Sovereign Command · Integrated Exec Surface</div>
            <h1 className="font-heading text-3xl font-extrabold" style={{ color: "var(--wai-gold-light)" }}>Executive Command Center</h1>
            <p className="text-sm mt-1" style={{ color: "rgba(241,240,251,0.92)" }}>
              Every number below is the same number in every tab — no copy/paste between screens. One briefing, one click.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={copyBriefing} className="font-bold text-sm px-5 py-2.5 rounded-xl" style={{ background: "var(--wai-gold)", color: "#1a1100" }}>
              📋 Copy briefing
            </button>
            <button onClick={load} disabled={loading} className="font-bold text-sm px-4 py-2.5 rounded-xl" style={{ background: "#1f2937", color: "#fff" }}>
              {loading ? "Loading…" : "⟳ Refresh"}
            </button>
          </div>
        </div>

        {loadErrors.length > 0 && (
          <div className="mb-5 rounded-2xl px-4 py-3" style={{ background: "#fff7ed", border: "1px solid #fdba74", color: "#9a3412" }} role="status">
            <div className="font-bold text-sm">Some live panels could not load.</div>
            <div className="text-xs mt-1">{loadErrors.join(" · ")}. Existing controls remain available; refresh after the service recovers.</div>
          </div>
        )}

        {/* CONTEXT BAR — shared by every tab */}
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-5 text-slate-900">
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-700 mb-2">Live context — shared across all tabs</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {[
              ["Users", totalUsers],
              ["Students", stats?.students],
              ["Completions", stats?.completions],
              ["Credentials", stats?.credentials_issued],
              ["Revenue (mo)", fmtUsd(abo?.runway?.month_revenue_cents)],
              ["Runway", abo?.runway?.runway_months != null ? abo.runway.runway_months + " mo" : "—"],
              ["AI budget", gwBudget.budget_pct != null ? gwBudget.budget_pct + "%" : "—"],
              ["Agenda", agenda.length],
            ].map(([l, v]) => (
              <div key={l} className="rounded-xl px-3 py-2" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                <div className="text-[10px] font-bold uppercase tracking-wide text-slate-600">{l}</div>
                <div className="font-mono font-bold text-slate-800" style={{ fontSize: 15 }}>{v ?? "—"}</div>
              </div>
            ))}
          </div>
        </div>

        {/* TABS */}
        <div className="flex gap-2 flex-wrap mb-6">
          {TABS.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`text-xs font-bold px-4 py-2 rounded-full border transition-colors ${tab === t.key ? "bg-white text-slate-900 border-white" : "border-slate-600 text-slate-300 hover:border-slate-400"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {loading && tab !== "reports" && <p className="text-sm text-slate-300">Loading shared context…</p>}

        {/* ── OVERVIEW ─────────────────────────────────────────────────── */}
        {tab === "overview" && !loading && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Platform Status</div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                <Chip ok={!!sys} label="API Server" sub={"v" + (sys?.version || "?")} />
                <Chip ok={!!sys && (health?.checks?.db?.status || "").includes("up")} label="Database" sub={sys?.env?.db_source} />
                <Chip ok={!((stats?.incidents_open || 0) > 0)} label={stats?.incidents_open ? stats.incidents_open + " Open Incidents" : "No Incidents"} />
                <Chip ok={!((stats?.labs_pending || 0) > 5)} label={stats?.labs_pending ? stats.labs_pending + " Labs Pending" : "Labs Current"} />
                <Chip ok={(health?.checks?.ai_api?.status || "") === "configured"} label="AI Gateway" sub={sys?.env?.active_free_providers + " free providers"} />
                <Chip ok={!!sys?.env?.payments_enabled} label="Payments" sub={sys?.env?.payments_enabled ? "Lemon Squeezy/Gumroad" : "Not configured"} />
                <Chip ok={!!sys?.env?.groq_key || !!sys?.env?.cerebras_key} label="Primary LLM keys" sub="Groq / Cerebras" />
                <Chip ok={!!sys?.env?.gemini_key} label="Gemini (free tier)" sub={sys?.env?.gemini_key ? "Available" : "Add key at /admin/providers"} />
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Total Users", totalUsers],
                ["Students", stats?.students],
                ["Completions", stats?.completions],
                ["Credentials", stats?.credentials_issued],
              ].map(([l, v]) => (
                <div key={l} className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm text-slate-900">
                  <div className="text-[10px] font-bold uppercase tracking-wide text-slate-600">{l}</div>
                  <div className="font-mono font-bold text-2xl text-slate-800">{v ?? "—"}</div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Quick actions</div>
              <div className="flex flex-wrap gap-2">
                {[
                  ["/admin/providers", "Provider Gateway"],
                  ["/admin/control", "Site Control"],
                  ["/admin/exec-control", "Breaker Panel"],
                  ["/business-office", "Business Office"],
                  ["/admin/exec-report", "Exec Report"],
                  ["/admin/scholarships", "Scholarships"],
                ].map(([p, l]) => (
                  <Link key={p} to={p} className="text-xs font-bold px-4 py-2 rounded-lg" style={{ background: "#06251c", color: "var(--wai-gold-light)", border: "1px solid rgba(232,165,30,0.35)" }}>
                    {l} →
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── BUSINESS ─────────────────────────────────────────────────── */}
        {tab === "business" && !loading && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600">Business Office — live from the ledger</div>
                <Link to="/business-office" className="text-xs font-bold" style={{ color: "#8a5a00" }}>Open Business Office →</Link>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                {[
                  ["Month revenue", fmtUsd(abo?.runway?.month_revenue_cents), abo?.runway?.month_pct != null ? abo.runway.month_pct + "% of goal" : ""],
                  ["Total revenue", fmtUsd(abo?.runway?.total_revenue_cents), "all time"],
                  ["Runway", abo?.runway?.runway_months != null ? abo.runway.runway_months + " months" : "—", abo?.runway?.status || ""],
                  ["Contracted", fmtUsd(abo?.contracted_cents), "deals"],
                  ["Deals / Jobs", (aboCounts.deals ?? 0) + " / " + (aboCounts.jobs ?? 0), "counts"],
                ].map(([l, v, s]) => (
                  <div key={l} className="rounded-xl px-3 py-3" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-600">{l}</div>
                    <div className="font-mono font-bold text-slate-800" style={{ fontSize: 16 }}>{v}</div>
                    {s && <div className="text-[10px] text-slate-600">{s}</div>}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-5">
              {/* AGENDA */}
              <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Business Agenda · {agenda.length} pending</div>
                {agenda.length === 0 && <p className="text-sm text-slate-600">No pending agenda items. Create a project to add one automatically.</p>}
                <div className="space-y-2">
                  {agenda.slice(0, 6).map((a) => (
                    <div key={a.id} className="rounded-xl px-3 py-2 flex items-center justify-between gap-2" style={{ background: "#faf9f7" }}>
                      <div className="text-sm text-slate-800">{a.title}</div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0" style={{ background: a.priority === "high" ? "#fee2e2" : "#fef3c7", color: a.priority === "high" ? "#b91c1c" : "#8a5a00" }}>
                        {a.priority || "normal"}
                      </span>
                    </div>
                  ))}
                </div>
                <Link to="/admin/staff-meetings" className="inline-block mt-3 text-xs font-bold" style={{ color: "#8a5a00" }}>Staff meetings & agenda history →</Link>
              </div>

              {/* PROJECTS */}
              <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Projects</div>
                {projects.length === 0 && <p className="text-sm text-slate-600">No projects yet — projects auto-create agenda items.</p>}
                <div className="space-y-2">
                  {projects.map((p) => (
                    <div key={p.project_id} className="rounded-xl px-3 py-2 flex items-center justify-between gap-2" style={{ background: "#faf9f7" }}>
                      <div className="text-sm text-slate-800 truncate">{p.title}</div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0" style={{ background: "#e0e7ff", color: "#3730a3" }}>{p.status || "active"}</span>
                    </div>
                  ))}
                </div>
                <Link to="/projects" className="inline-block mt-3 text-xs font-bold" style={{ color: "#8a5a00" }}>Manage projects →</Link>
              </div>
            </div>
          </div>
        )}

        {/* ── AI & PROVIDERS ───────────────────────────────────────────── */}
        {tab === "ai" && !loading && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600">LLM Gateway — free-first provider chain</div>
                <Link to="/admin/providers" className="text-xs font-bold" style={{ color: "#8a5a00" }}>Manage keys →</Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[560px]">
                  <thead>
                    <tr className="text-left text-[10px] uppercase tracking-widest text-slate-600 border-b">
                      <th className="py-2 pr-4">Provider</th><th className="py-2 pr-4">Tier</th><th className="py-2 pr-4">Cost</th><th className="py-2 pr-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(Object.entries(sys?.gateway?.providers || {}).filter(([k]) => k !== "kb_fallback")).map(([k, p]) => (
                      <tr key={k} className="border-b border-slate-50">
                        <td className="py-2 pr-4 font-bold text-slate-800">{k}</td>
                        <td className="py-2 pr-4 text-slate-700">{String(p.tier)}</td>
                        <td className="py-2 pr-4 text-slate-700">{p.cost}</td>
                        <td className="py-2 pr-4">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: p.available ? "#d1fae5" : "#fee2e2", color: p.available ? "#065f46" : "#b91c1c" }}>
                            {p.available ? "available" : "no key"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
                {[
                  ["Hourly budget", gwBudget.tokens_used + " / " + gwBudget.hourly_cap, gwBudget.budget_pct + "%"],
                  ["Over budget?", gwBudget.over_budget ? "YES" : "No", ""],
                  ["Per-user daily cap", "50,000 tokens", "students; exec unlimited"],
                  ["BYOK", "Free for instructors+", "$3 below instructor"],
                ].map(([l, v, s]) => (
                  <div key={l} className="rounded-xl px-3 py-2" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-600">{l}</div>
                    <div className="font-mono font-bold text-slate-800 text-sm">{v}</div>
                    {s && <div className="text-[10px] text-slate-600">{s}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* FREE GOOGLE STACK — the evaluation, live */}
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-2">Free Google Stack — evaluated & live status</div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-xl p-4" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                  <div className="flex items-center justify-between">
                    <div className="font-heading font-extrabold text-slate-800">Gemini Developer API</div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: sys?.env?.gemini_key ? "#d1fae5" : "#fef3c7", color: sys?.env?.gemini_key ? "#065f46" : "#8a5a00" }}>
                      {sys?.env?.gemini_key ? "Key set" : "No key yet"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 mt-2 leading-relaxed">
                    Already integrated as gateway Tier 2 (free, 1M context) and as a BYOK provider. Free tier now: ~5–15
                    requests/min (2.0 Flash 15 RPM / 1M TPM; 2.5 Flash 10 RPM / 250K TPM), Pro models excluded. Perfect as
                    a fallback — not as the only provider.
                  </p>
                  <div className="flex flex-wrap gap-2 mt-3">
                    <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" className="text-xs font-bold px-3 py-1.5 rounded-lg" style={{ background: "#06251c", color: "var(--wai-gold-light)" }}>
                      Get a free key (AI Studio)
                    </a>
                    <a href="https://ai.google.dev/gemini-api/docs/rate-limits" target="_blank" rel="noreferrer" className="text-xs font-bold px-3 py-1.5 rounded-lg border" style={{ borderColor: "#d6c9a8", color: "#8a5a00" }}>
                      Current rate limits
                    </a>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-2">
                    Setup (2 minutes): log into AI Studio as <span className="font-mono">morehelpcenter@gmail.com</span> → create an
                    API key → paste it at <span className="font-mono">/admin/providers</span> (type: gemini). Done.
                  </p>
                </div>
                <div className="rounded-xl p-4" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                  <div className="font-heading font-extrabold text-slate-800">Other Google free features — evaluated</div>
                  <ul className="text-xs text-slate-700 mt-2 space-y-1.5 leading-relaxed">
                    <li><strong className="text-slate-800">Free courses (worth it):</strong> Google AI Essentials, Google Cloud Skills Boost (~35 free credits/mo), grow.google — link them in a Free Learning lane for the community.</li>
                    <li><strong className="text-slate-800">Google Cloud free tier ($300/90 days):</strong> not needed now — the platform runs on a zero-cost stack; defer until there's a real need for GCP compute/storage.</li>
                    <li><strong className="text-slate-800">Workspace (Gmail/Drive/Calendar):</strong> the base account already provides daily ops — no integration required.</li>
                    <li><strong className="text-slate-800">Verdict:</strong> integrate Gemini key (fallback AI) + free courses (mission education). Skip GCP cloud spend.</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── SITE FLAGS ──────────────────────────────────────────────── */}
        {tab === "flags" && !loading && (
          <div className="space-y-5">
            {flagReasonTarget && (
              <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
                <div className="text-sm font-bold text-slate-800 mb-2">Reason for enabling {flagReasonTarget.flag}:</div>
                <input value={flagReason} onChange={(e) => setFlagReason(e.target.value)}
                  className="w-full rounded-xl px-4 py-2 text-sm border border-slate-200 mb-3"
                  placeholder="Justify this change…" />
                <div className="flex gap-2">
                  <button onClick={() => applyFlagDirect(flagReasonTarget.flag, flagReasonTarget.value, flagReason)}
                    className="text-xs font-bold px-4 py-2 rounded-lg bg-red-600 text-white">Confirm Enable</button>
                  <button onClick={() => { setFlagReasonTarget(null); setFlagReason(""); }}
                    className="text-xs font-bold px-4 py-2 rounded-lg border border-slate-200 text-slate-800">Cancel</button>
                </div>
              </div>
            )}
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Platform Feature Flags</div>
              <p className="text-sm text-slate-700 mb-4">Toggle platform-wide features. Dangerous flags require a reason.</p>
              <div className="space-y-3">
                {[
                  ["platform_locked", "🔒 Platform Lock", "Locks ALL non-exec access", true],
                  ["marketplace_disabled", "🛒 Store Disabled", "Disables checkout and store", true],
                  ["ai_disabled", "🤖 AI Services Off", "Disables all AI endpoints", false],
                  ["community_disabled", "👥 Community Off", "Disables M.O.R.E. hub", false],
                  ["labs_disabled", "🔬 Labs Disabled", "Disables lab submissions", false],
                ].map(([flag, label, desc, danger]) => {
                  const enabled = flags?.platform_flags?.[flag]?.enabled || false;
                  return (
                    <div key={flag} className="flex items-center justify-between gap-4 rounded-xl px-4 py-3" style={{ background: enabled ? (danger ? "#fef2f2" : "#f0fdf4") : "#faf9f7", border: `1px solid ${enabled ? (danger ? "#fecaca" : "#bbf7d0") : "#f0eadf"}` }}>
                      <div>
                        <div className="text-sm font-bold text-slate-800">{label}</div>
                        <div className="text-xs text-slate-700">{desc}</div>
                      </div>
                      <button onClick={() => toggleFlag(flag, enabled)} disabled={flagBusy[flag]}
                        className="text-xs font-bold px-4 py-2 rounded-lg transition-colors"
                        style={{ background: enabled ? (danger ? "#dc2626" : "#16a34a") : "#e5e7eb", color: enabled ? "#fff" : "#6b7280" }}>
                        {flagBusy[flag] ? "…" : enabled ? "ON" : "OFF"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
            {flags?.active_broadcast && (
              <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-2">Active Broadcast</div>
                <div className="text-sm text-slate-800">{flags.active_broadcast.message}</div>
              </div>
            )}
          </div>
        )}

        {/* ── USER CONTROLS ───────────────────────────────────────────── */}
        {tab === "users" && !loading && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Change User Role</div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input value={roleForm.user_id} onChange={(e) => setRoleForm(f => ({ ...f, user_id: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200" placeholder="User ID" />
                <select value={roleForm.new_role} onChange={(e) => setRoleForm(f => ({ ...f, new_role: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200">
                  <option value="student">Student (1)</option>
                  <option value="trial_pass">Trial Pass (2)</option>
                  <option value="instructor">Instructor (3)</option>
                  <option value="support_staff">Support Staff (4)</option>
                  <option value="oversight">Oversight (5)</option>
                  <option value="admin">Admin (6)</option>
                  <option value="executive_admin">Exec Admin (7)</option>
                </select>
                <input value={roleForm.reason} onChange={(e) => setRoleForm(f => ({ ...f, reason: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200" placeholder="Reason (required)" />
                <button onClick={applyUserRole} disabled={roleBusy}
                  className="text-xs font-bold px-4 py-2 rounded-lg" style={{ background: "var(--wai-gold)", color: "#1a1100" }}>
                  {roleBusy ? "…" : "Apply Role"}
                </button>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Change User Feature Tier</div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input value={tierForm.user_id} onChange={(e) => setTierForm(f => ({ ...f, user_id: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200" placeholder="User ID" />
                <select value={tierForm.new_feature_tier} onChange={(e) => setTierForm(f => ({ ...f, new_feature_tier: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200">
                  <option value="free">Free</option>
                  <option value="starter">Starter</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <input value={tierForm.reason} onChange={(e) => setTierForm(f => ({ ...f, reason: e.target.value }))}
                  className="rounded-xl px-4 py-2 text-sm border border-slate-200" placeholder="Reason (required)" />
                <button onClick={applyUserTier} disabled={tierBusy}
                  className="text-xs font-bold px-4 py-2 rounded-lg" style={{ background: "var(--wai-gold)", color: "#1a1100" }}>
                  {tierBusy ? "…" : "Apply Tier"}
                </button>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600">Recent Users ({siteUsers.length})</div>
                <Link to="/admin/accounts" className="text-xs font-bold" style={{ color: "#8a5a00" }}>Full account controls →</Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-[10px] uppercase tracking-widest text-slate-600 border-b">
                    <th className="py-2 pr-4">Name</th><th className="py-2 pr-4">Role</th><th className="py-2 pr-4">Email</th><th className="py-2 pr-4">Joined</th>
                  </tr></thead>
                  <tbody>
                    {siteUsers.slice(0, 15).map((u) => (
                      <tr key={u.id} className="border-b border-slate-50">
                        <td className="py-2 pr-4 font-bold text-slate-800 text-xs">{u.display_name || u.name || u.email}</td>
                        <td className="py-2 pr-4"><span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: "#e0e7ff", color: "#3730a3" }}>{u.role}</span></td>
                        <td className="py-2 pr-4 text-slate-700 text-xs">{u.email}</td>
                        <td className="py-2 pr-4 text-slate-600 text-xs">{u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── REPORTS & MANUALS ────────────────────────────────────────── */}
        {tab === "reports" && (
          <div className="space-y-5">
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Report engines</div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2">
                {[
                  ["/admin/exec-report", "Executive Site Report", "Deep automated platform audit"],
                  ["/admin/sage-audit", "Sage Audit", "Integrity & audit checks"],
                  ["/admin/staff-meetings", "Staff Meetings", "Agenda & meeting records"],
                  ["/revenue", "Revenue Division", "Revenue & projections"],
                ].map(([p, t, d]) => (
                  <Link key={p} to={p} className="rounded-xl p-4 hover:shadow-md transition-shadow" style={{ background: "#faf9f7", border: "1px solid #f0eadf", textDecoration: "none" }}>
                    <div className="font-heading font-extrabold text-slate-800 text-sm">{t}</div>
                    <div className="text-[11px] text-slate-600 mt-1">{d}</div>
                    <div className="text-xs font-bold mt-2" style={{ color: "#8a5a00" }}>Open →</div>
                  </Link>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600">Operations manuals & handbooks</div>
                <span className="text-[11px] text-slate-600">{manuals.length} documents served from the repo</span>
              </div>
              {manuals.length === 0 && <p className="text-sm text-slate-600">Manuals unavailable in this environment.</p>}
              <div className="space-y-2">
                {manuals.map((m) => (
                  <details key={m.slug + m.group} className="rounded-xl" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}
                    open={openManual === m.slug} onToggle={(e) => e.target.open && setOpenManual(m.slug)}>
                    <summary className="cursor-pointer px-4 py-3 text-sm font-bold text-slate-800">
                      {m.group === "handbook" ? "📖 " : "📘 "}{m.title}
                    </summary>
                    <div className="px-4 pb-4 text-sm leading-relaxed text-slate-700 max-h-[60vh] overflow-y-auto prose-headings:mt-3 prose-p:my-2">
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                    </div>
                  </details>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── ALL CONTROLS ─────────────────────────────────────────────── */}
        {tab === "controls" && (
          <div className="space-y-4">
            <input value={controlQuery} onChange={(e) => setControlQuery(e.target.value)} placeholder="Search every exec control — e.g. 'providers', 'report', 'panel'…"
              className="w-full rounded-xl px-4 py-3 text-sm border" style={{ borderColor: "#444", background: "#fff", color: "#111" }} />
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredTools.map((t) => (
                <Link key={t.name + t.path} to={t.path} className="rounded-2xl p-4 hover:shadow-md transition-shadow" style={{ background: "#fff", border: "1px solid #f0eadf", textDecoration: "none" }}>
                  <div className="font-heading font-extrabold text-slate-800 text-sm">{t.name}</div>
                  <div className="text-[11px] text-slate-600 mt-1">{t.desc}</div>
                  <div className="text-[11px] font-mono mt-2" style={{ color: "#8a5a00" }}>{t.path}</div>
                </Link>
              ))}
              {filteredTools.length === 0 && <p className="text-sm text-slate-600 col-span-full">No controls match “{controlQuery}”.</p>}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
