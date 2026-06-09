import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../lib/auth";
import { Link } from "react-router-dom";
import SovereignVoice from "../components/studio/SovereignVoice";
import CheerleaderOrb from "../components/studio/CheerleaderOrb";
import CreativeTimeline from "../components/studio/CreativeTimeline";
import CreativeStats from "../components/studio/CreativeStats";
import ProjectRitual from "../components/studio/ProjectRitual";
import CustomizationPanel from "../components/studio/CustomizationPanel";
import { useStudioTheme } from "../components/studio/CustomizationPanel";
import { studioSound } from "../components/studio/SoundSystem";
import LyricForge from "../components/studio/chambers/LyricForge";
import PublishingGate from "../components/studio/chambers/PublishingGate";
import VisualAltar from "../components/studio/chambers/VisualAltar";
import ScriptScriptorium from "../components/studio/chambers/ScriptScriptorium";
import SoundLab from "../components/studio/chambers/SoundLab";
import VaultOfVersions from "../components/studio/chambers/VaultOfVersions";
import { ArrowLeft, Lock, Palette } from "lucide-react";

// ─── Chamber definitions ──────────────────────────────────────────────────────
const CHAMBERS = [
  { id: 'lyric-forge',      name: 'Lyric Forge',            glyph: '♪',  color: '#ffd700', glow: 'rgba(255,215,0,0.3)',    desc: 'Write lyrics, hooks, verses, and flows powered by AI.', tier: 'base' },
  { id: 'visual-altar',     name: 'Visual Altar',           glyph: '◉',  color: '#c084fc', glow: 'rgba(192,132,252,0.3)',  desc: 'Cover art concepts, branding kits, moodboard generator.', tier: 'base' },
  { id: 'script',           name: 'Script Scriptorium',     glyph: '✦',  color: '#67e8f9', glow: 'rgba(103,232,249,0.3)',  desc: 'Book builder, script generator, story engine, dialogue lab.', tier: 'base' },
  { id: 'sound-lab',        name: 'Sound Lab',              glyph: '⟁',  color: '#34d399', glow: 'rgba(52,211,153,0.3)',   desc: 'Beat concepts, loop ideas, audio palette mixer.', tier: 'mid' },
  { id: 'vault',            name: 'Vault of Versions',      glyph: '⌬',  color: '#f87171', glow: 'rgba(248,113,113,0.3)',  desc: 'Version history, asset library, idea archive.', tier: 'mid' },
  { id: 'publishing-gate',  name: 'Publishing Gate',        glyph: '⬡',  color: '#fbbf24', glow: 'rgba(251,191,36,0.3)',   desc: 'Metadata generator, social templates, release checklist.', tier: 'base' },
  { id: 'marketplace',      name: 'Marketplace Forge',      glyph: '⊕',  color: '#fb923c', glow: 'rgba(251,146,60,0.3)',   desc: 'Merch builder, course creator, digital product drops.', tier: 'top', comingSoon: true },
  { id: 'collaboration',    name: 'Collaboration Chamber',  glyph: '⊞',  color: '#a78bfa', glow: 'rgba(167,139,250,0.3)',  desc: 'Shared projects, guest creators, persona collaboration.', tier: 'top', comingSoon: true },
];

const TIER_RANK = { base: 0, mid: 1, top: 2 };
const USER_TIER = "mid"; // TODO: pull from subscription

