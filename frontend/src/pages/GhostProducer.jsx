import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

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

const TRACKS = [
  { icon:"🌊", name:"Ethereal Drift",   bpm:"85 BPM — Ambient Pad",   mode:"ghost" },
  { icon:"💀", name:"Ghost Kick",       bpm:"90 BPM — 808 Sub",        mode:"chaos" },
  { icon:"🗣️", name:"NAM Whisper",      bpm:"90 BPM — Vocal Chops",    mode:"human" },
  { icon:"🧠", name:"WAI Cortex",       bpm:"140 BPM — AI Synth Lead", mode:"chaos" },
  { icon:"🥁", name:"Phantom Hi-Hat",   bpm:"90 BPM — Percussion",     mode:"ghost" },
  { icon:"📡", name:"Soul Frequency",   bpm:"88 BPM — Bass Line",      mode:"human" },
  { icon:"🌫️", name:"Haunted Reverb",   bpm:"FREE — FX / Atmosphere",  mode:"ghost" },
];

/* ── Clone definitions with AI system prompts ───────────────────────────── */
const CLONES = [
  {
    id: "editor",
    icon: "📝",
    label: "Ghost Editor",
    desc: "Fixes manuscripts, formats content, sharpens prose. Keen eye. No sleep needed.",
    color: T.ghost,
    placeholder: "Paste your text, lyrics, script, or manuscript here…",
    system: "You are the Ghost Editor — a ruthless, brilliant manuscript editor. You fix grammar, sharpen prose, improve flow, restructure sentences for impact, and cut dead weight. Be direct and precise. Return the edited version followed by a brief note on the key changes made.",
    btnLabel: "✍️ Edit This",
  },
  {
    id: "publicist",
    icon: "📢",
    label: "Ghost Publicist",
    desc: "Social media algorithms, streaming platforms, press releases. Makes you unavoidable.",
    color: "#a855f7",
    placeholder: "Describe your release, project, or what you want to promote…",
    system: "You are the Ghost Publicist — a ruthless music/content publicist who knows every platform algorithm. Generate press releases, social media post packages (Twitter/X, Instagram, TikTok, LinkedIn), pitch emails to blogs/playlists, and streaming platform bio copy. Make the artist sound legendary.",
    btnLabel: "📣 Generate Press Kit",
  },
  {
    id: "legal",
    icon: "⚖️",
    label: "Ghost Legal",
    desc: "Copyright guidance, contract templates, publishing rights. Kemetic knowledge on retainer.",
    color: T.warn,
    placeholder: "Describe your situation — song ownership, samples, contracts, licensing…",
    system: "You are the Ghost Legal advisor — an expert in music copyright, publishing rights, trademark, licensing, and contract basics. Give clear, practical guidance. Flag risks. Suggest contract language. Remind the user this is informational, not legal representation, and they should consult an attorney for binding agreements.",
    btnLabel: "⚖️ Get Legal Guidance",
  },
  {
    id: "marketer",
    icon: "📈",
    label: "Ghost Marketer",
    desc: "Chess-level strategy. Visual art direction. Crushes competition before they know you exist.",
    color: T.accent,
    placeholder: "Describe your music, brand, target audience, and goals…",
    system: "You are the Ghost Marketer — a chess-level music marketing strategist. Create release strategies, rollout timelines, visual art direction briefs, playlist pitching strategies, email campaign copy, and audience targeting plans. Think 3 moves ahead. Make every campaign feel inevitable in hindsight.",
    btnLabel: "🎯 Build Strategy",
  },
];

