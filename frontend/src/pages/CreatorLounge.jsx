import { useState, useEffect, useCallback } from "react";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";
import { Music, Users, Plus, X, RefreshCw, Send, ChevronDown, ChevronUp } from "lucide-react";

/* ── tokens ── */
const T = {
  bg:     "#08060f",
  card:   "#100e1a",
  purple: "#7c3aed",
  gold:   "#d4af37",
  teal:   "#0ea5e9",
  text:   "#e0d8f0",
  muted:  "#6b6480",
  border: "rgba(124,58,237,0.2)",
};

const S = {
  page:    { background: T.bg, color: T.text, minHeight: "100vh", padding: "2rem 1.5rem", maxWidth: 1000, margin: "0 auto" },
  card:    { background: T.card, border: `1px solid ${T.border}`, borderRadius: 14, padding: "1.25rem 1.4rem", marginBottom: "1rem" },
  label:   { fontSize: "0.68rem", color: T.gold, textTransform: "uppercase", letterSpacing: "0.09em", display: "block", marginBottom: "0.25rem" },
  input:   { background: "#060410", border: `1px solid rgba(124,58,237,0.3)`, borderRadius: 8, color: T.text, padding: "0.5rem 0.75rem", fontSize: "0.83rem", width: "100%", outline: "none", fontFamily: "inherit" },
  btn:     { background: T.purple, color: "#fff", border: "none", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: "bold", cursor: "pointer" },
  btnGold: { background: T.gold, color: "#1a1100", border: "none", borderRadius: 8, padding: "0.5rem 1.1rem", fontSize: "0.82rem", fontWeight: "bold", cursor: "pointer" },
  tag:     { display: "inline-block", background: "rgba(124,58,237,0.18)", border: `1px solid rgba(124,58,237,0.35)`, borderRadius: 99, padding: "0.2rem 0.6rem", fontSize: "0.7rem", color: "#c4b5fd", marginRight: "0.3rem", marginBottom: "0.25rem" },
  tagOpen: { background: "rgba(14,165,233,0.12)", border: `1px solid rgba(14,165,233,0.3)`, color: "#7dd3fc" },
};

function GenreTags({ genres }) {
  return genres?.length > 0
    ? <div style={{ marginTop: "0.4rem" }}>{genres.map(g => <span key={g} style={S.tag}>{g}</span>)}</div>
    : null;
}

function LookingForTags({ tags }) {
  return tags?.length > 0
    ? <div style={{ marginTop: "0.4rem" }}>{tags.map(t => <span key={t} style={{ ...S.tag, ...S.tagOpen }}>{t}</span>)}</div>
    : null;
}

