// The workflow timeline: vision → forge → sound → visual → script → publish.
// Each stage jumps the creator straight into the chamber that does that work.
const STAGES = ["VISION", "LYRIC FORGE", "SOUND LAB", "VISUAL ALTAR", "SCRIPT", "PUBLISH"];

const STAGE_CHAMBERS = {
  0: "/studio",
  1: "lyric-forge",
  2: "sound-lab",
  3: "visual-altar",
  4: "script",
  5: "publishing-gate",
};

const CYAN = "#0e7490";

export default function CreativeTimeline({ activeStage = 0, onStageClick, onChamberJump }) {
  const handleClick = (index) => {
    if (onStageClick) onStageClick(index);
    const chamber = STAGE_CHAMBERS[index];
    if (chamber && onChamberJump) onChamberJump(chamber);
  };

  return (
    <div style={{
      position: "fixed", bottom: 0, left: 0, right: 0,
      height: 56, zIndex: 80,
      background: "#faf9f7",
      borderTop: "1px solid rgba(28,25,23,0.07)",
      display: "flex", alignItems: "center",
      padding: "0 16px",
      overflowX: "auto",
    }}>
      {/* Connecting line */}
      <div style={{
        position: "absolute", left: 0, right: 0, top: "50%",
        height: 1, background: "rgba(14,116,144,0.15)",
        transform: "translateY(-50%)",
        pointerEvents: "none",
      }} />

      {STAGES.map((stage, i) => {
        const isActive = i === activeStage;
        const isPast = i < activeStage;

        return (
          <div
            key={stage}
            onClick={() => handleClick(i)}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 4, cursor: "pointer", flex: "0 0 auto",
              padding: "0 18px", position: "relative", zIndex: 1,
              opacity: isPast ? 0.65 : isActive ? 1 : 0.45,
              transition: "all 0.2s ease",
            }}
          >
            {/* Node dot */}
            <div style={{
              width: isActive ? 10 : 7, height: isActive ? 10 : 7,
              borderRadius: "50%",
              background: isActive ? CYAN : isPast ? "rgba(14,116,144,0.5)" : "rgba(28,25,23,0.2)",
              boxShadow: isActive ? `0 0 12px ${CYAN}, 0 0 24px rgba(14,116,144,0.5)` : "none",
              transition: "all 0.2s ease",
              flexShrink: 0,
            }} />

            {/* Label */}
            <div style={{
              fontSize: 9.5, fontFamily: "'SF Mono', 'Cascadia Code', Consolas, monospace",
              letterSpacing: "0.12em", textTransform: "uppercase",
              color: isActive ? CYAN : isPast ? "rgba(14,116,144,0.6)" : "rgba(28,25,23,0.5)",
              textShadow: isActive ? `0 0 10px rgba(14,116,144,0.6)` : "none",
              whiteSpace: "nowrap",
              fontWeight: isActive ? 900 : 500,
            }}>
              {stage}
            </div>

            {/* Active indicator underline */}
            {isActive && (
              <div style={{
                position: "absolute", bottom: -1, left: "50%",
                transform: "translateX(-50%)",
                width: "85%", height: 2,
                background: `linear-gradient(90deg, transparent, ${CYAN}, transparent)`,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}
