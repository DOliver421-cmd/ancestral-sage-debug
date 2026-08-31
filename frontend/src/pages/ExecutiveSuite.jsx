/**
 * ExecutiveSuite.jsx — THE unified executive workflow dashboard.
 *
 * One page. One pipeline. Every stage shares context. Nothing is isolated.
 *
 * This is the command center for the executive team:
 *   Intake → Assign → Execute → Review → Operate → Deliver
 *
 * Each project flows through all 6 stages. Context passes forward at every
 * transition. The executive (you) sees the whole pipeline at a glance and
 * can drill into any project, approve deliverables, or open the exec tools
 * (Arena, Jamil, Source Protocol, Business Office, Ops) within context.
 *
 * ENFORCEMENT: admin+ roles only (BoundedAdmin wraps this route).
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import PageBack from "../components/PageBack";
import {
  Target, Users, Zap, ShieldCheck, BarChart3, CheckCircle2,
  Plus, ChevronRight, ChevronDown, ChevronUp, ArrowRight,
  RefreshCw, Clock, AlertTriangle, Crown, FileText, Send,
  ExternalLink, MessageSquare, Star, Eye,
} from "lucide-react";

const GREEN = "#1B4332";
const GOLD = "#E8A51E";
const COPPER = "#C0572D";
const BONE = "#FDFBF5";
const INK = "#1a1a1a";

const STAGES = ["intake", "assign", "execute", "review", "operate", "deliver"];

const STAGE_META = {
  intake:  { label: "Intake",    icon: "🎯", color: "#6366f1", desc: "Brief & project creation" },
  assign:  { label: "Assign",    icon: "👥", color: "#8b5cf6", desc: "Jamil coordinates, assigns personas" },
  execute: { label: "Execute",   icon: "⚡", color: "#f59e0b", desc: "Personas produce deliverables" },
  review:  { label: "Review",    icon: "🛡️", color: "#10b981", desc: "Source Protocol + Sage approval" },
  operate: { label: "Operate",   icon: "📊", color: "#3b82f6", desc: "Business Office + Ops tracking" },
  deliver: { label: "Deliver",   icon: "✅", color: "#22c55e", desc: "Final output & archive" },
};

const PRIORITY_COLORS = {
  low: { bg: "#f0fdf4", border: "#86efac", text: "#166534" },
  normal: { bg: "#eff6ff", border: "#93c5fd", text: "#1e40af" },
  high: { bg: "#fef3c7", border: "#fcd34d", text: "#92400e" },
  urgent: { bg: "#fef2f2", border: "#fca5a5", text: "#991b1b" },
};

const STATUS_LABELS = {
  active: { label: "Active", color: GREEN },
  paused: { label: "Paused", color: "#6b7280" },
  completed: { label: "Completed", color: "#22c55e" },
  archived: { label: "Archived", color: "#9ca3af" },
};

function ago(iso) {
  if (!iso) return "";
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

// ── Pipeline visualization ─────────────────────────────────────────────────

function PipelineBar({ pipeline, onSelectStage }) {
  if (!pipeline?.stages) return null;
  return (
    <div className="flex gap-1 mb-6 overflow-x-auto pb-2">
      {STAGES.map((stage) => {
        const meta = STAGE_META[stage];
        const projects = pipeline.stages[stage]?.projects || [];
        const active = projects.length;
        return (
          <button
            key={stage}
            onClick={() => onSelectStage(stage)}
            className="flex-1 min-w-[100px] rounded-xl px-3 py-3 text-center transition-all hover:scale-[1.02]"
            style={{
              background: active > 0 ? meta.color : "rgba(0,0,0,0.04)",
              color: active > 0 ? "#fff" : "#666",
            }}
          >
            <div className="text-lg">{meta.icon}</div>
            <div className="text-[11px] font-bold uppercase tracking-wider mt-1">{meta.label}</div>
            <div className="text-xl font-black mt-0.5">{active}</div>
          </button>
        );
      })}
    </div>
  );
}

// ── Project card ────────────────────────────────────────────────────────────

function ProjectCard({ project, onSelect, onAdvance }) {
  const stage = STAGE_META[project.current_stage] || STAGE_META.intake;
  const priority = PRIORITY_COLORS[project.priority] || PRIORITY_COLORS.normal;
  const pending = project.deliverables?.filter(d => d.approval_status === "pending")?.length || 0;

  return (
    <div
      className="rounded-xl border p-4 mb-3 cursor-pointer transition-all hover:shadow-md hover:border-opacity-50"
      style={{ borderColor: stage.color + "40", background: "#fff" }}
      onClick={() => onSelect(project)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-base">{stage.icon}</span>
            <h3 className="font-heading text-sm font-bold text-ink truncate">{project.title}</h3>
          </div>
          <p className="text-xs text-ink/50 line-clamp-2 mb-2">{project.brief}</p>
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
              style={{ background: stage.color + "20", color: stage.color }}
            >
              {stage.label}
            </span>
            <span
              className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full"
              style={{ background: priority.bg, color: priority.text, border: `1px solid ${priority.border}` }}
            >
              {project.priority}
            </span>
            {pending > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                {pending} pending review
              </span>
            )}
            <span className="text-[10px] text-ink/40">{ago(project.updated_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {project.assignees?.length > 0 && (
            <div className="flex -space-x-1">
              {project.assignees.slice(0, 3).map((a, i) => (
                <div
                  key={i}
                  className="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-bold"
                  style={{ background: stage.color, color: "#fff" }}
                  title={a}
                >
                  {a.charAt(0).toUpperCase()}
                </div>
              ))}
            </div>
          )}
          <ChevronRight className="w-4 h-4 text-ink/30" />
        </div>
      </div>
    </div>
  );
}

// ── Working exec tools panel ───────────────────────────────────────────────

function ExecToolsPanel({ project }) {
  const [toolTab, setToolTab] = useState("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState("");
  const [searching, setSearching] = useState(false);
  const [emailTo, setEmailTo] = useState("executive");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [emailSending, setEmailSending] = useState(false);
  const [kbQuery, setKbQuery] = useState("");
  const [kbResults, setKbResults] = useState("");
  const [kbSearching, setKbSearching] = useState(false);
  const [healthResult, setHealthResult] = useState("");
  const [healthLoading, setHealthLoading] = useState(false);

  const doWebSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchResults("");
    try {
      const res = await api.post("/exec/tools/web-search", { query: searchQuery, num_results: 6 });
      setSearchResults(res.data?.result || "No results");
    } catch (e) {
      setSearchResults("Error: " + (e?.response?.data?.detail || e.message));
    } finally {
      setSearching(false);
    }
  };

  const doSendEmail = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) {
      toast.error("Subject and body are required");
      return;
    }
    setEmailSending(true);
    try {
      const res = await api.post("/exec/tools/send-email", {
        to: emailTo || "executive",
        subject: emailSubject,
        body: emailBody,
      });
      toast.success(res.data?.result || "Email sent");
      setEmailSubject("");
      setEmailBody("");
    } catch (e) {
      toast.error("Failed: " + (e?.response?.data?.detail || e.message));
    } finally {
      setEmailSending(false);
    }
  };

  const doKBSearch = async () => {
    if (!kbQuery.trim()) return;
    setKbSearching(true);
    setKbResults("");
    try {
      const res = await api.post("/exec/tools/knowledge-search", { query: kbQuery });
      const items = res.data?.result || [];
      if (Array.isArray(items) && items.length > 0) {
        setKbResults(items.map((k, i) => `${i + 1}. **${k.title || k.content?.slice(0, 60) || 'Untitled'}**\n${k.content?.slice(0, 200) || ''}`).join("\n\n"));
      } else {
        setKbResults(typeof items === "string" ? items : "No knowledge found for this query.");
      }
    } catch (e) {
      setKbResults("Error: " + (e?.response?.data?.detail || e.message));
    } finally {
      setKbSearching(false);
    }
  };

  const doHealthCheck = async () => {
    setHealthLoading(true);
    setHealthResult("");
    try {
      const res = await api.get("/exec/tools/system-health");
      setHealthResult(res.data?.result || "No health data");
    } catch (e) {
      setHealthResult("Error: " + (e?.response?.data?.detail || e.message));
    } finally {
      setHealthLoading(false);
    }
  };

  const tools = [
    { id: "search", label: "Web Search", icon: "🔍" },
    { id: "email", label: "Send Email", icon: "📧" },
    { id: "kb", label: "Knowledge Search", icon: "📚" },
    { id: "health", label: "System Health", icon: "💊" },
    { id: "links", label: "App Shortcuts", icon: "🔗" },
  ];

  return (
    <div>
      <div className="flex gap-1 mb-4 overflow-x-auto">
        {tools.map((t) => (
          <button
            key={t.id}
            onClick={() => setToolTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg whitespace-nowrap transition-all ${
              toolTab === t.id
                ? "bg-amber-600 text-white"
                : "bg-ink/[0.04] text-ink/50 hover:bg-ink/[0.08]"
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Web Search */}
      {toolTab === "search" && (
        <div>
          <div className="flex gap-2 mb-3">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && doWebSearch()}
              placeholder="Search the live web... (DuckDuckGo + Wikipedia — FREE)"
              className="flex-1 text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
            />
            <button
              onClick={doWebSearch}
              disabled={searching}
              className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold hover:bg-amber-700 disabled:opacity-50"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </div>
          {searchResults && (
            <div className="p-3 rounded-lg bg-ink/[0.02] border border-ink/5 text-xs text-ink/80 whitespace-pre-wrap max-h-60 overflow-y-auto">
              {searchResults}
            </div>
          )}
        </div>
      )}

      {/* Send Email */}
      {toolTab === "email" && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-ink/40 w-12 pt-2">To:</label>
            <input
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder="'executive' for D. Oliver, or email address"
              className="flex-1 text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
            />
          </div>
          <div className="flex gap-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-ink/40 w-12 pt-2">Subject:</label>
            <input
              value={emailSubject}
              onChange={(e) => setEmailSubject(e.target.value)}
              placeholder="Subject line"
              className="flex-1 text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
            />
          </div>
          <div>
            <textarea
              value={emailBody}
              onChange={(e) => setEmailBody(e.target.value)}
              rows={5}
              placeholder="Email body (markdown ok)"
              className="w-full text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
            />
          </div>
          <button
            onClick={doSendEmail}
            disabled={emailSending}
            className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold hover:bg-amber-700 disabled:opacity-50"
          >
            {emailSending ? "Sending..." : "Send Email"}
          </button>
        </div>
      )}

      {/* Knowledge Search */}
      {toolTab === "kb" && (
        <div>
          <div className="flex gap-2 mb-3">
            <input
              value={kbQuery}
              onChange={(e) => setKbQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && doKBSearch()}
              placeholder="Search institutional knowledge... (FREE, no AI cost)"
              className="flex-1 text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
            />
            <button
              onClick={doKBSearch}
              disabled={kbSearching}
              className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold hover:bg-amber-700 disabled:opacity-50"
            >
              {kbSearching ? "Searching..." : "Search"}
            </button>
          </div>
          {kbResults && (
            <div className="p-3 rounded-lg bg-ink/[0.02] border border-ink/5 text-xs text-ink/80 whitespace-pre-wrap max-h-60 overflow-y-auto">
              {kbResults}
            </div>
          )}
        </div>
      )}

      {/* System Health */}
      {toolTab === "health" && (
        <div>
          <button
            onClick={doHealthCheck}
            disabled={healthLoading}
            className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold hover:bg-amber-700 disabled:opacity-50 mb-3"
          >
            {healthLoading ? "Checking..." : "Check System Health"}
          </button>
          {healthResult && (
            <div className="p-3 rounded-lg bg-ink/[0.02] border border-ink/5 text-xs text-ink/80 whitespace-pre-wrap max-h-60 overflow-y-auto">
              {healthResult}
            </div>
          )}
        </div>
      )}

      {/* App Shortcuts */}
      {toolTab === "links" && (
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "Arena — Competitive Analysis", icon: "⚔️", route: "/arena" },
            { label: "Jamil — Team Coordination", icon: "🤖", route: "/jamil" },
            { label: "Source Protocol", icon: "🛡️", route: "/business-office" },
            { label: "Business Office — Revenue", icon: "📊", route: "/business-office" },
            { label: "M.O.R.E. Ops", icon: "⚙️", route: "/more/ops" },
            { label: "Studio — Content Creation", icon: "🎨", route: "/studio" },
            { label: "Ghost Producer", icon: "✍️", route: "/ghost-producer" },
            { label: "Social Blast", icon: "📢", route: "/social/publish" },
            { label: "Legal Tools", icon: "⚖️", route: "/more/litigation" },
          ].map((tool) => (
            <Link
              key={tool.label}
              to={tool.route}
              className="flex items-center gap-2 p-3 rounded-lg border border-ink/5 hover:border-amber-300 hover:bg-amber-50 transition-all group"
            >
              <span className="text-base">{tool.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-ink truncate">{tool.label}</div>
              </div>
              <ExternalLink className="w-3 h-3 text-ink/20 group-hover:text-amber-600 shrink-0" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Project detail panel ────────────────────────────────────────────────────

function ProjectDetail({ project, onAdvance, onApprove, onClose, onRefresh }) {
  const [tab, setTab] = useState("context");
  const [commentText, setCommentText] = useState("");
  const [comments, setComments] = useState([]);
  const [advanceNotes, setAdvanceNotes] = useState("");
  const [showAdvance, setShowAdvance] = useState(false);

  const stage = STAGE_META[project.current_stage] || STAGE_META.intake;
  const currentIdx = STAGES.indexOf(project.current_stage);

  const loadComments = useCallback(async () => {
    try {
      const res = await api.get(`/executive/projects/${project.id}/comments`);
      setComments(res.data || []);
    } catch {}
  }, [project.id]);

  useEffect(() => { loadComments(); }, [loadComments]);

  const submitComment = async () => {
    if (!commentText.trim()) return;
    try {
      await api.post(`/executive/projects/${project.id}/comments`, { text: commentText });
      setCommentText("");
      loadComments();
      toast.success("Comment added");
    } catch (e) {
      toast.error("Failed to add comment");
    }
  };

  const handleAdvance = async (targetStage) => {
    try {
      await api.post(`/executive/projects/${project.id}/advance`, {
        target_stage: targetStage || undefined,
        notes: advanceNotes,
      });
      toast.success(`Advanced to ${STAGE_META[targetStage || STAGES[currentIdx + 1]]?.label}`);
      setShowAdvance(false);
      setAdvanceNotes("");
      onRefresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to advance");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-12 px-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl mb-12">
        {/* Header */}
        <div className="p-6 border-b" style={{ borderColor: stage.color + "30" }}>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">{stage.icon}</span>
                <h2 className="font-heading text-lg font-bold text-ink">{project.title}</h2>
              </div>
              <p className="text-sm text-ink/60 mt-1">{project.brief}</p>
              <div className="flex gap-2 mt-3">
                <span className="text-[11px] font-bold uppercase px-2 py-0.5 rounded-full"
                  style={{ background: stage.color + "20", color: stage.color }}>
                  {stage.label}
                </span>
                <span className="text-[11px] font-bold uppercase px-2 py-0.5 rounded-full"
                  style={{ background: STATUS_LABELS[project.status]?.color + "20", color: STATUS_LABELS[project.status]?.color }}>
                  {STATUS_LABELS[project.status]?.label || project.status}
                </span>
                {project.deliverables?.length > 0 && (
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                    {project.deliverables.length} deliverable{project.deliverables.length > 1 ? "s" : ""}
                  </span>
                )}
              </div>
            </div>
            <button onClick={onClose} className="text-ink/40 hover:text-ink text-xl leading-none p-1">✕</button>
          </div>

          {/* Pipeline steps */}
          <div className="flex gap-1 mt-4">
            {STAGES.map((s, i) => {
              const sm = STAGE_META[s];
              const isCurrent = s === project.current_stage;
              const isPast = i < currentIdx;
              return (
                <div key={s} className="flex-1 text-center">
                  <div
                    className="h-1.5 rounded-full mb-1 transition-all"
                    style={{
                      background: isCurrent ? sm.color : isPast ? sm.color + "60" : "#e5e7eb",
                    }}
                  />
                  <div className="text-[9px] font-bold" style={{ color: isCurrent ? sm.color : isPast ? "#666" : "#ccc" }}>
                    {sm.label}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6">
          {[
            { id: "context", label: "Context", icon: <FileText className="w-3.5 h-3.5" /> },
            { id: "deliverables", label: "Deliverables", icon: <Star className="w-3.5 h-3.5" /> },
            { id: "tools", label: "Exec Tools", icon: <Zap className="w-3.5 h-3.5" /> },
            { id: "comments", label: "Discussion", icon: <MessageSquare className="w-3.5 h-3.5" /> },
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors ${
                tab === t.id ? "border-amber-600 text-amber-700" : "border-transparent text-ink/40 hover:text-ink/60"
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-6 max-h-[50vh] overflow-y-auto">
          {tab === "context" && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-ink/40 mb-3">Shared Context (flows forward)</h4>
              {Object.entries(project.context || {}).filter(([k]) => !k.startsWith("_")).map(([key, val]) => (
                <div key={key} className="mb-3 p-3 rounded-lg bg-ink/[0.02] border border-ink/5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-ink/40 mb-1">
                    {key.replace(/_/g, " ")}
                  </div>
                  <div className="text-sm text-ink/80 whitespace-pre-wrap">
                    {typeof val === "object" ? JSON.stringify(val, null, 2) : String(val)}
                  </div>
                </div>
              ))}
              {Object.keys(project.context || {}).filter(k => !k.startsWith("_")).length === 0 && (
                <p className="text-sm text-ink/40 italic">No context yet. Advance the stage to pass data forward.</p>
              )}
            </div>
          )}

          {tab === "deliverables" && (
            <div>
              {project.deliverables?.length > 0 ? project.deliverables.map((d, i) => (
                <div key={i} className="mb-3 p-3 rounded-lg border border-ink/5">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-bold text-ink">{d.title}</span>
                      <span className="text-[10px] ml-2 text-ink/40">by {d.persona}</span>
                    </div>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                      d.approval_status === "approved" ? "bg-green-100 text-green-700" :
                      d.approval_status === "rejected" ? "bg-red-100 text-red-700" :
                      d.approval_status === "revision_requested" ? "bg-amber-100 text-amber-700" :
                      "bg-gray-100 text-gray-700"
                    }`}>
                      {d.approval_status}
                    </span>
                  </div>
                  {d.content && <p className="text-xs text-ink/60 mt-2 whitespace-pre-wrap">{d.content}</p>}
                  {d.approval_status === "pending" && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => onApprove(project.id, "approve")}
                        className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => onApprove(project.id, "request_revision")}
                        className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200"
                      >
                        Request Revision
                      </button>
                    </div>
                  )}
                </div>
              )) : (
                <p className="text-sm text-ink/40 italic">No deliverables submitted yet.</p>
              )}
            </div>
          )}

          {tab === "tools" && (
            <ExecToolsPanel project={project} />
          )}

          {tab === "comments" && (
            <div>
              <div className="space-y-2 mb-4">
                {comments.map((c, i) => (
                  <div key={i} className="p-2 rounded-lg bg-ink/[0.02] text-sm">
                    <span className="font-bold text-ink text-xs">{c.user_name}</span>
                    <span className="text-[10px] text-ink/40 ml-2">{ago(c.created_at)}</span>
                    {c.persona && <span className="text-[10px] text-amber-600 ml-2">as {c.persona}</span>}
                    <p className="text-ink/80 mt-1">{c.text}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submitComment()}
                  placeholder="Add a note..."
                  className="flex-1 text-sm border border-ink/10 rounded-lg px-3 py-2 focus:outline-none focus:border-amber-400"
                />
                <button
                  onClick={submitComment}
                  className="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-bold hover:bg-amber-700"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="p-4 border-t border-ink/5 flex items-center justify-between">
          <div className="flex gap-2">
            {currentIdx < STAGES.length - 1 && (
              <>
                {showAdvance ? (
                  <div className="flex items-center gap-2">
                    <input
                      value={advanceNotes}
                      onChange={(e) => setAdvanceNotes(e.target.value)}
                      placeholder="Stage notes..."
                      className="text-xs border border-ink/10 rounded-lg px-3 py-1.5 w-48 focus:outline-none focus:border-amber-400"
                    />
                    <button
                      onClick={() => handleAdvance()}
                      className="text-xs font-bold px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700"
                    >
                      Advance → {STAGE_META[STAGES[currentIdx + 1]]?.label}
                    </button>
                    <button onClick={() => setShowAdvance(false)} className="text-xs text-ink/40 hover:text-ink">
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowAdvance(true)}
                    className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg bg-green-50 text-green-700 hover:bg-green-100"
                  >
                    Advance Stage <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── New project form ────────────────────────────────────────────────────────

function NewProjectForm({ onSubmit, onClose }) {
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [type, setType] = useState("general");
  const [priority, setPriority] = useState("normal");

  const handleSubmit = async () => {
    if (!title.trim() || !brief.trim()) {
      toast.error("Title and brief are required");
      return;
    }
    try {
      await api.post("/executive/projects", { title, brief, project_type: type, priority });
      toast.success("Project created — starts at Intake stage");
      onSubmit();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to create project");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-12 px-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading text-base font-bold text-ink">New Executive Project</h3>
          <button onClick={onClose} className="text-ink/40 hover:text-ink">✕</button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-ink/40">Title</label>
            <input value={title} onChange={e => setTitle(e.target.value)}
              className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:border-amber-400"
              placeholder="e.g., Vonn's Saga — Full Funnel Launch" />
          </div>
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-ink/40">Brief</label>
            <textarea value={brief} onChange={e => setBrief(e.target.value)} rows={4}
              className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:border-amber-400"
              placeholder="Describe what needs to happen, who's involved, what success looks like..." />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-ink/40">Type</label>
              <select value={type} onChange={e => setType(e.target.value)}
                className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm mt-1">
                <option value="general">General</option>
                <option value="release">Release (music/content)</option>
                <option value="campaign">Campaign</option>
                <option value="content">Content Creation</option>
                <option value="course">Course</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-ink/40">Priority</label>
              <select value={priority} onChange={e => setPriority(e.target.value)}
                className="w-full border border-ink/10 rounded-lg px-3 py-2 text-sm mt-1">
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="text-sm font-bold px-4 py-2 text-ink/50 hover:text-ink">Cancel</button>
          <button onClick={handleSubmit}
            className="text-sm font-bold px-4 py-2 rounded-lg text-white hover:opacity-90"
            style={{ background: GOLD }}>
            Create Project
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Executive Suite ────────────────────────────────────────────────────

export default function ExecutiveSuite() {
  const { user } = useAuth();
  const [pipeline, setPipeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [filterStatus, setFilterStatus] = useState("active");

  const loadPipeline = useCallback(async () => {
    try {
      const res = await api.get("/executive/pipeline");
      setPipeline(res.data);
    } catch (e) {
      toast.error("Failed to load pipeline");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadPipeline(); }, [loadPipeline]);

  const handleApprove = async (projectId, action) => {
    try {
      await api.post(`/executive/projects/${projectId}/approve`, {
        action,
        notes: "",
      });
      toast.success(action === "approve" ? "Deliverable approved" : "Revision requested");
      loadPipeline();
      // Refresh selected project
      const res = await api.get(`/executive/projects/${projectId}`);
      setSelectedProject(res.data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Action failed");
    }
  };

  const projects = selectedStage
    ? pipeline?.stages?.[selectedStage]?.projects || []
    : Object.values(pipeline?.stages || {}).flatMap(s => s.projects || []);

  const summary = pipeline?.summary || {};

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 text-ink/30 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <PageBack to="/admin/command" label="Command Center" />
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl font-black text-ink">Executive Suite</h1>
          <p className="text-sm text-ink/50 mt-1">
            Unified workflow pipeline — {summary.total_active || 0} active project{summary.total_active !== 1 ? "s" : ""} · {summary.pending_approvals || 0} awaiting review
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadPipeline}
            className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg border border-ink/10 hover:bg-ink/5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-lg text-white hover:opacity-90"
            style={{ background: GOLD }}
          >
            <Plus className="w-3.5 h-3.5" /> New Project
          </button>
        </div>
      </div>

      {/* Pipeline bar */}
      <PipelineBar pipeline={pipeline} onSelectStage={(s) => setSelectedStage(selectedStage === s ? null : s)} />

      {/* Stage filter label */}
      {selectedStage && (
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-ink">
            {STAGE_META[selectedStage]?.icon} {STAGE_META[selectedStage]?.label} — {projects.length} project{projects.length !== 1 ? "s" : ""}
          </h2>
          <button onClick={() => setSelectedStage(null)} className="text-xs text-ink/40 hover:text-ink">
            Show all
          </button>
        </div>
      )}

      {/* Project list */}
      {projects.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">🎯</div>
          <h3 className="font-heading text-base font-bold text-ink mb-2">
            {selectedStage ? `No projects at ${STAGE_META[selectedStage]?.label} stage` : "No active projects"}
          </h3>
          <p className="text-sm text-ink/50 mb-4">
            {selectedStage ? "Projects will appear here when advanced to this stage." : "Create your first executive project to get started."}
          </p>
          {!selectedStage && (
            <button
              onClick={() => setShowNew(true)}
              className="text-sm font-bold px-4 py-2 rounded-lg text-white hover:opacity-90"
              style={{ background: GOLD }}
            >
              <Plus className="w-4 h-4 inline mr-1" /> Create Project
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-1">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onSelect={setSelectedProject}
            />
          ))}
        </div>
      )}

      {/* Quick links to exec tools */}
      <div className="mt-8 pt-6 border-t border-ink/5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-ink/40 mb-3">Executive Tools</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {[
            { label: "Arena", icon: "⚔️", route: "/arena", desc: "Competitive analysis" },
            { label: "Jamil", icon: "🤖", route: "/jamil", desc: "Team coordination" },
            { label: "AI Business Office", icon: "📊", route: "/business-office", desc: "Revenue & strategy" },
            { label: "M.O.R.E. Ops", icon: "⚙️", route: "/more/ops", desc: "Operations" },
            { label: "Source Protocol", icon: "🛡️", route: "/business-office", desc: "Mission alignment" },
            { label: "Command Center", icon: "👑", route: "/admin/command", desc: "Executive controls" },
            { label: "Studio", icon: "🎨", route: "/studio", desc: "Content creation" },
            { label: "Social Blast", icon: "📢", route: "/social/publish", desc: "Multi-platform publishing" },
          ].map((tool) => (
            <Link
              key={tool.label}
              to={tool.route}
              className="flex items-center gap-2 p-3 rounded-xl border border-ink/5 hover:border-amber-300 hover:bg-amber-50 transition-all group"
            >
              <span className="text-lg">{tool.icon}</span>
              <div>
                <div className="text-xs font-bold text-ink">{tool.label}</div>
                <div className="text-[10px] text-ink/40">{tool.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Modals */}
      {showNew && <NewProjectForm onSubmit={() => { setShowNew(false); loadPipeline(); }} onClose={() => setShowNew(false)} />}
      {selectedProject && (
        <ProjectDetail
          project={selectedProject}
          onApprove={handleApprove}
          onClose={() => setSelectedProject(null)}
          onRefresh={async () => {
            loadPipeline();
            const res = await api.get(`/executive/projects/${selectedProject.id}`);
            setSelectedProject(res.data);
          }}
        />
      )}
    </div>
  );
}
