import { useState, useEffect, useRef, useCallback } from "react";
import PublicNav from "../components/PublicNav";
import BackButton from "../components/BackButton";

// ====================================================================// VIDEO PRESENTATION BUILDER — 100% client-side, zero cost, zero upload
// ---------------------------------------------------------------------------
// Canvas-based Ken Burns presentation recorder. Everything runs in the user's
// browser: images never leave the device, narration is recorded live from the
// microphone, and the export is a standard WebM the user owns.
//
// HONEST LIMITATION (differs from the common "record TTS" marketing claim):
// the browser's Web Speech API (speechSynthesis) CANNOT be captured into a
// MediaRecorder stream — the OS renders that audio outside the page. So:
//   • "Preview narration" reads a scene aloud with TTS (free, instant).
//   • Recording captures the animated visuals + LIVE MIC narration.
//   • Export is WebM; add professional audio later with any editor if needed.
// This keeps the tool free and private — nothing is rendered on a server.
// ====================================================================
const MOTIONS = [
  { key: "zoom", label: "Cinematic Zoom-In" },
  { key: "pan", label: "Pan Right" },
  { key: "subtle", label: "Subtle Breath" },
  { key: "none", label: "Static" },
];

const CANVAS_W = 1280;
const CANVAS_H = 720;

const IMPACT_TEMPLATE = [
  {
    id: "s1", title: "A Door Opens", motion: "zoom", image: "",
    script: "Every day, talented people in the M.O.R.E. network are one step away from their goals — held back only by financial friction. Your sponsorship bridges that gap.",
  },
  {
    id: "s2", title: "The Student", motion: "pan", image: "",
    script: "Meet a learner whose next step was blocked by a single cost — a certification fee, a tool, a license. Small support, enormous leverage.",
  },
  {
    id: "s3", title: "The Milestone", motion: "subtle", image: "",
    script: "Funds release only as verified milestones are met. As a sponsor you see exactly where your support goes — no opacity, no red tape.",
  },
  {
    id: "s4", title: "The Thank-You", motion: "zoom", image: "",
    script: "Join the M.O.R.E. Scholarship Initiative. Turn your resources into lifelong transformation.",
  },
];

function sceneDuration(script) {
  // ~13 chars/sec speaking pace; min 4s, max 14s.
  return Math.max(4, Math.min(14, Math.ceil((script || "").length / 13)));
}

