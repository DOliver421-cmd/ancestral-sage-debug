import { useReducer, useState } from "react";

const BUSINESSES = [
  { id: "grocery", name: "Greenwood Grocery", cost: 200, income: 40, trust: 10, desc: "Feed the community. Steady income, high trust." },
  { id: "law", name: "Law Office", cost: 350, income: 60, trust: 15, desc: "Legal protection for Black families." },
  { id: "hotel", name: "Stradford Hotel", cost: 500, income: 100, trust: 20, desc: "Largest Black-owned hotel in America." },
  { id: "bank", name: "Fraternal Bank", cost: 600, income: 90, trust: 25, desc: "Keep Black dollars circulating in Greenwood." },
  { id: "press", name: "The Tribune Press", cost: 250, income: 30, trust: 20, desc: "Tell our story. The press is power." },
  { id: "hospital", name: "Gurley Hospital", cost: 450, income: 50, trust: 30, desc: "Healthcare owned by us, for us." },
];

const EVENTS = [
  { id: "e1", text: "A white-owned bank refuses your loan application. The community rallies — neighbors lend what they can.", moneyEffect: -50, trustEffect: +15 },
  { id: "e2", text: "City inspectors arrive with new 'regulations' targeting Black businesses. Legal fees mount.", moneyEffect: -80, trustEffect: -5 },
  { id: "e3", text: "A traveling preacher speaks of Greenwood's prosperity. New families arrive, bringing skills and savings.", moneyEffect: +60, trustEffect: +10 },
  { id: "e4", text: "Neighboring Black farmers pool resources and buy from your stores. Mutual aid at work.", moneyEffect: +70, trustEffect: +20 },
  { id: "e5", text: "A major newspaper runs a story calling Greenwood 'Little Africa' in mockery. We wear it as a badge of honor.", moneyEffect: 0, trustEffect: +25 },
  { id: "e6", text: "Arson destroys a neighboring Black business. Community fundraiser organized.", moneyEffect: -100, trustEffect: +30 },
  { id: "e7", text: "Word spreads: Greenwood has its own everything. Visitors come to witness Black Wall Street.", moneyEffect: +90, trustEffect: +15 },
  { id: "e8", text: "City attempts to rezone Greenwood as industrial. The community lawyers fight back.", moneyEffect: -60, trustEffect: +10 },
];

function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5); }

const initialState = {
  money: 800,
  trust: 50,
  turn: 1,
  maxTurns: 8,
  owned: [],
  eventLog: [],
  phase: "build",
  gameOver: false,
};

function reducer(state, action) {
  switch (action.type) {
    case "BUY": {
      const b = BUSINESSES.find((x) => x.id === action.id);
      if (!b || state.owned.includes(b.id) || state.money < b.cost) return state;
      return { ...state, money: state.money - b.cost, owned: [...state.owned, b.id], trust: Math.min(100, state.trust + b.trust) };
    }
    case "END_TURN": {
      const income = state.owned.reduce((sum, id) => sum + (BUSINESSES.find((b) => b.id === id)?.income || 0), 0);
      const event = EVENTS[Math.floor(Math.random() * EVENTS.length)];
      const newMoney = state.money + income + event.moneyEffect;
      const newTrust = Math.max(0, Math.min(100, state.trust + event.trustEffect));
      const newTurn = state.turn + 1;
      const gameOver = newTurn > state.maxTurns || newMoney <= 0;
      return {
        ...state,
        money: newMoney,
        trust: newTrust,
        turn: newTurn,
        eventLog: [{ ...event, turn: state.turn, income }, ...state.eventLog],
        phase: "build",
        gameOver,
      };
    }
    default: return state;
  }
}

