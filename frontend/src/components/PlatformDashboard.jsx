import { useState, useEffect, useRef } from "react";
import {
  Plus, X, CheckCircle2, Clock, AlertCircle, Circle,
  Music, Scale, Users, TrendingUp, BookOpen, Cpu,
  Sparkles, ChevronDown, ChevronUp, Edit3, Trash2, Save,
} from "lucide-react";
import { api } from "../lib/api";

// ── Design tokens ─────────────────────────────────────────────────────────────
const T = {
  bg:        "#fdf6f9",
  bgDeep:    "#faeef4",
  card:      "#ffffff",
  rose:      "#e879a0",
  roseSoft:  "#fce7f3",
  lavender:  "#a78bfa",
  lavSoft:   "#ede9fe",
  mauve:     "#c084fc",
  mauvesoft: "#f3e8ff",
  sage:      "#6ee7b7",
  sageSoft:  "#d1fae5",
  blush:     "#fbcfe8",
  text:      "#3d2c3e",
  muted:     "#9d7faa",
  border:    "rgba(232,121,160,0.18)",
  shadow:    "0 2px 16px rgba(232,121,160,0.07)",
};

// ── Area config ────────────────────────────────────────────────────────────────
const AREAS = [
  { id: "all",        label: "All",        icon: Sparkles,   color: T.rose,     bg: T.roseSoft },
  { id: "Music",      label: "Music",      icon: Music,      color: "#db2777",  bg: "#fce7f3" },
  { id: "Legal",      label: "Legal",      icon: Scale,      color: "#7c3aed",  bg: "#ede9fe" },
  { id: "Community",  label: "Community",  icon: Users,      color: "#0891b2",  bg: "#e0f2fe" },
  { id: "Business",   label: "Business",   icon: TrendingUp, color: "#b45309",  bg: "#fef3c7" },
  { id: "Education",  label: "Education",  icon: BookOpen,   color: "#059669",  bg: "#d1fae5" },
  { id: "Platform",   label: "Platform",   icon: Cpu,        color: T.lavender, bg: T.lavSoft },
  { id: "Personal",   label: "Personal",   icon: CheckCircle2, color: "#e879a0", bg: "#fce7f3" },
];

// ── Status config ──────────────────────────────────────────────────────────────
const STATUSES = [
  { id: "live",        label: "Live",        cls: "bg-emerald-50 text-emerald-700 border border-emerald-200" },
  { id: "in-progress", label: "In Progress", cls: "bg-amber-50 text-amber-700 border border-amber-200" },
  { id: "pending",     label: "Pending",     cls: "bg-sky-50 text-sky-700 border border-sky-200" },
  { id: "sent",        label: "Sent",        cls: "bg-violet-50 text-violet-700 border border-violet-200" },
  { id: "blocked",     label: "Blocked",     cls: "bg-rose-50 text-rose-700 border border-rose-200" },
  { id: "done",        label: "Done ✓",      cls: "bg-slate-50 text-slate-500 border border-slate-200" },
];

// ── Priority config ────────────────────────────────────────────────────────────
const PRIORITIES = [
  { id: "high",   label: "High",   dot: "bg-rose-400" },
  { id: "medium", label: "Medium", dot: "bg-amber-400" },
  { id: "low",    label: "Low",    dot: "bg-slate-300" },
];

