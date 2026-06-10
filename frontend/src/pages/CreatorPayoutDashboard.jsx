import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import AppShell from "../components/AppShell";
import { api } from "../lib/api";
import CreatorSplitBadge from "../components/studio/CreatorSplitBadge";

const T = { bg: "#080508", card: "#100a10", copper: "#b5651d", gold: "#d4af37", green: "#39ff14", cyan: "#00ffcc", text: "#ede8e0", muted: "#6b5e60", border: "rgba(181,101,29,0.2)" };

const TIERS = [
  { key: "base", label: "Base Creator", pct: 70, desc: "Default for all creators" },
  { key: "certified", label: "Certified Creator", pct: 75, desc: "Complete Creator Certification" },
  { key: "active_instructor", label: "Active Instructor", pct: 80, desc: "Publish a course with enrolled students" },
  { key: "certified_instructor", label: "Certified Instructor", pct: 85, desc: "Certified + teaching + 4.0+ rating" },
];

function fmtCents(c) {
  if (!c) return "$0";
  return `$${(c / 100).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
}

export default function CreatorPayoutDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/creator/payout-summary")
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const currentTierKey = data?.split?.tier || "base";
  const currentTierIdx = TIERS.findIndex(t => t.key === currentTierKey);

  return (
    <AppShell>
      <div style={{ background: T.bg, minHeight: "100vh", color: T.text, fontFamily: "monospace", padding: "2rem 1.5rem", maxWidth: 900, margin: "0 auto" }}>
        <h1 style={{ color: T.copper, fontSize: "1.4rem", fontWeight: 900, letterSpacing: "0.1em", marginBottom: 24 }}>💰 CREATOR PAYOUTS</h1>

        {loading ? (
          <div style={{ color: T.muted }}>Loading your earnings…</div>
        ) : (
          <>
            {/* Split badge + big display */}
            <div style={{ display: "flex", gap: 20, flexWrap: "wrap", marginBottom: 32 }}>
              <CreatorSplitBadge split={data?.split} nextTier={data?.next_tier} />
              <div style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: 12, padding: "1.2rem 1.6rem", flex: 1, minWidth: 200 }}>
                <div style={{ fontSize: 9, color: T.gold, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 8 }}>Total Earned</div>
                <div style={{ fontSize: 32, fontWeight: 900, color: T.green }}>{fmtCents(data?.total_earned_cents)}</div>
                <div style={{ fontSize: 10, color: T.muted, marginTop: 4 }}>from accepted bookings</div>
              </div>
            </div>

            {/* Tier ladder */}
            <div style={{ marginBottom: 32 }}>
              <div style={{ fontSize: 11, color: T.copper, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12, borderBottom: `1px solid ${T.border}`, paddingBottom: 8 }}>Tier Ladder</div>
              {TIERS.map((tier, i) => {
                const isCurrent = tier.key === currentTierKey;
                const isPast = i < currentTierIdx;
                return (
                  <div key={tier.key} style={{ background: T.card, border: `1px solid ${isCurrent ? T.copper : T.border}`, borderRadius: 8, padding: "12px 16px", marginBottom: 8, opacity: (!isCurrent && !isPast) ? 0.45 : 1, display: "flex", alignItems: "center", gap: 16 }}>
                    <div style={{ fontSize: 20, fontWeight: 900, color: isCurrent ? T.copper : isPast ? T.green : T.muted, minWidth: 48 }}>{tier.pct}%</div>
                    <div>
                      <div style={{ color: isCurrent ? T.copper : T.text, fontSize: 12, fontWeight: isCurrent ? 900 : 400 }}>{tier.label} {isCurrent && "← YOU"}</div>
                      <div style={{ color: T.muted, fontSize: 10, marginTop: 2 }}>{tier.desc}</div>
                    </div>
                    {isPast && <div style={{ marginLeft: "auto", color: T.green, fontSize: 14 }}>✓</div>}
                    {!isCurrent && !isPast && <div style={{ marginLeft: "auto", color: T.muted, fontSize: 14 }}>🔒</div>}
                  </div>
                );
              })}
            </div>

            {/* Level up card */}
            {data?.next_tier && currentTierKey !== "certified_instructor" && (
              <div style={{ background: "rgba(181,101,29,0.08)", border: `1px solid ${T.copper}`, borderRadius: 10, padding: "16px 20px", marginBottom: 32 }}>
                <div style={{ color: T.copper, fontSize: 11, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 8 }}>Level Up</div>
                <div style={{ color: T.text, fontSize: 13, marginBottom: 4 }}>Next: <strong>{data.next_tier.label}</strong></div>
                <div style={{ color: T.muted, fontSize: 12, marginBottom: 12 }}>{data.next_tier.action}</div>
                <Link to={data.next_tier.link} style={{ background: T.copper, color: "#fff", padding: "8px 16px", fontFamily: "monospace", fontSize: 11, fontWeight: 900, textDecoration: "none", borderRadius: 4 }}>Get Started →</Link>
              </div>
            )}

            {/* Earnings table */}
            <div>
              <div style={{ fontSize: 11, color: T.copper, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 12, borderBottom: `1px solid ${T.border}`, paddingBottom: 8 }}>Recent Earnings</div>
              {(!data?.recent_bookings || data.recent_bookings.length === 0) ? (
                <div style={{ color: T.muted, fontSize: 12, padding: "20px 0" }}>No accepted bookings yet. List yourself on <Link to="/band" style={{ color: T.copper }}>Band on a Page</Link>.</div>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${T.border}` }}>
                        {["Date", "Event", "Offer", `Your Cut (${data?.split?.creator_pct}%)`, "Platform (30%)"].map(h => (
                          <th key={h} style={{ padding: "8px 12px", color: T.gold, textAlign: "left", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", fontSize: 9 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_bookings.map((b, i) => (
                        <tr key={b.id || i} style={{ borderBottom: `1px solid rgba(181,101,29,0.08)` }}>
                          <td style={{ padding: "10px 12px", color: T.muted }}>{b.event_date || "—"}</td>
                          <td style={{ padding: "10px 12px" }}>{b.event_name || "—"}</td>
                          <td style={{ padding: "10px 12px", color: T.text }}>{fmtCents(b.offer_cents)}</td>
                          <td style={{ padding: "10px 12px", color: T.green }}>{fmtCents(b.creator_cut_cents)}</td>
                          <td style={{ padding: "10px 12px", color: T.muted }}>{fmtCents(b.platform_cut_cents)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
