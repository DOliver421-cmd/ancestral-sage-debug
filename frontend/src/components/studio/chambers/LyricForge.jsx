import { useState } from "react";
import { api } from "../../../lib/api";
import { toast } from "sonner";
import { Wand2, Copy, Check, RefreshCw } from "lucide-react";

const STYLES = ["Hip-Hop", "R&B", "Gospel", "Spoken Word", "Trap", "Neo-Soul", "Afrobeats", "Reggae", "Folk", "Pop"];
const MOODS = ["Triumphant", "Reflective", "Angry", "Joyful", "Melancholic", "Spiritual", "Romantic", "Raw", "Peaceful"];
const STRUCTURES = ["Verse", "Hook / Chorus", "Bridge", "Full Song (V/C/V/C/B/C)", "Freestyle Bars", "Intro / Outro"];

export default function LyricForge({ tier = "base" }) {
  const [form, setForm] = useState({ topic: "", style: "Hip-Hop", mood: "Triumphant", structure: "Verse", notes: "" });
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    if (!form.topic.trim()) { toast.error("Give me a topic or concept to write about."); return; }
    setLoading(true);
    setResult("");
    try {
      const r = await api.post("/studio/lyric", form);
      setResult(r.data.lyrics);
    } catch {
      toast.error("The Forge went cold — try again.");
    } finally {
      setLoading(false);
    }
  };

  const copy = () => {
    navigator.clipboard?.writeText(result).then(() => {
      setCopied(true);
      toast.success("Lyrics copied.");
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={{ fontFamily: "inherit", color: "rgba(255,255,255,0.9)", height: "100%", display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Controls */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
        <div>
          <label style={labelStyle}>Genre / Style</label>
          <select style={selectStyle} value={form.style} onChange={e => setForm(f => ({ ...f, style: e.target.value }))}>
            {STYLES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Mood / Energy</label>
          <select style={selectStyle} value={form.mood} onChange={e => setForm(f => ({ ...f, mood: e.target.value }))}>
            {MOODS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Structure</label>
          <select style={selectStyle} value={form.structure} onChange={e => setForm(f => ({ ...f, structure: e.target.value }))}>
            {STRUCTURES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label style={labelStyle}>Topic / Concept *</label>
        <input
          style={inputStyle}
          value={form.topic}
          onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}
          placeholder="e.g. overcoming doubt, Black excellence, losing someone you love, building from nothing..."
          maxLength={300}
        />
      </div>

      <div>
        <label style={labelStyle}>Extra notes (optional)</label>
        <textarea
          style={{ ...inputStyle, height: 60, resize: "none" }}
          value={form.notes}
          onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          placeholder="Specific words, references, rhyme scheme, flow style..."
          maxLength={500}
        />
      </div>

      <button
        onClick={generate}
        disabled={loading}
        style={{
          background: loading ? "rgba(184,134,11,0.3)" : "linear-gradient(135deg, #b8860b, #d4a017)",
          border: "none", color: "#0a0a0f", fontWeight: 900, fontSize: 13,
          padding: "12px 24px", cursor: loading ? "default" : "pointer",
          letterSpacing: "0.08em", textTransform: "uppercase", fontFamily: "monospace",
          display: "flex", alignItems: "center", gap: 8, alignSelf: "flex-start",
          boxShadow: loading ? "none" : "0 4px 0 #7a5c0a",
        }}
      >
        {loading ? <RefreshCw style={{ width: 14, height: 14, animation: "spin 1s linear infinite" }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
        {loading ? "Forging..." : "Forge Lyrics"}
      </button>

      {/* Output */}
      {result && (
        <div style={{ flex: 1, position: "relative" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label style={labelStyle}>Output</label>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={generate} style={actionBtn} title="Regenerate">
                <RefreshCw style={{ width: 12, height: 12 }} />
              </button>
              <button onClick={copy} style={{ ...actionBtn, background: copied ? "rgba(34,197,94,0.2)" : "rgba(184,134,11,0.15)" }}>
                {copied ? <Check style={{ width: 12, height: 12 }} /> : <Copy style={{ width: 12, height: 12 }} />}
                <span style={{ fontSize: 11 }}>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </div>
          <textarea
            readOnly
            value={result}
            style={{
              ...inputStyle,
              height: 280,
              resize: "vertical",
              fontFamily: "monospace",
              fontSize: 13,
              lineHeight: 1.8,
              color: "#ffd700",
              background: "rgba(0,0,0,0.4)",
              border: "1px solid rgba(184,134,11,0.4)",
            }}
          />
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 10, fontFamily: "monospace", letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(184,134,11,0.8)", marginBottom: 6 };
const inputStyle = { width: "100%", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(184,134,11,0.25)", padding: "9px 12px", color: "rgba(255,255,255,0.9)", fontSize: 13, fontFamily: "inherit", outline: "none", borderRadius: 4, boxSizing: "border-box" };
const selectStyle = { ...inputStyle, cursor: "pointer" };
const actionBtn = { background: "rgba(184,134,11,0.15)", border: "1px solid rgba(184,134,11,0.3)", color: "#b8860b", padding: "5px 10px", cursor: "pointer", borderRadius: 4, display: "flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 700 };
