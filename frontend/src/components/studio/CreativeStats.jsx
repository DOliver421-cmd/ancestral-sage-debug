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

// ── Progress ring (pure SVG — no chart lib, no cost) ────────────────────────
function Ring({ value, max, sub, label, color }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const pct = max > 0 ? Math.min(1, value / max) : 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 7 }}>
      <div style={{ position: "relative", width: 64, height: 64 }}>
        <svg width="64" height="64" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
          <circle
            cx="32" cy="32" r={r} fill="none"
            stroke={color} strokeWidth="6" strokeLinecap="round"
            strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
            style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        <div style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 11, fontWeight: 900, color: "#fff", fontFamily: "monospace",
        }}>
          {sub}
        </div>
      </div>
      <div style={{
        fontSize: 8, fontFamily: "monospace", letterSpacing: "0.16em",
        textTransform: "uppercase", color: "rgba(255,255,255,0.4)",
      }}>
        {label}
      </div>
    </div>
  );
}

export default function CreativeStats({ projects = [], sessions = [] }) {
  const totalTime = sessions.reduce((acc, s) => {
    if (s.start && s.end) return acc + (s.end - s.start);
    return acc;
  }, 0);

  const completed = projects.filter(p => p.status === 'completed').length;
  const drafts = projects.filter(p => !p.status || p.status === 'draft').length;
  const streak = calcStreak(sessions);
  const chambers = [...new Set(sessions.flatMap(s => s.chambers || []))];

  // Rings: 10-project target, 4-hour session target
  const projectTarget = 10;
  const timeTargetMin = 240;
  const timeSub = totalTime >= 3600000 ? formatDuration(totalTime) : `${Math.floor(totalTime / 60000)}m`;

  return (
    <div style={{
      width: 232,
      background: "rgba(8,8,16,0.96)",
      border: "1px solid rgba(255,215,0,0.15)",
      borderRadius: 8,
      padding: "16px 16px 14px",
      display: "flex", flexDirection: "column", gap: 12,
      boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
    }}>
      {/* Header */}
      <div style={{
        fontFamily: "monospace", fontSize: 9, fontWeight: 900,
        letterSpacing: "0.22em", textTransform: "uppercase",
        color: "rgba(255,215,0,0.75)", display: "flex", alignItems: "center", gap: 8,
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: "50%",
          background: "#00ffcc", boxShadow: "0 0 8px #00ffcc",
        }} />
        Session Stats
      </div>

      {/* Rings */}
      <div style={{ display: "flex", justifyContent: "space-around", padding: "4px 0" }}>
        <Ring
          value={projects.length}
          max={projectTarget}
          sub={`${projects.length}/${projectTarget}`}
          label="Projects"
          color="#00ffcc"
        />
        <Ring
          value={Math.min(timeTargetMin, Math.floor(totalTime / 60000))}
          max={timeTargetMin}
          sub={timeSub}
          label="Time"
          color="#ffd700"
        />
      </div>

      {/* Divider */}
      <div style={{ height: 1, background: "rgba(255,215,0,0.1)" }} />

      {/* Detail rows */}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <StatRow label="Completed" value={completed} icon="✦" />
        <StatRow label="Active Drafts" value={drafts} icon="⌬" />
        <StatRow label="Creative Streak" value={`${streak} day${streak !== 1 ? 's' : ''}`} icon="🔥" />
      </div>

      {chambers.length > 0 && (
        <>
          <div style={{ height: 1, background: "rgba(255,215,0,0.1)" }} />
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
            {chambers.map(ch => (
              <span key={ch} style={{
                fontSize: 9, fontFamily: "monospace", color: "rgba(255,215,0,0.65)",
                border: "1px solid rgba(255,215,0,0.2)", padding: "2px 7px",
                background: "rgba(255,215,0,0.04)",
              }}>
                {ch}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function StatRow({ label, value, icon }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ fontSize: 13, width: 18, textAlign: "center", opacity: 0.8 }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: 8, fontFamily: "monospace", letterSpacing: "0.15em",
          textTransform: "uppercase", color: "rgba(255,255,255,0.35)",
        }}>
          {label}
        </div>
      </div>
      <div style={{ fontSize: 13, fontWeight: 900, color: "#ffd700", fontFamily: "monospace" }}>
        {value}
      </div>
    </div>
  );
}
