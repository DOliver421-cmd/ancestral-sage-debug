/**
 * BusinessOffice — the AI Business Office.
 *
 * The revenue engine command center for M.O.R.E. Help Center. Mission rule:
 * no revenue = no office = no jobs for the AI workforce. This page gives the
 * office the tools to do the business AI can do — every card is a real,
 * shipped platform capability — and shows exactly where the mission stands.
 *
 * Sections:
 *  1. Mission Runway  — month revenue vs. the monthly operating goal.
 *  2. Revenue KPIs    — totals from the real payments collection.
 *  3. Tools Dock      — the business tools AI can run (launcher cards).
 *  4. Divisions       — the revenue lines and their division of labor.
 *  5. Deals Pipeline  — B2B service requests (lead → proposed → won).
 *  6. AI Jobs Ledger  — the workforce board: who does what, for how much.
 *  7. Admin Desk      — set the monthly goal, manage deals & jobs.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Building2, TrendingUp, DollarSign, Receipt, Users, RefreshCw,
  ArrowRight, Plus, Wrench, Briefcase, Target, ShieldCheck, HeartHandshake,
} from "lucide-react";

const GREEN = "#1B4332";
const GOLD = "#E8A51E";
const COPPER = "#C0572D";
const BONE = "#FDFBF5";

const STAGE_FLOW = ["lead", "proposed", "won", "delivered", "closed_lost"];
const STAGE_LABEL = { lead: "Lead", proposed: "Proposed", won: "Won", delivered: "Delivered", closed_lost: "Closed" };
const STATUS_COLOR = {
  covered: { label: "Mission funded", color: "#2D6A4F" },
  on_track: { label: "On track", color: "#5B8C5A" },
  watch: { label: "Watch", color: GOLD },
  critical: { label: "Critical — act now", color: "#B23A2E" },
};

const fmt = (cents) => {
  if (cents == null) return "—";
  return "$" + (cents / 100).toLocaleString("en-US", { maximumFractionDigits: 2 });
};

export default function BusinessOffice() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "executive_admin";

  const [overview, setOverview] = useState(null);
  const [tools, setTools] = useState(null);
  const [deals, setDeals] = useState([]);
  const [jobs, setJobs] = useState(null);
  const [adminData, setAdminData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [ov, tl, dl, jb] = await Promise.all([
        api.get("/abo/overview"),
        api.get("/abo/tools"),
        api.get("/abo/deals"),
        api.get("/abo/jobs"),
      ]);
      setOverview(ov.data);
      setTools(tl.data);
      setDeals(dl.data.deals || []);
      setJobs(jb.data);
      if (isAdmin) {
        const ad = await api.get("/abo/admin/overview");
        setAdminData(ad.data);
      }
    } catch (e) {
      toast.error("Could not load the Business Office — check the backend connection.");
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <AppShell>
        <div className="p-12 text-ink font-heading">Opening the Business Office…</div>
      </AppShell>
    );
  }

  const runway = overview?.runway;
  const rev = overview?.revenue || {};
  const status = STATUS_COLOR[runway?.status] || STATUS_COLOR.watch;
  const pct = Math.min(100, Math.max(0, runway?.month_pct || 0));

  return (
    <AppShell>
      <div style={{ background: BONE, minHeight: "100vh" }}>
        {/* ── Header ─────────────────────────────────────────────────── */}
        <div style={{ background: `linear-gradient(135deg, ${GREEN}, #2D6A4F)`, padding: "36px 32px 28px", color: "#fff" }}>
          <div className="flex items-center gap-3">
            <span style={{ fontSize: 28 }}>🏦</span>
            <h1 className="font-heading text-2xl font-bold tracking-tight">
              AI Business Office
            </h1>
            <span className="ml-2 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded"
              style={{ background: GOLD, color: "#0a0a0a" }}>
              Revenue Engine
            </span>
          </div>
          <p className="text-white/80 text-sm mt-2 max-w-2xl">
            This office turns the platform's AI capabilities into mission funding. No revenue — no office —
            no jobs for people or the AI workforce. Every tool below is real and already shipped; the office's
            job is to run them for income — and that income pays the people who run the office.
          </p>
          <div className="flex flex-wrap gap-2 mt-4">
            {tools?.tools?.slice(0, 8).map((t) => (
              <Link key={t.key} to={t.link}
                className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full border transition-colors"
                style={{ borderColor: "rgba(255,255,255,0.35)", color: "#fff" }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.12)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}>
                <span>{t.icon}</span> {t.name}
              </Link>
            ))}
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">
          {/* ── 1. Mission Runway ────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Target className="w-5 h-5" style={{ color: GOLD }} /> Mission Runway
            </h2>
            <div className="grid md:grid-cols-3 gap-4 mt-3">
              <div className="card-flat rounded-2xl p-6 border" style={{ background: "#fff" }}>
                <div className="text-xs font-black uppercase tracking-widest text-ink/40">Monthly operating goal</div>
                <div className="font-heading text-3xl font-bold text-ink mt-2">{fmt(runway?.monthly_goal_cents)}</div>
                <div className="text-xs text-ink/50 mt-1">{runway?.goal_note || "What the office must raise each month."}</div>
              </div>
              <div className="card-flat rounded-2xl p-6 border" style={{ background: "#fff" }}>
                <div className="text-xs font-black uppercase tracking-widest text-ink/40">Raised this month</div>
                <div className="font-heading text-3xl font-bold mt-2" style={{ color: GREEN }}>{fmt(runway?.month_revenue_cents)}</div>
                <div className="text-xs text-ink/50 mt-1">from real paid orders in the payments ledger.</div>
              </div>
              <div className="card-flat rounded-2xl p-6 border" style={{ background: "#fff" }}>
                <div className="text-xs font-black uppercase tracking-widest text-ink/40">Runway (total cash ÷ goal)</div>
                <div className="font-heading text-3xl font-bold text-ink mt-2">
                  {runway?.runway_months} <span className="text-base font-semibold text-ink/40">mo</span>
                </div>
                <div className="text-xs font-bold mt-1" style={{ color: status.color }}>{status.label}</div>
              </div>
            </div>
            <div className="card-flat rounded-2xl p-6 border mt-4" style={{ background: "#fff" }}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-bold text-ink">{pct.toFixed(1)}% of this month's goal</span>
                <span className="text-xs font-black uppercase tracking-widest" style={{ color: status.color }}>{status.label}</span>
              </div>
              <div className="h-4 rounded-full overflow-hidden" style={{ background: "#eee7d8" }}>
                <div className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${status.color}, ${GOLD})` }} />
              </div>
              <p className="text-xs text-ink/50 mt-3">
                Every membership, product, deal, and donation counts here. {pct >= 100
                  ? "The mission is funded this month — keep the engine running."
                  : "The office is still selling. Keep pushing the tools below."}
              </p>
            </div>
          </section>

          {/* ── 2. Revenue KPIs ──────────────────────────────────────── */}
          <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { icon: DollarSign, label: "Total revenue", value: fmt(rev.total_revenue_cents) },
              { icon: TrendingUp, label: "This month", value: fmt(rev.month_revenue_cents) },
              { icon: Receipt, label: "Paid orders", value: (rev.order_count || 0).toLocaleString() },
              { icon: Users, label: "Paying members", value: (rev.paying_members || 0).toLocaleString() },
              { icon: Target, label: "Recurring est. (30d)", value: fmt(rev.recurring_estimate_cents) },
              { icon: Briefcase, label: "Contracted (deals)", value: fmt(overview?.contracted_cents) },
            ].map((kpi) => (
              <div key={kpi.label} className="card-flat rounded-2xl p-5 border text-center" style={{ background: "#fff" }}>
                <kpi.icon className="w-5 h-5 mx-auto" style={{ color: COPPER }} />
                <div className="font-heading text-xl font-bold text-ink mt-2">{kpi.value}</div>
                <div className="text-[11px] font-bold uppercase tracking-widest text-ink/40 mt-1">{kpi.label}</div>
              </div>
            ))}
          </section>

          {/* ── 2b. Commercial Feedback Loops ─────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <RefreshCw className="w-5 h-5" style={{ color: GREEN }} /> Commercial Feedback Loops
            </h2>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl">
              Each loop feeds the next — that is what makes the revenue consistent instead of one-off. When one loop slows, the office knows which lever to pull.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-3">
              {[
                { emoji: "🎓", name: "Learn → Member", desc: "Free modules and the AI Tutor prove the value. The $3 All-Access Trial converts learners into $9–$59/mo members.", metric: "Watch: trial → member rate" },
                { emoji: "🎨", name: "Create → Sell", desc: "Creator Studio, Ghost Producer, and Band on a Page produce digital products for the Media Store. Sales pay creators first, then the platform.", metric: "Watch: products sold / month" },
                { emoji: "🤝", name: "Serve → Contract → Pay", desc: "The office turns shipped capabilities into B2B deals. AI drafts, humans approve and deliver, clients pay — contracted revenue pays the human labor that ran the deal.", metric: "Watch: deals closed / month" },
                { emoji: "🔄", name: "Trust → Mission", desc: "Transparent runway and free help lanes build trust. Patrons and donors fund free access for others, growing the community that buys.", metric: "Watch: mission fund / month" },
              ].map((loop, i) => (
                <div key={loop.name} className="card-flat rounded-2xl p-5 border relative" style={{ background: "#fff" }}>
                  <div className="text-2xl">{loop.emoji}</div>
                  <div className="font-heading font-bold text-ink text-sm mt-2">{loop.name}</div>
                  <p className="text-xs text-ink/60 mt-1.5 leading-snug">{loop.desc}</p>
                  <div className="text-[10px] font-black uppercase tracking-widest mt-3" style={{ color: COPPER }}>{loop.metric}</div>
                  {i < 3 && (
                    <ArrowRight className="w-4 h-4 absolute -right-3 top-1/2 -translate-y-1/2 hidden lg:block" style={{ color: GOLD }} />
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* ── 3. Tools Dock — the tools to do the business AI can do ── */}
          <section>
            <div className="flex items-center justify-between">
              <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
                <Wrench className="w-5 h-5" style={{ color: COPPER }} /> The Tools — what AI can do for revenue
              </h2>
              <button onClick={load} className="flex items-center gap-1.5 text-xs font-bold text-ink/50 hover:text-copper">
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
              {(tools?.tools || []).map((t) => (
                <Link key={t.key} to={t.link}
                  className="card-flat rounded-2xl p-5 border no-underline transition-all hover:-translate-y-0.5 hover:shadow-lg"
                  style={{ background: "#fff", borderColor: "#eee7d8" }}>
                  <div className="flex items-center gap-3">
                    <span className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                      style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>{t.icon}</span>
                    <div>
                      <div className="font-heading font-bold text-ink">{t.name}</div>
                      <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: COPPER }}>{t.access}</div>
                    </div>
                  </div>
                  <p className="text-sm text-ink/70 mt-3 leading-snug">{t.what}</p>
                  <div className="mt-3 pt-3 border-t border-ink/5 flex items-center justify-between">
                    <span className="text-[11px] font-bold text-ink/50">{t.revenue}</span>
                    <span className="text-xs font-black" style={{ color: GREEN }}>Open →</span>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          {/* ── 4. Divisions ─────────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Building2 className="w-5 h-5" style={{ color: GREEN }} /> Business Divisions
            </h2>
            <div className="grid sm:grid-cols-2 gap-4 mt-3">
              {(overview?.divisions || []).map((d) => (
                <div key={d.key} className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-heading font-bold text-ink text-sm">{d.name}</h3>
                    <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                      style={{
                        background: d.status === "live" ? "rgba(45,106,79,0.12)" : "rgba(232,165,30,0.15)",
                        color: d.status === "live" ? GREEN : "#8a6400",
                      }}>
                      {d.status === "live" ? "Live" : "Pipeline"}
                    </span>
                  </div>
                  <p className="text-xs text-ink/60 mt-1">{d.tagline}</p>
                  <div className="mt-3 text-xs space-y-1.5">
                    <div><span className="font-black text-ink/70">AI does:</span> <span className="text-ink/60">{d.what_ai_does}</span></div>
                    <div><span className="font-black text-ink/70">Human oversees:</span> <span className="text-ink/60">{d.human_oversight}</span></div>
                    <div><span className="font-black text-ink/70">Revenue:</span> <span className="text-ink/60">{d.revenue}</span></div>
                    {d.deals_revenue_cents > 0 && (
                      <div><span className="font-black text-ink/70">Contracted:</span> <span style={{ color: GREEN }} className="font-bold">{fmt(d.deals_revenue_cents)}</span></div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {d.tools.map((t) => (
                      <Link key={t.link} to={t.link}
                        className="text-[11px] font-bold px-2.5 py-1 rounded border no-underline"
                        style={{ borderColor: "rgba(27,67,50,0.3)", color: GREEN }}>
                        {t.label} →
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ── 4b. Mission Guardrails ────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <ShieldCheck className="w-5 h-5" style={{ color: COPPER }} /> Mission Guardrails — what revenue can never buy
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-3">
              {[
                { emoji: "🆓", title: "Help stays free, always", desc: "Core help lanes, free modules, and community never sit behind a paywall. Paid features are additions — never substitutions." },
                { emoji: "👤", title: "Humans get paid — labor is never free", desc: "Every human hour in the office is compensated (pay, creator share, or equity). AI work generates revenue that pays people — never the reverse." },
                { emoji: "🎨", title: "Creators get paid first", desc: "Creator earnings and payouts are priority obligations. The platform's cut never competes with the creator's cut." },
                { emoji: "🔍", title: "No invented revenue", desc: "The dashboard reads the real payments ledger. Deals count only when closed. Every promise must be deliverable." },
                { emoji: "🗣️", title: "AI always discloses", desc: "Any AI that talks to people for transactions or support says so, per FTC guidance." },
              ].map((g) => (
                <div key={g.title} className="card-flat rounded-2xl p-4 border" style={{ background: "#fff" }}>
                  <div className="text-xl">{g.emoji}</div>
                  <div className="font-heading font-bold text-ink text-xs mt-2">{g.title}</div>
                  <p className="text-[11px] text-ink/60 mt-1.5 leading-snug">{g.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ── 5. Deals Pipeline ────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <Briefcase className="w-5 h-5" style={{ color: GOLD }} /> Service Deals — the B2B pipeline
            </h2>
            <div className="grid md:grid-cols-2 gap-4 mt-3">
              <DealForm divisions={overview?.divisions || []} onCreated={load} />
              <DealsList deals={deals} isAdmin={isAdmin} onChanged={load} />
            </div>
          </section>

          {/* ── 6. AI Jobs Ledger ────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <HeartHandshake className="w-5 h-5" style={{ color: COPPER }} /> Workforce Ledger — paid people & AI
            </h2>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl">
              AI jobs create revenue (<b>value</b>). Human jobs — the people who own, approve, and deliver — are paid from it (<b>pay</b>). Labor is never free.
            </p>
            <div className="card-flat rounded-2xl border mt-3 overflow-hidden" style={{ background: "#fff" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[10px] font-black uppercase tracking-widest text-ink/40 border-b"
                    style={{ background: "#f8f3e8" }}>
                    <th className="px-4 py-3">Job</th>
                    <th className="px-4 py-3">Worker</th>
                    <th className="px-4 py-3">Persona / Role</th>
                    <th className="px-4 py-3">Division</th>
                    <th className="px-4 py-3 text-right">Hours</th>
                    <th className="px-4 py-3 text-right">Pay</th>
                    <th className="px-4 py-3 text-right">Value</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(jobs?.jobs || []).map((j) => {
                    const isHuman = j.worker_type === "human";
                    return (
                      <tr key={j.id} className="border-b border-ink/5">
                        <td className="px-4 py-3 font-semibold text-ink">{j.title}</td>
                        <td className="px-4 py-3">
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                            style={{
                              background: isHuman ? "rgba(232,165,30,0.18)" : "rgba(27,67,50,0.12)",
                              color: isHuman ? "#8a6400" : GREEN,
                            }}>
                            {isHuman ? "Human" : "AI"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-ink/70">{j.persona}</td>
                        <td className="px-4 py-3 text-ink/60 capitalize">{j.division.replace(/_/g, " ")}</td>
                        <td className="px-4 py-3 text-right text-ink/70">{j.hours}</td>
                        <td className="px-4 py-3 text-right font-bold" style={{ color: isHuman ? COPPER : "#c9bda6" }}>
                          {isHuman ? fmt(j.pay_cents) : "—"}
                        </td>
                        <td className="px-4 py-3 text-right font-bold" style={{ color: isHuman ? "#c9bda6" : GREEN }}>
                          {isHuman ? "—" : fmt(j.value_cents)}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                            style={{
                              background: j.status === "completed" ? "rgba(45,106,79,0.12)" : j.status === "assigned" ? "rgba(232,165,30,0.15)" : "rgba(192,87,45,0.1)",
                              color: j.status === "completed" ? GREEN : j.status === "assigned" ? "#8a6400" : COPPER,
                            }}>
                            {j.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="px-4 py-3 text-xs font-bold text-ink/60 flex flex-wrap gap-x-6 gap-y-1" style={{ background: "#f8f3e8" }}>
                <span>Human jobs: <span style={{ color: COPPER }}>{jobs?.human_jobs}</span></span>
                <span>AI jobs: <span style={{ color: GREEN }}>{jobs?.ai_jobs}</span></span>
                <span>Human pay committed: <span style={{ color: COPPER }}>{fmt(jobs?.human_pay_cents)}</span></span>
                <span>AI work value: <span style={{ color: GREEN }}>{fmt(jobs?.ai_value_cents)}</span></span>
                <span>Total hours: <span style={{ color: GREEN }}>{jobs?.total_hours}</span></span>
              </div>
            </div>
            {isAdmin && <JobForm divisions={overview?.divisions || []} onCreated={load} />}
          </section>

          {/* ── 7. Admin Desk ────────────────────────────────────────── */}
          {isAdmin && <AdminDesk data={adminData} onChanged={load} />}
        </div>
      </div>
    </AppShell>
  );
}

