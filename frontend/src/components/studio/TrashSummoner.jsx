import { useState, useEffect, useRef } from "react";

const POSITIONS = [
  { top: "15%", left: "5%" },
  { top: "20%", right: "5%" },
  { bottom: "25%", left: "8%" },
  { top: "40%", right: "8%" },
  { top: "30%", left: "30%" },
];

const TRASH_PROMPTS = [
  "Write a poem so bad it makes flowers wilt.",
  "Invent a product no one should ever buy.",
  "Create a melody that sounds like a toaster crying.",
  "Design a logo for a company that should not exist.",
  "Write the worst dating profile bio imaginable.",
  "Pitch a startup idea that would definitely fail.",
  "Describe a painting that should never be painted.",
  "Write instructions for something that cannot be done.",
  "Name a restaurant that no one would ever visit.",
  "Invent a sport that is both dangerous and boring.",
];

const SUMMON_LINES = [
  "YOU. Yes, YOU. The Sanctuary has chosen you… to make GLORIOUS TRASH.",
  "Behold! A new victim— I mean, visionary!",
  "The Pantheon whispers… and they said your name wrong, but close enough.",
  "Drop everything. It's trash time.",
  "You look like someone who could disappoint us beautifully.",
  "The Sanctuary is too clean. Fix that.",
];

const ENCOURAGE_LINES = [
  "Magnificent. Truly awful. The Pantheon is pleased.",
  "Incredible. This is the worst thing we've ever seen. Perfect.",
  "We are moved. Not positively. But moved.",
  "The Pantheon weeps with pride. Mostly weeps.",
];

const REFUSE_STEPS = [
  { text: "You DARE refuse the Pantheon?", icon: "😤" },
  { text: "Cowardice detected. 🦝 Regret is shaking his head.", icon: "🦝" },
  { text: "Fine. If you won't make trash… go BE with the trash.", icon: "🗑️" },
  { text: "The dumpster awaits you, chosen one. →", icon: "☢️" },
];

function injectSummonerStyles() {
  const id = "trash-summoner-styles";
  if (document.getElementById(id)) return;
  const el = document.createElement("style");
  el.id = id;
  el.textContent = `
    @keyframes summonerPop {
      0% { opacity: 0; transform: scale(0.7) translateY(20px); }
      70% { transform: scale(1.05) translateY(-4px); }
      100% { opacity: 1; transform: scale(1) translateY(0); }
    }
    @keyframes orbPulse {
      0%, 100% { box-shadow: 0 0 8px #39ff14, 0 0 16px #39ff14; opacity: 0.8; }
      50% { box-shadow: 0 0 20px #39ff14, 0 0 40px #39ff14; opacity: 1; }
    }
    @keyframes refuseShake {
      0%, 100% { transform: translateX(0); }
      20% { transform: translateX(-8px); }
      40% { transform: translateX(8px); }
      60% { transform: translateX(-5px); }
      80% { transform: translateX(5px); }
    }
    @keyframes bananaSpIn {
      0% { transform: rotate(0deg) scale(1); }
      50% { transform: rotate(180deg) scale(1.3); }
      100% { transform: rotate(360deg) scale(1); }
    }
    @keyframes summonerFadeOut {
      from { opacity: 1; transform: translateY(0); }
      to { opacity: 0; transform: translateY(30px); }
    }
    .summoner-pop { animation: summonerPop 0.4s ease forwards; }
    .summoner-orb { animation: orbPulse 1.5s ease-in-out infinite; }
    .refuse-shake { animation: refuseShake 0.5s ease; }
    .banana-spin { animation: bananaSpIn 1s linear infinite; }
    .summoner-fadeout { animation: summonerFadeOut 0.5s ease forwards; }
  `;
  document.head.appendChild(el);
}

