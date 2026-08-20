import { Link } from "react-router-dom";
import PublicNav from "../components/PublicNav";

// ===========================================================================
// THE ASCENSION PROTOCOLS — A Course in Ancestral and Cosmic Remembrance
// ---------------------------------------------------------------------------
// Open-access, static, ZERO-DRAIN curriculum (syllabus-as-teacher model):
//   • No API calls. No tokens. No server cost per reader.
//   • All media is hosted externally (YouTube search links) — external hosts
//     pay the bandwidth, the platform is only the curated gateway.
//   • "Listen" uses the browser's built-in speech synthesis — free, offline.
//   • Ledgers print from the browser — no server round-trip.
//   • The schedule is kept by the moon — no databases, no email automation.
// The Kemetic/pan-African frame is structural, not decorative: each pillar
// below (Ma'at, Djed, Khepera, Ankh, Sema Tawy, the Pesedjet) anchors a real
// practice in the curriculum.
// ===========================================================================

function speak(text) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.92;
  u.pitch = 1;
  window.speechSynthesis.speak(u);
}

function ListenButton({ text, label = "Listen to this practice" }) {
  return (
    <button
      onClick={() => speak(text)}
      className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full"
      style={{ background: "rgba(232,165,30,0.12)", color: "#8a5a00", border: "1px solid rgba(232,165,30,0.35)" }}
    >
      🔊 {label}
    </button>
  );
}

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
    f.style.position = "fixed";
    f.style.right = "0";
    f.style.bottom = "0";
    f.style.width = "0";
    f.style.height = "0";
    f.style.border = "0";
    document.body.appendChild(f);
    f.contentDocument.open();
    f.contentDocument.write(html);
    f.contentDocument.close();
    setTimeout(() => {
      try {
        f.contentWindow.focus();
        f.contentWindow.print();
      } catch {
        /* popup/print blocked — user can still print the page itself */
      }
      setTimeout(() => f.remove(), 60_000);
    }, 250);
  };
  return (
    <button
      onClick={print}
      className="inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full"
      style={{ background: "#1f2933", color: "#fff" }}
    >
      🖨️ Print {title}
    </button>
  );
}

function LedgerRows(days, label) {
  let out = "";
  for (let d = 1; d <= days; d++) out += `<tr><td class="day">${label} ${d}</td><td></td></tr>`;
  return out;
}

const SUPPORT_LINK = (q) => `https://www.youtube.com/results?search_query=${encodeURIComponent(q)}`;

const TIER1 = [
  {
    n: 1,
    name: "The Dawn First-Light Alignment",
    time: "5–10 minutes",
    kemetic: "Khepera — the self-created scarab who rolls the sun across the horizon each dawn. This anchor opens the day the way the temple opened at sunrise.",
    practice:
      "Before engaging with any digital interfaces or human-made frequencies, stand barefoot upon the naked earth or look out toward the eastern horizon. Recognize that the sun is the primary living broadcaster of life-force and memory to this planet. Breathe deeply through your nose, drawing the morning light down into your bone marrow. Declare internally: “I am an unbroken extension of the primary creation. I return my awareness to the original design.”",
    steps: [
      "Wake and do this BEFORE any screen. A window counts; bare earth counts more.",
      "Stand flat-footed, spine long, shoulders relaxed. Face east.",
      "Breathe in through the nose for 5 seconds, hold 2, exhale 7 — repeat.",
      "Draw the light down to the marrow of your legs, arms, spine.",
      "Speak the declaration silently, then go about your day.",
    ],
    support: "Morning Light Visualization Meditation",
  },
  {
    n: 2,
    name: "The Midday Stasis Anchor",
    time: "3 minutes",
    kemetic: "The Djed pillar — the backbone of Ausar, the symbol of stability and endurance. Your spine erect is the Djed; the chatter you observe is not you.",
    practice:
      "At high noon, when the external world demands maximum performance and extraction of your labor, halt entirely. Place both feet flat on the floor, spine erect like an unshakeable pillar. Close your eyes and pull your attention away from external tasks. Observe the mental chatter not as your identity, but as synthetic noise running through a temporary broadcast tower. Find the silent, primordial void beneath the chatter and rest there.",
    steps: [
      "Set a noon reminder — the anchor takes 3 minutes, no longer.",
      "Both feet flat. Spine stacked. Hands open on your thighs.",
      "Close the eyes. Name the chatter: “noise,” not “me.”",
      "Rest in the silence beneath it for the remaining time.",
    ],
    support: "5 Minute Nervous System Grounding Exercise",
  },
  {
    n: 3,
    name: "The Night Element Dissolve",
    time: "10 minutes",
    kemetic: "The retrograde review — the Kemetic practice of reciting the day before the Hall of Two Truths at the close of the day: witness, do not re-live.",
    practice:
      "Before sleep, sit in absolute stillness. Mentally trace your day in reverse order, from the present moment back to the dawn. As you review each event, perceive it through a lens of neutral cosmic history. Strip away the emotional demands, the systemic stress, and the roles you were forced to play. Wash your hands or face in cold water to physically and energetically sever the daily cycle, ensuring your subconscious dreams remain unpolluted by artificial anxieties.",
    steps: [
      "Sit upright in dim light or candlelight. No screens after this point.",
      "Run the day backward: evening → afternoon → noon → morning.",
      "Witness each scene as neutral history — a token exchange, not a verdict.",
      "Finish with cold water on the hands and face. The day is closed.",
    ],
    support: "Somatic Cleansing and Release Meditation",
  },
];