/* ── Deal submission form ─────────────────────────────────────────────────── */
function DealForm({ divisions, onCreated }) {
  const { user } = useAuth();
  const [service, setService] = useState("");
  const [org, setOrg] = useState("");
  const [desc, setDesc] = useState("");
  const [budget, setBudget] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!service || !org || !desc) { toast.error("Pick a service, add your organization, and describe the job."); return; }
    setBusy(true);
    try {
      await api.post("/abo/deals", {
        service_key: service,
        org_name: org,
        description: desc,
        budget_cents: budget ? Math.round(parseFloat(budget) * 100) : null,
      });
      toast.success("Deal submitted — the office has your request.");
      setOrg(""); setDesc(""); setBudget("");
      onCreated();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not submit the request.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
      <h3 className="font-heading font-bold text-ink text-sm">Start a service engagement</h3>
      <p className="text-xs text-ink/50 mt-1">
        Tell the office what you need — the AI workforce drafts the plan, a human signs off before anything ships.
      </p>
      <select value={service} onChange={(e) => setService(e.target.value)}
        className="w-full mt-3 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf", background: "#fff" }}>
        <option value="">Choose a division…</option>
        {divisions.filter((d) => d.status === "live").map((d) => (
          <option key={d.key} value={d.key}>{d.name}</option>
        ))}
      </select>
      <input value={org} onChange={(e) => setOrg(e.target.value)} placeholder="Your organization / brand"
        className="w-full mt-2 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      <textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="What do you need done? Scope, goals, timeline…"
        rows={3} className="w-full mt-2 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      <div className="flex gap-2 mt-2">
        <input value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="Budget ($, optional)"
          type="number" min="0" step="10"
          className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
        <button type="submit" disabled={busy}
          className="px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-50 flex items-center gap-1.5"
          style={{ background: GREEN }}>
          <Plus className="w-4 h-4" /> {busy ? "Sending…" : "Open deal"}
        </button>
      </div>
      <p className="text-[10px] text-ink/40 mt-2">
        You're signed in as {user?.full_name}. The office records you as the point of contact.
      </p>
    </form>
  );
}

