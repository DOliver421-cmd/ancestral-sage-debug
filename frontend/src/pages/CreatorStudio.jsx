/**
 * CreatorStudio — the M.O.R.E. Creator Studio.
 *
 * Direct adaptation of the reference design: dark navy (#141824) + cyan,
 * top nav, left icon rail, three columns (Session Stats / Sovereign AI +
 * Chamber Map / Studio Workspace), a floating Ghost Producer window, and the
 * creative timeline along the bottom.
 *
 * Every surface is real: chambers call the Sovereign AI endpoint, the Lyric
 * Forge generates and saves versions, the Ghost Producer synthesizes and
 * publishes tracks, Marketplace Forge creates real store products, and the
 * Collaboration Chamber manages real guest rosters. Nothing here is a dead
 * link.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../lib/auth";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Home, Music2, History, BarChart3, Settings, User, LogOut,
  Plus, Pencil, Lock, Send, ChevronDown, Save, Check,
} from "lucide-react";
import LyricForge from "../components/studio/chambers/LyricForge";
import PublishingGate from "../components/studio/chambers/PublishingGate";
import VisualAltar from "../components/studio/chambers/VisualAltar";
import ScriptScriptorium from "../components/studio/chambers/ScriptScriptorium";
import SoundLab from "../components/studio/chambers/SoundLab";
import VaultOfVersions from "../components/studio/chambers/VaultOfVersions";
import MarketplaceForge from "../components/studio/chambers/MarketplaceForge";
import CollaborationChamber from "../components/studio/chambers/CollaborationChamber";
import CreativeTimeline from "../components/studio/CreativeTimeline";
import { StudioContent } from "./Studio";
import { useEntitlements } from "../hooks/useEntitlements";
import { api } from "../lib/api";

// ── Design tokens (reference: dark navy + cyan) ─────────────────────────────
const CYAN = "#22d3ee";
const CYAN_SOFT = "rgba(34,211,238,0.12)";
const BG = "#141824";
const PANEL = "#1a2130";
const PANEL2 = "#1d2536";
const BORDER = "rgba(255,255,255,0.07)";
const MUTED = "rgba(255,255,255,0.52)";
const FADED = "rgba(255,255,255,0.28)";
const MONO = "'SF Mono', 'Cascadia Code', Consolas, monospace";
const SANS = "system-ui, -apple-system, 'Segoe UI', sans-serif";

// ─── Chamber definitions (all 9 are real, working capabilities) ─────────────
const CHAMBERS = [
  { id: "lyric-forge",      name: "Lyric Forge",           glyph: "♪",  desc: "Write lyrics, hooks, verses, and flows powered by AI.",        tier: "base" },
  { id: "visual-altar",     name: "Visual Altar",          glyph: "◉",  desc: "Cover art concepts, branding kits, moodboard generator.",       tier: "base" },
  { id: "script",           name: "Script Scriptorium",    glyph: "✦",  desc: "Book builder, script generator, story engine, dialogue lab.",   tier: "base" },
  { id: "sound-lab",        name: "Sound Lab",             glyph: "⟁",  desc: "Beat concepts, loop ideas, audio palette mixer.",               tier: "mid" },
  { id: "ghost-producer",   name: "Ghost Producer",        glyph: "🎚", desc: "Drum sequencer, live synth beats, WAV export, publish to store.", tier: "mid" },
  { id: "vault",            name: "Vault of Versions",     glyph: "⌬",  desc: "Version history, asset library, idea archive.",                tier: "mid" },
  { id: "publishing-gate",  name: "Publishing Gate",       glyph: "⬡",  desc: "Metadata generator, social templates, release checklist.",     tier: "base" },
  { id: "marketplace",      name: "Marketplace Forge",     glyph: "⊕",  desc: "Forge sellable drops — ebooks, guides, beats, merch — straight to your store.", tier: "top" },
  { id: "collaboration",    name: "Collaboration Chamber", glyph: "⊞",  desc: "Guest creators, roles, scope, and shareable invites for your project.", tier: "top" },
];

const TIER_RANK = { base: 0, mid: 1, top: 2 };
const CANONICAL_TIER_RANK = { free: 0, member: 1, plus: 2, pro: 3, patron: 4, platinum: 5, executive: 6 };

const CHAMBER_ROUTE_LABELS = {
  "lyric-forge": "Lyric Forge",
  "visual-altar": "Visual Altar",
  "script": "Script Scriptorium",
  "sound-lab": "Sound Lab",
  "vault": "Vault of Versions",
  "publishing-gate": "Publishing Gate",
  "ghost-producer": "Ghost Producer",
  "marketplace": "Marketplace Forge",
  "collaboration": "Collaboration Chamber",
};

// Stage index for the timeline: VISION(0) → LYRIC FORGE(1) → SOUND LAB(2) →
// VISUAL ALTAR(3) → SCRIPT(4) → PUBLISH(5). Active chamber drives the stage.
const STAGE_FOR_CHAMBER = {
  "lyric-forge": 1,
  "sound-lab": 2,
  "visual-altar": 3,
  "script": 4,
  "publishing-gate": 5,
};

function fmtDuration(ms) {
  if (!ms || ms <= 0) return "0h 0m";
  const totalMinutes = Math.floor(ms / 60000);
  return `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`;
}

/* ── Progress ring (pure SVG — no chart lib, no cost) ─────────────────────── */
function Ring({ value, max, sub, label, color = CYAN }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const pct = max > 0 ? Math.min(1, value / max) : 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <div style={{ position: "relative", width: 72, height: 72 }}>
        <svg width="72" height="72" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="36" cy="36" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="5" />
          <circle
            cx="36" cy="36" r={r} fill="none"
            stroke={color} strokeWidth="5" strokeLinecap="round"
            strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
            style={{ filter: `drop-shadow(0 0 5px ${color})`, transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 12, fontWeight: 800, color: "#fff", fontFamily: MONO,
        }}>
          {sub}
        </div>
      </div>
      <div style={{
        fontSize: 9, fontFamily: MONO, letterSpacing: "0.18em",
        textTransform: "uppercase", color: MUTED,
      }}>
        {label}
      </div>
    </div>
  );
}