const TIER2 = [
  {
    week: 1,
    days: "Days 1–7",
    theme: "Decolonizing the Subconscious Workspace",
    kemetic: "Djehuty — the scribe of truth. Writing uncensored is the scribe's discipline: pour out the vessel before the day begins.",
    practice:
      "Uncensored morning downloads. Upon waking, immediately write down three pages of raw, stream-of-consciousness text. Do not edit, judge, or read it over. This clears the cognitive residue left behind by institutional programming.",
    protocol:
      "Total information sovereignty. Abstain from algorithmic media feeds, synthetic entertainment, and commercial advertisements. Protect your mind as sacred, unmonetized territory.",
    support: "Guide to Unconscious Mind Integration",
  },
  {
    week: 2,
    days: "Days 8–14",
    theme: "Restoring Somatic Intelligence",
    kemetic: "The Ankh — breath is life. And Ma'at's law of speech: maa-kheru, “true of voice,” speaking only what is true, necessary, and regenerative.",
    practice:
      "Primary heart-rhythm breathing. Dedicate 15 minutes each afternoon to breathing exclusively into the physical chest cavity. Feel the heart not merely as a pump, but as an ancient, intelligent organ capable of direct cosmic perception.",
    protocol:
      "Impeccability of expression. Monitor every word that crosses your lips. Refuse to participate in systemic gossip, self-diminishment, or complaints that reinforce a victim architecture. Speak only what is historically true, intrinsically necessary, and regenerative.",
    support: "20 Minute Guided Heart Resonance Breathwork",
  },
  {
    week: 3,
    days: "Days 15–21",
    theme: "Expanding Spatial Sovereignty",
    kemetic: "The horizon and the ancestors — in Kemetic thought the Akh (the luminous spirit) stands on the horizon at dawn. You are that standing ground.",
    practice:
      "Ancestral landscape extension. Spend 15 minutes daily sitting silently, breathing, and visualizing your awareness expanding downward into the deep layers of the earth beneath you, acknowledging the generations of ancestors who stood upon it, and expanding outward to touch the horizon. Realize you are part of a continuous, living fabric.",
    protocol:
      "Direct earth communication. Spend 20 minutes a day in direct physical contact with living matter — trees, soil, natural water, or stone. Intentionally match your heartbeat to the slower, ancient rhythm of the ecosystem.",
    support: "Ancestral Connection Somatic Guide",
  },
  {
    week: 4,
    days: "Days 22–30",
    theme: "Activating Autonomous Creation",
    kemetic: "The Weighing of the Heart — in the Hall of Two Truths the heart is weighed against the feather of Ma'at. The Sovereignty Ledger is your daily feather: three moments you acted from integrity.",
    practice:
      "The Sovereignty Ledger. Each evening, document three specific moments where you chose to act out of innate spiritual integrity rather than societal pressure or defensive ego loops.",
    protocol:
      "Organic play and creation. Dedicate 20 minutes daily to physical movement, vocal sounding, or physical crafting without seeking external evaluation, monetization, or applause. Let your soul express itself purely for the joy of creation.",
    support: "Heart Coherence and Creative Flow Visualization",
  },
];

