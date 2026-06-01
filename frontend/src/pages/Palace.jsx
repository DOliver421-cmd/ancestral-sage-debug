import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import BackButton from "../components/BackButton";
import SovereignAvatar from "../components/SovereignAvatar";
import { BookOpen, Brain, MessageSquare, ShoppingBag, Sparkles, HandHelping, ArrowRight } from "lucide-react";

// Members' Palace — Zamunda aesthetic (deep emerald + gold). A real members'
// space: live partnership standing + gateways to existing, working features
// (no dead ends, not a toy). Themed via the --zam-/--wai- tokens.
const HALLS = [
  { to: "/modules", label: "Hall of Learning", desc: "Your curriculum & courses", icon: BookOpen },
  { to: "/ai", label: "The Oracle", desc: "Your AI tutor & guide", icon: Sparkles },
  { to: "/dashboard", label: "Hall of Trials", desc: "Daily puzzle — earn points", icon: Brain },
  { to: "/elder-council", label: "Council of Elders", desc: "Ancestral wisdom & counsel", icon: MessageSquare },
  { to: "/app/more", label: "The Exchange", desc: "M.O.R.E. — community mutual aid", icon: HandHelping },
  { to: "/store", label: "The Market", desc: "Store & creations", icon: ShoppingBag },
];

export default function Palace() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.get("/partnership/status").then((r) => setStatus(r.data)).catch(() => {});
  }, []);

  const pts = status?.points ?? 0;
  const next = status?.next_tier;
  const toNext = status?.points_to_next ?? 0;
  const tierMin = status?.tier_min ?? 0;
  const nextThreshold = next ? pts + toNext : null;
  const pct = next ? Math.min(100, Math.round(((pts - tierMin) / Math.max(1, nextThreshold - tierMin)) * 100)) : 100;

  return (
    <div
      style={{
        minHeight: "100vh",
        color: "var(--wai-text)",
        background:
          "radial-gradient(1200px 600px at 50% -10%, rgba(201,168,76,0.18), transparent), linear-gradient(160deg, #06251c, #0a0a0f 70%)",
      }}
    >
      <div
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          opacity: 0.06,
          backgroundImage: "repeating-linear-gradient(45deg, var(--zam-gold) 0 2px, transparent 2px 22px)",
        }}
      />
      <div style={{ position: "relative", maxWidth: 1100, margin: "0 auto", padding: "2.5rem 1.5rem" }}>
        <BackButton to="/dashboard" label="Leave the Palace" style={{ color: "var(--zam-gold)" }} />

        <div className="flex items-center gap-4" style={{ marginTop: 24 }}>
          <SovereignAvatar size={64} name={user?.full_name || "Member"} />
          <div>
            <div style={{ color: "var(--zam-gold)", letterSpacing: "0.2em", fontWeight: 700, fontSize: 12, textTransform: "uppercase" }}>
              Members' Palace
            </div>
            <h1 className="font-heading" style={{ fontSize: "2.25rem", fontWeight: 800, color: "var(--wai-gold-light)" }}>
              Welcome, {user?.full_name?.split(" ")[0] || "Partner"}.
            </h1>
            <p style={{ color: "var(--wai-muted)", marginTop: 4 }}>You are a partner here, not a guest. Walk the halls.</p>
          </div>
        </div>

        <div style={{ marginTop: 28, padding: 24, borderRadius: 18, border: "1px solid var(--wai-border)", background: "rgba(212,175,55,0.06)" }}>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <div style={{ color: "var(--zam-gold)", fontSize: 12, letterSpacing: "0.15em", textTransform: "uppercase", fontWeight: 700 }}>
                Your Standing
              </div>
              <div className="font-heading" style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--wai-gold-light)" }}>
                {status?.tier || "Seed I"}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="font-heading" style={{ fontSize: "1.6rem", fontWeight: 800 }}>{pts}</div>
              <div style={{ color: "var(--wai-muted)", fontSize: 12, textTransform: "uppercase" }}>points</div>
            </div>
          </div>
          <div style={{ height: 10, background: "rgba(255,255,255,0.08)", borderRadius: 999, marginTop: 14, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${pct}%`, background: "linear-gradient(90deg, var(--zam-gold), var(--wai-gold-light))", transition: "width .5s" }} />
          </div>
          <div style={{ color: "var(--wai-muted)", fontSize: 12, marginTop: 8 }}>
            {next ? `${toNext} points to ${next}` : "You have reached the summit."}
            {status?.membership_unlocked && <span style={{ color: "var(--zam-gold)", fontWeight: 700 }}> · Free membership unlocked</span>}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, marginTop: 28 }}>
          {HALLS.map((h) => {
            const Icon = h.icon;
            return (
              <Link key={h.to} to={h.to} style={{ textDecoration: "none", color: "inherit" }}>
                <div
                  style={{ padding: 20, borderRadius: 16, border: "1px solid var(--wai-border)", background: "rgba(255,255,255,0.02)", transition: "all .2s", height: "100%" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--zam-gold)";
                    e.currentTarget.style.background = "rgba(212,175,55,0.07)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--wai-border)";
                    e.currentTarget.style.background = "rgba(255,255,255,0.02)";
                  }}
                >
                  <Icon style={{ color: "var(--zam-gold)" }} className="w-6 h-6" />
                  <div className="font-heading" style={{ fontWeight: 800, fontSize: "1.1rem", marginTop: 10, color: "var(--wai-gold-light)" }}>
                    {h.label}
                  </div>
                  <div style={{ color: "var(--wai-muted)", fontSize: 13, marginTop: 4 }}>{h.desc}</div>
                  <div style={{ color: "var(--zam-gold)", fontSize: 12, fontWeight: 700, marginTop: 12, display: "flex", alignItems: "center", gap: 6 }}>
                    Enter <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
