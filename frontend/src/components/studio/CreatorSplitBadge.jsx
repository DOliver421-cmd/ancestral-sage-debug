import { Link } from "react-router-dom";

const TIER_COLORS = { base: "#b5651d", certified: "#d4af37", active_instructor: "#39ff14", certified_instructor: "#00ffcc" };

export default function CreatorSplitBadge({ split, nextTier }) {
  if (!split) return null;
  const color = TIER_COLORS[split.tier] || "#b5651d";
  const pct = ((split.creator_pct - 70) / 15) * 100;
  return (
    <div style={{ maxWidth: 280, background: "#0a0805", border: "1px solid rgba(181,101,29,0.3)", borderRadius: 10, padding: 14, fontFamily: "monospace" }}>
      <div style={{ fontSize: 9, color: "#b5651d", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 6 }}>Your Split</div>
      <div style={{ fontSize: 24, fontWeight: 900, color, marginBottom: 2 }}>{split.creator_pct}% <span style={{ fontSize: 12, opacity: 0.5 }}>/ {split.platform_pct}%</span></div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)", marginBottom: 10 }}>{split.tier_label}</div>
      <div style={{ height: 4, background: "rgba(181,101,29,0.15)", borderRadius: 2, marginBottom: 10 }}>
        <div style={{ height: "100%", width: `${Math.max(5, pct)}%`, background: color, borderRadius: 2, transition: "width 0.5s ease" }} />
      </div>
      {nextTier && (
        <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)" }}>
          Next: <span style={{ color: "#b5651d" }}>{nextTier.label}</span><br />
          <Link to={nextTier.link} style={{ color: "#b5651d", textDecoration: "none", fontSize: 10 }}>{nextTier.action} →</Link>
        </div>
      )}
    </div>
  );
}