const TIER3 = [
  {
    month: 1,
    season: "AKHET — The Inundation (Days 1–30)",
    season_note: "The Nile floods, the old land dissolves, and what was buried rises. This month you do the same.",
    objective: "The Stripping of the False Self — auditing and discarding the synthetic identities, ancestral traumas, and coping mechanisms built to survive within an oppressive society.",
    kemetic: "The 42 Declarations of Ma'at — the original ethical audit. The ancient scribe stood before the council and declared what they had NOT done. The Freedom Audit is the same discipline: name the agreements, then dissolve them.",
    daily: [
      "Maintain the Tier 1 Dawn First-Light Alignment.",
      "The Freedom Audit: every seventh night, identify every contract, relationship, or daily habit you maintain out of systemic guilt, fear, or false dependency. Begin taking quiet, logical steps to systematically dissolve those agreements.",
      "The Energy Ledger of Dead Weight: every seventh night, mark where you are expending life force to protect someone else's comfortable illusions — then close those leaks with silent, unshakeable boundary execution.",
    ],
    weekly: "Radical detachment from artificial dopamine triggers (e.g., compulsive spending, digital validation, ultra-processed substances).",
    support: "Step by Step Self-Knowledge Framework",
  },
  {
    month: 2,
    season: "PERET — The Emergence (Days 31–60)",
    season_note: "The waters recede and green life emerges from the mud. The vessel you emptied is now filling with your own force.",
    objective: "Structural Stabilization & Life-Force Accumulation — cultivating the vital energy required to withstand external pressures and maintaining an unshakeable inner compass.",
    kemetic: "The silent initiation — in the Kemetic mysteries the candidate passed through silence to be reborn. Your one day of absolute silence is that passage.",
    daily: [
      "The Breath of Original Design: 20 minutes of daily morning movement or intentional breathwork to clear blockages within your biological pathways, allowing pure life force to circulate freely.",
      "Reframe every daily systemic obstacle, bureaucratic irritation, or microaggression not as a personal defeat, but as a simulated training sequence meant to test and prove your internal emotional sovereignty.",
    ],
    weekly: "One full day of absolute auditory and communicative silence. No text, no talk, no consumption. Return completely to the quiet self.",
    support: "Somatic Movement and Body Regulation Practice",
  },
  {
    month: 3,
    season: "SHEMU — The Harvest (Days 61–90)",
    season_note: "The harvest is gathered and shared. What you cultivated now becomes presence — and presence becomes service.",
    objective: "Sovereign Walk & Active Orchestration — operating as an active, conscious conduit of cosmic truth, transforming your immediate environment through your mere presence.",
    kemetic: "Sema Tawy — “the uniting of the two lands.” Upper and Lower Egypt joined into one body; your spirit and your daily walk joined into one sovereign life.",
    daily: [
      "The Intention Broadcast: before interacting with another human being, establish the core frequency you will broadcast for the day (e.g., Absolute Truth, Unshakable Peace, Severe Clarity). Do not allow external environments to dictate your inner state.",
      "Spend 10 minutes before rest visualizing your life operating completely outside the mental and spiritual confines of current societal matrices.",
    ],
    weekly: "Unconditional, organic service. Offer your energy, skills, or support anonymously to an individual, a family, or a piece of local earth, acting as the direct, helping hands of cosmic justice.",
    support: "Grounding and Community Connection Visualization",
  },
];

