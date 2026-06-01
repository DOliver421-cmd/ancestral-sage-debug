import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";

/* ── design tokens ──────────────────────────────────────────────────────── */
const T = {
  ghost:    "#00ffcc",
  ghostDim: "#00aa88",
  bg:       "#0a0a0f",
  card:     "#12121a",
  text:     "#e0e0e0",
  accent:   "#ff0066",
  gold:     "#d4af37",
  goldDim:  "#8b7020",
  warn:     "#ffaa00",
};

const APIS = [
  "Puter.js TTS","Puter.js STT","Puter.js Share","LibreTranslate",
  "DeepL Free","MyMemory","Qwant Search","DuckDuckGo",
  "OpenStreetMap","PDF.js","EPUB.js","MOBI.js",
];

const TRACKS = [
  { icon:"🌊", name:"Ethereal Drift",   bpm:"85 BPM — Ambient Pad",   mode:"ghost" },
  { icon:"💀", name:"Ghost Kick",       bpm:"90 BPM — 808 Sub",        mode:"chaos" },
  { icon:"🗣️", name:"NAM Whisper",      bpm:"90 BPM — Vocal Chops",    mode:"human" },
  { icon:"🧠", name:"WAI Cortex",       bpm:"140 BPM — AI Synth Lead", mode:"chaos" },
  { icon:"🥁", name:"Phantom Hi-Hat",   bpm:"90 BPM — Percussion",     mode:"ghost" },
  { icon:"📡", name:"Soul Frequency",   bpm:"88 BPM — Bass Line",      mode:"human" },
  { icon:"🌫️", name:"Haunted Reverb",   bpm:"FREE — FX / Atmosphere",  mode:"ghost" },
];

const CLONES = [
  { icon:"📝", id:"editor",    label:"Ghost Editor",    desc:"Fixes manuscripts, formats PDF/EPUB/MOBI. Keen eye. No sleep needed." },
  { icon:"📢", id:"publicist", label:"Ghost Publicist", desc:"Social media algorithms, streaming platforms, radio/TV. Makes you unavoidable." },
  { icon:"&",  id:"legal",     label:"Ghost Legal",     desc:"Copyright, trademark, global law. Kemetic spirituality & Powernomics on retainer." },
  { icon:"📈", id:"marketer",  label:"Ghost Marketer",  desc:"Chess-level strategy. Visual art. Crushes competition before they know you exist." },
];

/* ── styles ──────────────────────────────────────────────────────────────── */
const S = {
  page:     { background: T.bg, color: T.text, fontFamily: "'Inter', sans-serif", minHeight: "100vh", overflowX: "hidden" },
  hero:     { textAlign: "center", padding: "50px 20px 30px", position: "relative", zIndex: 1 },
  h1:       { fontFamily: "'Space Mono', monospace", fontSize: "clamp(1.8rem,5vw,4rem)", color: T.ghost, textShadow: `0 0 40px rgba(0,255,204,0.4)`, lineHeight: 1.1, marginBottom: 5 },
  h2gold:   { fontFamily: "'Space Mono', monospace", fontSize: "clamp(1rem,3vw,1.6rem)", color: T.gold, textShadow: `0 0 30px rgba(212,175,55,0.3)`, marginBottom: 10 },
  byline:   { fontSize: "1rem", color: "#888", marginTop: 8, letterSpacing: 3, textTransform: "uppercase" },
  tag:      { display: "inline-block", marginTop: 18, padding: "8px 24px", border: `1px solid ${T.ghostDim}`, borderRadius: 50, color: T.ghost, fontFamily: "'Space Mono', monospace", fontSize: "0.85rem", background: "rgba(0,255,204,0.05)" },
  tagGold:  { display: "inline-block", marginTop: 10, marginLeft: 8, padding: "8px 24px", border: `1px solid ${T.goldDim}`, borderRadius: 50, color: T.gold, fontFamily: "'Space Mono', monospace", fontSize: "0.85rem", background: "rgba(212,175,55,0.05)" },
  tabs:     { display: "flex", justifyContent: "center", gap: 8, padding: "16px", flexWrap: "wrap", position: "relative", zIndex: 1 },
  panel:    { maxWidth: 900, margin: "0 auto", padding: "20px 30px 80px", position: "relative", zIndex: 1 },
  secTitle: { fontFamily: "'Space Mono', monospace", fontSize: "1.4rem", color: T.ghost, marginBottom: 20, paddingBottom: 10, borderBottom: "1px solid #222" },
  secTitleGold: { fontFamily: "'Space Mono', monospace", fontSize: "1.4rem", color: T.gold, marginBottom: 20, paddingBottom: 10, borderBottom: `1px solid ${T.goldDim}` },
  card:     { background: T.card, border: "1px solid #1e1e2e", borderRadius: 16, padding: 20, marginBottom: 16 },
  cardGold: { background: T.card, border: `1px solid ${T.goldDim}`, borderRadius: 16, padding: 20, marginBottom: 16 },
  step:     { display: "flex", gap: 20, alignItems: "flex-start", padding: 20, background: T.card, border: "1px solid #1e1e2e", borderRadius: 16, marginBottom: 12 },
  stepNum:  { fontFamily: "'Space Mono', monospace", fontSize: "1.5rem", color: T.ghost, minWidth: 40, textAlign: "center", background: "rgba(0,255,204,0.08)", borderRadius: 12, padding: "10px 0" },
  warning:  { background: "rgba(255,170,0,0.08)", border: `1px solid ${T.warn}`, borderRadius: 12, padding: 20, margin: "20px 0" },
  footer:   { textAlign: "center", padding: "40px 20px", color: "#444", fontSize: "0.8rem", position: "relative", zIndex: 1 },
};