export default function CreatorLounge() {
  const { user } = useAuth();
  const [projects, setProjects]   = useState([]);
  const [myProjects, setMyProjects] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [tab,       setTab]       = useState("browse");
  const [showForm,  setShowForm]  = useState(false);
  const [collab,    setCollab]    = useState(null); // project to collab request
  const [collabMsg, setCollabMsg] = useState("");

  const [form, setForm] = useState({
    title: "", description: "", genre: "", looking_for_text: "", open: true
  });
  const [saving, setSaving] = useState(false);
  const [genre, setGenre]   = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pub, mine] = await Promise.allSettled([
        api.get(`/creator-lounge/projects?open_only=false${genre ? `&genre=${encodeURIComponent(genre)}` : ""}`),
        api.get("/creator-lounge/my-projects"),
      ]);
      if (pub.status  === "fulfilled") setProjects(pub.value.data?.projects || []);
      if (mine.status === "fulfilled") setMyProjects(mine.value.data?.projects || []);
    } catch(e) {
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [genre]);

  useEffect(() => { load(); }, [load]);

  async function saveProject() {
    if (!form.title.trim()) return toast.error("Title required");
    setSaving(true);
    try {
      const payload = {
        title:       form.title,
        description: form.description,
        genre:       form.genre,
        looking_for: form.looking_for_text.split(",").map(s => s.trim()).filter(Boolean),
        open:        form.open,
      };
      await api.post("/creator-lounge/projects", payload);
      toast.success("Project posted!");
      setForm({ title: "", description: "", genre: "", looking_for_text: "", open: true });
      setShowForm(false);
      load();
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed to save"); }
    finally { setSaving(false); }
  }

  async function sendCollab() {
    if (!collab) return;
    try {
      await api.post(`/creator-lounge/projects/${collab.id}/collab`, { project_id: collab.id, message: collabMsg });
      toast.success("Collaboration request sent!");
      setCollab(null);
      setCollabMsg("");
    } catch(e) { toast.error(e?.response?.data?.detail || "Failed to send"); }
  }

  async function toggleOpen(proj) {
    try {
      await api.patch(`/creator-lounge/projects/${proj.id}`, {
        ...proj,
        looking_for: proj.looking_for || [],
        open: !proj.open,
      });
      toast.success(`Project ${proj.open ? "closed" : "opened"}`);
      load();
    } catch(e) { toast.error("Failed"); }
  }

  async function deleteProj(id) {
    if (!window.confirm("Delete this project?")) return;
    try {
      await api.delete(`/creator-lounge/projects/${id}`);
      toast.success("Deleted");
      load();
    } catch(e) { toast.error("Failed"); }
  }

  const TABS = ["browse", "mine", "post"];

  return (
    <AppShell>
      <div style={S.page}>

        {/* Header */}
        <div style={{ marginBottom: "1.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.3rem" }}>
            <Music size={18} color={T.gold} />
            <span style={{ fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.12em", color: T.gold, fontFamily: "Trebuchet MS, sans-serif" }}>Creator Lounge</span>
          </div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: "bold", color: "#e8d0ff", fontFamily: "Trebuchet MS, sans-serif" }}>
            Find Your People
          </h1>
          <p style={{ fontSize: "0.8rem", color: T.muted, marginTop: "0.25rem" }}>
            Post projects. Find collaborators. Build something real.
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              ...S.btn,
              background: tab === t ? T.purple : "rgba(124,58,237,0.1)",
              border: `1px solid ${tab === t ? T.purple : T.border}`,
              textTransform: "capitalize",
            }}>{t === "mine" ? "My Projects" : t === "post" ? "+ Post" : "Browse All"}</button>
          ))}
          <div style={{ flex: 1 }} />
          <input
            value={genre}
            onChange={e => setGenre(e.target.value)}
            placeholder="Filter by genre…"
            style={{ ...S.input, maxWidth: 180 }}
          />
          <button onClick={load} style={{ ...S.btn, background: "none", border: `1px solid ${T.border}`, padding: "0.45rem 0.6rem" }}>
            <RefreshCw size={14} color={T.purple} />
          </button>
        </div>

        {/* ── BROWSE ── */}
        {tab === "browse" && (
          loading
            ? <div style={{ color: T.muted, fontSize: "0.85rem" }}>Loading…</div>
            : projects.length === 0
              ? <div style={{ ...S.card, textAlign: "center", color: T.muted, padding: "2.5rem" }}>
                  <p>No projects yet. Be the first to post one.</p>
                  <button onClick={() => setTab("post")} style={{ ...S.btnGold, marginTop: "1rem" }}>Post a Project</button>
                </div>
              : projects.map(p => <ProjectCard key={p.id} project={p} currentUserId={user?.id} onCollab={setCollab} onToggle={toggleOpen} onDelete={deleteProj} />)
        )}

        {/* ── MY PROJECTS ── */}
        {tab === "mine" && (
          myProjects.length === 0
            ? <div style={{ ...S.card, textAlign: "center", color: T.muted, padding: "2.5rem" }}>
                <p>You haven't posted any projects yet.</p>
                <button onClick={() => setTab("post")} style={{ ...S.btnGold, marginTop: "1rem" }}>Post Your First Project</button>
              </div>
            : myProjects.map(p => (
                <ProjectCard key={p.id} project={p} currentUserId={user?.id} isOwner
                  onCollab={setCollab} onToggle={toggleOpen} onDelete={deleteProj} />
              ))
        )}

        {/* ── POST ── */}
        {tab === "post" && (
          <div style={S.card}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: "bold", color: "#e8d0ff", marginBottom: "1rem", fontFamily: "Trebuchet MS, sans-serif" }}>Post a New Project</h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <div>
                <label style={S.label}>Project Title *</label>
                <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} style={S.input} placeholder="e.g. Jazz EP, Trap Beat Series…" />
              </div>
              <div>
                <label style={S.label}>Genre</label>
                <input value={form.genre} onChange={e => setForm(f => ({ ...f, genre: e.target.value }))} style={S.input} placeholder="Hip-Hop, R&B, Gospel…" />
              </div>
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <label style={S.label}>Description</label>
              <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                rows={4} style={{ ...S.input, resize: "vertical" }} placeholder="What's the project about? What are you building?" />
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <label style={S.label}>Looking For (comma-separated)</label>
              <input value={form.looking_for_text} onChange={e => setForm(f => ({ ...f, looking_for_text: e.target.value }))}
                style={S.input} placeholder="vocalist, mixing engineer, beatmaker…" />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
              <label style={{ ...S.label, marginBottom: 0 }}>Accepting Collaborators:</label>
              <button onClick={() => setForm(f => ({ ...f, open: !f.open }))} style={{
                background: form.open ? "rgba(14,165,233,0.15)" : "rgba(107,100,128,0.15)",
                border: `1px solid ${form.open ? "rgba(14,165,233,0.4)" : "rgba(107,100,128,0.3)"}`,
                borderRadius: 8, padding: "0.3rem 0.75rem", cursor: "pointer",
                color: form.open ? "#7dd3fc" : T.muted, fontSize: "0.78rem", fontWeight: "bold"
              }}>{form.open ? "Yes — Open" : "No — Closed"}</button>
            </div>

            <div style={{ display: "flex", gap: "0.6rem" }}>
              <button onClick={saveProject} disabled={saving} style={{ ...S.btnGold, opacity: saving ? 0.5 : 1 }}>
                {saving ? "Posting…" : "Post Project"}
              </button>
              <button onClick={() => setTab("browse")} style={{ ...S.btn, background: "none", border: `1px solid ${T.border}` }}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* ── COLLAB MODAL ── */}
        {collab && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 9000, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ ...S.card, width: "min(480px, 90vw)", position: "relative" }}>
              <button onClick={() => setCollab(null)} style={{ position: "absolute", top: "0.75rem", right: "0.75rem", background: "none", border: "none", cursor: "pointer", color: T.muted }}>
                <X size={18} />
              </button>
              <h3 style={{ fontFamily: "Trebuchet MS, sans-serif", color: "#e8d0ff", marginBottom: "0.5rem" }}>Request to Collaborate</h3>
              <p style={{ color: T.muted, fontSize: "0.8rem", marginBottom: "1rem" }}>
                On: <strong style={{ color: T.text }}>{collab.title}</strong> by {collab.owner_name}
              </p>
              <label style={S.label}>Message (optional)</label>
              <textarea value={collabMsg} onChange={e => setCollabMsg(e.target.value)}
                rows={3} style={{ ...S.input, resize: "vertical", marginBottom: "0.85rem" }}
                placeholder="Introduce yourself and describe what you'd bring to this project…" />
              <div style={{ display: "flex", gap: "0.6rem" }}>
                <button onClick={sendCollab} style={S.btnGold}>
                  <Send size={13} style={{ display: "inline", marginRight: 5 }} />Send Request
                </button>
                <button onClick={() => setCollab(null)} style={{ ...S.btn, background: "none", border: `1px solid ${T.border}` }}>Cancel</button>
              </div>
            </div>
          </div>
        )}

      </div>
    </AppShell>
  );
}