// ── Default projects (all W.A.I. / M.O.R.E. / personal work streams) ──────────
const DEFAULT_PROJECTS = [
  // Music
  { id: "m1", area: "Music", priority: "high", status: "in-progress",
    title: "Vonn Oshun — Original × AI Track",
    note: "Record originals. Upload to CDN. Suno AI version in parallel. Player built, ready to receive files.",
    tasks: ["Record vocal tracks", "Upload to CDN / get direct MP3 URL", "Paste URLs into MoreOps track player", "Share on socials"] },
  { id: "m2", area: "Music", priority: "medium", status: "in-progress",
    title: "Ghost Producer Studio",
    note: "Interactive music engine live at /ghost-producer. Expand with real track uploads and sharing.",
    tasks: ["Add track upload to Ghost Producer page", "Connect to playlist gateway"] },
  { id: "m3", area: "Music", priority: "medium", status: "live",
    title: "Playlist Curation Gateway",
    note: "Artist submission gateway open. Artists save playlist, follow, add required song, share, then get reviewed.",
    tasks: ["Monitor submissions", "Approve / reject weekly", "Add new gateways as needed"] },

  // Legal
  { id: "l1", area: "Legal", priority: "high", status: "sent",
    title: "Notice of Dispute — Anthropic PBC",
    note: "Formal Notice of Dispute re: platform malfunction & unauthorized AI actions. Certified mail sent 6/3/26 to 548 Market St PMB 90375, San Francisco CA 94104. Awaiting response.",
    tasks: ["✅ Send certified mail", "Wait for Anthropic response (30 days)", "Follow up if no response by 7/3/26", "Document all AI behavior logs as evidence"] },
  { id: "l2", area: "Legal", priority: "medium", status: "pending",
    title: "Copyright — NAM Oshun Poetry",
    note: "Register original works. Catalog all published and unpublished poems.",
    tasks: ["Catalog all works", "File copyright registration", "Document publication dates"] },
  { id: "l3", area: "Legal", priority: "medium", status: "pending",
    title: "Trademark — W.A.I. Institute / M.O.R.E.",
    note: "Brand protection for W.A.I. Institute, M.O.R.E. Help Center, and Oliver Guardian names.",
    tasks: ["Search existing marks", "File applications", "Monitor for infringement"] },

  // Community
  { id: "c1", area: "Community", priority: "high", status: "live",
    title: "M.O.R.E. Help Center",
    note: "Skill exchange hub. Oliver Guardian protection active. Students, creators, and community members exchanging freely.",
    tasks: ["Monitor exchange requests", "Onboard new members", "Add skill categories as needed"] },
  { id: "c2", area: "Community", priority: "medium", status: "live",
    title: "Creator Profiles — NAM, Nova, Royal Black Falcon, Vonn",
    note: "Four creator profiles live. Each links socials, M.O.R.E. offerings, and platform work.",
    tasks: ["Add real social URLs", "Add portfolio pieces", "Add Vonn Oshun audio URLs when ready"] },
  { id: "c3", area: "Community", priority: "medium", status: "in-progress",
    title: "Poets Got To Eat Too — Feeder Pipeline",
    note: "Facebook community → WAI-Institute pipeline. Add one-line WAI bio to group description.",
    tasks: ["Post WAI bio in group description", "Pin WAI link in group", "Track referral signups"] },
  { id: "c4", area: "Community", priority: "low", status: "pending",
    title: "S.O.U.P. — Society of Unified Poets",
    note: "Spoken word collective. Partner org. Route interested members to WAI creator pipeline.",
    tasks: ["Connect with group admins", "Share creator profile link", "Track sign-ups"] },

  // Business
  { id: "b1", area: "Business", priority: "high", status: "in-progress",
    title: "LLM Provider Keys — Grok + Gemini",
    note: "Keys ready to paste. Go to /admin/providers, open xAI card, enter Grok key. Repeat for Gemini.",
    tasks: ["✅ Get Grok key", "Paste into /admin/providers xAI card", "✅ Get Gemini key", "Paste into Gemini card", "Test AI chat in MoreOps"] },
  { id: "b2", area: "Business", priority: "medium", status: "live",
    title: "Revenue Division Dashboard",
    note: "Revenue tracking, payment admin, and billing management live at /revenue and /admin/payments.",
    tasks: ["Review revenue weekly", "Process pending payouts", "Update pricing if needed"] },
  { id: "b3", area: "Business", priority: "medium", status: "in-progress",
    title: "Subscription Tier Rollout",
    note: "Tier enforcement middleware active. Student, Instructor, Admin, Executive tiers defined.",
    tasks: ["Test tier gating on all routes", "Set up payment processing", "Launch paid tiers publicly"] },

  // Education
  { id: "e1", area: "Education", priority: "high", status: "live",
    title: "Free Course — On How to Work with AI",
    note: "Public access enabled. No login required. Share URL: /modules/how-to-work-with-ai",
    tasks: ["✅ Deploy free field fix", "Share on social media", "Add more free lesson modules", "Track anonymous views"] },
  { id: "e2", area: "Education", priority: "medium", status: "in-progress",
    title: "WAI-Institute Course Catalog",
    note: "Community development, healing arts, and workforce training modules. Expand catalog.",
    tasks: ["Audit existing modules", "Write 2 new modules this month", "Add quiz questions", "Assign instructors"] },
  { id: "e3", area: "Education", priority: "low", status: "pending",
    title: "Electrical / Trade Skills Courses",
    note: "Circuit design, wiring, solar, safety — trade skill AI tutor at /tools/electrical-courses.html",
    tasks: ["Review existing content", "Add video walkthroughs", "Partner with trade instructors"] },

  // Platform
  { id: "p1", area: "Platform", priority: "high", status: "live",
    title: "AI Team Monitor",
    note: "Self-healing monitor runs every 5 min. Revokes bad keys, logs all actions to /team/ops.",
    tasks: ["Monitor /team/ops dashboard", "Review action log weekly", "Tune failure thresholds if needed"] },
  { id: "p2", area: "Platform", priority: "medium", status: "live",
    title: "MoreOps Interface",
    note: "Department AI routing, TTS voice, track player, file upload, and this dashboard — all live.",
    tasks: ["Test each department route", "Add more departments if needed", "Keep AI keys active"] },
  { id: "p3", area: "Platform", priority: "medium", status: "in-progress",
    title: "Platform API — LLM Chat",
    note: "Server active, DB connected. AI chat needs provider keys to work. See Business > LLM Provider Keys.",
    tasks: ["Activate provider keys", "Test chat in MoreOps", "Monitor response quality"] },

  // Personal
  { id: "pe1", area: "Personal", priority: "medium", status: "in-progress",
    title: "NAM Oshun — Poetry Collection",
    note: "Document and publish original works. Platform is the distribution channel.",
    tasks: ["Catalog unpublished poems", "Schedule open mic events", "Upload to creator profile"] },
];

