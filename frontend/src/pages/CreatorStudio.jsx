import { useState, useEffect } from "react";
import { useAuth } from "../lib/auth";
import { Link } from "react-router-dom";
import SovereignVoice from "../components/studio/SovereignVoice";
import CheerleaderOrb from "../components/studio/CheerleaderOrb";
import LyricForge from "../components/studio/chambers/LyricForge";
import PublishingGate from "../components/studio/chambers/PublishingGate";
import { ArrowLeft, Lock } from "lucide-react";

// ─── Chamber definitions ──────────────────────────────────────────────────────
const CHAMBERS = [
  {
    id: "lyric",
    name: "The Lyric Forge",
    glyph: "✍",
    color: "#f59e0b",
    glow: "rgba(245,158,11,0.35)",
    desc: "Write lyrics, hooks, verses, and flows powered by AI.",
    tier: "base",
    col: 1, row: 1,
  },
  {
    id: "visual",
    name: "The Visual Altar",
    glyph: "🎨",
    color: "#a855f7",
    glow: "rgba(168,85,247,0.35)",
    desc: "Cover art concepts, branding kits, moodboard generator.",
    tier: "mid",
    col: 2, row: 1,
  },
  {
    id: "script",
    name: "Script Scriptorium",
    glyph: "📜",
    color: "#06b6d4",
    glow: "rgba(6,182,212,0.35)",
    desc: "Book builder, script generator, story engine, dialogue lab.",
    tier: "mid",
    col: 3, row: 1,
  },
  {
    id: "sound",
    name: "The Sound Lab",
    glyph: "🎛",
    color: "#22c55e",
    glow: "rgba(34,197,94,0.35)",
    desc: "Beat concepts, loop ideas, audio palette mixer.",
    tier: "mid",
    col: 1, row: 2,
  },
  {
    id: "vault",
    name: "Vault of Versions",
    glyph: "🗄",
    color: "#64748b",
    glow: "rgba(100,116,139,0.35)",
    desc: "Version history, asset library, idea archive.",
    tier: "base",
    col: 2, row: 2,
    comingSoon: true,
  },
  {
    id: "publishing",
    name: "The Publishing Gate",
    glyph: "🌐",
    color: "#3b82f6",
    glow: "rgba(59,130,246,0.35)",
    desc: "Metadata generator, social templates, release checklist.",
    tier: "base",
    col: 3, row: 2,
  },
  {
    id: "marketplace",
    name: "Marketplace Forge",
    glyph: "🛒",
    color: "#f97316",
    glow: "rgba(249,115,22,0.35)",
    desc: "Merch builder, course creator, digital product drops.",
    tier: "top",
    col: 1, row: 3,
  },
  {
    id: "collab",
    name: "Collaboration Chamber",
    glyph: "🤝",
    color: "#ec4899",
    glow: "rgba(236,72,153,0.35)",
    desc: "Shared projects, guest creators, persona collaboration.",
    tier: "top",
    col: 2, row: 3,
  },
];

const TIER_RANK = { base: 0, mid: 1, top: 2 };
const USER_TIER = "base"; // TODO: pull from subscription

