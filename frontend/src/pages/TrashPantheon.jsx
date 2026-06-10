import { useState, useEffect, useRef } from "react";

const TRASH_EMOJIS = ["🍌", "📜", "💡", "🗑️", "✏️"];

const TRASH_FEED_BASE = [
  { id: 1, text: "A poem so bad it made a cactus wilt" },
  { id: 2, text: "Startup idea: Uber for chewing gum" },
  { id: 3, text: "Logo for a company called 'Meh Inc.'" },
  { id: 4, text: "Dating profile that led to 47 blocks" },
  { id: 5, text: "Song called 'My Feelings Are Valid (feat. nobody)'" },
  { id: 6, text: "Business plan: rent air to people who already have it" },
  { id: 7, text: "A haiku about spreadsheets. Three times." },
  { id: 8, text: "Prototype app: Tinder but for socks" },
  { id: 9, text: "Poem that rhymes 'orange' with 'orange'" },
  { id: 10, text: "Pitch deck for a subscription box of dirt" },
  { id: 11, text: "Novel: 400 pages, no plot, 3 fonts" },
  { id: 12, text: "Resume listing 'professional napper' as skill #1" },
  { id: 13, text: "Jingle for a brand called 'Adequate Solutions LLC'" },
  { id: 14, text: "App to remind you to drink water. It crashes." },
  { id: 15, text: "Portrait painted entirely in condiments" },
  { id: 16, text: "Product name: 'The Unnecessarily Premium Spoon'" },
  { id: 17, text: "A motivational quote that just says 'fine.'" },
];

const RACCOON_LINES = [
  "hmph.",
  "*judges silently*",
  "I've seen worse. This is worse.",
  "you call this trash? amateur.",
  "Regret has entered the chat.",
  "...and immediately regretted it.",
];

const TRASH_FEED = [...TRASH_FEED_BASE, ...TRASH_FEED_BASE.map((i) => ({ ...i, id: i.id + 100 }))];

function playClang() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(150, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(50, ctx.currentTime + 0.5);
    gain.gain.setValueAtTime(0.4, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.5);
  } catch (_) {}
}

