import { useState } from "react";

const SCENARIOS = [
  {
    title: "Payday Loan Trap",
    situation: "You need $300 for a car repair to keep your job. A payday lender offers $300 — just pay back $375 in two weeks. Seems small. What do you do?",
    options: [
      { text: "Take the payday loan — $75 isn't that bad", good: false, moneyEffect: -75, explanation: "That's a 650% APR. Miss one payment? Fees stack and the debt traps you in a cycle. This is how people owe $1,000 on a $300 loan." },
      { text: "Ask your employer for a payroll advance", good: true, moneyEffect: 0, explanation: "Many employers do this. Zero interest, no trap. Ask before you borrow from a lender." },
      { text: "Call a local credit union about an emergency loan", good: true, moneyEffect: -15, explanation: "Credit union emergency loans often cap at 18-28% APR. Costs $15 instead of $75. That's the right move." },
    ],
  },
  {
    title: "Rent-to-Own Furniture",
    situation: "You need a couch and a TV. Rent-to-own store offers: only $29/week, no credit check. 'Own it in 2 years.' The set would cost $800 at a regular store. What do you do?",
    options: [
      { text: "Sign up — $29/week sounds affordable", good: false, moneyEffect: -1516, explanation: "$29 × 104 weeks = $3,016 for $800 worth of furniture. You paid 3.7x retail. Rent-to-own is legal predatory lending." },
      { text: "Save $50/month and buy it outright in 4 months", good: true, moneyEffect: -200, explanation: "Waiting costs $200 in a short-term storage unit max. You save over $800 vs. rent-to-own. Patience is a financial weapon." },
      { text: "Check Facebook Marketplace / thrift stores first", good: true, moneyEffect: -150, explanation: "Quality used furniture at 10-20% of retail price. No credit check, no trap, money in your pocket." },
    ],
  },
  {
    title: "Store Credit Card",
    situation: "At checkout, the cashier offers you a store credit card — 'Save 20% today on your $200 purchase!' The card has 29.99% APR. You plan to pay it off next month. What do you do?",
    options: [
      { text: "Open the card — I'll pay it off right away", good: false, moneyEffect: -40, explanation: "Most people don't. Store cards have the highest APRs in the industry. One missed month = you lost the 20% and more. This is how retailers trap you." },
      { text: "Decline and pay cash or existing card", good: true, moneyEffect: -200, explanation: "You paid full price but you didn't open a high-APR trap. If your existing card is under 20% and you pay in full — that's the win." },
      { text: "Ask if the 20% discount applies without opening a card", good: true, moneyEffect: -160, explanation: "Sometimes it applies with a coupon or loyalty app. Always ask. The worst they say is no." },
    ],
  },
  {
    title: "Car Title Loan",
    situation: "You're $500 short on rent. A title loan place will give you $1,000 using your car as collateral — 30-day term at 25% monthly interest. What do you do?",
    options: [
      { text: "Take the title loan — just for 30 days", good: false, moneyEffect: -250, explanation: "25% monthly = 300% APR. If you can't repay in 30 days, they roll it over and fees compound. 20% of title loan borrowers lose their car." },
      { text: "Call 211 for emergency rental assistance programs", good: true, moneyEffect: 0, explanation: "211 connects you to emergency assistance — utility help, rental aid, food banks. Free money you earned as a taxpayer. Use it." },
      { text: "Negotiate directly with your landlord for 2-week extension", good: true, moneyEffect: 0, explanation: "Most landlords prefer a conversation to the eviction process. Ask for time. The worst answer is no — not homelessness." },
    ],
  },
  {
    title: "Buy Here Pay Here Car Lot",
    situation: "You need a car. A 'Buy Here Pay Here' lot offers a 2015 sedan for $8,000 — $100/week, no credit check. A credit union offers the same car for $7,500 at 12% APR with a credit check you're nervous about. What do you do?",
    options: [
      { text: "Buy Here Pay Here — easier, no credit check", good: false, moneyEffect: -2400, explanation: "$100/week × 52 × 2 years = $10,400 for a $7,500 car. That's $2,900 extra. BHPH lots often embed GPS kill switches to repossess remotely." },
      { text: "Apply for the credit union loan anyway", good: true, moneyEffect: -900, explanation: "Even at 12% APR you pay ~$900 in interest on $7,500 over 2 years. That's $2,000 less than BHPH. A credit check is not the enemy — predatory APRs are." },
    ],
  },
  {
    title: "Insurance Add-On",
    situation: "Buying a phone on a payment plan. The rep offers 'Damage Protection Insurance' for $15/month. Your homeowners/renters insurance may already cover your phone. What do you do?",
    options: [
      { text: "Add the insurance — phones are expensive to fix", good: false, moneyEffect: -180, explanation: "$15/month × 24 months = $360 for a plan that often pays less than replacement cost and has high deductibles. You likely paid for a benefit you already have." },
      { text: "Check your renters/homeowners policy first", good: true, moneyEffect: -20, explanation: "Many policies cover electronics. A quick call saves $360. Take 10 minutes before you spend $15/month." },
    ],
  },
];

