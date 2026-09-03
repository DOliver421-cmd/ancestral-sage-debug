import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import BackButton from "../components/BackButton";
import { MessageSquare, ArrowRight } from "lucide-react";

// Elder Council — Egyptian temple aesthetic (sand + lapis, Ankh glyph). A themed
// gateway into the existing Council/Sage chat at /council (real function, no dead end).
const PILLARS = [
  { t: "Sankofa", d: "Look back to move forward — wisdom from what came before." },
  { t: "Ubuntu", d: "I am because we are. The Council holds the community's good." },
  { t: "Maat", d: "Truth, balance, and order guide every counsel given." },
];

export default function ElderCouncil() {
  return (
    <AppShell>
    <div style={{ minHeight: "100vh", color: "#292524", background: "linear-gradient(160deg, #faf6ec, #f2ecdc 75%)" }}>
      <div
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          opacity: 0.07,
          backgroundImage: "repeating-linear-gradient(90deg, var(--egypt-sand) 0 2px, transparent 2px 40px)",
        }}
      />
      <div style={{ position: "relative", maxWidth: 900, margin: "0 auto", padding: "2.5rem 1.5rem" }}>
        <BackButton to="/dashboard" label="Depart the Temple" style={{ color: "#1f2c4d" }} />

        <div style={{ textAlign: "center", marginTop: 40 }}>
          <div style={{ fontSize: 56, color: "#1f2c4d", lineHeight: 1 }}>&#9765;</div>
          <div style={{ color: "#1f2c4d", letterSpacing: "0.3em", textTransform: "uppercase", fontWeight: 700, fontSize: 12, marginTop: 10 }}>
            Council of Elders
          </div>
          <h1 className="font-heading" style={{ fontSize: "2.4rem", fontWeight: 800, color: "#1f2c4d", marginTop: 8 }}>
            The Temple of Counsel
          </h1>
          <p style={{ color: "#57534e", maxWidth: 560, margin: "16px auto 0", lineHeight: 1.6 }}>
            Here the elders convene — ancestral wisdom, ethics, and the long view. Bring a question that matters and the Council will weigh it with you.
          </p>
          <Link to="/council" style={{ textDecoration: "none" }}>
            <button
              style={{
                marginTop: 28,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: "#1f2c4d",
                color: "#f3ead6",
                fontWeight: 800,
                padding: "0.85rem 1.6rem",
                borderRadius: 10,
                border: "none",
                cursor: "pointer",
              }}
            >
              <MessageSquare className="w-5 h-5" /> Convene the Council <ArrowRight className="w-4 h-4" />
            </button>
          </Link>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))", gap: 16, marginTop: 48 }}>
          {PILLARS.map((p) => (
            <div key={p.t} style={{ padding: 20, borderRadius: 14, border: "1px solid rgba(31,44,77,0.18)", background: "rgba(31,44,77,0.04)" }}>
              <div className="font-heading" style={{ fontWeight: 800, color: "#1f2c4d", fontSize: "1.15rem" }}>{p.t}</div>
              <div style={{ color: "#57534e", fontSize: 13, marginTop: 6, lineHeight: 1.5 }}>{p.d}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
    </AppShell>
  );
}