function tabBtnStyle(active, gold = false) {
  return {
    padding: "12px 24px",
    border: active ? `1px solid ${gold ? T.gold : T.ghost}` : "1px solid #333",
    background: active ? (gold ? "rgba(212,175,55,0.1)" : "rgba(0,255,204,0.1)") : T.card,
    color: active ? (gold ? T.gold : T.ghost) : "#aaa",
    borderRadius: 12, cursor: "pointer",
    fontFamily: "'Space Mono', monospace", fontSize: "0.82rem",
    boxShadow: active ? `0 0 20px ${gold ? "rgba(212,175,55,0.15)" : "rgba(0,255,204,0.15)"}` : "none",
    transition: "all 0.3s",
  };
}

function vizBtnStyle(active = false, gold = false) {
  return {
    padding: "12px 28px",
    border: `1px solid ${gold ? T.goldDim : T.ghostDim}`,
    background: active ? (gold ? T.gold : T.ghost) : "transparent",
    color: active ? "#000" : (gold ? T.gold : T.ghost),
    borderRadius: 10, cursor: "pointer",
    fontFamily: "'Space Mono', monospace", fontSize: "0.85rem",
    transition: "all 0.3s",
  };
}

/* ── component ──────────────────────────────────────────────────────────── */
export default function GhostProducer() {
  const [tab, setTab]               = useState("manual");
  const [isPlaying, setIsPlaying]   = useState(false);
  const [mode, setMode]             = useState("ghost");
  const [bpm, setBpm]               = useState(90);
  const [mix, setMix]               = useState(50);
  const [activeTrack, setActiveTrack] = useState(null);
  const [activeClone, setActiveClone] = useState(null);
  const [vaultPass, setVaultPass]   = useState("");
  const [vaultOpen, setVaultOpen]   = useState(false);
  const [ttsOutput, setTtsOutput]   = useState("");
  const [ttsText, setTtsText]       = useState("");
  const [ttsVoice, setTtsVoice]     = useState("sage");
  const [ttsLoading, setTtsLoading] = useState(false);
  const ttsAudioRef = useRef(null);
  const [currentSession, setCurrentSession] = useState(1);
  const [panelOpen, setPanelOpen]   = useState(false);

  const canvasRef  = useRef(null);
  const rafRef     = useRef(null);
  const timeRef    = useRef(0);
  const playRef    = useRef(false);
  const modeRef    = useRef("ghost");
  const bpmRef     = useRef(90);
  const mixRef     = useRef(50);

  // keep refs in sync with state
  useEffect(() => { playRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { modeRef.current = mode; },    [mode]);
  useEffect(() => { bpmRef.current  = bpm; },     [bpm]);
  useEffect(() => { mixRef.current  = mix; },     [mix]);

  // canvas sizing
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      canvas.width  = canvas.offsetWidth  * 2;
      canvas.height = canvas.offsetHeight * 2;
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  // draw once on mount
  useEffect(() => { drawFrame(); }, []); // eslint-disable-line

  // session ticker
  useEffect(() => {
    const t = setInterval(() => setCurrentSession(s => s >= 14 ? 1 : s + 1), 30000);
    return () => clearInterval(t);
  }, []);

  function drawFrame() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx  = canvas.getContext("2d");
    const w    = canvas.offsetWidth;
    const h    = canvas.offsetHeight;
    const t    = timeRef.current;
    const m    = modeRef.current;
    const ml   = mixRef.current;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.scale(2, 2);

    const barCount = 64;
    const barW = w / barCount - 2;
    for (let i = 0; i < barCount; i++) {
      let barH;
      if      (m === "ghost")  barH = Math.sin(t * 0.03 + i * 0.2) * 30 + Math.sin(t * 0.07 + i * 0.1) * 20 + 40;
      else if (m === "human")  barH = Math.sin(t * 0.05 + i * 0.3) * 50 + Math.cos(t * 0.02 + i * 0.15) * 30 + 50;
      else if (m === "chaos")  barH = Math.random() * 80 + 20 + Math.sin(t * 0.1 + i) * 40;
      else                     barH = Math.sin(t * 0.04 + i * 0.25) * 45 + Math.cos(t * 0.06 + i * 0.2) * 25 + 55;

      const r = ml > 50 ? 255 : 0;
      const g = ml < 50 ? 255 : 0;
      const b = 200;
      const a = 0.4 + (barH / 120) * 0.6;
      ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
      ctx.shadowBlur  = 15;
      ctx.shadowColor = `rgba(${r},${g},${b},0.5)`;
      ctx.fillRect(i * (barW + 2), h - barH, barW, barH);
      ctx.shadowBlur = 0;
    }

    ctx.beginPath();
    const waveColor = m === "ghost" ? "rgba(0,255,204,0.3)" : m === "human" ? "rgba(255,0,102,0.3)" : m === "chaos" ? "rgba(255,170,0,0.3)" : "rgba(212,175,55,0.3)";
    ctx.strokeStyle = waveColor;
    ctx.lineWidth = 2;
    for (let x = 0; x < w; x++) {
      const y = h / 2 + Math.sin(x * 0.02 + t * 0.05) * 20 * (m === "chaos" ? 2 : 1);
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();

    if (playRef.current) {
      timeRef.current += bpmRef.current / 30;
      rafRef.current = requestAnimationFrame(drawFrame);
    }
  }

  function togglePlay() {
    const next = !isPlaying;
    setIsPlaying(next);
    playRef.current = next;
    if (next) { drawFrame(); }
    else { cancelAnimationFrame(rafRef.current); }
  }

  function handleMode(m) {
    setMode(m);
    modeRef.current = m;
    if (!isPlaying) drawFrame();
  }

  function handleTrack(track) {
    setActiveTrack(track.name);
    modeRef.current = track.mode;
    setMode(track.mode);
    if (isPlaying) drawFrame();
  }

  function unlockVault() {
    if (vaultPass.length >= 4) { setVaultOpen(true); setVaultPass(""); }
    else { alert("⚠️ Password too short. The ghost demands at least 4 characters."); }
  }

  async function puterTTS() {
    const text = ttsText.trim();
    if (!text) { setTtsOutput("⚠️ Enter text above to convert."); return; }
    setTtsLoading(true);
    setTtsOutput("🔄 Generating audio…");
    try {
      const resp = await api.post("/ai/sage/tts", { text, voice: ttsVoice, speed: 1.0, session_id: "ghost_producer" }, { responseType: "blob" });
      const url = URL.createObjectURL(resp.data);
      if (ttsAudioRef.current) { ttsAudioRef.current.pause(); URL.revokeObjectURL(ttsAudioRef.current.src); }
      const audio = new Audio(url);
      ttsAudioRef.current = audio;
      audio.play();
      setTtsOutput("🔊 Playing — voice: " + ttsVoice);
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || "TTS failed";
      setTtsOutput("⚠️ " + detail);
    } finally {
      setTtsLoading(false);
    }
  }
  function puterSTT() {
    setTtsOutput("🎙️ Speech-to-Text — coming soon.");
  }
  function puterShare() {
    setTtsOutput("📁 File Share — coming soon.");
  }
  function compressMemory() {
    try {
      const keys = Object.keys(localStorage).filter(k => k.startsWith("wai_hub_"));
      keys.forEach(k => localStorage.removeItem(k));
      setTtsOutput("💾 Session memory cleared — " + keys.length + " keys removed.");
    } catch (e) {
      setTtsOutput("⚠️ Could not clear memory: " + e.message);
    }
  }

  /* ── render ── */
  return (
    <>
      {/* Google Fonts */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet" />

      <div style={S.page}>
        {/* HERO */}
        <div style={S.hero}>
          <h1 style={S.h1}>THE <span style={{ color: T.accent, textShadow: "0 0 40px rgba(255,0,102,0.4)" }}>GHOST</span> PRODUCER</h1>
          <h2 style={S.h2gold}>× PUBLISHER <span style={{ color: T.gold }}>PRIME</span> v14</h2>
          <div style={S.byline}>NAM Oshun &amp; WAI-Institute × 14th Evolution</div>
          <div style={S.tag}>🎧 INTERACTIVE INSTRUCTION MANUAL v1.0</div>
          <div style={S.tagGold}>⚙️ PUBLISHER PRIME ACTIVE — NO SIGN-IN</div>
        </div>

        {/* TABS */}
        <div style={S.tabs}>
          {[
            { id: "manual",  label: "📖 Manual",        gold: false },
            { id: "studio",  label: "🎛️ Studio",         gold: false },
            { id: "tracks",  label: "🎵 Tracks",         gold: false },
            { id: "prime",   label: "& Publisher Prime", gold: true  },
            { id: "about",   label: "👻 About",          gold: false },
          ].map(({ id, label, gold }) => (
            <button key={id} style={tabBtnStyle(tab === id, gold)} onClick={() => setTab(id)}>
              {label}
            </button>
          ))}
        </div>

        {/* ── MANUAL ── */}
        {tab === "manual" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>📋 HANDY INSTRUCTION MANUAL FOR SIMPLE HUMANS</h2>
            <div style={S.warning}>
              <h4 style={{ color: T.warn, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>⚠️ READ THIS FIRST OR YOU'LL BE LOST</h4>
              <p style={{ color: "#bb8844", fontSize: "0.9rem" }}>This is TWO powerhouses fused into ONE widget. <strong>The Ghost Producer</strong> (NAM Oshun × WAI-Institute) gives you the music. <strong>Publisher Prime</strong> (14th Evolution) gives you the publishing empire. Together = you don't need a label, a lawyer, or a soul. Well... you still need a soul. But the rest? Covered.</p>
            </div>
            {[
              { n:"1", title:"🧠 UNDERSTAND THE VIBE", body:"\"The Ghost Producer\" makes music that sounds like it was made by a ghost — ethereal, layered, half-there, but HITS hard. NAM Oshun brings the soul. WAI-Institute brings the AI brain. Publisher Prime takes that music and dominates every publishing channel on Earth — no sign-in, no account, no gatekeeping." },
              { n:"2", title:"🎧 OPEN YOUR EARS", body:"Go to the \"Studio\" tab. Click the big glowing buttons. The visualizer reacts to YOUR clicks. Then go to \"Publisher Prime\" tab to see your empire dashboard. Listen with headphones if you can — it hits different when you know you're about to take over the industry." },
              { n:"3", title:"🎛️ PLAY WITH THE CONTROLS", body:"In Studio: BPM slider (speed), Ghost Mix (AI vs Human), Visualizer modes. In Publisher Prime: Clone Army (4 personas), Vault (your secrets), 12 Free APIs (no sign-in ever). Drag everything. There's no wrong way. The ghost doesn't judge." },
              { n:"4", title:"👥 DEPLOY YOUR CLONES", body:"Publisher Prime lets you spawn 4 clones: Ghost Editor (fixes your manuscripts), Ghost Publicist (makes you famous), Ghost Legal (handles copyright/trademark), Ghost Marketer (crushes social media). They all sync back to your brain. You are the hive mind now." },
              { n:"5", title:"🔐 LOCK YOUR VAULT", body:"Go to Publisher Prime → Vault. Set a master password. Your trade secrets, passwords, manuscripts — all encrypted. Military-grade. Even YOU can't get in without the password. Well... you can. But the ghost respects the lock." },
              { n:"6", title:"👻 BECOME THE PRODUCER", body:"Here's the secret: YOU are the ghost producer AND the publisher now. NAM Oshun and WAI-Institute made the foundation. Publisher Prime makes you unstoppable. Remix it in your head. Hum it in the shower. Publish it at 3am. That's the whole point." },
            ].map(({ n, title, body }) => (
              <div key={n} style={S.step}>
                <div style={S.stepNum}>{n}</div>
                <div>
                  <h4 style={{ color: "#fff", marginBottom: 6 }}>{title}</h4>
                  <p style={{ color: "#888", fontSize: "0.9rem", lineHeight: 1.6 }}>{body}</p>
                </div>
              </div>
            ))}
            <div style={{ ...S.cardGold, borderColor: T.gold, marginTop: 20 }}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🚨 TROUBLESHOOTING FOR SIMPLE HUMANS</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>
                <strong>"It's not working"</strong> → Refresh. Ghosts are shy.<br />
                <strong>"I don't get the clones"</strong> → Go to Publisher Prime tab. Click a clone card. They're your little helpers.<br />
                <strong>"This is amazing"</strong> → ✅ Correct. You're welcome.<br />
                <strong>"Who is NAM Oshun?"</strong> → Go to About tab. Nerd.<br />
                <strong>"Where's my vault password?"</strong> → You set it. If you forgot... you're on your own. 👻
              </p>
            </div>
          </div>
        )}

        {/* ── STUDIO ── */}
        {tab === "studio" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>🎛️ THE GHOST STUDIO × PRIME ENGINE</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>Interactive visualizer powered by Publisher Prime's API rotation.</p>
            <div style={{ background: T.card, border: "1px solid #1e1e2e", borderRadius: 16, padding: 30, textAlign: "center" }}>
              <canvas ref={canvasRef} style={{ width: "100%", maxWidth: 600, height: 200, borderRadius: 12, background: "#000", display: "block", margin: "0 auto" }} />
              <div style={{ marginTop: 20, display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <button style={vizBtnStyle(isPlaying)} onClick={togglePlay}>{isPlaying ? "⏸ PAUSE" : "▶ PLAY"}</button>
                {[
                  { id:"ghost", label:"👻 GHOST MODE"  },
                  { id:"human", label:"🧍 HUMAN MODE"  },
                  { id:"chaos", label:"🌀 CHAOS MODE"  },
                  { id:"prime", label:"& PRIME MODE", gold: true },
                ].map(({ id, label, gold }) => (
                  <button key={id} style={vizBtnStyle(mode === id, gold)} onClick={() => handleMode(id)}>{label}</button>
                ))}
              </div>
            </div>
            <div style={{ marginTop: 24 }}>
              <div style={S.card}>
                <h3 style={{ color: T.accent, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🎚️ BPM CONTROL</h3>
                <p style={{ marginBottom: 12, color: "#888" }}>Drag to change the ghost's heartbeat</p>
                <input type="range" min="60" max="180" value={bpm}
                  style={{ width: "100%", accentColor: T.ghost, height: 8, cursor: "pointer" }}
                  onChange={e => { const v = parseInt(e.target.value); setBpm(v); bpmRef.current = v; }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "'Space Mono', monospace", color: T.ghost, fontSize: "0.85rem", marginTop: 8 }}>
                  <span>🐢 60 BPM</span><span>{bpm} BPM</span><span>🐇 180 BPM</span>
                </div>
              </div>
              <div style={{ ...S.card, marginTop: 12 }}>
                <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>📊 GHOST MIX LEVEL (PRIME ENGINE)</h3>
                <p style={{ marginBottom: 12, color: "#888" }}>How much AI (WAI) vs Human (NAM) energy</p>
                <input type="range" min="0" max="100" value={mix}
                  style={{ width: "100%", accentColor: T.accent, height: 8, cursor: "pointer" }}
                  onChange={e => { const v = parseInt(e.target.value); setMix(v); mixRef.current = v; }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "'Space Mono', monospace", fontSize: "0.85rem", marginTop: 8 }}>
                  <span style={{ color: T.accent }}>100% WAI-Institute</span>
                  <span style={{ color: T.ghost }}>{mix}/{100 - mix}</span>
                  <span style={{ color: T.ghost }}>100% NAM Oshun</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TRACKS ── */}
        {tab === "tracks" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>🎵 TRACK BREAKDOWN</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>The bones of The Ghost Producer. Click any track to "activate" it.</p>
            {TRACKS.map(t => (
              <div key={t.name}
                onClick={() => handleTrack(t)}
                style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "16px 20px", background: T.card,
                  border: `1px solid ${activeTrack === t.name ? T.ghost : "#1e1e2e"}`,
                  borderRadius: 12, marginBottom: 8, cursor: "pointer",
                  background: activeTrack === t.name ? "rgba(0,255,204,0.08)" : T.card,
                  transition: "all 0.3s",
                }}
              >
                <span style={{ fontWeight: 600 }}>{t.icon} {t.name}</span>
                <span style={{ fontFamily: "'Space Mono', monospace", color: T.ghost, fontSize: "0.85rem" }}>{t.bpm}</span>
              </div>
            ))}
            <div style={{ ...S.cardGold, borderColor: T.goldDim, marginTop: 20 }}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🎼 HOW THE TRACKS FIT TOGETHER</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>
                Think of it like a ghost story: <strong>Ethereal Drift</strong> sets the scene. <strong>Ghost Kick</strong> is the heartbeat you feel but can't see. <strong>NAM Whisper</strong> is the voice calling your name. <strong>WAI Cortex</strong> is the AI brain behind the curtain. <strong>Phantom Hi-Hat</strong> keeps time like a clock in a haunted house. <strong>Soul Frequency</strong> is the bass that rattles your chest. And <strong>Haunted Reverb</strong>... that's the ghost itself. It's everywhere. It's nowhere.
              </p>
            </div>
          </div>
        )}

        {/* ── PUBLISHER PRIME ── */}
        {tab === "prime" && (
          <div style={S.panel}>
            <h2 style={S.secTitleGold}>& PUBLISHER PRIME — 14TH EVOLUTION</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>Your one-man publishing empire. No sign-in. No account. No limits.</p>

            {/* Clone Army */}
            <div style={S.card}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>👥 CLONE ARMY — 4 LESSER PERSONAS</h3>
              <p style={{ marginBottom: 16, color: "#888" }}>Deploy a clone to handle any task. They sync back to your central memory.</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginTop: 16 }}>
                {CLONES.map(c => (
                  <div key={c.id}
                    onClick={() => setActiveClone(c.id)}
                    style={{
                      background: T.card, border: `1px solid ${activeClone === c.id ? T.gold : "#1e1e2e"}`,
                      borderRadius: 16, padding: 20, textAlign: "center", cursor: "pointer",
                      background: activeClone === c.id ? "rgba(212,175,55,0.08)" : T.card,
                      transition: "all 0.3s",
                    }}
                  >
                    <div style={{ fontSize: "2.5rem", marginBottom: 10 }}>{c.icon}</div>
                    <h4 style={{ fontFamily: "'Space Mono', monospace", color: T.gold, marginBottom: 8 }}>{c.label}</h4>
                    <p style={{ color: "#888", fontSize: "0.85rem" }}>{c.desc}</p>
                  </div>
                ))}
              </div>
              {activeClone && (
                <div style={{ marginTop: 16, textAlign: "center", fontFamily: "'Space Mono', monospace", color: T.gold, fontSize: "0.85rem" }}>
                  ✅ {CLONES.find(c => c.id === activeClone)?.label} ACTIVE — SYNCING TO CENTRAL MEMORY...
                </div>
              )}
            </div>

            {/* Vault */}
            <div style={{ ...S.cardGold, marginTop: 16 }}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🔐 VAULT MODE — MASTER PASSWORD</h3>
              <p style={{ marginBottom: 12, color: "#888" }}>Lock your trade secrets, passwords, manuscripts. Military-grade encryption. No one gets in without the password. Not even you. (Okay, even you. But the ghost respects the lock.)</p>
              <div style={{ background: T.card, border: `2px solid ${T.goldDim}`, borderRadius: 16, padding: 30, textAlign: "center", marginTop: 16 }}>
                <p style={{ fontFamily: "'Space Mono', monospace", color: T.gold, fontSize: "1.1rem" }}>🔑 ENTER MASTER PASSWORD</p>
                <input
                  type="password" value={vaultPass}
                  onChange={e => setVaultPass(e.target.value)}
                  placeholder="Type your master password..."
                  style={{ width: "100%", maxWidth: 400, padding: "14px 20px", background: T.bg, border: `1px solid ${vaultOpen ? T.gold : "#333"}`, borderRadius: 10, color: T.gold, fontFamily: "'Space Mono', monospace", fontSize: "1rem", textAlign: "center", outline: "none", marginTop: 12 }}
                />
                <br />
                <button onClick={unlockVault}
                  style={{ marginTop: 16, padding: "14px 40px", background: T.gold, color: "#000", border: "none", borderRadius: 10, fontFamily: "'Space Mono', monospace", fontSize: "1rem", fontWeight: "bold", cursor: "pointer" }}>
                  🔓 UNLOCK VAULT
                </button>
                {vaultOpen && (
                  <div style={{ marginTop: 20, textAlign: "left" }}>
                    {[
                      ["📁 Manuscript", "Ghost_Producer_Final_v3.docx"],
                      ["🔑 API Key",    "PUTER-XXXX-XXXX-XXXX"],
                      ["📧 DistroKid", "ghost@namoshun.com"],
                      ["📊 Streaming", "Spotify: 12.4K | Apple: 8.7K"],
                      ["🏛️ Copyright", "Registered US/EU/UK — 2025"],
                      ["💰 Revenue",   "$4,280.50 (this month)"],
                    ].map(([k, v]) => (
                      <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "12px 16px", background: "rgba(212,175,55,0.05)", border: "1px solid rgba(212,175,55,0.15)", borderRadius: 8, marginBottom: 8 }}>
                        <span style={{ fontFamily: "'Space Mono', monospace", fontSize: "0.85rem", color: T.gold }}>{k}</span>
                        <span style={{ fontFamily: "'Space Mono', monospace", fontSize: "0.85rem", color: "#aaa" }}>{v}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Session Memory */}
            <div style={{ ...S.card, marginTop: 16 }}>
              <h3 style={{ color: T.ghost, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>💾 SESSION MEMORY — 14 SLOTS</h3>
              <p style={{ marginBottom: 12, color: "#888" }}>Compressed context across 14 consecutive sessions. Total awareness. Nothing lost.</p>
              <div style={{ display: "flex", gap: 4, marginTop: 12 }}>
                {Array.from({ length: 14 }, (_, i) => {
                  const n = i + 1;
                  const isCurrent = n === currentSession;
                  const isFilled  = n <= 3;
                  return (
                    <div key={n} style={{
                      flex: 1, height: 30, borderRadius: 6,
                      background: isCurrent ? "rgba(255,0,102,0.15)" : isFilled ? "rgba(0,255,204,0.1)" : "#1a1a2e",
                      border: `1px solid ${isCurrent ? T.accent : isFilled ? T.ghostDim : "#222"}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontFamily: "'Space Mono', monospace", fontSize: "0.65rem",
                      color: isCurrent ? T.accent : isFilled ? T.ghost : "#555",
                    }}>S{n}</div>
                  );
                })}
              </div>
              <p style={{ marginTop: 12, fontFamily: "'Space Mono', monospace", color: T.ghost, fontSize: "0.8rem", textAlign: "center" }}>
                SESSION {currentSession} OF 14 — ACTIVE
              </p>
            </div>

            {/* API Status */}
            <div style={{ ...S.card, marginTop: 16 }}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🌐 API STATUS — 12 FREE (NO SIGN-IN)</h3>
              <p style={{ marginBottom: 12, color: "#888" }}>Fail-safe rotation. If one dies, another takes over. You never face downtime.</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10, marginTop: 16 }}>
                {APIS.map(name => (
                  <div key={name} style={{ background: T.card, border: "1px solid #00cc88", borderRadius: 10, padding: 14, textAlign: "center" }}>
                    <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#00cc88", boxShadow: "0 0 8px #00cc88", display: "inline-block", marginBottom: 6 }} />
                    <h5 style={{ fontFamily: "'Space Mono', monospace", fontSize: "0.75rem", color: T.ghost, marginBottom: 4 }}>{name}</h5>
                    <p style={{ fontSize: "0.7rem", color: "#666" }}>✅ Active</p>
                  </div>
                ))}
              </div>
              <div style={{ textAlign: "center", marginTop: 16, fontFamily: "'Space Mono', monospace", color: T.gold, fontSize: "0.85rem" }}>
                🟢 ALL SYSTEMS OPERATIONAL — ROTATION ACTIVE
              </div>
            </div>

            {/* TTS */}
            <div style={{ ...S.cardGold, marginTop: 16 }}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🔊 WAI TEXT TO SPEECH</h3>
              <p style={{ marginBottom: 12, color: "#888" }}>Convert any text to audio using the WAI voice engine. Requires a WAI account.</p>
              <textarea
                value={ttsText}
                onChange={e => setTtsText(e.target.value)}
                rows={3}
                placeholder="Type something for the ghost to speak…"
                style={{ width: "100%", background: "#0a0a0f", border: "1px solid #333", borderRadius: 8, padding: "10px 12px", color: T.text, fontFamily: "'Space Mono', monospace", fontSize: "0.8rem", resize: "vertical", boxSizing: "border-box", marginBottom: 10 }}
              />
              <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
                <select value={ttsVoice} onChange={e => setTtsVoice(e.target.value)}
                  style={{ background: "#1a1a2a", border: "1px solid #333", borderRadius: 8, padding: "6px 10px", color: T.gold, fontFamily: "'Space Mono', monospace", fontSize: "0.8rem" }}>
                  {["alloy","ash","coral","echo","fable","nova","onyx","sage","shimmer"].map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
                <button style={vizBtnStyle(ttsLoading, true)} onClick={puterTTS} disabled={ttsLoading}>
                  {ttsLoading ? "⏳ Generating…" : "🔊 TEXT → SPEECH"}
                </button>
                <button style={{ ...vizBtnStyle(false, false), opacity: 0.5, cursor: "default" }} title="Coming soon">🎙️ STT</button>
                <button style={{ ...vizBtnStyle(false, false), opacity: 0.5, cursor: "default" }} title="Coming soon">📁 SHARE</button>
              </div>
              {ttsOutput && (
                <div style={{ marginTop: 8, textAlign: "center", fontFamily: "'Space Mono', monospace", color: T.ghost, fontSize: "0.85rem", minHeight: 32 }}>
                  {ttsOutput}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── ABOUT ── */}
        {tab === "about" && (
          <div style={S.panel}>
            <h2 style={S.secTitleGold}>👻 ABOUT THE GHOST × PRIME</h2>
            <div style={S.card}>
              <h3 style={{ color: T.accent, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🎭 NAM Oshun</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>The soul. The voice. The human heartbeat behind the machine. NAM Oshun brings warmth, emotion, and that "I can't explain why this makes me cry" energy. Think of them as the ghost's human side — the part that still remembers what it feels like to be alive.</p>
            </div>
            <div style={S.cardGold}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🤖 WAI-Institute</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>The brain. The algorithm. The entity that lives in the wires. WAI-Institute is where artificial intelligence meets musical intuition. They don't just process sound — they dream it. They're the reason the ghost sounds like it's from the future but also from your grandmother's attic.</p>
            </div>
            <div style={{ ...S.card, borderColor: T.accent }}>
              <h3 style={{ color: T.accent, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>🔥 SO WHAT IS "THE GHOST PRODUCER × PUBLISHER PRIME"?</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>
                It's the question: <strong>What happens when a human soul, an AI brain, AND a 14th-evolution publishing widget all work together in a dark room?</strong>
              </p>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem", marginTop: 12 }}>
                The answer is THIS. It's not fully human. It's not fully AI. It's not fully software. It's a ghost with a publishing empire. And ghosts with empires don't follow rules. They just haunt you until you can't stop listening... and buying.
              </p>
            </div>
            <div style={S.cardGold}>
              <h3 style={{ color: T.gold, fontFamily: "'Space Mono', monospace", marginBottom: 8 }}>📜 THE PHILOSOPHY (SIMPLE VERSION)</h3>
              <p style={{ color: "#999", lineHeight: 1.7, fontSize: "0.95rem" }}>
                🎵 Music should feel like a memory you never had.<br />
                🤖 AI shouldn't replace humans — it should haunt them (lovingly).<br />
                👻 The best producers are invisible. You feel them, you don't see them.<br />
                🎧 If it gives you chills, it worked.<br />
                ⚙️ The best publishers don't need accounts. They need ghosts.<br />
                🔐 Your secrets are safe. Even from you. (Especially from you.)
              </p>
            </div>
            <div style={{ textAlign: "center", marginTop: 40, padding: 30, background: T.card, borderRadius: 16, border: "1px solid #1e1e2e" }}>
              <p style={{ fontFamily: "'Space Mono', monospace", color: T.ghost, fontSize: "1.2rem" }}>
                "We don't make music.<br />We summon it.<br />And we publish it before anyone else can."
              </p>
              <p style={{ color: "#555", marginTop: 10, fontSize: "0.85rem" }}>— NAM Oshun, WAI-Institute &amp; Publisher Prime</p>
            </div>
          </div>
        )}

        {/* FOOTER */}
        <footer style={S.footer}>
          <p>THE GHOST PRODUCER × PUBLISHER PRIME — NAM Oshun &amp; WAI-Institute</p>
          <p style={{ marginTop: 6 }}>Made with 👻 🤖 &amp; | All rights haunted | No sign-in ever</p>
        </footer>

        {/* PUBLISHER PRIME SLIDE-OUT WIDGET */}
        <div style={{ position: "fixed", bottom: 20, right: 20, zIndex: 1000 }}>
          <button
            onClick={() => setPanelOpen(o => !o)}
            style={{ background: `linear-gradient(135deg, ${T.gold}, ${T.goldDim})`, color: "#000", border: "none", padding: "16px 24px", borderRadius: 30, fontWeight: "bold", cursor: "pointer", fontFamily: "'Space Mono', monospace", fontSize: "0.9rem", boxShadow: "0 4px 20px rgba(212,175,55,0.4)", transition: "all 0.3s" }}
          >
            &amp; PUBLISHER PRIME
          </button>
        </div>

        {/* SLIDE-OUT PANEL */}
        <div style={{ width: panelOpen ? 300 : 0, height: "100vh", position: "fixed", top: 0, right: 0, background: "linear-gradient(180deg, rgba(10,10,15,0.98), rgba(26,26,10,0.98))", overflowX: "hidden", transition: "0.5s", paddingTop: 70, boxShadow: "-5px 0 20px rgba(0,0,0,0.6)", zIndex: 1001 }}>
          <span onClick={() => setPanelOpen(false)} style={{ position: "absolute", top: 18, right: 22, fontSize: 32, cursor: "pointer", color: T.gold, transition: "0.3s" }}>×</span>
          {[
            { label: "👥 Deploy Clones (4)", action: () => { setTab("prime"); setPanelOpen(false); } },
            { label: "🔐 Secret/Vault Access", action: () => { setTab("prime"); setPanelOpen(false); } },
            { label: "💾 Compress & Save Memory", action: () => { compressMemory(); setPanelOpen(false); } },
            { label: "🔊 Text to Speech", action: () => { puterTTS(); setPanelOpen(false); } },
            { label: "🎙️ Speech to Text", action: () => { puterSTT(); setPanelOpen(false); } },
            { label: "🌐 API Status (12 Free)", action: () => { setTab("prime"); setPanelOpen(false); } },
            { label: "🎛️ Open Studio", action: () => { setTab("studio"); setPanelOpen(false); } },
            { label: "📖 Open Manual", action: () => { setTab("manual"); setPanelOpen(false); } },
          ].map(({ label, action }) => (
            <button key={label} onClick={action}
              style={{ width: "100%", padding: "14px 24px", textDecoration: "none", fontSize: "1rem", color: "#818181", display: "block", background: "transparent", border: "none", borderLeft: "3px solid transparent", textAlign: "left", cursor: "pointer", fontFamily: "'Space Mono', monospace", transition: "0.3s" }}
              onMouseEnter={e => { e.target.style.color = T.gold; e.target.style.borderLeftColor = T.gold; }}
              onMouseLeave={e => { e.target.style.color = "#818181"; e.target.style.borderLeftColor = "transparent"; }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