function wrapText(ctx, text, maxWidth) {
  const words = (text || "").split(" ");
  const lines = [];
  let line = "";
  for (const w of words) {
    const test = line ? line + " " + w : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  return lines;
}

export default function VideoPresenter() {
  const [scenes, setScenes] = useState(JSON.parse(JSON.stringify(IMPACT_TEMPLATE)));
  const [activeIdx, setActiveIdx] = useState(0);
  const [mode, setMode] = useState("preview"); // preview | recording
  const [elapsed, setElapsed] = useState(0);
  const [recMsg, setRecMsg] = useState("");
  const [exportUrl, setExportUrl] = useState("");
  const canvasRef = useRef(null);
  const rafRef = useRef(null);
  const recRef = useRef(null); // MediaRecorder
  const micRef = useRef(null);
  const chunksRef = useRef([]);
  const startRef = useRef(0);
  const sceneIdxRef = useRef(0);
  const sceneStartRef = useRef(0);
  const imgCacheRef = useRef({}); // scene.id → HTMLImageElement

  const scene = scenes[activeIdx] || scenes[0];

  // Preload scene images once (object URLs are local — instant).
  useEffect(() => {
    for (const s of scenes) {
      if (s.image && !imgCacheRef.current[s.id]) {
        const img = new Image();
        img.src = s.image;
        imgCacheRef.current[s.id] = img;
      }
    }
  }, [scenes]);

  // ── Drawing ──────────────────────────────────────────────────────────────
  const paintOverlay = useCallback((ctx, s, p) => {
    // bottom gradient
    const g = ctx.createLinearGradient(0, CANVAS_H * 0.45, 0, CANVAS_H);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(0,0,0,0.82)");
    ctx.fillStyle = g;
    ctx.fillRect(0, CANVAS_H * 0.45, CANVAS_W, CANVAS_H * 0.55);

    // title (top-left)
    ctx.fillStyle = "rgba(232,165,30,0.95)";
    ctx.font = "800 40px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText((s.title || "Untitled").toUpperCase().slice(0, 34), 56, 76);

    // progress bar
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.fillRect(56, 96, 220, 4);
    ctx.fillStyle = "#E8A51E";
    ctx.fillRect(56, 96, 220 * p, 4);

    // script text — reveal lines as the scene plays
    ctx.fillStyle = "#fff";
    ctx.font = "500 34px 'IBM Plex Sans', sans-serif";
    const lines = wrapText(ctx, s.script, CANVAS_W - 112);
    const shown = Math.min(lines.length, Math.max(1, Math.ceil(lines.length * p)));
    let y = CANVAS_H - 96;
    for (let i = shown - 1; i >= 0; i--) {
      ctx.fillText(lines[i], 56, y);
      y -= 46;
    }
  }, []);

  const drawFrame = useCallback((idx, t, dur) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const s = scenes[idx];
    if (!s) return;
    const p = Math.min(1, Math.max(0, t / dur)); // 0..1 through the scene

    ctx.save();
    ctx.fillStyle = "#0d0a06";
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    const img = imgCacheRef.current[s.id];
    if (img && img.complete && img.naturalWidth > 0) {
      // cover-fit
      const scale = Math.max(CANVAS_W / img.naturalWidth, CANVAS_H / img.naturalHeight);
      const dw = img.naturalWidth * scale;
      const dh = img.naturalHeight * scale;
      let dx = (CANVAS_W - dw) / 2;
      let dy = (CANVAS_H - dh) / 2;
      // Ken Burns transform
      let k = 1;
      let ox = 0;
      let oy = 0;
      if (s.motion === "zoom") { k = 1 + 0.18 * p; }
      if (s.motion === "pan") { k = 1.08; ox = (p - 0.5) * dw * 0.12; }
      if (s.motion === "subtle") { k = 1 + 0.06 * Math.sin(p * Math.PI); }
      const sw = dw * k, sh = dh * k;
      ctx.drawImage(img, dx - (sw - dw) / 2 + ox, dy - (sh - dh) / 2 + oy, sw, sh);
    } else {
      // branded fallback background
      const g = ctx.createLinearGradient(0, 0, CANVAS_W, CANVAS_H);
      g.addColorStop(0, "#241a08");
      g.addColorStop(0.5, "#4a3209");
      g.addColorStop(1, "#0d1a0a");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
      ctx.fillStyle = "rgba(232,165,30,0.15)";
      for (let i = 0; i < 24; i++) {
        ctx.beginPath();
        ctx.arc((i * 137) % CANVAS_W, (i * 89) % CANVAS_H, 40 + (i % 4) * 30, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    paintOverlay(ctx, s, p);
    ctx.restore();
  }, [scenes, paintOverlay]);



  // ── Animation loop ───────────────────────────────────────────────────────
  useEffect(() => {
    const loop = (now) => {
      const t = (now - (startRef.current || now)) / 1000;
      const dur = sceneDuration(scenes[sceneIdxRef.current]?.script);
      setElapsed(t);
      if (t >= dur) {
        // advance to next scene (both preview and recording)
        const next = sceneIdxRef.current + 1;
        if (next < scenes.length) {
          sceneIdxRef.current = next;
          sceneStartRef.current = now;
          setActiveIdx(next);
          startRef.current = now;
        } else if (modeRef.current === "recording") {
          stopRecording(true);
        } else {
          sceneIdxRef.current = 0;
          sceneStartRef.current = now;
          setActiveIdx(0);
          startRef.current = now;
        }
      }
      drawFrame(sceneIdxRef.current, t, dur);
      rafRef.current = requestAnimationFrame(loop);
    };
    startRef.current = performance.now();
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenes, drawFrame]);

  const modeRef = useRef(mode);
  modeRef.current = mode;
  const stopRecordingRef = useRef(null);

  // ── TTS preview (cannot be captured — used for listening only) ──────────
  function previewNarration() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const full = scenes.map((s) => `${s.title}. ${s.script}`).join(" ");
    const u = new SpeechSynthesisUtterance(full);
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }

  // ── Recording (canvas stream + live mic) ────────────────────────────────
  async function startRecording() {
    setExportUrl("");
    chunksRef.current = [];
    let micStream = null;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setRecMsg("Microphone unavailable — recording visuals only (no narration). You can add audio later.");
    }
    micRef.current = micStream;

    const canvas = canvasRef.current;
    const canvasStream = canvas.captureStream(30);
    const tracks = canvasStream.getVideoTracks();
    if (micStream) tracks.push(...micStream.getAudioTracks());
    const stream = new MediaStream(tracks);

    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : "video/webm";
    const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 6_000_000 });
    rec.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data); };
    rec.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: mime });
      const url = URL.createObjectURL(blob);
      setExportUrl(url);
      setMode("preview");
      setRecMsg("Done! Download your WebM below. To add professional narration or music later, open it in any free editor (CapCut, OpenShot, DaVinci Resolve).");
      if (micStream) micStream.getTracks().forEach((t) => t.stop());
    };
    rec.start(250);
    recRef.current = rec;

    // reset timeline and run scenes once
    sceneIdxRef.current = 0;
    setActiveIdx(0);
    startRef.current = performance.now();
    setMode("recording");
    setRecMsg("Recording — scenes play automatically. Speak your narration into the mic.");
  }

  function stopRecording(auto = false) {
    if (recRef.current && recRef.current.state !== "inactive") {
      recRef.current.stop();
    }
    if (!auto) setRecMsg("Stopping…");
  }

  stopRecordingRef.current = stopRecording;

  // ── Scene editing ────────────────────────────────────────────────────────
  function updateScene(idx, patch) {
    setScenes((s) => s.map((sc, i) => (i === idx ? { ...sc, ...patch } : sc)));
  }

  function addScene() {
    setScenes((s) => [...s, { id: "s" + Date.now(), title: "New Scene", motion: "zoom", image: "", script: "Tell the story here." }]);
  }

  function removeScene(idx) {
    setScenes((s) => {
      const n = s.filter((_, i) => i !== idx);
      if (activeIdx >= n.length) setActiveIdx(Math.max(0, n.length - 1));
      return n;
    });
  }

  function loadImage(idx, file) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    updateScene(idx, { image: url });
  }

  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        <BackButton to="/sponsor" />
        <div className="mt-4">
          <div className="overline text-copper">Free Tool · Runs 100% in your browser · Nothing uploaded</div>
          <h1 className="font-heading text-3xl font-black text-ink mt-1">Video Presentation Builder</h1>
          <p className="text-ink/60 mt-2 max-w-3xl text-sm leading-relaxed">
            Turn images and a script into a narrated presentation — sponsor impact reports, applicant spotlights,
            and tutorials. Images never leave your device; the export is your own WebM file.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mt-8">
          {/* PREVIEW */}
          <div className="lg:col-span-2">
            <div className="rounded-2xl overflow-hidden" style={{ background: "#000", border: "1px solid #1c1917" }}>
              <canvas ref={canvasRef} width={CANVAS_W} height={CANVAS_H} className="w-full block" style={{ aspectRatio: "16/9" }} />
            </div>
            <div className="text-xs text-ink/50 mt-1.5">
              Scene {activeIdx + 1} of {scenes.length} · {scene?.title} · {sceneDuration(scene?.script)}s
            </div>

            {/* CONTROLS */}
            <div className="flex flex-wrap gap-2 mt-4">
              {mode === "preview" ? (
                <>
                  <button onClick={startRecording} className="font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#dc2626", color: "#fff" }}>
                    🔴 Record (with mic narration)
                  </button>
                  <button onClick={previewNarration} className="font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "#d6c9a8", color: "#8a5a00" }}>
                    🔊 Preview narration (listen only)
                  </button>
                </>
              ) : (
                <button onClick={() => stopRecording(false)} className="font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#1f2933", color: "#fff" }}>
                  ⏹ Stop & export
                </button>
              )}
            </div>
            {recMsg && <div className="mt-3 text-xs leading-relaxed rounded-xl px-4 py-3" style={{ background: "#fef3c7", border: "1px solid #fde68a", color: "#8a5a00" }}>{recMsg}</div>}
            {exportUrl && (
              <div className="mt-4 rounded-2xl p-4" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <a href={exportUrl} download="video-presentation.webm" className="inline-block font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                  ⬇️ Download your WebM
                </a>
                <video controls src={exportUrl} className="w-full mt-3 rounded-xl" style={{ maxHeight: 360 }} />
              </div>
            )}
            <div className="mt-4 text-[11px] text-ink/40 leading-relaxed">
              Why is narration mic-only? The browser's text-to-speech plays through the operating system and cannot be
              captured into a recording — a limitation of every browser, not this tool. So TTS is free for listening
              during preview, and recording captures your live voice. Export is WebM; any free editor can add music or
              a produced voice track later.
            </div>
          </div>

          {/* SCENE EDITOR */}
          <div>
            <div className="flex items-center justify-between">
              <h2 className="font-heading font-extrabold text-ink">Scenes</h2>
              <button onClick={addScene} className="text-xs font-bold px-3 py-1.5 rounded-lg" style={{ background: "#1f2933", color: "#fff" }}>+ Add scene</button>
            </div>
            <div className="space-y-3 mt-3">
              {scenes.map((s, idx) => (
                <div key={s.id} className={`rounded-2xl p-4 ${idx === activeIdx ? "" : ""}`} style={{ background: "#fff", border: idx === activeIdx ? "2px solid #E8A51E" : "1px solid #eee7db" }}>
                  <div className="flex items-center justify-between gap-2">
                    <button onClick={() => { setActiveIdx(idx); sceneIdxRef.current = idx; }} className="font-bold text-sm text-ink">{idx + 1}. {s.title}</button>
                    <div className="flex gap-2">
                      <button onClick={() => removeScene(idx)} className="text-[11px] text-red-500 font-bold">✕</button>
                    </div>
                  </div>
                  <input value={s.title} onChange={(e) => updateScene(idx, { title: e.target.value })} placeholder="Scene title"
                    className="mt-2 w-full text-xs rounded-lg px-2.5 py-1.5 border" style={{ borderColor: "#ddd3c0" }} />
                  <textarea rows={3} value={s.script} onChange={(e) => updateScene(idx, { script: e.target.value })} placeholder="Narration script"
                    className="mt-2 w-full text-xs rounded-lg px-2.5 py-1.5 border resize-none" style={{ borderColor: "#ddd3c0" }} />
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    <select value={s.motion} onChange={(e) => updateScene(idx, { motion: e.target.value })}
                      className="text-[11px] rounded-lg px-2 py-1.5 border" style={{ borderColor: "#ddd3c0" }}>
                      {MOTIONS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
                    </select>
                    <label className="text-[11px] font-bold px-3 py-1.5 rounded-lg cursor-pointer" style={{ background: "#faf9f7", border: "1px solid #eee7db", color: "#8a5a00" }}>
                      {s.image ? "🖼️ Replace image" : "🖼️ Add image"}
                      <input type="file" accept="image/*" className="hidden" onChange={(e) => loadImage(idx, e.target.files?.[0])} />
                    </label>
                    {s.image && <button onClick={() => updateScene(idx, { image: "" })} className="text-[11px] text-ink/40">remove</button>}
                  </div>
                </div>
              ))}
            </div>
            <div className="rounded-2xl p-4 mt-4 text-xs text-ink/60 leading-relaxed" style={{ background: "#fef3c7", border: "1px solid #fde68a" }}>
              💡 <strong>Impact report template loaded.</strong> Start from scratch with "Add scene" — perfect for sponsor impact reports, applicant spotlights, and onboarding tutorials.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