/* ── Deals list ───────────────────────────────────────────────────────────── */
function DealsList({ deals, isAdmin, onChanged }) {
  const [note, setNote] = useState({});

  const draftProposal = async (dealId) => {
    try {
      await api.post(`/abo/deals/${dealId}/propose`);
      toast.success("Proposal drafted by the office AI.");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not draft the proposal.");
    }
  };

  const advance = async (deal, stage) => {
    try {
      const body = { stage };
      if (note[deal.id]) { body.note = note[deal.id]; setNote({}); }
      await api.patch(`/abo/deals/${deal.id}`, body);
      toast.success(`Deal moved to ${STAGE_LABEL[stage]}.`);
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not update the deal.");
    }
  };

  if (!deals.length) {
    return (
      <div className="card-flat rounded-2xl p-5 border flex flex-col items-center justify-center text-center" style={{ background: "#fff" }}>
        <Briefcase className="w-8 h-8" style={{ color: "#ddd3bf" }} />
        <p className="text-sm font-bold text-ink/60 mt-3">No deals yet</p>
        <p className="text-xs text-ink/40 mt-1">Open one on the left — it lands here as a Lead for the office to work.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
      {deals.map((d) => {
        const idx = STAGE_FLOW.indexOf(d.stage);
        const next = idx >= 0 && idx < STAGE_FLOW.length - 1 ? STAGE_FLOW[idx + 1] : null;
        return (
          <div key={d.id} className="card-flat rounded-2xl p-4 border" style={{ background: "#fff" }}>
            <div className="flex items-center justify-between gap-2">
              <div className="font-heading font-bold text-ink text-sm">{d.org_name}</div>
              <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                style={{ background: "rgba(192,87,45,0.1)", color: COPPER }}>
                {STAGE_LABEL[d.stage] || d.stage}
              </span>
            </div>
            <div className="text-xs text-ink/50 mt-0.5">{d.service_name}</div>
            <p className="text-xs text-ink/70 mt-2 leading-snug">{d.description}</p>
            {d.proposal && (
              <div className="mt-3 rounded-lg p-3" style={{ background: "#f8f3e8" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mb-1">
                  AI-drafted proposal · {d.proposal_provider || "gateway"}
                </div>
                <pre className="text-[11px] text-ink/70 whitespace-pre-wrap font-sans leading-relaxed max-h-40 overflow-y-auto">{d.proposal}</pre>
              </div>
            )}
            {isAdmin && !d.proposal && (
              <button onClick={() => draftProposal(d.id)}
                className="mt-3 px-3 py-1.5 rounded-lg text-xs font-black flex items-center gap-1.5 text-white"
                style={{ background: COPPER }}>
                ✨ Draft proposal (AI)
              </button>
            )}
            <div className="flex items-center justify-between mt-3 text-xs">
              <span className="font-black" style={{ color: GREEN }}>{fmt(d.value_cents)}</span>
              <div className="flex items-center gap-2">
                {d.status === "closed" && d.stage !== "closed_lost" && (
                  <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                    style={{ background: "rgba(45,106,79,0.12)", color: GREEN }}>
                    Contracted
                  </span>
                )}
                {d.human_approval && (
                  <span className="flex items-center gap-1 text-[10px] font-black" style={{ color: GREEN }}>
                    <ShieldCheck className="w-3.5 h-3.5" /> Human approved
                  </span>
                )}
              </div>
            </div>
            {isAdmin && next && (
              <div className="flex gap-2 mt-3">
                <button onClick={() => advance(d, next)}
                  className="flex-1 px-3 py-1.5 rounded-lg text-xs font-black text-white"
                  style={{ background: GREEN }}>
                  Advance to {STAGE_LABEL[next]} →
                </button>
                {d.stage === "lead" && (
                  <button onClick={() => advance(d, "closed_lost")}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold border"
                    style={{ borderColor: "#e5c9c4", color: "#B23A2E" }}>
                    Close lost
                  </button>
                )}
              </div>
            )}
            {isAdmin && (
              <input value={note[d.id] || ""} onChange={(e) => setNote((n) => ({ ...n, [d.id]: e.target.value }))}
                placeholder="Add a note (audited)…" className="w-full mt-2 px-3 py-1.5 rounded-lg border text-xs"
                style={{ borderColor: "#ddd3bf" }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Job form (admin) ─────────────────────────────────────────────────────── */
function JobForm({ divisions, onCreated }) {
  const [title, setTitle] = useState("");
  const [persona, setPersona] = useState("");
  const [division, setDivision] = useState("memberships");
  const [hours, setHours] = useState("4");
  const [workerType, setWorkerType] = useState("ai");
  const [value, setValue] = useState("50");
  const [pay, setPay] = useState("30");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!title) { toast.error("Give the job a title."); return; }
    setBusy(true);
    try {
      await api.post("/abo/jobs", {
        title,
        persona: persona || (workerType === "human" ? "Human — Operator" : "Platform AI"),
        division,
        hours: parseFloat(hours) || 0,
        worker_type: workerType,
        value_cents: workerType === "ai" ? Math.round((parseFloat(value) || 0) * 100) : 0,
        pay_cents: workerType === "human" ? Math.round((parseFloat(pay) || 0) * 100) : 0,
      });
      toast.success(workerType === "human" ? "Paid human job opened." : "AI job opened — its revenue pays people.");
      setTitle(""); setPersona("");
      onCreated();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not open the job.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="card-flat rounded-2xl p-4 border mt-3 flex flex-wrap items-end gap-2"
      style={{ background: "#fff", borderStyle: "dashed" }}>
      <div className="flex-1 min-w-[180px]">
        <label className="text-[10px] font-black uppercase tracking-widest text-ink/40">New job — people or AI</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Job title"
          className="w-full mt-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      </div>
      <select value={workerType} onChange={(e) => setWorkerType(e.target.value)}
        className="px-3 py-2 rounded-lg border text-sm font-bold" style={{ borderColor: "#ddd3bf" }}>
        <option value="ai">🤖 AI worker</option>
        <option value="human">👤 Human worker</option>
      </select>
      <input value={persona} onChange={(e) => setPersona(e.target.value)}
        placeholder={workerType === "human" ? "Role (e.g. Owner/Operator)" : "Persona (e.g. The Oracle)"}
        className="flex-1 min-w-[140px] px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      <select value={division} onChange={(e) => setDivision(e.target.value)}
        className="px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }}>
        {divisions.map((d) => <option key={d.key} value={d.key}>{d.name}</option>)}
      </select>
      <input value={hours} onChange={(e) => setHours(e.target.value)} type="number" min="0" step="0.5"
        placeholder="Hours" className="w-20 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      {workerType === "ai" ? (
        <input value={value} onChange={(e) => setValue(e.target.value)} type="number" min="0" step="5"
          placeholder="$ value" className="w-24 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
      ) : (
        <input value={pay} onChange={(e) => setPay(e.target.value)} type="number" min="0" step="5"
          placeholder="$ pay/hr" className="w-24 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: COPPER }} />
      )}
      <button type="submit" disabled={busy} className="px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-50"
        style={{ background: workerType === "human" ? COPPER : GREEN }}>
        {busy ? "Opening…" : "Open job"}
      </button>
    </form>
  );
}

/* ── Admin desk ───────────────────────────────────────────────────────────── */
function AdminDesk({ data, onChanged }) {
  const [goal, setGoal] = useState(data ? String((data.monthly_goal_cents || 100000) / 100) : "1000");
  const [busy, setBusy] = useState(false);

  const saveGoal = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/abo/goals", { monthly_goal_cents: Math.round(parseFloat(goal) * 100) || 100000 });
      toast.success("Monthly goal updated.");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not update the goal.");
    } finally {
      setBusy(false);
    }
  };

  const topProducts = Object.entries(data?.revenue?.by_product || {}).slice(0, 6);

  return (
    <section>
      <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
        <ShieldCheck className="w-5 h-5" style={{ color: GREEN }} /> Admin Desk — human oversight
      </h2>
      <div className="grid md:grid-cols-3 gap-4 mt-3">
        <form onSubmit={saveGoal} className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
          <h3 className="font-heading font-bold text-ink text-sm">Monthly operating goal</h3>
          <p className="text-xs text-ink/50 mt-1">What the office must raise per month to keep the mission funded.</p>
          <div className="flex gap-2 mt-3">
            <input value={goal} onChange={(e) => setGoal(e.target.value)} type="number" min="1" step="10"
              className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
            <button type="submit" disabled={busy} className="px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-50"
              style={{ background: GREEN }}>
              {busy ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
        <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
          <h3 className="font-heading font-bold text-ink text-sm">Top revenue sources</h3>
          {topProducts.length ? (
            <ul className="mt-2 space-y-1.5">
              {topProducts.map(([k, v]) => (
                <li key={k} className="flex justify-between text-xs">
                  <span className="text-ink/60 font-semibold capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="font-bold text-ink">{fmt(v)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-ink/40 mt-2">No paid orders recorded yet — the ledger fills in as checkout flows.</p>
          )}
        </div>
        <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
          <h3 className="font-heading font-bold text-ink text-sm">Recent orders</h3>
          <ul className="mt-2 space-y-1.5">
            {(data?.revenue?.recent_orders || []).slice(0, 6).map((o, i) => (
              <li key={i} className="flex justify-between text-xs">
                <span className="text-ink/60 truncate max-w-[60%]">{o.buyer_email || o.product_key || "Order"}</span>
                <span className="font-bold text-ink">{fmt(o.amount_cents)}</span>
              </li>
            ))}
            {!(data?.revenue?.recent_orders || []).length && (
              <li className="text-xs text-ink/40">No orders yet.</li>
            )}
          </ul>
        </div>
      </div>
    </section>
  );
}
