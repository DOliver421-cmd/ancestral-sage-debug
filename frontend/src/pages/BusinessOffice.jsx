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
import { roleAtLeast, ROLE_LABELS } from "../lib/roles";
import SourceProtocolPanel from "../components/SourceProtocolPanel";
import { MoreOpsContent } from "./MoreOps";
import { CompetitionArenaContent } from "./CompetitionArena";
import { HybridNamContent } from "./HybridNam";
import {
  Building2, TrendingUp, DollarSign, Receipt, Users, RefreshCw,
  ArrowRight, Plus, Wrench, Briefcase, Target, ShieldCheck, HeartHandshake, Sparkles, Lock, Loader2,
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

const fmtDt = (s) => {
  if (!s) return "—";
  const d = new Date(s);
  return isNaN(d) ? String(s) : d.toLocaleString();
};

// ── AI Business Office hub — the virtual back office of everything M.O.R.E. ──
// One office: the revenue engine, M.O.R.E. Ops (with Director Jamil inside),
// the Arena, and the executive control desk. Embedded views share the office
// shell so nothing is a dead link or a walled-off feature.
const HUB_TABS = [
  { id: "office",   label: "Office",   desc: "Revenue engine" },
  { id: "ops",      label: "More Ops", desc: "Department AI + Director Jamil" },
  { id: "nam",      label: "NAM",      desc: "Assistant Director" },
  { id: "projects", label: "Projects", desc: "AI team pipeline" },
  { id: "arena",    label: "Arena",    desc: "Competition" },
  { id: "control",  label: "Control",  desc: "Exec tools" },
];

function HubBar({ tab, setTab }) {
  return (
    <div style={{ background: "#0f2a1e", borderBottom: "1px solid rgba(232,165,30,0.25)", padding: "10px 24px" }}>
      <div className="flex flex-wrap gap-2">
        {HUB_TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", borderRadius: 10,
              border: tab === t.id ? "1px solid rgba(232,165,30,0.5)" : "1px solid rgba(255,255,255,0.12)",
              background: tab === t.id ? "rgba(232,165,30,0.14)" : "transparent",
              color: tab === t.id ? "#E8A51E" : "rgba(255,255,255,0.65)",
              fontSize: 13, fontWeight: 700, cursor: "pointer",
            }}
          >
            {t.label}
            <span style={{ fontSize: 10, fontWeight: 600, opacity: 0.6, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              {t.desc}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── AI Team Projects — the executive pipeline, inside the office ─────────────
// The AI team (Jamil coordinating personas) runs projects through the
// executive pipeline: intake → assign → execute → review → operate → deliver.
// This panel gives the office a live project workspace — create, advance,
// deliver, discuss — without leaving the hub.
const PIPE_STAGE_RANK = ["intake", "assign", "execute", "review", "operate", "deliver"];
const PIPE_STAGE_LABEL = { intake: "Intake", assign: "Assign", execute: "Execute", review: "Review", operate: "Operate", deliver: "Deliver" };
const PRIORITY_COLOR = { low: "#5B8C5A", normal: COPPER, high: "#B5651D", urgent: "#B23A2E" };

function ExecProjectsPanel() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [comments, setComments] = useState([]);
  const [showNew, setShowNew] = useState(false);
  const [showDiscovery, setShowDiscovery] = useState(false);
  const [discovery, setDiscovery] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [busy, setBusy] = useState(false);
  const [packetForm, setPacketForm] = useState(null);
  const [form, setForm] = useState({ title: "", brief: "", project_type: "general", priority: "normal" });
  const [deliv, setDeliv] = useState({ title: "", persona: "Jamil", content_type: "text", content: "", file_refs: "" });
  const [comment, setComment] = useState("");
  const [run, setRun] = useState({ persona: "Jamil", instructions: "" });
  const [showRun, setShowRun] = useState(false);
  const [running, setRunning] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/executive/projects");
      setProjects(data || []);
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openProject = async (p) => {
    setSelected(p);
    try {
      const [d, c] = await Promise.all([
        api.get(`/executive/projects/${p.id}`).then((r) => r.data).catch(() => null),
        api.get(`/executive/projects/${p.id}/comments`).then((r) => r.data || []).catch(() => []),
      ]);
      setDetail(d);
      setComments(Array.isArray(c) ? c : []);
      const pk = d?.packet;
      setPacketForm(pk ? {
        objective: pk.objective || "", owner: pk.owner || "", ai_team: (pk.ai_team || []).join(", "),
        deliverables_summary: pk.deliverables_summary || "", constraints: pk.constraints || "",
        authority: pk.authority || "approval_required", approval_points: (pk.approval_points || []).join(", "),
        evidence: pk.evidence || "", outcome_report: pk.outcome_report || "", packet_status: pk.packet_status || "planning",
      } : null);
    } catch {}
  };

  const scanDiscovery = async () => {
    setScanning(true);
    try {
      const { data } = await api.get("/executive/discovery");
      setDiscovery(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Scan failed.");
    } finally {
      setScanning(false);
    }
  };

  const startFromProposal = (proposal) => {
    setForm({ title: proposal.title, brief: proposal.brief, project_type: "general", priority: "normal" });
    setShowNew(true);
    setShowDiscovery(false);
  };

  const savePacket = async () => {
    if (!selected || !packetForm) return;
    setBusy(true);
    try {
      await api.put(`/executive/projects/${selected.id}/packet`, {
        ...packetForm,
        ai_team: packetForm.ai_team.split(",").map((s) => s.trim()).filter(Boolean),
        approval_points: packetForm.approval_points.split(",").map((s) => s.trim()).filter(Boolean),
      });
      toast.success("Project packet saved — the operating agreement is set.");
      await openProject(selected);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save packet.");
    } finally {
      setBusy(false);
    }
  };

  const createProject = async () => {
    if (!form.title.trim() || !form.brief.trim()) { toast.error("Title and brief are required."); return; }
    setBusy(true);
    try {
      await api.post("/executive/projects", form);
      toast.success("Project created — the AI team starts at Intake.");
      setShowNew(false);
      setForm({ title: "", brief: "", project_type: "general", priority: "normal" });
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to create project.");
    } finally {
      setBusy(false);
    }
  };

  const advance = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      await api.post(`/executive/projects/${selected.id}/advance`, {});
      toast.success("Advanced to the next stage — context flows forward.");
      await openProject(selected);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not advance.");
    } finally {
      setBusy(false);
    }
  };

  const runStage = async () => {
    if (!selected || !run.persona.trim()) { toast.error("Pick the persona to run this stage."); return; }
    setRunning(true);
    try {
      await api.post(`/executive/projects/${selected.id}/run-stage`, {
        persona: run.persona,
        instructions: run.instructions,
      });
      toast.success(`${run.persona} executed the stage — result posted as a pending deliverable.`);
      setShowRun(false);
      setRun({ persona: "Jamil", instructions: "" });
      await openProject(selected);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Stage run failed.");
    } finally {
      setRunning(false);
    }
  };

  const submitDeliverable = async () => {
    if (!selected || !deliv.title.trim()) { toast.error("Deliverable title is required."); return; }
    setBusy(true);
    try {
      await api.post(`/executive/projects/${selected.id}/deliverables`, {
        stage: detail?.current_stage || "execute",
        persona: deliv.persona || "Jamil",
        title: deliv.title,
        content_type: deliv.content_type,
        content: deliv.content,
        file_refs: deliv.file_refs.split("\n").map((s) => s.trim()).filter(Boolean),
      });
      toast.success("Deliverable submitted.");
      setDeliv({ title: "", persona: "Jamil", content_type: "text", content: "", file_refs: "" });
      await openProject(selected);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not submit deliverable.");
    } finally {
      setBusy(false);
    }
  };

  const addComment = async () => {
    if (!selected || !comment.trim()) return;
    try {
      await api.post(`/executive/projects/${selected.id}/comments`, { text: comment });
      setComment("");
      const c = await api.get(`/executive/projects/${selected.id}/comments`).then((r) => r.data || []).catch(() => []);
      setComments(Array.isArray(c) ? c : []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Comment failed.");
    }
  };

  const stageIdx = detail ? PIPE_STAGE_RANK.indexOf(detail.current_stage) : -1;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div>
            <div className="overline text-copper mb-1">AI Team Projects</div>
            <h2 className="font-heading text-2xl font-bold text-ink">The Pipeline</h2>
            <p className="text-sm text-ink/55 mt-1 max-w-2xl">
              Jamil coordinates, personas execute, the Source reviews. Every stage sees what the
              last produced — nothing is isolated. Give the team work to run.
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => { setShowDiscovery((v) => !v); if (!discovery && !showDiscovery) scanDiscovery(); }}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-black transition-colors"
              style={{ background: GOLD, color: "#0a0a0a" }}>
              <Sparkles className="w-4 h-4" /> {scanning ? "Scanning…" : "Discover"}
            </button>
            <button onClick={() => setShowNew(true)}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-black text-white transition-colors"
              style={{ background: GREEN }}>
              <Plus className="w-4 h-4" /> New Project
            </button>
          </div>
        </div>

        {showDiscovery && (
          <div className="card-flat rounded-2xl border p-5 mb-6" style={{ background: "#fff", borderColor: "rgba(232,165,30,0.4)" }}>
            <div className="font-heading font-bold text-ink mb-1">Turn what already exists into what comes next</div>
            <p className="text-sm text-ink/55 mb-4 max-w-2xl">
              The AI team catalogues existing material — published products, pipeline deliverables, audio — and
              proposes the highest-value next projects. Nothing is generated without your approval.
            </p>
            {scanning ? (
              <div className="py-6 text-center text-sm text-ink/45 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Cataloguing existing material…
              </div>
            ) : discovery ? (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {[
                    { label: "Total assets", n: discovery.assets?.total },
                    { label: "Audio products", n: discovery.assets?.audio_products },
                    { label: "Published products", n: discovery.assets?.published_products },
                    { label: "Pipeline deliverables", n: discovery.assets?.pipeline_deliverables },
                  ].map((s) => (
                    <div key={s.label} className="rounded-xl p-4 text-center" style={{ background: "#faf9f7" }}>
                      <div className="font-heading text-2xl font-bold" style={{ color: GREEN }}>{s.n ?? 0}</div>
                      <div className="text-[10px] font-black uppercase tracking-widest text-ink/40 mt-1">{s.label}</div>
                    </div>
                  ))}
                </div>
                {(discovery.proposals || []).length === 0 ? (
                  <p className="text-sm text-ink/45 italic">No proposals yet — create material first, then scan again.</p>
                ) : (
                  <div className="grid md:grid-cols-2 gap-3">
                    {discovery.proposals.map((pr) => (
                      <div key={pr.title} className="rounded-xl border p-4" style={{ borderColor: "rgba(181,101,29,0.25)", background: "#fdfbf5" }}>
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="font-bold text-sm text-ink">{pr.title}</span>
                          <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                            style={{ background: "rgba(27,67,50,0.1)", color: GREEN }}>
                            {pr.authority}
                          </span>
                        </div>
                        <p className="text-xs text-ink/60 mb-2">{pr.rationale}</p>
                        <p className="text-[10px] text-ink/45 mb-3">AI team: {pr.suggested_team.join(", ")}</p>
                        <button onClick={() => startFromProposal(pr)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black text-white"
                          style={{ background: COPPER }}>
                          <Plus className="w-3 h-3" /> Start project from this
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}

        {showNew && (
          <div className="card-flat rounded-2xl border p-5 mb-6" style={{ background: "#fff" }}>
            <div className="font-heading font-bold text-ink mb-4">Give the AI team work</div>
            <div className="grid sm:grid-cols-2 gap-3 mb-3">
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Project title — e.g. Launch my youth program"
                className="px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
              <div className="flex gap-2">
                <select value={form.project_type} onChange={(e) => setForm({ ...form, project_type: e.target.value })}
                  className="px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                  {["general", "release", "campaign", "content", "course"].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                  className="px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                  {["low", "normal", "high", "urgent"].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <textarea value={form.brief} onChange={(e) => setForm({ ...form, brief: e.target.value })}
              placeholder="Brief — what is the goal, what does done look like?" rows={3}
              className="w-full px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y mb-3" />
            <div className="flex gap-2">
              <button onClick={createProject} disabled={busy}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40" style={{ background: GREEN }}>
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Start project
              </button>
              <button onClick={() => setShowNew(false)} className="px-4 py-2 rounded-lg text-sm font-bold text-ink/50 hover:text-ink">Cancel</button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-16 text-center text-ink/50 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading the pipeline…
          </div>
        ) : projects.length === 0 && !showNew ? (
          <div className="card-flat rounded-2xl border p-10 text-center" style={{ background: "#fff" }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🗂️</div>
            <div className="font-heading font-bold text-lg text-ink">The pipeline is empty</div>
            <p className="text-sm text-ink/55 max-w-md mx-auto mt-2">
              The AI team is ready to run. Start a project and Jamil will coordinate personas through
              intake → assign → execute → review → operate → deliver.
            </p>
            <button onClick={() => setShowNew(true)}
              className="mt-5 inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-black text-white" style={{ background: GREEN }}>
              <Plus className="w-4 h-4" /> Start the first project
            </button>
          </div>
        ) : (
          <div className="grid lg:grid-cols-5 gap-5">
            {/* Project list */}
            <div className="lg:col-span-2 space-y-2">
              {projects.map((p) => (
                <button key={p.id} onClick={() => openProject(p)}
                  className={`w-full text-left card-flat rounded-xl p-4 border transition-all ${selected?.id === p.id ? "border-copper" : "hover:border-copper/40"}`}
                  style={{ background: "#fff" }}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-heading font-bold text-ink text-sm">{p.title}</span>
                    <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                      style={{ background: `${PRIORITY_COLOR[p.priority] || COPPER}15`, color: PRIORITY_COLOR[p.priority] || COPPER }}>
                      {p.priority}
                    </span>
                  </div>
                  <div className="text-xs text-ink/50 mt-1 line-clamp-2">{p.brief}</div>
                  <div className="flex items-center gap-2 mt-2 text-[10px] font-black uppercase tracking-widest text-ink/40">
                    <span style={{ color: COPPER }}>{PIPE_STAGE_LABEL[p.current_stage] || p.current_stage}</span>
                    <span>· {(p.deliverables || []).length} deliverables</span>
                    <span className="ml-auto">{new Date(p.updated_at).toLocaleDateString()}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Detail */}
            <div className="lg:col-span-3 space-y-4">
              {!selected ? (
                <div className="card-flat rounded-2xl border p-8 text-center text-sm text-ink/45" style={{ background: "#fff" }}>
                  Select a project to open the pipeline workspace.
                </div>
              ) : (
                <>
                  <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-bold text-lg text-ink">{selected.title}</span>
                      {detail && (
                        <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded text-white" style={{ background: GREEN }}>
                          {PIPE_STAGE_LABEL[detail.current_stage] || detail.current_stage}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-ink/60 mt-2">{selected.brief}</p>
                    {detail?.stage_history?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {detail.stage_history.map((s, i) => (
                          <span key={i} className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full"
                            style={{ background: "#f3ede2", color: COPPER }}>
                            {PIPE_STAGE_LABEL[s.stage] || s.stage}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      <button onClick={() => setShowRun((v) => !v)} disabled={running}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black disabled:opacity-40 transition-colors"
                        style={{ background: GREEN, color: "#fff" }}>
                        {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        Run stage
                      </button>
                      {stageIdx >= 0 && stageIdx < PIPE_STAGE_RANK.length - 1 && (
                        <button onClick={advance} disabled={busy}
                          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40 transition-colors"
                          style={{ background: COPPER }}>
                          <ArrowRight className="w-4 h-4" />
                          Advance to {PIPE_STAGE_LABEL[PIPE_STAGE_RANK[stageIdx + 1]]}
                        </button>
                      )}
                    </div>
                    {showRun && (
                      <div className="mt-3 rounded-xl border p-4" style={{ borderColor: "rgba(27,67,50,0.3)", background: "#f8f6f0" }}>
                        <div className="text-xs font-black uppercase tracking-widest mb-2" style={{ color: GREEN }}>
                          AI executes this stage
                        </div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          <select value={run.persona} onChange={(e) => setRun({ ...run, persona: e.target.value })}
                            className="px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                            {["Jamil", "Hybrid NAM", "Production", "Creative Partner", "Marketing", "Review", "Source", "Operations", "Analytics", "Architect", "Ghost Producer"].map((p) => (
                              <option key={p} value={p}>{p}</option>
                            ))}
                          </select>
                          <input value={run.instructions} onChange={(e) => setRun({ ...run, instructions: e.target.value })}
                            placeholder="Optional direction for this run (or let the persona read the brief)"
                            className="flex-1 min-w-[220px] px-3 py-2 bg-white border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </div>
                        <div className="flex items-center gap-3">
                          <button onClick={runStage} disabled={running}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40"
                            style={{ background: GREEN }}>
                            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                            {running ? "Executing…" : `Run with ${run.persona}`}
                          </button>
                          <span className="text-[10px] text-ink/45">
                            Result lands as a pending deliverable — you approve, reject, or request revision.
                          </span>
                        </div>
                      </div>
                    )}
                    {detail?.packet?.packet_status && (
                      <div className="mt-3 flex items-center gap-2 flex-wrap text-[10px] font-black uppercase tracking-widest text-ink/40">
                        <span>Packet:</span>
                        <span style={{ color: GREEN }}>{detail.packet.packet_status}</span>
                        <span>· Authority:</span>
                        <span style={{ color: COPPER }}>{detail.packet.authority}</span>
                        {(detail.packet.approval_points || []).length > 0 && (
                          <span>· {detail.packet.approval_points.length} approval point{(detail.packet.approval_points || []).length === 1 ? "" : "s"}</span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Project packet — the operating agreement */}
                  <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff", borderColor: "rgba(27,67,50,0.25)" }}>
                    <div className="font-heading font-bold text-ink mb-1">Project Packet</div>
                    <p className="text-xs text-ink/50 mb-4">
                      The operating agreement: what the AI team may do, what needs your approval, and what only you decide.
                    </p>
                    {packetForm ? (
                      <div className="grid sm:grid-cols-2 gap-3">
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Objective</span>
                          <input value={packetForm.objective} onChange={(e) => setPacketForm({ ...packetForm, objective: e.target.value })}
                            placeholder="What are we trying to accomplish?"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Owner</span>
                          <input value={packetForm.owner} onChange={(e) => setPacketForm({ ...packetForm, owner: e.target.value })}
                            placeholder="You / designated human"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">AI team (comma separated)</span>
                          <input value={packetForm.ai_team} onChange={(e) => setPacketForm({ ...packetForm, ai_team: e.target.value })}
                            placeholder="Jamil, Hybrid NAM, Production…"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Authority — what the AI can do without asking</span>
                          <select value={packetForm.authority} onChange={(e) => setPacketForm({ ...packetForm, authority: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                            <option value="autonomous">Autonomous — completes without asking</option>
                            <option value="approval_required">Approval required — prepares, you approve</option>
                            <option value="human_only">Human-only — advises, cannot execute</option>
                          </select>
                        </label>
                        <label className="block">
                          <span className="text-xs font-bold text-ink/60">Packet status</span>
                          <select value={packetForm.packet_status} onChange={(e) => setPacketForm({ ...packetForm, packet_status: e.target.value })}
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                            {["planning", "active", "review", "approved", "published", "complete"].map((s) => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </label>
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Approval points (comma separated) — what requires you</span>
                          <input value={packetForm.approval_points} onChange={(e) => setPacketForm({ ...packetForm, approval_points: e.target.value })}
                            placeholder="Release track, publish campaign, submit grant…"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Constraints (budget, timeline, platform rules, brand)</span>
                          <textarea value={packetForm.constraints} onChange={(e) => setPacketForm({ ...packetForm, constraints: e.target.value })}
                            rows={2} placeholder="What bounds the work?"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
                        </label>
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Evidence required</span>
                          <input value={packetForm.evidence} onChange={(e) => setPacketForm({ ...packetForm, evidence: e.target.value })}
                            placeholder="What research / support must back decisions?"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                        </label>
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Deliverables summary</span>
                          <textarea value={packetForm.deliverables_summary} onChange={(e) => setPacketForm({ ...packetForm, deliverables_summary: e.target.value })}
                            rows={2} placeholder="What must exist when finished?"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
                        </label>
                        <label className="block sm:col-span-2">
                          <span className="text-xs font-bold text-ink/60">Post-project report</span>
                          <textarea value={packetForm.outcome_report} onChange={(e) => setPacketForm({ ...packetForm, outcome_report: e.target.value })}
                            rows={2} placeholder="What happened? What worked? What didn't?"
                            className="mt-1 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
                        </label>
                        <div className="sm:col-span-2 flex gap-2">
                          <button onClick={savePacket} disabled={busy}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40" style={{ background: GREEN }}>
                            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Save packet
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button onClick={() => setPacketForm({
                        objective: "", owner: "", ai_team: "", deliverables_summary: "", constraints: "",
                        authority: "approval_required", approval_points: "", evidence: "", outcome_report: "", packet_status: "planning",
                      })}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white" style={{ background: GREEN }}>
                        <Sparkles className="w-4 h-4" /> Define the packet
                      </button>
                    )}
                  </div>

                  {/* Deliverables */}
                  <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                    <div className="font-heading font-bold text-ink mb-3">Deliverables</div>
                    {(detail?.deliverables || []).length === 0 ? (
                      <p className="text-sm text-ink/45 italic">Nothing delivered yet — personas produce here.</p>
                    ) : (
                      <div className="space-y-2">
                        {detail.deliverables.map((d) => (
                          <div key={d.id || d._id} className="rounded-lg border border-ink/8 bg-bone/60 p-3">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-bold text-ink">{d.title}</span>
                              <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(181,101,29,0.1)", color: COPPER }}>
                                {d.content_type}
                              </span>
                              <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(27,67,50,0.1)", color: GREEN }}>
                                {d.persona}
                              </span>
                              <span className="text-[10px] text-ink/40">{d.approval_status}</span>
                            </div>
                            {d.content && <p className="text-xs text-ink/60 mt-1">{d.content}</p>}
                            {d.file_refs?.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {d.file_refs.map((f, i) => <span key={i} className="text-[10px] font-mono text-copper">🔗 {f}</span>)}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="grid sm:grid-cols-2 gap-2 mt-4">
                      <input value={deliv.title} onChange={(e) => setDeliv({ ...deliv, title: e.target.value })}
                        placeholder="Deliverable title" className="px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                      <div className="flex gap-2">
                        <select value={deliv.content_type} onChange={(e) => setDeliv({ ...deliv, content_type: e.target.value })}
                          className="px-2 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                          {["text", "audio", "image", "video", "code", "document", "mixed"].map((t) => <option key={t} value={t}>{t}</option>)}
                        </select>
                        <select value={deliv.persona} onChange={(e) => setDeliv({ ...deliv, persona: e.target.value })}
                          className="px-2 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper">
                          {["Jamil", "Hybrid NAM", "Production", "Revenue", "Finance", "Creative Partner", "Owner"].map((t) => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                    </div>
                    <textarea value={deliv.content} onChange={(e) => setDeliv({ ...deliv, content: e.target.value })}
                      placeholder="Content or description — or paste a file URL / product link below" rows={2}
                      className="mt-2 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
                    <textarea value={deliv.file_refs} onChange={(e) => setDeliv({ ...deliv, file_refs: e.target.value })}
                      placeholder="File URLs / product links — one per line" rows={2}
                      className="mt-2 w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y" />
                    <button onClick={submitDeliverable} disabled={busy}
                      className="mt-2 flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40" style={{ background: GREEN }}>
                      {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Submit deliverable
                    </button>
                  </div>

                  {/* Comments */}
                  <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                    <div className="font-heading font-bold text-ink mb-3">Thread</div>
                    {comments.length === 0 ? (
                      <p className="text-sm text-ink/45 italic">No discussion yet.</p>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {comments.map((c, i) => (
                          <div key={i} className="rounded-lg bg-bone/70 p-3 text-sm text-ink/75">
                            {c.text}
                            <div className="text-[10px] text-ink/35 mt-1">{c.persona || "Owner"} · {fmtDt(c.created_at)}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2 mt-3">
                      <input value={comment} onChange={(e) => setComment(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); addComment(); } }}
                        placeholder="Comment — as owner or a persona"
                        className="flex-1 px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper" />
                      <button onClick={addComment} className="px-4 py-2 rounded-lg text-sm font-black text-white" style={{ background: GREEN }}>Post</button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// The executive control desk — every back-office control in one place. These
// are real, working tools (IAM, Feature Control, audit, etc.), not dead links.
function ExecControlDesk() {
  const controls = [
    { icon: "IAM",       title: "IAM Console",        desc: "Roles, permissions, and who can do what.",        to: "/admin/iam" },
    { icon: "FCC",       title: "Feature Control",    desc: "Turn platform features and flags on or off.",      to: "/admin/features" },
    { icon: "CTL",       title: "Site Control",       desc: "Platform lock, maintenance, and exec controls.",   to: "/admin/control" },
    { icon: "AUD",       title: "Audit Log",          desc: "Every action, who did it, and when.",              to: "/admin/audit" },
    { icon: "CMD",       title: "Command Center",     desc: "Executive command and oversight.",                to: "/admin/command" },
    { icon: "OFF",       title: "Exec Business Office", desc: "Advanced office and distribution controls.",     to: "/admin/office" },
    { icon: "BRG",       title: "AI Team Bridge",     desc: "Cross-team AI coordination and handoffs.",        to: "/admin/bridge" },
    { icon: "ANA",       title: "Analytics",          desc: "Platform analytics and trends.",                  to: "/admin/analytics" },
  ];
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="overline text-copper mb-2">Executive Control</div>
        <h2 className="font-heading text-2xl font-bold text-ink mb-2">The Control Desk</h2>
        <p className="text-sm text-ink/55 max-w-2xl mb-8">
          Every back-office control in one place — IAM, feature flags, audit, command, and
          platform controls. Data is live; nothing here is a dead link.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {controls.map((c) => (
            <Link key={c.title} to={c.to}
              className="card-flat rounded-2xl p-6 border hover:border-copper transition-all group no-underline"
              style={{ background: "#fff" }}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-[10px] font-black tracking-widest px-2 py-1 rounded"
                  style={{ background: "#f5f0e8", color: COPPER }}>{c.icon}</span>
                <div className="font-heading font-bold text-ink group-hover:text-copper transition-colors">{c.title}</div>
              </div>
              <p className="text-sm text-ink/55 leading-relaxed">{c.desc}</p>
              <div className="mt-4 text-xs font-bold uppercase tracking-widest text-copper flex items-center gap-1">
                Open <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function BusinessOffice() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "executive_admin";

  const [overview, setOverview] = useState(null);
  const [tools, setTools] = useState(null);
  const [deals, setDeals] = useState([]);
  const [jobs, setJobs] = useState(null);
  const [exchange, setExchange] = useState(null);
  const [redteam, setRedteam] = useState(null);
  const [adminData, setAdminData] = useState(null);
  const [audit, setAudit] = useState(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [agenda, setAgenda] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("office");

  const load = useCallback(async () => {
    try {
      const [ov, tl, dl, jb, xc, rt, ag] = await Promise.all([
        api.get("/abo/overview"),
        api.get("/abo/tools"),
        api.get("/abo/deals"),
        api.get("/abo/jobs"),
        api.get("/abo/exchange"),
        api.get("/abo/redteam"),
        api.get("/abo/agenda"),
      ]);
      setOverview(ov.data);
      setTools(tl.data);
      setDeals(dl.data.deals || []);
      setJobs(jb.data);
      setExchange(xc.data);
      setRedteam(rt.data);
      setAgenda(ag.data.agenda || []);
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

  // Truth Test — deterministic, zero-token check of every office claim against
  // the real ledger. Optional free-tier AI explainer (?explain=1) teaches the
  // business in plain language; if the free quota is out the audit still runs.
  const advanceAgenda = useCallback(async (itemId, status) => {
    try {
      await api.patch(`/abo/agenda/${itemId}`, { status });
      setAgenda(prev => prev.map(i => i.item_id === itemId ? { ...i, status } : i));
      toast.success(`Agenda item ${status}`);
    } catch {
      toast.error("Could not update agenda item.");
    }
  }, []);

  const runAudit = useCallback(async (withExplain) => {
    setAuditLoading(true);
    try {
      const { data } = await api.get("/abo/verify", { params: withExplain ? { explain: 1 } : {} });
      setAudit(data);
    } catch {
      toast.error("Truth Test could not run — check the backend connection.");
    } finally {
      setAuditLoading(false);
    }
  }, []);

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

  if (tab === "source") {
    return (
      <AppShell>
        <SourceProtocolPanel onOpenOffice={() => setTab("office")} />
      </AppShell>
    );
  }

  // Hub views — More Ops (with Director Jamil inside) and the Arena live
  // inside the AI Business Office; the Control Desk hosts the exec tools.
  if (tab === "ops" || tab === "nam" || tab === "projects" || tab === "arena" || tab === "control") {
    return (
      <AppShell>
        <div className="h-[calc(100vh-4rem)] flex flex-col" style={{ background: BONE }}>
          <div className="flex-shrink-0"><HubBar tab={tab} setTab={setTab} /></div>
          <div className="flex-1 min-h-0 overflow-hidden">
            {tab === "ops" && <MoreOpsContent embedded />}
            {tab === "nam" && <HybridNamContent embedded />}
            {tab === "projects" && <ExecProjectsPanel />}
            {tab === "arena" && <CompetitionArenaContent embedded />}
            {tab === "control" && <ExecControlDesk />}
          </div>
        </div>
      </AppShell>
    );
  }

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
            <button onClick={() => setTab("source")}
              className="ml-2 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded cursor-pointer transition-opacity"
              style={{ background: "#fff", color: GREEN, opacity: 0.92 }}
              onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; }}
              onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.92; }}>
              ◉ The Source
            </button>
          </div>
          <p className="text-white/80 text-sm mt-2 max-w-2xl">
            This office turns the platform's AI capabilities into mission funding — and it is <b>owner-first</b>.
            Revenue covers infrastructure costs, then profit belongs to the business entity and the founder.
            Nothing is auto-drained; every distribution happens only when the owner says so, only from net profit.
          </p>
          <div className="flex flex-wrap gap-2 mt-4">
            {tools?.tools?.slice(0, 12).filter(t => !t.access || t.access === "student" || roleAtLeast(user?.role || "public", t.access)).map((t) => (
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

        <div className="flex-shrink-0"><HubBar tab={tab} setTab={setTab} /></div>

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

          {/* ── 2a. Owner-First P&L ─────────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <TrendingUp className="w-5 h-5" style={{ color: COPPER }} /> Owner-First P&L — the founder is secured first
            </h2>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl">
              The waterfall is the law of the office: revenue → infrastructure costs → net profit to the owner and
              the business entity. Distributions to any role happen only when the owner records them, only out of net profit.
            </p>
            <div className="grid md:grid-cols-5 gap-4 mt-3">
              <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40">1 · Gross revenue (month)</div>
                <div className="font-heading text-2xl font-bold text-ink mt-2">{fmt(overview?.pnl?.gross_cents)}</div>
                <div className="text-[11px] text-ink/50 mt-1">Real paid orders, this month.</div>
              </div>
              <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40">2 · Infrastructure costs</div>
                <div className="font-heading text-2xl font-bold text-ink mt-2">−{fmt(overview?.pnl?.infra_cents)}</div>
                <div className="text-[11px] text-ink/50 mt-1">Hosting, API tokens, database — covered first.</div>
              </div>
              <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40">3 · Net profit</div>
                <div className="font-heading text-2xl font-bold mt-2" style={{ color: GREEN }}>{fmt(overview?.pnl?.net_profit_cents)}</div>
                <div className="text-[11px] text-ink/50 mt-1">Belongs to the owner / business entity.</div>
              </div>
              <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40">4 · Owner retained ({overview?.pnl?.owner_draw_pct}%)</div>
                <div className="font-heading text-2xl font-bold mt-2" style={{ color: GOLD }}>{fmt(overview?.pnl?.owner_retained_cents)}</div>
                <div className="text-[11px] text-ink/50 mt-1">Until the owner is whole, there is no profit unless the owner says there is.</div>
              </div>
              <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
                <div className="text-[10px] font-black uppercase tracking-widest text-ink/40">5 · Performance pool</div>
                <div className="font-heading text-2xl font-bold mt-2" style={{ color: COPPER }}>{fmt(overview?.pnl?.distributable_cents)}</div>
                <div className="text-[11px] text-ink/50 mt-1">
                  {overview?.pnl?.fully_payable
                    ? "Net profit covers committed human milestones."
                    : "Net profit is below committed milestones — nothing pays until it clears."}
                </div>
              </div>
            </div>
            <p className="text-[10px] text-ink/40 mt-2">
              {overview?.pnl?.waterfall_note} Infrastructure costs are editable from the Exec Control page — no code.
            </p>
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

          {/* ── 2c. Business Agenda — projects & items waiting for the office ── */}
          <section>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
                <Target className="w-5 h-5" style={{ color: GOLD }} /> Business Agenda
              </h2>
              <span className="text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-full" style={{ background: "rgba(232,165,30,0.15)", color: "#8a6400" }}>
                {agenda.filter(i => i.status === "pending").length} pending
              </span>
            </div>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl leading-relaxed">
              Every new project automatically becomes an agenda item here — no manual step. The office works the
              list from <b>pending</b> → <b>on_agenda</b> → <b>discussed</b> → <b>resolved</b>.
            </p>
            {agenda.length === 0 ? (
              <p className="text-sm text-ink/40 text-center py-6">
                The agenda is empty — create a project at /projects and it appears here automatically.
              </p>
            ) : (
              <div className="mt-3 rounded-2xl border overflow-hidden" style={{ background: "#fff" }}>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[10px] font-black uppercase tracking-widest text-ink/40 border-b" style={{ background: "#f8f3e8" }}>
                      <th className="px-4 py-2.5">Item</th>
                      <th className="px-4 py-2.5">Owner</th>
                      <th className="px-4 py-2.5">Priority</th>
                      <th className="px-4 py-2.5">Status</th>
                      <th className="px-4 py-2.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agenda.map((item) => {
                      const statusColor =
                        item.status === "resolved" || item.status === "discussed" ? { c: "#1b7a3d", bg: "#e7f4ec" }
                        : item.status === "on_agenda" ? { c: "#8a6400", bg: "#fdf3d8" }
                        : item.status === "dropped" ? { c: "#8a8a8a", bg: "#f0f0f0" }
                        : { c: "#b3261e", bg: "#fdeaea" };
                      return (
                        <tr key={item.item_id} className="border-b border-ink/5">
                          <td className="px-4 py-2.5">
                            <div className="font-bold text-ink text-xs">{item.title}</div>
                            <div className="text-[10px] text-ink/40">
                              {item.source === "project" && item.project_id ? (
                                <Link to={`/projects`} className="hover:text-copper">#{item.project_id}</Link>
                              ) : item.source}
                              {item.due_date && <span className="ml-2">📅 {item.due_date}</span>}
                            </div>
                          </td>
                          <td className="px-4 py-2.5 text-xs text-ink/60">{item.owner || "—"}</td>
                          <td className="px-4 py-2.5 text-xs">
                            <span className="uppercase font-bold" style={{ color: item.priority === "critical" ? "#dc2626" : item.priority === "high" ? "#ea580c" : COPPER }}>
                              {item.priority || "normal"}
                            </span>
                          </td>
                          <td className="px-4 py-2.5">
                            <span className="inline-block text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full" style={{ color: statusColor.c, background: statusColor.bg }}>
                              {item.status}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right">
                            {isAdmin && item.status !== "resolved" && item.status !== "dropped" && (
                              <select
                                value={item.status}
                                onChange={(e) => advanceAgenda(item.item_id, e.target.value)}
                                className="text-xs font-bold rounded-lg border px-2 py-1.5"
                                style={{ borderColor: "#ddd3bf", color: GREEN }}
                              >
                                <option value="pending">Pending</option>
                                <option value="on_agenda">On agenda</option>
                                <option value="discussed">Discussed</option>
                                <option value="resolved">Resolved</option>
                                <option value="dropped">Dropped</option>
                              </select>
                            )}
                            {(!isAdmin || item.status === "resolved" || item.status === "dropped") && (
                              <span className="text-[10px] text-ink/40">{item.updated_by ? `by ${item.updated_by}` : ""}</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* ── 2d. Truth Test — every claim, checked against the real ledger ── */}
          <section>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
                <ShieldCheck className="w-5 h-5" style={{ color: GREEN }} /> Truth Test — are these claims real?
              </h2>
              <div className="flex gap-2">
                <button onClick={() => runAudit(false)} disabled={auditLoading}
                  className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg border transition-colors disabled:opacity-50"
                  style={{ borderColor: "#ddd3bf", color: GREEN }}>
                  <RefreshCw className="w-3.5 h-3.5" /> {auditLoading ? "Checking…" : "Run Truth Test"}
                </button>
                <button onClick={() => runAudit(true)} disabled={auditLoading}
                  className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg text-white transition-colors disabled:opacity-50"
                  style={{ background: GREEN }}>
                  <Sparkles className="w-3.5 h-3.5" /> {auditLoading ? "Checking…" : "Run + teach me the business"}
                </button>
              </div>
            </div>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl leading-relaxed">
              Every number this office shows is recomputed from the real ledger (payments, deals, jobs, exchange,
              red-team) — <b>zero API tokens</b>. <b className="text-green-700">Verified</b> matches the ledger,
              <b className="text-red-600"> mismatch</b> means the display is wrong, <b className="text-ink/60">target</b> is an
              owner-set goal, <b className="text-amber-600">copy</b> is aspirational marketing (price ranges, taglines) —
              realized only when deals close — and <b className="text-ink/40">empty</b> is an honest zero.
            </p>

            {!audit && !auditLoading && (
              <p className="text-sm text-ink/40 text-center py-8">
                Press “Run Truth Test” to audit every claim in the office against the real data.
              </p>
            )}

            {audit && (
              <div className="mt-3 rounded-2xl border overflow-hidden" style={{ background: "#fff" }}>
                {/* Summary bar */}
                <div className="flex items-center gap-3 flex-wrap px-4 py-3 border-b" style={{ background: "#f8f3e8" }}>
                  <span className={`text-[11px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full ${audit.verdict === "clean" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                    {audit.verdict === "clean" ? "✓ Every claim matches the ledger" : "! Attention — mismatches found"}
                  </span>
                  <span className="text-xs text-ink/50">{audit.summary.verified} verified · {audit.summary.mismatch} mismatch · {audit.summary.target} target · {audit.summary.copy} copy · {audit.summary.empty} empty · {audit.summary.total} total</span>
                </div>

                {/* AI explainer (free tier) */}
                {audit.explainer?.text && (
                  <div className="px-4 py-3 border-b" style={{ background: "#f0f7f2" }}>
                    <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest mb-1.5" style={{ color: GREEN }}>
                      <Sparkles className="w-3.5 h-3.5" /> Free-tier business briefing
                    </div>
                    <p className="text-sm text-ink/80 leading-relaxed">{audit.explainer.text}</p>
                  </div>
                )}
                {audit.explainer && !audit.explainer.text && (
                  <div className="px-4 py-2.5 border-b text-xs" style={{ background: "#fdf6e3" }}>
                    {audit.explainer.note}
                  </div>
                )}

                {/* Checks table */}
                <div className="max-h-[420px] overflow-y-auto overflow-x-auto">
                  <table className="w-full text-sm min-w-[640px]">
                    <thead className="sticky top-0" style={{ background: "#fff" }}>
                      <tr className="text-left text-[10px] font-black uppercase tracking-widest text-ink/40 border-b">
                        <th className="px-4 py-2.5">Claim</th>
                        <th className="px-4 py-2.5">Office shows</th>
                        <th className="px-4 py-2.5">Verdict</th>
                        <th className="px-4 py-2.5 hidden md:table-cell">Source / note</th>
                      </tr>
                    </thead>
                    <tbody>
                      {audit.checks.map((c) => {
                        const verdictStyle =
                          c.verdict === "verified" ? { color: "#1b7a3d", bg: "#e7f4ec" }
                          : c.verdict === "mismatch" ? { color: "#b3261e", bg: "#fdeaea" }
                          : c.verdict === "target" ? { color: "#6b5b3e", bg: "#f3ecd9" }
                          : c.verdict === "copy" ? { color: "#8a6400", bg: "#fdf3d8" }
                          : { color: "#8a8a8a", bg: "#f0f0f0" };
                        return (
                          <tr key={c.key} className="border-b border-ink/5 align-top">
                            <td className="px-4 py-2.5">
                              <div className="font-bold text-ink text-xs">{c.label}</div>
                              <div className="text-[10px] text-ink/40 uppercase tracking-wider">{c.section}</div>
                            </td>
                            <td className="px-4 py-2.5 text-xs text-ink/70 whitespace-nowrap">{c.claim}</td>
                            <td className="px-4 py-2.5">
                              <span className="inline-block text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full"
                                style={{ color: verdictStyle.color, background: verdictStyle.bg }}>
                                {c.verdict}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-[11px] text-ink/50 hidden md:table-cell leading-snug max-w-[340px]">{c.note}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
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
              {(tools?.tools || []).map((t) => {
                const hasAccess = !t.access || t.access === "student" || roleAtLeast(user?.role || "public", t.access);
                const accessLabel = ROLE_LABELS[t.access] || t.access;
                if (!hasAccess) {
                  return (
                    <div key={t.key}
                      className="card-flat rounded-2xl p-5 border opacity-60 cursor-not-allowed"
                      style={{ background: "#f9f6f0", borderColor: "#eee7d8" }}>
                      <div className="flex items-center gap-3">
                        <span className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                          style={{ background: "#e8e2d4" }}>{t.icon}</span>
                        <div>
                          <div className="font-heading font-bold text-ink">{t.name}</div>
                          <div className="text-[10px] font-black uppercase tracking-widest flex items-center gap-1" style={{ color: "#999" }}>
                            <Lock className="w-3 h-3" /> {accessLabel} required
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-ink/50 mt-3 leading-snug">{t.what}</p>
                      <div className="mt-3 pt-3 border-t border-ink/5">
                        <span className="text-[11px] font-bold text-ink/40">{t.revenue}</span>
                      </div>
                    </div>
                  );
                }
                return (
                  <Link key={t.key} to={t.link}
                    className="card-flat rounded-2xl p-5 border no-underline transition-all hover:-translate-y-0.5 hover:shadow-lg"
                    style={{ background: "#fff", borderColor: "#eee7d8" }}>
                    <div className="flex items-center gap-3">
                      <span className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                        style={{ background: "linear-gradient(135deg,#1B4332,#2D6A4F)" }}>{t.icon}</span>
                      <div>
                        <div className="font-heading font-bold text-ink">{t.name}</div>
                        <div className="text-[10px] font-black uppercase tracking-widest" style={{ color: COPPER }}>{accessLabel}</div>
                      </div>
                    </div>
                    <p className="text-sm text-ink/70 mt-3 leading-snug">{t.what}</p>
                    <div className="mt-3 pt-3 border-t border-ink/5 flex items-center justify-between">
                      <span className="text-[11px] font-bold text-ink/50">{t.revenue}</span>
                      <span className="text-xs font-black" style={{ color: GREEN }}>Open →</span>
                    </div>
                  </Link>
                );
              })}
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

          {/* ── 4a. A2A Economy — Workforce Exchange + Red-Teaming Bureau ── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <RefreshCw className="w-5 h-5" style={{ color: GOLD }} /> A2A Economy — AI doing business with AI, cleared by you
            </h2>
            <p className="text-xs text-ink/50 mt-1 max-w-3xl">
              Two new revenue lanes: the <b>Workforce Exchange</b> (agents subcontract tasks; the office takes a
              clearinghouse fee on every completed contract) and the <b>Red-Teaming Bureau</b> (adversarial AI scans
              client systems and hands over patches — one human Merge/Approve click ships them).
            </p>
            <div className="grid md:grid-cols-2 gap-4 mt-3">
              <ExchangeBoard data={exchange} isAdmin={isAdmin} onChanged={load} />
              <RedteamPanel data={redteam} isAdmin={isAdmin} onChanged={load} />
            </div>
          </section>

          {/* ── 4b. Mission Guardrails ────────────────────────────────── */}
          <section>
            <h2 className="font-heading text-lg font-bold text-ink flex items-center gap-2">
              <ShieldCheck className="w-5 h-5" style={{ color: COPPER }} /> Mission Guardrails — what revenue can never buy
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-3">
              {[
                { emoji: "👑", title: "Owner-first — the founder is the ultimate beneficiary", desc: "The owner's capital, risk, and vision are secured before any distribution. Revenue covers infrastructure, then profit belongs to the business entity. Until the owner is whole, there is no profit unless the owner says there is." },
                { emoji: "📈", title: "Performance-linked labor — no fixed drains", desc: "Human roles earn commissions on closed business and distributions from net profit — payable only when the office is profitable, at the owner's direction. Never a fixed out-of-pocket liability." },
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
              AI jobs create revenue (<b>value</b>). Human roles earn <b>performance-linked pay</b> — commissions on
              closed business and distributions from net profit, at the owner's direction. Nothing is auto-drained.
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
                          {isHuman && j.pay_type && (
                            <div className="text-[9px] font-bold uppercase tracking-widest" style={{ color: "#b3934a" }}>
                              {j.pay_type === "commission" ? `${j.commission_pct || 0}% commission` : j.pay_type} · from profit
                            </div>
                          )}
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
                <span>Net profit available: <span style={{ color: GREEN }}>{fmt(jobs?.net_profit_available_cents)}</span></span>
                <span>Total hours: <span style={{ color: GREEN }}>{jobs?.total_hours}</span></span>
              </div>
              <div className="px-4 py-2 text-[10px] text-ink/40" style={{ background: "#fbf8f0" }}>
                {jobs?.pay_note}
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
  const [pay, setPay] = useState("75");
  const [payType, setPayType] = useState("commission");
  const [commission, setCommission] = useState("5");
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
        pay_type: workerType === "human" ? payType : "fixed",
        commission_pct: workerType === "human" && payType === "commission" ? (parseFloat(commission) || 0) : 0,
      });
      toast.success(workerType === "human" ? "Performance-linked human role opened." : "AI job opened — its revenue builds the business.");
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
        <>
          <select value={payType} onChange={(e) => setPayType(e.target.value)}
            className="px-3 py-2 rounded-lg border text-sm font-bold" style={{ borderColor: "#ddd3bf" }}>
            <option value="commission">Commission</option>
            <option value="distribution">Distribution</option>
            <option value="fixed">Fixed (owner-authorized)</option>
          </select>
          {payType === "commission" && (
            <input value={commission} onChange={(e) => setCommission(e.target.value)} type="number" min="0" max="100" step="1"
              placeholder="% of closed business" className="w-28 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: COPPER }} />
          )}
          <input value={pay} onChange={(e) => setPay(e.target.value)} type="number" min="0" step="5"
            placeholder="Milestone $" className="w-28 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: COPPER }} />
        </>
      )}
      <p className="w-full text-[10px] text-ink/40">
        {workerType === "human"
          ? "Performance-linked: payable only when net profit covers it, at the owner's direction."
          : "AI work creates value that builds the business — revenue covers infra, then profit goes to the owner."}
      </p>
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

/* ── Workforce Arbitrage Exchange (A2A) ───────────────────────────────────── */
function ExchangeBoard({ data, isAdmin, onChanged }) {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [reward, setReward] = useState("50");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!title || !desc) { toast.error("Name the task and describe the work."); return; }
    setBusy(true);
    try {
      await api.post("/abo/exchange/contracts", {
        title,
        description: desc,
        reward_cents: Math.round((parseFloat(reward) || 0) * 100),
      });
      toast.success("Contract posted to the exchange.");
      setTitle(""); setDesc("");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not post the contract.");
    } finally {
      setBusy(false);
    }
  };

  const complete = async (id) => {
    try {
      await api.post(`/abo/exchange/contracts/${id}/complete`);
      toast.success("Contract settled — clearinghouse fee booked.");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not settle the contract.");
    }
  };

  const stats = data?.stats;
  return (
    <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
      <div className="flex items-center justify-between">
        <h3 className="font-heading font-bold text-ink text-sm">🔄 Workforce Exchange</h3>
        <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(232,165,30,0.15)", color: "#8a6400" }}>
          {stats?.completed || 0}/{stats?.contracts || 0} settled · {fmt(stats?.fees_cents)} fees
        </span>
      </div>
      <form onSubmit={submit} className="mt-3 space-y-2">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Agent task — e.g. 'Audit this repo's dependencies'"
          className="w-full px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
        <textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Describe the deliverable an agent must produce…"
          rows={2} className="w-full px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
        <div className="flex gap-2">
          <input value={reward} onChange={(e) => setReward(e.target.value)} type="number" min="1" step="5"
            placeholder="Reward ($)" className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
          <button type="submit" disabled={busy} className="px-4 py-2 rounded-lg text-xs font-black text-white disabled:opacity-50"
            style={{ background: GREEN }}>
            {busy ? "Posting…" : "Post contract"}
          </button>
        </div>
      </form>
      <div className="mt-3 space-y-2 max-h-56 overflow-y-auto pr-1">
        {(data?.contracts || []).map((c) => (
          <div key={c.id} className="rounded-lg border p-3" style={{ borderColor: "#eee7d8" }}>
            <div className="flex items-center justify-between gap-2">
              <div className="font-bold text-ink text-xs">{c.title}</div>
              <span className="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded"
                style={{ background: c.status === "completed" ? "rgba(45,106,79,0.12)" : "rgba(232,165,30,0.15)", color: c.status === "completed" ? GREEN : "#8a6400" }}>
                {c.status}
              </span>
            </div>
            <p className="text-[11px] text-ink/60 mt-1 leading-snug">{c.description}</p>
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="font-black" style={{ color: GREEN }}>{fmt(c.reward_cents)}</span>
              <span className="text-ink/50">Fee: <b>{c.fee_pct}%</b> = {fmt(c.fee_cents)}</span>
              {isAdmin && c.status === "open" && (
                <button onClick={() => complete(c.id)} className="px-2 py-1 rounded text-[10px] font-black text-white" style={{ background: COPPER }}>
                  Settle →
                </button>
              )}
            </div>
          </div>
        ))}
        {!(data?.contracts || []).length && (
          <p className="text-xs text-ink/40 text-center py-4">No contracts yet — post the first agent task.</p>
        )}
      </div>
    </div>
  );
}

/* ── Shadow IT / Red-Teaming Bureau ───────────────────────────────────────── */
function RedteamPanel({ data, isAdmin, onChanged }) {
  const [target, setTarget] = useState("");
  const [url, setUrl] = useState("");
  const [scope, setScope] = useState("");
  const [tier, setTier] = useState("oneshot");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!target || !scope) { toast.error("Name the target and describe the scope."); return; }
    setBusy(true);
    try {
      await api.post("/abo/redteam/engagements", {
        target_name: target,
        target_url: url || null,
        scope_note: scope,
        tier,
      });
      toast.success("Red-team engagement started — agents are scanning.");
      setTarget(""); setUrl(""); setScope("");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start the engagement.");
    } finally {
      setBusy(false);
    }
  };

  const approve = async (id) => {
    try {
      await api.post(`/abo/redteam/engagements/${id}/approve`);
      toast.success("Patches approved by human oversight — revenue booked.");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not approve.");
    }
  };

  const close = async (id) => {
    try {
      await api.post(`/abo/redteam/engagements/${id}/close`);
      toast.success("Engagement closed.");
      onChanged();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not close.");
    }
  };

  const stats = data?.stats;
  return (
    <div className="card-flat rounded-2xl p-5 border" style={{ background: "#fff" }}>
      <div className="flex items-center justify-between">
        <h3 className="font-heading font-bold text-ink text-sm">🛡️ Red-Teaming Bureau</h3>
        <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded" style={{ background: "rgba(192,87,45,0.12)", color: COPPER }}>
          {stats?.active || 0} active · {fmt(stats?.contracted_cents)} contracted
        </span>
      </div>
      <form onSubmit={submit} className="mt-3 space-y-2">
        <div className="flex gap-2">
          <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="Client target / platform name"
            className="flex-1 px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
          <select value={tier} onChange={(e) => setTier(e.target.value)}
            className="px-3 py-2 rounded-lg border text-sm font-bold" style={{ borderColor: "#ddd3bf" }}>
            <option value="oneshot">$495 scan</option>
            <option value="retainer">$799/mo retainer</option>
          </select>
        </div>
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Target URL (optional)"
          className="w-full px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
        <textarea value={scope} onChange={(e) => setScope(e.target.value)} placeholder="Scope — what should the adversarial agents probe?"
          rows={2} className="w-full px-3 py-2 rounded-lg border text-sm" style={{ borderColor: "#ddd3bf" }} />
        <button type="submit" disabled={busy} className="w-full px-4 py-2 rounded-lg text-xs font-black text-white disabled:opacity-50"
          style={{ background: COPPER }}>
          {busy ? "Starting scan…" : "Start red-team engagement"}
        </button>
      </form>
      <div className="mt-3 space-y-2 max-h-56 overflow-y-auto pr-1">
        {(data?.engagements || []).map((e) => (
          <div key={e.id} className="rounded-lg border p-3" style={{ borderColor: "#eee7d8" }}>
            <div className="flex items-center justify-between gap-2">
              <div className="font-bold text-ink text-xs">{e.target_name}</div>
              <span className="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded"
                style={{ background: e.status === "scanning" ? "rgba(232,165,30,0.15)" : e.status === "patches_approved" ? "rgba(45,106,79,0.12)" : "rgba(192,87,45,0.1)", color: e.status === "scanning" ? "#8a6400" : e.status === "patches_approved" ? GREEN : COPPER }}>
                {e.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-[11px] text-ink/60 mt-1 leading-snug">{e.scope_note}</p>
            <div className="flex items-center justify-between mt-2 text-[11px]">
              <span className="text-ink/50">{(e.findings || []).length} findings · {(e.patches || []).length} patches ready</span>
              <span className="font-black" style={{ color: GREEN }}>{fmt(e.price_cents)}</span>
            </div>
            {isAdmin && e.status === "scanning" && (
              <button onClick={() => approve(e.id)} className="mt-2 w-full px-2 py-1.5 rounded text-[10px] font-black text-white" style={{ background: GREEN }}>
                Human Merge/Approve → ship patches & book revenue
              </button>
            )}
            {isAdmin && e.status === "patches_approved" && (
              <button onClick={() => close(e.id)} className="mt-2 w-full px-2 py-1.5 rounded text-[10px] font-black border" style={{ borderColor: "#e5c9c4", color: "#B23A2E" }}>
                Mark delivered / close
              </button>
            )}
          </div>
        ))}
        {!(data?.engagements || []).length && (
          <p className="text-xs text-ink/40 text-center py-4">No engagements yet — run the first scan.</p>
        )}
      </div>
    </div>
  );
}
