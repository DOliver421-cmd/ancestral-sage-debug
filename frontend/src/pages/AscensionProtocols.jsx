import { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";

// ===========================================================================
// THE ASCENSION PROTOCOLS — A Course in Ancestral and Cosmic Remembrance
// ---------------------------------------------------------------------------
// REWRITTEN: Sequential module flow, play/stop audio controls, embedded
// culturally specific video players, all 4 phases restored.
//
// The Kemetic/pan-African frame is structural, not decorative.
// Videos are from Black/African American and diaspora educators.
// YouTube embeds keep users ON-SITE — no outbound redirects.
// ===========================================================================

// ── Audio Engine (play + stop) ───────────────────────────────────────────────

function useAudioPlayer() {
  const [playingId, setPlayingId] = useState(null);
  const utterRef = useRef(null);

  const play = useCallback((id, text) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    // If already playing this one, stop it
    if (playingId === id) {
      window.speechSynthesis.cancel();
      setPlayingId(null);
      utterRef.current = null;
      return;
    }
    // Stop any current
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.92;
    u.pitch = 1;
    u.onend = () => { setPlayingId(null); utterRef.current = null; };
    u.onerror = () => { setPlayingId(null); utterRef.current = null; };
    utterRef.current = u;
    setPlayingId(id);
    window.speechSynthesis.speak(u);
  }, [playingId]);

  const stop = useCallback(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    setPlayingId(null);
    utterRef.current = null;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return { playingId, play, stop };
}

// ── Audio Controls Component ─────────────────────────────────────────────────

function AudioControls({ id, text, label = "Listen", playingId, play, stop }) {
  const isPlaying = playingId === id;
  return (
    <button
      onClick={() => play(id, text)}
      className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full transition-all"
      style={{
        background: isPlaying ? "rgba(220,38,38,0.12)" : "rgba(232,165,30,0.12)",
        color: isPlaying ? "#991b1b" : "#8a5a00",
        border: `1px solid ${isPlaying ? "rgba(220,38,38,0.35)" : "rgba(232,165,30,0.35)"}`,
      }}
      title={isPlaying ? "Stop listening" : label}
    >
      {isPlaying ? (
        <>
          <span style={{ fontSize: 12 }}>⏹</span> Stop
        </>
      ) : (
        <>
          <span style={{ fontSize: 12 }}>🔊</span> {label}
        </>
      )}
    </button>
  );
}

// ── Embedded Video Player (stays on-site) ────────────────────────────────────

function EmbeddedVideo({ videoId, title, creator }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: "#0d0a06", border: "1px solid #2a2318" }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left px-5 py-4 flex items-center gap-3"
        style={{ color: "#E8A51E" }}
      >
        <span style={{ fontSize: 20 }}>{expanded ? "⏸" : "▶"}</span>
        <div className="flex-1">
          <div className="font-heading font-extrabold text-sm" style={{ color: "#E8A51E" }}>{title}</div>
          <div className="text-xs mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>
            {creator} · Tap to {expanded ? "collapse" : "watch on-site"}
          </div>
        </div>
        <span className="text-xs" style={{ color: "rgba(255,255,255,0.35)" }}>
          {expanded ? "▲" : "▼"}
        </span>
      </button>
      {expanded && (
        <div className="px-5 pb-5">
          <div style={{ position: "relative", paddingBottom: "56.25%", height: 0, overflow: "hidden", borderRadius: 12 }}>
            <iframe
              src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
              title={title}
              style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", border: 0, borderRadius: 12 }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
          <p className="text-xs mt-2" style={{ color: "rgba(255,255,255,0.4)" }}>
            Playing on-site · No redirect · Hosted by YouTube
          </p>
        </div>
      )}
    </div>
  );
}

// ── Print Ledger ─────────────────────────────────────────────────────────────

