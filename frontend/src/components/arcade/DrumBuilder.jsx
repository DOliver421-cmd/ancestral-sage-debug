import { useRef, useState, useEffect, useCallback } from "react";

const INSTRUMENTS = [
  { id: "djembe", label: "Djembe", color: "#b8860b", freq: 80, type: "drum" },
  { id: "bass", label: "Bass Drum", color: "#c0392b", freq: 50, type: "bass" },
  { id: "shekere", label: "Shekere", color: "#27ae60", freq: 1200, type: "shaker" },
  { id: "bell", label: "Bell", color: "#2980b9", freq: 900, type: "bell" },
];
const STEPS = 8;

function playSound(audioCtx, instrument) {
  const now = audioCtx.currentTime;
  const gain = audioCtx.createGain();
  gain.connect(audioCtx.destination);

  if (instrument.type === "drum" || instrument.type === "bass") {
    const osc = audioCtx.createOscillator();
    osc.type = "sine";
    osc.frequency.setValueAtTime(instrument.freq, now);
    osc.frequency.exponentialRampToValueAtTime(instrument.freq * 0.1, now + 0.15);
    gain.gain.setValueAtTime(1, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
    osc.connect(gain);
    osc.start(now);
    osc.stop(now + 0.2);
  } else if (instrument.type === "shaker") {
    const bufSize = audioCtx.sampleRate * 0.05;
    const buf = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1) * 0.8;
    const src = audioCtx.createBufferSource();
    src.buffer = buf;
    const filter = audioCtx.createBiquadFilter();
    filter.type = "highpass";
    filter.frequency.value = 3000;
    src.connect(filter);
    filter.connect(gain);
    gain.gain.setValueAtTime(0.6, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
    src.start(now);
  } else {
    const osc = audioCtx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = instrument.freq;
    gain.gain.setValueAtTime(0.7, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
    osc.connect(gain);
    osc.start(now);
    osc.stop(now + 0.4);
  }
}

export default function DrumBuilder({ onGameEnd }) {
  const [grid, setGrid] = useState(() =>
    Object.fromEntries(INSTRUMENTS.map((inst) => [inst.id, Array(STEPS).fill(false)]))
  );
  const [playing, setPlaying] = useState(false);
  const [bpm, setBpm] = useState(100);
  const [currentStep, setCurrentStep] = useState(-1);
  const [saved, setSaved] = useState(false);
  const audioCtxRef = useRef(null);
  const intervalRef = useRef(null);
  const stepRef = useRef(0);

  const toggle = (instId, step) => {
    setGrid((g) => ({ ...g, [instId]: g[instId].map((v, i) => (i === step ? !v : v)) }));
  };

  const startPlay = useCallback(() => {
    if (!audioCtxRef.current) audioCtxRef.current = new AudioContext();
    if (audioCtxRef.current.state === "suspended") audioCtxRef.current.resume();
    stepRef.current = 0;
    const interval = Math.round(60000 / bpm / 2);
    intervalRef.current = setInterval(() => {
      const step = stepRef.current % STEPS;
      setCurrentStep(step);
      INSTRUMENTS.forEach((inst) => {
        if (grid[inst.id][step]) playSound(audioCtxRef.current, inst);
      });
      stepRef.current++;
    }, interval);
    setPlaying(true);
  }, [bpm, grid]);

  const stopPlay = useCallback(() => {
    clearInterval(intervalRef.current);
    setPlaying(false);
    setCurrentStep(-1);
  }, []);

  useEffect(() => {
    if (playing) {
      stopPlay();
      startPlay();
    }
  }, [bpm]); // eslint-disable-line

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const handleSave = () => {
    stopPlay();
    setSaved(true);
    const filledCells = INSTRUMENTS.reduce((sum, inst) => sum + grid[inst.id].filter(Boolean).length, 0);
    const score = filledCells * 10 + bpm;
    onGameEnd({ score });
  };

  const clearGrid = () => {
    stopPlay();
    setGrid(Object.fromEntries(INSTRUMENTS.map((inst) => [inst.id, Array(STEPS).fill(false)])));
  };

  return (
    <div style={{ fontFamily: "monospace", background: "#0a0a0f", border: "2px solid #b8860b", padding: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ color: "#ffd700", fontWeight: 900, fontSize: "1.1rem" }}>🥁 DRUM BUILDER</div>
          <div style={{ color: "rgba(255,255,255,0.4)", fontSize: "0.7rem", marginTop: "0.25rem" }}>West African 8-Step Sequencer</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div>
            <label style={{ color: "#b8860b", fontSize: "0.7rem", display: "block", marginBottom: "0.25rem" }}>BPM: {bpm}</label>
            <input
              type="range"
              min={60}
              max={180}
              value={bpm}
              onChange={(e) => setBpm(Number(e.target.value))}
              style={{ accentColor: "#b8860b", width: "100px" }}
            />
          </div>
        </div>
      </div>

      {/* Step indicators */}
      <div style={{ display: "grid", gridTemplateColumns: `80px repeat(${STEPS}, 1fr)`, gap: "4px", marginBottom: "4px" }}>
        <div />
        {Array.from({ length: STEPS }, (_, i) => (
          <div key={i} style={{
            textAlign: "center",
            fontSize: "0.6rem",
            color: currentStep === i ? "#ffd700" : "rgba(255,255,255,0.2)",
            fontWeight: currentStep === i ? 900 : 400,
            transition: "color 0.05s",
          }}>
            {i + 1}
          </div>
        ))}
      </div>

      {/* Grid */}
      <div className="space-y-2">
        {INSTRUMENTS.map((inst) => (
          <div key={inst.id} style={{ display: "grid", gridTemplateColumns: `80px repeat(${STEPS}, 1fr)`, gap: "4px", alignItems: "center" }}>
            <div style={{ color: inst.color, fontSize: "0.7rem", fontWeight: 700, paddingRight: "0.5rem" }}>{inst.label}</div>
            {Array.from({ length: STEPS }, (_, step) => {
              const active = grid[inst.id][step];
              const isCurrent = currentStep === step;
              return (
                <button
                  key={step}
                  onClick={() => toggle(inst.id, step)}
                  style={{
                    height: "36px",
                    background: active
                      ? isCurrent ? inst.color : `${inst.color}99`
                      : isCurrent ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.05)",
                    border: `1px solid ${active ? inst.color : "rgba(255,255,255,0.1)"}`,
                    cursor: "pointer",
                    transition: "all 0.05s",
                    transform: active && isCurrent ? "scale(1.1)" : "scale(1)",
                  }}
                />
              );
            })}
          </div>
        ))}
      </div>

      {/* Controls */}
      <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        {!playing ? (
          <button
            onClick={startPlay}
            style={{ background: "#22c55e", color: "#0a0a0f", border: "none", padding: "0.6rem 1.5rem", fontFamily: "monospace", fontWeight: 900, fontSize: "0.85rem", cursor: "pointer", letterSpacing: "0.05em", boxShadow: "0 3px 0 #15803d" }}
          >
            ▶ PLAY
          </button>
        ) : (
          <button
            onClick={stopPlay}
            style={{ background: "#ef4444", color: "white", border: "none", padding: "0.6rem 1.5rem", fontFamily: "monospace", fontWeight: 900, fontSize: "0.85rem", cursor: "pointer", letterSpacing: "0.05em", boxShadow: "0 3px 0 #991b1b" }}
          >
            ■ STOP
          </button>
        )}
        <button
          onClick={clearGrid}
          style={{ background: "transparent", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.15)", padding: "0.6rem 1rem", fontFamily: "monospace", fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}
        >
          CLEAR
        </button>
        <button
          onClick={handleSave}
          disabled={saved}
          style={{ background: saved ? "rgba(184,134,11,0.3)" : "#b8860b", color: "#0a0a0f", border: "none", padding: "0.6rem 1.5rem", fontFamily: "monospace", fontWeight: 900, fontSize: "0.85rem", cursor: saved ? "default" : "pointer", letterSpacing: "0.05em", boxShadow: saved ? "none" : "0 3px 0 #7a5c0a" }}
        >
          {saved ? "✓ SAVED" : "SAVE PATTERN"}
        </button>
      </div>

      <p style={{ color: "rgba(255,255,255,0.25)", fontSize: "0.65rem", marginTop: "1rem", lineHeight: 1.6 }}>
        The djembe originated in West Africa. Rhythm is language — these patterns have been passed down for thousands of years.
      </p>
    </div>
  );
}
