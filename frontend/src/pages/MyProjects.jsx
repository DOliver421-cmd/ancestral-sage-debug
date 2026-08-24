import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Plus, Loader2, Send, Check, X, RotateCcw, MessageSquare, Sparkles,
  Archive, ChevronDown, ChevronUp,
} from "lucide-react";

const GREEN = "#1B4332";
const GOLD = "#E8A51E";
const COPPER = "#C0572D";

const STAGES = ["intake", "assign", "execute", "review", "operate", "deliver"];
const STAGE_LABEL = { intake: "Intake", assign: "Assign", execute: "Execute", review: "Review", operate: "Operate", deliver: "Deliver" };
const STAGE_ICON = { intake: "🎯", assign: "👥", execute: "⚡", review: "🛡️", operate: "📊", deliver: "✅" };

const TEAM = [
  { id: "Helper", label: "Helper", desc: "Research & answers" },
  { id: "Creative Partner", label: "Creative Partner", desc: "Concepts & writing" },
  { id: "Production", label: "Production", desc: "Content & packaging" },
  { id: "Ghost Producer", label: "Ghost Producer", desc: "Music & studio" },
  { id: "Marketing", label: "Marketing", desc: "Audience & promotion" },
  { id: "Review", label: "Review", desc: "Quality check" },
  { id: "Operations", label: "Operations", desc: "Logistics & plans" },
  { id: "Analytics", label: "Analytics", desc: "Metrics & tracking" },
];

const CATEGORIES = [
  { id: "launch", label: "Launch a project / program" },
  { id: "create", label: "Create something — a track, a book, art" },
  { id: "organize", label: "Get organized" },
  { id: "grow", label: "Grow my audience" },
  { id: "learn", label: "Build my skills" },
];

const STATUS_BADGE = {
  pending: { label: "Awaiting your review", color: GOLD, bg: "rgba(232,165,30,0.12)" },
  approved: { label: "Approved", color: "#2D6A4F", bg: "rgba(45,106,79,0.12)" },
  rejected: { label: "Rejected", color: "#B23A2E", bg: "rgba(178,58,46,0.12)" },
  revision_requested: { label: "Revision requested", color: "#B5651D", bg: "rgba(181,101,29,0.12)" },
};

const fmtDt = (s) => {
  if (!s) return "—";
  const d = new Date(s);
  return isNaN(d) ? String(s) : d.toLocaleString();
};