// ─── Entry Screen ─────────────────────────────────────────────────────────────
function EntryScreen({ onEnter }) {
  const [phase, setPhase] = useState(0); // 0=black, 1=glyphs, 2=map illuminates, 3=cheerleader welcome, 4=button

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 400);
    const t2 = setTimeout(() => setPhase(2), 1200);
    const t3 = setTimeout(() => {
      setPhase(3);
      studioSound.play('chamber_enter');
    }, 2200);
    const t4 = setTimeout(() => setPhase(4), 3200);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, []);

  return (
    <div
      onClick={phase >= 4 ? onEnter : undefined}
      style={{
        position: "fixed", inset: 0, zIndex: 200,
        background: "radial-gradient(ellipse at center, #0d0818 0%, #040408 70%)",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        cursor: phase >= 4 ? "pointer" : "default",
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
          color: "rgba(255,255,255,0.65)",
          marginTop: 16,
          fontSize: 14,
          letterSpacing: "0.05em",
          fontStyle: "italic",
          maxWidth: 440,
          lineHeight: 1.6,
        }}>
          You are stepping into the Creator's Sanctuary — a sacred chamber of invention, learning, and mastery. Your mission begins here.
        </p>
      </div>

      {/* Phase 3 — Cheerleader welcome message */}
      {phase >= 3 && (
        <div style={{
          marginTop: 24,
          background: "rgba(10,10,20,0.9)",
          border: "1px solid rgba(255,215,0,0.3)",
          borderRadius: 10,
          padding: "12px 20px",
          maxWidth: 360,
          fontSize: 13,
          color: "rgba(255,255,255,0.9)",
          textAlign: "center",
          lineHeight: 1.6,
          animation: "fadeInUp 0.5s ease",
          boxShadow: "0 0 20px rgba(255,215,0,0.1)",
        }}>
          ✦ Welcome, Creator. The Sanctuary is open. Where shall we begin?
        </div>
      )}

      {phase >= 4 && (
        <button
          onClick={onEnter}
          style={{
            marginTop: 32,
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
        @keyframes fadeInUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
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
          : locked ? "rgba(255,255,255,0.01)"
          : hovered ? "rgba(0,0,0,0.5)"
          : "rgba(255,255,255,0.02)",
        cursor: locked ? "default" : "pointer",
        transition: "all 0.25s ease",
        boxShadow: active ? `0 0 30px ${chamber.glow}, inset 0 0 20px ${chamber.glow}` : hovered ? `0 0 15px ${chamber.glow}` : "none",
        filter: locked ? "grayscale(0.8) opacity(0.4)" : "none",
        minHeight: 110,
      }}
    >
      {locked && <Lock style={{ position: "absolute", top: 10, right: 10, width: 14, height: 14, color: "rgba(255,255,255,0.2)" }} />}
      {active && <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${chamber.color}, transparent)` }} />}
      <div style={{ fontSize: 28, marginBottom: 8, filter: active ? `drop-shadow(0 0 8px ${chamber.color})` : "none" }}>{chamber.glyph}</div>
      <div style={{ fontSize: 13, fontWeight: 900, color: active ? chamber.color : locked ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.85)", lineHeight: 1.2, marginBottom: 6 }}>
        {chamber.name}
      </div>
      <div style={{ fontSize: 11, color: locked ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.45)", lineHeight: 1.5 }}>
        {locked ? `Unlock with ${chamber.tier} tier` : chamber.comingSoon ? "Coming soon" : chamber.desc}
      </div>
      {active && <div style={{ position: "absolute", bottom: 8, right: 10, fontSize: 9, fontFamily: "monospace", color: chamber.color, letterSpacing: "0.1em" }}>ACTIVE ▶</div>}
    </div>
  );
}

// ─── Ritual Save Overlay ──────────────────────────────────────────────────────
function RitualSaveOverlay({ onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 1500);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 400,
      background: "rgba(0,0,0,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center",
      animation: "rsOverlayIn 0.3s ease",
    }}>
      <div style={{ textAlign: "center" }}>
        <div style={{
          fontSize: 64,
          animation: "rsSigilPulse 0.6s ease-in-out infinite",
          filter: "drop-shadow(0 0 30px rgba(255,215,0,0.9))",
          marginBottom: 20,
        }}>⬡</div>
        <div style={{
          fontFamily: "monospace", fontSize: 14, letterSpacing: "0.25em",
          textTransform: "uppercase", color: "#ffd700",
          textShadow: "0 0 20px rgba(255,215,0,0.5)",
        }}>
          Your work is sealed.
        </div>
      </div>
      <style>{`
        @keyframes rsOverlayIn { from{opacity:0} to{opacity:1} }
        @keyframes rsSigilPulse { 0%,100%{transform:scale(1) rotate(0deg)} 50%{transform:scale(1.1) rotate(10deg)} }
      `}</style>
    </div>
  );
}

// ─── Main Studio ─────────────────────────────────────────────────────────────
export default function CreatorStudio() {
  const { user } = useAuth();
  const { theme, colors } = useStudioTheme();

  const [entered, setEntered] = useState(false);
  const [activeChamber, setActiveChamber] = useState(null);
  const [activeStage, setActiveStage] = useState(0);
  const [chamberHistory, setChamberHistory] = useState([]);

  // Projects state persisted to localStorage
  const [projects, setProjects] = useState(() => {
    try { return JSON.parse(localStorage.getItem('studio_projects') || '[]'); } catch { return []; }
  });
  const [activeProject, setActiveProject] = useState(null);

  // Sessions (track time spent)
  const sessionStartRef = useRef(Date.now());
  const [sessions, setSessions] = useState(() => {
    try { return JSON.parse(localStorage.getItem('studio_sessions') || '[]'); } catch { return []; }
  });

  // UI state
  const [showProjectRitual, setShowProjectRitual] = useState(false);
  const [showCustomization, setShowCustomization] = useState(false);
  const [showRitualSave, setShowRitualSave] = useState(false);

  const userTierRank = TIER_RANK[USER_TIER] ?? 0;

  // Save session on unmount
  useEffect(() => {
    return () => {
      const session = { start: sessionStartRef.current, end: Date.now(), chambers: chamberHistory };
      const updated = [...sessions, session];
      try { localStorage.setItem('studio_sessions', JSON.stringify(updated)); } catch {}
    };
  }, []); // eslint-disable-line

  const saveProjects = useCallback((updated) => {
    try { localStorage.setItem('studio_projects', JSON.stringify(updated)); } catch {}
    setProjects(updated);
  }, []);

  const openChamber = useCallback((chamber) => {
    if (chamber.comingSoon) return;
    setActiveChamber(prev => {
      if (prev?.id === chamber.id) return null;
      studioSound.play('chamber_enter');
      setChamberHistory(h => h.includes(chamber.id) ? h : [...h, chamber.id]);
      return chamber;
    });
  }, []);

  const handleChamberJump = useCallback((chamberRoute) => {
    if (chamberRoute === '/studio') {
      setActiveChamber(null);
      return;
    }
    const found = CHAMBERS.find(c => c.id === chamberRoute);
    if (found) openChamber(found);
  }, [openChamber]);

  const handleSave = useCallback(() => {
    studioSound.play('save_ritual');
    saveProjects(projects);
    setShowRitualSave(true);
  }, [projects, saveProjects]);

  const handleProjectCreated = useCallback((project) => {
    const updated = [...projects, { ...project, status: 'draft', createdAt: Date.now() }];
    saveProjects(updated);
    setActiveProject(project);
    setShowProjectRitual(false);
  }, [projects, saveProjects]);

  return (
    <>
      {/* Entry screen */}
      {!entered && <EntryScreen onEnter={() => setEntered(true)} />}

      {/* Sovereign voice sidebar */}
      {entered && <SovereignVoice activeChamber={activeChamber?.id} />}

      {/* Creative Stats panel — sits between SovereignVoice and main */}
      {entered && (
        <div style={{ position: "fixed", left: 280, top: 0, bottom: 0, zIndex: 45, pointerEvents: "none" }}>
          <div style={{ pointerEvents: "all" }}>
            <CreativeStats projects={projects} sessions={sessions} />
          </div>
        </div>
      )}

      {/* Main studio */}
      <div style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at top, ${colors.bg} 0%, #040408 60%)`,
        paddingLeft: entered ? 300 : 0,
        paddingBottom: 56,
        opacity: entered ? 1 : 0,
        transition: "opacity 0.6s ease, padding-left 0.3s ease, background 0.5s ease",
      }}>
        {/* Top bar */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "16px 28px",
          borderBottom: `1px solid ${colors.primary}20`,
          background: "rgba(0,0,0,0.35)",
          position: "sticky", top: 0, zIndex: 20,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Link to="/dashboard" style={{ color: "rgba(255,255,255,0.4)", textDecoration: "none", display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontFamily: "monospace", letterSpacing: "0.05em" }}>
              <ArrowLeft style={{ width: 14, height: 14 }} /> Exit Sanctuary
            </Link>
            <div style={{ width: 1, height: 16, background: "rgba(255,255,255,0.1)" }} />
            <div style={{ fontSize: 11, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", color: `${colors.primary}b3` }}>
              The Creator's Sanctuary
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {activeChamber && (
              <div style={{ fontSize: 11, fontFamily: "monospace", color: activeChamber.color, letterSpacing: "0.08em" }}>
                {activeChamber.glyph} {activeChamber.name}
              </div>
            )}

            {/* New Project button */}
            <button
              onClick={() => setShowProjectRitual(true)}
              style={{
                background: `${colors.primary}18`,
                border: `1px solid ${colors.primary}50`,
                color: colors.primary,
                padding: "6px 14px",
                fontFamily: "monospace", fontSize: 11,
                fontWeight: 700, letterSpacing: "0.1em",
                cursor: "pointer",
                display: "flex", alignItems: "center", gap: 6,
                transition: "all 0.2s ease",
              }}
            >
              ⊕ New Project
            </button>

            {/* Palette / Customization */}
            <button
              onClick={() => setShowCustomization(true)}
              title="Customize Sanctuary"
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.5)",
                padding: "6px 10px",
                cursor: "pointer",
                display: "flex", alignItems: "center",
              }}
            >
              <Palette style={{ width: 14, height: 14 }} />
            </button>

            {/* Save */}
            <button
              onClick={handleSave}
              style={{
                background: `linear-gradient(135deg, ${colors.primary}cc, ${colors.primary})`,
                border: "none",
                color: "#050508",
                padding: "6px 16px",
                fontFamily: "monospace", fontSize: 11,
                fontWeight: 900, letterSpacing: "0.12em",
                textTransform: "uppercase",
                cursor: "pointer",
                boxShadow: `0 3px 0 ${colors.glow}`,
              }}
            >
              SAVE
            </button>

            <div style={{ fontSize: 11, fontFamily: "monospace", color: "rgba(255,255,255,0.3)", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", padding: "3px 10px", borderRadius: 20 }}>
              {USER_TIER.toUpperCase()} TIER
            </div>
          </div>
        </div>

        {/* Active project indicator */}
        {activeProject && (
          <div style={{
            padding: "8px 28px",
            background: `${colors.primary}0d`,
            borderBottom: `1px solid ${colors.primary}15`,
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <span style={{ fontSize: 16 }}>{activeProject.glyph}</span>
            <span style={{ fontSize: 12, fontFamily: "monospace", color: `${colors.primary}cc` }}>
              {activeProject.name}
            </span>
            <button
              onClick={() => setActiveProject(null)}
              style={{ background: "none", border: "none", color: "rgba(255,255,255,0.25)", cursor: "pointer", fontSize: 14, marginLeft: 4 }}
            >×</button>
          </div>
        )}

        <div style={{ padding: "28px 28px 20px" }}>
          {/* Chamber map */}
          <div style={{ marginBottom: activeChamber ? 24 : 0 }}>
            <div style={{ fontSize: 10, fontFamily: "monospace", letterSpacing: "0.2em", textTransform: "uppercase", color: `${colors.primary}80`, marginBottom: 14 }}>
              ◈ The Sacred Map — Select a Chamber
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, maxWidth: 900 }}>
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
                {activeChamber.id === 'lyric-forge'   && <LyricForge tier={USER_TIER} />}
                {activeChamber.id === 'visual-altar'  && <VisualAltar tier={USER_TIER} />}
                {activeChamber.id === 'script'        && <ScriptScriptorium tier={USER_TIER} />}
                {activeChamber.id === 'sound-lab'     && <SoundLab tier={USER_TIER} />}
                {activeChamber.id === 'vault'         && <VaultOfVersions projects={projects} />}
                {activeChamber.id === 'publishing-gate' && <PublishingGate tier={USER_TIER} />}
              </div>
            </div>
          )}

          {/* Tier upgrade prompt */}
          {!activeChamber && (
            <div style={{ marginTop: 32, padding: "20px 24px", border: `1px solid ${colors.primary}25`, background: `${colors.primary}05`, maxWidth: 900 }}>
              <div style={{ fontSize: 10, fontFamily: "monospace", letterSpacing: "0.15em", textTransform: "uppercase", color: `${colors.primary}99`, marginBottom: 8 }}>
                Unlock More Chambers
              </div>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                {[
                  { tier: "mid", label: "Mid Tier", desc: "Sound Lab, Vault of Versions + more tools", color: "#a855f7" },
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

      {/* Creative Timeline (fixed bottom) */}
      {entered && (
        <CreativeTimeline
          activeStage={activeStage}
          onStageClick={setActiveStage}
          onChamberJump={handleChamberJump}
        />
      )}

      {/* Cheerleader orb */}
      {entered && <CheerleaderOrb chamber={activeChamber?.id} />}

      {/* Project Ritual modal */}
      {showProjectRitual && (
        <ProjectRitual
          onCreated={handleProjectCreated}
          onClose={() => setShowProjectRitual(false)}
        />
      )}

      {/* Customization panel modal */}
      {showCustomization && (
        <CustomizationPanel onClose={() => setShowCustomization(false)} />
      )}

      {/* Ritual save overlay */}
      {showRitualSave && (
        <RitualSaveOverlay onDone={() => setShowRitualSave(false)} />
      )}

      <style>{`
        @keyframes float0 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        @keyframes float1 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-16px)} }
        @keyframes float2 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
      `}</style>
    </>
  );
}