export default function DontGetPlayed({ onGameEnd }) {
  const [index, setIndex] = useState(0);
  const [money, setMoney] = useState(1000);
  const [selected, setSelected] = useState(null);
  const [log, setLog] = useState([]);
  const [done, setDone] = useState(false);

  const scenario = SCENARIOS[index];

  const choose = (opt) => {
    if (selected !== null) return;
    setSelected(opt);
    setMoney((m) => Math.max(0, m + opt.moneyEffect));
    setLog((l) => [...l, { scenario: scenario.title, choice: opt.text, good: opt.good, effect: opt.moneyEffect }]);
  };

  const next = () => {
    setSelected(null);
    if (index + 1 >= SCENARIOS.length) {
      setDone(true);
      const finalScore = money + log.filter((l) => l.good).length * 50;
      onGameEnd({ score: finalScore });
    } else {
      setIndex((i) => i + 1);
    }
  };

  if (done) {
    const good = log.filter((l) => l.good).length;
    const finalScore = money + good * 50;
    return (
      <div style={{ fontFamily: "monospace", background: "#0a0a0f", border: "2px solid #b8860b", padding: "2rem" }}>
        <div style={{ color: "#ffd700", fontSize: "1.3rem", fontWeight: 900, marginBottom: "1rem" }}>
          {good >= 5 ? "💰 YOU CAN'T BE PLAYED" : good >= 3 ? "⚡ SHARP MIND" : "📚 KEEP LEARNING"}
        </div>
        <div style={{ color: "white", marginBottom: "0.5rem" }}>Smart choices: <span style={{ color: "#22c55e" }}>{good}/{SCENARIOS.length}</span></div>
        <div style={{ color: "white", marginBottom: "0.5rem" }}>Money saved: <span style={{ color: "#ffd700" }}>${money}</span></div>
        <div style={{ color: "#ffd700", fontSize: "1.8rem", fontWeight: 900, marginTop: "1rem" }}>SCORE: {finalScore.toLocaleString()}</div>
        <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "0.75rem", marginTop: "1rem", lineHeight: 1.6 }}>
          Predatory financial products cost Black and Brown families billions annually. Knowledge is the first defense. Share this game.
        </p>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "monospace" }} className="space-y-5">
      {/* HUD */}
      <div style={{ background: "#0a0a0f", border: "1px solid #b8860b", padding: "1rem", display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        <div><span style={{ color: "#b8860b" }}>SCENARIO </span><span style={{ color: "#ffd700", fontWeight: 900 }}>{index + 1}/{SCENARIOS.length}</span></div>
        <div><span style={{ color: "#b8860b" }}>WALLET </span><span style={{ color: money > 800 ? "#22c55e" : money > 500 ? "#ffd700" : "#ef4444", fontWeight: 900 }}>${money}</span></div>
        <div><span style={{ color: "#b8860b" }}>SMART MOVES </span><span style={{ color: "#22c55e", fontWeight: 900 }}>{log.filter((l) => l.good).length}</span></div>
      </div>

      {/* Scenario */}
      <div style={{ background: "rgba(184,134,11,0.05)", border: "1px solid rgba(184,134,11,0.3)", padding: "1.5rem" }}>
        <div style={{ color: "#ffd700", fontWeight: 900, marginBottom: "0.75rem" }}>▶ {scenario.title}</div>
        <p style={{ color: "rgba(255,255,255,0.8)", lineHeight: 1.7, fontSize: "0.9rem" }}>{scenario.situation}</p>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {scenario.options.map((opt, i) => {
          const isSelected = selected?.text === opt.text;
          const showResult = selected !== null;
          return (
            <button
              key={i}
              onClick={() => choose(opt)}
              disabled={selected !== null}
              style={{
                width: "100%",
                textAlign: "left",
                padding: "1rem",
                background: showResult
                  ? isSelected
                    ? opt.good ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)"
                    : opt.good ? "rgba(34,197,94,0.07)" : "rgba(255,255,255,0.02)"
                  : "rgba(255,255,255,0.03)",
                border: `1px solid ${showResult
                  ? isSelected
                    ? opt.good ? "#22c55e" : "#ef4444"
                    : opt.good ? "rgba(34,197,94,0.4)" : "rgba(255,255,255,0.1)"
                  : "rgba(184,134,11,0.3)"}`,
                cursor: selected ? "default" : "pointer",
                transition: "all 0.2s",
              }}
            >
              <div style={{ color: showResult ? (opt.good ? "#22c55e" : "#ef4444") : "#ffd700", fontWeight: 700, fontSize: "0.85rem" }}>
                {showResult ? (opt.good ? "✓ " : "✗ ") : `${String.fromCharCode(65 + i)}. `}{opt.text}
              </div>
              {showResult && (
                <div style={{ color: "rgba(255,255,255,0.6)", fontSize: "0.75rem", marginTop: "0.5rem", lineHeight: 1.6 }}>
                  {opt.explanation}
                  {opt.moneyEffect !== 0 && (
                    <span style={{ color: opt.moneyEffect > 0 ? "#22c55e" : "#ef4444", fontWeight: 700, marginLeft: "0.5rem" }}>
                      ({opt.moneyEffect > 0 ? "+" : ""}{opt.moneyEffect})
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {selected && (
        <button
          onClick={next}
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
          {index + 1 >= SCENARIOS.length ? "SEE RESULTS ▶" : "NEXT SCENARIO ▶"}
        </button>
      )}
    </div>
  );
}
