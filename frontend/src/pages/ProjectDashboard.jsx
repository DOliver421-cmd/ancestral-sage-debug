import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

const COPPER = "#b5651d";
const BONE = "#f5f0e8";
const INK = "#1a1a1a";
const WHITE = "#ffffff";

const STATUS_COLORS = {
  active:     { bg: "#dcfce7", text: "#166534" },
  in_review:  { bg: "#fef9c3", text: "#854d0e" },
  blocked:    { bg: "#fee2e2", text: "#991b1b" },
  complete:   { bg: "#e0e7ff", text: "#3730a3" },
  archived:   { bg: "#f3f4f6", text: "#6b7280" },
};

const PRIORITY_COLORS = {
  critical: "#dc2626",
  high:     "#ea580c",
  normal:   COPPER,
  low:      "#64748b",
};

const PERSONAS = ["AXIOM", "CIPHER", "MAVEN", "SAGE", "Jamil"];

function StatusBadge({ status }) {
  const s = STATUS_COLORS[status] || STATUS_COLORS.active;
  return (
    <span style={{ background: s.bg, color: s.text, borderRadius: 20, padding: "2px 10px", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
      {status.replace("_", " ")}
    </span>
  );
}

function MilestoneRow({ m, projectId, onUpdate }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0", borderBottom: "1px solid rgba(0,0,0,0.04)" }}>
      <button
        onClick={() => onUpdate(projectId, m.id, { complete: !m.complete })}
        style={{ width: 20, height: 20, borderRadius: 4, border: `2px solid ${m.complete ? COPPER : "#ccc"}`, background: m.complete ? COPPER : "transparent", cursor: "pointer", flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", color: WHITE, fontSize: 12 }}
      >
        {m.complete ? "✓" : ""}
      </button>
      <span style={{ flex: 1, fontSize: 13, color: INK, textDecoration: m.complete ? "line-through" : "none", opacity: m.complete ? 0.5 : 1 }}>{m.title}</span>
      {m.assigned_to && <span style={{ fontSize: 11, color: COPPER, fontWeight: 600 }}>{m.assigned_to}</span>}
      {m.due_date && <span style={{ fontSize: 11, color: "#888" }}>{m.due_date}</span>}
    </div>
  );
}

function ProjectCard({ project, onUpdate, onMilestoneUpdate, onAddMilestone, onArchive }) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ title: project.title, description: project.description || "", owner: project.owner || "", priority: project.priority || "normal", due_date: project.due_date || "", notes: project.notes || "", status: project.status });
  const [newMilestone, setNewMilestone] = useState("");
  const [milestoneAssign, setMilestoneAssign] = useState("");
  const [saving, setSaving] = useState(false);
  const [confirmArchive, setConfirmArchive] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await onUpdate(project.project_id, form);
      setEditing(false);
      toast.success("Project updated");
    } catch { toast.error("Save failed"); }
    finally { setSaving(false); }
  };

  const addMilestone = async () => {
    if (!newMilestone.trim()) return;
    await onAddMilestone(project.project_id, { title: newMilestone.trim(), assigned_to: milestoneAssign });
    setNewMilestone("");
    setMilestoneAssign("");
  };

  const milestones = project.milestones || [];
  const done = milestones.filter(m => m.complete).length;

  return (
    <div style={{ background: WHITE, borderRadius: 12, border: `1px solid rgba(181,101,29,0.15)`, marginBottom: 16, overflow: "hidden" }}>
      {/* Card header */}
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "flex-start", gap: 12, cursor: "pointer" }} onClick={() => setExpanded(e => !e)}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 6 }}>
            <span style={{ fontSize: 17, fontWeight: 800, color: INK }}>{project.title}</span>
            <StatusBadge status={project.status} />
            <span style={{ fontSize: 11, color: PRIORITY_COLORS[project.priority] || COPPER, fontWeight: 700, textTransform: "uppercase" }}>{project.priority}</span>
          </div>
          <div style={{ display: "flex", gap: 16, fontSize: 12, color: "#888", flexWrap: "wrap" }}>
            {project.owner && <span>👤 {project.owner}</span>}
            {project.due_date && <span>📅 {project.due_date}</span>}
            {milestones.length > 0 && <span>🎯 {done}/{milestones.length} milestones</span>}
            {project.arena_rounds?.length > 0 && <span>⚔️ {project.arena_rounds.length} Arena rounds</span>}
          </div>
        </div>
        <span style={{ color: COPPER, fontSize: 18, flexShrink: 0 }}>{expanded ? "▲" : "▼"}</span>
      </div>

      {/* Expanded body */}
      {expanded && (
        <div style={{ padding: "0 20px 20px", borderTop: "1px solid rgba(181,101,29,0.08)" }}>
          {editing ? (
            <div style={{ paddingTop: 16 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Title</label>
                  <input value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box" }} />
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Status</label>
                  <select value={form.status} onChange={e => setForm(f => ({...f, status: e.target.value}))} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14 }}>
                    {["active","in_review","blocked","complete"].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Owner</label>
                  <input value={form.owner} onChange={e => setForm(f => ({...f, owner: e.target.value}))} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box" }} />
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Priority</label>
                  <select value={form.priority} onChange={e => setForm(f => ({...f, priority: e.target.value}))} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14 }}>
                    {["critical","high","normal","low"].map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Due Date</label>
                  <input type="date" value={form.due_date} onChange={e => setForm(f => ({...f, due_date: e.target.value}))} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box" }} />
                </div>
              </div>
              <div style={{ marginBottom: 10 }}>
                <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>Description</label>
                <textarea value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} rows={2} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box", resize: "vertical" }} />
              </div>
              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase" }}>PM Notes</label>
                <textarea value={form.notes} onChange={e => setForm(f => ({...f, notes: e.target.value}))} rows={3} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14, boxSizing: "border-box", resize: "vertical" }} />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={save} disabled={saving} style={{ background: COPPER, color: WHITE, border: "none", borderRadius: 8, padding: "8px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>{saving ? "Saving…" : "Save"}</button>
                <button onClick={() => setEditing(false)} style={{ background: "transparent", border: "1px solid #ddd", borderRadius: 8, padding: "8px 16px", fontSize: 13, cursor: "pointer" }}>Cancel</button>
                <button onClick={() => setConfirmArchive(true)} style={{ marginLeft: "auto", background: "transparent", border: "1px solid #fca5a5", color: "#dc2626", borderRadius: 8, padding: "8px 14px", fontSize: 12, cursor: "pointer" }}>Archive</button>
              </div>
            </div>
          ) : (
            <div style={{ paddingTop: 12 }}>
              {project.description && <p style={{ margin: "0 0 10px", fontSize: 14, color: "#555", lineHeight: 1.6 }}>{project.description}</p>}
              {project.notes && (
                <div style={{ background: BONE, borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: 13, color: INK, lineHeight: 1.6 }}>
                  <strong>PM Notes:</strong> {project.notes}
                </div>
              )}
              <button onClick={() => setEditing(true)} style={{ background: "transparent", border: `1px solid rgba(181,101,29,0.3)`, color: COPPER, borderRadius: 6, padding: "6px 14px", fontSize: 12, fontWeight: 700, cursor: "pointer", marginBottom: 16 }}>✏️ Edit Project</button>
            </div>
          )}

          {/* Milestones */}
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#888", textTransform: "uppercase", marginBottom: 8 }}>Milestones</div>
            {milestones.length === 0 && <div style={{ fontSize: 13, color: "#aaa", marginBottom: 8 }}>No milestones yet.</div>}
            {milestones.map(m => (
              <MilestoneRow key={m.id} m={m} projectId={project.project_id} onUpdate={onMilestoneUpdate} />
            ))}
            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <input value={newMilestone} onChange={e => setNewMilestone(e.target.value)} onKeyDown={e => e.key === "Enter" && addMilestone()} placeholder="Add milestone…" style={{ flex: 1, padding: "7px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13 }} />
              <select value={milestoneAssign} onChange={e => setMilestoneAssign(e.target.value)} style={{ padding: "7px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13 }}>
                <option value="">Assign to…</option>
                {PERSONAS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <button onClick={addMilestone} style={{ background: COPPER, color: WHITE, border: "none", borderRadius: 6, padding: "7px 14px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>+</button>
            </div>
          </div>

          {/* Arena rounds summary */}
          {project.arena_rounds?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#888", textTransform: "uppercase", marginBottom: 8 }}>Arena Rounds</div>
              {project.arena_rounds.map(r => (
                <div key={r.round} style={{ background: BONE, borderRadius: 6, padding: "8px 12px", marginBottom: 6, fontSize: 12 }}>
                  <strong>Round {r.round}:</strong> {r.task?.slice(0, 80)}{r.task?.length > 80 ? "…" : ""}
                  <div style={{ display: "flex", gap: 10, marginTop: 4, flexWrap: "wrap" }}>
                    {r.results.map(res => (
                      <span key={res.persona} style={{ color: res.verdict === "PASS" ? "#166534" : "#991b1b", fontWeight: 600 }}>{res.persona}: {res.score}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {confirmArchive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
            <h2 className="font-heading font-bold text-lg text-slate-900 mb-2">Archive Project</h2>
            <p className="text-sm text-slate-600 mb-6">Archive this project? It will no longer appear in the active list.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmArchive(false)} className="text-sm px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-50">Cancel</button>
              <button onClick={() => { setConfirmArchive(false); onArchive(project.project_id); }} className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white font-bold hover:bg-red-700">Archive</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProjectDashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({ title: "", description: "", owner: "", priority: "normal", due_date: "" });
  const [creating, setCreating] = useState(false);
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/projects");
      // Enrich each with arena rounds by fetching individually
      const enriched = await Promise.all(
        (data.projects || []).map(async p => {
          try {
            const { data: full } = await api.get(`/projects/${p.project_id}`);
            return full;
          } catch { return p; }
        })
      );
      setProjects(enriched);
    } catch { toast.error("Could not load projects"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const createProject = async () => {
    if (!newProject.title.trim()) return;
    setCreating(true);
    try {
      const { data } = await api.post("/projects", newProject);
      setProjects(prev => [data, ...prev]);
      setShowCreate(false);
      setNewProject({ title: "", description: "", owner: "", priority: "normal", due_date: "" });
      toast.success("Project created");
    } catch { toast.error("Create failed"); }
    finally { setCreating(false); }
  };

  const updateProject = async (projectId, updates) => {
    const { data } = await api.patch(`/projects/${projectId}`, updates);
    setProjects(prev => prev.map(p => p.project_id === projectId ? { ...p, ...data } : p));
  };

  const updateMilestone = async (projectId, milestoneId, updates) => {
    await api.patch(`/projects/${projectId}/milestone/${milestoneId}`, updates);
    load();
  };

  const addMilestone = async (projectId, milestone) => {
    await api.post(`/projects/${projectId}/milestone`, milestone);
    load();
  };

  const archiveProject = async (projectId) => {
    await api.delete(`/projects/${projectId}`);
    setProjects(prev => prev.filter(p => p.project_id !== projectId));
    toast.success("Project archived");
  };

  const filtered = filter === "all" ? projects : projects.filter(p => p.status === filter);
  const counts = { active: 0, in_review: 0, blocked: 0, complete: 0 };
  projects.forEach(p => { if (counts[p.status] !== undefined) counts[p.status]++; });

  return (
    <div style={{ minHeight: "100vh", background: BONE }}>
      {/* Header */}
      <div style={{ background: WHITE, borderBottom: `1px solid rgba(181,101,29,0.12)`, padding: "24px 32px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 32, fontWeight: 900, color: COPPER }}>Project Dashboard</h1>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: "#888" }}>Managed by Jamil · {projects.length} project{projects.length !== 1 ? "s" : ""}</p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button onClick={() => navigate("/jamil")} style={{ background: "transparent", border: `1px solid rgba(181,101,29,0.3)`, color: COPPER, borderRadius: 8, padding: "8px 16px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>Talk to Jamil</button>
            <button onClick={() => setShowCreate(true)} style={{ background: COPPER, color: WHITE, border: "none", borderRadius: 8, padding: "8px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>+ New Project</button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 32px" }}>
        {/* Status summary */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
          {[["active","Active","#dcfce7","#166534"],["in_review","In Review","#fef9c3","#854d0e"],["blocked","Blocked","#fee2e2","#991b1b"],["complete","Complete","#e0e7ff","#3730a3"]].map(([k, label, bg, color]) => (
            <button key={k} onClick={() => setFilter(f => f === k ? "all" : k)}
              style={{ background: filter === k ? bg : WHITE, border: `1.5px solid ${filter === k ? color : "rgba(0,0,0,0.08)"}`, borderRadius: 10, padding: "14px 16px", cursor: "pointer", textAlign: "left" }}>
              <div style={{ fontSize: 24, fontWeight: 900, color }}>{counts[k]}</div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>{label}</div>
            </button>
          ))}
        </div>

        {/* Create form */}
        {showCreate && (
          <div style={{ background: WHITE, borderRadius: 12, border: `1px solid rgba(181,101,29,0.2)`, padding: 20, marginBottom: 20 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: COPPER, marginBottom: 14 }}>New Project</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div style={{ gridColumn: "1 / -1" }}>
                <input value={newProject.title} onChange={e => setNewProject(p => ({...p, title: e.target.value}))} placeholder="Project title *" style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd", fontSize: 15, boxSizing: "border-box" }} />
              </div>
              <input value={newProject.owner} onChange={e => setNewProject(p => ({...p, owner: e.target.value}))} placeholder="Owner / responsible party" style={{ padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13 }} />
              <select value={newProject.priority} onChange={e => setNewProject(p => ({...p, priority: e.target.value}))} style={{ padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13 }}>
                {["critical","high","normal","low"].map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <input type="date" value={newProject.due_date} onChange={e => setNewProject(p => ({...p, due_date: e.target.value}))} style={{ padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13 }} />
            </div>
            <textarea value={newProject.description} onChange={e => setNewProject(p => ({...p, description: e.target.value}))} placeholder="Description (optional)" rows={2} style={{ width: "100%", padding: "8px 10px", borderRadius: 6, border: "1px solid #ddd", fontSize: 13, boxSizing: "border-box", resize: "vertical", marginBottom: 12 }} />
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={createProject} disabled={creating || !newProject.title.trim()} style={{ background: COPPER, color: WHITE, border: "none", borderRadius: 8, padding: "8px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>{creating ? "Creating…" : "Create Project"}</button>
              <button onClick={() => setShowCreate(false)} style={{ background: "transparent", border: "1px solid #ddd", borderRadius: 8, padding: "8px 16px", fontSize: 13, cursor: "pointer" }}>Cancel</button>
            </div>
          </div>
        )}

        {/* Project list */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 60, color: "#aaa", fontSize: 15 }}>Loading projects…</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: "center", padding: 60, color: "#aaa" }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
            <div style={{ fontSize: 15 }}>{filter === "all" ? "No projects yet. Create one to get started." : `No ${filter} projects.`}</div>
          </div>
        ) : (
          filtered.map(p => (
            <ProjectCard
              key={p.project_id}
              project={p}
              onUpdate={updateProject}
              onMilestoneUpdate={updateMilestone}
              onAddMilestone={addMilestone}
              onArchive={archiveProject}
            />
          ))
        )}
      </div>
    </div>
  );
}