// ─── Entry Screen ─────────────────────────────────────────────────────────────
function EntryScreen({ onEnter }) {
  const [phase, setPhase] = useState(0); // 0=dark, 1=glyph, 2=text, 3=button

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 400);
    const t2 = setTimeout(() => setPhase(2), 1200);
    const t3 = setTimeout(() => setPhase(3), 2200);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  return (
    <div
      onClick={phase >= 3 ? onEnter : undefined}
      style={{
        position: "fixed", inset: 0, zIndex: 200,
        background: "radial-gradient(ellipse at center, #0d0818 0%, #040408 70%)",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        cursor: phase >= 3 ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      {/* Floating glyphs */}
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none" }}>
        {["✦", "◈", "⬡", "✧", "⟡", "◉", "⬢", "✦"].map((g, i) => (
          <div key={i} style={{
            position: "absolute",
            left: `${10 + i * 12}%`,
            top: `${15 + (i % 3) * 25}%`,
            fontSize: 14 + (i % 3) * 8,
            color: `rgba(184,134,11,${phase >= 1 ? 0.15 + (i % 4) * 0.05 : 0})`,
            transition: `opacity 1.5s ease ${i * 0.15}s`,
            animation: phase >= 1 ? `float${i % 3} ${4 + i}s ease-in-out infinite` : "none",
          }}>{g}</div>
        ))}
      </div>

      {/* Central glyph */}
      <div style={{
        fontSize: 72,
        opacity: phase >= 1 ? 1 : 0,
        transition: "opacity 0.8s ease",
        filter: phase >= 1 ? "drop-shadow(0 0 30px rgba(184,134,11,0.6))" : "none",
        marginBottom: 32,
        animation: phase >= 1 ? "pulseGlow 3s ease-in-out infinite" : "none",
      }}>
        ⬡
      </div>

      <div style={{
        textAlign: "center",
        opacity: phase >= 2 ? 1 : 0,
        transform: phase >= 2 ? "translateY(0)" : "translateY(20px)",
        transition: "all 0.8s ease",
      }}>
        <div style={{ fontFamily: "monospace", fontSize: 11, letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(184,134,11,0.7)", marginBottom: 16 }}>
          WAI INSTITUTE
        </div>
        <h1 style={{
          fontFamily: "Georgia, serif",
          fontSize: "clamp(2rem, 5vw, 3.5rem)",
          fontWeight: 900,
          color: "#ffd700",
          textShadow: "0 0 40px rgba(255,215,0,0.4), 0 0 80px rgba(255,215,0,0.2)",
          lineHeight: 1.1,
          letterSpacing: "0.03em",
          margin: 0,
        }}>
          The Creator's<br />Sanctuary
        </h1>
        <p style={{
          color: "rgba(255,255,255,0.5)",
          marginTop: 16,
          fontSize: 14,
          letterSpacing: "0.05em",
          fontStyle: "italic",
        }}>
          A sacred chamber of learning, invention, and creation.
        </p>
      </div>

      {phase >= 3 && (
        <button
          onClick={onEnter}
          style={{
            marginTop: 48,
            background: "transparent",
            border: "1px solid rgba(184,134,11,0.5)",
            color: "#ffd700",
            padding: "12px 40px",
            fontFamily: "monospace",
            fontWeight: 900,
            fontSize: 13,
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            cursor: "pointer",
            animation: "entryPulse 2s ease-in-out infinite",
            opacity: 1,
          }}
        >
          Enter the Sanctuary
        </button>
      )}

      <style>{`
        @keyframes float0 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-12px) rotate(5deg)} }
        @keyframes float1 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-18px) rotate(-3deg)} }
        @keyframes float2 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-8px) rotate(8deg)} }
        @keyframes pulseGlow { 0%,100%{filter:drop-shadow(0 0 20px rgba(184,134,11,0.5))} 50%{filter:drop-shadow(0 0 40px rgba(184,134,11,0.9))} }
        @keyframes entryPulse { 0%,100%{box-shadow:0 0 0 0 rgba(184,134,11,0)} 50%{box-shadow:0 0 20px 4px rgba(184,134,11,0.3)} }
      `}</style>
    </div>
  );
}

// ─── Chamber Card ─────────────────────────────────────────────────────────────
function ChamberCard({ chamber, active, locked, onClick }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={locked ? undefined : onClick}
      onMouseEnter={() => !locked && setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: "relative",
        padding: "20px 18px",
        border: `1px solid ${active ? chamber.color : locked ? "rgba(255,255,255,0.06)" : hovered ? `${chamber.color}60` : "rgba(255,255,255,0.08)"}`,
        background: active
          ? `radial-gradient(ellipse at top left, ${chamber.glow}, rgba(0,0,0,0.6))`
          : locked
          ? "rgba(255,255,255,0.01)"
          : hovered
          ? `rgba(0,0,0,0.5)`
          : "rgba(255,255,255,0.02)",
        cursor: locked ? "default" : "pointer",
        transition: "all 0.25s ease",
        boxShadow: active ? `0 0 30px ${chamber.glow}, inset 0 0 20px ${chamber.glow}` : hovered ? `0 0 15px ${chamber.glow}` : "none",
        filter: locked ? "grayscale(0.8) opacity(0.4)" : "none",
        minHeight: 110,
      }}
    >
      {locked && (
        <Lock style={{ position: "absolute", top: 10, right: 10, width: 14, height: 14, color: "rgba(255,255,255,0.2)" }} />
      )}
      {active && (
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${chamber.color}, transparent)` }} />
      )}
      <div style={{ fontSize: 28, marginBottom: 8, filter: active ? `drop-shadow(0 0 8px ${chamber.color})` : "none" }}>{chamber.glyph}</div>
      <div style={{ fontSize: 13, fontWeight: 900, color: active ? chamber.color : locked ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.85)", lineHeight: 1.2, marginBottom: 6 }}>
        {chamber.name}
      </div>
      <div style={{ fontSize: 11, color: locked ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.45)", lineHeight: 1.5 }}>
        {locked ? `Unlock with ${chamber.tier} tier` : chamber.comingSoon ? "Coming soon" : chamber.desc}
      </div>
      {active && (
        <div style={{ position: "absolute", bottom: 8, right: 10, fontSize: 9, fontFamily: "monospace", color: chamber.color, letterSpacing: "0.1em" }}>ACTIVE ▶</div>
      )}
    </div>
  );
}

// ─── Main Studio ─────────────────────────────────────────────────────────────
export default function CreatorStudio() {
  const { user } = useAuth();
  const [entered, setEntered] = useState(false);
  const [activeChamber, setActiveChamber] = useState(null);

  const userTierRank = TIER_RANK[USER_TIER] ?? 0;

  const openChamber = (chamber) => {
    if (chamber.comingSoon) return;
    setActiveChamber(prev => prev?.id === chamber.id ? null : chamber);
  };

  return (
    <>
      {/* Entry screen */}
      {!entered && <EntryScreen onEnter={() => setEntered(true)} />}

      {/* Sovereign voice sidebar */}
      {entered && <SovereignVoice activeChamber={activeChamber?.id} />}

      {/* Main studio */}
      <div style={{
        minHeight: "100vh",
        background: "radial-gradient(ellipse at top, #0d0818 0%, #040408 60%)",
        paddingLeft: entered ? 300 : 0,
        transition: "padding-left 0.3s ease",
        opacity: entered ? 1 : 0,
        transition: "opacity 0.6s ease, padding-left 0.3s ease",
      }}>
        {/* Top bar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 28px", borderBottom: "1px solid rgba(184,134,11,0.12)", background: "rgba(0,0,0,0.3)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Link to="/dashboard" style={{ color: "rgba(255,255,255,0.4)", textDecoration: "none", display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontFamily: "monospace", letterSpacing: "0.05em" }}>
              <ArrowLeft style={{ width: 14, height: 14 }} /> Exit Sanctuary
            </Link>
            <div style={{ width: 1, height: 16, background: "rgba(255,255,255,0.1)" }} />
            <div style={{ fontSize: 11, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", color: "rgba(184,134,11,0.7)" }}>
              The Creator's Sanctuary
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {activeChamber && (
              <div style={{ fontSize: 11, fontFamily: "monospace", color: activeChamber.color, letterSpacing: "0.08em" }}>
                {activeChamber.glyph} {activeChamber.name}
              </div>
            )}
            <div style={{ fontSize: 11, fontFamily: "monospace", color: "rgba(255,255,255,0.3)", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", padding: "3px 10px", borderRadius: 20 }}>
              {USER_TIER.toUpperCase()} TIER
            </div>
          </div>
        </div>

        <div style={{ padding: "28px 28px 80px" }}>
          {/* Chamber map */}
          <div style={{ marginBottom: activeChamber ? 24 : 0 }}>
            <div style={{ fontSize: 10, fontFamily: "monospace", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(184,134,11,0.5)", marginBottom: 14 }}>
              ◈ The Sacred Map — Select a Chamber
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, maxWidth: 900 }}>
              {CHAMBERS.map(chamber => {
                const locked = TIER_RANK[chamber.tier] > userTierRank;
                return (
                  <ChamberCard
                    key={chamber.id}
                    chamber={chamber}
                    active={activeChamber?.id === chamber.id}
                    locked={locked}
                    onClick={() => openChamber(chamber)}
                  />
                );
              })}
            </div>
          </div>

          {/* Active chamber workspace */}
          {activeChamber && !activeChamber.comingSoon && (
            <div style={{
              marginTop: 24,
              background: "rgba(0,0,0,0.4)",
              border: `1px solid ${activeChamber.color}40`,
              boxShadow: `0 0 40px ${activeChamber.glow}`,
            }}>
              {/* Chamber header */}
              <div style={{
                padding: "16px 24px",
                borderBottom: `1px solid ${activeChamber.color}25`,
                background: `linear-gradient(135deg, ${activeChamber.glow}, transparent)`,
                display: "flex", alignItems: "center", gap: 12,
              }}>
                <div style={{ fontSize: 24, filter: `drop-shadow(0 0 8px ${activeChamber.color})` }}>{activeChamber.glyph}</div>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 900, color: activeChamber.color }}>{activeChamber.name}</div>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", marginTop: 2 }}>{activeChamber.desc}</div>
                </div>
                <button
                  onClick={() => setActiveChamber(null)}
                  style={{ marginLeft: "auto", background: "none", border: "none", color: "rgba(255,255,255,0.3)", cursor: "pointer", fontSize: 18, lineHeight: 1 }}
                >×</button>
              </div>

              {/* Chamber content */}
              <div style={{ padding: 24 }}>
                {activeChamber.id === "lyric" && <LyricForge tier={USER_TIER} />}
                {activeChamber.id === "publishing" && <PublishingGate tier={USER_TIER} />}
              </div>
            </div>
          )}

          {/* Tier upgrade prompt */}
          {!activeChamber && (
            <div style={{ marginTop: 32, padding: "20px 24px", border: "1px solid rgba(184,134,11,0.15)", background: "rgba(184,134,11,0.03)", maxWidth: 900 }}>
              <div style={{ fontSize: 10, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", color: "rgba(184,134,11,0.6)", marginBottom: 8 }}>
                Unlock More Chambers
              </div>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                {[
                  { tier: "mid", label: "Mid Tier", desc: "Visual Altar, Script Scriptorium, Sound Lab", color: "#a855f7" },
                  { tier: "top", label: "Top Tier", desc: "Marketplace Forge, Collaboration Chamber + everything", color: "#f97316" },
                ].map(({ tier, label, desc, color }) => (
                  <div key={tier} style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ fontSize: 13, fontWeight: 900, color, marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", marginBottom: 10, lineHeight: 1.5 }}>{desc}</div>
                    <Link to="/subscribe" style={{ fontSize: 11, fontFamily: "monospace", fontWeight: 700, color, border: `1px solid ${color}50`, padding: "5px 14px", textDecoration: "none", letterSpacing: "0.05em" }}>
                      UPGRADE →
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Cheerleader orb */}
      {entered && <CheerleaderOrb chamber={activeChamber?.id} />}

      <style>{`
        @keyframes float0 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        @keyframes float1 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-16px)} }
        @keyframes float2 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
      `}</style>
    </>
  );
}
