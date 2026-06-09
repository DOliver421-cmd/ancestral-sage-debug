import { useState, useEffect, useRef } from "react";

const VERSES = [
  { ref: "Proverbs 22:29", words: ["Do", "you", "see", "someone", "skilled", "in", "their", "work?", "They", "will", "serve", "before", "kings."] },
  { ref: "Philippians 4:13", words: ["I", "can", "do", "all", "this", "through", "him", "who", "gives", "me", "strength."] },
  { ref: "Isaiah 40:31", words: ["Those", "who", "hope", "in", "the", "Lord", "will", "renew", "their", "strength."] },
  { ref: "Colossians 3:23", words: ["Whatever", "you", "do,", "work", "at", "it", "with", "all", "your", "heart."] },
  { ref: "Jeremiah 29:11", words: ["For", "I", "know", "the", "plans", "I", "have", "for", "you,", "declares", "the", "Lord."] },
  { ref: "Romans 8:28", words: ["And", "we", "know", "that", "in", "all", "things", "God", "works", "for", "the", "good."] },
  { ref: "Joshua 1:9", words: ["Be", "strong", "and", "courageous.", "Do", "not", "be", "afraid;", "do", "not", "be", "discouraged."] },
  { ref: "Psalm 23:1", words: ["The", "Lord", "is", "my", "shepherd,", "I", "lack", "nothing."] },
];

function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5); }