const LS_KEY = "moreops_projects_v1";

function loadProjects() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_PROJECTS;
  } catch { return DEFAULT_PROJECTS; }
}

function saveProjects(p) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(p)); } catch {}
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function areaConfig(id) { return AREAS.find(a => a.id === id) || AREAS[1]; }
function statusConfig(id) { return STATUSES.find(s => s.id === id) || STATUSES[1]; }
function priorityConfig(id) { return PRIORITIES.find(p => p.id === id) || PRIORITIES[1]; }

// ── Sub-components ────────────────────────────────────────────────────────────
function AreaTab({ area, active, onClick, count }) {
  const Icon = area.icon;
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all whitespace-nowrap"
      style={active
        ? { background: area.color, color: "#fff", boxShadow: `0 2px 8px ${area.color}40` }
        : { background: T.card, color: T.muted, border: `1px solid ${T.border}` }}
    >
      <Icon size={11} />
      {area.label}
      {count != null && (
        <span className="text-xs opacity-70">({count})</span>
      )}
    </button>
  );
}

function ProjectCard({ project, onUpdate, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const [editing,  setEditing]  = useState(false);
  const [draft,    setDraft]    = useState(project);

  const area   = areaConfig(project.area);
  const status = statusConfig(project.status);
  const pri    = priorityConfig(project.priority);
  const AreaIcon = area.icon;

  const saveEdit = () => {
    onUpdate(draft);
    setEditing(false);
  };

  const toggleTask = (idx) => {
    const tasks = [...(project.tasks || [])];
    const t = tasks[idx];
    tasks[idx] = t.startsWith("✅ ") ? t.slice(3) : `✅ ${t}`;
    onUpdate({ ...project, tasks });
  };

  const doneCount = (project.tasks || []).filter(t => t.startsWith("✅")).length;
  const totalTasks = (project.tasks || []).length;

  if (editing) {
    return (
      <div className="rounded-2xl p-4 space-y-3" style={{ background: T.card, border: `2px solid ${T.rose}`, boxShadow: T.shadow }}>
        <input
          className="w-full text-sm font-bold rounded-lg px-3 py-2 border focus:outline-none"
          style={{ borderColor: T.border, color: T.text }}
          value={draft.title}
          onChange={e => setDraft({ ...draft, title: e.target.value })}
        />
        <textarea
          className="w-full text-xs rounded-lg px-3 py-2 border focus:outline-none resize-none"
          style={{ borderColor: T.border, color: T.muted }}
          rows={3}
          value={draft.note}
          onChange={e => setDraft({ ...draft, note: e.target.value })}
        />
        <div className="grid grid-cols-2 gap-2">
          <select className="text-xs px-2 py-1.5 rounded-lg border focus:outline-none"
            style={{ borderColor: T.border }}
            value={draft.status}
            onChange={e => setDraft({ ...draft, status: e.target.value })}>
            {STATUSES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
          <select className="text-xs px-2 py-1.5 rounded-lg border focus:outline-none"
            style={{ borderColor: T.border }}
            value={draft.area}
            onChange={e => setDraft({ ...draft, area: e.target.value })}>
            {AREAS.filter(a => a.id !== "all").map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
          </select>
        </div>
        <div className="flex gap-2">
          <button onClick={saveEdit} className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg text-white"
            style={{ background: T.rose }}>
            <Save size={11} /> Save
          </button>
          <button onClick={() => { setEditing(false); setDraft(project); }}
            className="text-xs px-3 py-1.5 rounded-lg border"
            style={{ borderColor: T.border, color: T.muted }}>
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden transition-all" style={{ background: T.card, border: `1px solid ${T.border}`, boxShadow: T.shadow }}>
      {/* Area color bar */}
      <div className="h-1" style={{ background: area.color }} />

      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-2 h-2 rounded-full shrink-0 ${pri.dot}`} />
              <span className="text-xs font-semibold" style={{ color: area.color }}>
                {project.area}
              </span>
            </div>
            <div className="text-sm font-bold leading-snug" style={{ color: T.text }}>{project.title}</div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => setEditing(true)} className="p-1 rounded-lg hover:bg-pink-50 transition-colors" style={{ color: T.muted }}>
              <Edit3 size={12} />
            </button>
            <button onClick={() => onDelete(project.id)} className="p-1 rounded-lg hover:bg-rose-50 transition-colors" style={{ color: T.muted }}>
              <Trash2 size={12} />
            </button>
          </div>
        </div>

        <p className="text-xs leading-relaxed mb-3" style={{ color: T.muted }}>{project.note}</p>

        {/* Footer */}
        <div className="flex items-center justify-between gap-2">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${status.cls}`}>{status.label}</span>
          <div className="flex items-center gap-2">
            {totalTasks > 0 && (
              <span className="text-xs" style={{ color: T.muted }}>{doneCount}/{totalTasks} tasks</span>
            )}
            <button
              onClick={() => setExpanded(v => !v)}
              className="flex items-center gap-1 text-xs py-0.5 px-2 rounded-full transition-colors"
              style={{ color: T.muted, background: T.bgDeep }}
            >
              {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
              {expanded ? "Less" : "Tasks"}
            </button>
          </div>
        </div>

        {/* Task checklist */}
        {expanded && totalTasks > 0 && (
          <div className="mt-3 space-y-1.5 pt-3 border-t" style={{ borderColor: T.border }}>
            {project.tasks.map((t, i) => {
              const done = t.startsWith("✅ ");
              const label = done ? t.slice(3) : t;
              return (
                <button
                  key={i}
                  onClick={() => toggleTask(i)}
                  className="flex items-start gap-2 w-full text-left transition-opacity"
                  style={{ opacity: done ? 0.5 : 1 }}
                >
                  {done
                    ? <CheckCircle2 size={13} className="shrink-0 mt-0.5" style={{ color: "#10b981" }} />
                    : <Circle      size={13} className="shrink-0 mt-0.5" style={{ color: T.muted }} />}
                  <span className="text-xs leading-snug" style={{ color: T.text, textDecoration: done ? "line-through" : "none" }}>
                    {label}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function AddProjectModal({ onAdd, onClose }) {
  const [form, setForm] = useState({
    title: "", area: "Music", status: "in-progress", priority: "medium", note: "", tasks: [],
  });
  const [taskInput, setTaskInput] = useState("");

  const addTask = () => {
    if (!taskInput.trim()) return;
    setForm(f => ({ ...f, tasks: [...f.tasks, taskInput.trim()] }));
    setTaskInput("");
  };

  const submit = (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    onAdd({ ...form, id: `custom-${Date.now()}` });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(61,44,62,0.4)", backdropFilter: "blur(4px)" }}>
      <div className="w-full max-w-md rounded-3xl shadow-2xl" style={{ background: T.card }}>
        <div className="flex items-center justify-between px-6 pt-6 pb-4">
          <h2 className="font-bold text-base" style={{ color: T.text }}>Add Project</h2>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-pink-50 transition-colors" style={{ color: T.muted }}>
            <X size={16} />
          </button>
        </div>
        <form onSubmit={submit} className="px-6 pb-6 space-y-4">
          <div>
            <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Project title *</label>
            <input required value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              className="w-full text-sm px-3 py-2 rounded-xl border focus:outline-none"
              style={{ borderColor: T.border }}
              placeholder="What are you working on?" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Area</label>
              <select value={form.area} onChange={e => setForm(f => ({ ...f, area: e.target.value }))}
                className="w-full text-xs px-2 py-2 rounded-xl border focus:outline-none"
                style={{ borderColor: T.border }}>
                {AREAS.filter(a => a.id !== "all").map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}
                className="w-full text-xs px-2 py-2 rounded-xl border focus:outline-none"
                style={{ borderColor: T.border }}>
                {STATUSES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Priority</label>
              <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}
                className="w-full text-xs px-2 py-2 rounded-xl border focus:outline-none"
                style={{ borderColor: T.border }}>
                {PRIORITIES.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Notes</label>
            <textarea value={form.note} onChange={e => setForm(f => ({ ...f, note: e.target.value }))}
              className="w-full text-xs px-3 py-2 rounded-xl border focus:outline-none resize-none"
              style={{ borderColor: T.border }}
              rows={2}
              placeholder="Context, links, or next steps…" />
          </div>
          <div>
            <label className="block text-xs font-bold mb-1" style={{ color: T.muted }}>Tasks (optional)</label>
            <div className="flex gap-2">
              <input value={taskInput} onChange={e => setTaskInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); addTask(); } }}
                className="flex-1 text-xs px-3 py-2 rounded-xl border focus:outline-none"
                style={{ borderColor: T.border }}
                placeholder="Add a task, press Enter" />
              <button type="button" onClick={addTask}
                className="px-3 py-2 rounded-xl text-xs font-bold text-white"
                style={{ background: T.lavender }}>
                Add
              </button>
            </div>
            {form.tasks.length > 0 && (
              <div className="mt-2 space-y-1">
                {form.tasks.map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs" style={{ color: T.muted }}>
                    <Circle size={10} style={{ color: T.muted }} />
                    <span className="flex-1">{t}</span>
                    <button type="button" onClick={() => setForm(f => ({ ...f, tasks: f.tasks.filter((_, j) => j !== i) }))}>
                      <X size={10} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button type="submit"
            className="w-full py-3 rounded-xl text-sm font-bold text-white transition-opacity"
            style={{ background: `linear-gradient(135deg, ${T.rose}, ${T.mauve})` }}>
            Add Project
          </button>
        </form>
      </div>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function PlatformDashboard() {
  const [projects,    setProjects]    = useState(loadProjects);
  const [activeArea,  setActiveArea]  = useState("all");
  const [showAdd,     setShowAdd]     = useState(false);
  const [aiActions,   setAiActions]   = useState(null);
  const [health,      setHealth]      = useState(null);

  useEffect(() => {
    api.get("/api/health").then(r => setHealth(r.data)).catch(() => {});
    api.get("/api/team/actions").then(r => setAiActions(r.data)).catch(() => {});
  }, []);

  useEffect(() => { saveProjects(projects); }, [projects]);

  const addProject = (p) => setProjects(ps => [p, ...ps]);
  const updateProject = (updated) => setProjects(ps => ps.map(p => p.id === updated.id ? updated : p));
  const deleteProject = (id) => setProjects(ps => ps.filter(p => p.id !== id));

  const filtered = activeArea === "all" ? projects : projects.filter(p => p.area === activeArea);

  const countByArea = (areaId) => projects.filter(p => p.area === areaId).length;

  const high    = projects.filter(p => p.priority === "high"   && p.status !== "done" && p.status !== "live").length;
  const inProg  = projects.filter(p => p.status === "in-progress").length;
  const done    = projects.filter(p => p.status === "done" || p.status === "live").length;

  return (
    <div className="px-6 py-6 space-y-6" style={{ background: T.bg, minHeight: "100%" }}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <Sparkles size={16} style={{ color: T.rose }} />
            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: T.rose }}>W.A.I. Institute</span>
          </div>
          <h1 className="text-xl font-bold" style={{ color: T.text }}>Project Tracker</h1>
          <p className="text-xs mt-0.5" style={{ color: T.muted }}>Music · Legal · Community · Business · Education · Platform · Personal</p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-1.5 text-xs font-bold px-4 py-2.5 rounded-xl text-white shrink-0 shadow-sm transition-opacity hover:opacity-90"
          style={{ background: `linear-gradient(135deg, ${T.rose}, ${T.mauve})` }}
        >
          <Plus size={13} /> Add Project
        </button>
      </div>

      {/* ── Summary pills ──────────────────────────────────────────────── */}
      <div className="flex gap-3 flex-wrap">
        {[
          { label: "Needs attention", val: high,   color: "#f43f5e", bg: "#fff1f2" },
          { label: "In progress",     val: inProg, color: T.lavender, bg: T.lavSoft },
          { label: "Live / Done",     val: done,   color: "#10b981", bg: T.sageSoft },
        ].map(s => (
          <div key={s.label} className="flex items-center gap-2 px-3 py-2 rounded-2xl text-xs font-semibold"
            style={{ background: s.bg, color: s.color }}>
            <span className="text-lg font-bold">{s.val}</span>
            <span style={{ color: T.muted }}>{s.label}</span>
          </div>
        ))}
        {health && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-2xl text-xs font-semibold"
            style={{ background: health.db ? T.sageSoft : "#fff1f2", color: health.db ? "#059669" : "#f43f5e" }}>
            <span className="w-2 h-2 rounded-full" style={{ background: health.db ? "#10b981" : "#f43f5e" }} />
            Platform {health.db ? "Online" : "Issue"}
          </div>
        )}
        {aiActions && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-2xl text-xs font-semibold"
            style={{ background: T.mauvesoft, color: T.mauve }}>
            <Sparkles size={11} />
            {aiActions.autonomy_pct ?? 0}% AI autonomous
          </div>
        )}
      </div>

      {/* ── Area filter tabs ────────────────────────────────────────────── */}
      <div className="flex gap-2 flex-wrap">
        {AREAS.map(area => (
          <AreaTab
            key={area.id}
            area={area}
            active={activeArea === area.id}
            onClick={() => setActiveArea(area.id)}
            count={area.id === "all" ? projects.length : countByArea(area.id)}
          />
        ))}
      </div>

      {/* ── Project grid ────────────────────────────────────────────────── */}
      {filtered.length === 0 ? (
        <div className="text-center py-12 text-sm" style={{ color: T.muted }}>
          No projects in this area yet.
          <button onClick={() => setShowAdd(true)} className="block mx-auto mt-3 text-xs font-bold underline" style={{ color: T.rose }}>
            Add one
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {filtered.map(p => (
            <ProjectCard key={p.id} project={p} onUpdate={updateProject} onDelete={deleteProject} />
          ))}
        </div>
      )}

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <p className="text-center text-xs pb-2" style={{ color: T.muted }}>
        Projects saved locally · Data owned by W.A.I. Institute & M.O.R.E.
      </p>

      {/* ── Add project modal ───────────────────────────────────────────── */}
      {showAdd && <AddProjectModal onAdd={addProject} onClose={() => setShowAdd(false)} />}
    </div>
  );
}