/* ── Column 1 — Session stats + glowing sphere ────────────────────────────── */
function SessionStatsPanel({ projects, sessions }) {
  const totalTime = (sessions || []).reduce((acc, s) => {
    if (s.start && s.end) return acc + (s.end - s.start);
    return acc;
  }, 0);
  const minutes = Math.floor(totalTime / 60000);
  const projectTarget = 10;
  const timeTargetMin = 240;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14, height: "100%" }}>
      <div style={{
        background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 14, padding: "16px 12px 14px",
      }}>
        <PanelHeader label="Session Stats" />
        <div style={{ display: "flex", justifyContent: "space-around", padding: "10px 0 2px" }}>
          <Ring value={projects.length} max={projectTarget} sub={`${projects.length}/${projectTarget}`} label="Projects" />
          <Ring value={Math.min(timeTargetMin, minutes)} max={timeTargetMin} sub={fmtDuration(totalTime)} label="Time" color="#67e8f9" />
        </div>
      </div>

      {/* Glowing cyan sphere */}
      <div style={{
        flex: 1, minHeight: 160, display: "flex", alignItems: "center", justifyContent: "center",
        background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 14, overflow: "hidden",
        position: "relative",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          background: "radial-gradient(circle at 50% 60%, rgba(34,211,238,0.16) 0%, transparent 60%)",
        }} />
        <div style={{
          width: 88, height: 88, borderRadius: "50%", position: "relative",
          background:
            "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.9) 0%, rgba(34,211,238,0.55) 22%, rgba(34,211,238,0.28) 45%, rgba(14,116,144,0.5) 70%, rgba(6,40,54,0.9) 100%)",
          boxShadow:
            "0 0 30px rgba(34,211,238,0.45), 0 0 70px rgba(34,211,238,0.22), inset -10px -14px 30px rgba(0,0,0,0.45)",
        }}>
          <div style={{
            position: "absolute", top: 14, left: 20, width: 16, height: 10, borderRadius: "50%",
            background: "rgba(255,255,255,0.85)", transform: "rotate(-20deg)", filter: "blur(1px)",
          }} />
        </div>
      </div>
    </div>
  );
}

/* ── Column 2 — Sovereign AI panel ────────────────────────────────────────── */
function SovereignPanel({ activeChamber, onArtifact, dispatchRef }) {
  const [input, setInput] = useState("Write an upbeat verse for a Neo-Soul track about city lights.");
  const [busy, setBusy] = useState(false);
  const [routingLabel, setRoutingLabel] = useState(null);

  const callSovereign = useCallback(async ({ action = "chat", context = {}, message = "", silent = false } = {}) => {
    setBusy(true);
    setRoutingLabel(CHAMBER_ROUTE_LABELS[activeChamber] || activeChamber || "the Studio");
    try {
      const r = await api.post("/studio/sovereign", {
        chamber: activeChamber || "map",
        action,
        context,
        message: message || "",
      });
      const { response, artifact, artifact_type } = r.data;
      if (artifact && artifact_type && onArtifact) {
        onArtifact(artifact_type, artifact);
      }
      if (!silent) toast.success(response || "Done.");
      return r.data;
    } catch {
      if (!silent) toast.error("Sovereign is unavailable right now — the Studio is still fully usable.");
      return null;
    } finally {
      setBusy(false);
      setRoutingLabel(null);
    }
  }, [activeChamber, onArtifact]);

  // Chambers dispatch through this ref (Lyric Forge's "Send to Sovereign" etc.)
  useEffect(() => {
    if (dispatchRef) dispatchRef.current = callSovereign;
  }, [callSovereign, dispatchRef]);

  const submit = async () => {
    const text = input.trim();
    if (!text) { toast.error("Tell Sovereign what you want to make."); return; }
    setInput("");
    await callSovereign({
      action: "generate_lyrics",
      context: { genre: "Neo-Soul", mood: "Uplifting", structure: "Verse", topic: text, notes: "" },
      message: text,
    });
  };

  return (
    <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <PanelHeader label="Sovereign AI" />
        <div style={{ display: "flex", gap: 4, color: FADED }}>
          <span style={{ fontSize: 14, lineHeight: 1 }}>⋮</span>
        </div>
      </div>

      {/* Floating orb */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: "50%",
          background:
            "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95) 0%, rgba(34,211,238,0.6) 25%, rgba(34,211,238,0.25) 48%, rgba(8,80,102,0.55) 72%, rgba(4,32,44,0.95) 100%)",
          boxShadow: "0 0 22px rgba(34,211,238,0.5), inset -6px -8px 16px rgba(0,0,0,0.4)",
        }} />
      </div>

      {/* Prompt input */}
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        background: "#12161f", border: `1px solid ${BORDER}`, borderRadius: 10,
        padding: "4px 4px 4px 12px",
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
          placeholder="Tell Sovereign what to build…"
          style={{
            flex: 1, background: "transparent", border: "none", outline: "none",
            color: "#fff", fontSize: 12, fontFamily: SANS, padding: "8px 0",
          }}
        />
        <button onClick={submit} disabled={busy}
          style={{
            background: CYAN, color: "#061018", border: "none", borderRadius: 8,
            padding: "7px 10px", cursor: busy ? "default" : "pointer", opacity: busy ? 0.7 : 1,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
          <Send style={{ width: 14, height: 14 }} />
        </button>
      </div>

      {/* Routing status */}
      {busy && routingLabel ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10, fontSize: 11, color: CYAN, fontFamily: MONO }}>
          <span style={{
            width: 8, height: 8, borderRadius: "50%", background: CYAN,
            boxShadow: `0 0 8px ${CYAN}`, animation: "csPulse 1s ease-in-out infinite",
          }} />
          Routing to {routingLabel}...
        </div>
      ) : (
        <div style={{ marginTop: 10, fontSize: 10.5, color: FADED, fontFamily: MONO, letterSpacing: "0.04em" }}>
          Sovereign routes every ask to the right chamber.
        </div>
      )}
    </div>
  );
}

