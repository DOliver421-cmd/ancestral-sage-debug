import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";

const TRASH_FEED = [
  { text: "A poem so bad it made a cactus wilt", author: "Anonymous Genius", tag: "Poetry" },
  { text: "Startup idea: Uber for chewing gum", author: "Future Billionaire", tag: "Business" },
  { text: "Logo for a company called 'Meh Inc.'", author: "Design Legend", tag: "Design" },
  { text: "Dating profile that led to 47 blocks", author: "Romantic Soul", tag: "Love" },
  { text: "Song called 'My Feelings Are Valid (feat. nobody)'", author: "Artist", tag: "Music" },
  { text: "A painting of a painting of nothing", author: "Visionary", tag: "Art" },
  { text: "App idea: Spotify but only for one song, forever", author: "Developer", tag: "Tech" },
  { text: "Recipe: cereal with orange juice", author: "Chef", tag: "Food" },
  { text: "A haiku about spreadsheets", author: "Poet", tag: "Poetry" },
  { text: "Business plan written entirely in emojis", author: "Entrepreneur", tag: "Business" },
  { text: "Font choice: Comic Sans for a law firm", author: "Designer", tag: "Design" },
  { text: "Cover letter addressed to 'Whom it May Disgust'", author: "Job Seeker", tag: "Career" },
  { text: "Motivational poster: 'Hang in there. Or don't.'", author: "Life Coach", tag: "Motivation" },
  { text: "Novel: 800 pages, no plot, vibes only", author: "Author", tag: "Literature" },
  { text: "Investment strategy: vibes", author: "Financial Advisor", tag: "Finance" },
  { text: "App for finding your keys by yelling at your phone", author: "Innovator", tag: "Tech" },
  { text: "A three-hour documentary about parking lots", author: "Filmmaker", tag: "Film" },
];

const REGRET_SAYS = [
  "hmph.",
  "*judges silently*",
  "I've seen worse. This is worse.",
  "you call this trash? amateur.",
  "Regret has entered the chat.",
  "...and immediately regretted it.",
];

function playClang() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(150, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(50, ctx.currentTime + 0.5);
    gain.gain.setValueAtTime(0.5, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
    osc.start(); osc.stop(ctx.currentTime + 0.6);
  } catch {}
}