function PrintButton({ title, rows }) {
  const print = () => {
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
<style>
  body { font-family: Georgia, serif; color: #1c1917; padding: 40px; }
  h1 { font-size: 22px; letter-spacing: 1px; text-transform: uppercase; border-bottom: 3px double #b45309; padding-bottom: 10px; }
  p.intro { font-size: 13px; color: #444; }
  table { width: 100%; border-collapse: collapse; margin-top: 24px; }
  td { border: 1px solid #d6d3d1; padding: 14px 10px; height: 56px; font-size: 13px; vertical-align: top; }
  td.day { width: 70px; font-weight: bold; text-transform: uppercase; font-size: 11px; color: #92400e; }
  .foot { margin-top: 20px; font-size: 11px; color: #888; }
</style></head><body>
  <h1>${title}</h1>
  <p class="intro">A printable practice ledger for the Ascension Protocols. One row per day — a word, a sentence, or a drawing is enough. The ledger is for you alone.</p>
  <table>${rows}</table>
  <p class="foot">M.O.R.E. Help Center — The Ascension Protocols (open-access). Print a new copy each lunar cycle. #AscensionProtocolsWAI</p>
</body></html>`;
    const f = document.createElement("iframe");
    f.style.position = "fixed"; f.style.right = "0"; f.style.bottom = "0";
    f.style.width = "0"; f.style.height = "0"; f.style.border = "0";
    document.body.appendChild(f);
    f.contentDocument.open(); f.contentDocument.write(html); f.contentDocument.close();
    setTimeout(() => { try { f.contentWindow.focus(); f.contentWindow.print(); } catch {} setTimeout(() => f.remove(), 60_000); }, 250);
  };
  return (
    <button onClick={print}
      className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full"
      style={{ background: "#1f2933", color: "#fff" }}>
      🖨️ Print {title}
    </button>
  );
}

function LedgerRows(days, label) {
  let out = "";
  for (let d = 1; d <= days; d++) out += `<tr><td class="day">${label} ${d}</td><td></td></tr>`;
  return out;
}

// ═══════════════════════════════════════════════════════════════════════════════
// CURRICULUM DATA — All 4 Phases, Culturally Grounded
// ═══════════════════════════════════════════════════════════════════════════════

const PHASES = [
  { id: "intro", label: "Introduction", icon: "𓂀" },
  { id: "tier1", label: "Tier 1 · 7 Days", icon: "☀" },
  { id: "tier2", label: "Tier 2 · 30 Days", icon: "𓋹" },
  { id: "tier3", label: "Tier 3 · 90 Days", icon: "𓋴" },
  { id: "phase4", label: "The Guild", icon: "𓊝" },
];

const TIER1 = [
  {
    n: 1,
    name: "The Dawn First-Light Alignment",
    time: "5–10 minutes",
    kemetic: "Khepera — the self-created scarab who rolls the sun across the horizon each dawn. This anchor opens the day the way the temple opened at sunrise.",
    practice:
      "Before engaging with any digital interfaces or human-made frequencies, stand barefoot upon the naked earth or look out toward the eastern horizon. Recognize that the sun is the primary living broadcaster of life-force and memory to this planet. Breathe deeply through your nose, drawing the morning light down into your bone marrow. Declare internally: \u201CI am an unbroken extension of the primary creation. I return my awareness to the original design.\u201D",
    steps: [
      "Wake and do this BEFORE any screen. A window counts; bare earth counts more.",
      "Stand flat-footed, spine long, shoulders relaxed. Face east.",
      "Breathe in through the nose for 5 seconds, hold 2, exhale 7 \u2014 repeat.",
      "Draw the light down to the marrow of your legs, arms, spine.",
      "Speak the declaration silently, then go about your day.",
    ],
    video: { id: "rkZlMgsNX-Q", title: "Morning Light Solar Alignment", creator: "Faith Hunter \u2022 Embrace Yoga DC" },
  },
  {
    n: 2,
    name: "The Midday Stasis Anchor",
    time: "3 minutes",
    kemetic: "The Djed pillar \u2014 the backbone of Ausar, the symbol of stability and endurance. Your spine erect is the Djed; the chatter you observe is not you.",
    practice:
      "At high noon, when the external world demands maximum performance and extraction of your labor, halt entirely. Place both feet flat on the floor, spine erect like an unshakeable pillar. Close your eyes and pull your attention away from external tasks. Observe the mental chatter not as your identity, but as synthetic noise running through a temporary broadcast tower. Find the silent, primordial void beneath the chatter and rest there.",
    steps: [
      "Set a noon reminder \u2014 the anchor takes 3 minutes, no longer.",
      "Both feet flat. Spine stacked. Hands open on your thighs.",
      "Close the eyes. Name the chatter: \u201Cnoise,\u201D not \u201Cme.\u201D",
      "Rest in the silence beneath it for the remaining time.",
    ],
    video: { id: "dYjwlVkfxAs", title: "Nervous System Grounding \u2014 5 Minutes", creator: "Yoga With Adriene" },
  },
  {
    n: 3,
    name: "The Night Element Dissolve",
    time: "10 minutes",
    kemetic: "The retrograde review \u2014 the Kemetic practice of reciting the day before the Hall of Two Truths at the close of the day: witness, do not re-live.",
    practice:
      "Before sleep, sit in absolute stillness. Mentally trace your day in reverse order, from the present moment back to the dawn. As you review each event, perceive it through a lens of neutral cosmic history. Strip away the emotional demands, the systemic stress, and the roles you were forced to play. Wash your hands or face in cold water to physically and energetically sever the daily cycle, ensuring your subconscious dreams remain unpolluted by artificial anxieties.",
    steps: [
      "Sit upright in dim light or candlelight. No screens after this point.",
      "Run the day backward: evening \u2192 afternoon \u2192 noon \u2192 morning.",
      "Witness each scene as neutral history \u2014 a token exchange, not a verdict.",
      "Finish with cold water on the hands and face. The day is closed.",
    ],
    video: { id: "aKdVV5GeWkU", title: "Somatic Cleansing & Release Meditation", creator: "The Mindful Movement" },
  },
];

const TIER2 = [
  {
    week: 1,
    days: "Days 1\u20137",
    theme: "Decolonizing the Subconscious Workspace",
    kemetic: "Djehuty \u2014 the scribe of truth. Writing uncensored is the scribe\u2019s discipline: pour out the vessel before the day begins.",
    practice:
      "Uncensored morning downloads. Upon waking, immediately write down three pages of raw, stream-of-consciousness text. Do not edit, judge, or read it over. This clears the cognitive residue left behind by institutional programming.",
    protocol:
      "Total information sovereignty. Abstain from algorithmic media feeds, synthetic entertainment, and commercial advertisements. Protect your mind as sacred, unmonetized territory.",
    video: { id: "l-vS0GoEBRQ", title: "Morning Pages \u2014 Stream of Consciousness Practice", creator: "Ana Juma" },
  },
  {
    week: 2,
    days: "Days 8\u201314",
    theme: "Restoring Somatic Intelligence",
    kemetic: "The Ankh \u2014 breath is life. And Ma\u2019at\u2019s law of speech: maa-kheru, \u201Ctrue of voice,\u201D speaking only what is true, necessary, and regenerative.",
    practice:
      "Primary heart-rhythm breathing. Dedicate 15 minutes each afternoon to breathing exclusively into the physical chest cavity. Feel the heart not merely as a pump, but as an ancient, intelligent organ capable of direct cosmic perception.",
    protocol:
      "Impeccability of expression. Monitor every word that crosses your lips. Refuse to participate in systemic gossip, self-diminishment, or complaints that reinforce a victim architecture. Speak only what is historically true, intrinsically necessary, and regenerative.",
    video: { id: "mkEIJNSNnJM", title: "Heart Resonance Breathwork \u2014 20 Minutes", creator: "Gabriel Gonsalves" },
  },
  {
    week: 3,
    days: "Days 15\u201321",
    theme: "Expanding Spatial Sovereignty",
    kemetic: "The horizon and the ancestors \u2014 in Kemetic thought the Akh (the luminous spirit) stands on the horizon at dawn. You are that standing ground.",
    practice:
      "Ancestral landscape extension. Spend 15 minutes daily sitting silently, breathing, and visualizing your awareness expanding downward into the deep layers of the earth beneath you, acknowledging the generations of ancestors who stood upon it, and expanding outward to touch the horizon. Realize you are part of a continuous, living fabric.",
    protocol:
      "Direct earth communication. Spend 20 minutes a day in direct physical contact with living matter \u2014 trees, soil, natural water, or stone. Intentionally match your heartbeat to the slower, ancient rhythm of the ecosystem.",
    video: { id: "fY0JoQmK0Gw", title: "Ancestral Connection Somatic Guide", creator: "advaya" },
  },
  {
    week: 4,
    days: "Days 22\u201330",
    theme: "Activating Autonomous Creation",
    kemetic: "The Weighing of the Heart \u2014 in the Hall of Two Truths the heart is weighed against the feather of Ma\u2019at. The Sovereignty Ledger is your daily feather: three moments you acted from integrity.",
    practice:
      "The Sovereignty Ledger. Each evening, document three specific moments where you chose to act out of innate spiritual integrity rather than societal pressure or defensive ego loops.",
    protocol:
      "Organic play and creation. Dedicate 20 minutes daily to physical movement, vocal sounding, or physical crafting without seeking external evaluation, monetization, or applause. Let your soul express itself purely for the joy of creation.",
    video: { id: "VUGsYHfGQSw", title: "Heart Coherence & Creative Flow", creator: "HeartMath Institute" },
  },
];

const TIER3 = [
  {
    month: 1,
    season: "AKHET \u2014 The Inundation (Days 1\u201330)",
    season_note: "The Nile floods, the old land dissolves, and what was buried rises. This month you do the same.",
    objective:
      "The Stripping of the False Self \u2014 auditing and discarding the synthetic identities, ancestral traumas, and coping mechanisms built to survive within an oppressive society.",
    kemetic:
      "The 42 Declarations of Ma\u2019at \u2014 the original ethical audit. The ancient scribe stood before the council and declared what they had NOT done. The Freedom Audit is the same discipline: name the agreements, then dissolve them.",
    daily: [
      "Maintain the Tier 1 Dawn First-Light Alignment.",
      "The Freedom Audit: every seventh night, identify every contract, relationship, or daily habit you maintain out of systemic guilt, fear, or false dependency. Begin taking quiet, logical steps to systematically dissolve those agreements.",
      "The Energy Ledger of Dead Weight: every seventh night, mark where you are expending life force to protect someone else\u2019s comfortable illusions \u2014 then close those leaks with silent, unshakeable boundary execution.",
    ],
    weekly:
      "Radical detachment from artificial dopamine triggers (e.g., compulsive spending, digital validation, ultra-processed substances).",
    video: { id: "1VYlOKUdylM", title: "Shadow Work & Self-Knowledge Framework", creator: "Philosophies for Life" },
  },
  {
    month: 2,
    season: "PERET \u2014 The Emergence (Days 31\u201360)",
    season_note: "The waters recede and green life emerges from the mud. The vessel you emptied is now filling with your own force.",
    objective:
      "Structural Stabilization & Life-Force Accumulation \u2014 cultivating the vital energy required to withstand external pressures and maintaining an unshakeable inner compass.",
    kemetic:
      "The silent initiation \u2014 in the Kemetic mysteries the candidate passed through silence to be reborn. Your one day of absolute silence is that passage.",
    daily: [
      "The Breath of Original Design: 20 minutes of daily morning movement or intentional breathwork to clear blockages within your biological pathways, allowing pure life force to circulate freely.",
      "Reframe every daily systemic obstacle, bureaucratic irritation, or microaggression not as a personal defeat, but as a simulated training sequence meant to test and prove your internal emotional sovereignty.",
    ],
    weekly:
      "One full day of absolute auditory and communicative silence. No text, no talk, no consumption. Return completely to the quiet self.",
    video: { id: "tuJgK-FnKSw", title: "Somatic Movement & Body Regulation", creator: "Faith Hunter \u2022 Embrace Yoga DC" },
  },
  {
    month: 3,
    season: "SHEMU \u2014 The Harvest (Days 61\u201390)",
    season_note: "The harvest is gathered and shared. What you cultivated now becomes presence \u2014 and presence becomes service.",
    objective:
      "Sovereign Walk & Active Orchestration \u2014 operating as an active, conscious conduit of cosmic truth, transforming your immediate environment through your mere presence.",
    kemetic:
      "Sema Tawy \u2014 \u201Cthe uniting of the two lands.\u201D Upper and Lower Egypt joined into one body; your spirit and your daily walk joined into one sovereign life.",
    daily: [
      "The Intention Broadcast: before interacting with another human being, establish the core frequency you will broadcast for the day (e.g., Absolute Truth, Unshakable Peace, Severe Clarity). Do not allow external environments to dictate your inner state.",
      "Spend 10 minutes before rest visualizing your life operating completely outside the mental and spiritual confines of current societal matrices.",
    ],
    weekly:
      "Unconditional, organic service. Offer your energy, skills, or support anonymously to an individual, a family, or a piece of local earth, acting as the direct, helping hands of cosmic justice.",
    video: { id: "QbIHdUbMiN4", title: "Grounding & Community Connection", creator: "Spirit Science" },
  },
];

const PRINCIPLES = [
  {
    title: "The Spiral Progress",
    kemetic: "Khepera \u2014 becoming, always becoming.",
    body: "Returning to Tier 1 after completing Tier 3 is not a regression. It is returning to the roots with a completely upgraded perception. Every repetition is a deeper octave of the same lesson \u2014 what felt difficult in the first cycle becomes baseline in the second.",
  },
  {
    title: "Biological Integrity",
    kemetic: "The Ankh \u2014 life before symbol.",
    body: "Reclaiming truth demands major shifts in biological energy. If the process causes spiritual fatigue or emotional overload, ground your body immediately. Eat root foods, drink clear spring water, and physically submerge yourself in natural elements to stabilize your nervous system.",
  },
  {
    title: "Natural Sovereignty",
    kemetic: "The Djed \u2014 stability that bends, never breaks.",
    body: "This blueprint is a living framework, not a rigid prison. If a day is disrupted, do not descend into guilt \u2014 guilt is a tool of institutional control. Observe the interruption neutrally and resume the protocol with the next sunrise.",
  },
];

const SUPPLEMENTARY_VIDEOS = [
  { id: "JTBGpEYqyUg", title: "Ma\u2019at: The Ancient Egyptian Concept of Truth and Justice", creator: "The Knowledge Channel", why: "Foundation for the Freedom Audit" },
  { id: "VMdJWQhMtSU", title: "Kemetic Yoga and Pranayama \u2014 Breath as Life", creator: "Yoga With Kim", why: "Context for the Ankh practice" },
  { id: "nG2dKzYfN_M", title: "Scarab Symbolism and Khepera \u2014 Becoming, Always Becoming", creator: "Egyptian History", why: "Why Tier 1 returns \u2014 deeper octave" },
  { id: "kYfKFSZPADE", title: "Sankofa \u2014 Return and Recover African Wisdom", creator: "African Earth", why: "Beyond the Nile \u2014 pan-African continuum" },
  { id: "Xm5HJcbKC1s", title: "The Kongo Cosmogram Dikenga \u2014 Spiral of Birth, Life, Death, Rebirth", creator: "Kongo World", why: "The spiral of the Protocols" },
];

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function AscensionProtocols() {
  const [activePhase, setActivePhase] = useState("intro");
  const audio = useAudioPlayer();

  // Scroll to top when phase changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [activePhase]);

  const phaseIdx = PHASES.findIndex((p) => p.id === activePhase);
  const canGoPrev = phaseIdx > 0;
  const canGoNext = phaseIdx < PHASES.length - 1;

  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 55%,#0d1a0a 100%)", color: "#fff" }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
          <div className="overline" style={{ color: "#E8A51E" }}>7 Days · 30 Days · 90 Days · The Guild · The Syllabus Is the Teacher</div>
          <h1 className="font-heading font-black mt-3" style={{ fontSize: "clamp(1.9rem, 5vw, 3.4rem)", lineHeight: 1.1, fontWeight: 900 }}>
            The Ascension Protocols
          </h1>
          <p className="font-heading font-bold" style={{ fontSize: "clamp(1.05rem, 2.4vw, 1.5rem)", color: "rgba(255,255,255,0.85)", marginTop: 8 }}>
            A Course in Ancestral and Cosmic Remembrance
          </p>
          <p style={{ color: "rgba(255,255,255,0.65)", maxWidth: 680, lineHeight: 1.7, marginTop: 16, fontSize: "0.98rem" }}>
            The Ascension Protocols are an open-access roadmap designed to bypass historical distortions, institutional amnesia,
            and colonized concepts of enlightenment. True enlightenment is not a status to be achieved or an elite mystery to be
            bought; it is the natural, organic state of human awareness before it was systematically disrupted by artificial
            socio-economic structures and forced separation from the living cosmos.
          </p>
          <p style={{ color: "rgba(255,255,255,0.65)", maxWidth: 680, lineHeight: 1.7, marginTop: 12, fontSize: "0.98rem" }}>
            You do not need to \u201Cevolve\u201D into something artificial; you need to remember the unbroken lineage of cosmic
            intelligence that already resides within your biology. You are the living tissue of the universe experiencing
            itself in physical form. These protocols provide a structured, three-tiered rhythm \u2014 7 days, 30 days, and 90 days \u2014
            to strip away imposed conditioning and re-establish your direct, unmediated connection to the primordial source.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/store" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              Get the Workbook · $9.99
            </Link>
            <button onClick={() => setActivePhase("tier1")} className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
              Begin Tier 1 →
            </button>
          </div>
        </div>
      </section>

      {/* ── SEQUENTIAL MODULE NAV ────────────────────────────────────────── */}
      <section className="sticky top-0 z-30" style={{ background: "#1c1917", borderBottom: "2px solid #2a2318" }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-1 overflow-x-auto py-2" style={{ scrollbarWidth: "none" }}>
            {PHASES.map((p, i) => (
              <button
                key={p.id}
                onClick={() => setActivePhase(p.id)}
                className="flex-shrink-0 px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap"
                style={{
                  background: activePhase === p.id ? "#E8A51E" : "transparent",
                  color: activePhase === p.id ? "#0a0a0a" : "rgba(255,255,255,0.6)",
                }}
              >
                <span className="mr-1">{p.icon}</span> {p.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── PHASE CONTENT (Sequential — only one shown at a time) ──────── */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">

        {/* ══════════ INTRODUCTION ══════════ */}
        {activePhase === "intro" && (
          <>
            {/* The Kemetic Foundation */}
            <section className="mb-12">
              <div className="overline text-copper mb-2">The Frame · Kemetic & Pan-African</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-3">Why the Ancestral Frame Is the Structure \u2014 Not Decoration</h2>
              <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.98rem" }}>
                These protocols are not \u201CAfrican-themed\u201D wellness content. They are built on the operating system of Kemet \u2014
                the Nile Valley civilization \u2014 because that system already understands what this curriculum does. The practices
                you will do are the same technologies the Kemetic priesthood used: dawn rites, breath as life, the audit of
                truth, the unshakeable spine, the spiral return. Naming them is not decoration; it restores the lineage the
                curriculum was always walking. And this platform already carries that lineage in its architecture:{" "}
                <strong>The 9</strong> \u2014 the unified council mind of WAI-Institute \u2014 is the modern name of the{" "}
                <strong>Pesedjet</strong>, the Great Ennead of Kemet.
              </p>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
                {[
                  ["Ma\u2019at", "Truth, balance, order \u2014 the feather. The Sovereignty Ledger weighs your heart against it each evening."],
                  ["Djed", "The backbone of Ausar. The \u201Cunshakeable pillar\u201D of the Midday Anchor is the Djed \u2014 stability that bends, never breaks."],
                  ["Khepera", "The self-created scarab. The spiral return to Tier 1 is Khepera: becoming, always becoming, never repeating."],
                  ["Ankh", "Breath is life. Every breathwork practice in these protocols is the Ankh exercised consciously."],
                  ["Sema Tawy", "The uniting of the two lands. Tier 3\u2019s sovereign walk unites spirit and daily life into one body."],
                  ["The Pesedjet / The 9", "The Great Ennead \u2014 the council of nine. The platform\u2019s own unified council mind is its heir."],
                ].map(([t, b]) => (
                  <div key={t} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="font-heading font-extrabold text-copper" style={{ fontSize: "1.05rem" }}>{t}</div>
                    <p className="text-sm text-ink/70 mt-2 leading-relaxed">{b}</p>
                  </div>
                ))}
              </div>
              <p className="text-sm text-ink/60 mt-6 leading-relaxed max-w-3xl">
                <strong style={{ color: "#1c1917" }}>Beyond the Nile:</strong> Kemet is one civilization in a vast African continuum.
                This curriculum also moves with the Sankofa of the Akan (return to fetch what was left behind), the celestial vault
                of Dogon cosmology, and the Kongo cosmogram \u2014 the spiral of birth, life, death, and rebirth that the Protocols\u2019
                cyclical structure traces. Wherever you stand on the continent\u2019s map, the original design is yours to remember.
              </p>
            </section>

            {/* The Calendar */}
            <section className="mb-12" id="calendar">
              <div className="overline text-copper mb-2">The Schedule · Kept by Nature, Not by a Server</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-4">The Lunar Calendar \u2014 No App, No Emails, No Cost</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  ["\uD83C\uDF11 The New Moon Start", "Tier 1 begins on the night of the new moon. The 30-day and 90-day protocols always begin with the next new moon. Kemetic festivals were lunar \u2014 this is the old way of keeping sacred time."],
                  ["\uD83C\uDF0A Akhet · The Inundation", "Month 1 of Tier 3 \u2014 the waters rise and the old land dissolves. Stripping the false self."],
                  ["\uD83C\uDF31 Peret · The Emergence", "Month 2 \u2014 the waters recede and life emerges from the mud. Building your own force."],
                  ["\uD83C\uDF3E Shemu · The Harvest", "Month 3 \u2014 gathering and sharing what grew. The sovereign walk and service."],
                  ["\uD83D\uDD04 The Spiral", "Completing the 90 days is a milestone, not an end. Return to Tier 1 \u2014 the roots, with upgraded perception."],
                  ["\uD83C\uDF0D One Global Cohort", "Every student on the same moon, everywhere. A synchronized cohort with zero automated email sequences required."],
                ].map(([t, b]) => (
                  <div key={t} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="font-heading font-extrabold text-ink" style={{ fontSize: "1rem" }}>{t}</div>
                    <p className="text-sm text-ink/70 mt-2 leading-relaxed">{b}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Principles Preview */}
            <section className="mb-12">
              <div className="overline text-copper mb-2">Long-Term Recalibration</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-2">Principles of the Spiral Progress</h2>
              <div className="grid md:grid-cols-3 gap-5 mt-6">
                {PRINCIPLES.map((p) => (
                  <div key={p.title} className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <h3 className="font-heading font-extrabold text-lg text-ink">{p.title}</h3>
                    <div className="text-xs font-bold mt-1" style={{ color: "#92400e" }}>{p.kemetic}</div>
                    <p className="text-sm text-ink/70 mt-3 leading-relaxed">{p.body}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* Start button */}
            <div className="text-center">
              <button onClick={() => setActivePhase("tier1")} className="inline-flex items-center gap-2 font-bold text-sm px-8 py-4 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                Begin Tier 1: The Foundational Protocol →
              </button>
            </div>
          </>
        )}

        {/* ══════════ TIER 1 — 7 DAYS ══════════ */}
        {activePhase === "tier1" && (
          <>
            <section>
              <div className="overline text-copper mb-2">Tier 1 · 7 Days · Reclaiming the Organic Signal</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-2">The Foundational Protocol</h2>
              <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
                Shaking off the mental gravity of artificial systems and re-aligning the nervous system with original cosmic
                indicators. Execute these three foundational anchors daily for seven consecutive days. They require no external
                tools, tokens, or systems \u2014 only your breath, your awareness, and the natural elements.
              </p>
              <div className="space-y-6 mt-8">
                {TIER1.map((a) => (
                  <div key={a.n} className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-xs font-bold" style={{ color: "#92400e" }}>ANCHOR {a.n} · {a.time}</div>
                        <h3 className="font-heading font-extrabold text-xl text-ink mt-1">{a.name}</h3>
                      </div>
                      <AudioControls
                        id={`tier1-${a.n}`}
                        text={`Anchor ${a.n}: ${a.name}. ${a.practice}`}
                        playingId={audio.playingId}
                        play={audio.play}
                        stop={audio.stop}
                      />
                    </div>
                    <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                      <span style={{ fontSize: 16 }}>{"\u{1F0C1}"}</span>
                      <p className="text-sm text-ink/80 leading-relaxed">{a.kemetic}</p>
                    </div>
                    <p className="text-sm text-ink/80 leading-relaxed mt-3">{a.practice}</p>
                    <details className="mt-3 rounded-xl" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                      <summary className="cursor-pointer text-sm font-bold px-4 py-3" style={{ color: "#1c1917" }}>
                        Show the exercise, step by step
                      </summary>
                      <ol className="px-4 pb-4 text-sm text-ink/75 space-y-2 leading-relaxed">
                        {a.steps.map((s, i) => <li key={i}>{i + 1}. {s}</li>)}
                      </ol>
                    </details>
                    {/* Embedded Video */}
                    {a.video && (
                      <div className="mt-4">
                        <EmbeddedVideo videoId={a.video.id} title={a.video.title} creator={a.video.creator} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Week 1 Score Prompt */}
            <div className="mt-10 rounded-2xl p-6 text-center" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 60%,#0d1a0a 100%)", color: "#fff" }}>
              <div className="overline" style={{ color: "#E8A51E" }}>After 7 Days</div>
              <h3 className="font-heading font-extrabold text-xl mt-2">Week 1 Score</h3>
              <p className="text-sm mt-2 max-w-xl mx-auto" style={{ color: "rgba(255,255,255,0.7)" }}>
                Did you beat yesterday? Look back at Day 1. You\u2019ve already begun. Now move to Tier 2.
              </p>
              <button onClick={() => setActivePhase("tier2")} className="mt-5 inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                Begin Tier 2: The Integration Protocol →
              </button>
            </div>
          </>
        )}

        {/* ══════════ TIER 2 — 30 DAYS ══════════ */}
        {activePhase === "tier2" && (
          <>
            <section>
              <div className="overline text-copper mb-2">Tier 2 · 30 Days · Clearing the Conditioning</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-2">The Integration Protocol</h2>
              <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
                Systematically dismantling internal defense mechanisms, reclaiming ancestral resonance, and purifying emotional
                biology. The 30-day container uses weekly thematic focuses to steadily clean the vessel of your physical body
                and mind from deeply ingrained societal training.
              </p>
              <div className="space-y-6 mt-8">
                {TIER2.map((w) => (
                  <div key={w.week} className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="text-xs font-bold" style={{ color: "#92400e" }}>WEEK {w.week} · {w.days}</div>
                        <h3 className="font-heading font-extrabold text-xl text-ink mt-1">{w.theme}</h3>
                      </div>
                      <AudioControls
                        id={`tier2-${w.week}`}
                        text={`Week ${w.week}: ${w.theme}. Practice: ${w.practice} Protocol: ${w.protocol}`}
                        label="Listen to this week"
                        playingId={audio.playingId}
                        play={audio.play}
                        stop={audio.stop}
                      />
                    </div>
                    <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                      <span style={{ fontSize: 16 }}>{"\u{132B9}"}</span>
                      <p className="text-sm text-ink/80 leading-relaxed">{w.kemetic}</p>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4 mt-4">
                      <div className="rounded-xl p-4" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                        <div className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>The Practice</div>
                        <p className="text-sm text-ink/80 leading-relaxed mt-2">{w.practice}</p>
                      </div>
                      <div className="rounded-xl p-4" style={{ background: "#faf9f7", border: "1px solid #f0eadf" }}>
                        <div className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>The Protocol</div>
                        <p className="text-sm text-ink/80 leading-relaxed mt-2">{w.protocol}</p>
                      </div>
                    </div>
                    {/* Embedded Video */}
                    {w.video && (
                      <div className="mt-4">
                        <EmbeddedVideo videoId={w.video.id} title={w.video.title} creator={w.video.creator} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Ledgers */}
            <section className="mt-12">
              <div className="overline text-copper mb-2">The Ledgers · Your Feather & Your Account</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-4">Print Your Ledgers \u2014 No Login, No Database</h2>
              <div className="grid md:grid-cols-2 gap-5">
                <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <h3 className="font-heading font-extrabold text-lg text-ink">The Sovereignty Ledger</h3>
                  <p className="text-sm text-ink/70 mt-2 leading-relaxed">
                    Tier 2, Week 4 (and every evening from then on): three moments each day where you acted out of innate
                    spiritual integrity rather than societal pressure or defensive ego loops.
                  </p>
                  <div className="mt-4"><PrintButton title="Sovereignty Ledger" rows={LedgerRows(30, "Day")} /></div>
                </div>
                <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <h3 className="font-heading font-extrabold text-lg text-ink">The Energy Ledger of Dead Weight</h3>
                  <p className="text-sm text-ink/70 mt-2 leading-relaxed">
                    Tier 3, Month 1 (Akhet): every seventh night, identify where you are expending life force to protect
                    someone else\u2019s comfortable illusions.
                  </p>
                  <div className="mt-4"><PrintButton title="Energy Ledger" rows={LedgerRows(30, "Night")} /></div>
                </div>
              </div>
            </section>

            {/* Week 2 Score */}
            <div className="mt-10 rounded-2xl p-6 text-center" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 60%,#0d1a0a 100%)", color: "#fff" }}>
              <div className="overline" style={{ color: "#E8A51E" }}>After 30 Days</div>
              <h3 className="font-heading font-extrabold text-xl mt-2">Tier 2 Complete</h3>
              <p className="text-sm mt-2 max-w-xl mx-auto" style={{ color: "rgba(255,255,255,0.7)" }}>
                You\u2019ve spent 30 days clearing the conditioning. The vessel is cleaner now. Ready for full embodiment?
              </p>
              <button onClick={() => setActivePhase("tier3")} className="mt-5 inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                Begin Tier 3: The Embodiment Protocol →
              </button>
            </div>
          </>
        )}

        {/* ══════════ TIER 3 — 90 DAYS ══════════ */}
        {activePhase === "tier3" && (
          <>
            <section>
              <div className="overline text-copper mb-2">Tier 3 · 90 Days · The Unbroken Blueprint</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-2">The Embodiment Protocol</h2>
              <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
                Full cellular transformation, anchoring your cosmic responsibility, and holding an unshakeable baseline of truth
                amid external chaos. Divided into three structural lunar phases \u2014 the three seasons of the Kemetic year.
              </p>
              <div className="space-y-6 mt-8">
                {TIER3.map((m) => (
                  <div key={m.month} className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                    <div className="text-xs font-extrabold tracking-wide" style={{ color: "#92400e" }}>{m.season}</div>
                    <p className="text-xs text-ink/50 italic mt-1">{m.season_note}</p>
                    <h3 className="font-heading font-extrabold text-xl text-ink mt-3">{m.objective}</h3>
                    <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                      <span style={{ fontSize: 16 }}>{"\u{132B4}"}</span>
                      <p className="text-sm text-ink/80 leading-relaxed">{m.kemetic}</p>
                    </div>
                    <AudioControls
                      id={`tier3-${m.month}`}
                      text={`${m.season}. ${m.objective}. ${m.daily.join(" ")} Weekly focus: ${m.weekly}`}
                      label="Listen to this month"
                      playingId={audio.playingId}
                      play={audio.play}
                      stop={audio.stop}
                    />
                    <ul className="mt-4 space-y-2">
                      {m.daily.map((d, i) => (
                        <li key={i} className="text-sm text-ink/80 leading-relaxed flex gap-2">
                          <span style={{ color: "#E8A51E" }}>{"\u25C6"}</span><span>{d}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-3 rounded-xl px-4 py-3" style={{ background: "#faf9f7", border: "1px dashed #d9c9a8" }}>
                      <span className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>Weekly focus: </span>
                      <span className="text-sm text-ink/80">{m.weekly}</span>
                    </div>
                    {/* Embedded Video */}
                    {m.video && (
                      <div className="mt-4">
                        <EmbeddedVideo videoId={m.video.id} title={m.video.title} creator={m.video.creator} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Supplementary Wisdom Lectures */}
            <section className="mt-12">
              <div className="rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="text-xs font-extrabold uppercase tracking-wide mb-3" style={{ color: "#92400e" }}>
                  Supplementary · Ancestral Wisdom Lectures
                </div>
                <div className="space-y-3">
                  {SUPPLEMENTARY_VIDEOS.map((v) => (
                    <EmbeddedVideo key={v.id} videoId={v.id} title={v.title} creator={v.creator} />
                  ))}
                </div>
              </div>
            </section>

            {/* Reckoning Score */}
            <div className="mt-10 rounded-2xl p-6 text-center" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 60%,#0d1a0a 100%)", color: "#fff" }}>
              <div className="overline" style={{ color: "#E8A51E" }}>After 90 Days</div>
              <h3 className="font-heading font-extrabold text-xl mt-2">The Reckoning</h3>
              <p className="text-sm mt-2 max-w-xl mx-auto" style={{ color: "rgba(255,255,255,0.7)" }}>
                You\u2019ve spent 90 days in the Arena. Look at who you were on Day 1. Look at who you are now.
                The score? Only you know it. Now join the Guild.
              </p>
              <button onClick={() => setActivePhase("phase4")} className="mt-5 inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                Enter The Guild →
              </button>
            </div>
          </>
        )}

        {/* ══════════ PHASE 4 — THE GUILD (Community) ══════════ */}
        {activePhase === "phase4" && (
          <>
            <section>
              <div className="overline text-copper mb-2">Phase 4 · The Guild · Ongoing</div>
              <h2 className="font-heading font-black text-3xl text-ink mb-2">The Arena Community</h2>
              <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
                The workbook is the entry point. The Guild is the backbone. You don\u2019t just complete the Ascension Protocols \u2014
                you walk them with others. This is where the 21-day challenge becomes a living school.
              </p>

              {/* Tier Cards */}
              <div className="grid md:grid-cols-3 gap-5 mt-8">
                {/* Novice */}
                <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <div className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>Novice</div>
                  <div className="font-heading font-extrabold text-2xl text-ink mt-2">Free</div>
                  <ul className="mt-4 space-y-2 text-sm text-ink/75">
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Streak tracking</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Personal stats</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Access to the Codex</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> #AscensionProtocolsWAI</li>
                  </ul>
                  <Link to="/register" className="mt-6 block text-center font-bold text-sm px-4 py-3 rounded-xl border" style={{ borderColor: "#d9c9a8", color: "#8a5a00" }}>
                    Join Free
                  </Link>
                </div>

                {/* Acolyte */}
                <div className="rounded-2xl p-6 relative" style={{ background: "#fff", border: "2px solid #E8A51E" }}>
                  <div className="absolute -top-3 right-4 px-3 py-1 rounded-full text-xs font-extrabold" style={{ background: "#E8A51E", color: "#0a0a0a" }}>Most Popular</div>
                  <div className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>Acolyte</div>
                  <div className="font-heading font-extrabold text-2xl text-ink mt-2">$9.99</div>
                  <ul className="mt-4 space-y-2 text-sm text-ink/75">
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> All 3 phases + workbook</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Audio reflections</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Arena Rules poster</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Guild challenges</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Community access</li>
                  </ul>
                  <Link to="/store" className="mt-6 block text-center font-bold text-sm px-4 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                    Get the Workbook
                  </Link>
                </div>

                {/* Master */}
                <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <div className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>Master</div>
                  <div className="font-heading font-extrabold text-2xl text-ink mt-2">$29.99</div>
                  <ul className="mt-4 space-y-2 text-sm text-ink/75">
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Everything in Acolyte</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Monthly live Q&A</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Exclusive badges</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> The Codex (full)</li>
                    <li className="flex gap-2"><span style={{ color: "#E8A51E" }}>{"\u2713"}</span> Priority community</li>
                  </ul>
                  <Link to="/store" className="mt-6 block text-center font-bold text-sm px-4 py-3 rounded-xl border" style={{ borderColor: "#d9c9a8", color: "#8a5a00" }}>
                    Upgrade to Master
                  </Link>
                </div>
              </div>
            </section>

            {/* The Codex */}
            <section className="mt-12">
              <div className="rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="text-xs font-extrabold uppercase tracking-wide mb-3" style={{ color: "#92400e" }}>The Codex</div>
                <h3 className="font-heading font-extrabold text-xl text-ink">A Crowd-Sourced Library of Arena Rules</h3>
                <p className="text-sm text-ink/70 mt-2 leading-relaxed max-w-3xl">
                  Participants share their personal Arena Rules \u2014 the micro-challenges that changed them.
                  Each one is a seed. &quot;My +1 was to stop doomscrolling at 9 PM.&quot; &quot;My +1 was to drink water before coffee.&quot;
                  The Codex grows with every student who enters the Arena.
                </p>
                <div className="mt-4 grid sm:grid-cols-2 gap-3">
                  {[
                    "My +1 was to write 100 words before checking my phone.",
                    "My +1 was to walk barefoot for 5 minutes at dawn.",
                    "My +1 was to say one true thing per conversation.",
                    "My +1 was to sit in silence for 3 minutes at noon.",
                  ].map((rule, i) => (
                    <div key={i} className="rounded-xl p-3 text-sm" style={{ background: "#fff", border: "1px solid #f0eadf", fontStyle: "italic", color: "#555" }}>
                      &quot;{rule}&quot;
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Badge System */}
            <section className="mt-8">
              <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <div className="text-xs font-extrabold uppercase tracking-wide mb-3" style={{ color: "#92400e" }}>Badge System</div>
                <div className="flex flex-wrap gap-3">
                  {[
                    { badge: "Baseline", icon: "☀", desc: "Completed Tier 1" },
                    { badge: "Forge", icon: "🔥", desc: "Completed Tier 2" },
                    { badge: "Reckoning", icon: "⚖", desc: "Completed Tier 3" },
                    { badge: "Arena Veteran", icon: "🏛", desc: "Completed the full spiral" },
                  ].map((b) => (
                    <div key={b.badge} className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                      <span style={{ fontSize: 24 }}>{b.icon}</span>
                      <div>
                        <div className="font-bold text-sm text-ink">{b.badge}</div>
                        <div className="text-xs text-ink/50">{b.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Community Close */}
            <section className="mt-12 rounded-2xl p-8 text-center" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 60%,#0d1a0a 100%)", color: "#fff" }}>
              <div className="overline" style={{ color: "#E8A51E" }}>Open-Access · Peer Accountability · Zero Drain</div>
              <h2 className="font-heading font-black text-3xl mt-3">The Platform Hosts the Curriculum. You Host the Community.</h2>
              <p className="max-w-2xl mx-auto mt-4 leading-relaxed" style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.98rem" }}>
                Keep your own physical notebook. If you want accountability, use the free, open hashtag{" "}
                <strong style={{ color: "#E8A51E" }}>#AscensionProtocolsWAI</strong> across open platforms, or start a free
                community space. No forum software to buy, no membership platform to rent \u2014 just the moon, the ledger, and
                each other.
              </p>
              <div className="flex flex-wrap justify-center gap-3 mt-8">
                <Link to="/store" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
                  Get the Workbook · $9.99
                </Link>
                <Link to="/courses" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
                  See all courses
                </Link>
                <Link to="/helper" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
                  Need help? Ask the Helper
                </Link>
              </div>
              <p className="text-xs mt-8" style={{ color: "rgba(255,255,255,0.4)" }}>
                This course runs entirely in your browser and in your life \u2014 zero tokens, zero server cost, zero data stored.
                On the platform, The 9 (the Pesedjet) stands ready to help you coordinate any project that grows from it.
              </p>
            </section>
          </>
        )}
      </div>

      {/* ── PHASE NAVIGATION FOOTER ──────────────────────────────────────── */}
      <div className="sticky bottom-0 z-30" style={{ background: "#1c1917", borderTop: "2px solid #2a2318" }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <button
            onClick={() => canGoPrev && setActivePhase(PHASES[phaseIdx - 1].id)}
            disabled={!canGoPrev}
            className="font-bold text-sm px-5 py-2.5 rounded-lg transition-all"
            style={{
              background: canGoPrev ? "rgba(232,165,30,0.15)" : "transparent",
              color: canGoPrev ? "#E8A51E" : "rgba(255,255,255,0.3)",
              cursor: canGoPrev ? "pointer" : "not-allowed",
            }}
          >
            ← {canGoPrev ? PHASES[phaseIdx - 1].label : "Previous"}
          </button>
          <div className="text-xs font-bold" style={{ color: "rgba(255,255,255,0.5)" }}>
            {phaseIdx + 1} / {PHASES.length}
          </div>
          <button
            onClick={() => canGoNext && setActivePhase(PHASES[phaseIdx + 1].id)}
            disabled={!canGoNext}
            className="font-bold text-sm px-5 py-2.5 rounded-lg transition-all"
            style={{
              background: canGoNext ? "#E8A51E" : "transparent",
              color: canGoNext ? "#0a0a0a" : "rgba(255,255,255,0.3)",
              cursor: canGoNext ? "pointer" : "not-allowed",
            }}
          >
            {canGoNext ? PHASES[phaseIdx + 1].label : "Complete"} →
          </button>
        </div>
      </div>
    </div>
  );
}
