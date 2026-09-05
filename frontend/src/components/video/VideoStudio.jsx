/**
 * VideoStudio — the full tabbed Video Studio panel for Creator Studio.
 *
 * Tabs: Home / Plan / Media / Words / Voice / Music / Storyboard / Edit /
 * Preview / Make — each wired to a real backend API on /api/video/*.
 * Nothing here is a mock: every action persists through the studio router.
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

function Field({ label, children }) {
  return <label style={{ display: "block" }}><span style={labelStyle}>{label}</span>{children}</label>;
}

function Err({ msg }) {
  if (!msg) return null;
  return <div role="alert" style={{ color: "#9a3412", background: "#fff7ed", border: "1px solid #fdba74", borderRadius: 8, padding: 10, fontSize: 12 }}>{msg}</div>;
}

export default function VideoStudio({ user }) {
  const [tab, setTab] = useState("home");
  const [projects, setProjects] = useState([]);
  const [project, setProject] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");

  // Plan fields
  const [plan, setPlan] = useState({ title: "", idea: "", description: "", intended_audience: "", desired_length: 30, purpose: "", call_to_action: "", aspect_ratio: "9:16" });
  // Scene draft
  const [scene, setScene] = useState({ media_url: "", text: "", duration: 5, text_placement: "bottom", text_size: 48, caption: "", transition: "none" });
  // Voice / music
  const [voiceText, setVoiceText] = useState("");
  const [voicePersona, setVoicePersona] = useState("director");
  const [voiceResult, setVoiceResult] = useState(null);
  const [audioTracks, setAudioTracks] = useState([]);
  const [musicTrack, setMusicTrack] = useState({ track_type: "music", audio_url: "", volume: 0.6, fade_in: 1, fade_out: 2 });
  const [publishForm, setPublishForm] = useState({ title: "", description: "", visibility: "morehelp" });
  const [shareLink, setShareLink] = useState("");

  const refresh = useCallback(async (id) => {
    const r = await api.get(`/video/projects/${id}`);
    setProject(r.data);
    setPlan({
      title: r.data.title || "", idea: r.data.idea || "", description: r.data.description || "",
      intended_audience: r.data.intended_audience || "", desired_length: r.data.desired_length || 30,
      purpose: r.data.purpose || "", call_to_action: r.data.call_to_action || "", aspect_ratio: r.data.aspect_ratio || "9:16",
    });
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [p, t] = await Promise.all([api.get("/video/projects"), api.get("/video/templates")]);
      setProjects(p.data || []);
      setTemplates(t.data || []);
    } catch (err) { setError(err?.response?.data?.detail || "Could not load your video projects."); }
  }, []);
  useEffect(() => { loadAll(); }, [loadAll]);

  // Preview via authenticated blob
  useEffect(() => {
    let objectUrl = "";
    if (!project?.final_video_url) { setPreviewUrl(""); return undefined; }
    api.get(project.final_video_url, { responseType: "blob", skipGenericErrorToast: true })
      .then((r) => { objectUrl = URL.createObjectURL(r.data); setPreviewUrl(objectUrl); })
      .catch(() => setError("Your finished video could not be previewed. Try Make again."));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [project?.final_video_url]);

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
      const r = await api.patch(`/video/projects/${project.id}`, { ...plan, title: plan.title.trim() });
      setProject((c) => ({ ...c, ...r.data }));
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
      const r = await api.post(`/video/projects/${project.id}/scenes`, {
        media_url: scene.media_url, text: scene.text, duration: scene.duration,
        position: (project.scenes || []).length, text_placement: scene.text_placement,
        text_size: scene.text_size, caption: scene.caption || null, transition: scene.transition,
      });
      setProject((c) => ({ ...c, scenes: [...(c.scenes || []), r.data], status: "Ready to Preview" }));
      setScene((s) => ({ ...s, text: "", caption: "", media_url: "" }));
      toast.success("Scene added.");
    } catch (err) { setError(err?.response?.data?.detail || "Could not add that scene."); }
    finally { setBusy(false); }
  };

  const updateScene = async (updated) => {
    setBusy(true); setError("");
    try {
      const r = await api.patch(`/video/projects/${project.id}/scenes/${updated.id}`, {
        media_url: updated.visual_url, text: updated.script_text || "", duration: updated.duration,
        position: updated.scene_order, text_placement: updated.text_placement, text_size: updated.text_size,
        caption: updated.caption || null, transition: updated.transition,
      });
      setProject((c) => ({ ...c, scenes: c.scenes.map((s) => (s.id === updated.id ? r.data : s)) }));
    } catch (err) { setError(err?.response?.data?.detail || "Could not update that scene."); }
    finally { setBusy(false); }
  };

  const duplicateScene = async (s) => {
    try {
      const r = await api.post(`/video/projects/${project.id}/scenes/${s.id}/duplicate`);
      setProject((c) => ({ ...c, scenes: [...c.scenes, r.data] }));
    } catch (err) { setError(err?.response?.data?.detail || "Could not duplicate that scene."); }
  };

  const deleteScene = async (s) => {
    try {
      await api.delete(`/video/projects/${project.id}/scenes/${s.id}`);
      setProject((c) => ({ ...c, scenes: c.scenes.filter((x) => x.id !== s.id) }));
    } catch (err) { setError(err?.response?.data?.detail || "Could not delete that scene."); }
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

  return (
    <div style={{ background: "#fff", border: `1px solid ${BORDER}`, borderRadius: 14, padding: 18 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <div>
          <h3 style={{ margin: 0, color: INK, fontSize: 16, fontWeight: 900 }}>Video Studio</h3>
          <div style={{ color: MUTED, fontSize: 12, marginTop: 4 }}>Plan it, build it scene by scene, make the MP4, publish it.</div>
        </div>
        <span style={{ fontFamily: "monospace", fontSize: 10, color: CYAN }}>{project?.status || "NO PROJECT OPEN"}</span>
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

      {/* ── PLAN ── */}
      {tab === "plan" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="Title"><input value={plan.title} onChange={(e) => setPlan((p) => ({ ...p, title: e.target.value }))} style={inputStyle} /></Field>
          <Field label="Idea"><textarea rows={3} value={plan.idea} onChange={(e) => setPlan((p) => ({ ...p, idea: e.target.value }))} onBlur={autosavePlan} style={inputStyle} placeholder="What is this video about?" /></Field>
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
        </div>
      )}
      {tab === "plan" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project on the Home tab first.</div>}

      {/* ── MEDIA (scene draft upload) ── */}
      {tab === "media" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <div style={{ color: MUTED, fontSize: 12 }}>Upload the picture or video for your next scene, then fill in its words on the Words tab.</div>
          <label style={{ ...labelStyle }}>Upload scene media
            <input type="file" accept="image/*,video/*" onChange={(e) => uploadMedia(e, (url) => setScene((s) => ({ ...s, media_url: url })))} style={{ display: "block", marginTop: 6, width: "100%" }} />
          </label>
          {scene.media_url && <div style={{ color: "#047857", fontSize: 12 }}>✓ Media ready — switch to Words to write this scene.</div>}
          <Field label="Duration (seconds)"><input type="number" min="1" max="60" value={scene.duration} onChange={(e) => setScene((s) => ({ ...s, duration: Number(e.target.value) }))} style={inputStyle} /></Field>
        </div>
      )}
      {tab === "media" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── WORDS ── */}
      {tab === "words" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="On-screen words for the next scene"><textarea rows={2} value={scene.text} onChange={(e) => setScene((s) => ({ ...s, text: e.target.value }))} style={inputStyle} /></Field>
          <Field label="Caption (burned in, can differ from on-screen words)"><textarea rows={2} value={scene.caption} onChange={(e) => setScene((s) => ({ ...s, caption: e.target.value }))} style={inputStyle} /></Field>
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

      {/* ── VOICE ── */}
      {tab === "voice" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          <Field label="Narration script"><textarea rows={4} value={voiceText} onChange={(e) => setVoiceText(e.target.value)} style={inputStyle} placeholder="Type what the narrator should say…" /></Field>
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

      {/* ── STORYBOARD ── */}
      {tab === "storyboard" && project && (
        <div style={{ display: "grid", gap: 8 }}>
          {scenes.length === 0 && <div style={{ color: MUTED, fontSize: 12 }}>No scenes yet — add them from Media + Words.</div>}
          {scenes.map((s, i) => (
            <div key={s.id} style={{ display: "grid", gridTemplateColumns: "28px minmax(0,1fr) auto", gap: 8, alignItems: "center", padding: 10, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
              <strong>{i + 1}</strong>
              <div>
                <div style={{ fontSize: 12, color: INK, fontWeight: 700 }}>{(s.script_text || s.caption || "(no words)").slice(0, 60)}</div>
                <div style={{ fontSize: 11, color: MUTED }}>{s.duration}s · {s.text_placement} · {s.transition}</div>
              </div>
              <div style={{ display: "flex", gap: 5 }}>
                <button onClick={() => duplicateScene(s)} disabled={busy} title="Duplicate" style={{ ...btnGhost, padding: "3px 8px" }}>+</button>
                <button onClick={() => deleteScene(s)} disabled={busy} title="Delete" style={{ ...btnGhost, padding: "3px 8px" }}>×</button>
              </div>
            </div>
          ))}
          {scenes.length > 0 && <div style={{ color: MUTED, fontSize: 12 }}>Total: {scenes.reduce((a, s) => a + (s.duration || 0), 0)}s across {scenes.length} scene(s).</div>}
        </div>
      )}
      {tab === "storyboard" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── EDIT (per-scene tweaks) ── */}
      {tab === "edit" && project && (
        <div style={{ display: "grid", gap: 12 }}>
          {scenes.length === 0 && <div style={{ color: MUTED, fontSize: 12 }}>Nothing to edit yet.</div>}
          {scenes.map((s, i) => (
            <SceneEditor key={s.id} index={i} scene={s} busy={busy} onSave={updateScene} />
          ))}
        </div>
      )}
      {tab === "edit" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── PREVIEW ── */}
      {tab === "preview" && project && (
        <div style={{ display: "grid", gap: 10 }}>
          {previewUrl ? <video controls src={previewUrl} style={{ width: "100%", maxHeight: 420, background: "#111", borderRadius: 8 }} />
            : <div style={{ color: MUTED, fontSize: 12 }}>No finished video yet — go to Make.</div>}
          {project.final_video_url && <button onClick={downloadMp4} style={btn}>Download MP4</button>}
        </div>
      )}
      {tab === "preview" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}

      {/* ── MAKE (+ publish + share) ── */}
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
            </>
          )}
        </div>
      )}
      {tab === "make" && !project && <div style={{ color: MUTED, fontSize: 12 }}>Create or open a project first.</div>}
    </div>
  );
}

function SceneEditor({ index, scene, busy, onSave }) {
  const [draft, setDraft] = useState({
    text: scene.script_text || "", caption: scene.caption || "", duration: scene.duration || 5,
    text_placement: scene.text_placement || "bottom", text_size: scene.text_size || 48, transition: scene.transition || "none",
  });
  useEffect(() => {
    setDraft({ text: scene.script_text || "", caption: scene.caption || "", duration: scene.duration || 5, text_placement: scene.text_placement || "bottom", text_size: scene.text_size || 48, transition: scene.transition || "none" });
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
      <button onClick={() => onSave({ ...scene, ...draft })} disabled={busy} style={btn}>Save scene {index + 1}</button>
    </div>
  );
}