/* ── styles ──────────────────────────────────────────────────────────────── */
const S = {
  page:     { background: T.bg, color: T.text, fontFamily: "'Inter', sans-serif", minHeight: "100vh", overflowX: "hidden" },
  hero:     { textAlign: "center", padding: "50px 20px 30px", position: "relative", zIndex: 1 },
  h1:       { fontFamily: "monospace", fontSize: "clamp(1.8rem,5vw,4rem)", color: T.ghost, textShadow: `0 0 40px rgba(0,255,204,0.4)`, lineHeight: 1.1, marginBottom: 5 },
  h2gold:   { fontFamily: "monospace", fontSize: "clamp(1rem,3vw,1.6rem)", color: T.gold, textShadow: `0 0 30px rgba(212,175,55,0.3)`, marginBottom: 10 },
  byline:   { fontSize: "1rem", color: "#888", marginTop: 8, letterSpacing: 3, textTransform: "uppercase" },
  tag:      { display: "inline-block", marginTop: 18, padding: "8px 24px", border: `1px solid ${T.ghostDim}`, borderRadius: 50, color: T.ghost, fontFamily: "monospace", fontSize: "0.85rem", background: "rgba(0,255,204,0.05)" },
  tagGold:  { display: "inline-block", marginTop: 10, marginLeft: 8, padding: "8px 24px", border: `1px solid ${T.goldDim}`, borderRadius: 50, color: T.gold, fontFamily: "monospace", fontSize: "0.85rem", background: "rgba(212,175,55,0.05)" },
  tabs:     { display: "flex", justifyContent: "center", gap: 8, padding: "16px", flexWrap: "wrap", position: "relative", zIndex: 1 },
  panel:    { maxWidth: 900, margin: "0 auto", padding: "20px 30px 80px", position: "relative", zIndex: 1 },
  secTitle: { fontFamily: "monospace", fontSize: "1.4rem", color: T.ghost, marginBottom: 20, paddingBottom: 10, borderBottom: "1px solid #222" },
  secTitleGold: { fontFamily: "monospace", fontSize: "1.4rem", color: T.gold, marginBottom: 20, paddingBottom: 10, borderBottom: `1px solid ${T.goldDim}` },
  card:     { background: T.card, border: "1px solid #1e1e2e", borderRadius: 16, padding: 20, marginBottom: 16 },
  cardGold: { background: T.card, border: `1px solid ${T.goldDim}`, borderRadius: 16, padding: 20, marginBottom: 16 },
  footer:   { textAlign: "center", padding: "40px 20px", color: "#444", fontSize: "0.8rem", position: "relative", zIndex: 1 },
};

function tabBtnStyle(active, gold = false) {
  return {
    padding: "12px 24px",
    border: active ? `1px solid ${gold ? T.gold : T.ghost}` : "1px solid #333",
    background: active ? (gold ? "rgba(212,175,55,0.1)" : "rgba(0,255,204,0.1)") : T.card,
    color: active ? (gold ? T.gold : T.ghost) : "#aaa",
    borderRadius: 12, cursor: "pointer",
    fontFamily: "monospace", fontSize: "0.82rem",
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
    fontFamily: "monospace", fontSize: "0.85rem",
    transition: "all 0.3s",
  };
}