function StageDots({ current }) {
  const idx = STAGES.indexOf(current);
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {STAGES.map((s, i) => (
        <div key={s} className="flex items-center gap-1.5">
          <div
            title={`${STAGE_LABEL[s]}${i === idx ? " — current" : i < idx ? " — done" : ""}`}
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs border ${
              i < idx ? "text-white" : i === idx ? "text-white" : "text-ink/35"
            }`}
            style={{
              background: i < idx ? GREEN : i === idx ? GOLD : "#f3ede2",
              borderColor: i === idx ? GOLD : i < idx ? GREEN : "rgba(0,0,0,0.1)",
            }}
          >
            {i < idx ? <Check className="w-3.5 h-3.5" /> : STAGE_ICON[s]}
          </div>
          {i < STAGES.length - 1 && (
            <div className={`h-px w-3 sm:w-5 ${i < idx ? "" : "bg-ink/10"}`} style={i < idx ? { background: GREEN } : undefined} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function MyProjects() {
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [showNew, setShowNew] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: "", brief: "", category: "launch", priority: "normal", desired_outcome: "" });

  const [run, setRun] = useState({ persona: "Production", instructions: "", open: false });
  const [running, setRunning] = useState(false);

  const [comment, setComment] = useState("");
  const [sendingComment, setSendingComment] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/my-projects");
      setProjects(data.projects || []);
      setSummary(data.summary || null);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not load your projects.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openProject = useCallback(async (p) => {
    setSelectedId(p.id);
    setDetailLoading(true);
    try {
      const { data } = await api.get(`/my-projects/${p.id}`);
      setDetail(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not open the project.");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const refreshDetail = useCallback(async (id) => {
    try {
      const { data } = await api.get(`/my-projects/${id}`);
      setDetail(data);
      return data;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not refresh the project.");
      return null;
    }
  }, []);

  const createProject = async () => {
    if (!form.title.trim() || form.brief.trim().length < 10) {
      toast.error("Give the project a title and tell the team a little more (at least 10 characters).");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post("/my-projects", form);
      toast.success("Project created — the M.O.R.E. team starts at Intake.");
      setForm({ title: "", brief: "", category: "launch", priority: "normal", desired_outcome: "" });
      setShowNew(false);
      await load();
      openProject(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not create the project.");
    } finally {
      setBusy(false);
    }
  };

  const runStage = async () => {
    if (!detail) return;
    setRunning(true);
    try {
      const { data } = await api.post(`/my-projects/${detail.id}/run-stage`, run);
      toast.success(`${run.persona} finished — review it below before it counts.`);
      setRun({ persona: "Production", instructions: "", open: false });
      await refreshDetail(detail.id);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "The run failed — nothing was saved.");
    } finally {
      setRunning(false);
    }
  };

  const decide = async (action, notes = "") => {
    if (!detail) return;
    try {
      const { data } = await api.post(`/my-projects/${detail.id}/approve`, { action, notes });
      toast.success(data.status === "approved" ? "Approved — moving on." : data.status === "rejected" ? "Rejected." : "Revision requested.");
      await refreshDetail(detail.id);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not record your decision.");
    }
  };

  const advance = async () => {
    if (!detail) return;
    try {
      await api.post(`/my-projects/${detail.id}/advance`, {});
      toast.success("Advanced — the next stage sees everything produced so far.");
      await refreshDetail(detail.id);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not advance.");
    }
  };

  const archiveProject = async () => {
    if (!detail) return;
    try {
      await api.post(`/my-projects/${detail.id}/archive`, {});
      toast.success("Project archived.");
      setSelectedId(null);
      setDetail(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not archive.");
    }
  };

  const sendComment = async () => {
    if (!detail || !comment.trim()) return;
    setSendingComment(true);
    try {
      await api.post(`/my-projects/${detail.id}/comments`, { text: comment.trim() });
      setComment("");
      await refreshDetail(detail.id);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not post the comment.");
    } finally {
      setSendingComment(false);
    }
  };

  const selected = projects.find((p) => p.id === selectedId) || null;
  const pending = (detail?.deliverables || []).filter((d) => d.approval_status === "pending");
  const runsLeft = summary?.daily_runs_left ?? "—";

  return (
    <AppShell>
      <div className="h-full overflow-y-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
          {/* Header */}
          <div className="overline text-copper mb-2">My Projects</div>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <h2 className="font-heading text-2xl sm:text-3xl font-bold text-ink">
                Have your M.O.R.E. team work on it.
              </h2>
              <p className="text-sm text-ink/55 max-w-2xl mt-2 leading-relaxed">
                Give the team a goal. They research, draft, and produce. You review, approve, or
                ask for changes — you stay the decision-maker. Nothing is published without you.
              </p>
            </div>
            <button
              onClick={() => setShowNew((v) => !v)}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-black text-white shrink-0"
              style={{ background: GREEN }}
            >
              {showNew ? <ChevronUp className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
              {showNew ? "Close" : "Start a project"}
            </button>
          </div>

          {/* Summary chips */}
          <div className="flex flex-wrap gap-2 mt-4">
            {[
              { label: "Active projects", value: summary?.active ?? "—" },
              { label: "Awaiting your review", value: summary?.pending_reviews ?? "—" },
              { label: "AI runs left today", value: `${runsLeft}/${summary?.daily_run_limit ?? 5}` },
            ].map((c) => (
              <div key={c.label} className="card-flat rounded-xl px-4 py-2 border flex items-baseline gap-2" style={{ background: "#fff" }}>
                <span className="font-heading font-black text-ink text-lg">{c.value}</span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-ink/45">{c.label}</span>
              </div>
            ))}
          </div>

          {/* New project form */}
          {showNew && (
            <div className="card-flat rounded-2xl border p-5 mt-5" style={{ background: "#fff", borderColor: "rgba(232,165,30,0.35)" }}>
              <div className="font-heading font-bold text-ink mb-3">What do you want done?</div>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Project title — e.g. Launch my podcast"
                className="w-full px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper mb-3"
              />
              <textarea
                value={form.brief}
                onChange={(e) => setForm({ ...form, brief: e.target.value })}
                placeholder="The goal — what are you trying to accomplish? What does done look like?"
                rows={3}
                className="w-full px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y mb-3"
              />
              <input
                value={form.desired_outcome}
                onChange={(e) => setForm({ ...form, desired_outcome: e.target.value })}
                placeholder="What done looks like (optional) — e.g. 5 episodes ready to publish"
                className="w-full px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper mb-3"
              />
              <div className="grid sm:grid-cols-2 gap-3 mb-3">
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper"
                >
                  {CATEGORIES.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
                </select>
                <select
                  value={form.priority}
                  onChange={(e) => setForm({ ...form, priority: e.target.value })}
                  className="px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper"
                >
                  {["low", "normal", "high"].map((t) => <option key={t} value={t}>{t[0].toUpperCase() + t.slice(1)} priority</option>)}
                </select>
              </div>
              <div className="flex gap-2">
                <button onClick={createProject} disabled={busy}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40"
                  style={{ background: GREEN }}>
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Start project
                </button>
                <button onClick={() => setShowNew(false)} className="px-4 py-2 rounded-lg text-sm font-bold text-ink/50 hover:text-ink">Cancel</button>
              </div>
            </div>
          )}

          {/* Body */}
          {loading ? (
            <div className="py-16 text-center text-ink/50 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading your projects…
            </div>
          ) : projects.length === 0 && !showNew ? (
            <div className="card-flat rounded-2xl border p-10 text-center mt-5" style={{ background: "#fff" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🗂️</div>
              <div className="font-heading font-bold text-lg text-ink">Nothing on the team's desk yet</div>
              <p className="text-sm text-ink/55 max-w-md mx-auto mt-2">
                Start with a goal — launch something, create something, get organized — and the
                M.O.R.E. team will bring you work to review, not promises.
              </p>
              <button onClick={() => setShowNew(true)}
                className="mt-5 inline-flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-black text-white"
                style={{ background: GREEN }}>
                <Plus className="w-4 h-4" /> Start your first project
              </button>
            </div>
          ) : (
            <div className="grid lg:grid-cols-5 gap-5 mt-5">
              {/* Project list */}
              <div className="lg:col-span-2 space-y-2">
                {projects.map((p) => (
                  <button key={p.id} onClick={() => openProject(p)}
                    className={`w-full text-left card-flat rounded-xl p-4 border transition-all ${selectedId === p.id ? "border-copper" : "hover:border-copper/40"}`}
                    style={{ background: "#fff" }}>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-bold text-ink text-sm">{p.title}</span>
                      <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                        style={{ background: "rgba(232,165,30,0.12)", color: COPPER }}>
                        {STAGE_LABEL[p.current_stage] || p.current_stage}
                      </span>
                    </div>
                    <div className="text-xs text-ink/50 mt-1 line-clamp-2">{p.brief}</div>
                    <div className="flex items-center gap-2 mt-2 text-[10px] font-black uppercase tracking-widest text-ink/40">
                      <span>{(p.deliverables || []).length} items</span>
                      <span className="ml-auto">{fmtDt(p.updated_at)}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Detail */}
              <div className="lg:col-span-3 space-y-4">
                {!selected ? (
                  <div className="card-flat rounded-2xl border p-8 text-center text-sm text-ink/45" style={{ background: "#fff" }}>
                    Select a project to open its workspace.
                  </div>
                ) : detailLoading ? (
                  <div className="py-16 text-center text-ink/50 flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Opening…
                  </div>
                ) : detail ? (
                  <>
                    {/* Project header */}
                    <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                      <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-heading font-bold text-lg text-ink">{detail.title}</span>
                            <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded text-white" style={{ background: GREEN }}>
                              {STAGE_LABEL[detail.current_stage] || detail.current_stage}
                            </span>
                          </div>
                          <p className="text-sm text-ink/60 mt-2">{detail.brief}</p>
                          {detail.desired_outcome && (
                            <p className="text-xs text-ink/45 mt-1"><b>Done looks like:</b> {detail.desired_outcome}</p>
                          )}
                        </div>
                        <button onClick={archiveProject} title="Archive this project"
                          className="p-2 rounded-lg text-ink/40 hover:text-destructive hover:bg-destructive/10 transition-colors">
                          <Archive className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="mt-4">
                        <StageDots current={detail.current_stage} />
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-4">
                        <button onClick={advance}
                          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-black uppercase tracking-widest text-white"
                          style={{ background: GREEN }}>
                          Advance stage <ChevronDown className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => setRun((r) => ({ ...r, open: !r.open }))}
                          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-black uppercase tracking-widest"
                          style={{ background: GOLD, color: "#0a0a0a" }}>
                          <Sparkles className="w-3.5 h-3.5" /> Run stage
                        </button>
                      </div>

                      {/* Run stage */}
                      {run.open && (
                        <div className="mt-4 rounded-xl p-4 border" style={{ background: "#faf7f0", borderColor: "rgba(232,165,30,0.3)" }}>
                          <div className="text-xs font-black uppercase tracking-widest mb-2" style={{ color: COPPER }}>
                            Hand the current stage to the team
                          </div>
                          <select
                            value={run.persona}
                            onChange={(e) => setRun({ ...run, persona: e.target.value })}
                            className="w-full sm:w-auto px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper mb-2"
                          >
                            {TEAM.map((t) => <option key={t.id} value={t.id}>{t.label} — {t.desc}</option>)}
                          </select>
                          <textarea
                            value={run.instructions}
                            onChange={(e) => setRun({ ...run, instructions: e.target.value })}
                            placeholder="Optional direction — e.g. keep it Southern Soul, no budget increases, plain language"
                            rows={2}
                            className="w-full px-3 py-2 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper resize-y mb-2"
                          />
                          <div className="flex items-center gap-2 flex-wrap">
                            <button onClick={runStage} disabled={running}
                              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-black text-white disabled:opacity-40"
                              style={{ background: COPPER }}>
                              {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                              {running ? "Working…" : "Run it"}
                            </button>
                            <span className="text-[10px] font-bold uppercase tracking-widest text-ink/40">
                              {runsLeft} runs left today · result lands pending for your review
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Deliverables */}
                    <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                        <div className="font-heading font-bold text-ink">Work produced</div>
                        {pending.length > 0 && (
                          <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                            style={{ background: "rgba(232,165,30,0.12)", color: COPPER }}>
                            {pending.length} awaiting your review
                          </span>
                        )}
                      </div>
                      {(detail.deliverables || []).length === 0 ? (
                        <div className="text-sm text-ink/45 text-center py-8">
                          Nothing here yet. Press <b>Run stage</b> and the team will produce the first piece of work.
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {[...(detail.deliverables || [])].reverse().map((d) => {
                            const badge = STATUS_BADGE[d.approval_status] || STATUS_BADGE.pending;
                            return (
                              <div key={d.id} className="rounded-xl border p-4" style={{ background: "#faf7f0" }}>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-heading font-bold text-ink text-sm">{d.title}</span>
                                  {d.metadata?.auto && (
                                    <span className="text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded text-white" style={{ background: GREEN }}>
                                      AI team
                                    </span>
                                  )}
                                  <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded"
                                    style={{ background: badge.bg, color: badge.color }}>
                                    {badge.label}
                                  </span>
                                  <span className="ml-auto text-[10px] text-ink/40">{fmtDt(d.submitted_at)}</span>
                                </div>
                                <div className="text-xs text-ink/55 mt-1">
                                  {STAGE_LABEL[d.stage] || d.stage} · {d.persona}
                                </div>
                                {d.content && (
                                  <pre className="mt-2 text-sm whitespace-pre-wrap font-sans text-ink/75 leading-relaxed max-h-64 overflow-y-auto">{d.content}</pre>
                                )}
                                {d.review_notes && (
                                  <div className="mt-2 text-xs rounded-lg px-3 py-2" style={{ background: "rgba(45,106,79,0.08)", color: "#1B4332" }}>
                                    <b>Your note:</b> {d.review_notes}
                                  </div>
                                )}
                                {d.approval_status === "pending" && (
                                  <div className="flex flex-wrap gap-2 mt-3">
                                    <button onClick={() => decide("approve")}
                                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest text-white"
                                      style={{ background: "#2D6A4F" }}>
                                      <Check className="w-3.5 h-3.5" /> Approve
                                    </button>
                                    <button onClick={() => decide("reject")}
                                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest text-white"
                                      style={{ background: "#B23A2E" }}>
                                      <X className="w-3.5 h-3.5" /> Reject
                                    </button>
                                    <button onClick={() => decide("request_revision")}
                                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest"
                                      style={{ background: "#B5651D", color: "#fff" }}>
                                      <RotateCcw className="w-3.5 h-3.5" /> Request changes
                                    </button>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Comments */}
                    <div className="card-flat rounded-2xl border p-5" style={{ background: "#fff" }}>
                      <div className="font-heading font-bold text-ink mb-3 flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" style={{ color: COPPER }} /> Discussion
                      </div>
                      <div className="space-y-2 max-h-56 overflow-y-auto mb-3">
                        {(detail.comments || []).length === 0 ? (
                          <div className="text-sm text-ink/45 text-center py-4">No comments yet — direct the team here.</div>
                        ) : (
                          (detail.comments || []).map((c) => (
                            <div key={c.id} className="rounded-lg px-3 py-2 text-sm" style={{ background: "#faf7f0" }}>
                              <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-ink/45">
                                <span style={{ color: c.persona ? COPPER : GREEN }}>
                                  {c.persona ? `${c.persona} (team)` : (c.user_name || "You")}
                                </span>
                                <span className="ml-auto font-normal normal-case tracking-normal">{fmtDt(c.created_at)}</span>
                              </div>
                              <div className="text-ink/75 mt-0.5">{c.text}</div>
                            </div>
                          ))
                        )}
                      </div>
                      <div className="flex gap-2">
                        <input
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") sendComment(); }}
                          placeholder="Direct the team…"
                          className="flex-1 px-3 py-2.5 bg-bone border border-ink/15 rounded-lg text-sm focus:outline-none focus:border-copper"
                        />
                        <button onClick={sendComment} disabled={sendingComment || !comment.trim()}
                          className="px-4 py-2.5 rounded-lg text-sm font-black text-white disabled:opacity-40"
                          style={{ background: GREEN }}>
                          {sendingComment ? <Loader2 className="w-4 h-4 animate-spin" /> : "Send"}
                        </button>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
