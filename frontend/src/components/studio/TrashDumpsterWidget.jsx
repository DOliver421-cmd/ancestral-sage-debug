import { useState, useEffect, useRef } from "react";

const WHISPERS = [
  "pssst… hey…",
  "you look like Trash material…",
  "the alley awaits…",
  "join us…",
  "your ideas belong here…",
  "greatness is overrated…",
];

function injectStyles() {
  const id = "trash-dumpster-styles";
  if (document.getElementById(id)) return;
  const el = document.createElement("style");
  el.id = id;
  el.textContent = `
    @keyframes dumpsterShake {
      0%, 100% { transform: translateX(0); }
      15% { transform: translateX(-5px) rotate(-2deg); }
      30% { transform: translateX(5px) rotate(2deg); }
      45% { transform: translateX(-4px) rotate(-1deg); }
      60% { transform: translateX(4px) rotate(1deg); }
      75% { transform: translateX(-2px); }
    }
    @keyframes smokeFloat {
      0% { transform: translateY(0); opacity: 0.7; }
      100% { transform: translateY(-40px); opacity: 0; }
    }
    @keyframes bubbleFloat {
      0% { transform: translateY(0) scale(1); opacity: 0.8; }
      100% { transform: translateY(-30px) scale(1.4); opacity: 0; }
    }
    @keyframes tooltipFlicker {
      0%, 100% { opacity: 1; }
      25% { opacity: 0.4; }
      50% { opacity: 0.9; }
      75% { opacity: 0.3; }
    }
    @keyframes trashFadeIn {
      from { opacity: 0; transform: scale(0.8) translateY(10px); }
      to { opacity: 1; transform: scale(1) translateY(0); }
    }
    .dumpster-shake { animation: dumpsterShake 0.6s ease; }
    .tooltip-flicker { animation: tooltipFlicker 0.5s linear; }
    .trash-widget-fadein { animation: trashFadeIn 0.3s ease; }
  `;
  document.head.appendChild(el);
}

function playClank(light = true) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    if (light) {
      osc.frequency.setValueAtTime(300, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.2);
    } else {
      osc.frequency.setValueAtTime(180, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(60, ctx.currentTime + 0.5);
      gain.gain.setValueAtTime(0.5, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    }
  } catch (_) {}
}