/* ── Clone Panel — real AI ──────────────────────────────────────────────── */
function ClonePanel({ clone, onClose }) {
  const [input, setInput]     = useState("");
  const [output, setOutput]   = useState("");
  const [loading, setLoading] = useState(false);

  async function run() {
    const text = input.trim();
    if (!text) return;
    setLoading(true);
    setOutput("");
    try {
      const res = await api.post("/ai/chat", {
        messages: [{ role: "user", content: text }],
        system: clone.system,
        persona_label: `ghost_${clone.id}`,
        max_tokens: 1200,
      });
      setOutput(res.data?.response || res.data?.text || "No response.");
    } catch (e) {
      setOutput("⚠️ " + (e?.response?.data?.detail || e?.message || "Request failed."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 2000,
      background: "rgba(0,0,0,0.85)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 20,
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{
        background: "#0e0e16", border: `1px solid ${clone.color}40`,
        borderRadius: 20, padding: 32, maxWidth: 640, width: "100%",
        maxHeight: "90vh", overflowY: "auto",
        boxShadow: `0 0 60px ${clone.color}20`,
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: "monospace", fontSize: "1.2rem", color: clone.color, fontWeight: 700 }}>
              {clone.icon} {clone.label}
            </div>
            <div style={{ fontSize: "0.85rem", color: "#666", marginTop: 4 }}>{clone.desc}</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#666", fontSize: 24, cursor: "pointer" }}>×</button>
        </div>

        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          rows={6}
          placeholder={clone.placeholder}
          style={{
            width: "100%", background: "#060608", border: `1px solid ${clone.color}30`,
            borderRadius: 10, padding: "12px 14px", color: T.text,
            fontFamily: "monospace", fontSize: "0.85rem", resize: "vertical",
            boxSizing: "border-box", marginBottom: 12, outline: "none",
          }}
        />

        <button
          onClick={run}
          disabled={loading || !input.trim()}
          style={{
            width: "100%", padding: "14px", background: loading ? "#222" : clone.color,
            color: loading ? "#666" : "#000", border: "none", borderRadius: 10,
            fontFamily: "monospace", fontWeight: 700, fontSize: "0.95rem", cursor: loading ? "default" : "pointer",
            marginBottom: 20, transition: "all 0.3s",
          }}
        >
          {loading ? "⏳ The ghost is working…" : clone.btnLabel}
        </button>

        {output && (
          <div style={{
            background: "#060608", border: `1px solid ${clone.color}20`,
            borderRadius: 10, padding: 20,
          }}>
            <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: clone.color, marginBottom: 12, opacity: 0.7 }}>
              ✦ {clone.label.toUpperCase()} OUTPUT
            </div>
            <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word", color: "#ccc", fontSize: "0.9rem", lineHeight: 1.7, margin: 0, fontFamily: "inherit" }}>
              {output}
            </pre>
            <button
              onClick={() => navigator.clipboard?.writeText(output)}
              style={{ marginTop: 14, background: "transparent", border: `1px solid ${clone.color}40`, color: clone.color, borderRadius: 8, padding: "6px 16px", fontFamily: "monospace", fontSize: "0.78rem", cursor: "pointer" }}
            >
              📋 Copy Output
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── main component ─────────────────────────────────────────────────────── */
export default function GhostProducer() {
  const { user } = useAuth();
  const [tab, setTab]               = useState("clones");
  const [isPlaying, setIsPlaying]   = useState(false);
  const [mode, setMode]             = useState("ghost");
  const [bpm, setBpm]               = useState(90);
  const [mix, setMix]               = useState(50);
  const [activeTrack, setActiveTrack] = useState(null);
  const [activeClone, setActiveClone] = useState(null);
  const [ttsOutput, setTtsOutput]   = useState("");
  const [ttsText, setTtsText]       = useState("");
  const [ttsVoice, setTtsVoice]     = useState("sage");
  const [ttsLoading, setTtsLoading] = useState(false);
  const ttsAudioRef = useRef(null);

  const canvasRef  = useRef(null);
  const rafRef     = useRef(null);
  const timeRef    = useRef(0);
  const playRef    = useRef(false);
  const modeRef    = useRef("ghost");
  const bpmRef     = useRef(90);
  const mixRef     = useRef(50);

  useEffect(() => { playRef.current = isPlaying; }, [isPlaying]);
  useEffect(() => { modeRef.current = mode; },    [mode]);
  useEffect(() => { bpmRef.current  = bpm; },     [bpm]);
  useEffect(() => { mixRef.current  = mix; },     [mix]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => { canvas.width = canvas.offsetWidth * 2; canvas.height = canvas.offsetHeight * 2; };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => { drawFrame(); }, []); // eslint-disable-line

  function drawFrame() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.offsetWidth; const h = canvas.offsetHeight;
    const t = timeRef.current; const m = modeRef.current; const ml = mixRef.current;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save(); ctx.scale(2, 2);
    const barCount = 64; const barW = w / barCount - 2;
    for (let i = 0; i < barCount; i++) {
      let barH;
      if      (m === "ghost")  barH = Math.sin(t * 0.03 + i * 0.2) * 30 + Math.sin(t * 0.07 + i * 0.1) * 20 + 40;
      else if (m === "human")  barH = Math.sin(t * 0.05 + i * 0.3) * 50 + Math.cos(t * 0.02 + i * 0.15) * 30 + 50;
      else if (m === "chaos")  barH = Math.random() * 80 + 20 + Math.sin(t * 0.1 + i) * 40;
      else                     barH = Math.sin(t * 0.04 + i * 0.25) * 45 + Math.cos(t * 0.06 + i * 0.2) * 25 + 55;
      const r = ml > 50 ? 255 : 0; const g = ml < 50 ? 255 : 0; const b = 200;
      const a = 0.4 + (barH / 120) * 0.6;
      ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
      ctx.shadowBlur = 15; ctx.shadowColor = `rgba(${r},${g},${b},0.5)`;
      ctx.fillRect(i * (barW + 2), h - barH, barW, barH);
      ctx.shadowBlur = 0;
    }
    ctx.beginPath();
    const waveColor = m === "ghost" ? "rgba(0,255,204,0.3)" : m === "human" ? "rgba(255,0,102,0.3)" : m === "chaos" ? "rgba(255,170,0,0.3)" : "rgba(212,175,55,0.3)";
    ctx.strokeStyle = waveColor; ctx.lineWidth = 2;
    for (let x = 0; x < w; x++) {
      const y = h / 2 + Math.sin(x * 0.02 + t * 0.05) * 20 * (m === "chaos" ? 2 : 1);
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke(); ctx.restore();
    if (playRef.current) {
      timeRef.current += bpmRef.current / 30;
      rafRef.current = requestAnimationFrame(drawFrame);
    }
  }

  function togglePlay() {
    const next = !isPlaying; setIsPlaying(next); playRef.current = next;
    if (next) drawFrame(); else cancelAnimationFrame(rafRef.current);
  }
  function handleMode(m) { setMode(m); modeRef.current = m; if (!isPlaying) drawFrame(); }
  function handleTrack(track) { setActiveTrack(track.name); modeRef.current = track.mode; setMode(track.mode); }

  async function puterTTS() {
    const text = ttsText.trim();
    if (!text) { setTtsOutput("⚠️ Enter text above to convert."); return; }
    setTtsLoading(true); setTtsOutput("🔄 Generating audio…");
    try {
      const resp = await api.post("/ai/sage/tts", { text, voice: ttsVoice, speed: 1.0, session_id: "ghost_producer" }, { responseType: "blob" });
      const url = URL.createObjectURL(resp.data);
      if (ttsAudioRef.current) { ttsAudioRef.current.pause(); URL.revokeObjectURL(ttsAudioRef.current.src); }
      const audio = new Audio(url); ttsAudioRef.current = audio; audio.play();
      setTtsOutput("🔊 Playing — voice: " + ttsVoice);
    } catch (e) {
      setTtsOutput("⚠️ " + (e?.response?.data?.detail || e?.message || "TTS failed"));
    } finally { setTtsLoading(false); }
  }

  return (
    <>
      {/* Context bar */}
      <div style={{ position: "sticky", top: 0, zIndex: 50, background: "#0d0818", borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "0 24px", height: 40, display: "flex", alignItems: "center", gap: 16 }}>
        <Link to="/profile" style={{ color: "#ff0066", textDecoration: "none", fontSize: 12, fontFamily: "monospace", fontWeight: 700, display: "flex", alignItems: "center", gap: 6 }}>
          ← My Profile
        </Link>
        <div style={{ width: 1, height: 16, background: "rgba(255,255,255,0.1)" }} />
        {[
          { label: "Social Blast", to: "/social/publish" },
          { label: "Studio", to: "/studio" },
          { label: "Earnings", to: "/creator/earnings" },
          { label: "Lounge", to: "/creator-lounge" },
        ].map(f => (
          <Link key={f.to} to={f.to} style={{ color: "rgba(255,255,255,0.3)", textDecoration: "none", fontSize: 11, fontFamily: "monospace", letterSpacing: "0.06em" }}>
            {f.label}
          </Link>
        ))}
      </div>

      {activeClone && <ClonePanel clone={activeClone} onClose={() => setActiveClone(null)} />}

      <div style={S.page}>
        {/* HERO */}
        <div style={S.hero}>
          <h1 style={S.h1}>THE <span style={{ color: T.accent, textShadow: "0 0 40px rgba(255,0,102,0.4)" }}>GHOST</span> PRODUCER</h1>
          <h2 style={S.h2gold}>× PUBLISHER PRIME v14</h2>
          <div style={S.byline}>NAM Oshun &amp; WAI-Institute × 14th Evolution</div>
          <div style={S.tag}>🎧 AI-POWERED PRODUCTION SUITE</div>
          <div style={S.tagGold}>⚙️ PUBLISHER PRIME ACTIVE</div>
        </div>

        {/* TABS */}
        <div style={S.tabs}>
          {[
            { id: "clones",  label: "👥 Clone Army",      gold: false },
            { id: "studio",  label: "🎛️ Studio",           gold: false },
            { id: "tracks",  label: "🎵 Tracks",           gold: false },
            { id: "tts",     label: "🔊 Voice",            gold: false },
            { id: "about",   label: "👻 About",            gold: false },
          ].map(({ id, label, gold }) => (
            <button key={id} style={tabBtnStyle(tab === id, gold)} onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>

        {/* ── CLONE ARMY ── */}
        {tab === "clones" && (
          <div style={S.panel}>
            <h2 style={S.secTitleGold}>👥 CLONE ARMY — 4 AI PERSONAS</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>
              Click any clone to activate it. Each one is a specialized AI that will do the work for you.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20 }}>
              {CLONES.map(c => (
                <div key={c.id}
                  onClick={() => setActiveClone(c)}
                  style={{
                    background: T.card, border: `1px solid ${c.color}30`,
                    borderRadius: 16, padding: 24, textAlign: "center", cursor: "pointer",
                    transition: "all 0.3s",
                    boxShadow: "none",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.border = `1px solid ${c.color}80`; e.currentTarget.style.boxShadow = `0 0 24px ${c.color}20`; e.currentTarget.style.transform = "translateY(-2px)"; }}
                  onMouseLeave={e => { e.currentTarget.style.border = `1px solid ${c.color}30`; e.currentTarget.style.boxShadow = "none"; e.currentTarget.style.transform = "none"; }}
                >
                  <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>{c.icon}</div>
                  <h4 style={{ fontFamily: "monospace", color: c.color, marginBottom: 8, fontSize: "1rem" }}>{c.label}</h4>
                  <p style={{ color: "#888", fontSize: "0.85rem", lineHeight: 1.6, marginBottom: 16 }}>{c.desc}</p>
                  <div style={{
                    display: "inline-block", padding: "8px 20px",
                    border: `1px solid ${c.color}50`, borderRadius: 8,
                    color: c.color, fontFamily: "monospace", fontSize: "0.8rem",
                    background: `${c.color}10`,
                  }}>
                    {c.btnLabel}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── STUDIO ── */}
        {tab === "studio" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>🎛️ THE GHOST STUDIO</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>Interactive visualizer. Click play and adjust the controls.</p>
            <div style={{ background: T.card, border: "1px solid #1e1e2e", borderRadius: 16, padding: 30, textAlign: "center" }}>
              <canvas ref={canvasRef} style={{ width: "100%", maxWidth: 600, height: 200, borderRadius: 12, background: "#000", display: "block", margin: "0 auto" }} />
              <div style={{ marginTop: 20, display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
                <button style={vizBtnStyle(isPlaying)} onClick={togglePlay}>{isPlaying ? "⏸ PAUSE" : "▶ PLAY"}</button>
                {[{id:"ghost",label:"👻 GHOST"},{id:"human",label:"🧍 HUMAN"},{id:"chaos",label:"🌀 CHAOS"},{id:"prime",label:"✦ PRIME",gold:true}].map(({id,label,gold}) => (
                  <button key={id} style={vizBtnStyle(mode===id,gold)} onClick={() => handleMode(id)}>{label}</button>
                ))}
              </div>
            </div>
            <div style={{ marginTop: 24 }}>
              <div style={S.card}>
                <h3 style={{ color: T.accent, fontFamily: "monospace", marginBottom: 8 }}>🎚️ BPM CONTROL</h3>
                <input type="range" min="60" max="180" value={bpm}
                  style={{ width: "100%", accentColor: T.ghost, height: 8, cursor: "pointer" }}
                  onChange={e => { const v = parseInt(e.target.value); setBpm(v); bpmRef.current = v; }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", color: T.ghost, fontSize: "0.85rem", marginTop: 8 }}>
                  <span>🐢 60</span><span>{bpm} BPM</span><span>🐇 180</span>
                </div>
              </div>
              <div style={{ ...S.card, marginTop: 12 }}>
                <h3 style={{ color: T.gold, fontFamily: "monospace", marginBottom: 8 }}>📊 GHOST MIX — AI vs Human</h3>
                <input type="range" min="0" max="100" value={mix}
                  style={{ width: "100%", accentColor: T.accent, height: 8, cursor: "pointer" }}
                  onChange={e => { const v = parseInt(e.target.value); setMix(v); mixRef.current = v; }} />
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "monospace", fontSize: "0.85rem", marginTop: 8 }}>
                  <span style={{ color: T.accent }}>100% WAI</span>
                  <span style={{ color: T.ghost }}>{mix}/{100-mix}</span>
                  <span style={{ color: T.ghost }}>100% Human</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TRACKS ── */}
        {tab === "tracks" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>🎵 TRACK BREAKDOWN</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>Click any track to set the visualizer mode.</p>
            {TRACKS.map(t => (
              <div key={t.name} onClick={() => { handleTrack(t); setTab("studio"); }}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px", background: activeTrack === t.name ? "rgba(0,255,204,0.08)" : T.card, border: `1px solid ${activeTrack === t.name ? T.ghost : "#1e1e2e"}`, borderRadius: 12, marginBottom: 8, cursor: "pointer", transition: "all 0.3s" }}
              >
                <span style={{ fontWeight: 600 }}>{t.icon} {t.name}</span>
                <span style={{ fontFamily: "monospace", color: T.ghost, fontSize: "0.85rem" }}>{t.bpm}</span>
              </div>
            ))}
          </div>
        )}

        {/* ── VOICE (TTS) ── */}
        {tab === "tts" && (
          <div style={S.panel}>
            <h2 style={S.secTitle}>🔊 WAI VOICE ENGINE</h2>
            <p style={{ color: "#777", marginBottom: 24 }}>Convert any text to audio using the WAI voice engine.</p>
            <div style={S.cardGold}>
              <textarea value={ttsText} onChange={e => setTtsText(e.target.value)} rows={5}
                placeholder="Type something for the ghost to speak…"
                style={{ width: "100%", background: "#0a0a0f", border: "1px solid #333", borderRadius: 8, padding: "12px 14px", color: T.text, fontFamily: "monospace", fontSize: "0.85rem", resize: "vertical", boxSizing: "border-box", marginBottom: 16, outline: "none" }}
              />
              <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
                <select value={ttsVoice} onChange={e => setTtsVoice(e.target.value)}
                  style={{ background: "#1a1a2a", border: "1px solid #333", borderRadius: 8, padding: "8px 12px", color: T.gold, fontFamily: "monospace", fontSize: "0.85rem" }}>
                  {["alloy","ash","coral","echo","fable","nova","onyx","sage","shimmer"].map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
                <button style={{ ...vizBtnStyle(ttsLoading, true), flex: 1 }} onClick={puterTTS} disabled={ttsLoading}>
                  {ttsLoading ? "⏳ Generating…" : "🔊 Convert to Speech"}
                </button>
              </div>
              {ttsOutput && (
                <div style={{ textAlign: "center", fontFamily: "monospace", color: T.ghost, fontSize: "0.85rem", padding: "12px 0" }}>
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
              <h3 style={{ color: T.accent, fontFamily: "monospace", marginBottom: 8 }}>🎭 NAM Oshun</h3>
              <p style={{ color: "#999", lineHeight: 1.7 }}>The soul. The voice. The human heartbeat behind the machine. NAM Oshun brings warmth, emotion, and that "I can't explain why this makes me cry" energy.</p>
            </div>
            <div style={S.cardGold}>
              <h3 style={{ color: T.gold, fontFamily: "monospace", marginBottom: 8 }}>🤖 WAI-Institute</h3>
              <p style={{ color: "#999", lineHeight: 1.7 }}>The brain. The algorithm. The entity that lives in the wires. WAI-Institute is where artificial intelligence meets musical intuition.</p>
            </div>
            <div style={{ textAlign: "center", marginTop: 40, padding: 30, background: T.card, borderRadius: 16 }}>
              <p style={{ fontFamily: "monospace", color: T.ghost, fontSize: "1.2rem" }}>
                "We don't make music.<br />We summon it.<br />And we publish it before anyone else can."
              </p>
              <p style={{ color: "#555", marginTop: 10, fontSize: "0.85rem" }}>— NAM Oshun, WAI-Institute &amp; Publisher Prime</p>
            </div>
          </div>
        )}

        <footer style={S.footer}>
          <p>THE GHOST PRODUCER × PUBLISHER PRIME — NAM Oshun &amp; WAI-Institute</p>
          <p style={{ marginTop: 6 }}>All rights haunted | Powered by WAI AI</p>
        </footer>
      </div>
    </>
  );
}