export default function BlackWallStreet({ onGameEnd }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [ended, setEnded] = useState(false);

  const score = Math.round(
    state.owned.length * 100 +
    (state.money / 10) +
    state.trust * 5
  );

  const handleEnd = () => {
    setEnded(true);
    onGameEnd({ score });
  };

  if (ended || state.gameOver) {
    const finalScore = Math.round(state.owned.length * 100 + (state.money / 10) + state.trust * 5);
    return (
      <div className="space-y-6" style={{ fontFamily: "monospace" }}>
        <div style={{ background: "#0a0a0f", border: "2px solid #b8860b", padding: "2rem" }}>
          <div style={{ color: "#ffd700", fontSize: "1.5rem", fontWeight: 900, marginBottom: "1rem" }}>
            {finalScore >= 600 ? "🏆 LEGACY BUILT" : finalScore >= 300 ? "⚡ GREENWOOD STANDS" : "💪 WE REBUILD"}
          </div>
          <div style={{ color: "white", marginBottom: "0.5rem" }}>Businesses Built: <span style={{ color: "#ffd700" }}>{state.owned.length}</span></div>
          <div style={{ color: "white", marginBottom: "0.5rem" }}>Community Treasury: <span style={{ color: "#ffd700" }}>${state.money}</span></div>
          <div style={{ color: "white", marginBottom: "1.5rem" }}>Community Trust: <span style={{ color: "#22c55e" }}>{state.trust}%</span></div>
          <div style={{ color: "#ffd700", fontSize: "2rem", fontWeight: 900 }}>SCORE: {finalScore.toLocaleString()}</div>
          <p style={{ color: "rgba(255,255,255,0.85)", fontSize: "0.75rem", marginTop: "1rem", lineHeight: 1.6 }}>
            "On May 31, 1921, the Greenwood District of Tulsa, Oklahoma — the wealthiest Black community in America — was burned to the ground by a white mob. Over 35 blocks destroyed. 300 lives lost. 10,000 left homeless. They could not burn the memory."
          </p>
        </div>
      </div>
    );
  }

  const availableEvents = shuffle(EVENTS).slice(0, 1);

  return (
    <div className="space-y-5" style={{ fontFamily: "monospace" }}>
      {/* HUD */}
      <div style={{ background: "#0a0a0f", border: "1px solid #b8860b", padding: "1rem", display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div><span style={{ color: "#b8860b" }}>TURN </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{state.turn}/{state.maxTurns}</span></div>
        <div><span style={{ color: "#b8860b" }}>TREASURY </span><span style={{ color: "#22c55e", fontWeight: 900 }}>${state.money}</span></div>
        <div><span style={{ color: "#b8860b" }}>TRUST </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{state.trust}%</span></div>
        <div><span style={{ color: "#b8860b" }}>BUSINESSES </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{state.owned.length}</span></div>
        <div><span style={{ color: "#b8860b" }}>SCORE </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{score.toLocaleString()}</span></div>
      </div>

      {/* Trust bar */}
      <div>
        <div style={{ color: "#b8860b", fontSize: "0.7rem", marginBottom: "0.25rem" }}>COMMUNITY TRUST</div>
        <div style={{ background: "rgba(255,255,255,0.1)", height: "8px", width: "100%" }}>
          <div style={{ background: state.trust > 60 ? "#22c55e" : state.trust > 30 ? "#b8860b" : "#ef4444", height: "100%", width: `${state.trust}%`, transition: "width 0.5s" }} />
        </div>
      </div>

      {/* Build businesses */}
      <div>
        <div style={{ color: "#ffd700", fontWeight: 900, marginBottom: "0.75rem", fontSize: "0.8rem" }}>▶ BUILD GREENWOOD</div>
        <div className="grid sm:grid-cols-2 gap-3">
          {BUSINESSES.map((b) => {
            const owned = state.owned.includes(b.id);
            const canAfford = state.money >= b.cost;
            return (
              <button
                key={b.id}
                onClick={() => dispatch({ type: "BUY", id: b.id })}
                disabled={owned || !canAfford}
                style={{
                  background: owned ? "rgba(34,197,94,0.1)" : canAfford ? "rgba(184,134,11,0.1)" : "rgba(255,255,255,0.03)",
                  border: `1px solid ${owned ? "#22c55e" : canAfford ? "#b8860b" : "rgba(255,255,255,0.1)"}`,
                  padding: "0.75rem",
                  cursor: owned || !canAfford ? "default" : "pointer",
                  textAlign: "left",
                  transition: "all 0.2s",
                }}
              >
                <div style={{ color: owned ? "#22c55e" : canAfford ? "#ffd700" : "rgba(255,255,255,0.55)", fontWeight: 900, fontSize: "0.85rem" }}>
                  {owned ? "✓ " : ""}{b.name}
                </div>
                <div style={{ color: "rgba(255,255,255,0.85)", fontSize: "0.7rem", marginTop: "0.25rem" }}>{b.desc}</div>
                <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", display: "flex", gap: "1rem" }}>
                  <span style={{ color: "#ef4444" }}>Cost: ${b.cost}</span>
                  <span style={{ color: "#22c55e" }}>+${b.income}/turn</span>
                  <span style={{ color: "#ffd700" }}>+{b.trust} trust</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Event log */}
      {state.eventLog.length > 0 && (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", padding: "1rem" }}>
          <div style={{ color: "#b8860b", fontSize: "0.7rem", marginBottom: "0.5rem" }}>LAST EVENT</div>
          <div style={{ color: "rgba(255,255,255,0.9)", fontSize: "0.8rem", lineHeight: 1.5 }}>{state.eventLog[0].text}</div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.7rem", display: "flex", gap: "1rem" }}>
            <span style={{ color: "#22c55e" }}>Income: +${state.eventLog[0].income}</span>
            <span style={{ color: state.eventLog[0].moneyEffect >= 0 ? "#22c55e" : "#ef4444" }}>
              Event: {state.eventLog[0].moneyEffect >= 0 ? "+" : ""}{state.eventLog[0].moneyEffect}
            </span>
            <span style={{ color: state.eventLog[0].trustEffect >= 0 ? "#ffd700" : "#ef4444" }}>
              Trust: {state.eventLog[0].trustEffect >= 0 ? "+" : ""}{state.eventLog[0].trustEffect}%
            </span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => dispatch({ type: "END_TURN" })}
          style={{
            background: "#b8860b",
            color: "#0a0a0f",
            border: "none",
            padding: "0.75rem 2rem",
            fontFamily: "monospace",
            fontWeight: 900,
            fontSize: "0.85rem",
            cursor: "pointer",
            letterSpacing: "0.1em",
            boxShadow: "0 4px 0 #7a5c0a",
          }}
        >
          END TURN ▶
        </button>
        {state.turn > 3 && (
          <button
            onClick={handleEnd}
            style={{
              background: "transparent",
              color: "rgba(255,255,255,0.75)",
              border: "1px solid rgba(255,255,255,0.4)",
              padding: "0.75rem 1.5rem",
              fontFamily: "monospace",
              fontWeight: 700,
              fontSize: "0.8rem",
              cursor: "pointer",
            }}
          >
            SUBMIT SCORE
          </button>
        )}
      </div>
    </div>
  );
}