export default function TrashDumpsterWidget({ onEnterTrash }) {
  const [minimized, setMinimized] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [whisper, setWhisper] = useState(null);
  const [smoke, setSmoke] = useState(false);
  const [bubble, setBubble] = useState(false);
  const [shaking, setShaking] = useState(false);
  const timersRef = useRef([]);

  useEffect(() => {
    injectStyles();
  }, []);

  const addTimer = (fn, delay) => {
    const id = setTimeout(fn, delay);
    timersRef.current.push(id);
    return id;
  };

  const addInterval = (fn, delay) => {
    const id = setInterval(fn, delay);
    timersRef.current.push(id);
    return id;
  };

  useEffect(() => {
    // Shake every 20-30s
    const scheduleShake = () => {
      const delay = 20000 + Math.random() * 10000;
      addTimer(() => {
        setShaking(true);
        addTimer(() => setShaking(false), 600);
        scheduleShake();
      }, delay);
    };
    scheduleShake();

    // Smoke puff every 15s
    const smokeId = addInterval(() => {
      setSmoke(true);
      addTimer(() => setSmoke(false), 1200);
    }, 15000);

    // Burp bubble every 25-35s
    const scheduleBubble = () => {
      const delay = 25000 + Math.random() * 10000;
      addTimer(() => {
        setBubble(true);
        addTimer(() => setBubble(false), 1500);
        scheduleBubble();
      }, delay);
    };
    scheduleBubble();

    // Whispers every 40-60s
    const scheduleWhisper = () => {
      const delay = 40000 + Math.random() * 20000;
      addTimer(() => {
        const line = WHISPERS[Math.floor(Math.random() * WHISPERS.length)];
        setWhisper(line);
        addTimer(() => setWhisper(null), 2500);
        scheduleWhisper();
      }, delay);
    };
    scheduleWhisper();

    return () => {
      timersRef.current.forEach(clearTimeout);
      clearInterval(smokeId);
    };
  }, []);

  if (minimized) {
    return (
      <div
        onClick={() => setMinimized(false)}
        style={{ position: "fixed", bottom: 20, right: 20, zIndex: 90, cursor: "pointer", fontSize: 20, opacity: 0.6 }}
        title="Restore Dumpster"
      >
        🗑️
      </div>
    );
  }

  return (
    <div
      style={{ position: "fixed", bottom: 80, right: 20, zIndex: 90, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, userSelect: "none" }}
    >
      {/* Whisper */}
      {whisper && (
        <div className="trash-widget-fadein" style={{ background: "rgba(8,5,3,0.92)", border: "1px solid #39ff14", borderRadius: 6, padding: "6px 10px", fontSize: 11, color: "#39ff14", fontFamily: "monospace", maxWidth: 180, textAlign: "right" }}>
          {whisper}
        </div>
      )}

      {/* Smoke */}
      {smoke && (
        <div style={{ position: "absolute", top: -20, right: 16, animation: "smokeFloat 1.2s ease forwards", pointerEvents: "none", fontSize: 16 }}>
          💨
        </div>
      )}

      {/* Bubble */}
      {bubble && (
        <div style={{ position: "absolute", top: -10, right: 30, animation: "bubbleFloat 1.5s ease forwards", pointerEvents: "none", fontSize: 14 }}>
          🫧
        </div>
      )}

      {/* Banana above */}
      <div style={{ fontSize: 18, textAlign: "right", opacity: 0.8 }}>🍌</div>

      {/* Dumpster button */}
      <div style={{ position: "relative" }}>
        <button
          className={shaking ? "dumpster-shake" : ""}
          onClick={() => setShowConfirm(true)}
          onMouseEnter={(e) => {
            playClank(true);
            setShowTooltip(true);
          }}
          onMouseLeave={() => setShowTooltip(false)}
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 32,
            filter: "drop-shadow(0 0 8px #39ff14)",
            display: "block",
          }}
          title="The Trash Pantheon"
        >
          🗑️
        </button>

        {/* Tooltip */}
        {showTooltip && (
          <div
            className="tooltip-flicker"
            style={{
              position: "absolute",
              right: "calc(100% + 10px)",
              top: "50%",
              transform: "translateY(-50%)",
              background: "rgba(8,5,3,0.95)",
              border: "1px solid #c8620a",
              borderRadius: 8,
              padding: "10px 14px",
              fontSize: 11,
              color: "#d4c9b0",
              fontFamily: "monospace",
              width: 200,
              lineHeight: 1.6,
              whiteSpace: "normal",
            }}
          >
            Don't go in there… Those people have actual skills. We can save you. Stay Trash.
          </div>
        )}
      </div>

      {/* Minimize */}
      <button
        onClick={() => setMinimized(true)}
        style={{ background: "transparent", border: "none", color: "#6b5e40", cursor: "pointer", fontFamily: "monospace", fontSize: 10 }}
      >
        hide
      </button>

      {/* Confirm overlay */}
      {showConfirm && (
        <div
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
        >
          <div className="trash-widget-fadein" style={{ background: "rgba(8,5,3,0.97)", border: "2px solid #39ff14", borderRadius: 12, padding: 32, maxWidth: 360, textAlign: "center", fontFamily: "monospace" }}>
            <div style={{ fontSize: 28, marginBottom: 16 }}>🗑️</div>
            <p style={{ color: "#d4c9b0", fontSize: 14, lineHeight: 1.8, marginBottom: 24 }}>
              Are you sure you want to enter the Trash Pantheon?<br />
              <em style={{ color: "#6b5e40" }}>There is no dignity inside.</em>
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}>
              <button
                onClick={() => {
                  playClank(false);
                  setShowConfirm(false);
                  if (onEnterTrash) onEnterTrash();
                }}
                style={{ background: "#39ff14", color: "#0a0805", border: "none", padding: "10px 20px", fontFamily: "monospace", fontWeight: 700, fontSize: 13, cursor: "pointer", borderRadius: 6, width: "100%" }}
              >
                YES, I AM TRASH 🗑️
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                style={{ background: "transparent", border: "1px solid #6b5e40", color: "#6b5e40", padding: "8px 16px", fontFamily: "monospace", fontSize: 12, cursor: "pointer", borderRadius: 6, width: "100%" }}
              >
                No, I have standards
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