export default function TrashPantheon() {
  const [loadPct, setLoadPct] = useState(0);
  const [raccoonIdx, setRaccoonIdx] = useState(0);
  const [formName, setFormName] = useState("");
  const [formIdea, setFormIdea] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [shaking, setShaking] = useState(false);
  const [exitModal, setExitModal] = useState(false);
  const [confetti, setConfetti] = useState([]);
  const feedRef = useRef(null);

  // Generate confetti on mount
  useEffect(() => {
    const items = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      emoji: TRASH_EMOJIS[Math.floor(Math.random() * TRASH_EMOJIS.length)],
      left: Math.random() * 100,
      delay: Math.random() * 5,
      duration: 4 + Math.random() * 4,
      size: 14 + Math.random() * 18,
    }));
    setConfetti(items);
  }, []);

  // Fake loading bar
  useEffect(() => {
    let pct = 0;
    const interval = setInterval(() => {
      pct += Math.random() * 1.5;
      if (pct >= 23) {
        pct = 23;
        clearInterval(interval);
      }
      setLoadPct(pct);
    }, 400);
    return () => clearInterval(interval);
  }, []);

  // Raccoon line cycling
  useEffect(() => {
    const interval = setInterval(() => {
      setRaccoonIdx((i) => (i + 1) % RACCOON_LINES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll feed
  useEffect(() => {
    const el = feedRef.current;
    if (!el) return;
    let pos = 0;
    const step = () => {
      pos += 0.5;
      if (pos >= el.scrollHeight / 2) pos = 0;
      el.scrollTop = pos;
    };
    const id = setInterval(step, 30);
    return () => clearInterval(id);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setShaking(true);
    setTimeout(() => setShaking(false), 600);
    setSubmitted(true);
  };

  const handleExit = () => {
    playClang();
    setExitModal(true);
  };

  const T = {
    bg: "#0a0805",
    green: "#39ff14",
    orange: "#c8620a",
    card: "#111008",
    text: "#d4c9b0",
    muted: "#6b5e40",
  };

  return (
    <>
      <style>{`
        @keyframes trashFall {
          0% { transform: translateY(-60px) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(360deg); opacity: 0.3; }
        }
        @keyframes glowPulse {
          0%, 100% { text-shadow: 0 0 20px #39ff14, 0 0 40px #39ff14; }
          50% { text-shadow: 0 0 40px #39ff14, 0 0 80px #39ff14, 0 0 120px #39ff14; }
        }
        @keyframes formShake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-8px); }
          40% { transform: translateX(8px); }
          60% { transform: translateX(-5px); }
          80% { transform: translateX(5px); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .trash-confetti { position: fixed; pointer-events: none; animation: trashFall linear infinite; }
        .glow-title { animation: glowPulse 2s ease-in-out infinite; }
        .form-shake { animation: formShake 0.6s ease; }
        .fade-in { animation: fadeIn 0.4s ease; }
      `}</style>

      <div style={{ minHeight: "100vh", background: T.bg, color: T.text, fontFamily: "monospace", position: "relative", overflow: "hidden" }}>

        {/* Confetti */}
        {confetti.map((c) => (
          <span
            key={c.id}
            className="trash-confetti"
            style={{
              left: `${c.left}%`,
              top: "-60px",
              fontSize: c.size,
              animationDelay: `${c.delay}s`,
              animationDuration: `${c.duration}s`,
              zIndex: 0,
            }}
          >
            {c.emoji}
          </span>
        ))}

        {/* Loading bar */}
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, background: "#080503", borderBottom: `1px solid ${T.muted}`, padding: "6px 16px" }}>
          <div style={{ fontSize: 10, color: T.muted, marginBottom: 4 }}>Processing your mediocrity…</div>
          <div style={{ height: 4, background: "#1a1208", borderRadius: 2, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${loadPct}%`, background: T.orange, transition: "width 0.4s linear", borderRadius: 2 }} />
          </div>
          <div style={{ fontSize: 10, color: T.muted, marginTop: 2 }}>{loadPct.toFixed(1)}%</div>
        </div>

        {/* Exit button */}
        <div style={{ position: "fixed", top: 56, right: 16, zIndex: 100 }}>
          <button
            onClick={handleExit}
            style={{ background: "transparent", border: `1px solid ${T.muted}`, color: T.muted, padding: "6px 12px", cursor: "pointer", fontFamily: "monospace", fontSize: 12 }}
          >
            I'm too talented for this →
          </button>
        </div>

        {/* Main content */}
        <div style={{ maxWidth: 800, margin: "0 auto", padding: "100px 24px 120px", position: "relative", zIndex: 1 }}>

          {/* Hero */}
          <div style={{ textAlign: "center", marginBottom: 60 }}>
            <h1
              className="glow-title"
              style={{ fontSize: "clamp(32px, 8vw, 72px)", fontWeight: 900, color: T.green, letterSpacing: "0.05em", marginBottom: 16, lineHeight: 1.1 }}
            >
              🗑️ THE TRASH PANTHEON
            </h1>
            <p style={{ fontSize: 18, color: T.orange, letterSpacing: "0.1em" }}>
              Where bad ideas come to be celebrated.
            </p>
          </div>

          {/* Trash Feed */}
          <div style={{ marginBottom: 60 }}>
            <h2 style={{ color: T.orange, fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 16 }}>— LIVE TRASH FEED —</h2>
            <div
              ref={feedRef}
              style={{ height: 320, overflow: "hidden", position: "relative" }}
            >
              {TRASH_FEED.map((item, idx) => (
                <div
                  key={`${item.id}-${idx}`}
                  style={{
                    background: T.card,
                    border: `1px solid #2a1f0a`,
                    borderRadius: 6,
                    padding: "12px 16px",
                    marginBottom: 10,
                    transform: `rotate(${(idx % 3 - 1) * 0.8}deg)`,
                    fontFamily: "monospace",
                    fontSize: 13,
                    color: T.text,
                    lineHeight: 1.4,
                  }}
                >
                  <span style={{ color: T.orange, marginRight: 8 }}>#{item.id.toString().padStart(3, "0")}</span>
                  {item.text}
                </div>
              ))}
            </div>
          </div>

          {/* Broken Contact Form */}
          <div style={{ marginBottom: 60, background: T.card, border: `1px solid #2a1f0a`, borderRadius: 10, padding: 28 }}>
            <h2 style={{ color: T.green, fontSize: 16, marginBottom: 20, letterSpacing: "0.1em" }}>SUBMIT YOUR TRASH</h2>
            {submitted ? (
              <div className="fade-in" style={{ color: T.orange, lineHeight: 1.8, fontSize: 14 }}>
                Don't worry. We will find you. Just keep being Trash.
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: 16 }}>
                  <label style={{ display: "block", fontSize: 11, color: T.muted, marginBottom: 6, letterSpacing: "0.1em" }}>YOUR NAME (if you dare)</label>
                  <input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    style={{ width: "100%", background: "#080503", border: `1px solid ${T.muted}`, color: T.text, padding: "8px 12px", fontFamily: "monospace", fontSize: 13, borderRadius: 4, boxSizing: "border-box" }}
                    placeholder="Anonymous Trash Creator"
                  />
                </div>
                <div style={{ marginBottom: 20 }}>
                  <label style={{ display: "block", fontSize: 11, color: T.muted, marginBottom: 6, letterSpacing: "0.1em" }}>YOUR WORST IDEA</label>
                  <textarea
                    value={formIdea}
                    onChange={(e) => setFormIdea(e.target.value)}
                    rows={4}
                    style={{ width: "100%", background: "#080503", border: `1px solid ${T.muted}`, color: T.text, padding: "8px 12px", fontFamily: "monospace", fontSize: 13, borderRadius: 4, boxSizing: "border-box", resize: "vertical" }}
                    placeholder="Describe your magnificent disaster…"
                  />
                </div>
                <button
                  type="submit"
                  className={shaking ? "form-shake" : ""}
                  style={{ background: T.orange, color: "#0a0805", border: "none", padding: "10px 24px", fontFamily: "monospace", fontWeight: 700, fontSize: 14, cursor: "pointer", borderRadius: 4, letterSpacing: "0.05em" }}
                >
                  SUBMIT TO THE PANTHEON
                </button>
              </form>
            )}
          </div>

          {/* Footer */}
          <div style={{ textAlign: "center", color: T.muted, fontSize: 11, letterSpacing: "0.1em", borderTop: `1px solid #1a1208`, paddingTop: 24 }}>
            Proudly powered by bad decisions. © The Trash Pantheon. All wrongs reserved.
          </div>
        </div>

        {/* Regret the Raccoon */}
        <div style={{ position: "fixed", bottom: 24, left: 20, zIndex: 200, display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
          <div
            className="fade-in"
            key={raccoonIdx}
            style={{ background: "#080503", border: `1px solid ${T.orange}`, borderRadius: 8, padding: "8px 12px", fontSize: 12, color: T.text, maxWidth: 200, lineHeight: 1.5 }}
          >
            {RACCOON_LINES[raccoonIdx]}
          </div>
          <div style={{ fontSize: 28 }}>🦝</div>
          <div style={{ fontSize: 10, color: T.muted }}>Regret</div>
        </div>

        {/* Exit Modal */}
        {exitModal && (
          <div
            style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 300, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
          >
            <div style={{ background: T.card, border: `2px solid ${T.orange}`, borderRadius: 12, padding: 36, maxWidth: 420, textAlign: "center" }}>
              <div style={{ fontSize: 32, marginBottom: 16 }}>🎩</div>
              <p style={{ color: T.text, fontSize: 15, lineHeight: 1.8, marginBottom: 24 }}>
                You weren't trashy enough. We're disappointed. Go on… back to the people with talent.
              </p>
              <a
                href="/studio"
                style={{ display: "inline-block", color: T.green, border: `1px solid ${T.green}`, padding: "10px 20px", textDecoration: "none", fontFamily: "monospace", fontSize: 13, borderRadius: 4 }}
              >
                Return to Sanctuary →
              </a>
              <div style={{ marginTop: 16 }}>
                <button
                  onClick={() => setExitModal(false)}
                  style={{ background: "transparent", border: "none", color: T.muted, cursor: "pointer", fontFamily: "monospace", fontSize: 12 }}
                >
                  actually I'm staying
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
