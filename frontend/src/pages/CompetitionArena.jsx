import { useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

// ── Design tokens ─────────────────────────────────────────────────────────────
const COPPER = "#b5651d";
const INK = "#1a1a1a";
const BONE = "#f5f0e8";

// ── Persona metadata ──────────────────────────────────────────────────────────
const PERSONA_META = {
  AXIOM:  { emoji: "🏛️", subtitle: "The Architect" },
  CIPHER: { emoji: "🎤", subtitle: "The Street Poet" },
  MAVEN:  { emoji: "📊", subtitle: "The Market Mind" },
  SAGE:   { emoji: "🌿", subtitle: "The Elder Voice" },
};

// ── Role badge ────────────────────────────────────────────────────────────────
function RoleBadge({ role }) {
  const styles = {
    lead:       { background: COPPER, color: "#fff" },
    support:    { background: "#6b7280", color: "#fff" },
    competitor: { background: "#1a1a1a", color: "#f5f0e8" },
  };
  return (
    <span style={{
      ...styles[role] || styles.competitor,
      fontSize: 10,
      fontWeight: 900,
      padding: "2px 7px",
      borderRadius: 3,
      textTransform: "uppercase",
      letterSpacing: "0.08em",
    }}>
      {role}
    </span>
  );
}

// ── Leaderboard bar ───────────────────────────────────────────────────────────
function LeaderboardBar({ leaderboard, totalRounds }) {
  if (!leaderboard || leaderboard.length === 0) return null;
  return (
    <div style={{
      background: INK,
      borderRadius: 10,
      padding: "16px 20px",
      marginBottom: 28,
      display: "flex",
      gap: 12,
      flexWrap: "wrap",
      alignItems: "center",
    }}>
      <span style={{ color: COPPER, fontWeight: 900, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.1em", marginRight: 4 }}>
        Standings
      </span>
      {leaderboard.map((p, i) => (
        <div key={p.persona} style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "rgba(255,255,255,0.06)",
          borderRadius: 6,
          padding: "8px 14px",
          flex: "1 1 180px",
          minWidth: 160,
        }}>
          <span style={{ color: COPPER, fontWeight: 900, fontSize: 13 }}>#{i + 1}</span>
          <span style={{ fontSize: 16 }}>{PERSONA_META[p.persona]?.emoji || "🤖"}</span>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#fff", fontWeight: 700, fontSize: 13 }}>{p.persona}</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>
              {p.rounds_completed}/{totalRounds} rounds · avg {p.cumulative_average > 0 ? p.cumulative_average.toFixed(1) : "—"}
            </div>
          </div>
          <RoleBadge role={p.role} />
        </div>
      ))}
    </div>
  );
}

// ── Persona result card ───────────────────────────────────────────────────────
function PersonaCard({ result, onScoreSubmit, submittingId }) {
  const [score, setScore] = useState(75);
  const [submitted, setSubmitted] = useState(false);
  const meta = PERSONA_META[result.persona] || {};
  const isSubmitting = submittingId === result.round_id;

  const handleSubmit = async () => {
    await onScoreSubmit(result.round_id, score);
    setSubmitted(true);
  };

  const verdictColor = result.commissioner_verdict === "PASS" ? "#16a34a" : "#dc2626";

  return (
    <div style={{
      background: "#fff",
      border: `2px solid ${BONE}`,
      borderRadius: 12,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      boxShadow: "0 2px 12px rgba(26,26,26,0.07)",
    }}>
      {/* Card header */}
      <div style={{
        background: INK,
        padding: "14px 18px",
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}>
        <span style={{ fontSize: 22 }}>{meta.emoji || "🤖"}</span>
        <div style={{ flex: 1 }}>
          <div style={{ color: COPPER, fontWeight: 900, fontSize: 16 }}>{result.persona}</div>
          <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 12 }}>{meta.subtitle || result.tagline}</div>
        </div>
        {result.commissioner_score > 0 && (
          <div style={{ textAlign: "right" }}>
            <div style={{ color: verdictColor, fontWeight: 900, fontSize: 18 }}>{result.commissioner_score}</div>
            <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 10, textTransform: "uppercase" }}>Comm. Score</div>
          </div>
        )}
      </div>

      {/* Output */}
      <div style={{
        flex: 1,
        maxHeight: 380,
        overflowY: "auto",
        padding: "16px 18px",
        fontSize: 13,
        lineHeight: 1.7,
        color: INK,
        whiteSpace: "pre-wrap",
        fontFamily: "Georgia, serif",
        borderBottom: `1px solid ${BONE}`,
      }}>
        {result.output}
      </div>

      {/* Commissioner feedback */}
      {result.commissioner_feedback && (
        <div style={{
          background: BONE,
          padding: "10px 18px",
          fontSize: 12,
          color: "#555",
          fontStyle: "italic",
          borderBottom: `1px solid #e5ddd0`,
        }}>
          <span style={{ fontWeight: 700, fontStyle: "normal", color: INK }}>Commissioner: </span>
          {result.commissioner_feedback}
        </div>
      )}

      {/* Attempts badge */}
      {result.attempts > 1 && (
        <div style={{
          padding: "6px 18px",
          background: "#fff7ed",
          fontSize: 11,
          color: COPPER,
          fontWeight: 700,
          borderBottom: `1px solid ${BONE}`,
        }}>
          ↻ Revised {result.attempts - 1}× before passing
        </div>
      )}

      {/* User scoring */}
      <div style={{ padding: "14px 18px", background: "#fafaf8" }}>
        {submitted ? (
          <div style={{ textAlign: "center", color: "#16a34a", fontWeight: 700, fontSize: 14, padding: "6px 0" }}>
            ✓ Your score: {score}/100 submitted
          </div>
        ) : (
          <>
            <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: INK, marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em" }}>
              Your Score: <span style={{ color: COPPER, fontSize: 16 }}>{score}</span>/100
            </label>
            <input
              type="range"
              min={1}
              max={100}
              value={score}
              onChange={e => setScore(Number(e.target.value))}
              style={{ width: "100%", accentColor: COPPER, marginBottom: 10 }}
            />
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              style={{
                width: "100%",
                background: isSubmitting ? "#ccc" : COPPER,
                color: "#fff",
                border: "none",
                borderRadius: 6,
                padding: "9px 0",
                fontWeight: 900,
                fontSize: 13,
                cursor: isSubmitting ? "not-allowed" : "pointer",
                textTransform: "uppercase",
                letterSpacing: "0.07em",
              }}
            >
              {isSubmitting ? "Submitting…" : "Submit My Score"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ── Spinner card (loading state) ──────────────────────────────────────────────
function SpinnerCard({ personaName }) {
  const meta = PERSONA_META[personaName] || {};
  return (
    <div style={{
      background: "#fff",
      border: `2px solid ${BONE}`,
      borderRadius: 12,
      overflow: "hidden",
      boxShadow: "0 2px 12px rgba(26,26,26,0.07)",
    }}>
      <div style={{ background: INK, padding: "14px 18px", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 22 }}>{meta.emoji || "🤖"}</span>
        <div>
          <div style={{ color: COPPER, fontWeight: 900, fontSize: 16 }}>{personaName}</div>
          <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 12 }}>{meta.subtitle}</div>
        </div>
      </div>
      <div style={{ padding: "48px 18px", textAlign: "center", color: "#aaa", fontSize: 13 }}>
        <div style={{
          width: 32,
          height: 32,
          border: `3px solid ${BONE}`,
          borderTopColor: COPPER,
          borderRadius: "50%",
          animation: "spin 0.9s linear infinite",
          margin: "0 auto 14px",
        }} />
        Working…
      </div>
    </div>
  );
}

// ── Round tracker ─────────────────────────────────────────────────────────────
function RoundTracker({ currentRound, totalRounds }) {
  const pct = Math.min((currentRound / totalRounds) * 100, 100);
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontWeight: 700, color: INK, marginBottom: 5 }}>
        <span style={{ textTransform: "uppercase", letterSpacing: "0.08em", color: COPPER }}>Round Progress</span>
        <span>{currentRound} of {totalRounds}</span>
      </div>
      <div style={{ background: BONE, borderRadius: 99, height: 8, overflow: "hidden" }}>
        <div style={{ background: COPPER, width: `${pct}%`, height: "100%", borderRadius: 99, transition: "width 0.4s ease" }} />
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function CompetitionArena() {
  const { user } = useAuth();
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [roundNumber, setRoundNumber] = useState(1);
  const [leaderboard, setLeaderboard] = useState([]);
  const [submittingId, setSubmittingId] = useState(null);
  const [error, setError] = useState(null);

  const fetchLeaderboard = useCallback(async () => {
    try {
      const data = await api.get("/competition/leaderboard");
      setLeaderboard(data.leaderboard || []);
    } catch {
      // Non-fatal
    }
  }, []);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  const handleAssign = async () => {
    if (!task.trim()) return;
    setLoading(true);
    setResults(null);
    setError(null);

    try {
      const data = await api.post("/competition/task", {
        task: task.trim(),
        project_id: projectId || undefined,
        round_number: undefined,
      });
      setResults(data.results);
      setProjectId(data.project_id);
      setRoundNumber(data.round_number);
      await fetchLeaderboard();
    } catch (err) {
      setError(err?.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleScoreSubmit = async (roundId, score) => {
    setSubmittingId(roundId);
    try {
      await api.post("/competition/score", {
        scores: [{ round_id: roundId, user_score: score }],
      });
      await fetchLeaderboard();
    } catch (err) {
      setError(err?.message || "Score submission failed.");
    } finally {
      setSubmittingId(null);
    }
  };

  return (
    <div style={{ background: BONE, minHeight: "100vh", padding: "32px 24px", fontFamily: "system-ui, sans-serif" }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 32, fontWeight: 900, color: INK, margin: 0, letterSpacing: "-0.02em" }}>
          ⚔️ The Arena
        </h1>
        <p style={{ color: "#666", fontSize: 15, marginTop: 6, marginBottom: 0 }}>
          4 competitors. 5 rounds. Best work wins.
        </p>
      </div>

      {/* Leaderboard bar */}
      <LeaderboardBar leaderboard={leaderboard} totalRounds={5} />

      {/* Round tracker */}
      <RoundTracker currentRound={roundNumber} totalRounds={5} />

      {/* Task input */}
      <div style={{
        background: "#fff",
        border: `2px solid ${BONE}`,
        borderRadius: 12,
        padding: 20,
        marginBottom: 28,
        boxShadow: "0 2px 8px rgba(26,26,26,0.05)",
      }}>
        <label style={{
          display: "block",
          fontSize: 11,
          fontWeight: 900,
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          color: COPPER,
          marginBottom: 10,
        }}>
          Project Brief — Assign to All 4
        </label>
        <textarea
          value={task}
          onChange={e => setTask(e.target.value)}
          placeholder="Describe the product you want all 4 personas to create. Be specific about the type (ebook, workshop, album, toolkit, etc.), the audience, and any constraints."
          rows={4}
          style={{
            width: "100%",
            border: `1.5px solid #ddd`,
            borderRadius: 8,
            padding: "12px 14px",
            fontSize: 14,
            color: INK,
            resize: "vertical",
            fontFamily: "inherit",
            outline: "none",
            boxSizing: "border-box",
          }}
        />
        {error && (
          <div style={{ color: "#dc2626", fontSize: 13, marginTop: 8, fontWeight: 600 }}>
            {error}
          </div>
        )}
        <button
          onClick={handleAssign}
          disabled={loading || !task.trim()}
          style={{
            marginTop: 12,
            background: loading || !task.trim() ? "#ccc" : COPPER,
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "11px 28px",
            fontWeight: 900,
            fontSize: 14,
            cursor: loading || !task.trim() ? "not-allowed" : "pointer",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          {loading ? "All 4 are working…" : "Assign to All 4"}
        </button>
      </div>

      {/* Results grid */}
      {loading && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
          gap: 20,
        }}>
          {["AXIOM", "CIPHER", "MAVEN", "SAGE"].map(name => (
            <SpinnerCard key={name} personaName={name} />
          ))}
        </div>
      )}

      {results && !loading && (
        <>
          <div style={{ marginBottom: 14, display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontWeight: 900, color: INK, fontSize: 15 }}>Round {roundNumber} Results</span>
            <span style={{ fontSize: 12, color: "#888" }}>
              Commissioner has scored. Now add your scores.
            </span>
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: 20,
          }}>
            {results.map(result => (
              <PersonaCard
                key={result.round_id}
                result={result}
                onScoreSubmit={handleScoreSubmit}
                submittingId={submittingId}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
