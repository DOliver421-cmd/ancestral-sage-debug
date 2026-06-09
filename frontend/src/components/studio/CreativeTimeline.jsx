import { studioSound } from "./SoundSystem";

const STAGES = ['Idea', 'Draft', 'Version', 'Asset', 'Final', 'Publish', 'Monetize'];

const STAGE_CHAMBERS = {
  0: '/studio',
  1: 'lyric-forge',
  2: 'vault',
  3: 'visual-altar',
  4: 'script',
  5: 'publishing-gate',
  6: 'marketplace',
};

export default function CreativeTimeline({ activeStage = 0, onStageClick, onChamberJump }) {
  const handleClick = (index) => {
    if (onStageClick) onStageClick(index);
    studioSound.play('timeline_advance');
    const chamber = STAGE_CHAMBERS[index];
    if (chamber && onChamberJump) onChamberJump(chamber);
  };

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      height: 56, zIndex: 80,
      background: '#0a0a14',
      borderTop: '1px solid rgba(255,215,0,0.15)',
      display: 'flex', alignItems: 'center',
      padding: '0 16px',
      overflowX: 'auto',
    }}>
      {/* Connecting line */}
      <div style={{
        position: 'absolute', left: 0, right: 0, top: '50%',
        height: 1, background: 'rgba(255,215,0,0.1)',
        transform: 'translateY(-50%)',
        pointerEvents: 'none',
      }} />

      {STAGES.map((stage, i) => {
        const isActive = i === activeStage;
        const isPast = i < activeStage;

        return (
          <div
            key={stage}
            onClick={() => handleClick(i)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              gap: 4, cursor: 'pointer', flex: '0 0 auto',
              padding: '0 16px', position: 'relative', zIndex: 1,
              opacity: isPast ? 0.7 : isActive ? 1 : 0.4,
              transition: 'all 0.2s ease',
            }}
          >
            {/* Node dot */}
            <div style={{
              width: isActive ? 10 : 7, height: isActive ? 10 : 7,
              borderRadius: '50%',
              background: isActive ? '#ffd700' : isPast ? 'rgba(255,215,0,0.5)' : 'rgba(255,255,255,0.2)',
              boxShadow: isActive ? '0 0 12px rgba(255,215,0,0.8), 0 0 24px rgba(255,215,0,0.4)' : 'none',
              transition: 'all 0.2s ease',
              flexShrink: 0,
            }} />

            {/* Label */}
            <div style={{
              fontSize: 10, fontFamily: 'monospace',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              color: isActive ? '#ffd700' : isPast ? 'rgba(255,215,0,0.6)' : 'rgba(255,255,255,0.45)',
              textShadow: isActive ? '0 0 10px rgba(255,215,0,0.6)' : 'none',
              whiteSpace: 'nowrap',
              fontWeight: isActive ? 900 : 400,
            }}>
              {stage}
            </div>

            {/* Active indicator underline */}
            {isActive && (
              <div style={{
                position: 'absolute', bottom: -1, left: '50%',
                transform: 'translateX(-50%)',
                width: '80%', height: 2,
                background: 'linear-gradient(90deg, transparent, #ffd700, transparent)',
              }} />
            )}
          </div>
        );
      })}

      <style>{`
        @media (max-width: 600px) {
          .creative-timeline { padding: 0 8px; }
        }
      `}</style>
    </div>
  );
}
