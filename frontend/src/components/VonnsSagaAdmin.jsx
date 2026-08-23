/**
 * VonnsSagaAdmin.jsx — Admin/Exec panel for VonnsSaga
 * 
 * Features:
 * - Upload tracks for $1 sale with 33-second preview limit
 * - Add images to saga pages
 * - Create short-form videos (image animation + soundtrack)
 * 
 * Access: admin/exec only (role-gated)
 */

import { useState, useRef, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { toast } from "sonner";
import {
  Upload, Music, Image, Video, DollarSign, Clock, Play, Pause,
  Trash2, Plus, Save, Eye, EyeOff, CheckCircle, Loader2, X
} from "lucide-react";

const C = {
  bg: "#0d0721",
  panel: "rgba(255,255,255,0.045)",
  panelLine: "rgba(233,180,97,0.22)",
  gold: "#E8A51E",
  purple: "#b78aff",
  ink: "#f3ecff",
  muted: "#b8a8d9",
  dim: "#8a78b5",
  danger: "#ff4444",
  success: "#4ade80",
};

const MAX_PREVIEW_SECONDS = 33;
const TRACK_PRICE_CENTS = 100; // $1.00

// ── Track Upload Section ──────────────────────────────────────────────────────
function TrackUpload({ onUpload }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [trimStart, setTrimStart] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);
  const fileRef = useRef(null);

  const handleFile = useCallback((e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.type.startsWith("audio/")) {
      toast.error("Please select an audio file");
      return;
    }
    setFile(f);
    setTitle(f.name.replace(/\.[^.]+$/, ""));
    
    const url = URL.createObjectURL(f);
    const audio = new Audio(url);
    audio.onloadedmetadata = () => {
      setDuration(audio.duration);
      if (audio.duration > MAX_PREVIEW_SECONDS) {
        toast.info(`Track is ${audio.duration.toFixed(1)}s — preview will be trimmed to ${MAX_PREVIEW_SECONDS}s`);
      }
    };
    audio.src = url;
    setPreview(url);
  }, []);

  const playPreview = useCallback(() => {
    if (!preview) return;
    const audio = new Audio(preview);
    audioRef.current = audio;
    audio.currentTime = trimStart;
    audio.ondurationupdate = () => {
      if (audio.currentTime >= trimStart + MAX_PREVIEW_SECONDS) {
        audio.pause();
        toast.info("Preview limit reached (33 seconds)");
      }
    };
    audio.play();
  }, [preview, trimStart]);

  const stopPreview = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
  }, []);

  const handleSave = async () => {
    if (!file || !title.trim()) {
      toast.error("Select a file and enter a title");
      return;
    }
    setSaving(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title.trim());
      formData.append("price_cents", TRACK_PRICE_CENTS);
      formData.append("preview_start", trimStart);
      formData.append("preview_duration", Math.min(duration, MAX_PREVIEW_SECONDS));
      formData.append("duration_seconds", duration || 0);
      formData.append("type", "track");
      
      await api.post("/saga/tracks", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      toast.success(`"${title}" uploaded — $1.00, ${MAX_PREVIEW_SECONDS}s preview`);
      setFile(null);
      setPreview(null);
      setTitle("");
      setDuration(0);
      setTrimStart(0);
      onUpload?.();
    } catch (e) {
      toast.error("Upload failed: " + (e?.message || "unknown error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ background: C.panel, border: `1px solid ${C.panelLine}`, borderRadius: 16, padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <Music style={{ width: 18, height: 18, color: C.gold }} />
        <div>
          <div style={{ fontSize: 10, fontWeight: 900, textTransform: "uppercase", letterSpacing: "0.2em", color: C.gold }}>
            Upload Track for Sale
          </div>
          <div style={{ fontSize: 11, color: C.muted }}>
            33-second preview · $1.00 per download
          </div>
        </div>
      </div>

      {/* File input */}
      <div
        onClick={() => fileRef.current?.click()}
        style={{
          border: `2px dashed ${file ? C.gold : C.panelLine}`,
          borderRadius: 12,
          padding: "24px 16px",
          textAlign: "center",
          cursor: "pointer",
          marginBottom: 16,
          background: file ? "rgba(232,165,30,0.05)" : "transparent",
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="audio/*"
          onChange={handleFile}
          style={{ display: "none" }}
        />
        {file ? (
          <div>
            <Music style={{ width: 24, height: 24, color: C.gold, margin: "0 auto 8px" }} />
            <div style={{ fontSize: 13, color: C.ink, fontWeight: 700 }}>{file.name}</div>
            <div style={{ fontSize: 11, color: C.muted }}>
              {duration.toFixed(1)}s · ${TRACK_PRICE_CENTS / 100}.00
              {duration > MAX_PREVIEW_SECONDS && ` · Preview trimmed to ${MAX_PREVIEW_SECONDS}s`}
            </div>
          </div>
        ) : (
          <div>
            <Upload style={{ width: 24, height: 24, color: C.muted, margin: "0 auto 8px" }} />
            <div style={{ fontSize: 12, color: C.muted }}>Click to select audio file</div>
          </div>
        )}
      </div>

      {/* Title */}
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Track title"
        style={{
          width: "100%", padding: "10px 14px", borderRadius: 8,
          border: `1px solid ${C.panelLine}`, background: "rgba(0,0,0,0.3)",
          color: C.ink, fontSize: 13, marginBottom: 12, outline: "none",
          fontFamily: "inherit",
        }}
      />

      {/* Trim controls */}
      {duration > MAX_PREVIEW_SECONDS && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 6 }}>
            Preview start: {trimStart.toFixed(1)}s — {(trimStart + MAX_PREVIEW_SECONDS).toFixed(1)}s
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(0, duration - MAX_PREVIEW_SECONDS)}
            step={0.1}
            value={trimStart}
            onChange={(e) => setTrimStart(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: C.gold }}
          />
        </div>
      )}

      {/* Preview + Save */}
      <div style={{ display: "flex", gap: 8 }}>
        {preview && (
          <>
            <button
              onClick={playPreview}
              style={{
                flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                padding: "10px", borderRadius: 8, border: `1px solid ${C.panelLine}`,
                background: "transparent", color: C.ink, fontSize: 12, fontWeight: 700, cursor: "pointer",
              }}
            >
              <Play style={{ width: 14, height: 14 }} /> Preview
            </button>
            <button
              onClick={stopPreview}
              style={{
                padding: "10px 14px", borderRadius: 8, border: `1px solid ${C.panelLine}`,
                background: "transparent", color: C.muted, cursor: "pointer",
              }}
            >
              <Pause style={{ width: 14, height: 14 }} />
            </button>
          </>
        )}
        <button
          onClick={handleSave}
          disabled={saving || !file}
          style={{
            flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            padding: "10px", borderRadius: 8, border: "none",
            background: C.gold, color: "#1a1033", fontSize: 12, fontWeight: 900, cursor: "pointer",
            opacity: saving || !file ? 0.5 : 1,
          }}
        >
          {saving ? <Loader2 style={{ width: 14, height: 14, animation: "spin 1s linear infinite" }} /> : <Save style={{ width: 14, height: 14 }} />}
          Upload · $1.00
        </button>
      </div>
    </div>
  );
}

