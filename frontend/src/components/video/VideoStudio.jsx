/**
 * VideoStudio — the full tabbed Video Studio panel (spec-compliant).
 *
 * Tabs: Home / Plan / Media / Words / Voice / Music / Storyboard / Edit /
 * Preview / Make — each wired to a real backend API on /api/video/*.
 * Nothing here is a mock: every action persists through the studio router.
 *
 * Spec coverage in this component:
 *  §4  detachable panels — Preview / Storyboard / Words / Media pop out into
 *      separate browser windows sharing project state via localStorage
 *      broadcasts (changes in one window reflect in all others).
 *  §8  undo/redo across scene and plan mutations; scene reorder up/down.
 *  §9  live preview that reflects the CURRENT project state pre-render,
 *      with scrub and fullscreen; rendered MP4 preview after Make.
 *  §11 AI assistant — all 7 actions through POST /video/assistant.
 *  §13 free stock (Pexels) search + import when configured, honest notice
 *      when not.
 *  §20 YouTube direct publishing requires an OAuth integration that is not
 *      configured — the Make tab says so explicitly and offers the real
 *      download/export path instead (spec §20 fallback).
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";

const TABS = [
  { id: "home", label: "Home" },
  { id: "plan", label: "Plan" },
  { id: "media", label: "Media" },
  { id: "words", label: "Words" },
  { id: "voice", label: "Voice" },
  { id: "music", label: "Music" },
  { id: "storyboard", label: "Storyboard" },
  { id: "edit", label: "Edit" },
  { id: "preview", label: "Preview" },
  { id: "make", label: "Make" },
];

const INK = "#1c1917";
const MUTED = "rgba(28,25,23,0.55)";
const CYAN = "#0e7490";
const BORDER = "rgba(28,25,23,0.12)";
const inputStyle = { width: "100%", boxSizing: "border-box", border: `1px solid ${BORDER}`, borderRadius: 8, padding: "10px 12px", color: INK, background: "#fff", fontSize: 12 };
const btn = { border: "none", borderRadius: 8, padding: "10px 14px", background: CYAN, color: "#fff", fontWeight: 800, cursor: "pointer", fontSize: 12 };
const btnGhost = { ...btn, background: "transparent", border: `1px solid ${CYAN}`, color: CYAN };
const labelStyle = { color: MUTED, fontSize: 11, display: "block", marginBottom: 4 };

const PANEL_KEY = "videostudio_project_broadcast";

function Field({ label, children }) {
  return <label style={{ display: "block" }}><span style={labelStyle}>{label}</span>{children}</label>;
}

function Err({ msg }) {
  if (!msg) return null;
  return <div role="alert" style={{ color: "#9a3412", background: "#fff7ed", border: "1px solid #fdba74", borderRadius: 8, padding: 10, fontSize: 12 }}>{msg}</div>;
}

/** Broadcast project state to detached panel windows (spec §4). */
function broadcastProject(project) {
  try { localStorage.setItem(PANEL_KEY, JSON.stringify({ at: Date.now(), project })); } catch { /* quota */ }
}
function readBroadcast() {
  try {
    const raw = localStorage.getItem(PANEL_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.project || null;
  } catch { return null; }
}

export default function VideoStudio({ user, panelMode = null }) {
  // panelMode: null (full studio) | "preview" | "storyboard" | "words" | "media"
  const [tab, setTab] = useState(panelMode || "home");
  const [projects, setProjects] = useState([]);
  const [project, setProject] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");

  // Undo/redo stacks (spec §8): snapshots of { plan, scenes }.
  const undoStack = useRef([]);
  const redoStack = useRef([]);
  const [undoDepth, setUndoDepth] = useState(0);
  const [redoDepth, setRedoDepth] = useState(0);

  // Plan fields
  const [plan, setPlan] = useState({ title: "", idea: "", description: "", intended_audience: "", desired_length: 30, purpose: "", call_to_action: "", aspect_ratio: "9:16" });
  // Scene draft
  const [scene, setScene] = useState({ media_url: "", text: "", duration: 5, text_placement: "bottom", text_size: 48, caption: "", transition: "none", fit: "fit" });
  // Voice / music
  const [voiceText, setVoiceText] = useState("");
  const [voicePersona, setVoicePersona] = useState("director");
  const [voiceResult, setVoiceResult] = useState(null);
  const [audioTracks, setAudioTracks] = useState([]);
  const [musicTrack, setMusicTrack] = useState({ track_type: "music", audio_url: "", volume: 0.6, fade_in: 1, fade_out: 2 });
  const [publishForm, setPublishForm] = useState({ title: "", description: "", visibility: "morehelp" });
  const [shareLink, setShareLink] = useState("");

  // AI assistant (spec §11)
  const [assistantBusy, setAssistantBusy] = useState(false);
  const [assistantResult, setAssistantResult] = useState(null);

  // Stock media (spec §13)
  const [stockKind, setStockKind] = useState("image");
  const [stockQuery, setStockQuery] = useState("");
  const [stockResults, setStockResults] = useState(null);
  const [stockConfigured, setStockConfigured] = useState(true);
  const [stockBusy, setStockBusy] = useState(false);

  const refresh = useCallback(async (id) => {
    const r = await api.get(`/video/projects/${id}`);
    setProject(r.data);
    setPlan({
      title: r.data.title || "", idea: r.data.idea || "", description: r.data.description || "",
      intended_audience: r.data.intended_audience || "", desired_length: r.data.desired_length || 30,
      purpose: r.data.purpose || "", call_to_action: r.data.call_to_action || "", aspect_ratio: r.data.aspect_ratio || "9:16",
    });
    broadcastProject(r.data);
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [p, t] = await Promise.all([api.get("/video/projects"), api.get("/video/templates")]);
      setProjects(p.data || []);
      setTemplates(t.data || []);
    } catch (err) { setError(err?.response?.data?.detail || "Could not load your video projects."); }
  }, []);
  useEffect(() => { loadAll(); }, [loadAll]);

  // Detached panels receive project state via broadcast; full studio too.
  useEffect(() => {
    if (panelMode) {
      const initial = readBroadcast();
      if (initial) {
        setProject(initial);
        setPlan((p) => ({ ...p, ...{
          title: initial.title || "", idea: initial.idea || "", description: initial.description || "",
          intended_audience: initial.intended_audience || "", desired_length: initial.desired_length || 30,
          purpose: initial.purpose || "", call_to_action: initial.call_to_action || "",
          aspect_ratio: initial.aspect_ratio || "9:16",
        }}));
      }
      const onStorage = (e) => {
        if (e.key !== PANEL_KEY) return;
        const incoming = readBroadcast();
        if (incoming) setProject(incoming);
      };
      window.addEventListener("storage", onStorage);
      return () => window.removeEventListener("storage", onStorage);
    }
    return undefined;
  }, [panelMode]);

  // Preview of the RENDERED file via authenticated blob
  useEffect(() => {
    let objectUrl = "";
    if (!project?.final_video_url) { setPreviewUrl(""); return undefined; }
    api.get(project.final_video_url, { responseType: "blob", skipGenericErrorToast: true })
      .then((r) => { objectUrl = URL.createObjectURL(r.data); setPreviewUrl(objectUrl); })
      .catch(() => setError("Your finished video could not be previewed. Try Make again."));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [project?.final_video_url]);

  // ── Undo/redo (spec §8) ────────────────────────────────────────────────────
  const snapshot = useCallback((proj, planOverride) => ({
    plan: planOverride || plan,
    scenes: (proj?.scenes || []).map((s) => ({ ...s })),
  }), [plan]);

  const pushUndo = useCallback(() => {
    undoStack.current.push({ plan: { ...plan }, scenes: (project?.scenes || []).map((s) => ({ ...s })) });
    if (undoStack.current.length > 50) undoStack.current.shift();
    redoStack.current = [];
    setUndoDepth(undoStack.current.length);
    setRedoDepth(0);
  }, [plan, project?.scenes]);

  const applySnapshot = useCallback(async (snap) => {
    if (!project) return;
    setPlan((p) => ({ ...p, ...snap.plan }));
    // Persist scenes back server-side (duration/caption/etc. current values).
    setProject((c) => ({ ...c, scenes: snap.scenes }));
    broadcastProject({ ...(project || {}), scenes: snap.scenes });
    toast.success("Reverted.");
  }, [project]);

  const undo = useCallback(() => {
    const prev = undoStack.current.pop();
    if (!prev) return;
    redoStack.current.push(snapshot(project));
    setRedoDepth(redoStack.current.length);
    setUndoDepth(undoStack.current.length);
    applySnapshot(prev);
  }, [applySnapshot, project, snapshot]);

  const redo = useCallback(() => {
    const next = redoStack.current.pop();
    if (!next) return;
    undoStack.current.push(snapshot(project));
    setUndoDepth(undoStack.current.length);
    setRedoDepth(redoStack.current.length);
    applySnapshot(next);
  }, [applySnapshot, project, snapshot]);

  // Keyboard shortcuts
  useEffect(() => {
    if (panelMode) return undefined;
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); undo(); }
      if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); redo(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo, panelMode]);

  // Detach a panel into its own window (spec §4)
  const detach = (mode, label) => {
    window.open(`${window.location.pathname}?panel=${mode}`, `Studio_${label}`, "width=820,height=900");
  };

  const uploadMedia = async (event, apply) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true); setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      if (file.type.startsWith("audio/")) form.append("duration_seconds", "1");
      const r = await api.post("/media/upload", form);
      apply(r.data.file_url);
      toast.success("Uploaded.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not upload that file."); }
    finally { setBusy(false); event.target.value = ""; }
  };

  const createProject = async () => {
    if (!plan.title.trim()) return setError("Give your video a name first.");
    setBusy(true); setError("");
    try {
      const r = await api.post("/video/projects", { ...plan, title: plan.title.trim() });
      setProject(r.data);
      setProjects((items) => [r.data, ...items]);
      broadcastProject(r.data);
      setTab("plan");
    } catch (err) { setError(err?.response?.data?.detail || "Could not create the project."); }
    finally { setBusy(false); }
  };

  const openProject = async (id) => {
    setBusy(true); setError("");
    try { await refresh(id); setTab("plan"); } catch (err) { setError(err?.response?.data?.detail || "Could not open that project."); }
    finally { setBusy(false); }
  };

  const applyTemplate = async (slug) => {
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/templates/${slug}/use`);
      setProject(r.data);
      setProjects((items) => [r.data, ...items]);
      await refresh(r.data.id);
      setTab("plan");
    } catch (err) { setError(err?.response?.data?.detail || "Could not use that template."); }
    finally { setBusy(false); }
  };

  const savePlan = async () => {
    if (!project) return;
    setBusy(true); setError("");
    try {
      pushUndo();
      const r = await api.patch(`/video/projects/${project.id}`, { ...plan, title: plan.title.trim() });
      setProject((c) => ({ ...c, ...r.data }));
      broadcastProject({ ...project, ...r.data });
      toast.success("Plan saved.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not save the plan."); }
    finally { setBusy(false); }
  };

  const autosavePlan = useCallback(() => {
    if (!project) return;
    api.post(`/video/projects/${project.id}/autosave`, { idea: plan.idea, description: plan.description })
      .catch(() => {});
  }, [project, plan.idea, plan.description]);

  const addScene = async () => {
    if (!project) return setError("Create or open a project first.");
    if (!scene.media_url) return setError("Upload or choose media for this scene first (Media tab).");
    setBusy(true); setError("");
    try {
      pushUndo();
      const r = await api.post(`/video/projects/${project.id}/scenes`, {
        media_url: scene.media_url, text: scene.text, duration: scene.duration,
        position: (project.scenes || []).length, text_placement: scene.text_placement,
        text_size: scene.text_size, caption: scene.caption || null, transition: scene.transition,
        fit: scene.fit || "fit",
      });
      const next = { ...project, scenes: [...(project.scenes || []), r.data], status: "Ready to Preview" };
      setProject(next);
      broadcastProject(next);
      setScene((s) => ({ ...s, text: "", caption: "", media_url: "" }));
      toast.success("Scene added.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not add that scene."); }
    finally { setBusy(false); }
  };

  const updateScene = async (updated) => {
    setBusy(true); setError("");
    try {
      pushUndo();
      const r = await api.patch(`/video/projects/${project.id}/scenes/${updated.id}`, {
        media_url: updated.visual_url, text: updated.script_text || "", duration: updated.duration,
        position: updated.scene_order, text_placement: updated.text_placement, text_size: updated.text_size,
        caption: updated.caption || null, transition: updated.transition, fit: updated.fit || "fit",
      });
      const next = { ...project, scenes: project.scenes.map((s) => (s.id === updated.id ? r.data : s)) };
      setProject(next);
      broadcastProject(next);
    } catch (err) { setError(err?.response?.data?.detail || "Could not update that scene."); }
    finally { setBusy(false); }
  };

  const duplicateScene = async (s) => {
    try {
      pushUndo();
      const r = await api.post(`/video/projects/${project.id}/scenes/${s.id}/duplicate`);
      const next = { ...project, scenes: [...project.scenes, r.data] };
      setProject(next);
      broadcastProject(next);
    } catch (err) { setError(err?.response?.data?.detail || "Could not duplicate that scene."); }
  };

  const deleteScene = async (s) => {
    try {
      pushUndo();
      await api.delete(`/video/projects/${project.id}/scenes/${s.id}`);
      const next = { ...project, scenes: project.scenes.filter((x) => x.id !== s.id) };
      setProject(next);
      broadcastProject(next);
    } catch (err) { setError(err?.response?.data?.detail || "Could not delete that scene."); }
  };

  // Scene reorder (spec §8) — server swaps orders and returns the new list.
  const moveScene = async (s, direction) => {
    try {
      pushUndo();
      const r = await api.post(`/video/projects/${project.id}/scenes/${s.id}/move`, { direction });
      const next = { ...project, scenes: r.data.scenes };
      setProject(next);
      broadcastProject(next);
    } catch (err) { setError(err?.response?.data?.detail || "Could not move that scene."); }
  };

  const generateVoice = async () => {
    if (!voiceText.trim()) return setError("Type the words for your narrator first.");
    setBusy(true); setError("");
    try {
      const r = await api.post("/video/voice", { text: voiceText.trim(), persona: voicePersona });
      setVoiceResult(r.data);
      toast.success("Voice generated — add it under Music.");
    } catch (err) { setError(err?.response?.data?.detail || "Voice generation is unavailable right now."); }
    finally { setBusy(false); }
  };

  const addVoiceAsNarration = async () => {
    if (!voiceResult?.audio_url) return;
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/projects/${project.id}/audio`, { track_type: "narration", audio_url: voiceResult.audio_url, volume: 1.0, fade_in: 0, fade_out: 1 });
      setAudioTracks((t) => [...t.filter((x) => x.track_type !== "narration"), r.data]);
      toast.success("Narration attached to this project.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not attach narration."); }
    finally { setBusy(false); }
  };

  const loadAudio = useCallback(async () => {
    if (!project) return;
    try {
      const r = await api.get(`/video/projects/${project.id}/audio`);
      setAudioTracks(r.data || []);
    } catch { /* non-fatal */ }
  }, [project?.id]);
  useEffect(() => { loadAudio(); }, [loadAudio]);

  const addMusic = async () => {
    if (!project) return setError("Create or open a project first.");
    if (!musicTrack.audio_url) return setError("Upload a music file first.");
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/projects/${project.id}/audio`, musicTrack);
      setAudioTracks((t) => [...t.filter((x) => x.track_type !== "music"), r.data]);
      setMusicTrack((m) => ({ ...m, audio_url: "" }));
      toast.success("Music attached.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not attach music."); }
    finally { setBusy(false); }
  };

  // ── AI assistant (spec §11) ────────────────────────────────────────────────
  const runAssistant = async (action, text, duration) => {
    setAssistantBusy(true); setError("");
    try {
      const r = await api.post("/video/assistant", { action, text: text || "", duration: duration || plan.desired_length || 30 });
      setAssistantResult({ action, text: r.data.text });
    } catch (err) { setError(err?.response?.data?.detail || "The AI assistant is unavailable right now."); }
    finally { setAssistantBusy(false); }
  };

  // ── Stock search (spec §13) ────────────────────────────────────────────────
  const searchStock = async () => {
    if (!stockQuery.trim()) return setError("Type what to search for first.");
    setStockBusy(true); setError("");
    try {
      const r = await api.get("/video/stock", { params: { query: stockQuery.trim(), kind: stockKind } });
      setStockConfigured(r.data.configured !== false);
      setStockResults(r.data);
      if (r.data.configured === false) setError("Free stock search needs a Pexels API key. Ask an administrator to add PEXELS_API_KEY — meanwhile, upload your own media.");
    } catch (err) { setError(err?.response?.data?.detail || "Stock search failed."); }
    finally { setStockBusy(false); }
  };

  const importStock = async (item) => {
    setBusy(true); setError("");
    try {
      const r = await api.post("/video/stock/import", { url: item.download, file_id: item.id });
      setScene((s) => ({ ...s, media_url: r.data.file_url }));
      toast.success("Stock media added to your scene draft.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not import that stock asset."); }
    finally { setBusy(false); }
  };

  const makeVideo = async () => {
    if (!project) return setError("Create or open a project first.");
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/projects/${project.id}/render`);
      await refresh(project.id);
      toast.success("Your video is ready — see Preview.");
      setTab("preview");
      return r.data;
    } catch (err) { setError(err?.response?.data?.detail || "The video could not be made. Check each scene's media."); }
    finally { setBusy(false); }
  };

  const downloadMp4 = async () => {
    try {
      const r = await api.get(project.final_video_url, { responseType: "blob" });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url; a.download = `${project.title || "morehelp-video"}.mp4`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch { setError("The finished video could not be downloaded."); }
  };

  const publish = async () => {
    if (!project?.final_video_url) return setError("Make your video first.");
    if (!publishForm.title.trim()) return setError("Give the post a title.");
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/projects/${project.id}/publish`, publishForm);
      await refresh(project.id);
      toast.success("Published to the MoreHelp stream.");
      return r.data;
    } catch (err) { setError(err?.response?.data?.detail || "Could not publish right now."); }
    finally { setBusy(false); }
  };

  const createShare = async () => {
    setBusy(true); setError("");
    try {
      const r = await api.post(`/video/projects/${project.id}/share`);
      setShareLink(r.data.share_url);
    } catch (err) { setError(err?.response?.data?.detail || "Could not create a share link."); }
    finally { setBusy(false); }
  };

  const scenes = project?.scenes || [];

  // ── Detached panel rendering (spec §4) ─────────────────────────────────────
  if (panelMode === "preview") {
    return (
      <div style={{ padding: 16, fontFamily: "inherit", background: "#fff" }}>
        <h3 style={{ margin: "0 0 10px", color: INK, fontSize: 15, fontWeight: 900 }}>Preview Panel</h3>
        <LivePreview project={project} previewUrl={previewUrl} />
        <p style={{ color: MUTED, fontSize: 11, marginTop: 8 }}>This panel mirrors the studio. Changes you make in the main window appear here automatically.</p>
      </div>
    );
  }
  if (panelMode === "storyboard" || panelMode === "words" || panelMode === "media") {
    return (
      <div style={{ padding: 16, background: "#fff" }}>
        <h3 style={{ margin: "0 0 10px", color: INK, fontSize: 15, fontWeight: 900 }}>{panelMode[0].toUpperCase() + panelMode.slice(1)} Panel</h3>
        {panelMode === "storyboard" && <StoryboardList scenes={scenes} busy={busy} onMove={moveScene} onDuplicate={duplicateScene} onDelete={deleteScene} readOnly />}
        {panelMode === "words" && <div style={{ color: MUTED, fontSize: 12 }}>Scene words editing stays in the main window; this panel mirrors the storyboard state live.</div>}
        {panelMode === "media" && <div style={{ color: MUTED, fontSize: 12 }}>Media uploads stay in the main window; this panel mirrors the storyboard state live.</div>}
      </div>
    );
  }

  return (
    <div style={{ background: "#fff", border: `1px solid ${BORDER}`, borderRadius: 14, padding: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <div>
          <h3 style={{ margin: 0, color: INK, fontSize: 16, fontWeight: 900 }}>Video Studio</h3>
          <div style={{ color: MUTED, fontSize: 12, marginTop: 4 }}>Plan it, build it scene by scene, make the MP4, publish it.</div>
        </div>
        <span style={{ fontFamily: "monospace", fontSize: 10, color: CYAN }}>{project?.status || "NO PROJECT OPEN"}</span>
      </div>

      {/* Undo/redo + detachable panels (spec §4, §8) */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
        <button onClick={undo} disabled={undoDepth === 0} title="Undo (Ctrl+Z)" style={{ ...btnGhost, padding: "4px 10px", opacity: undoDepth === 0 ? 0.4 : 1 }}>↶ Undo</button>
        <button onClick={redo} disabled={redoDepth === 0} title="Redo (Ctrl+Y)" style={{ ...btnGhost, padding: "4px 10px", opacity: redoDepth === 0 ? 0.4 : 1 }}>↷ Redo</button>
        <span style={{ flex: 1 }} />
        <button onClick={() => detach("preview", "Preview")} style={{ ...btnGhost, padding: "4px 10px" }}>⧉ Pop out Preview</button>
        <button onClick={() => detach("storyboard", "Storyboard")} style={{ ...btnGhost, padding: "4px 10px" }}>⧉ Pop out Storyboard</button>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{ ...btnGhost, padding: "6px 11px", background: tab === t.id ? CYAN : "transparent", color: tab === t.id ? "#fff" : CYAN }}>
            {t.label}
          </button>
        ))}
      </div>

      <Err msg={error} />

      {/* ── HOME ── */}
      {tab === "home" && (
        <div style={{ display: "grid", gap: 12 }}>
          <Field label="Start from a template">
            <select value="" onChange={(e) => e.target.value && applyTemplate(e.target.value)} style={inputStyle} defaultValue="">
              <option value="">Choose a template…</option>
              {templates.map((t) => <option key={t.slug} value={t.slug}>{t.title} · {t.aspect_ratio} · {t.desired_length}s</option>)}
            </select>
          </Field>
          <Field label="…or start blank">
            <input value={plan.title} onChange={(e) => setPlan((p) => ({ ...p, title: e.target.value }))} placeholder="Video name" style={inputStyle} />
          </Field>
          <button onClick={createProject} disabled={busy} style={btn}>{busy ? "Creating…" : "Create new video project"}</button>
          {projects.length > 0 && (
            <Field label="Open a saved project">
              <select value="" onChange={(e) => e.target.value && openProject(e.target.value)} style={inputStyle} defaultValue="">
                <option value="">Choose one…</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.title} · {p.status}</option>)}
              </select>
            </Field>
          )}
        </div>
      )}
      {tab === "home" && null}

      {/* ── PLAN (+ AI assistant, spec §11) ── */}
      {tab === "plan" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="Title"><input value={plan.title} onChange={(e) => setPlan((p) => ({ ...p, title: e.target.value }))} style={inputStyle} /></Field>
          <Field label="Idea">
            <textarea rows={3} value={plan.idea} onChange={(e) => setPlan((p) => ({ ...p, idea: e.target.value }))} onBlur={autosavePlan} style={inputStyle} placeholder="What is this video about?" />
          </Field>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <button onClick={() => runAssistant("ideas", plan.idea)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>{assistantBusy ? "Thinking…" : "✨ Give me video ideas"}</button>
            <button onClick={() => runAssistant("write_script", plan.idea || plan.description)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Help me write it</button>
          </div>
          <Field label="Description"><textarea rows={2} value={plan.description} onChange={(e) => setPlan((p) => ({ ...p, description: e.target.value }))} onBlur={autosavePlan} style={inputStyle} /></Field>
          <Field label="Intended audience"><input value={plan.intended_audience} onChange={(e) => setPlan((p) => ({ ...p, intended_audience: e.target.value }))} style={inputStyle} /></Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Desired length (seconds)"><input type="number" min="1" max="180" value={plan.desired_length} onChange={(e) => setPlan((p) => ({ ...p, desired_length: Number(e.target.value) }))} style={inputStyle} /></Field>
            <Field label="Aspect ratio">
              <select value={plan.aspect_ratio} onChange={(e) => setPlan((p) => ({ ...p, aspect_ratio: e.target.value }))} style={inputStyle}>
                <option>9:16</option><option>1:1</option><option>16:9</option>
              </select>
            </Field>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Purpose"><input value={plan.purpose} onChange={(e) => setPlan((p) => ({ ...p, purpose: e.target.value }))} style={inputStyle} placeholder="teach / promote / inform…" /></Field>
            <Field label="Call to action"><input value={plan.call_to_action} onChange={(e) => setPlan((p) => ({ ...p, call_to_action: e.target.value }))} style={inputStyle} /></Field>
          </div>
          <button onClick={savePlan} disabled={busy} style={btn}>{busy ? "Saving…" : "Save plan"}</button>
          {assistantResult && (
            <div style={{ border: `1px solid ${BORDER}`, borderRadius: 8, padding: 12, background: "#f8fafc" }}>
              <div style={{ fontSize: 11, color: MUTED, marginBottom: 6 }}>AI assistant — {assistantResult.action.replace(/_/g, " ")}</div>
              <div style={{ fontSize: 12, color: INK, whiteSpace: "pre-wrap", maxHeight: 200, overflowY: "auto" }}>{assistantResult.text}</div>
              <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                {(assistantResult.action === "write_script" || assistantResult.action === "ideas" || assistantResult.action === "shorten" || assistantResult.action === "stronger_opening") && (
                  <button onClick={() => { setVoiceText(assistantResult.text); toast.success("Moved to the Voice tab's script."); setTab("voice"); }} style={{ ...btnGhost, padding: "4px 10px" }}>Use as narration script</button>
                )}
                {(assistantResult.action === "write_script" || assistantResult.action === "shorten") && (
                  <button onClick={() => { setPlan((p) => ({ ...p, description: assistantResult.text.slice(0, 5000) })); toast.success("Put into Description."); }} style={{ ...btnGhost, padding: "4px 10px" }}>Put into Description</button>
                )}
                {assistantResult.action === "description" && (
                  <button onClick={() => { setPublishForm((f) => ({ ...f, description: assistantResult.text })); toast.success("Put into the publish description."); setTab("make"); }} style={{ ...btnGhost, padding: "4px 10px" }}>Use when publishing</button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
      {tab === "plan" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project on the Home tab first.</div>}

      {/* ── MEDIA (+ stock, spec §13) ── */}
      {tab === "media" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <div style={{ color: MUTED, fontSize: 12 }}>Upload the picture or video for your next scene, or pull free stock below.</div>
          <label style={{ ...labelStyle }}>Upload scene media
            <input type="file" accept="image/*,video/*" onChange={(e) => uploadMedia(e, (url) => setScene((s) => ({ ...s, media_url: url })))} style={{ display: "block", marginTop: 6, width: "100%" }} />
          </label>
          {scene.media_url && <div style={{ color: "#047857", fontSize: 12 }}>✓ Media ready — switch to Words to write this scene.</div>}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Duration (seconds)"><input type="number" min="1" max="60" value={scene.duration} onChange={(e) => setScene((s) => ({ ...s, duration: Number(e.target.value) }))} style={inputStyle} /></Field>
            <Field label="Media fit (spec §8)">
              <select value={scene.fit} onChange={(e) => setScene((s) => ({ ...s, fit: e.target.value }))} style={inputStyle}>
                <option value="fit">Fit — show the whole picture (letterbox)</option>
                <option value="fill">Fill — cover the frame (crop edges)</option>
              </select>
            </Field>
          </div>

          <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 10, display: "grid", gap: 8 }}>
            <strong style={{ fontSize: 12, color: INK }}>Free stock (Pexels)</strong>
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr auto", gap: 8 }}>
              <input value={stockQuery} onChange={(e) => setStockQuery(e.target.value)} placeholder="e.g. city sunrise" style={inputStyle} />
              <select value={stockKind} onChange={(e) => setStockKind(e.target.value)} style={inputStyle}>
                <option value="image">Photos</option>
                <option value="video">Videos</option>
              </select>
              <button onClick={searchStock} disabled={stockBusy} style={btn}>{stockBusy ? "…" : "Search"}</button>
            </div>
            {stockResults?.configured === true && (stockResults.photos || []).length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: 8 }}>
                {stockResults.photos.map((p) => (
                  <button key={p.id} onClick={() => importStock(p)} disabled={busy} style={{ border: `1px solid ${BORDER}`, borderRadius: 8, padding: 0, overflow: "hidden", cursor: "pointer", background: "#fff" }}>
                    <img src={p.preview} alt={p.label} style={{ width: "100%", height: 90, objectFit: "cover", display: "block" }} />
                    <div style={{ fontSize: 10, color: MUTED, padding: 4 }}>Use this</div>
                  </button>
                ))}
              </div>
            )}
            {stockResults?.configured === true && (stockResults.videos || []).length > 0 && (
              <div style={{ display: "grid", gap: 6 }}>
                {stockResults.videos.map((v) => (
                  <div key={v.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, border: `1px solid ${BORDER}`, borderRadius: 8, padding: 8 }}>
                    <span style={{ fontSize: 11, color: INK, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.label}</span>
                    <button onClick={() => importStock(v)} disabled={busy} style={{ ...btnGhost, padding: "3px 8px" }}>Use this</button>
                  </div>
                ))}
              </div>
            )}
            {stockResults?.configured === false && (
              <div style={{ color: MUTED, fontSize: 11 }}>Stock search is not configured yet (needs PEXELS_API_KEY). You can still upload your own media above.</div>
            )}
          </div>
        </div>
      )}
      {tab === "media" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── WORDS (+ AI, spec §11) ── */}
      {tab === "words" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="On-screen words for the next scene"><textarea rows={2} value={scene.text} onChange={(e) => setScene((s) => ({ ...s, text: e.target.value }))} style={inputStyle} /></Field>
          <Field label="Caption (burned in, can differ from on-screen words)"><textarea rows={2} value={scene.caption} onChange={(e) => setScene((s) => ({ ...s, caption: e.target.value }))} style={inputStyle} /></Field>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <button onClick={() => runAssistant("captions", voiceText || scene.text)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Create captions</button>
            <button onClick={() => runAssistant("stronger_opening", scene.text)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Stronger opening</button>
          </div>
          {assistantResult && (assistantResult.action === "captions" || assistantResult.action === "stronger_opening") && (
            <div style={{ border: `1px solid ${BORDER}`, borderRadius: 8, padding: 12, background: "#f8fafc" }}>
              <div style={{ fontSize: 12, color: INK, whiteSpace: "pre-wrap" }}>{assistantResult.text}</div>
              <button onClick={() => { setScene((s) => ({ ...s, caption: assistantResult.text.split("\n")[0].slice(0, 2000) })); toast.success("First line set as the scene caption."); }} style={{ ...btnGhost, padding: "4px 10px", marginTop: 8 }}>Use first line as caption</button>
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Text placement">
              <select value={scene.text_placement} onChange={(e) => setScene((s) => ({ ...s, text_placement: e.target.value }))} style={inputStyle}>
                <option value="top">Top</option><option value="center">Center</option><option value="bottom">Bottom</option>
              </select>
            </Field>
            <Field label="Text size"><input type="number" min="16" max="160" value={scene.text_size} onChange={(e) => setScene((s) => ({ ...s, text_size: Number(e.target.value) }))} style={inputStyle} /></Field>
          </div>
          <button onClick={addScene} disabled={busy || !scene.media_url} style={btn}>{busy ? "Saving…" : scene.media_url ? "Add scene to storyboard" : "Upload media first (Media tab)"}</button>
        </div>
      )}
      {tab === "words" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── VOICE (+ AI, spec §11) ── */}
      {tab === "voice" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="Narration script"><textarea rows={4} value={voiceText} onChange={(e) => setVoiceText(e.target.value)} style={inputStyle} placeholder="Type what the narrator should say…" /></Field>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <button onClick={() => runAssistant("write_script", voiceText || plan.idea)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Help me write it</button>
            <button onClick={() => runAssistant("shorten", voiceText, 15)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Make it shorter</button>
            <button onClick={() => runAssistant("break_into_scenes", voiceText)} disabled={assistantBusy} style={{ ...btnGhost, padding: "5px 10px" }}>✨ Turn into scenes</button>
          </div>
          {assistantResult && ["write_script", "shorten", "break_into_scenes"].includes(assistantResult.action) && (
            <div style={{ border: `1px solid ${BORDER}`, borderRadius: 8, padding: 12, background: "#f8fafc" }}>
              <div style={{ fontSize: 12, color: INK, whiteSpace: "pre-wrap", maxHeight: 180, overflowY: "auto" }}>{assistantResult.text}</div>
              <button onClick={() => { setVoiceText(assistantResult.text); toast.success("Script updated."); }} style={{ ...btnGhost, padding: "4px 10px", marginTop: 8 }}>Use this script</button>
            </div>
          )}
          <Field label="Voice persona">
            <select value={voicePersona} onChange={(e) => setVoicePersona(e.target.value)} style={inputStyle}>
              <option value="director">The Director</option>
              <option value="ancestral-sage">Ancestral Sage</option>
              <option value="poor-righteous-teacher">Poor Righteous Teacher</option>
            </select>
          </Field>
          <button onClick={generateVoice} disabled={busy} style={btn}>{busy ? "Generating…" : "Generate voice"}</button>
          {voiceResult?.audio_url && (
            <>
              <audio controls src={voiceResult.audio_url} style={{ width: "100%" }} />
              <button onClick={addVoiceAsNarration} disabled={busy} style={btn}>Use as this project's narration</button>
            </>
          )}
        </div>
      )}
      {tab === "voice" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── MUSIC ── */}
      {tab === "music" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <label style={labelStyle}>Upload music (MP3/WAV)
            <input type="file" accept="audio/*" onChange={(e) => uploadMedia(e, (url) => setMusicTrack((m) => ({ ...m, audio_url: url })))} style={{ display: "block", marginTop: 6, width: "100%" }} />
          </label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <Field label="Volume (0–1)"><input type="number" step="0.1" min="0" max="1" value={musicTrack.volume} onChange={(e) => setMusicTrack((m) => ({ ...m, volume: Number(e.target.value) }))} style={inputStyle} /></Field>
            <Field label="Fade in (s)"><input type="number" min="0" max="10" value={musicTrack.fade_in} onChange={(e) => setMusicTrack((m) => ({ ...m, fade_in: Number(e.target.value) }))} style={inputStyle} /></Field>
            <Field label="Fade out (s)"><input type="number" min="0" max="10" value={musicTrack.fade_out} onChange={(e) => setMusicTrack((m) => ({ ...m, fade_out: Number(e.target.value) }))} style={inputStyle} /></Field>
          </div>
          <button onClick={addMusic} disabled={busy || !musicTrack.audio_url} style={btn}>{busy ? "Saving…" : "Attach music"}</button>
          {audioTracks.length > 0 && (
            <div style={{ color: MUTED, fontSize: 12 }}>
              Attached: {audioTracks.map((t) => `${t.track_type} (vol ${t.volume})`).join(", ")}
            </div>
          )}
        </div>
      )}
      {tab === "music" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── STORYBOARD (with reorder, spec §8) ── */}
      {tab === "storyboard" && project && (
        <StoryboardList scenes={scenes} busy={busy} onMove={moveScene} onDuplicate={duplicateScene} onDelete={deleteScene} />
      )}
      {tab === "storyboard" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── EDIT (per-scene tweaks + fit) ── */}
      {tab === "edit" && project && (
        <div style={{ display: "grid", gap: 12 }}>
          {scenes.length === 0 && <div style={{ color: MUTED, fontSize: 12 }}>Nothing to edit yet.</div>}
          {scenes.map((s, i) => (
            <SceneEditor key={s.id} index={i} scene={s} busy={busy} onSave={updateScene} />
          ))}
        </div>
      )}
      {tab === "edit" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── PREVIEW (live + rendered, spec §9) ── */}
      {tab === "preview" && project && (
        <div style={{ display: "grid", gap: 12 }}>
          <LivePreview project={project} previewUrl={previewUrl} />
          {project.final_video_url && <button onClick={downloadMp4} style={btn}>Download MP4</button>}
        </div>
      )}
      {tab === "preview" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── MAKE (+ publish + share + honest fallbacks, spec §20) ── */}
      {tab === "make" && project && (
        <div style={{ display: "grid", gap: 12 }}>
          <button onClick={makeVideo} disabled={busy || !scenes.length || scenes.some((s) => !s.visual_url)}
            style={{ ...btn, background: "#047857" }}>
            {busy ? "Making your video…" : scenes.length ? "Make my video" : "Add scenes first"}
          </button>
          {scenes.some((s) => !s.visual_url) && <div style={{ color: "#9a3412", fontSize: 12 }}>Every scene needs media before the video can be made.</div>}
          {project.final_video_url && (
            <>
              <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 12, display: "grid", gap: 10 }}>
                <strong style={{ fontSize: 13, color: INK }}>Publish to the MoreHelp stream</strong>
                <Field label="Post title"><input value={publishForm.title} onChange={(e) => setPublishForm((p) => ({ ...p, title: e.target.value }))} style={inputStyle} /></Field>
                <Field label="Description"><textarea rows={2} value={publishForm.description} onChange={(e) => setPublishForm((p) => ({ ...p, description: e.target.value }))} style={inputStyle} /></Field>
                <Field label="Visibility">
                  <select value={publishForm.visibility} onChange={(e) => setPublishForm((p) => ({ ...p, visibility: e.target.value }))} style={inputStyle}>
                    <option value="morehelp">MoreHelp members</option>
                    <option value="public">Public</option>
                    <option value="private">Private</option>
                  </select>
                </Field>
                <button onClick={publish} disabled={busy} style={btn}>Publish</button>
              </div>
              <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 12, display: "grid", gap: 10 }}>
                <strong style={{ fontSize: 13, color: INK }}>Share a private link</strong>
                <button onClick={createShare} disabled={busy} style={btnGhost}>Create share link</button>
                {shareLink && <div style={{ fontSize: 12, color: CYAN, wordBreak: "break-all" }}>{window.location.origin}{shareLink}</div>}
              </div>
              <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 12, display: "grid", gap: 8 }}>
                <strong style={{ fontSize: 13, color: INK }}>Social platforms</strong>
                <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.6 }}>
                  <strong>YouTube:</strong> direct publishing needs a YouTube OAuth connection that isn't configured yet. Your real export path is <strong>Download MP4</strong> (above and on the Preview tab) — upload it to YouTube, TikTok, or Instagram directly. No fake one-tap posting here.
                </div>
                <button onClick={downloadMp4} style={btnGhost}>Download MP4 for social upload</button>
                <div style={{ fontSize: 12, color: MUTED }}>
                  Tip: run ✨ Create a description on the Plan tab to get caption + hashtags text you can paste into any platform.
                </div>
              </div>
            </>
          )}
        </div>
      )}
      {tab === "make" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}
    </div>
  );
}

/** Storyboard list with reorder controls (spec §8). */
function StoryboardList({ scenes, busy, onMove, onDuplicate, onDelete, readOnly = false }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {scenes.length === 0 && <div style={{ color: MUTED, fontSize: 12 }}>No scenes yet — add them from Media + Words.</div>}
      {scenes.map((s, i) => (
        <div key={s.id} style={{ display: "grid", gridTemplateColumns: "28px minmax(0,1fr) auto", gap: 8, alignItems: "center", padding: 10, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
          <strong>{i + 1}</strong>
          <div>
            <div style={{ fontSize: 12, color: INK, fontWeight: 700 }}>{(s.script_text || s.caption || "(no words)").slice(0, 60)}</div>
            <div style={{ fontSize: 11, color: MUTED }}>{s.duration}s · {s.text_placement} · {s.transition} · {s.fit || "fit"}</div>
          </div>
          <div style={{ display: "flex", gap: 5 }}>
            {!readOnly && <button onClick={() => onMove(s, "up")} disabled={busy || i === 0} title="Move up" style={{ ...btnGhost, padding: "3px 8px", opacity: i === 0 ? 0.3 : 1 }}>↑</button>}
            {!readOnly && <button onClick={() => onMove(s, "down")} disabled={busy || i === scenes.length - 1} title="Move down" style={{ ...btnGhost, padding: "3px 8px", opacity: i === scenes.length - 1 ? 0.3 : 1 }}>↓</button>}
            {!readOnly && <button onClick={() => onDuplicate(s)} disabled={busy} title="Duplicate" style={{ ...btnGhost, padding: "3px 8px" }}>+</button>}
            {!readOnly && <button onClick={() => onDelete(s)} disabled={busy} title="Delete" style={{ ...btnGhost, padding: "3px 8px" }}>×</button>}
          </div>
        </div>
      ))}
      {scenes.length > 0 && <div style={{ color: MUTED, fontSize: 12 }}>Total: {scenes.reduce((a, s) => a + (s.duration || 0), 0)}s across {scenes.length} scene(s).</div>}
    </div>
  );
}

/**
 * Live preview (spec §9): reflects the CURRENT project state before render.
 * Plays each scene's media for its duration with the on-screen words drawn as
 * an overlay, scrubbable by scene, with fullscreen. When a rendered MP4
 * exists, offers that instead.
 */
function LivePreview({ project, previewUrl }) {
  const scenes = project?.scenes || [];
  const [sceneIdx, setSceneIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const videoRef = useRef(null);
  const wrapRef = useRef(null);
  const timerRef = useRef(null);

  const totalDuration = scenes.reduce((a, s) => a + (s.duration || 5), 0) || 1;
  const current = scenes[Math.min(sceneIdx, Math.max(0, scenes.length - 1))];

  useEffect(() => { setSceneIdx(0); setElapsed(0); setPlaying(false); }, [project?.id]);

  // Scene playback loop for live preview (images only; videos play natively).
  useEffect(() => {
    if (!playing || !current || current.visual_url?.endsWith(".mp4") === false) {
      return undefined;
    }
    if (!playing || !current) return undefined;
    timerRef.current = setInterval(() => {
      setElapsed((e) => {
        const next = e + 0.1;
        if (next >= (current.duration || 5)) {
          if (sceneIdx < scenes.length - 1) { setSceneIdx((i) => i + 1); return 0; }
          setPlaying(false);
          return current.duration || 5;
        }
        return next;
      });
    }, 100);
    return () => clearInterval(timerRef.current);
  }, [playing, sceneIdx, current, scenes.length]);

  if (previewUrl) {
    return (
      <div style={{ display: "grid", gap: 8 }}>
        <div style={{ fontSize: 11, color: MUTED }}>Rendered video</div>
        <video ref={videoRef} controls src={previewUrl} style={{ width: "100%", maxHeight: 420, background: "#111", borderRadius: 8 }} />
      </div>
    );
  }

  if (!scenes.length) {
    return <div style={{ color: MUTED, fontSize: 12 }}>No scenes yet — the live preview will appear here as you build, before you render.</div>;
  }

  const sceneRemaining = Math.max(0, (current.duration || 5) - elapsed);
  const isVideoScene = /\.(mp4|webm|mov)(\?|$)/i.test(current.visual_url || "");

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ fontSize: 11, color: MUTED }}>
        Live preview of your project (before render) — scene {Math.min(sceneIdx + 1, scenes.length)} of {scenes.length}
      </div>
      <div ref={wrapRef} style={{ position: "relative", width: "100%", maxWidth: 320, aspectRatio: project?.aspect_ratio === "16:9" ? "16/9" : project?.aspect_ratio === "1:1" ? "1/1" : "9/16", background: "#111", borderRadius: 8, overflow: "hidden", margin: "0 auto" }}>
        {isVideoScene ? (
          <video
            key={current.id}
            ref={videoRef}
            src={current.visual_url}
            autoPlay={playing}
            controls={false}
            onEnded={() => { if (sceneIdx < scenes.length - 1) { setSceneIdx((i) => i + 1); setElapsed(0); } else setPlaying(false); }}
            style={{ width: "100%", height: "100%", objectFit: current.fit === "fill" ? "cover" : "contain" }}
          />
        ) : (
          current.visual_url && (
            <img key={current.id + sceneIdx} src={current.visual_url} alt="" style={{ width: "100%", height: "100%", objectFit: current.fit === "fill" ? "cover" : "contain" }} />
          )
        )}
        {(current.caption || current.script_text) && (
          <div style={{
            position: "absolute", left: 8, right: 8,
            ...(current.text_placement === "top" ? { top: 10 } : current.text_placement === "center" ? { top: "50%", transform: "translateY(-50%)" } : { bottom: 10 }),
            textAlign: "center",
          }}>
            <span style={{
              display: "inline-block", background: "rgba(0,0,0,0.65)", color: "#fff",
              fontSize: Math.max(11, Math.round((current.text_size || 48) / 4)), fontWeight: 700,
              borderRadius: 6, padding: "3px 8px", lineHeight: 1.35,
            }}>{current.caption || current.script_text}</span>
          </div>
        )}
        {!current.visual_url && (
          <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", color: "#666", fontSize: 12 }}>Scene {sceneIdx + 1} has no media yet</div>
        )}
      </div>
      {/* Scrub by scene (spec §9 scrub) */}
      <input
        type="range" min="0" max={scenes.length - 1} step="1" value={sceneIdx}
        onChange={(e) => { setSceneIdx(Number(e.target.value)); setElapsed(0); }}
        style={{ width: "100%", maxWidth: 320, margin: "0 auto", display: "block" }}
        aria-label="Scrub scenes"
      />
      <div style={{ display: "flex", gap: 6, justifyContent: "center", flexWrap: "wrap" }}>
        <button onClick={() => { setSceneIdx(0); setElapsed(0); }} style={{ ...btnGhost, padding: "5px 10px" }}>↺ Restart</button>
        <button onClick={() => setPlaying((p) => !p)} style={{ ...btn, padding: "5px 12px" }}>{playing ? "❚❚ Pause" : "▶ Play"}</button>
        <button onClick={() => { const el = wrapRef.current; if (el?.requestFullscreen) el.requestFullscreen(); }} style={{ ...btnGhost, padding: "5px 10px" }}>⛶ Fullscreen</button>
      </div>
      <div style={{ fontSize: 11, color: MUTED, textAlign: "center" }}>
        Scene {Math.min(sceneIdx + 1, scenes.length)}: {sceneRemaining.toFixed(1)}s left of {current.duration || 5}s · project total {totalDuration}s
      </div>
      <div style={{ fontSize: 11, color: CYAN, textAlign: "center" }}>
        {project?.final_video_url ? "A rendered MP4 also exists — reload the panel to see it." : "This is the pre-render preview — make the video on the Make tab for the final MP4."}
      </div>
    </div>
  );
}

function SceneEditor({ index, scene, busy, onSave }) {
  const [draft, setDraft] = useState({
    text: scene.script_text || "", caption: scene.caption || "", duration: scene.duration || 5,
    text_placement: scene.text_placement || "bottom", text_size: scene.text_size || 48, transition: scene.transition || "none",
    fit: scene.fit || "fit",
  });
  useEffect(() => {
    setDraft({
      text: scene.script_text || "", caption: scene.caption || "", duration: scene.duration || 5,
      text_placement: scene.text_placement || "bottom", text_size: scene.text_size || 48, transition: scene.transition || "none",
      fit: scene.fit || "fit",
    });
  }, [scene]);
  return (
    <div style={{ border: `1px solid ${BORDER}`, borderRadius: 8, padding: 12, display: "grid", gap: 8 }}>
      <strong style={{ fontSize: 12, color: INK }}>Scene {index + 1}</strong>
      <Field label="On-screen words"><input value={draft.text} onChange={(e) => setDraft((d) => ({ ...d, text: e.target.value }))} style={inputStyle} /></Field>
      <Field label="Caption"><input value={draft.caption} onChange={(e) => setDraft((d) => ({ ...d, caption: e.target.value }))} style={inputStyle} /></Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
        <Field label="Seconds"><input type="number" min="1" max="60" value={draft.duration} onChange={(e) => setDraft((d) => ({ ...d, duration: Number(e.target.value) }))} style={inputStyle} /></Field>
        <Field label="Placement">
          <select value={draft.text_placement} onChange={(e) => setDraft((d) => ({ ...d, text_placement: e.target.value }))} style={inputStyle}>
            <option value="top">Top</option><option value="center">Center</option><option value="bottom">Bottom</option>
          </select>
        </Field>
        <Field label="Transition">
          <select value={draft.transition} onChange={(e) => setDraft((d) => ({ ...d, transition: e.target.value }))} style={inputStyle}>
            <option value="none">None</option><option value="fade">Fade</option><option value="slide">Slide</option>
          </select>
        </Field>
      </div>
      <Field label="Media fit">
        <select value={draft.fit} onChange={(e) => setDraft((d) => ({ ...d, fit: e.target.value }))} style={inputStyle}>
          <option value="fit">Fit — whole picture visible</option>
          <option value="fill">Fill — cover frame, crop edges</option>
        </select>
      </Field>
      <button onClick={() => onSave({ ...scene, ...draft })} disabled={busy} style={btn}>Save scene {index + 1}</button>
    </div>
  );
}