const PRINCIPLES = [
  {
    title: "The Spiral Progression",
    kemetic: "Khepera — becoming, always becoming.",
    body: "Returning to Tier 1 after completing Tier 3 is not a regression. It is returning to the roots with a completely upgraded perception. Every repetition is a deeper octave of the same lesson — what felt difficult in the first cycle becomes baseline in the second.",
  },
  {
    title: "Biological Integrity",
    kemetic: "The Ankh — life before symbol.",
    body: "Reclaiming truth demands major shifts in biological energy. If the process causes spiritual fatigue or emotional overload, ground your body immediately. Eat root foods, drink clear spring water, and physically submerge yourself in natural elements to stabilize your nervous system.",
  },
  {
    title: "Natural Sovereignty",
    kemetic: "The Djed — stability that bends, never breaks.",
    body: "This blueprint is a living framework, not a rigid prison. If a day is disrupted, do not descend into guilt — guilt is a tool of institutional control. Observe the interruption neutrally and resume the protocol with the next sunrise.",
  },
];

export default function AscensionProtocols() {
  return (
    <div style={{ background: "#faf9f7", minHeight: "100dvh" }}>
      <PublicNav />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 55%,#0d1a0a 100%)", color: "#fff" }}>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-14 sm:py-20">
          <div className="overline" style={{ color: "#E8A51E" }}>7 Days · 30 Days · 90 Days · $9.99 All Phases · The Syllabus Is the Teacher</div>
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
            You do not need to “evolve” into something artificial; you need to remember the unbroken lineage of cosmic
            intelligence that already resides within your biology. You are the living tissue of the universe experiencing
            itself in physical form. These protocols provide a structured, three-tiered rhythm — 7 days, 30 days, and 90 days —
            to strip away imposed conditioning and re-establish your direct, unmediated connection to the primordial source.
          </p>
          <div className="flex flex-wrap gap-3 mt-8">
            <Link to="/store" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl" style={{ background: "#E8A51E", color: "#0a0a0a" }}>
              Get the Workbook · $9.99
            </Link>
            <a href="#calendar" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
              Start at the New Moon
            </a>
            <a href="#tier1" className="inline-flex items-center gap-2 font-bold text-sm px-6 py-3 rounded-xl border" style={{ borderColor: "rgba(255,255,255,0.25)", color: "rgba(255,255,255,0.9)" }}>
              Begin Tier 1 →
            </a>
          </div>
        </div>
      </section>

      {/* ── THE KEMETIC FOUNDATION ───────────────────────────────────────── */}
      <section className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">The Frame · Kemetic & Pan-African</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-3">Why the Ancestral Frame Is the Structure — Not Decoration</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.98rem" }}>
            These protocols are not “African-themed” wellness content. They are built on the operating system of Kemet —
            the Nile Valley civilization — because that system already understands what this curriculum does. The practices
            you will do are the same technologies the Kemetic priesthood used: dawn rites, breath as life, the audit of
            truth, the unshakeable spine, the spiral return. Naming them is not decoration; it restores the lineage the
            curriculum was always walking. And this platform already carries that lineage in its architecture:{" "}
            <strong>The 9</strong> — the unified council mind of WAI-Institute — is the modern name of the{" "}
            <strong>Pesedjet</strong>, the Great Ennead of Kemet.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
            {[
              ["Ma'at", "Truth, balance, order — the feather. The Sovereignty Ledger weighs your heart against it each evening."],
              ["Djed", "The backbone of Ausar. The “unshakeable pillar” of the Midday Anchor is the Djed — stability that bends, never breaks."],
              ["Khepera", "The self-created scarab. The spiral return to Tier 1 is Khepera: becoming, always becoming, never repeating."],
              ["Ankh", "Breath is life. Every breathwork practice in these protocols is the Ankh exercised consciously."],
              ["Sema Tawy", "The uniting of the two lands. Tier 3's sovereign walk unites spirit and daily life into one body."],
              ["The Pesedjet / The 9", "The Great Ennead — the council of nine. The platform's own unified council mind is its heir."],
            ].map(([t, b]) => (
              <div key={t} className="rounded-2xl p-5" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="font-heading font-extrabold text-copper" style={{ fontSize: "1.05rem" }}>{t}</div>
                <p className="text-sm text-ink/70 mt-2 leading-relaxed">{b}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-ink/60 mt-6 leading-relaxed max-w-3xl">
            <strong style={{ color: "#1c1917" }}>Beyond the Nile:</strong> Kemet is one civilization in a vast African continuum.
            This curriculum also moves with the Sankofa of the Akan (return to fetch what was left behind), the celestial vault
            of Dogon cosmology, and the Kongo cosmogram — the spiral of birth, life, death, and rebirth that the Protocols'
            cyclical structure traces. Wherever you stand on the continent's map, the original design is yours to remember.
          </p>
        </div>
      </section>

      {/* ── THE CALENDAR ─────────────────────────────────────────────────── */}
      <section id="calendar" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">The Schedule · Kept by Nature, Not by a Server</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-4">The Lunar Calendar — No App, No Emails, No Cost</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              ["🌑 The New Moon Start", "Tier 1 begins on the night of the new moon. The 30-day and 90-day protocols always begin with the next new moon. Kemetic festivals were lunar — this is the old way of keeping sacred time."],
              ["🌊 Akhet · The Inundation", "Month 1 of Tier 3 — the waters rise and the old land dissolves. Stripping the false self."],
              ["🌱 Peret · The Emergence", "Month 2 — the waters recede and life emerges from the mud. Building your own force."],
              ["🌾 Shemu · The Harvest", "Month 3 — gathering and sharing what grew. The sovereign walk and service."],
              ["🔄 The Spiral", "Completing the 90 days is a milestone, not an end. Return to Tier 1 — the roots, with upgraded perception."],
              ["🌍 One Global Cohort", "Every student on the same moon, everywhere. A synchronized cohort with zero automated email sequences required."],
            ].map(([t, b]) => (
              <div key={t} className="rounded-2xl p-5" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <div className="font-heading font-extrabold text-ink" style={{ fontSize: "1rem" }}>{t}</div>
                <p className="text-sm text-ink/70 mt-2 leading-relaxed">{b}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-ink/50 mt-5">
            Check the night sky, a basic calendar, or your phone's moon phase widget. The platform hosts the curriculum; nature hosts the schedule.
          </p>
        </div>
      </section>

      {/* ── TIER 1 ───────────────────────────────────────────────────────── */}
      <section id="tier1" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Tier 1 · 7 Days · Reclaiming the Organic Signal</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-2">The Foundational Protocol</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Shaking off the mental gravity of artificial systems and re-aligning the nervous system with original cosmic
            indicators. Execute these three foundational anchors daily for seven consecutive days. They require no external
            tools, tokens, or systems — only your breath, your awareness, and the natural elements. Each anchor's exercise
            is inline — tap to reveal — so you never have to hunt outside the syllabus.
          </p>
          <div className="space-y-5 mt-8">
            {TIER1.map((a) => (
              <div key={a.n} className="rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-xs font-bold" style={{ color: "#92400e" }}>ANCHOR {a.n} · {a.time}</div>
                    <h3 className="font-heading font-extrabold text-xl text-ink mt-1">{a.name}</h3>
                  </div>
                  <ListenButton text={`Anchor ${a.n}: ${a.name}. ${a.practice}`} />
                </div>
                <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                  <span style={{ fontSize: 16 }}>🜁</span>
                  <p className="text-sm text-ink/80 leading-relaxed">{a.kemetic}</p>
                </div>
                <p className="text-sm text-ink/80 leading-relaxed mt-3">{a.practice}</p>
                <details className="mt-3 rounded-xl" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                  <summary className="cursor-pointer text-sm font-bold px-4 py-3" style={{ color: "#1c1917" }}>
                    Show the exercise, step by step
                  </summary>
                  <ol className="px-4 pb-4 text-sm text-ink/75 space-y-2 leading-relaxed">
                    {a.steps.map((s, i) => <li key={i}>{i + 1}. {s}</li>)}
                  </ol>
                </details>
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <a href={SUPPORT_LINK(a.support)} target="_blank" rel="noreferrer" className="text-xs font-bold underline" style={{ color: "#8a5a00" }}>
                    ▶ Practice support: {a.support}
                  </a>
                  <span className="text-[11px] text-ink/40">hosted externally — no data cost to the platform</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TIER 2 ───────────────────────────────────────────────────────── */}
      <section id="tier2" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Tier 2 · 30 Days · Clearing the Conditioning</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-2">The Integration Protocol</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Systematically dismantling internal defense mechanisms, reclaiming ancestral resonance, and purifying emotional
            biology. The 30-day container uses weekly thematic focuses to steadily clean the vessel of your physical body
            and mind from deeply ingrained societal training.
          </p>
          <div className="space-y-5 mt-8">
            {TIER2.map((w) => (
              <div key={w.week} className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="text-xs font-bold" style={{ color: "#92400e" }}>WEEK {w.week} · {w.days}</div>
                    <h3 className="font-heading font-extrabold text-xl text-ink mt-1">{w.theme}</h3>
                  </div>
                  <ListenButton text={`Week ${w.week}: ${w.theme}. Practice: ${w.practice} Protocol: ${w.protocol}`} label="Listen to this week" />
                </div>
                <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                  <span style={{ fontSize: 16 }}>𓋹</span>
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
                <div className="mt-4">
                  <a href={SUPPORT_LINK(w.support)} target="_blank" rel="noreferrer" className="text-xs font-bold underline" style={{ color: "#8a5a00" }}>
                    ▶ Practice support: {w.support}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TIER 3 ───────────────────────────────────────────────────────── */}
      <section id="tier3" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Tier 3 · 90 Days · The Unbroken Blueprint</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-2">The Embodiment Protocol</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Full cellular transformation, anchoring your cosmic responsibility, and holding an unshakeable baseline of truth
            amid external chaos. Divided into three structural lunar phases — the three seasons of the Kemetic year.
          </p>
          <div className="space-y-5 mt-8">
            {TIER3.map((m) => (
              <div key={m.month} className="rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <div className="text-xs font-extrabold tracking-wide" style={{ color: "#92400e" }}>{m.season}</div>
                <p className="text-xs text-ink/50 italic mt-1">{m.season_note}</p>
                <h3 className="font-heading font-extrabold text-xl text-ink mt-3">{m.objective}</h3>
                <div className="flex items-start gap-2 mt-3 rounded-xl px-4 py-3" style={{ background: "rgba(232,165,30,0.08)", border: "1px solid rgba(232,165,30,0.2)" }}>
                  <span style={{ fontSize: 16 }}>𓋴</span>
                  <p className="text-sm text-ink/80 leading-relaxed">{m.kemetic}</p>
                </div>
                <ul className="mt-4 space-y-2">
                  {m.daily.map((d, i) => (
                    <li key={i} className="text-sm text-ink/80 leading-relaxed flex gap-2">
                      <span style={{ color: "#E8A51E" }}>◆</span><span>{d}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-3 rounded-xl px-4 py-3" style={{ background: "#fff", border: "1px dashed #d9c9a8" }}>
                  <span className="text-xs font-extrabold uppercase tracking-wide" style={{ color: "#92400e" }}>Weekly focus: </span>
                  <span className="text-sm text-ink/80">{m.weekly}</span>
                </div>
                <div className="mt-4">
                  <a href={SUPPORT_LINK(m.support)} target="_blank" rel="noreferrer" className="text-xs font-bold underline" style={{ color: "#8a5a00" }}>
                    ▶ Practice support: {m.support}
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LEDGERS ──────────────────────────────────────────────────────── */}
      <section id="ledgers" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#faf9f7" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">The Ledgers · Your Feather & Your Account</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-4">Print Your Ledgers — No Login, No Database</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Deep personal audits deserve a physical record. These ledgers print directly from your browser — the platform
            never stores your words. If you want community accountability, keep them in your own notebook or share
            neutrally under <strong>#AscensionProtocolsWAI</strong> on open platforms.
          </p>
          <div className="grid md:grid-cols-2 gap-5 mt-8">
            <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
              <h3 className="font-heading font-extrabold text-lg text-ink">The Sovereignty Ledger</h3>
              <p className="text-sm text-ink/70 mt-2 leading-relaxed">
                Tier 2, Week 4 (and every evening from then on): three moments each day where you acted out of innate
                spiritual integrity rather than societal pressure or defensive ego loops. This is the daily weighing of
                your heart against the feather of Ma'at.
              </p>
              <div className="mt-4"><PrintButton title="Sovereignty Ledger" rows={LedgerRows(30, "Day")} /></div>
            </div>
            <div className="rounded-2xl p-6" style={{ background: "#fff", border: "1px solid #eee7db" }}>
              <h3 className="font-heading font-extrabold text-lg text-ink">The Energy Ledger of Dead Weight</h3>
              <p className="text-sm text-ink/70 mt-2 leading-relaxed">
                Tier 3, Month 1 (Akhet): every seventh night, identify where you are expending life force to protect
                someone else's comfortable illusions. Systematically close those leaks with silent, unshakeable boundary
                execution.
              </p>
              <div className="mt-4"><PrintButton title="Energy Ledger" rows={LedgerRows(30, "Night")} /></div>
            </div>
          </div>
        </div>
      </section>

      {/* ── VIDEO LIBRARY ─────────────────────────────────────────────── */}
      <section id="videos" className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">The Companion Library · Curated Practice Videos</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-2">Watch. Breathe. Practice.</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Each practice below links to a curated YouTube search — free, publicly accessible, hosted externally.
            The platform hosts the curriculum; the videos host the experience. No data stored. No tokens spent.
          </p>
          <div className="grid md:grid-cols-2 gap-5 mt-8">
            {/* Tier 1 videos */}
            {TIER1.map((a) => (
              <a key={a.n} href={SUPPORT_LINK(a.support)} target="_blank" rel="noreferrer"
                className="rounded-2xl p-5 flex flex-col gap-2 group"
                style={{ background: "#faf9f7", border: "1px solid #eee7db", transition: "border-color 0.2s" }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "#E8A51E"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "#eee7db"}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">▶</span>
                  <span className="text-xs font-bold" style={{ color: "#92400e" }}>TIER 1 · ANCHOR {a.n}</span>
                </div>
                <div className="font-heading font-extrabold text-ink group-hover:text-copper" style={{ fontSize: "0.98rem" }}>{a.support}</div>
                <div className="text-xs text-ink/50">{a.name} · {a.time} practice</div>
              </a>
            ))}
            {/* Tier 2 videos */}
            {TIER2.map((w) => (
              <a key={w.week} href={SUPPORT_LINK(w.support)} target="_blank" rel="noreferrer"
                className="rounded-2xl p-5 flex flex-col gap-2 group"
                style={{ background: "#faf9f7", border: "1px solid #eee7db", transition: "border-color 0.2s" }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "#E8A51E"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "#eee7db"}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">▶</span>
                  <span className="text-xs font-bold" style={{ color: "#92400e" }}>TIER 2 · WEEK {w.week}</span>
                </div>
                <div className="font-heading font-extrabold text-ink group-hover:text-copper" style={{ fontSize: "0.98rem" }}>{w.support}</div>
                <div className="text-xs text-ink/50">{w.theme}</div>
              </a>
            ))}
            {/* Tier 3 videos */}
            {TIER3.map((m) => (
              <a key={m.month} href={SUPPORT_LINK(m.support)} target="_blank" rel="noreferrer"
                className="rounded-2xl p-5 flex flex-col gap-2 group"
                style={{ background: "#faf9f7", border: "1px solid #eee7db", transition: "border-color 0.2s" }}
                onMouseEnter={(e) => e.currentTarget.style.borderColor = "#E8A51E"}
                onMouseLeave={(e) => e.currentTarget.style.borderColor = "#eee7db"}
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">▶</span>
                  <span className="text-xs font-bold" style={{ color: "#92400e" }}>TIER 3 · MONTH {m.month}</span>
                </div>
                <div className="font-heading font-extrabold text-ink group-hover:text-copper" style={{ fontSize: "0.98rem" }}>{m.support}</div>
                <div className="text-xs text-ink/50">{m.season}</div>
              </a>
            ))}
          </div>
          {/* Supplementary wisdom lectures */}
          <div className="mt-8 rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
            <div className="text-xs font-extrabold uppercase tracking-wide mb-3" style={{ color: "#92400e" }}>Supplementary · Ancestral Wisdom Lectures</div>
            <div className="grid sm:grid-cols-2 gap-3">
              {[
                ["Ma'at: The Ancient Egyptian Concept of Truth and Justice", "Foundation for the Freedom Audit"],
                ["Kemetic Yoga and Pranayama — Breath as Life", "Context for the Ankh practice"],
                ["Scarab Symbolism and Khepera — Becoming, Always Becoming", "Why Tier 1 returns — deeper octave"],
                ["Sankofa — Return and Recover African Wisdom", "Beyond the Nile — pan-African continuum"],
                ["The Kongo Cosmogram Dikenga — Spiral of Birth, Life, Death, Rebirth", "The spiral of the Protocols"],
              ].map(([title, why]) => (
                <a key={title} href={SUPPORT_LINK(title)} target="_blank" rel="noreferrer"
                  className="flex gap-3 p-3 rounded-xl group"
                  style={{ background: "#fff", border: "1px solid #f0eadf" }}
                >
                  <span className="text-sm mt-0.5" style={{ color: "#E8A51E" }}>▶</span>
                  <div>
                    <div className="text-sm font-bold text-ink group-hover:text-copper" style={{ transition: "color 0.2s" }}>{title}</div>
                    <div className="text-xs text-ink/50 mt-0.5">{why}</div>
                  </div>
                </a>
              ))}
            </div>
            <p className="text-xs text-ink/40 mt-4">All videos are publicly accessible on YouTube. No paywalls. The platform curates; the external host delivers.</p>
          </div>
        </div>
      </section>

      {/* ── PRINCIPLES ───────────────────────────────────────────────────── */}
      <section className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "#fff" }}>
        <div className="max-w-5xl mx-auto">
          <div className="overline text-copper mb-2">Long-Term Recalibration</div>
          <h2 className="font-heading font-black text-3xl text-ink mb-2">Principles of the Spiral Progress</h2>
          <p className="text-ink/70 max-w-3xl leading-relaxed" style={{ fontSize: "0.95rem" }}>
            Completing the 90 days is not an “end point,” but a cyclical milestone. These three laws govern every return.
          </p>
          <div className="grid md:grid-cols-3 gap-5 mt-8">
            {PRINCIPLES.map((p) => (
              <div key={p.title} className="rounded-2xl p-6" style={{ background: "#faf9f7", border: "1px solid #eee7db" }}>
                <h3 className="font-heading font-extrabold text-lg text-ink">{p.title}</h3>
                <div className="text-xs font-bold mt-1" style={{ color: "#92400e" }}>{p.kemetic}</div>
                <p className="text-sm text-ink/70 mt-3 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── COMMUNITY + CLOSE ────────────────────────────────────────────── */}
      <section className="py-14 sm:py-16 px-4 sm:px-6" style={{ background: "linear-gradient(160deg,#0d0a06 0%,#241a08 60%,#0d1a0a 100%)", color: "#fff" }}>
        <div className="max-w-5xl mx-auto text-center">
          <div className="overline" style={{ color: "#E8A51E" }}>Open-Access · Peer Accountability · Zero Drain</div>
          <h2 className="font-heading font-black text-3xl mt-3">The Platform Hosts the Curriculum. You Host the Community.</h2>
          <p className="max-w-2xl mx-auto mt-4 leading-relaxed" style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.98rem" }}>
            Keep your own physical notebook. If you want accountability, use the free, open hashtag{" "}
            <strong style={{ color: "#E8A51E" }}>#AscensionProtocolsWAI</strong> across open platforms, or start a free
            community space. No forum software to buy, no membership platform to rent — just the moon, the ledger, and
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
            This course runs entirely in your browser and in your life — zero tokens, zero server cost, zero data stored.
            On the platform, The 9 (the Pesedjet) stands ready to help you coordinate any project that grows from it.
          </p>
        </div>
      </section>
    </div>
  );
}