// ── Image Upload Section ──────────────────────────────────────────────────────
function ImageUpload({ nodeId, onUpload }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [caption, setCaption] = useState("");
  const [saving, setSaving] = useState(false);
  const fileRef = useRef(null);

  const handleFile = useCallback((e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const handleSave = async () => {
    if (!file) {
      toast.error("Select an image");
      return;
    }
    setSaving(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("node_id", nodeId || "general");
      formData.append("caption", caption.trim());
      
      await api.post("/saga/images", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      toast.success("Image added to saga");
      setFile(null);
      setPreview(null);
      setCaption("");
      onUpload?.();
    } catch (e) {
      toast.error("Upload failed: " + (e?.message || "unknown error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ background: C.panel, border: `1px solid ${C.panelLine}`, borderRadius: 16, padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <Image style={{ width: 18, height: 18, color: C.purple }} />
        <div>
          <div style={{ fontSize: 10, fontWeight: 900, textTransform: "uppercase", letterSpacing: "0.2em", color: C.purple }}>
            Add Image to Saga
          </div>
          <div style={{ fontSize: 11, color: C.muted }}>
            {nodeId ? `Scene: ${nodeId}` : "General saga image"}
          </div>
        </div>
      </div>

      {/* File input */}
      <div
        onClick={() => fileRef.current?.click()}
        style={{
          border: `2px dashed ${file ? C.purple : C.panelLine}`,
          borderRadius: 12,
          padding: "16px",
          textAlign: "center",
          cursor: "pointer",
          marginBottom: 12,
          background: file ? "rgba(183,138,255,0.05)" : "transparent",
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          onChange={handleFile}
          style={{ display: "none" }}
        />
        {preview ? (
          <img src={preview} alt="Preview" style={{ maxHeight: 120, borderRadius: 8, objectFit: "contain" }} />
        ) : (
          <div>
            <Image style={{ width: 24, height: 24, color: C.muted, margin: "0 auto 8px" }} />
            <div style={{ fontSize: 12, color: C.muted }}>Click to select image</div>
          </div>
        )}
      </div>

      {/* Caption */}
      <input
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
        placeholder="Image caption (optional)"
        style={{
          width: "100%", padding: "8px 12px", borderRadius: 8,
          border: `1px solid ${C.panelLine}`, background: "rgba(0,0,0,0.3)",
          color: C.ink, fontSize: 12, marginBottom: 12, outline: "none",
          fontFamily: "inherit",
        }}
      />

      <button
        onClick={handleSave}
        disabled={saving || !file}
        style={{
          width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
          padding: "10px", borderRadius: 8, border: "none",
          background: C.purple, color: "#fff", fontSize: 12, fontWeight: 900, cursor: "pointer",
          opacity: saving || !file ? 0.5 : 1,
        }}
      >
        {saving ? <Loader2 style={{ width: 14, height: 14, animation: "spin 1s linear infinite" }} /> : <Plus style={{ width: 14, height: 14 }} />}
        Add Image
      </button>
    </div>
  );
}

// ── Video Creation Section ────────────────────────────────────────────────────
function VideoCreator({ nodeId, onUpload }) {
  const [images, setImages] = useState([]);
  const [soundtrack, setSoundtrack] = useState(null);
  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(15); // seconds
  const [saving, setSaving] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const imageRef = useRef(null);
  const audioRef = useRef(null);

  const addImages = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    const imageFiles = files.filter(f => f.type.startsWith("image/"));
    if (imageFiles.length === 0) {
      toast.error("Select image files");
      return;
    }
    const newImages = imageFiles.map(f => ({
      file: f,
      url: URL.createObjectURL(f),
      name: f.name,
    }));
    setImages(prev => [...prev, ...newImages]);
  }, []);

  const removeImage = useCallback((idx) => {
    setImages(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const handleSoundtrack = useCallback((e) => {
    const f = e.target.files?.[0];
    if (!f || !f.type.startsWith("audio/")) return;
    setSoundtrack({ file: f, name: f.name, url: URL.createObjectURL(f) });
  }, []);

  const handleSave = async () => {
    if (images.length === 0) {
      toast.error("Add at least one image");
      return;
    }
    setSaving(true);
    try {
      const formData = new FormData();
      formData.append("title", title || "Vonns Saga Video");
      formData.append("node_id", nodeId || "general");
      formData.append("duration_seconds", duration);
      images.forEach((img, i) => {
        formData.append(`image_${i}`, img.file);
      });
      if (soundtrack?.file) {
        formData.append("soundtrack", soundtrack.file);
      }
      
      await api.post("/saga/videos", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      toast.success("Video created — images will animate with Ken Burns effect");
      setImages([]);
      setSoundtrack(null);
      setTitle("");
      onUpload?.();
    } catch (e) {
      toast.error("Video creation failed: " + (e?.message || "unknown error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ background: C.panel, border: `1px solid ${C.panelLine}`, borderRadius: 16, padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <Video style={{ width: 18, height: 18, color: C.success }} />
        <div>
          <div style={{ fontSize: 10, fontWeight: 900, textTransform: "uppercase", letterSpacing: "0.2em", color: C.success }}>
            Create Short-Form Video
          </div>
          <div style={{ fontSize: 11, color: C.muted }}>
            Ken Burns pan/zoom · soundtrack · auto-transitions
          </div>
        </div>
      </div>

      {/* Title */}
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Video title"
        style={{
          width: "100%", padding: "8px 12px", borderRadius: 8,
          border: `1px solid ${C.panelLine}`, background: "rgba(0,0,0,0.3)",
          color: C.ink, fontSize: 12, marginBottom: 12, outline: "none",
          fontFamily: "inherit",
        }}
      />

      {/* Image grid */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
          Images ({images.length}) — drag to reorder, each image pans and zooms
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))", gap: 8 }}>
          {images.map((img, i) => (
            <div key={i} style={{ position: "relative", borderRadius: 8, overflow: "hidden", border: `1px solid ${C.panelLine}` }}>
              <img src={img.url} alt="" style={{ width: "100%", height: 60, objectFit: "cover" }} />
              <button
                onClick={() => removeImage(i)}
                style={{
                  position: "absolute", top: 2, right: 2, width: 20, height: 20,
                  borderRadius: "50%", background: "rgba(0,0,0,0.7)", border: "none",
                  color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 10,
                }}
              >
                ×
              </button>
              <div style={{ position: "absolute", bottom: 2, left: 2, fontSize: 9, color: "#fff", background: "rgba(0,0,0,0.6)", padding: "1px 4px", borderRadius: 4 }}>
                {i + 1}
              </div>
            </div>
          ))}
          {/* Add image button */}
          <div
            onClick={() => imageRef.current?.click()}
            style={{
              height: 60, borderRadius: 8, border: `2px dashed ${C.panelLine}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer", background: "transparent",
            }}
          >
            <Plus style={{ width: 16, height: 16, color: C.muted }} />
          </div>
        </div>
        <input
          ref={imageRef}
          type="file"
          accept="image/*"
          multiple
          onChange={addImages}
          style={{ display: "none" }}
        />
      </div>

      {/* Soundtrack */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 6 }}>Soundtrack (optional)</div>
        <div
          onClick={() => audioRef.current?.click()}
          style={{
            border: `1px solid ${C.panelLine}`, borderRadius: 8, padding: "10px 14px",
            cursor: "pointer", display: "flex", alignItems: "center", gap: 8,
            background: soundtrack ? "rgba(74,222,128,0.05)" : "transparent",
          }}
        >
          <Music style={{ width: 14, height: 14, color: soundtrack ? C.success : C.muted }} />
          <span style={{ fontSize: 12, color: soundtrack ? C.ink : C.muted }}>
            {soundtrack?.name || "Add audio track"}
          </span>
        </div>
        <input
          ref={audioRef}
          type="file"
          accept="audio/*"
          onChange={handleSoundtrack}
          style={{ display: "none" }}
        />
      </div>

      {/* Duration */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: C.muted, marginBottom: 6 }}>
          Duration: {duration}s
        </div>
        <input
          type="range"
          min={5}
          max={60}
          value={duration}
          onChange={(e) => setDuration(parseInt(e.target.value))}
          style={{ width: "100%", accentColor: C.success }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: C.dim }}>
          <span>5s</span>
          <span>60s</span>
        </div>
      </div>

      {/* Create button */}
      <button
        onClick={handleSave}
        disabled={saving || images.length === 0}
        style={{
          width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
          padding: "12px", borderRadius: 8, border: "none",
          background: C.success, color: "#000", fontSize: 12, fontWeight: 900, cursor: "pointer",
          opacity: saving || images.length === 0 ? 0.5 : 1,
        }}
      >
        {saving ? <Loader2 style={{ width: 14, height: 14, animation: "spin 1s linear infinite" }} /> : <Video style={{ width: 14, height: 14 }} />}
        Create Video
      </button>
    </div>
  );
}

// ── Track List ────────────────────────────────────────────────────────────────
function TrackList({ tracks, onDelete }) {
  if (!tracks?.length) {
    return (
      <div style={{ fontSize: 12, color: C.dim, textAlign: "center", padding: 20 }}>
        No uploaded tracks yet
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {tracks.map((t) => (
        <div key={t.id || t._id} style={{
          display: "flex", alignItems: "center", gap: 10, padding: "10px 14px",
          background: "rgba(0,0,0,0.2)", borderRadius: 8, border: `1px solid ${C.panelLine}`,
        }}>
          <Music style={{ width: 14, height: 14, color: C.gold, flexShrink: 0 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, color: C.ink, fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {t.title}
            </div>
            <div style={{ fontSize: 10, color: C.muted }}>
              ${(t.price_cents / 100).toFixed(2)} · {t.preview_duration || 33}s preview
            </div>
          </div>
          {onDelete && (
            <button
              onClick={() => onDelete(t.id || t._id)}
              style={{ background: "none", border: "none", color: C.danger, cursor: "pointer", padding: 4 }}
            >
              <Trash2 style={{ width: 14, height: 14 }} />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main Admin Panel ──────────────────────────────────────────────────────────
export default function VonnsSagaAdmin({ nodeId }) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("tracks");
  const [tracks, setTracks] = useState([]);
  const [images, setImages] = useState([]);
  const [expanded, setExpanded] = useState(false);

  // Only show for admin/exec
  const isAdmin = ["admin", "executive_admin", "oversight", "support_staff"].includes(user?.role);
  if (!isAdmin) return null;

  const tabs = [
    { id: "tracks", label: "Tracks", icon: Music, color: C.gold },
    { id: "images", label: "Images", icon: Image, color: C.purple },
    { id: "videos", label: "Videos", icon: Video, color: C.success },
  ];

  const loadTracks = async () => {
    try {
      const res = await api.get("/saga/tracks");
      setTracks(res.data?.tracks || []);
    } catch { /* ignore */ }
  };

  const deleteTrack = async (id) => {
    try {
      await api.delete(`/saga/tracks/${id}`);
      setTracks(prev => prev.filter(t => (t.id || t._id) !== id));
      toast.success("Track removed");
    } catch (e) {
      toast.error("Delete failed");
    }
  };

  return (
    <div style={{ marginTop: 20 }}>
      {/* Toggle button */}
      <button
        onClick={() => {
          setExpanded(!expanded);
          if (!expanded) loadTracks();
        }}
        style={{
          display: "flex", alignItems: "center", gap: 8, padding: "8px 16px",
          borderRadius: 8, border: `1px solid ${C.panelLine}`, background: C.panel,
          color: C.gold, fontSize: 11, fontWeight: 900, textTransform: "uppercase",
          letterSpacing: "0.1em", cursor: "pointer", width: "100%", justifyContent: "center",
        }}
      >
        {expanded ? <EyeOff style={{ width: 14, height: 14 }} /> : <Eye style={{ width: 14, height: 14 }} />}
        {expanded ? "Hide" : "Show"} Admin Panel
      </button>

      {expanded && (
        <div style={{ marginTop: 12, background: "rgba(0,0,0,0.3)", borderRadius: 16, border: `1px solid ${C.panelLine}`, padding: 16 }}>
          {/* Tab bar */}
          <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                  padding: "8px 12px", borderRadius: 8,
                  border: `1px solid ${activeTab === tab.id ? tab.color : C.panelLine}`,
                  background: activeTab === tab.id ? `${tab.color}15` : "transparent",
                  color: activeTab === tab.id ? tab.color : C.muted,
                  fontSize: 11, fontWeight: 700, cursor: "pointer",
                }}
              >
                <tab.icon style={{ width: 14, height: 14 }} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === "tracks" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <TrackUpload onUpload={loadTracks} />
              <TrackList tracks={tracks} onDelete={deleteTrack} />
            </div>
          )}

          {activeTab === "images" && (
            <ImageUpload nodeId={nodeId} />
          )}

          {activeTab === "videos" && (
            <VideoCreator nodeId={nodeId} />
          )}
        </div>
      )}
    </div>
  );
}