export default function ScriptureScramble({ onGameEnd }) {
  const [verseIndex, setVerseIndex] = useState(0);
  const [bank, setBank] = useState(() => shuffle(VERSES[0].words));
  const [tray, setTray] = useState([]);
  const [timeLeft, setTimeLeft] = useState(60);
  const [score, setScore] = useState(0);
  const [correct, setCorrect] = useState(null);
  const [done, setDone] = useState(false);
  const [round, setRound] = useState(1);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current);
          endRound(false, 0);
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [verseIndex]); // eslint-disable-line

  const moveToTray = (word, idx) => {
    setBank((b) => b.filter((_, i) => i !== idx));
    setTray((t) => [...t, word]);
  };

  const moveToBank = (word, idx) => {
    setTray((t) => t.filter((_, i) => i !== idx));
    setBank((b) => [...b, word]);
  };

  const checkAnswer = () => {
    clearInterval(timerRef.current);
    const verse = VERSES[verseIndex];
    const isCorrect = tray.join(" ") === verse.words.join(" ");
    const pts = isCorrect ? 100 + timeLeft : 0;
    setScore((s) => s + pts);
    setCorrect(isCorrect);
    endRound(isCorrect, pts);
  };

  const endRound = (isCorrect, pts) => {
    setCorrect(isCorrect);
    setTimeout(() => {
      const next = verseIndex + 1;
      if (next >= VERSES.length) {
        setDone(true);
        onGameEnd({ score: score + pts });
      } else {
        setVerseIndex(next);
        setBank(shuffle(VERSES[next].words));
        setTray([]);
        setTimeLeft(60);
        setCorrect(null);
        setRound((r) => r + 1);
      }
    }, 2000);
  };

  if (done) {
    return (
      <div style={{ fontFamily: "monospace", background: "#0a0a0f", border: "2px solid #b8860b", padding: "2rem" }}>
        <div style={{ color: "#ffd700", fontSize: "1.3rem", fontWeight: 900, marginBottom: "1rem" }}>
          {score >= 600 ? "📖 THE WORD IS IN YOU" : score >= 300 ? "⚡ GROWING IN THE WORD" : "🙏 KEEP STUDYING"}
        </div>
        <div style={{ color: "white", marginBottom: "0.5rem" }}>Verses completed: <span style={{ color: "#22c55e" }}>{round - 1}/{VERSES.length}</span></div>
        <div style={{ color: "#ffd700", fontSize: "1.8rem", fontWeight: 900, marginTop: "1rem" }}>SCORE: {score.toLocaleString()}</div>
      </div>
    );
  }

  const verse = VERSES[verseIndex];

  return (
    <div style={{ fontFamily: "monospace" }} className="space-y-4">
      {/* HUD */}
      <div style={{ background: "#0a0a0f", border: "1px solid #b8860b", padding: "1rem", display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div><span style={{ color: "#b8860b" }}>ROUND </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{round}/{VERSES.length}</span></div>
        <div><span style={{ color: "#b8860b" }}>TIME </span><span style={{ color: timeLeft <= 10 ? "#ef4444" : "#ffd700", fontWeight: 900 }}>{timeLeft}s</span></div>
        <div><span style={{ color: "#b8860b" }}>SCORE </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{score.toLocaleString()}</span></div>
        <div><span style={{ color: "#b8860b" }}>VERSE </span><span style={{ color: "rgba(255,255,255,0.6)", fontWeight: 700 }}>{verse.ref}</span></div>
      </div>

      {/* Timer bar */}
      <div style={{ background: "rgba(255,255,255,0.08)", height: "6px" }}>
        <div style={{ background: timeLeft <= 10 ? "#ef4444" : "#b8860b", height: "100%", width: `${(timeLeft / 60) * 100}%`, transition: "width 1s linear" }} />
      </div>

      {/* Instruction */}
      <div style={{ color: "rgba(255,255,255,0.5)", fontSize: "0.75rem" }}>
        Build the verse in order — tap words to move them between bank and answer.
      </div>

      {/* Answer tray */}
      <div>
        <div style={{ color: "#b8860b", fontSize: "0.7rem", marginBottom: "0.5rem" }}>YOUR ANSWER:</div>
        <div
          style={{
            minHeight: "60px",
            background: correct === true ? "rgba(34,197,94,0.1)" : correct === false ? "rgba(239,68,68,0.1)" : "rgba(255,255,255,0.02)",
            border: `1px solid ${correct === true ? "#22c55e" : correct === false ? "#ef4444" : "rgba(184,134,11,0.4)"}`,
            padding: "0.75rem",
            display: "flex",
            flexWrap: "wrap",
            gap: "0.4rem",
            alignContent: "flex-start",
          }}
        >
          {tray.map((word, i) => (
            <button
              key={`${word}-${i}`}
              onClick={() => moveToBank(word, i)}
              style={{
                background: "#b8860b",
                color: "#0a0a0f",
                border: "none",
                padding: "0.3rem 0.6rem",
                fontFamily: "monospace",
                fontWeight: 700,
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              {word}
            </button>
          ))}
          {tray.length === 0 && <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "0.75rem" }}>Tap words below to build the verse...</span>}
        </div>
        {correct !== null && (
          <div style={{ color: correct ? "#22c55e" : "#ef4444", fontSize: "0.8rem", marginTop: "0.5rem", fontWeight: 700 }}>
            {correct ? `✓ Correct! +${100 + timeLeft} pts` : `✗ Wrong. The verse: "${verse.words.join(" ")}"`}
          </div>
        )}
      </div>

      {/* Word bank */}
      <div>
        <div style={{ color: "#b8860b", fontSize: "0.7rem", marginBottom: "0.5rem" }}>WORD BANK:</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
          {bank.map((word, i) => (
            <button
              key={`${word}-${i}`}
              onClick={() => moveToTray(word, i)}
              style={{
                background: "rgba(255,255,255,0.07)",
                color: "rgba(255,255,255,0.8)",
                border: "1px solid rgba(255,255,255,0.15)",
                padding: "0.3rem 0.6rem",
                fontFamily: "monospace",
                fontWeight: 600,
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              {word}
            </button>
          ))}
        </div>
      </div>

      {/* Check button */}
      {correct === null && tray.length === verse.words.length && (
        <button
          onClick={checkAnswer}
          style={{
            background: "#b8860b",
            color: "#0a0a0f",
            border: "none",
            padding: "0.75rem 2rem",
            fontFamily: "monospace",
            fontWeight: 900,
            fontSize: "0.85rem",
            cursor: "pointer",
            letterSpacing: "0.1em",
            boxShadow: "0 4px 0 #7a5c0a",
          }}
        >
          CHECK ANSWER ▶
        </button>
      )}
    </div>
  );
}
