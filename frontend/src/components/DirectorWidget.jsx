import { useState, useEffect, useRef, useCallback } from "react";
import { api, API, BACKEND_URL } from "../lib/api";
import { useAuth } from "../lib/auth";
import { toast } from "sonner";

// ── Constants ──────────────────────────────────────────────────────────────────

const PERSONA_STYLES = {
  director: {
    title: "THE DIRECTOR",
    subtitle: "Executive Intelligence",
    color: "#C9A84C",
    bg: "#0A0F1E",
  },
  assistant_director: {
    title: "ASSISTANT DIRECTOR",
    subtitle: "Your Institute Guide",
    color: "#4C9AC9",
    bg: "#0A1A2E",
  },
};

const SpeechRecognitionImpl =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

const QUICK_ACTIONS = {
  student: [
    { label: "My Progress", msg: "Show me a summary of my learning progress and what I should focus on next." },
    { label: "Help Me Study", msg: "I need help studying. What resources are available to me?" },
    { label: "Find a Course", msg: "What courses are available and which should I take next?" },
  ],
  instructor: [
    { label: "My Students", msg: "Give me a summary of my students and their progress." },
    { label: "Lab Approvals", msg: "Are there any lab submissions pending my review?" },
    { label: "Course Help", msg: "Help me with course and curriculum management." },
  ],
  admin: [
    { label: "Session Brief", msg: "Generate a full session brief: open incidents, at-risk students, pending reviews, platform health, and my top 3 priority actions right now. Use get_incident_register and any other tools needed." },
    { label: "System Status", msg: "Give me a quick system status report for WAI-Institute." },
    { label: "Threat Report", msg: "Are there any active threats or incidents I should know about?" },
    { label: "Legal Strategy", msg: "What legal risks or considerations require my attention?" },
  ],
  executive_admin: [
    { label: "Session Brief", msg: "Generate a full session brief: open incidents, at-risk students, pending reviews, platform health, and my top 3 priority actions right now. Use get_incident_register and any other tools needed." },
    { label: "System Status", msg: "Give me a full system status and security posture report." },
    { label: "Revenue Update", msg: "What is our current revenue status, recent payments, and this week's projections?" },
    { label: "Legal Strategy", msg: "What legal risks or considerations require my attention?" },
  ],
};

// Tabs available per role
const ROLE_TABS = {
  student:         ["chat"],
  instructor:      ["chat", "students"],
  admin:           ["chat", "monitor", "more", "notes"],
  executive_admin: ["chat", "monitor", "more", "notes"],
};

const TAB_META = {
  chat:     { label: "Chat",     icon: "💬" },
  monitor:  { label: "Monitor",  icon: "📡" },
  more:     { label: "M.O.R.E.", icon: "🤝" },
  students: { label: "Students", icon: "👥" },
  notes:    { label: "Notes",    icon: "📝" },
};

const POLL_INTERVAL = 90_000;

const HEALTH_COLORS = {
  nominal:  "#4CAF50",
  warning:  "#C9A84C",
  critical: "#E53935",
};

const SIZE_WIDTH = {
  normal:     "400px",
  expanded:   "600px",
  fullscreen: "min(92vw, 960px)",
};

