import { useState, useEffect } from "react";
import { studioSound } from "./SoundSystem";

function formatDuration(ms) {
  if (!ms || ms <= 0) return '0h 0m';
  const totalMinutes = Math.floor(ms / 60000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours}h ${minutes}m`;
}

function calcStreak(sessions) {
  if (!sessions || sessions.length === 0) return 0;
  const days = new Set(
    sessions.map(s => new Date(s.start).toDateString())
  );
  const today = new Date();
  let streak = 0;
  for (let i = 0; i < 30; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    if (days.has(d.toDateString())) {
      streak++;
    } else if (i > 0) {
      break;
    }
  }
  return streak;
}

export default function CreativeStats({ projects = [], sessions = [] }) {
  const [open, setOpen] = useState(false);

  const toggle = () => {
    if (!open) studioSound.play('summon');
    setOpen(v => !v);
  };

  const totalTime = sessions.reduce((acc, s) => {
    if (s.start && s.end) return acc + (s.end - s.start);
    return acc;
  }, 0);

  const completed = projects.filter(p => p.status === 'completed').length;
  const drafts = projects.filter(p => !p.status || p.status === 'draft').length;
  const streak = calcStreak(sessions);

  const chambers = [...new Set(sessions.flatMap(s => s.chambers || []))];

  return (
    <div style={{
      position: 'fixed', left: 0, top: 0, bottom: 0,
      zIndex: 60, display: 'flex', alignItems: 'stretch',
      transition: 'all 0.3s ease',
      // Sits behind SovereignVoice (z: 50) but above main (z: 0)
      // Actually let's make it not conflict — it will be inside main layout
    }}>
      {/* Panel */}
      <div style={{
        width: open ? 280 : 0,
        overflow: 'hidden',
        transition: 'width 0.3s ease',
        background: 'rgba(6,6,14,0.97)',
        borderRight: '1px solid rgba(255,215,0,0.15)',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ padding: '24px 20px 20px', minWidth: 280 }}>
          {/* Header */}
          <div style={{
            fontFamily: 'monospace', fontSize: 9,
            letterSpacing: '0.25em', textTransform: 'uppercase',
            color: 'rgba(184,134,11,0.6)', marginBottom: 20,
          }}>
            ◈ Creator Stats
          </div>

          {/* Stats */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Stat label="Time Creating" value={formatDuration(totalTime)} icon="⏱" />
            <Stat label="Completed Projects" value={completed} icon="✦" />
            <Stat label="Active Drafts" value={drafts} icon="⌬" />
            <Stat label="Creative Streak" value={`${streak} day${streak !== 1 ? 's' : ''}`} icon="🔥" />
          </div>

          {chambers.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <div style={{
                fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.2em',
                textTransform: 'uppercase', color: 'rgba(184,134,11,0.5)', marginBottom: 10,
              }}>
                Tools Used
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {chambers.map(ch => (
                  <div key={ch} style={{
                    fontSize: 10, fontFamily: 'monospace',
                    color: 'rgba(255,215,0,0.7)',
                    border: '1px solid rgba(255,215,0,0.2)',
                    padding: '3px 8px',
                    background: 'rgba(255,215,0,0.04)',
                  }}>
                    {ch}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Caption */}
          <div style={{
            marginTop: 28, paddingTop: 16,
            borderTop: '1px solid rgba(255,215,0,0.1)',
            fontFamily: 'Georgia, serif', fontStyle: 'italic',
            fontSize: 12, color: 'rgba(255,255,255,0.35)',
          }}>
            "The stats don't lie."
          </div>
        </div>
      </div>

      {/* Toggle tab */}
      <button
        onClick={toggle}
        style={{
          width: 20, alignSelf: 'center',
          background: 'rgba(184,134,11,0.12)',
          border: '1px solid rgba(184,134,11,0.25)',
          borderLeft: 'none',
          padding: '14px 0',
          cursor: 'pointer',
          color: 'rgba(184,134,11,0.7)',
          borderRadius: '0 4px 4px 0',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          writingMode: 'vertical-rl',
          fontSize: 14,
        }}
        title={open ? 'Collapse stats' : 'View creative stats'}
      >
        ≡
      </button>
    </div>
  );
}

function Stat({ label, value, icon }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ fontSize: 16, width: 20, textAlign: 'center' }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: 9, fontFamily: 'monospace', letterSpacing: '0.15em',
          textTransform: 'uppercase', color: 'rgba(255,255,255,0.35)', marginBottom: 2,
        }}>
          {label}
        </div>
        <div style={{ fontSize: 16, fontWeight: 900, color: '#ffd700', lineHeight: 1 }}>
          {value}
        </div>
      </div>
    </div>
  );
}
