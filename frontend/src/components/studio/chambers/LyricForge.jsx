import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Wand2, Copy, Check, RefreshCw, Save } from "lucide-react";

const STYLES = ["Neo-Soul", "Hip-Hop", "R&B", "Gospel", "Spoken Word", "Trap", "Afrobeats", "Reggae", "Folk", "Pop"];
const MOODS = ["Uplifting", "Triumphant", "Reflective", "Angry", "Joyful", "Melancholic", "Spiritual", "Romantic", "Raw", "Peaceful"];
const STRUCTURES = ["Verse", "Hook / Chorus", "Bridge", "Full Song (V/C/V/C/B/C)", "Freestyle Bars", "Intro / Outro"];

const CYAN = "#22d3ee";
const CYAN_SOFT = "rgba(34,211,238,0.12)";

export default function LyricForge({ tier = "base", sovereignDispatch, artifact, activeProject, onSaveVersion }) {
  const [form, setForm] = useState({
    topic: "City Lights",
    genre: "Neo-Soul",
    mood: "Uplifting",
    structure: "Verse",
    notes: "Groovy, soulful, inspiring",
  });
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Sovereign delivers the generated lyrics back through CreatorStudio.
  useEffect(() => {
    if (artifact) {
      setResult(artifact);
      setLoading(false);
    }
  }, [artifact]);

  const generate = async () => {
    if (!form.topic.trim()) { toast.error("Give me a topic or concept to write about."); return; }
    if (!sovereignDispatch?.current) { toast.error("Sovereign is not connected."); return; }
    setLoading(true);
    setResult("");
    try {
      await sovereignDispatch.current({
        action: "generate_lyrics",
        context: { genre: form.genre, mood: form.mood, structure: form.structure, topic: form.topic, notes: form.notes },
        message: `Forge ${form.structure} lyrics — ${form.genre}, ${form.mood} mood, topic: ${form.topic}`,
        silent: true,
      });
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

  const saveVersion = () => {
    if (!result) { toast.error("Generate lyrics first."); return; }
    if (!activeProject) { toast.error("Open a project first (+ New Project) to save versions."); return; }
    if (!onSaveVersion) { toast.error("Save is not connected."); return; }
    onSaveVersion("lyrics", result, `${form.genre} · ${form.mood} · ${form.structure}`);
  };

  return (
    <div style={{ color: "rgba(255,255,255,0.92)", height: "100%", display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Filter row — Genre / Mood / Structure / Topic */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 10 }}>
        <div>
          <label style={labelStyle}>Genre</label>
          <select style={selectStyle} value={form.genre} onChange={(e) => setForm((f) => ({ ...f, genre: e.target.value }))}>
            {STYLES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Mood</label>
          <select style={selectStyle} value={form.mood} onChange={(e) => setForm((f) => ({ ...f, mood: e.target.value }))}>
            {MOODS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Structure</label>
          <select style={selectStyle} value={form.structure} onChange={(e) => setForm((f) => ({ ...f, structure: e.target.value }))}>
            {STRUCTURES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Topic</label>
          <input
            style={inputStyle}
            value={form.topic}
            onChange={(e) => setForm((f) => ({ ...f, topic: e.target.value }))}
            placeholder="e.g. overcoming doubt, city lights, building from nothing..."
            maxLength={300}
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label style={labelStyle}>Notes</label>
        <textarea
          style={{ ...inputStyle, height: 52, resize: "none" }}
          value={form.notes}
          onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          placeholder="Specific words, references, rhyme scheme, flow style..."
          maxLength={500}
        />
      </div>

      {/* Action toolbar */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <button
          onClick={generate}
          disabled={loading}
          style={{
            display: "flex", alignItems: "center", gap: 7, padding: "8px 16px", borderRadius: 9,
            background: CYAN, border: "none", color: "#061018", fontWeight: 800, fontSize: 12.5,
            cursor: loading ? "default" : "pointer", opacity: loading ? 0.7 : 1,
            boxShadow: "0 2px 12px rgba(34,211,238,0.3)",
          }}
        >
          {loading ? <RefreshCw style={{ width: 14, height: 14, animation: "csSpin 1s linear infinite" }} /> : <Wand2 style={{ width: 14, height: 14 }} />}
          {loading ? "Forging…" : "Generate"}
        </button>
        <button onClick={generate} style={actionBtn} title="Regenerate" disabled={loading}>
          <RefreshCw style={{ width: 13, height: 13 }} /> Regenerate
        </button>
        <button onClick={copy} style={{ ...actionBtn, background: copied ? "rgba(52,211,153,0.14)" : "rgba(255,255,255,0.05)" }}>
          {copied ? <Check style={{ width: 13, height: 13 }} /> : <Copy style={{ width: 13, height: 13 }} />}
          {copied ? "Copied" : "Copy"}
        </button>
        <button onClick={saveVersion} style={{ ...actionBtn, color: "#34d399", borderColor: "rgba(52,211,153,0.3)", background: "rgba(52,211,153,0.1)" }} title="Save this version to the active project">
          <Save style={{ width: 13, height: 13 }} /> Save Version
        </button>
      </div>

      {/* Output */}
      {result && (
        <div style={{ flex: 1, position: "relative", display: "flex", flexDirection: "column" }}>
          <label style={{ ...labelStyle, marginBottom: 8 }}>Output</label>
          <textarea
            value={result}
            onChange={(e) => setResult(e.target.value)}
            style={{
              flex: 1, minHeight: 220, resize: "vertical",
              fontFamily: MONO, fontSize: 13.5, lineHeight: 1.9,
              color: "#a5f3fc", background: "#12161f",
              border: "1px solid rgba(34,211,238,0.25)",
              padding: 14, outline: "none", borderRadius: 10, boxSizing: "border-box", width: "100%",
            }}
          />
        </div>
      )}

      <style>{`
        @keyframes csSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

const MONO = "'SF Mono', 'Cascadia Code', Consolas, monospace";
const labelStyle = { display: "block", fontSize: 9.5, fontFamily: MONO, letterSpacing: "0.14em", textTransform: "uppercase", color: "rgba(255,255,255,0.5)", marginBottom: 6 };
const inputStyle = { width: "100%", background: "#12161f", border: "1px solid rgba(255,255,255,0.09)", padding: "9px 12px", color: "rgba(255,255,255,0.92)", fontSize: 13, fontFamily: "inherit", outline: "none", borderRadius: 8, boxSizing: "border-box" };
const selectStyle = { ...inputStyle, cursor: "pointer" };
const actionBtn = { background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", color: "#cbd5e1", padding: "8px 12px", cursor: "pointer", borderRadius: 8, display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontWeight: 700 };