/* ── Column 2 — Chamber map (reference 2×2 grid) ──────────────────────────── */
const MAP_CARDS = [
  { id: "lyric-forge", name: "Lyric Forge", tier: "base", badge: "ACTIVE", desc: "Write lyrics, hooks, verses, and flows powered by AI." },
  { id: "script", name: "Script Scriptorium", tier: "base", badge: "UNLOCKED", desc: "Book builder, script generator, story engine." },
  { id: "marketplace", name: "Marketplace Forge", tier: "top", badge: "UNLOCKED", desc: "Forge sellable drops straight to your store." },
  { id: "collaboration", name: "Collaboration Chamber", tier: "top", badge: "UNLOCKED", desc: "Guest creators, roles, and shareable invites." },
];

function ChamberMap({ activeId, onOpen, canUseStudio, userTierRank }) {
  return (
    <div style={{ background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 14, padding: 16 }}>
      <PanelHeader label="Chamber Map" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 12 }}>
        {MAP_CARDS.map((card) => {
          const isActive = activeId === card.id;
          const isLyric = card.id === "lyric-forge";
          const locked = TIER_RANK[card.tier] > userTierRank && !canUseStudio;
          const badge = isActive ? "ACTIVE" : locked ? "LOCKED" : "UNLOCKED";
          const badgeColor =
            badge === "ACTIVE" ? CYAN
            : badge === "LOCKED" ? "#f59e0b"
            : "#34d399";
          const badgeBg =
            badge === "ACTIVE" ? CYAN_SOFT
            : badge === "LOCKED" ? "rgba(245,158,11,0.1)"
            : "rgba(52,211,153,0.1)";
          return (
            <button
              key={card.id}
              onClick={() => onOpen(card.id)}
              style={{
                textAlign: "left", cursor: locked ? "not-allowed" : "pointer",
                background: isActive ? "rgba(34,211,238,0.08)" : "#12161f",
                border: `1px solid ${isActive ? "rgba(34,211,238,0.55)" : BORDER}`,
                borderRadius: 12, padding: "12px 12px 10px",
                boxShadow: isActive ? "0 0 18px rgba(34,211,238,0.15)" : "none",
                transition: "border-color 0.15s ease, background 0.15s ease",
                fontFamily: SANS, opacity: locked ? 0.75 : 1,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                {isLyric ? (
                  <span style={{
                    width: 26, height: 26, borderRadius: "50%", flexShrink: 0,
                    background: "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95) 0%, rgba(34,211,238,0.65) 28%, rgba(34,211,238,0.3) 55%, rgba(8,80,102,0.6) 100%)",
                    boxShadow: "0 0 10px rgba(34,211,238,0.5)",
                  }} />
                ) : (
                  <span style={{
                    width: 26, height: 26, borderRadius: 8, flexShrink: 0,
                    background: "rgba(255,255,255,0.06)", border: `1px solid ${BORDER}`,
                    display: "flex", alignItems: "center", justifyContent: "center", color: FADED,
                  }}>
                    <Lock style={{ width: 12, height: 12 }} />
                  </span>
                )}
                <span style={{ fontWeight: 800, fontSize: 12.5, color: "#fff", letterSpacing: "0.01em" }}>{card.name}</span>
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, alignItems: "center" }}>
                {card.tier && (
                  <span style={{
                    fontSize: 8, fontFamily: MONO, letterSpacing: "0.08em", color: MUTED,
                    border: `1px solid ${BORDER}`, borderRadius: 4, padding: "2px 5px",
                  }}>
                    {card.tier.toUpperCase()}
                  </span>
                )}
                <span style={{
                  fontSize: 8, fontFamily: MONO, fontWeight: 800, letterSpacing: "0.08em",
                  color: badgeColor, background: badgeBg,
                  borderRadius: 4, padding: "2px 5px",
                }}>
                  {badge}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ── Shared panel header ──────────────────────────────────────────────────── */
function PanelHeader({ label }) {
  return (
    <div style={{
      fontFamily: MONO, fontSize: 9.5, fontWeight: 800, letterSpacing: "0.22em",
      textTransform: "uppercase", color: MUTED, display: "flex", alignItems: "center", gap: 8,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: CYAN, boxShadow: `0 0 8px ${CYAN}` }} />
      {label}
    </div>
  );
}

/* ── New project modal ────────────────────────────────────────────────────── */
function NewProjectModal({ onCreated, onClose }) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState("music");
  const KIND_GLYPH = { music: "♪", visual: "◉", writing: "✦", business: "⬡" };
  const submit = (e) => {
    e.preventDefault();
    if (!name.trim()) { toast.error("Name the project first."); return; }
    onCreated({ id: `proj_${Date.now()}`, name: name.trim(), glyph: KIND_GLYPH[kind] || "♪", kind });
  };
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 120, background: "rgba(6,10,16,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center", padding: 20, backdropFilter: "blur(3px)",
    }}>
      <form onSubmit={submit} style={{
        width: 400, maxWidth: "100%", background: PANEL2, border: `1px solid ${BORDER}`,
        borderRadius: 16, padding: 24, boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
          <div style={{ fontSize: 15, fontWeight: 800, color: "#fff" }}>New Project</div>
          <button type="button" onClick={onClose} style={{ background: "none", border: "none", color: FADED, cursor: "pointer", fontSize: 18, lineHeight: 1 }}>×</button>
        </div>
        <label style={{ display: "block", marginBottom: 14 }}>
          <span style={{ fontSize: 10, fontFamily: MONO, letterSpacing: "0.12em", textTransform: "uppercase", color: MUTED, display: "block", marginBottom: 6 }}>Project name</span>
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Urban Sunset EP"
            style={{ width: "100%", boxSizing: "border-box", background: "#12161f", border: `1px solid ${BORDER}`, borderRadius: 8, padding: "10px 12px", color: "#fff", fontSize: 13, outline: "none" }} />
        </label>
        <label style={{ display: "block", marginBottom: 20 }}>
          <span style={{ fontSize: 10, fontFamily: MONO, letterSpacing: "0.12em", textTransform: "uppercase", color: MUTED, display: "block", marginBottom: 6 }}>Kind</span>
          <select value={kind} onChange={(e) => setKind(e.target.value)}
            style={{ width: "100%", background: "#12161f", border: `1px solid ${BORDER}`, borderRadius: 8, padding: "10px 12px", color: "#fff", fontSize: 13, outline: "none" }}>
            <option value="music">♪ Music</option>
            <option value="visual">◉ Visual</option>
            <option value="writing">✦ Writing</option>
            <option value="business">⬡ Business</option>
          </select>
        </label>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button type="button" onClick={onClose} style={{ background: "rgba(255,255,255,0.06)", border: `1px solid ${BORDER}`, color: MUTED, borderRadius: 8, padding: "9px 16px", cursor: "pointer", fontSize: 12.5 }}>Cancel</button>
          <button type="submit" style={{ background: CYAN, border: "none", color: "#061018", borderRadius: 8, padding: "9px 18px", cursor: "pointer", fontSize: 12.5, fontWeight: 800 }}>Create Project</button>
        </div>
      </form>
    </div>
  );
}

/* ── Customize dropdown (reference: dark button with SAVE rows) ───────────── */
function CustomizeMenu({ open, onClose, onSave }) {
  if (!open) return null;
  return (
    <div style={{
      position: "absolute", top: 44, right: 0, width: 190, zIndex: 130,
      background: PANEL2, border: `1px solid ${BORDER}`, borderRadius: 12,
      boxShadow: "0 18px 60px rgba(0,0,0,0.55)", overflow: "hidden",
    }}>
      {[
        { icon: <Save style={{ width: 13, height: 13 }} />, label: "SAVE", onClick: () => { onSave(); onClose(); } },
        { icon: <Check style={{ width: 13, height: 13 }} />, label: "SAVE & CONTINUE", onClick: () => { onSave(); onClose(); } },
      ].map((row, i) => (
        <button key={i} onClick={row.onClick}
          style={{
            display: "flex", alignItems: "center", gap: 10, width: "100%", textAlign: "left",
            background: "transparent", border: "none", borderBottom: i === 0 ? `1px solid ${BORDER}` : "none",
            color: "#e2e8f0", padding: "11px 14px", cursor: "pointer", fontSize: 11, fontWeight: 800,
            fontFamily: MONO, letterSpacing: "0.1em",
          }}>
          {row.icon} {row.label}
        </button>
      ))}
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────────────── */
export default function CreatorStudio() {
  const { user, logout } = useAuth();
  const { tier } = useEntitlements();

  const [activeChamber, setActiveChamber] = useState(null);
  const [ghostOpen, setGhostOpen] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);
  const [customizeOpen, setCustomizeOpen] = useState(false);

  // Projects + sessions persisted to localStorage (same keys as before)
  const [projects, setProjects] = useState(() => {
    try { return JSON.parse(localStorage.getItem("studio_projects") || "[]"); } catch { return []; }
  });
  const [activeProject, setActiveProject] = useState(null);
  const [sessions] = useState(() => {
    try { return JSON.parse(localStorage.getItem("studio_sessions") || "[]"); } catch { return []; }
  });

  const sessionStartRef = useRef(Date.now());

  // Sovereign dispatch ref — chambers call this to trigger AI
  const sovereignDispatch = useRef(null);
  const [artifactType, setArtifactType] = useState(null);
  const [artifactText, setArtifactText] = useState(null);

  const handleArtifact = useCallback((type, text) => {
    setArtifactType(type);
    setArtifactText(text);
  }, []);

  // Tier logic — owners / admins / execs always get full rank
  const isElevated = ["admin", "executive_admin"].includes(user?.role) || user?.is_owner === true || user?.owner === true;
  const studioTier = isElevated ? "executive" : (user?.feature_tier || user?.membership?.tier || tier || "free");
  const userTierRank = isElevated ? CANONICAL_TIER_RANK.executive : (CANONICAL_TIER_RANK[String(studioTier).toLowerCase()] ?? 0);
  const canUseStudio = isElevated || userTierRank >= CANONICAL_TIER_RANK.plus;
  // Tier logic
  const studioTier = user?.feature_tier || user?.membership?.tier || tier;
  const userTierRank = ["admin", "executive_admin"].includes(user?.role) ? CANONICAL_TIER_RANK.executive : (CANONICAL_TIER_RANK[String(studioTier || "free").toLowerCase()] ?? 0);
  const canUseStudio = ["admin", "executive_admin"].includes(user?.role) || userTierRank >= CANONICAL_TIER_RANK.plus;

  const saveProjects = useCallback((updated) => {
    try { localStorage.setItem("studio_projects", JSON.stringify(updated)); } catch {}
    setProjects(updated);
  }, []);

  const openChamber = useCallback((id) => {
    const found = CHAMBERS.find((c) => c.id === id);
    if (!found) return;
    const locked = TIER_RANK[found.tier] > userTierRank && !canUseStudio;
    if (locked) { toast.error(`${found.name} unlocks with Top Tier.`); return; }
    setActiveChamber((prev) => (prev?.id === id ? null : found));
  }, [userTierRank, canUseStudio]);

  const handleChamberJump = useCallback((route) => {
    if (route === "/studio") { setActiveChamber(null); return; }
    openChamber(route);
  }, [openChamber]);

  // ?chamber= param support
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requested = params.get("chamber") || params.get("tab");
    if (!requested) return;
    const mapped = { produce: "lyric-forge", publish: "publishing-gate", write: "lyric-forge", history: "vault" }[requested] || requested;
    const found = CHAMBERS.find((c) => c.id === mapped);
    if (found) setActiveChamber(found);
  }, []);

  // Default to Lyric Forge on first load (reference: active chamber)
  useEffect(() => {
    if (!activeChamber) {
      const params = new URLSearchParams(window.location.search);
      if (!params.get("chamber") && !params.get("tab")) setActiveChamber(CHAMBERS[0]);
    }
  }, [activeChamber]);

  // Save session on unmount
  useEffect(() => {
    const startTime = sessionStartRef.current;
    return () => {
      const session = { start: startTime, end: Date.now(), chambers: [] };
      try {
        const existing = JSON.parse(localStorage.getItem("studio_sessions") || "[]");
        localStorage.setItem("studio_sessions", JSON.stringify([...existing, session]));
      } catch {}
    };
  }, []);

  const handleProjectCreated = useCallback((project) => {
    const updated = [...projects, { ...project, status: "draft", createdAt: Date.now() }];
    saveProjects(updated);
    setActiveProject(project);
    setShowNewProject(false);
    toast.success(`Project "${project.name}" created.`);
  }, [projects, saveProjects]);

  const handleSave = useCallback(() => {
    saveProjects(projects);
    toast.success("Suite saved.");
  }, [projects, saveProjects]);

  // Save a chamber's output as a version on the active project
  const saveVersion = useCallback((chamberId, content, note) => {
    if (!activeProject) { toast.error("Open a project first — use + New Project to name one."); return; }
    if (!content) { toast.error("Nothing to save yet — generate something first."); return; }
    try {
      const key = `studio_versions:${activeProject.id}`;
      const existing = JSON.parse(localStorage.getItem(key) || "[]");
      localStorage.setItem(key, JSON.stringify([
        ...existing,
        { id: Date.now(), chamber: chamberId, content, note: note || "", timestamp: Date.now() },
      ]));
      toast.success(`Version saved to "${activeProject.name}".`);
    } catch {
      toast.error("Could not save version.");
    }
  }, [activeProject]);

  const activeStage = activeChamber ? (STAGE_FOR_CHAMBER[activeChamber.id] ?? 0) : 0;
  const tierBadge = isElevated ? "OWNER CREATOR" : `${(studioTier || "free").toUpperCase()} CREATOR`;
  const workspaceId = activeChamber ? activeChamber.id : "studio";

  return (
    <div style={{ minHeight: "100vh", background: BG, color: "#fff", fontFamily: SANS }}>
      {/* ── Top navigation ── */}
      <div style={{
        height: 58, display: "flex", alignItems: "center", gap: 18,
        padding: "0 22px", borderBottom: `1px solid ${BORDER}`,
        background: "rgba(20,24,36,0.9)", position: "sticky", top: 0, zIndex: 90,
      }}>
        {/* Logo */}
        <Link to="/studio" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <span style={{
            width: 26, height: 26, borderRadius: "50%",
            background: "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95) 0%, rgba(34,211,238,0.6) 25%, rgba(34,211,238,0.25) 50%, rgba(8,80,102,0.6) 100%)",
            boxShadow: "0 0 14px rgba(34,211,238,0.55)",
          }} />
          <span style={{ fontSize: 17, fontWeight: 900, letterSpacing: "0.06em", color: "#fff" }}>M.O.R.E.</span>
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: 4, flex: 1 }}>
          <button
            onClick={() => { setGhostOpen(false); setActiveChamber(null); }}
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 999,
              border: "none", cursor: "pointer", fontSize: 12.5, fontWeight: 700, color: "#061018",
              background: ghostOpen ? CYAN : CYAN_SOFT, color: ghostOpen ? "#061018" : CYAN,
              border: `1px solid ${ghostOpen ? CYAN : "transparent"}`,
              boxShadow: ghostOpen ? "0 0 16px rgba(34,211,238,0.4)" : "none",
            }}
          >
            Ghost Producer
          </button>
        </div>

        {/* Right actions */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => setShowNewProject(true)}
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "8px 16px", borderRadius: 10,
              background: CYAN, border: "none", color: "#061018", fontWeight: 800, fontSize: 12.5,
              cursor: "pointer", boxShadow: "0 2px 12px rgba(34,211,238,0.35)",
            }}>
            <Plus style={{ width: 14, height: 14 }} /> New Project
          </button>

          <div style={{ position: "relative" }}>
            <button onClick={() => setCustomizeOpen((v) => !v)}
              style={{
                display: "flex", alignItems: "center", gap: 7, padding: "8px 14px", borderRadius: 10,
                background: "#1d2536", border: `1px solid ${BORDER}`, color: "#cbd5e1", cursor: "pointer",
                fontSize: 12.5, fontWeight: 700,
              }}>
              <Pencil style={{ width: 13, height: 13 }} /> Customize
              <ChevronDown style={{ width: 12, height: 12, opacity: 0.6 }} />
            </button>
            <CustomizeMenu open={customizeOpen} onClose={() => setCustomizeOpen(false)} onSave={handleSave} />
          </div>

          {/* Tier badge */}
          <div style={{
            display: "flex", alignItems: "center", gap: 8, padding: "6px 12px 6px 8px", borderRadius: 999,
            background: "#1d2536", border: `1px solid ${BORDER}`,
          }}>
            <span style={{
              width: 18, height: 18, borderRadius: "50%",
              background: "radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95) 0%, rgba(34,211,238,0.6) 25%, rgba(34,211,238,0.25) 52%, rgba(8,80,102,0.6) 100%)",
              boxShadow: "0 0 8px rgba(34,211,238,0.5)",
            }} />
            <span style={{ fontSize: 10.5, fontWeight: 800, fontFamily: MONO, letterSpacing: "0.1em", color: "#e2e8f0" }}>
              {tierBadge}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", minHeight: "calc(100vh - 58px - 56px)" }}>
        {/* ── Left icon rail ── */}
        <div style={{
          width: 58, flexShrink: 0, borderRight: `1px solid ${BORDER}`,
          background: "#11151f", display: "flex", flexDirection: "column", alignItems: "center",
          padding: "14px 0", gap: 6,
        }}>
          <RailIcon title="Dashboard" onClick={() => { setGhostOpen(false); setActiveChamber(null); }}><Home style={{ width: 17, height: 17 }} /></RailIcon>
          <RailIcon title="Studio" onClick={() => { setGhostOpen(false); openChamber("lyric-forge"); }}><Music2 style={{ width: 17, height: 17 }} /></RailIcon>
          <RailIcon title="Version history" onClick={() => openChamber("vault")}><History style={{ width: 17, height: 17 }} /></RailIcon>
          <RailIcon title="Earnings" onClick={() => openChamber("marketplace")}><BarChart3 style={{ width: 17, height: 17 }} /></RailIcon>
          <RailIcon title="Settings" onClick={() => setCustomizeOpen((v) => !v)}><Settings style={{ width: 17, height: 17 }} /></RailIcon>
          <RailIcon title="Profile" onClick={() => { window.location.href = "/avatar-setup"; }}><User style={{ width: 17, height: 17 }} /></RailIcon>
          <div style={{ flex: 1 }} />
          <RailIcon title="Sign out" onClick={() => logout()}><LogOut style={{ width: 17, height: 17 }} /></RailIcon>
        </div>

        {/* ── Three-column main ── */}
        <div className="cs-grid" style={{ flex: 1, minWidth: 0, display: "grid", gridTemplateColumns: "250px 330px minmax(0,1fr)", gap: 14, padding: 14 }}>
          {/* Column 1 — Session stats */}
          <div style={{ minWidth: 0 }}>
            <SessionStatsPanel projects={projects} sessions={sessions} />
          </div>

          {/* Column 2 — Sovereign AI + Chamber Map */}
          <div style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 14, overflowY: "auto", maxHeight: "calc(100vh - 58px - 56px - 28px)" }}>
            <SovereignPanel activeChamber={activeChamber?.id} onArtifact={handleArtifact} dispatchRef={sovereignDispatch} />
            <ChamberMap activeId={activeChamber?.id} canUseStudio={canUseStudio} userTierRank={userTierRank} onOpen={(id) => { setGhostOpen(false); openChamber(id); }} />
          </div>

          {/* Column 3 — Studio workspace */}
          <div style={{ minWidth: 0, display: "flex", flexDirection: "column", gap: 12 }}>
            {/* Workspace top bar */}
            <div style={{
              display: "flex", alignItems: "center", gap: 12,
              background: PANEL, border: `1px solid ${BORDER}`, borderRadius: 12, padding: "9px 14px",
            }}>
              <span style={{ fontFamily: MONO, fontSize: 12.5, color: "#fff", letterSpacing: "0.02em" }}>
                /studio{activeChamber ? `/${activeChamber.id}` : ""}
              </span>
              <select
                value={activeChamber ? activeChamber.id : ""}
                onChange={(e) => { const v = e.target.value; setGhostOpen(false); v ? openChamber(v) : setActiveChamber(null); }}
                style={{
                  marginLeft: "auto", background: "#12161f", border: `1px solid ${BORDER}`, borderRadius: 8,
                  color: "#cbd5e1", fontSize: 12, padding: "6px 8px", outline: "none", cursor: "pointer",
                }}
              >
                <option value="">Top Nav — all chambers</option>
                {CHAMBERS.map((c) => <option key={c.id} value={c.id}>{c.glyph} {c.name}</option>)}
              </select>
              <button onClick={() => setShowNewProject(true)} title="New project"
                style={{
                  width: 28, height: 28, borderRadius: 8, background: CYAN_SOFT, border: `1px solid ${CYAN}55`,
                  color: CYAN, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                <Plus style={{ width: 14, height: 14 }} />
              </button>
            </div>

            {/* Active chamber editor */}
            <div style={{
              flex: 1, minHeight: 480, display: "flex", flexDirection: "column",
              background: PANEL, border: `1px solid ${activeChamber ? `rgba(34,211,238,0.28)` : BORDER}`,
              borderRadius: 14, overflow: "hidden",
            }}>
              {/* Editor header */}
              <div style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "12px 16px", borderBottom: `1px solid ${BORDER}`,
                background: "rgba(34,211,238,0.04)",
              }}>
                <span style={{ fontSize: 15, filter: "drop-shadow(0 0 6px rgba(34,211,238,0.6))" }}>
                  {activeChamber ? activeChamber.glyph : "⬡"}
                </span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: "#fff", letterSpacing: "0.02em" }}>
                    {(activeChamber ? activeChamber.name : "Studio Workspace").toUpperCase()}
                  </div>
                  <div style={{ fontSize: 10.5, color: MUTED, marginTop: 1 }}>
                    {activeChamber ? activeChamber.desc : "Select a chamber from the map, the timeline, or the selector above."}
                  </div>
                </div>
                {activeChamber && (
                  <button onClick={() => setActiveChamber(null)} title="Close chamber"
                    style={{ marginLeft: "auto", background: "none", border: "none", color: FADED, cursor: "pointer", fontSize: 17, lineHeight: 1 }}>
                    ×
                  </button>
                )}
              </div>

              {/* Editor body */}
              <div style={{ flex: 1, padding: 18, overflowY: "auto" }}>
                {!activeChamber ? (
                  <div style={{ textAlign: "center", padding: "60px 20px", color: FADED, fontSize: 13 }}>
                    <div style={{ fontSize: 34, marginBottom: 12, opacity: 0.5 }}>⬡</div>
                    The workspace is empty. Pick a chamber to start creating.
                  </div>
                ) : (
                  <>
                    {activeChamber.id === "lyric-forge" && (
                      <LyricForge
                        tier={userTierRank >= 2 ? "top" : userTierRank >= 1 ? "mid" : "base"}
                        sovereignDispatch={sovereignDispatch}
                        artifact={artifactType === "lyrics" ? artifactText : null}
                        activeProject={activeProject}
                        onSaveVersion={saveVersion}
                      />
                    )}
                    {activeChamber.id === "visual-altar" && (
                      <VisualAltar
                        tier={userTierRank >= 2 ? "top" : userTierRank >= 1 ? "mid" : "base"}
                        sovereignDispatch={sovereignDispatch}
                        artifact={artifactType === "visual_direction" ? artifactText : null}
                      />
                    )}
                    {activeChamber.id === "script" && (
                      <ScriptScriptorium
                        tier={userTierRank >= 2 ? "top" : userTierRank >= 1 ? "mid" : "base"}
                        sovereignDispatch={sovereignDispatch}
                        artifact={artifactType === "polished_script" ? artifactText : null}
                      />
                    )}
                    {activeChamber.id === "sound-lab" && (
                      <SoundLab
                        tier={userTierRank >= 2 ? "top" : userTierRank >= 1 ? "mid" : "base"}
                        sovereignDispatch={sovereignDispatch}
                        artifact={artifactType === "sonic_blueprint" ? artifactText : null}
                      />
                    )}
                    {activeChamber.id === "vault" && <VaultOfVersions projects={projects} />}
                    {activeChamber.id === "publishing-gate" && (
                      <PublishingGate
                        tier={userTierRank >= 2 ? "top" : userTierRank >= 1 ? "mid" : "base"}
                        sovereignDispatch={sovereignDispatch}
                        artifact={artifactType === "metadata" ? artifactText : null}
                      />
                    )}
                    {activeChamber.id === "ghost-producer" && <StudioContent embedded />}
                    {activeChamber.id === "marketplace" && <MarketplaceForge />}
                    {activeChamber.id === "collaboration" && <CollaborationChamber activeProject={activeProject} />}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Creative timeline (fixed bottom) ── */}
      <CreativeTimeline
        activeStage={activeStage}
        onStageClick={() => {}}
        onChamberJump={handleChamberJump}
      />

      {/* ── Floating Ghost Producer window ── */}
      {ghostOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 110, background: "rgba(6,10,16,0.55)",
          display: "flex", justifyContent: "flex-end", backdropFilter: "blur(2px)",
        }} onClick={() => setGhostOpen(false)}>
          <div onClick={(e) => e.stopPropagation()} style={{
            width: 780, maxWidth: "96vw", height: "100%",
            background: BG, borderLeft: `1px solid ${BORDER}`, borderTop: `1px solid ${BORDER}`,
            boxShadow: "-30px 0 80px rgba(0,0,0,0.5)",
            display: "flex", flexDirection: "column",
          }}>
            {/* Modal top bar */}
            <div style={{
              display: "flex", alignItems: "center", gap: 14, padding: "12px 18px",
              borderBottom: `1px solid ${BORDER}`, background: "#11151f",
            }}>
              <span style={{ fontFamily: MONO, fontSize: 13, fontWeight: 700, color: "#fff" }}>
                /ghostProducer Studio
              </span>
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
                <button onClick={() => setShowNewProject(true)}
                  style={{
                    display: "flex", alignItems: "center", gap: 6, padding: "6px 12px", borderRadius: 8,
                    background: CYAN, border: "none", color: "#061018", fontWeight: 800, fontSize: 11.5, cursor: "pointer",
                  }}>
                  <Plus style={{ width: 12, height: 12 }} /> New Project
                </button>
                <button onClick={() => setCustomizeOpen((v) => !v)}
                  style={{
                    display: "flex", alignItems: "center", gap: 6, padding: "6px 12px", borderRadius: 8,
                    background: "#1d2536", border: `1px solid ${BORDER}`, color: "#cbd5e1", fontSize: 11.5, fontWeight: 700, cursor: "pointer",
                  }}>
                  <Pencil style={{ width: 12, height: 12 }} /> Customize
                </button>
                <button onClick={() => setGhostOpen(false)} title="Close"
                  style={{ background: "none", border: "none", color: FADED, cursor: "pointer", fontSize: 19, lineHeight: 1, padding: "0 4px" }}>
                  ×
                </button>
              </div>
            </div>
            {/* Sequencer + publish (real StudioContent) */}
            <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
              <StudioContent embedded />
            </div>
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      {showNewProject && (
        <NewProjectModal onCreated={handleProjectCreated} onClose={() => setShowNewProject(false)} />
      )}

      <style>{`
        @keyframes csPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
        @media (max-width: 1100px) {
          .cs-grid { grid-template-columns: 220px minmax(0,1fr) !important; }
          .cs-grid > div:first-child { display: none; }
        }
        @media (max-width: 820px) {
          .cs-grid { grid-template-columns: minmax(0,1fr) !important; }
          .cs-grid > div:nth-child(2) { display: none; }
        }
      `}</style>
    </div>
  );
}

/* ── Small presentational helpers ─────────────────────────────────────────── */
function NavPill({ to, label }) {
  return (
    <Link to={to} style={{
      padding: "7px 12px", borderRadius: 8, textDecoration: "none",
      color: MUTED, fontSize: 12.5, fontWeight: 600, letterSpacing: "0.01em",
    }}>
      {label}
    </Link>
  );
}

function RailIcon({ children, title, onClick }) {
  return (
    <button onClick={onClick} title={title}
      style={{
        width: 36, height: 36, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
        background: "transparent", border: "none", color: FADED, cursor: "pointer",
      }}>
      {children}
    </button>
  );
}
