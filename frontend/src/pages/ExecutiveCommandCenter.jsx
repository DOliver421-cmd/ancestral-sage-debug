import { useState, useEffect, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";

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
  { name: "Business Office", desc: "P&L, runway, divisions, truth test", path: "/admin/business-office" },
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
        <div className="text-xs font-bold text-ink">{label}</div>
        {sub && <div className="text-[10px] text-ink/50">{sub}</div>}
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

  const load = useCallback(async () => {
    setLoading(true);
    const [sR, stR, hR, aR, agR, pR, mR] = await Promise.allSettled([
      api.get("/exec/system"),
      api.get("/admin/stats"),
      api.get("/health"),
      api.get("/abo/overview"),
      api.get("/abo/agenda"),
      api.get("/projects"),
      api.get("/exec/manuals"),
    ]);
    if (sR.status === "fulfilled") setSys(sR.value.data);
    if (stR.status === "fulfilled") setStats(stR.value.data);
    if (hR.status === "fulfilled") setHealth(hR.value.data);
    if (aR.status === "fulfilled") setAbo(aR.value.data);
    if (agR.status === "fulfilled") setAgenda((agR.value.data || []).filter((x) => x.status === "pending" || x.status === "on_agenda"));
    if (pR.status === "fulfilled") setProjects(Array.isArray(pR.value.data) ? pR.value.data.slice(0, 8) : []);
    if (mR.status === "fulfilled") setManuals(mR.value.data.manuals || []);
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

  return (
    <AppShell>
      <div className="px-4 sm:px-6 lg:px-10 py-8 max-w-7xl" style={{ background: "linear-gradient(160deg,#06251c,#0a0a0f 70%)", minHeight: "100vh", color: "#e8e4f0" }}>
        {/* HEADER */}
        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div>
            <div className="text-xs font-bold uppercase tracking-widest mb-1" style={{ color: "var(--wai-gold-light)" }}>Sovereign Command · Integrated Exec Surface</div>
            <h1 className="font-heading text-3xl font-extrabold" style={{ color: "var(--wai-gold-light)" }}>Executive Command Center</h1>
            <p className="text-sm mt-1" style={{ color: "rgba(241,240,251,0.7)" }}>
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

        {/* CONTEXT BAR — shared by every tab */}
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm mb-5 text-slate-900">
          <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Live context — shared across all tabs</div>
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
                <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{l}</div>
                <div className="font-mono font-bold text-ink" style={{ fontSize: 15 }}>{v ?? "—"}</div>
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

        {loading && tab !== "reports" && <p className="text-sm text-slate-400">Loading shared context…</p>}

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
                <div key={l} className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                  <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{l}</div>
                  <div className="font-mono font-bold text-2xl text-ink">{v ?? "—"}</div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Quick actions</div>
              <div className="flex flex-wrap gap-2">
                {[
                  ["/admin/providers", "Provider Gateway"],
                  ["/admin/control", "Site Control"],
                  ["/admin/exec-control", "Breaker Panel"],
                  ["/admin/business-office", "Business Office"],
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
                <Link to="/admin/business-office" className="text-xs font-bold" style={{ color: "#8a5a00" }}>Open Business Office →</Link>
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
                    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{l}</div>
                    <div className="font-mono font-bold text-ink" style={{ fontSize: 16 }}>{v}</div>
                    {s && <div className="text-[10px] text-slate-400">{s}</div>}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-5">
              {/* AGENDA */}
              <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600 mb-3">Business Agenda · {agenda.length} pending</div>
                {agenda.length === 0 && <p className="text-sm text-slate-400">No pending agenda items. Create a project to add one automatically.</p>}
                <div className="space-y-2">
                  {agenda.slice(0, 6).map((a) => (
                    <div key={a.id} className="rounded-xl px-3 py-2 flex items-center justify-between gap-2" style={{ background: "#faf9f7" }}>
                      <div className="text-sm text-ink">{a.title}</div>
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
                {projects.length === 0 && <p className="text-sm text-slate-400">No projects yet — projects auto-create agenda items.</p>}
                <div className="space-y-2">
                  {projects.map((p) => (
                    <div key={p.project_id} className="rounded-xl px-3 py-2 flex items-center justify-between gap-2" style={{ background: "#faf9f7" }}>
                      <div className="text-sm text-ink truncate">{p.title}</div>
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
                    <tr className="text-left text-[10px] uppercase tracking-widest text-slate-400 border-b">
                      <th className="py-2 pr-4">Provider</th><th className="py-2 pr-4">Tier</th><th className="py-2 pr-4">Cost</th><th className="py-2 pr-4">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(Object.entries(sys?.gateway?.providers || {}).filter(([k]) => k !== "kb_fallback")).map(([k, p]) => (
                      <tr key={k} className="border-b border-slate-50">
                        <td className="py-2 pr-4 font-bold text-ink">{k}</td>
                        <td className="py-2 pr-4 text-slate-500">{String(p.tier)}</td>
                        <td className="py-2 pr-4 text-slate-500">{p.cost}</td>
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
                    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{l}</div>
                    <div className="font-mono font-bold text-ink text-sm">{v}</div>
                    {s && <div className="text-[10px] text-slate-400">{s}</div>}
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
                    <div className="font-heading font-extrabold text-ink">Gemini Developer API</div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: sys?.env?.gemini_key ? "#d1fae5" : "#fef3c7", color: sys?.env?.gemini_key ? "#065f46" : "#8a5a00" }}>
                      {sys?.env?.gemini_key ? "Key set" : "No key yet"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">
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
                  <p className="text-[11px] text-slate-400 mt-2">
                    Setup (2 minutes): log into AI Studio as <span className="font-mono">morehelpcenter@gmail.com</span> → create an
                    API key → paste it at <span className="font-mono">/admin/providers</span> (type: gemini). Done.
                  </p>
                </div>
                <div className="rounded-xl p-4" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                  <div className="font-heading font-extrabold text-ink">Other Google free features — evaluated</div>
                  <ul className="text-xs text-slate-500 mt-2 space-y-1.5 leading-relaxed">
                    <li><strong className="text-ink">Free courses (worth it):</strong> Google AI Essentials, Google Cloud Skills Boost (~35 free credits/mo), grow.google — link them in a Free Learning lane for the community.</li>
                    <li><strong className="text-ink">Google Cloud free tier ($300/90 days):</strong> not needed now — the platform runs on a zero-cost stack; defer until there's a real need for GCP compute/storage.</li>
                    <li><strong className="text-ink">Workspace (Gmail/Drive/Calendar):</strong> the base account already provides daily ops — no integration required.</li>
                    <li><strong className="text-ink">Verdict:</strong> integrate Gemini key (fallback AI) + free courses (mission education). Skip GCP cloud spend.</li>
                  </ul>
                </div>
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
                    <div className="font-heading font-extrabold text-ink text-sm">{t}</div>
                    <div className="text-[11px] text-slate-400 mt-1">{d}</div>
                    <div className="text-xs font-bold mt-2" style={{ color: "#8a5a00" }}>Open →</div>
                  </Link>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm text-slate-900">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="text-xs font-bold uppercase tracking-widest text-slate-600">Operations manuals & handbooks</div>
                <span className="text-[11px] text-slate-400">{manuals.length} documents served from the repo</span>
              </div>
              {manuals.length === 0 && <p className="text-sm text-slate-400">Manuals unavailable in this environment.</p>}
              <div className="space-y-2">
                {manuals.map((m) => (
                  <details key={m.slug + m.group} className="rounded-xl" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}
                    open={openManual === m.slug} onToggle={(e) => e.target.open && setOpenManual(m.slug)}>
                    <summary className="cursor-pointer px-4 py-3 text-sm font-bold text-ink">
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
                  <div className="font-heading font-extrabold text-ink text-sm">{t.name}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{t.desc}</div>
                  <div className="text-[11px] font-mono mt-2" style={{ color: "#8a5a00" }}>{t.path}</div>
                </Link>
              ))}
              {filteredTools.length === 0 && <p className="text-sm text-slate-400 col-span-full">No controls match “{controlQuery}”.</p>}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