function ProjectCard({ project: p, currentUserId, isOwner, onCollab, onToggle, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const mine = isOwner || p.owner_id === currentUserId;

  return (
    <div style={{ background: "#100e1a", border: `1px solid ${p.open ? "rgba(14,165,233,0.2)" : "rgba(124,58,237,0.15)"}`, borderRadius: 14, padding: "1.1rem 1.3rem", marginBottom: "0.85rem" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ fontWeight: "bold", fontSize: "0.95rem", color: "#e8d0ff", fontFamily: "Trebuchet MS, sans-serif" }}>{p.title}</span>
            {p.genre && <span style={{ fontSize: "0.7rem", color: "#7c3aed", background: "rgba(124,58,237,0.12)", border: "1px solid rgba(124,58,237,0.25)", borderRadius: 99, padding: "0.15rem 0.5rem" }}>{p.genre}</span>}
            <span style={{ fontSize: "0.7rem", color: p.open ? "#7dd3fc" : "#6b6480", background: p.open ? "rgba(14,165,233,0.1)" : "rgba(107,100,128,0.1)", border: `1px solid ${p.open ? "rgba(14,165,233,0.3)" : "rgba(107,100,128,0.25)"}`, borderRadius: 99, padding: "0.15rem 0.5rem" }}>
              {p.open ? "✦ Open" : "Closed"}
            </span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#7c3aed", marginTop: "0.2rem" }}>by {p.owner_name}</div>
        </div>

        <div style={{ display: "flex", gap: "0.4rem", flexShrink: 0 }}>
          {!mine && p.open && (
            <button onClick={() => onCollab(p)} style={{ background: "rgba(14,165,233,0.15)", border: "1px solid rgba(14,165,233,0.3)", borderRadius: 8, padding: "0.35rem 0.8rem", fontSize: "0.75rem", color: "#7dd3fc", cursor: "pointer", fontWeight: "bold" }}>
              <Users size={12} style={{ display: "inline", marginRight: 4 }} />Collab
            </button>
          )}
          {mine && (
            <>
              <button onClick={() => onToggle(p)} style={{ background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.25)", borderRadius: 8, padding: "0.35rem 0.7rem", fontSize: "0.72rem", color: "#c4b5fd", cursor: "pointer" }}>
                {p.open ? "Close" : "Open"}
              </button>
              <button onClick={() => onDelete(p.id)} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)", borderRadius: 8, padding: "0.35rem 0.7rem", fontSize: "0.72rem", color: "#fca5a5", cursor: "pointer" }}>
                <X size={12} />
              </button>
            </>
          )}
          <button onClick={() => setExpanded(v => !v)} style={{ background: "none", border: "1px solid rgba(124,58,237,0.15)", borderRadius: 8, padding: "0.35rem 0.5rem", cursor: "pointer", color: "#6b6480" }}>
            {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
        </div>
      </div>

      {p.looking_for?.length > 0 && (
        <div style={{ marginTop: "0.5rem" }}>
          <LookingForTags tags={p.looking_for} />
        </div>
      )}

      {expanded && p.description && (
        <p style={{ fontSize: "0.8rem", color: "#b8b0c8", marginTop: "0.7rem", lineHeight: 1.65, whiteSpace: "pre-wrap" }}>{p.description}</p>
      )}

      {expanded && p.collabs?.length > 0 && mine && (
        <div style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid rgba(124,58,237,0.15)" }}>
          <div style={{ fontSize: "0.68rem", color: "#d4af37", textTransform: "uppercase", letterSpacing: "0.09em", marginBottom: "0.4rem" }}>Collaboration Requests ({p.collabs.length})</div>
          {p.collabs.map((c, i) => (
            <div key={i} style={{ background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.15)", borderRadius: 8, padding: "0.5rem 0.75rem", marginBottom: "0.35rem", fontSize: "0.78rem" }}>
              <strong style={{ color: "#c4b5fd" }}>{c.user_name}</strong>
              {c.message && <span style={{ color: "#9090a8", marginLeft: 8 }}>{c.message}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LookingForTags({ tags }) {
  return tags?.length > 0
    ? <>{tags.map(t => <span key={t} style={{ display: "inline-block", background: "rgba(14,165,233,0.1)", border: "1px solid rgba(14,165,233,0.25)", borderRadius: 99, padding: "0.18rem 0.55rem", fontSize: "0.68rem", color: "#7dd3fc", marginRight: "0.3rem" }}>{t}</span>)}</>
    : null;
}
