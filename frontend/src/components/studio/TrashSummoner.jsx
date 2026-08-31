import { useState, useEffect, useRef, useCallback } from "react";

const SUMMONS = [
  { text: "Your genius is wasted on quality. The Trash Pantheon calls.", accept: "Take me there", refuse: "Not today" },
  { text: "We've analyzed your ideas. They belong with us.", accept: "I accept my fate", refuse: "I disagree" },
  { text: "A new artifact of beautiful failure has been added to the Pantheon. You may have inspired it.", accept: "Show me", refuse: "Unlikely" },
  { text: "The raccoon Regret has requested your presence.", accept: "For the raccoon", refuse: "Tell Regret no" },
  { text: "Your last idea was almost trash. Almost. Come perfect the craft.", accept: "Let's go", refuse: "Rude" },
  { text: "The Pantheon is running low on bad business ideas. You seem promising.", accept: "Challenge accepted", refuse: "How dare you" },
];

const FORCE_TRASH_LINES = [
  "Resistance is futile. You are already Trash.",
  "The Pantheon has decided FOR you.",
  "Your standards have been confiscated.",
  "Too late. You've been enrolled.",
];

export default function TrashSummoner({ onAccept, onRefuse, onForceTrash, summonerRef }) {
  const [visible, setVisible] = useState(false);
  const [summon, setSummon] = useState(null);
  const [forceMsg, setForceMsg] = useState(null);
  const [shaking, setShaking] = useState(false);
  const intervalRef = useRef(null);

  const trigger = useCallback(() => {
    if (visible) return;
    const s = SUMMONS[Math.floor(Math.random() * SUMMONS.length)];
    setSummon(s);
    setForceMsg(null);
    setVisible(true);
  }, [visible]);

  // Expose trigger via ref
  useEffect(() => {
    if (summonerRef) summonerRef.current = trigger;
  }, [summonerRef, trigger]);

  // Auto-fire every 90–180s
  useEffect(() => {
    const schedule = () => {
      const delay = 90000 + Math.random() * 90000;
      intervalRef.current = setTimeout(() => {
        trigger();
        schedule();
      }, delay);
    };
    schedule();
    return () => clearTimeout(intervalRef.current);
  }, [trigger]);

  const handleAccept = () => {
    setVisible(false);
    if (onAccept && summon) onAccept(summon.text);
  };

  const handleRefuse = () => {
    // 30% chance of force-trash
    if (Math.random() < 0.3) {
      const msg = FORCE_TRASH_LINES[Math.floor(Math.random() * FORCE_TRASH_LINES.length)];
      setForceMsg(msg);
      setShaking(true);
      setTimeout(() => setShaking(false), 700);
      setTimeout(() => {
        setVisible(false);
        if (onForceTrash) onForceTrash();
      }, 1800);
    } else {
      setVisible(false);
      if (onRefuse) onRefuse();
    }
  };

  if (!visible || !summon) return null;

  return (
    <>
      <style>{`
        @keyframes tsModalIn { from{opacity:0;transform:translateY(20px) scale(0.92)} to{opacity:1;transform:translateY(0) scale(1)} }
        @keyframes tsShake { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-8px)} 40%{transform:translateX(8px)} 60%{transform:translateX(-5px)} 80%{transform:translateX(5px)} }
        @keyframes tsPulse { 0%,100%{box-shadow:0 0 20px rgba(57,255,20,0.2)} 50%{box-shadow:0 0 40px rgba(57,255,20,0.5)} }
      `}</style>

      <div style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
        zIndex: 700, display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "monospace",
      }}>
        <div style={{
          background: "#0a0805", border: "2px solid rgba(57,255,20,0.4)",
          borderRadius: 14, padding: "32px 28px", maxWidth: 360, width: "90%",
          textAlign: "center",
          animation: shaking
            ? "tsShake 0.7s ease-in-out"
            : "tsModalIn 0.35s ease-out, tsPulse 3s ease-in-out infinite",
          boxShadow: "0 0 60px rgba(57,255,20,0.15)",
        }}>
          <div style={{ fontSize: 42, marginBottom: 14 }}>🦝</div>
          <div style={{ fontSize: 10, color: "rgba(57,255,20,0.5)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 10 }}>
            The Trash Pantheon Summons You
          </div>

          {forceMsg ? (
            <div style={{ color: "#39ff14", fontSize: 13, lineHeight: 1.7, fontWeight: 900, marginBottom: 8 }}>
              {forceMsg}
            </div>
          ) : (
            <>
              <div style={{ color: "rgba(255,255,255,0.85)", fontSize: 13, lineHeight: 1.7, marginBottom: 20 }}>
                {summon.text}
              </div>
              <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
                <button
                  onClick={handleAccept}
                  style={{
                    background: "#39ff14", color: "#0a0805", border: "none",
                    padding: "10px 18px", fontFamily: "monospace", fontWeight: 900,
                    fontSize: 12, cursor: "pointer", borderRadius: 5,
                    letterSpacing: "0.04em",
                  }}
                >
                  {summon.accept} 🗑️
                </button>
                <button
                  onClick={handleRefuse}
                  style={{
                    background: "transparent", color: "rgba(255,255,255,0.4)",
                    border: "1px solid rgba(255,255,255,0.15)", padding: "10px 18px",
                    fontFamily: "monospace", fontSize: 12, cursor: "pointer", borderRadius: 5,
                  }}
                >
                  {summon.refuse}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
