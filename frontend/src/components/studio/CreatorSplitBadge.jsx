const TIER_COLORS = {
  base: "#b5651d",
  certified: "#d4af37",
  active_instructor: "#39ff14",
  certified_instructor: "#00ffcc",
};

export default function CreatorSplitBadge({ split, nextTier }) {
  if (!split) return null;

  const { creator_pct = 70, platform_pct = 30, tier = "base", tier_label = "Base Creator" } = split;
  const tierColor = TIER_COLORS[tier] || TIER_COLORS.base;
  const fillPct = Math.max(0, Math.min(100, ((creator_pct - 70) / 15) * 100));

  return (
    <div
      style={{
        maxWidth: 280,
        background: "#0a0805",
        border: "1px solid rgba(181,101,29,0.3)",
        borderRadius: 10,
        padding: 14,
        fontFamily: "monospace",
      }}
    >
      {/* Label */}
      <div style={{ fontSize: 9, color: "#b5651d", textTransform: "uppercase", letterSpacing: "0.2em", marginBottom: 8 }}>
        YOUR SPLIT
      </div>

      {/* Big split numbers */}
      <div style={{ fontSize: 24, fontWeight: 900, color: tierColor, marginBottom: 4, lineHeight: 1.1 }}>
        {creator_pct}% / {platform_pct}%
      </div>

      {/* Tier label */}
      <div style={{ fontSize: 11, color: "#6b5e60", marginBottom: 12 }}>{tier_label}</div>

      {/* Progress bar */}
      <div style={{ background: "#1a1208", borderRadius: 4, height: 6, marginBottom: 10, overflow: "hidden" }}>
        <div
          style={{ height: "100%", width: `${fillPct}%`, background: "#b5651d", borderRadius: 4, transition: "width 0.6s ease" }}
        />
      </div>

      {/* Next tier */}
      {nextTier && (
        <>
          <div style={{ fontSize: 10, color: "#6b5e60", marginBottom: 4 }}>
            Next: {nextTier.label}
          </div>
          <a
            href={nextTier.link}
            style={{ fontSize: 11, color: "#b5651d", textDecoration: "none", display: "inline-block" }}
          >
            {nextTier.action} →
          </a>
        </>
      )}
    </div>
  );
}