export default function TrashPantheon() {
  const [loadPct, setLoadPct] = useState(0);
  const [regretIdx, setRegretIdx] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [formShake, setFormShake] = useState(false);
  const [exitOpen, setExitOpen] = useState(false);
  const [confetti, setConfetti] = useState([]);
  const feedRef = useRef(null);

  // Falling confetti on mount
  useEffect(() => {
    const items = ["🍌", "📜", "💡", "🗑️", "✏️", "🦝", "📎", "🥄"];
    const els = Array.from({ length: 18 }, (_, i) => ({
      id: i,
      icon: items[i % items.length],
      left: Math.random() * 95,
      delay: Math.random() * 3,
      duration: 3 + Math.random() * 4,
    }));
    setConfetti(els);
  }, []);

  // Fake loading bar crawls to 23%
  useEffect(() => {
    const interval = setInterval(() => {
      setLoadPct(p => {
        if (p >= 23) { clearInterval(interval); return 23; }
        return p + 0.3;
      });
    }, 100);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll feed
  useEffect(() => {
    const el = feedRef.current;
    if (!el) return;
    let frame;
    let pos = 0;
    const scroll = () => {
      pos += 0.5;
      if (pos >= el.scrollHeight / 2) pos = 0;
      el.scrollTop = pos;
      frame = requestAnimationFrame(scroll);
    };
    frame = requestAnimationFrame(scroll);
    return () => cancelAnimationFrame(frame);
  }, []);

  // Regret cycles
  useEffect(() => {
    const t = setInterval(() => setRegretIdx(i => (i + 1) % REGRET_SAYS.length), 4000);
    return () => clearInterval(t);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormShake(true);
    setTimeout(() => setFormShake(false), 600);
    setSubmitted(true);
  };

  const FEED_DOUBLED = [...TRASH_FEED, ...TRASH_FEED];

  return (
    <>
      <style>{`
        @keyframes confettiFall { from { transform: translateY(-60px) rotate(0deg); opacity: 1; } to { transform: translateY(110vh) rotate(720deg); opacity: 0; } }
        @keyframes feedScroll { from { transform: translateY(0); } to { transform: translateY(-50%); } }
        @keyframes flickerGlow { 0%,100% { text-shadow: 0 0 20px #39ff14, 0 0 40px #39ff14; } 50% { text-shadow: 0 0 10px #39ff14; } }
        @keyframes formShake { 0%,100%{transform:translateX(0)}25%{transform:translateX(-8px)}75%{transform:translateX(8px)} }
        @keyframes raccoonBob { 0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)} }
        @keyframes modalIn { from{opacity:0;transform:scale(0.8)} to{opacity:1;transform:scale(1)} }
      `}</style>

      <div style={{ background: "#0a0805", minHeight: "100vh", color: "#e0e0e0", fontFamily: "monospace", position: "relative", overflow: "hidden" }}>

        {/* Confetti */}
        {confetti.map(c => (
          <div key={c.id} style={{ position: "fixed", top: -60, left: `${c.left}%`, fontSize: 20, animation: `confettiFall ${c.duration}s ${c.delay}s linear infinite`, pointerEvents: "none", zIndex: 1 }}>{c.icon}</div>
        ))}

        {/* Fake loading bar */}
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 200 }}>
          <div style={{ height: 3, background: "rgba(57,255,20,0.15)" }}>
            <div style={{ height: "100%", width: `${loadPct}%`, background: "#39ff14", transition: "width 0.1s linear", boxShadow: "0 0 8px #39ff14" }} />
          </div>
          <div style={{ textAlign: "center", fontSize: 9, color: "rgba(57,255,20,0.5)", paddingTop: 3 }}>Processing your mediocrity… {Math.floor(loadPct)}%</div>
        </div>

        {/* Hero */}
        <div style={{ textAlign: "center", padding: "80px 20px 40px", position: "relative", zIndex: 2 }}>
          <div style={{ fontSize: "clamp(2rem,8vw,5rem)", lineHeight: 1 }}>🗑️</div>
          <h1 style={{ fontFamily: "monospace", fontSize: "clamp(1.5rem,5vw,3.5rem)", color: "#39ff14", animation: "flickerGlow 2s ease-in-out infinite", margin: "16px 0 8px", letterSpacing: "0.1em" }}>THE TRASH PANTHEON</h1>
          <p style={{ color: "#c8620a", fontSize: "clamp(0.8rem,2vw,1.1rem)", letterSpacing: "0.2em", textTransform: "uppercase" }}>Where bad ideas come to be celebrated.</p>
          <div style={{ marginTop: 20, display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <span style={{ background: "rgba(57,255,20,0.08)", border: "1px solid rgba(57,255,20,0.2)", padding: "6px 14px", borderRadius: 20, fontSize: 11, color: "#39ff14" }}>Est. in a dumpster, 2024</span>
            <span style={{ background: "rgba(200,98,10,0.08)", border: "1px solid rgba(200,98,10,0.2)", padding: "6px 14px", borderRadius: 20, fontSize: 11, color: "#c8620a" }}>No quality control</span>
          </div>
        </div>

        {/* Main content */}
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 20px 80px", position: "relative", zIndex: 2 }}>

          {/* Trash feed */}
          <div style={{ marginBottom: 40 }}>
            <div style={{ color: "#39ff14", fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 12, borderBottom: "1px solid rgba(57,255,20,0.15)", paddingBottom: 8 }}>📡 Live Trash Feed</div>
            <div ref={feedRef} style={{ height: 280, overflow: "hidden", position: "relative" }}>
              {FEED_DOUBLED.map((item, i) => (
                <div key={i} style={{ background: "rgba(57,255,20,0.04)", border: "1px solid rgba(57,255,20,0.1)", borderRadius: 8, padding: "12px 14px", marginBottom: 8, transform: `rotate(${(i % 3 - 1) * 0.5}deg)` }}>
                  <div style={{ color: "rgba(255,255,255,0.85)", fontSize: 12, marginBottom: 4 }}>"{item.text}"</div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 10, color: "rgba(57,255,20,0.5)" }}>— {item.author}</span>
                    <span style={{ fontSize: 9, color: "#c8620a", background: "rgba(200,98,10,0.1)", padding: "2px 6px", borderRadius: 4 }}>{item.tag}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contact form */}
          <div style={{ marginBottom: 40 }}>
            <div style={{ color: "#39ff14", fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 12, borderBottom: "1px solid rgba(57,255,20,0.15)", paddingBottom: 8 }}>📬 Submit Your Trash</div>
            <form onSubmit={handleSubmit} style={{ animation: formShake ? "formShake 0.6s ease-in-out" : "none" }}>
              <input placeholder="Your name (or alias)" style={{ width: "100%", background: "rgba(57,255,20,0.05)", border: "1px solid rgba(57,255,20,0.2)", color: "#e0e0e0", padding: "10px 12px", fontFamily: "monospace", fontSize: 12, borderRadius: 6, marginBottom: 10, outline: "none", boxSizing: "border-box" }} />
              <textarea placeholder="Your worst idea…" rows={4} style={{ width: "100%", background: "rgba(57,255,20,0.05)", border: "1px solid rgba(57,255,20,0.2)", color: "#e0e0e0", padding: "10px 12px", fontFamily: "monospace", fontSize: 12, borderRadius: 6, resize: "none", outline: "none", boxSizing: "border-box", marginBottom: 10 }} />
              <button type="submit" style={{ background: "#39ff14", color: "#0a0805", border: "none", padding: "10px 24px", fontFamily: "monospace", fontWeight: 900, fontSize: 12, cursor: "pointer", borderRadius: 4, letterSpacing: "0.05em" }}>Submit to the Pantheon 🗑️</button>
              {submitted && <div style={{ marginTop: 10, color: "#c8620a", fontSize: 12 }}>Don't worry. We will find you. Just keep being Trash.</div>}
            </form>
          </div>

          {/* Exit */}
          <div style={{ textAlign: "center" }}>
            <button onClick={() => { playClang(); setExitOpen(true); }} style={{ background: "transparent", border: "1px solid rgba(57,255,20,0.3)", color: "rgba(57,255,20,0.6)", padding: "10px 20px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", borderRadius: 4 }}>
              I'm too talented for this →
            </button>
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", padding: "20px", color: "rgba(57,255,20,0.3)", fontSize: 10, borderTop: "1px solid rgba(57,255,20,0.1)", position: "relative", zIndex: 2 }}>
          Proudly powered by bad decisions. © The Trash Pantheon. All wrongs reserved.
        </div>

        {/* Regret the Raccoon */}
        <div style={{ position: "fixed", bottom: 20, left: 20, zIndex: 300, display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
          <div style={{ background: "rgba(8,5,3,0.95)", border: "1px solid rgba(57,255,20,0.3)", borderRadius: 8, padding: "6px 10px", fontSize: 11, color: "#39ff14", fontFamily: "monospace", maxWidth: 180 }}>
            {REGRET_SAYS[regretIdx]}
          </div>
          <div style={{ fontSize: 28, animation: "raccoonBob 2s ease-in-out infinite" }}>🦝</div>
          <div style={{ fontSize: 9, color: "rgba(57,255,20,0.4)" }}>Regret</div>
        </div>

        {/* Exit modal */}
        {exitOpen && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 500, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ background: "#0a0805", border: "2px solid #39ff14", borderRadius: 12, padding: "32px", maxWidth: 360, textAlign: "center", animation: "modalIn 0.3s ease-out", boxShadow: "0 0 40px rgba(57,255,20,0.3)", fontFamily: "monospace" }}>
              <div style={{ fontSize: 36, marginBottom: 16 }}>😤</div>
              <div style={{ color: "#39ff14", fontSize: 13, lineHeight: 1.7, marginBottom: 8 }}>You weren't trashy enough.</div>
              <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 12, lineHeight: 1.6, marginBottom: 20 }}>We're disappointed. Go on… back to the people with talent.</div>
              <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
                <Link to="/studio" style={{ background: "#39ff14", color: "#0a0805", padding: "9px 18px", fontFamily: "monospace", fontWeight: 900, fontSize: 11, textDecoration: "none", borderRadius: 4 }}>Return to Sanctuary</Link>
                <button onClick={() => setExitOpen(false)} style={{ background: "transparent", color: "rgba(57,255,20,0.5)", border: "1px solid rgba(57,255,20,0.3)", padding: "9px 18px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", borderRadius: 4 }}>Stay Trash</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
