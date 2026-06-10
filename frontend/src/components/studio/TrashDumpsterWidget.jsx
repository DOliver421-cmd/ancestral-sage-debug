import { useState, useEffect, useRef, useCallback } from "react";

const WHISPERS = [
  "pssst… hey…",
  "you look like Trash material…",
  "the alley awaits…",
  "join us…",
  "your ideas belong here…",
  "greatness is overrated…",
];

function playClank() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(180, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, ctx.currentTime + 0.4);
    gain.gain.setValueAtTime(0.4, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch {}
}

export default function TrashDumpsterWidget({ onEnterTrash }) {
  const [minimized, setMinimized] = useState(false);
  const [shaking, setShaking] = useState(false);
  const [whisperIdx, setWhisperIdx] = useState(null);
  const [showWhisper, setShowWhisper] = useState(false);
  const [smokeItems, setSmokeItems] = useState([]);
  const [bubbleItems, setBubbleItems] = useState([]);
  const [hovered, setHovered] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const whisperTimerRef = useRef(null);
  const shakeTimerRef = useRef(null);
  const smokeTimerRef = useRef(null);
  const bubbleTimerRef = useRef(null);
  const smokeIdRef = useRef(0);
  const bubbleIdRef = useRef(0);

  // Shake every 20–30s
  const scheduleShake = useCallback(() => {
    const delay = 20000 + Math.random() * 10000;
    shakeTimerRef.current = setTimeout(() => {
      setShaking(true);
      playClank();
      setTimeout(() => setShaking(false), 600);
      scheduleShake();
    }, delay);
  }, []);

  // Whisper — show a random whisper, cycle every ~8s
  const scheduleWhisper = useCallback(() => {
    whisperTimerRef.current = setTimeout(() => {
      setWhisperIdx(Math.floor(Math.random() * WHISPERS.length));
      setShowWhisper(true);
      setTimeout(() => setShowWhisper(false), 3500);
      scheduleWhisper();
    }, 6000 + Math.random() * 5000);
  }, []);

  // Smoke 💨 every 15s
  const scheduleSmoke = useCallback(() => {
    smokeTimerRef.current = setTimeout(() => {
      const id = smokeIdRef.current++;
      setSmokeItems(prev => [...prev, { id, left: 30 + Math.random() * 40 }]);
      setTimeout(() => setSmokeItems(prev => prev.filter(s => s.id !== id)), 2000);
      scheduleSmoke();
    }, 15000);
  }, []);

  // Bubble 🫧 every 25–35s
  const scheduleBubble = useCallback(() => {
    bubbleTimerRef.current = setTimeout(() => {
      const id = bubbleIdRef.current++;
      setBubbleItems(prev => [...prev, { id, left: 20 + Math.random() * 60 }]);
      setTimeout(() => setBubbleItems(prev => prev.filter(b => b.id !== id)), 2500);
      scheduleBubble();
    }, 25000 + Math.random() * 10000);
  }, []);

  useEffect(() => {
    scheduleShake();
    scheduleWhisper();
    scheduleSmoke();
    scheduleBubble();
    return () => {
      clearTimeout(shakeTimerRef.current);
      clearTimeout(whisperTimerRef.current);
      clearTimeout(smokeTimerRef.current);
      clearTimeout(bubbleTimerRef.current);
    };
  }, [scheduleShake, scheduleWhisper, scheduleSmoke, scheduleBubble]);

  const handleEnter = () => {
    playClank();
    if (onEnterTrash) onEnterTrash();
  };

  if (minimized) {
    return (
      <>
        <style>{`
          @keyframes tdwBob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
        `}</style>
        <div
          onClick={() => setMinimized(false)}
          title="Trash Pantheon"
          style={{
            position: "fixed", bottom: 20, right: 20, zIndex: 400,
            fontSize: 28, cursor: "pointer",
            animation: "tdwBob 2s ease-in-out infinite",
          }}
        >
          🗑️
        </div>
      </>
    );
  }

  return (
    <>
      <style>{`
        @keyframes tdwShake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-6px)} 40%{transform:translateX(6px)} 60%{transform:translateX(-4px)} 80%{transform:translateX(4px)} }
        @keyframes tdwSmoke { 0%{opacity:0.8;transform:translateY(0) scale(1)} 100%{opacity:0;transform:translateY(-40px) scale(2)} }
        @keyframes tdwBubble { 0%{opacity:0.9;transform:translateY(0) scale(1)} 100%{opacity:0;transform:translateY(-50px) scale(1.5)} }
        @keyframes tdwWhisperIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
        @keyframes tdwModalIn { from{opacity:0;transform:scale(0.85)} to{opacity:1;transform:scale(1)} }
        @keyframes tdwBob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
      `}</style>

      <div style={{
        position: "fixed", bottom: 80, right: 20, zIndex: 400,
        display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6,
        fontFamily: "monospace",
      }}>
        {/* Hover tooltip */}
        {hovered && !confirmOpen && (
          <div style={{
            background: "rgba(8,5,3,0.97)", border: "1px solid rgba(57,255,20,0.25)",
            borderRadius: 8, padding: "8px 12px", fontSize: 11, color: "rgba(255,255,255,0.75)",
            maxWidth: 220, lineHeight: 1.5, textAlign: "right",
          }}>
            Don't go in there… Those people have actual skills. We can save you. Stay Trash.
          </div>
        )}

        {/* Whisper bubble */}
        {showWhisper && whisperIdx !== null && (
          <div style={{
            background: "rgba(8,5,3,0.95)", border: "1px solid rgba(57,255,20,0.3)",
            borderRadius: 8, padding: "6px 10px", fontSize: 11, color: "#39ff14",
            maxWidth: 180, animation: "tdwWhisperIn 0.3s ease-out",
          }}>
            {WHISPERS[whisperIdx]}
          </div>
        )}

        {/* Smoke particles */}
        <div style={{ position: "relative", height: 0 }}>
          {smokeItems.map(s => (
            <div key={s.id} style={{
              position: "absolute", bottom: 0, left: `${s.left}%`,
              fontSize: 16, animation: "tdwSmoke 2s ease-out forwards",
              pointerEvents: "none",
            }}>💨</div>
          ))}
          {bubbleItems.map(b => (
            <div key={b.id} style={{
              position: "absolute", bottom: 0, left: `${b.left}%`,
              fontSize: 14, animation: "tdwBubble 2.5s ease-out forwards",
              pointerEvents: "none",
            }}>🫧</div>
          ))}
        </div>

        {/* Main dumpster widget */}
        <div
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          style={{
            background: "rgba(8,5,3,0.97)", border: "1px solid rgba(57,255,20,0.25)",
            borderRadius: 12, padding: "14px 16px", minWidth: 160, textAlign: "center",
            animation: shaking ? "tdwShake 0.6s ease-in-out" : "tdwBob 3s ease-in-out infinite",
            boxShadow: hovered ? "0 0 20px rgba(57,255,20,0.15)" : "none",
            transition: "box-shadow 0.2s",
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 6 }}>🗑️</div>
          <div style={{ fontSize: 10, color: "#39ff14", letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 8 }}>Trash Pantheon</div>
          <div style={{ display: "flex", gap: 6, justifyContent: "center" }}>
            <button
              onClick={() => { playClank(); setConfirmOpen(true); }}
              style={{
                background: "rgba(57,255,20,0.12)", border: "1px solid rgba(57,255,20,0.3)",
                color: "#39ff14", padding: "5px 10px", fontFamily: "monospace", fontSize: 10,
                cursor: "pointer", borderRadius: 4,
              }}
            >
              Enter
            </button>
            <button
              onClick={() => setMinimized(true)}
              style={{
                background: "transparent", border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.3)", padding: "5px 8px", fontFamily: "monospace",
                fontSize: 10, cursor: "pointer", borderRadius: 4,
              }}
            >
              —
            </button>
          </div>
        </div>
      </div>

      {/* Confirm overlay */}
      {confirmOpen && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)",
          zIndex: 600, display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <div style={{
            background: "#0a0805", border: "2px solid rgba(57,255,20,0.4)",
            borderRadius: 12, padding: "28px 32px", maxWidth: 320, textAlign: "center",
            animation: "tdwModalIn 0.25s ease-out", fontFamily: "monospace",
            boxShadow: "0 0 40px rgba(57,255,20,0.2)",
          }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🗑️</div>
            <div style={{ color: "#39ff14", fontSize: 13, fontWeight: 900, marginBottom: 8 }}>
              Are you sure?
            </div>
            <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 11, lineHeight: 1.6, marginBottom: 20 }}>
              Once you enter the Trash Pantheon, there's no telling what ideas you might have.
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
              <button
                onClick={() => { setConfirmOpen(false); handleEnter(); }}
                style={{
                  background: "#39ff14", color: "#0a0805", border: "none",
                  padding: "9px 16px", fontFamily: "monospace", fontWeight: 900,
                  fontSize: 11, cursor: "pointer", borderRadius: 4,
                }}
              >
                YES, I AM TRASH 🗑️
              </button>
              <button
                onClick={() => setConfirmOpen(false)}
                style={{
                  background: "transparent", color: "rgba(255,255,255,0.5)",
                  border: "1px solid rgba(255,255,255,0.2)", padding: "9px 16px",
                  fontFamily: "monospace", fontSize: 11, cursor: "pointer", borderRadius: 4,
                }}
              >
                No, I have standards
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