const SIZE_PX = {
  normal:     400,
  expanded:   600,
  fullscreen: () => Math.round(window.innerWidth * 0.92),
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function getDefaultPos() {
  return {
    x: Math.max(16, window.innerWidth - 420),
    y: Math.max(16, window.innerHeight - 560),
  };
}

function snapToCorner(x, y, w, h) {
  const pad = 16;
  const corners = [
    { x: pad,                           y: pad },
    { x: window.innerWidth - w - pad,   y: pad },
    { x: pad,                           y: window.innerHeight - h - pad },
    { x: window.innerWidth - w - pad,   y: window.innerHeight - h - pad },
  ];
  return corners.reduce((best, c) =>
    Math.hypot(x - c.x, y - c.y) < Math.hypot(x - best.x, y - best.y) ? c : best
  );
}

function buildAlertMessage(pulse, prev) {
  const lines = [];
  if (prev) {
    const m = pulse.metrics, p = prev.metrics;
    if (m.incidents_open      > p.incidents_open)      lines.push(`⚠ ${m.incidents_open - p.incidents_open} new incident(s) opened.`);
    if (m.at_risk_login       > p.at_risk_login)       lines.push(`⚠ ${m.at_risk_login - p.at_risk_login} additional student(s) inactive 7+ days.`);
    if (m.at_risk_quiz        > p.at_risk_quiz)        lines.push(`⚠ ${m.at_risk_quiz - p.at_risk_quiz} additional student(s) struggling with quizzes.`);
    if (m.more_flags_pending  > p.more_flags_pending)  lines.push(`⚠ ${m.more_flags_pending - p.more_flags_pending} new M.O.R.E. content flag(s).`);
    if (m.failed_payments_24h > p.failed_payments_24h) lines.push(`⚠ ${m.failed_payments_24h - p.failed_payments_24h} new payment failure(s).`);
    if (m.new_users_24h       > p.new_users_24h)       lines.push(`ℹ ${m.new_users_24h - p.new_users_24h} new user registration(s).`);
    if (m.pending_labs        > p.pending_labs)        lines.push(`ℹ ${m.pending_labs - p.pending_labs} additional lab submission(s) pending.`);
  } else {
    if (!pulse.alerts.length) {
      lines.push("✓ All systems nominal. No action required.");
    } else {
      lines.push("Initial scan complete:");
      pulse.alerts.forEach(a =>
        lines.push(`${a.level === "high" ? "⚠" : a.level === "warn" ? "⚡" : "ℹ"} ${a.msg}`)
      );
    }
    if (pulse.recent_incidents?.length) {
      lines.push(`\nOpen incidents:`);
      pulse.recent_incidents.forEach(i => lines.push(`  · ${i.title || "Untitled"}`));
    }
  }
  return lines.length ? lines.join("\n") : null;
}

// ── Sub-panels ─────────────────────────────────────────────────────────────────

function MonitorPanel({ pulse, style, onAction, onScan }) {
  if (!pulse) {
    return (
      <div style={{ padding: "32px", textAlign: "center", color: "#aaa", fontSize: "12px" }}>
        <div style={{ fontSize: "28px", marginBottom: "10px" }}>📡</div>
        Scanning systems…
      </div>
    );
  }

  const m = pulse.metrics;
  const healthColor = HEALTH_COLORS[pulse.health] || HEALTH_COLORS.nominal;

  const metrics = [
    {
      label: "Open Incidents", val: m.incidents_open,
      warn: m.incidents_open > 0, critical: m.incidents_open > 3, icon: "🚨",
      action: "Brief me on all open incidents — titles, severity, and the immediate actions I should take right now.",
    },
    {
      label: "At-Risk (Login)", val: m.at_risk_login,
      warn: m.at_risk_login > 0, icon: "👤",
      action: "List every student who has not logged in for 7 or more days. For each one suggest a specific outreach message.",
    },
    {
      label: "At-Risk (Quiz)", val: m.at_risk_quiz,
      warn: m.at_risk_quiz > 0, icon: "📊",
      action: "List students who are struggling with quizzes — scores, which modules, and recommended intervention steps.",
    },
    {
      label: "Labs Pending", val: m.pending_labs,
      warn: m.pending_labs > 0, icon: "🔬",
      action: "List all pending lab submissions that need instructor review, oldest first.",
    },
    {
      label: "M.O.R.E. Flags", val: m.more_flags_pending,
      warn: m.more_flags_pending > 0, critical: m.more_flags_pending > 5, icon: "🚩",
      action: "What M.O.R.E. content flags are pending? Summarize each and recommend approve or remove.",
    },
    {
      label: "Failed Payments", val: m.failed_payments_24h,
      warn: m.failed_payments_24h > 0, icon: "💳",
      action: "Report on payment failures in the last 24 hours. Who was affected and what follow-up is needed?",
    },
    {
      label: "Total Users", val: m.total_users,
      warn: false, icon: "👥",
    },
    {
      label: "New (24h)", val: m.new_users_24h,
      warn: false, icon: "✨",
    },
  ];

  return (
    <div style={{ overflowY: "auto", height: "100%", padding: "10px" }}>
      {/* Health banner */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "8px 12px", borderRadius: "4px", marginBottom: "10px",
        background: pulse.health === "critical" ? "#2A0A0A" : pulse.health === "warning" ? "#1A1500" : "#0A1A0A",
        border: `1px solid ${healthColor}35`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{
            width: "8px", height: "8px", borderRadius: "50%", background: healthColor,
            display: "inline-block",
            animation: pulse.health !== "nominal" ? "pulse-dot 1.5s infinite" : "none",
          }} />
          <span style={{ color: healthColor, fontSize: "10px", fontWeight: "800", letterSpacing: "1.5px" }}>
            SYSTEM {pulse.health.toUpperCase()}
          </span>
        </div>
        <button onClick={onScan} style={{
          background: "transparent", border: "1px solid #333",
          color: "#666", padding: "2px 8px", fontSize: "9px",
          cursor: "pointer", borderRadius: "2px", letterSpacing: "0.5px",
        }}>↺ SCAN</button>
      </div>

      {/* Metrics grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px", marginBottom: "10px" }}>
        {metrics.map(item => {
          const c = item.critical ? HEALTH_COLORS.critical : item.warn ? HEALTH_COLORS.warning : "#aaa";
          return (
            <div
              key={item.label}
              onClick={item.action ? () => onAction(item.action) : undefined}
              style={{
                background: item.critical ? "#2A0A0A" : item.warn ? "#1A1500" : "#111",
                border: `1px solid ${item.warn ? c + "40" : "#1E1E1E"}`,
                borderRadius: "4px", padding: "8px 10px",
                cursor: item.action ? "pointer" : "default",
                transition: "border-color 0.15s, background 0.15s",
              }}
              title={item.action ? "Click to brief Director" : ""}
            >
              <div style={{ fontSize: "8px", color: "#999", letterSpacing: "0.5px", marginBottom: "3px" }}>
                {item.icon} {item.label}
              </div>
              <div style={{ fontSize: "22px", fontWeight: "900", fontFamily: "monospace", color: item.warn ? c : "#ccc" }}>
                {item.val ?? "—"}
              </div>
              {item.action && item.warn && (
                <div style={{ fontSize: "8px", color: c + "CC", marginTop: "2px" }}>tap to brief →</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Recent incidents */}
      {pulse.recent_incidents?.length > 0 && (
        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "5px" }}>OPEN INCIDENTS</div>
          {pulse.recent_incidents.map((inc, i) => (
            <div
              key={i}
              onClick={() => onAction(`Tell me everything about this incident and the recommended response: "${inc.title || "Untitled incident"}"`)}
              style={{
                padding: "6px 10px", marginBottom: "3px",
                background: "#1A0A0A", border: "1px solid #E5393520",
                borderLeft: "3px solid #E53935",
                borderRadius: "2px", cursor: "pointer",
                fontSize: "11px", color: "#CCC",
              }}
            >
              🚨 {inc.title || "Untitled incident"}
            </div>
          ))}
        </div>
      )}

      {/* Active alerts */}
      {pulse.alerts?.length > 0 && (
        <div>
          <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "5px" }}>ACTIVE ALERTS</div>
          {pulse.alerts.map((alert, i) => {
            const ac = alert.level === "high" ? HEALTH_COLORS.critical
              : alert.level === "warn" ? HEALTH_COLORS.warning : "#4CAF50";
            return (
              <div
                key={i}
                onClick={() => onAction(`Give me a full briefing and action plan for this alert: ${alert.msg}`)}
                style={{
                  padding: "5px 8px", marginBottom: "3px",
                  background: "#0D0D0D", border: `1px solid ${ac}20`,
                  borderLeft: `2px solid ${ac}`, borderRadius: "2px",
                  fontSize: "10px", color: "#AAA", cursor: "pointer",
                }}
              >
                {alert.level === "high" ? "⚠" : "⚡"} {alert.msg}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MorePanel({ style, onAction, pulse }) {
  const [moreStats, setMoreStats] = useState(null);
  const [loadingMore, setLoadingMore] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [posts, needs] = await Promise.all([
          fetch(`${BACKEND_URL}/api/more/posts?limit=5`).then(r => r.json()),
          fetch(`${BACKEND_URL}/api/more/needs?limit=5`).then(r => r.json()),
        ]);
        setMoreStats({
          postsTotal:  posts.total  || 0,
          needsTotal:  needs.total  || 0,
          recentPosts: posts.posts  || [],
          recentNeeds: needs.needs  || [],
        });
      } catch {
        setMoreStats({ postsTotal: 0, needsTotal: 0, recentPosts: [], recentNeeds: [] });
      } finally {
        setLoadingMore(false);
      }
    }
    load();
  }, []);

  const flagCount = pulse?.metrics?.more_flags_pending || 0;

  if (loadingMore) {
    return (
      <div style={{ padding: "32px", textAlign: "center", color: "#aaa", fontSize: "12px" }}>
        <div style={{ fontSize: "28px", marginBottom: "10px" }}>🤝</div>
        Loading M.O.R.E. data…
      </div>
    );
  }

  return (
    <div style={{ overflowY: "auto", height: "100%", padding: "10px" }}>
      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "5px", marginBottom: "10px" }}>
        {[
          { label: "Posts",  val: moreStats.postsTotal, icon: "📝", color: "#4C9AC9",                   warn: false },
          { label: "Needs",  val: moreStats.needsTotal, icon: "🙏", color: "#C9A84C",                   warn: false },
          { label: "Flags",  val: flagCount,            icon: "🚩", color: flagCount > 0 ? HEALTH_COLORS.warning : "#aaa", warn: flagCount > 0 },
        ].map(item => (
          <div key={item.label} style={{
            background: item.warn ? "#1A1500" : "#111",
            border: `1px solid ${item.warn ? item.color + "40" : "#1E1E1E"}`,
            borderRadius: "4px", padding: "8px", textAlign: "center",
          }}>
            <div style={{ fontSize: "14px" }}>{item.icon}</div>
            <div style={{ fontSize: "20px", fontWeight: "900", color: item.color, fontFamily: "monospace" }}>{item.val}</div>
            <div style={{ fontSize: "8px", color: "#999" }}>{item.label}</div>
          </div>
        ))}
      </div>

      {/* Flag action */}
      {flagCount > 0 && (
        <div
          onClick={() => onAction(`There are ${flagCount} pending M.O.R.E. content flags. Summarize each and tell me which to approve, which to remove, and why.`)}
          style={{
            padding: "8px 12px", marginBottom: "10px",
            background: "#1A1500", border: "1px solid #C9A84C40",
            borderLeft: "3px solid #C9A84C", borderRadius: "2px",
            cursor: "pointer", fontSize: "11px", color: "#C9A84C",
          }}
        >
          ⚠ {flagCount} content flag{flagCount !== 1 ? "s" : ""} need review — tap to brief Director
        </div>
      )}

      {/* Action buttons */}
      <div style={{ marginBottom: "10px" }}>
        <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "6px" }}>DIRECTOR ACTIONS</div>
        {[
          { label: "Review Content Flags",  msg: "Review all pending M.O.R.E. content flags. For each: what is it, does it violate policy, and what action should I take?" },
          { label: "Community Health",      msg: "Analyze the current state of the M.O.R.E. community exchange — engagement levels, common needs, and what needs my attention." },
          { label: "Litigation Queue",      msg: "Are there any M.O.R.E. litigation tool requests or legal flag items I should review?" },
          { label: "Oliver Guardian Status", msg: "Give me a status report on Oliver Guardian — is AI moderation working correctly, any bypasses or edge cases I should know about?" },
        ].map(action => (
          <button key={action.label} onClick={() => onAction(action.msg)} style={{
            display: "block", width: "100%", textAlign: "left",
            background: "transparent", border: `1px solid ${style.color}25`,
            color: style.color, padding: "6px 10px",
            fontSize: "10px", cursor: "pointer", borderRadius: "2px",
            marginBottom: "4px", letterSpacing: "0.3px",
          }}>
            → {action.label}
          </button>
        ))}
      </div>

      {/* Quick links */}
      <div style={{ marginBottom: "10px" }}>
        <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "6px" }}>QUICK LINKS</div>
        {[
          { label: "↗ M.O.R.E. Exchange",   href: "/more" },
          { label: "↗ M.O.R.E. Admin",      href: "/more/admin" },
          { label: "↗ M.O.R.E. Ops",        href: "/more/ops" },
          { label: "↗ Litigation Tool",      href: "/more/litigation" },
          { label: "↗ Community Chat",       href: "/more/chat" },
        ].map(link => (
          <a key={link.href} href={link.href} style={{
            display: "block", color: style.color + "CC", fontSize: "10px",
            padding: "4px 0", textDecoration: "none",
            borderBottom: "1px solid #1A1A1A",
            transition: "color 0.1s",
          }}
            onMouseEnter={e => { e.currentTarget.style.color = style.color; }}
            onMouseLeave={e => { e.currentTarget.style.color = style.color + "CC"; }}
          >
            {link.label}
          </a>
        ))}
      </div>

      {/* Recent needs */}
      {moreStats.recentNeeds.length > 0 && (
        <div>
          <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "6px" }}>RECENT NEEDS</div>
          {moreStats.recentNeeds.slice(0, 3).map((n, i) => (
            <div key={i} style={{
              padding: "5px 8px", marginBottom: "3px",
              background: "#0D0D0D", border: "1px solid #C9A84C18",
              borderLeft: "2px solid #C9A84C35", borderRadius: "2px",
              fontSize: "10px", color: "#bbb",
            }}>
              🙏 {n.title}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StudentsPanel({ pulse, style, onAction }) {
  const atRiskTotal = (pulse?.metrics?.at_risk_login || 0) + (pulse?.metrics?.at_risk_quiz || 0);
  const pendingLabs = pulse?.metrics?.pending_labs || 0;

  return (
    <div style={{ overflowY: "auto", height: "100%", padding: "10px" }}>
      {/* Key metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px", marginBottom: "10px" }}>
        {[
          {
            label: "At-Risk Students", val: atRiskTotal, warn: atRiskTotal > 0, icon: "⚠️",
            action: "List all at-risk students — those inactive 7+ days and those struggling with quizzes. For each, suggest a specific outreach message I can send.",
          },
          {
            label: "Labs Pending Review", val: pendingLabs, warn: pendingLabs > 0, icon: "🔬",
            action: "List all lab submissions pending my review, sorted oldest first. What should I prioritize?",
          },
        ].map(item => (
          <div
            key={item.label}
            onClick={() => onAction(item.action)}
            style={{
              background: item.warn ? "#1A1500" : "#111",
              border: `1px solid ${item.warn ? "#C9A84C40" : "#1E1E1E"}`,
              borderRadius: "4px", padding: "10px", cursor: "pointer",
            }}
          >
            <div style={{ fontSize: "8px", color: "#999", marginBottom: "3px" }}>{item.icon} {item.label}</div>
            <div style={{ fontSize: "24px", fontWeight: "900", fontFamily: "monospace", color: item.warn ? "#C9A84C" : "#ccc" }}>
              {item.val ?? "—"}
            </div>
            <div style={{ fontSize: "8px", color: "#C9A84C", marginTop: "2px" }}>tap to brief →</div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{ marginBottom: "10px" }}>
        <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "6px" }}>ACTIONS</div>
        {[
          { label: "Student Progress Report", msg: "Give me a full progress report across all students — who is excelling, who is struggling, and what I should do." },
          { label: "Lab Review Queue",        msg: "List all pending lab submissions in priority order. Include student name, module, and how long it has been waiting." },
          { label: "Outreach Drafts",         msg: "Which students need outreach right now? Draft a brief personalized message for each one." },
          { label: "Top Performers",          msg: "Who are my top performing students this month? What recognition or next steps would motivate them?" },
          { label: "Attendance Summary",      msg: "Give me an attendance summary — who has been consistently present and who is falling behind?" },
        ].map(action => (
          <button key={action.label} onClick={() => onAction(action.msg)} style={{
            display: "block", width: "100%", textAlign: "left",
            background: "transparent", border: `1px solid ${style.color}25`,
            color: style.color, padding: "6px 10px",
            fontSize: "10px", cursor: "pointer", borderRadius: "2px",
            marginBottom: "4px",
          }}>
            → {action.label}
          </button>
        ))}
      </div>

      {/* Quick links */}
      <div>
        <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px", marginBottom: "6px" }}>QUICK LINKS</div>
        {[
          { label: "↗ Admin Dashboard",  href: "/admin" },
          { label: "↗ Instructor Hub",   href: "/instructor" },
          { label: "↗ Attendance",       href: "/attendance" },
          { label: "↗ Leaderboard",      href: "/leaderboard" },
          { label: "↗ Incidents",        href: "/incidents" },
        ].map(link => (
          <a key={link.href} href={link.href} style={{
            display: "block", color: style.color + "CC", fontSize: "10px",
            padding: "4px 0", textDecoration: "none", borderBottom: "1px solid #1A1A1A",
            transition: "color 0.1s",
          }}
            onMouseEnter={e => { e.currentTarget.style.color = style.color; }}
            onMouseLeave={e => { e.currentTarget.style.color = style.color + "CC"; }}
          >
            {link.label}
          </a>
        ))}
      </div>
    </div>
  );
}

function NotesPanel({ style }) {
  const STORAGE_KEY = "director_widget_notes";
  const [notes, setNotes] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || ""; } catch { return ""; }
  });
  const [saved, setSaved] = useState(false);
  const timerRef = useRef(null);

  const handleChange = (val) => {
    setNotes(val);
    setSaved(false);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      try { localStorage.setItem(STORAGE_KEY, val); setSaved(true); } catch {}
    }, 800);
  };

  const clearNotes = () => {
    if (window.confirm("Clear all notes?")) {
      setNotes("");
      try { localStorage.removeItem(STORAGE_KEY); } catch {}
    }
  };

  const exportNotes = () => {
    const blob = new Blob([notes], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `director-notes-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
        <div style={{ fontSize: "8px", color: "#999", letterSpacing: "1px" }}>SESSION NOTES — auto-saves</div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {saved && <span style={{ fontSize: "8px", color: "#4CAF50" }}>✓ saved</span>}
          <button onClick={exportNotes} style={{
            background: "transparent", border: "1px solid #333",
            color: "#999", padding: "2px 6px", fontSize: "8px",
            cursor: "pointer", borderRadius: "2px",
          }}>↓ export</button>
          <button onClick={clearNotes} style={{
            background: "transparent", border: "1px solid #333",
            color: "#999", padding: "2px 6px", fontSize: "8px",
            cursor: "pointer", borderRadius: "2px",
          }}>clear</button>
        </div>
      </div>
      <textarea
        value={notes}
        onChange={e => handleChange(e.target.value)}
        placeholder={"Jot decisions, names, follow-ups, priorities…\n\nSurvives page navigation. Export anytime."}
        style={{
          flex: 1, background: "#0D0D0D",
          border: `1px solid ${style.color}18`,
          color: "#CCC", padding: "10px", fontSize: "11px",
          lineHeight: "1.7", resize: "none", outline: "none",
          borderRadius: "2px", fontFamily: "inherit",
        }}
      />
    </div>
  );
}

// ── Main Widget ────────────────────────────────────────────────────────────────

export default function DirectorWidget() {
  const { user } = useAuth();

  const [open, setOpen] = useState(() => {
    try { return localStorage.getItem("director_widget_open") !== "false"; } catch { return true; }
  });
  const [persona, setPersona]       = useState("assistant_director");
  const [msgs, setMsgs]             = useState([]);
  const [input, setInput]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [minimized, setMinimized]   = useState(false);
  const [audioOn, setAudioOn]       = useState(true);
  const [recording, setRecording]   = useState(false);
  const [uploading, setUploading]   = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [activeTab, setActiveTab]   = useState("chat");
  const fileInputRef = useRef(null);

  // Monitoring state
  const [pulse, setPulse]   = useState(null);
  const [unread, setUnread] = useState(0);
  const prevPulseRef  = useRef(null);
  const pollTimerRef  = useRef(null);

  // ── Position & size ────────────────────────────────────────────────────────

  const [pos, setPos] = useState(() => {
    try {
      const saved = localStorage.getItem("director_widget_pos");
      if (saved) return JSON.parse(saved);
    } catch {}
    return getDefaultPos();
  });
  const [widgetSize, setWidgetSize] = useState("normal");

  const widgetRef      = useRef(null);
  const dragging       = useRef(false);
  const dragOffset     = useRef({ x: 0, y: 0 });
  const hasDragged     = useRef(false);
  const dragStartPos   = useRef({ x: 0, y: 0 });
  const posRef         = useRef(pos);
  useEffect(() => { posRef.current = pos; }, [pos]);

  // Clamp position when size changes
  useEffect(() => {
    const w = typeof SIZE_PX[widgetSize] === "function" ? SIZE_PX[widgetSize]() : SIZE_PX[widgetSize];
    setPos(p => ({
      x: Math.max(0, Math.min(window.innerWidth  - w,  p.x)),
      y: Math.max(0, Math.min(window.innerHeight - 50, p.y)),
    }));
  }, [widgetSize]);

  const startDrag = useCallback((clientX, clientY) => {
    dragging.current     = true;
    hasDragged.current   = false;
    dragStartPos.current = { x: clientX, y: clientY };
    const rect = widgetRef.current?.getBoundingClientRect();
    if (rect) dragOffset.current = { x: clientX - rect.left, y: clientY - rect.top };
  }, []);

  const onHeaderMouseDown = useCallback((e) => {
    if (e.button !== 0) return;
    startDrag(e.clientX, e.clientY);
    e.preventDefault();
  }, [startDrag]);

  const onHeaderTouchStart = useCallback((e) => {
    if (e.touches.length !== 1) return;
    startDrag(e.touches[0].clientX, e.touches[0].clientY);
  }, [startDrag]);

  useEffect(() => {
    const THRESHOLD = 5;

    const moveWidget = (clientX, clientY) => {
      const dx = clientX - dragStartPos.current.x;
      const dy = clientY - dragStartPos.current.y;
      if (!hasDragged.current && Math.hypot(dx, dy) < THRESHOLD) return;
      hasDragged.current = true;
      const w = widgetRef.current?.offsetWidth || 400;
      setPos({
        x: Math.max(0, Math.min(window.innerWidth  - w,  clientX - dragOffset.current.x)),
        y: Math.max(0, Math.min(window.innerHeight - 50, clientY - dragOffset.current.y)),
      });
    };

    const endDrag = () => {
      if (!dragging.current) return;
      dragging.current = false;
      if (hasDragged.current && widgetRef.current) {
        const w      = widgetRef.current.offsetWidth;
        const h      = widgetRef.current.offsetHeight;
        const snapped = snapToCorner(posRef.current.x, posRef.current.y, w, h);
        setPos(snapped);
        posRef.current = snapped;
      }
      try { localStorage.setItem("director_widget_pos", JSON.stringify(posRef.current)); } catch {}
    };

    const onMove     = e => { if (dragging.current) moveWidget(e.clientX, e.clientY); };
    const onTouchMove = e => {
      if (!dragging.current || e.touches.length !== 1) return;
      e.preventDefault();
      moveWidget(e.touches[0].clientX, e.touches[0].clientY);
    };

    window.addEventListener("mousemove",  onMove);
    window.addEventListener("mouseup",    endDrag);
    window.addEventListener("touchmove",  onTouchMove, { passive: false });
    window.addEventListener("touchend",   endDrag);
    return () => {
      window.removeEventListener("mousemove",  onMove);
      window.removeEventListener("mouseup",    endDrag);
      window.removeEventListener("touchmove",  onTouchMove);
      window.removeEventListener("touchend",   endDrag);
    };
  }, []);

  // Alt+D global shortcut
  useEffect(() => {
    const onKey = e => {
      if (e.altKey && e.key.toLowerCase() === "d") {
        e.preventDefault();
        setMinimized(m => !m);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const cycleSize = useCallback((e) => {
    e.stopPropagation();
    setMinimized(cur => {
      if (cur) return false;
      setWidgetSize(s => s === "normal" ? "expanded" : s === "expanded" ? "fullscreen" : "normal");
      return false;
    });
  }, []);

  // ── Derived ────────────────────────────────────────────────────────────────

  const bottomRef     = useRef(null);
  const recRef        = useRef(null);
  const speakAudioRef = useRef(null);
  const speakAbortRef = useRef(null);
  const isMonitor  = user?.role === "admin" || user?.role === "executive_admin";
  const roleTabs   = ROLE_TABS[user?.role] || ["chat"];

  // Reset tab if role changes and current tab is not available
  useEffect(() => {
    if (!roleTabs.includes(activeTab)) setActiveTab("chat");
  }, [user?.role]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Greeting ──────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!user) { setOpen(false); setMsgs([]); setPulse(null); return; }
    const isExec = user.role === "admin" || user.role === "executive_admin";
    setPersona(isExec ? "director" : "assistant_director");
    const fallback = isExec
      ? `Welcome back, ${user.full_name}. I am The Director. Initiating monitoring scan…`
      : `Welcome back, ${user.full_name}. I am the Assistant Director. How can I guide you today?`;
    setMsgs([{ role: "assistant", text: fallback }]);
    // Always show widget on login — clear any stale "closed" state from localStorage
    try { localStorage.removeItem("director_widget_open"); } catch {}
    setOpen(true);

    api.get("/ai/director/greeting")
      .then(r => { setPersona(r.data.persona); setMsgs([{ role: "assistant", text: r.data.greeting }]); })
      .catch(() => {});
  }, [user]);

  // Persist open state
  useEffect(() => {
    try { localStorage.setItem("director_widget_open", open ? "true" : "false"); } catch {}
  }, [open]);

  // ── Pulse monitoring ──────────────────────────────────────────────────────

  const poll = useCallback(async () => {
    if (!isMonitor) return;
    try {
      const { data } = await api.get("/ai/director/pulse");
      const prev = prevPulseRef.current;
      const alertMsg = buildAlertMessage(data, prev);
      setPulse(data);
      prevPulseRef.current = data;
      if (alertMsg) {
        setMsgs(m => [...m, { role: "assistant", text: alertMsg, isAlert: true, health: data.health, pulse: data }]);
        if (minimized) setUnread(u => u + 1);
      }
    } catch {}
  }, [isMonitor, minimized]);

  useEffect(() => {
    if (!isMonitor) return;
    poll();
    pollTimerRef.current = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(pollTimerRef.current);
  }, [isMonitor, poll]);

  useEffect(() => { if (!minimized) setUnread(0); }, [minimized]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  // ── TTS ───────────────────────────────────────────────────────────────────

  const speak = async (text) => {
    if (!audioOn) return;
    speakAbortRef.current?.abort();
    if (speakAudioRef.current) { speakAudioRef.current.pause(); speakAudioRef.current = null; }
    const controller = new AbortController();
    speakAbortRef.current = controller;
    try {
      const token = localStorage.getItem("lce_token");
      const r = await fetch(`${API}/ai/sage/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text, voice: persona === "director" ? "onyx" : "nova", speed: 1.0, session_id: "director" }),
        signal: controller.signal,
      });
      if (!r.ok) return;
      const blob = await r.blob();
      const url  = URL.createObjectURL(blob);
      const audio = new Audio(url);
      speakAudioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); speakAudioRef.current = null; };
      audio.play().catch(() => { URL.revokeObjectURL(url); speakAudioRef.current = null; });
    } catch (e) { if (e?.name !== "AbortError") { speakAudioRef.current = null; } }
  };

  // ── STT ───────────────────────────────────────────────────────────────────

  const toggleMic = () => {
    if (!SpeechRecognitionImpl) return;
    if (recording) {
      recRef.current?.stop();
      recRef.current = null;
      setRecording(false);
      return;
    }
    const rec = new SpeechRecognitionImpl();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false;
    rec.onresult = ev => {
      const txt = ev.results?.[0]?.[0]?.transcript?.trim();
      if (txt) setInput(cur => cur ? `${cur} ${txt}` : txt);
    };
    rec.onerror = () => { recRef.current = null; setRecording(false); };
    rec.onend   = () => { recRef.current = null; setRecording(false); };
    recRef.current = rec;
    try {
      rec.start();
      setRecording(true);
    } catch {
      recRef.current = null;
    }
  };

  // ── File upload ───────────────────────────────────────────────────────────

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast.error("File too large. Max 5 MB."); return; }
    setUploading(true);
    try {
      const form  = new FormData();
      form.append("file", file);
      const token = localStorage.getItem("lce_token");
      const r     = await fetch(`${API}/ai/director/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Upload failed");
      setAttachedFile({ file_id: data.file_id, filename: data.filename });
      setMsgs(m => [...m, {
        role: "assistant",
        text: `📎 File received: ${data.filename}\nMention it in your next message — I will read it automatically.`,
      }]);
    } catch (err) {
      toast.error(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // ── Send ──────────────────────────────────────────────────────────────────

  const send = async (overrideMsg) => {
    const userMsg = (overrideMsg || input).trim();
    if (!userMsg || loading) return;
    setInput("");
    setActiveTab("chat"); // Always switch to chat so response is visible

    const displayMsg = attachedFile
      ? `${userMsg}\n[Attached: ${attachedFile.filename}]`
      : userMsg;
    setMsgs(m => [...m, { role: "user", text: displayMsg }]);
    setLoading(true);

    const payload = {
      message: attachedFile
        ? `${userMsg}\n\n[ATTACHED FILE — use read_file with file_id: ${attachedFile.file_id}]`
        : userMsg,
      session_id: "director_session",
    };
    setAttachedFile(null);

    try {
      const r = await api.post("/ai/director", payload);
      setMsgs(m => [...m, { role: "assistant", text: r.data.reply }]);
      speak(r.data.reply);
      setPersona(r.data.persona);
    } catch {
      setMsgs(m => [...m, { role: "assistant", text: "I am temporarily unavailable. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const copyMsg = (text) => {
    navigator.clipboard?.writeText(text)
      .then(() => toast.success("Copied to clipboard"))
      .catch(() => toast.error("Copy failed"));
  };

  const clearChat = () => {
    if (window.confirm("Clear the conversation?")) setMsgs([]);
  };

  const exportChat = () => {
    const text = msgs.map(m => `[${m.role.toUpperCase()}]\n${m.text}`).join("\n\n---\n\n");
    const blob  = new Blob([text], { type: "text/plain" });
    const url   = URL.createObjectURL(blob);
    const a     = document.createElement("a");
    a.href = url;
    a.download = `director-session-${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  const quickActions  = QUICK_ACTIONS[user?.role] || QUICK_ACTIONS.student;
  const style         = PERSONA_STYLES[persona];
  const healthColor   = pulse ? HEALTH_COLORS[pulse.health] : style.color;

  const panelHeights = {
    normal:     "210px",
    expanded:   "330px",
    fullscreen: "480px",
  };

  if (!open) return null;

  // ── Minimized orb ─────────────────────────────────────────────────────────

  if (minimized) {
    return (
      <div
        ref={widgetRef}
        onMouseDown={onHeaderMouseDown}
        onTouchStart={onHeaderTouchStart}
        onClick={() => { if (!hasDragged.current) setMinimized(false); }}
        title="Director Widget — click to expand (Alt+D)"
        style={{
          position: "fixed",
          left: `${pos.x}px`,
          top:  `${pos.y}px`,
          width: "52px", height: "52px",
          zIndex: 1000,
          borderRadius: "50%",
          background: style.bg,
          border: `2px solid ${healthColor}70`,
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: `0 4px 24px rgba(0,0,0,0.5), 0 0 18px ${healthColor}20`,
          userSelect: "none", touchAction: "none",
        }}
      >
        {unread > 0 && (
          <span style={{
            position: "absolute", top: "-4px", right: "-4px",
            background: "#E53935", color: "#fff",
            borderRadius: "50%", width: "18px", height: "18px",
            fontSize: "9px", fontWeight: "900",
            display: "flex", alignItems: "center", justifyContent: "center",
            border: `2px solid ${style.bg}`,
          }}>{unread > 9 ? "9+" : unread}</span>
        )}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "3px" }}>
          <span style={{
            width: "7px", height: "7px", borderRadius: "50%", background: healthColor,
            animation: pulse?.health !== "nominal" ? "pulse-dot 1.5s infinite" : "none",
          }} />
          <span style={{ color: style.color, fontSize: "9px", fontWeight: "900", letterSpacing: "1px" }}>
            {persona === "director" ? "DIR" : "ADR"}
          </span>
        </div>
        <style>{`@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:0.3}}`}</style>
      </div>
    );
  }

  // ── Full widget ───────────────────────────────────────────────────────────

  return (
    <div
      ref={widgetRef}
      style={{
        position: "fixed",
        left: `${pos.x}px`,
        top:  `${pos.y}px`,
        width: SIZE_WIDTH[widgetSize],
        zIndex: 1000,
        fontFamily: "inherit",
        boxShadow: `0 8px 40px rgba(0,0,0,0.55), 0 0 0 1px ${style.color}18`,
        border: `1px solid ${style.color}25`,
        borderRadius: "6px",
        overflow: "hidden",
        transition: "width 0.15s ease",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* ── Header / drag zone ───────────────────────────────────────────── */}
      <div
        onMouseDown={onHeaderMouseDown}
        onTouchStart={onHeaderTouchStart}
        onClick={() => { if (!hasDragged.current) setMinimized(true); }}
        style={{
          background: style.bg,
          color: style.color,
          padding: "10px 12px",
          cursor: "grab",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          userSelect: "none", touchAction: "none", flexShrink: 0,
        }}
      >
        {/* Drag handle + identity */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span
            title="Drag to move"
            style={{ color: style.color + "45", fontSize: "15px", lineHeight: 1, cursor: "grab" }}
          >⠿</span>
          {isMonitor && (
            <span style={{
              width: "7px", height: "7px", borderRadius: "50%",
              background: healthColor, display: "inline-block",
              animation: pulse?.health !== "nominal" ? "pulse-dot 1.5s infinite" : "none",
            }} title={pulse ? `System: ${pulse.health}` : "Monitoring…"} />
          )}
          <div>
            <div style={{ fontSize: "10px", letterSpacing: "2px", fontWeight: "800" }}>{style.title}</div>
            <div style={{ fontSize: "8px", opacity: 0.55, letterSpacing: "0.5px" }}>
              {pulse && isMonitor
                ? `${pulse.health.toUpperCase()} · ${pulse.alerts.length} alert${pulse.alerts.length !== 1 ? "s" : ""}`
                : style.subtitle}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div
          onMouseDown={e => e.stopPropagation()}
          onTouchStart={e => e.stopPropagation()}
          style={{ display: "flex", gap: "8px", alignItems: "center" }}
        >
          {unread > 0 && (
            <span style={{
              background: "#E53935", color: "#fff",
              borderRadius: "50%", width: "16px", height: "16px",
              fontSize: "8px", fontWeight: "900",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>{unread > 9 ? "9+" : unread}</span>
          )}
          <span
            onClick={cycleSize}
            title={widgetSize === "fullscreen" ? "Shrink" : widgetSize === "expanded" ? "Fullscreen" : "Expand"}
            style={{ fontSize: "15px", cursor: "pointer", color: style.color, padding: "2px", lineHeight: 1 }}
          >{widgetSize === "fullscreen" ? "⊟" : "⊞"}</span>
          <span
            onClick={e => { e.stopPropagation(); setMinimized(true); }}
            title="Minimize (Alt+D)"
            style={{ fontSize: "12px", opacity: 0.7, cursor: "pointer", padding: "2px" }}
          >▼</span>
          <span
            onClick={e => { e.stopPropagation(); setOpen(false); }}
            title="Close"
            style={{ fontSize: "13px", opacity: 0.7, cursor: "pointer", padding: "2px" }}
          >✕</span>
        </div>
      </div>

      {/* ── Tab bar (only when more than 1 tab) ─────────────────────────── */}
      {roleTabs.length > 1 && (
        <div style={{
          background: style.bg,
          borderTop: `1px solid ${style.color}12`,
          display: "flex",
          flexShrink: 0,
        }}>
          {roleTabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                flex: 1, padding: "6px 3px",
                background: activeTab === tab ? "#0D0D0D" : "transparent",
                border: "none",
                borderBottom: activeTab === tab
                  ? `2px solid ${style.color}`
                  : "2px solid transparent",
                color: activeTab === tab ? style.color : style.color + "45",
                fontSize: "8px", fontWeight: "700", letterSpacing: "0.3px",
                cursor: "pointer", transition: "all 0.1s",
                display: "flex", alignItems: "center", justifyContent: "center", gap: "3px",
              }}
            >
              <span>{TAB_META[tab].icon}</span>
              <span>{TAB_META[tab].label}</span>
              {/* Badge: monitor alerts */}
              {tab === "monitor" && pulse?.alerts?.length > 0 && (
                <span style={{
                  background: healthColor, color: "#000",
                  borderRadius: "50%", width: "12px", height: "12px",
                  fontSize: "7px", fontWeight: "900",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{pulse.alerts.length}</span>
              )}
              {/* Badge: M.O.R.E. flags */}
              {tab === "more" && (pulse?.metrics?.more_flags_pending || 0) > 0 && (
                <span style={{
                  background: HEALTH_COLORS.warning, color: "#000",
                  borderRadius: "50%", width: "12px", height: "12px",
                  fontSize: "7px", fontWeight: "900",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{pulse.metrics.more_flags_pending}</span>
              )}
              {/* Badge: students at risk */}
              {tab === "students" && ((pulse?.metrics?.at_risk_login || 0) + (pulse?.metrics?.at_risk_quiz || 0)) > 0 && (
                <span style={{
                  background: HEALTH_COLORS.warning, color: "#000",
                  borderRadius: "50%", width: "12px", height: "12px",
                  fontSize: "7px", fontWeight: "900",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{(pulse.metrics.at_risk_login || 0) + (pulse.metrics.at_risk_quiz || 0)}</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* ── Panel area ──────────────────────────────────────────────────── */}
      <div style={{
        background: "#0D0D0D",
        height: panelHeights[widgetSize],
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        transition: "height 0.15s ease",
        flexShrink: 0,
      }}>

        {/* Chat */}
        {activeTab === "chat" && (
          <div style={{
            flex: 1, overflowY: "auto", padding: "10px",
            display: "flex", flexDirection: "column", gap: "8px",
          }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column" }}>
                <div
                  onClick={() => copyMsg(m.text)}
                  title="Click to copy"
                  style={{
                    alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: "92%",
                    background: m.isAlert
                      ? (m.health === "critical" ? "#2A0A0A" : m.health === "warning" ? "#1A1500" : "#0A1A0A")
                      : m.role === "user" ? style.color + "18" : "#1A1A1A",
                    border: `1px solid ${
                      m.isAlert
                        ? HEALTH_COLORS[m.health] + "45"
                        : m.role === "user" ? style.color + "35" : "#2A2A2A"
                    }`,
                    borderLeft: m.isAlert ? `3px solid ${HEALTH_COLORS[m.health]}` : undefined,
                    borderRadius: "4px", padding: "8px 10px",
                    fontSize: "11.5px", color: "#E0E0E0",
                    lineHeight: "1.65", whiteSpace: "pre-wrap",
                    cursor: "pointer",
                  }}
                >
                  {m.isAlert && (
                    <div style={{
                      fontSize: "8px", color: HEALTH_COLORS[m.health],
                      letterSpacing: "1px", fontWeight: "900", marginBottom: "4px",
                    }}>
                      ◉ DIRECTOR MONITORING ALERT
                    </div>
                  )}
                  {m.text}
                </div>
                {m.isAlert && m.pulse?.alerts?.length > 0 && (
                  <div style={{ marginTop: "4px", display: "flex", gap: "4px" }}>
                    <button
                      onClick={() => send(`Brief me on the current alerts: ${m.pulse.alerts.map(a => a.msg).join("; ")}`)}
                      style={{
                        background: "transparent", border: `1px solid ${style.color}40`,
                        color: style.color, padding: "2px 8px",
                        fontSize: "9px", cursor: "pointer", borderRadius: "2px",
                      }}
                    >Brief me →</button>
                    <button
                      onClick={() => send(`Give me an immediate action plan for: ${m.pulse.alerts.map(a => a.msg).join("; ")}`)}
                      style={{
                        background: "transparent", border: `1px solid ${style.color}25`,
                        color: style.color + "80", padding: "2px 8px",
                        fontSize: "9px", cursor: "pointer", borderRadius: "2px",
                      }}
                    >Action plan →</button>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: "flex-start", color: style.color, fontSize: "11px", padding: "4px 8px", opacity: 0.8 }}>
                Processing…
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}

        {activeTab === "monitor"  && <MonitorPanel  pulse={pulse} style={style} onAction={send} onScan={poll} />}
        {activeTab === "more"     && <MorePanel      style={style} onAction={send} pulse={pulse} />}
        {activeTab === "students" && <StudentsPanel  pulse={pulse} style={style} onAction={send} />}
        {activeTab === "notes"    && <NotesPanel     style={style} />}
      </div>

      {/* ── Quick actions bar (chat tab only) ───────────────────────────── */}
      {activeTab === "chat" && (
        <div style={{
          background: "#0A0A0A", borderTop: `1px solid ${style.color}12`,
          padding: "5px 8px", display: "flex", gap: "4px", flexWrap: "wrap",
          flexShrink: 0,
        }}>
          {quickActions.map(action => (
            <button key={action.label} onClick={() => setInput(action.msg)} style={{
              background: "transparent", border: `1px solid ${style.color}30`,
              color: style.color, padding: "3px 8px",
              fontSize: "9px", cursor: "pointer", borderRadius: "2px",
              letterSpacing: "0.3px",
            }}>
              {action.label}
            </button>
          ))}
          <div style={{ marginLeft: "auto", display: "flex", gap: "3px" }}>
            <button onClick={clearChat} title="Clear conversation" style={{
              background: "transparent", border: "1px solid #2A2A2A",
              color: "#aaa", padding: "3px 6px", fontSize: "11px",
              cursor: "pointer", borderRadius: "2px",
            }}>🗑</button>
            <button onClick={exportChat} title="Export conversation" style={{
              background: "transparent", border: "1px solid #2A2A2A",
              color: "#aaa", padding: "3px 6px", fontSize: "11px",
              cursor: "pointer", borderRadius: "2px",
            }}>↓</button>
            {isMonitor && (
              <button onClick={poll} title="Force monitoring scan" style={{
                background: "transparent", border: "1px solid #2A2A2A",
                color: "#aaa", padding: "3px 6px", fontSize: "10px",
                cursor: "pointer", borderRadius: "2px",
              }}>↺</button>
            )}
          </div>
        </div>
      )}

      {/* ── Input (chat tab only) ────────────────────────────────────────── */}
      {activeTab === "chat" && (
        <div style={{
          background: "#0A0A0A", borderTop: `1px solid ${style.color}20`,
          padding: "7px 8px", display: "flex", gap: "5px", alignItems: "center",
          flexShrink: 0,
        }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.json,.csv,.py,.js,.jsx,.ts,.tsx,.html,.xml,.yaml,.yml,.log,.pdf"
            style={{ display: "none" }}
            onChange={handleFileSelect}
          />
          <button onClick={toggleMic} title={recording ? "Stop recording" : "Voice input"} style={{
            background: recording ? style.color : "#161616",
            border: `1px solid ${style.color}22`,
            color: recording ? "#000" : style.color,
            padding: "6px 7px", fontSize: "13px", cursor: "pointer", borderRadius: "2px",
          }}>{recording ? "⏹" : "🎤"}</button>
          <button onClick={() => setAudioOn(!audioOn)} title={audioOn ? "Voice ON — click to mute" : "Voice OFF — click to unmute"} style={{
            background: audioOn ? style.color : "#161616",
            border: `1px solid ${style.color}22`,
            color: audioOn ? "#000" : style.color,
            padding: "6px 7px", fontSize: "13px", cursor: "pointer", borderRadius: "2px",
          }}>{audioOn ? "🔊" : "🔇"}</button>
          {isMonitor && (
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title={attachedFile ? `Attached: ${attachedFile.filename}` : "Attach file"}
              style={{
                background: attachedFile ? style.color : "#161616",
                border: `1px solid ${style.color}22`,
                color: attachedFile ? "#000" : style.color,
                padding: "6px 7px", fontSize: "13px", cursor: "pointer", borderRadius: "2px",
                opacity: uploading ? 0.5 : 1,
              }}
            >{uploading ? "⏳" : attachedFile ? "📎" : "📂"}</button>
          )}
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder={attachedFile ? "File attached — add a message…" : "Ask The Director…"}
            style={{
              flex: 1, background: "#161616",
              border: `1px solid ${style.color}20`,
              color: "#E8E8E8", padding: "6px 10px",
              fontSize: "12px", borderRadius: "2px", outline: "none",
            }}
          />
          <button onClick={() => send()} disabled={loading} style={{
            background: style.color, color: "#000",
            border: "none", padding: "6px 12px",
            fontSize: "10px", fontWeight: "800",
            cursor: loading ? "default" : "pointer",
            borderRadius: "2px", letterSpacing: "1px",
            opacity: loading ? 0.6 : 1,
          }}>SEND</button>
        </div>
      )}

      <style>{`@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:0.3}}`}</style>
    </div>
  );
}