export default function TrashSummoner({ onAccept, onRefuse, onForceTrash, summonerRef }) {
  const [phase, setPhase] = useState("idle"); // idle | summoning | accepted | refused | fadeout
  const [posIdx, setPosIdx] = useState(0);
  const [promptIdx, setPromptIdx] = useState(0);
  const [summonLine, setSummonLine] = useState("");
  const [trashInput, setTrashInput] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [refuseStep, setRefuseStep] = useState(0);
  const [refuseShaking, setRefuseShaking] = useState(false);
  const [cowardText, setCowardText] = useState(false);
  const timersRef = useRef([]);

  useEffect(() => {
    injectSummonerStyles();
  }, []);

  const addTimer = (fn, delay) => {
    const id = setTimeout(fn, delay);
    timersRef.current.push(id);
    return id;
  };

  const trigger = () => {
    const pos = Math.floor(Math.random() * POSITIONS.length);
    const prompt = Math.floor(Math.random() * TRASH_PROMPTS.length);
    const line = SUMMON_LINES[Math.floor(Math.random() * SUMMON_LINES.length)];
    setPosIdx(pos);
    setPromptIdx(prompt);
    setSummonLine(line);
    setPhase("summoning");
    setTrashInput("");
    setSubmitted(false);
    setRefuseStep(0);
    setCowardText(false);
  };

  // Expose trigger
  useEffect(() => {
    if (summonerRef) summonerRef.current = trigger;
  }, [summonerRef]);

  // Auto-trigger every 90-180s
  useEffect(() => {
    const schedule = () => {
      const delay = 90000 + Math.random() * 90000;
      addTimer(() => {
        if (phase === "idle") trigger();
        schedule();
      }, delay);
    };
    schedule();
    return () => timersRef.current.forEach(clearTimeout);
  }, [phase]);

  const handleAccept = () => {
    setPhase("accepted");
    if (onAccept) onAccept(TRASH_PROMPTS[promptIdx]);
  };

  const handleRefuse = () => {
    setPhase("refused");
    if (onRefuse) onRefuse();
    let step = 0;
    const advance = () => {
      step++;
      setRefuseStep(step);
      setRefuseShaking(true);
      addTimer(() => setRefuseShaking(false), 500);
      if (step < REFUSE_STEPS.length - 1) {
        addTimer(advance, 1200);
      } else {
        addTimer(() => {
          if (onForceTrash) onForceTrash();
          setPhase("idle");
        }, 1200);
      }
    };
    addTimer(advance, 1200);
  };

  const handleClose = () => {
    setCowardText(true);
    setPhase("fadeout");
    addTimer(() => setPhase("idle"), 500);
  };

  const handleSubmitTrash = () => {
    setSubmitted(true);
  };

  if (phase === "idle") return null;

  const pos = POSITIONS[posIdx];

  return (
    <div
      style={{
        position: "fixed",
        ...pos,
        zIndex: 500,
        maxWidth: 300,
        background: "rgba(8,5,3,0.97)",
        border: "2px solid #39ff14",
        borderRadius: 10,
        padding: 20,
        fontFamily: "monospace",
        color: "#d4c9b0",
      }}
      className={phase === "fadeout" ? "summoner-fadeout" : "summoner-pop"}
    >
      {/* Pulsing orb */}
      <div
        className="summoner-orb"
        style={{ position: "absolute", top: 12, right: 12, width: 10, height: 10, borderRadius: "50%", background: "#39ff14" }}
      />

      {/* Close */}
      {phase === "summoning" && (
        <button
          onClick={handleClose}
          style={{ position: "absolute", top: 8, left: 10, background: "transparent", border: "none", color: "#6b5e40", cursor: "pointer", fontFamily: "monospace", fontSize: 12 }}
        >
          ✕
        </button>
      )}

      {phase === "summoning" && (
        <>
          <div style={{ marginBottom: 12, fontSize: 11, color: "#39ff14", lineHeight: 1.6, marginTop: 4 }}>{summonLine}</div>
          <div style={{ marginBottom: 16, fontSize: 12, color: "#c8620a", lineHeight: 1.6, fontStyle: "italic" }}>
            "{TRASH_PROMPTS[promptIdx]}"
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleAccept}
              style={{ flex: 1, background: "#39ff14", color: "#0a0805", border: "none", padding: "8px 4px", fontFamily: "monospace", fontWeight: 700, fontSize: 11, cursor: "pointer", borderRadius: 4 }}
            >
              YES, TRASH ME
            </button>
            <button
              onClick={handleRefuse}
              style={{ flex: 1, background: "transparent", border: "1px solid #6b5e40", color: "#6b5e40", padding: "8px 4px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", borderRadius: 4 }}
            >
              I REFUSE
            </button>
          </div>
        </>
      )}

      {phase === "accepted" && (
        <>
          <div style={{ marginBottom: 10, fontSize: 11, color: "#39ff14" }}>The Pantheon commands:</div>
          <div style={{ marginBottom: 12, fontSize: 11, color: "#c8620a", fontStyle: "italic", lineHeight: 1.5 }}>
            "{TRASH_PROMPTS[promptIdx]}"
          </div>
          {!submitted ? (
            <>
              <textarea
                value={trashInput}
                onChange={(e) => setTrashInput(e.target.value)}
                rows={4}
                placeholder="Make it awful…"
                style={{ width: "100%", background: "#080503", border: "1px solid #3a2f1a", color: "#d4c9b0", padding: "8px", fontFamily: "monospace", fontSize: 11, borderRadius: 4, boxSizing: "border-box", resize: "vertical", marginBottom: 10 }}
              />
              <button
                onClick={handleSubmitTrash}
                style={{ width: "100%", background: "#c8620a", color: "#0a0805", border: "none", padding: "8px", fontFamily: "monospace", fontWeight: 700, fontSize: 11, cursor: "pointer", borderRadius: 4 }}
              >
                SUBMIT TO THE PANTHEON
              </button>
            </>
          ) : (
            <div>
              <div style={{ fontSize: 28, marginBottom: 8, textAlign: "center" }} className="banana-spin">🍌</div>
              <div style={{ fontSize: 11, color: "#39ff14", lineHeight: 1.6, marginBottom: 6 }}>
                {ENCOURAGE_LINES[Math.floor(Math.random() * ENCOURAGE_LINES.length)]}
              </div>
              <div style={{ fontSize: 11, color: "#c8620a" }}>+1 Digital Banana Peel</div>
              <button
                onClick={() => setPhase("idle")}
                style={{ marginTop: 12, background: "transparent", border: "1px solid #39ff14", color: "#39ff14", padding: "6px 12px", fontFamily: "monospace", fontSize: 11, cursor: "pointer", borderRadius: 4, width: "100%" }}
              >
                close
              </button>
            </div>
          )}
        </>
      )}

      {phase === "refused" && (
        <div className={refuseShaking ? "refuse-shake" : ""}>
          <div style={{ fontSize: 24, marginBottom: 8, textAlign: "center" }}>{REFUSE_STEPS[Math.min(refuseStep, REFUSE_STEPS.length - 1)].icon}</div>
          <div style={{ fontSize: 12, color: "#c8620a", lineHeight: 1.6, textAlign: "center" }}>
            {REFUSE_STEPS[Math.min(refuseStep, REFUSE_STEPS.length - 1)].text}
          </div>
        </div>
      )}

      {phase === "fadeout" && (
        <div>
          <div style={{ fontSize: 11, color: "#6b5e40", marginBottom: 6 }}>Coward.</div>
          <div style={{ fontSize: 11, color: "#3a2f1a" }}>*disappears into the floor*</div>
        </div>
      )}
    </div>
  );
}
