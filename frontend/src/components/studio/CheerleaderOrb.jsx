import { useState, useEffect, useRef } from "react";
import { api } from "../../lib/api";

const HYPE_LINES = [
  "Let's cook today. 🔥",
  "That idea is fire — clarify the hook.",
  "You're on a roll. Keep going.",
  "Pause. Breathe. You're overthinking.",
  "We can do this. Let's build.",
  "This is the one. I feel it.",
  "Stop second-guessing. Hit record.",
  "The beat's already in your head. Write it down.",
  "Consistency beats perfection. Every time.",
  "Nobody else can make what you make.",
  "What if it's actually that simple?",
  "The world needs this. Don't sit on it.",
  "You're closer than you think.",
  "Big energy today. Let's channel it.",
  "I see what you're building. It's real.",
];

export default function CheerleaderOrb({ chamber }) {
  const [message, setMessage] = useState(HYPE_LINES[Math.floor(Math.random() * HYPE_LINES.length)]);
  const [visible, setVisible] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [pulse, setPulse] = useState(false);
  const timeoutRef = useRef(null);

  // Pulse randomly
  useEffect(() => {
    const interval = setInterval(() => {
      setPulse(true);
      setTimeout(() => setPulse(false), 600);
    }, 4000 + Math.random() * 3000);
    return () => clearInterval(interval);
  }, []);

  // Rotate messages on chamber change
  useEffect(() => {
    if (chamber) {
      setThinking(true);
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        const CHAMBER_LINES = {
          lyric: ["Okay, the pen is hot. Let's write.", "Rhymes incoming. Stay loose.", "Your voice is the instrument. Use it."],
          publishing: ["Time to get this out into the world.", "The metadata is the passport. Do it right.", "Distribution is the mission — let's go."],
        };
        const pool = CHAMBER_LINES[chamber] || HYPE_LINES;
        setMessage(pool[Math.floor(Math.random() * pool.length)]);
        setThinking(false);
      }, 800);
    }
    return () => clearTimeout(timeoutRef.current);
  }, [chamber]);

  const askCheerleader = async () => {
    setThinking(true);
    try {
      const r = await api.post("/studio/cheer", { chamber: chamber || "studio" });
      setMessage(r.data.message);
    } catch {
      setMessage(HYPE_LINES[Math.floor(Math.random() * HYPE_LINES.length)]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div style={{ position: "fixed", bottom: 28, right: 28, zIndex: 100, display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 10 }}>
      {/* Speech bubble */}
      {visible && (
        <div
          style={{
            background: "rgba(10,10,20,0.95)",
            border: "1px solid rgba(255,215,0,0.4)",
            borderRadius: 12,
            padding: "10px 14px",
            maxWidth: 220,
            fontSize: 13,
            color: thinking ? "rgba(255,215,0,0.5)" : "#fff",
            lineHeight: 1.5,
            boxShadow: "0 0 20px rgba(255,215,0,0.15)",
            position: "relative",
          }}
          onClick={askCheerleader}
          title="Tap for fresh energy"
          className="cursor-pointer select-none"
        >
          {thinking ? "..." : message}
          <div style={{ position: "absolute", bottom: -8, right: 22, width: 0, height: 0, borderLeft: "8px solid transparent", borderRight: "8px solid transparent", borderTop: "8px solid rgba(255,215,0,0.4)" }} />
        </div>
      )}

      {/* Orb */}
      <button
        onClick={() => setVisible(v => !v)}
        style={{
          width: 52, height: 52,
          borderRadius: "50%",
          border: "none",
          cursor: "pointer",
          background: "radial-gradient(circle at 35% 35%, #ffe066, #f59e0b, #b45309)",
          boxShadow: pulse
            ? "0 0 0 12px rgba(251,191,36,0.12), 0 0 30px rgba(251,191,36,0.6), 0 0 60px rgba(251,191,36,0.3)"
            : "0 0 0 4px rgba(251,191,36,0.15), 0 0 20px rgba(251,191,36,0.4)",
          transition: "box-shadow 0.4s ease",
          transform: pulse ? "scale(1.08)" : "scale(1)",
          fontSize: 22,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}
        title="Your creative spirit guide"
        aria-label="Creative spirit guide"
      >
        ✦
      </button>
    </div>
  );
}
