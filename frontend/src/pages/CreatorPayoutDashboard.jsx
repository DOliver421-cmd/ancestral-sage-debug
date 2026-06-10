import { useState, useEffect } from "react";
import AppShell from "../components/AppShell";
import api from "../lib/api";
import CreatorSplitBadge from "../components/studio/CreatorSplitBadge";

const T = {
  bg: "#080508",
  card: "#100a10",
  copper: "#b5651d",
  gold: "#d4af37",
  green: "#39ff14",
  cyan: "#00ffcc",
  text: "#ede8e0",
  muted: "#6b5e60",
};

const TIERS = [
  { key: "base", label: "Base Creator", pct: 70 },
  { key: "certified", label: "Certified Creator", pct: 75 },
  { key: "active_instructor", label: "Active Instructor", pct: 80 },
  { key: "certified_instructor", label: "Certified Instructor", pct: 85 },
];

const TIER_COLORS = {
  base: T.copper,
  certified: T.gold,
  active_instructor: T.green,
  certified_instructor: T.cyan,
};

function fmtCents(cents) {
  if (!cents && cents !== 0) return "—";
  return "$" + (cents / 100).toFixed(2);
}

export default function CreatorPayoutDashboard() {
  const [split, setSplit] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [splitRes, summaryRes] = await Promise.all([
          api.get("/creator/split"),
          api.get("/creator/payout-summary"),
        ]);
        setSplit(splitRes.data);
        setSummary(summaryRes.data);
      } catch (e) {
        setError("Failed to load payout data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const currentTierKey = split?.tier || "base";
  const nextTier = summary?.next_tier || null;
  const bookings = summary?.recent_bookings || [];
  const totalEarned = summary?.total_earned_cents || 0;

  return (
    <AppShell>
      <div style={{ minHeight: "100vh", background: T.bg, color: T.text, fontFamily: "monospace", padding: "32px 24px 80px" }}>
        <div style={{ maxWidth: 860, margin: "0 auto" }}>

          {/* Header */}
          <div style={{ marginBottom: 32 }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: T.copper, letterSpacing: "0.05em", marginBottom: 4 }}>
              💰 CREATOR PAYOUTS
            </h1>
            <p style={{ color: T.muted, fontSize: 13 }}>Your revenue split and earnings history</p>
          </div>

          {loading && <div style={{ color: T.muted }}>Loading…</div>}
          {error && <div style={{ color: "#ff4444" }}>{error}</div>}

          {!loading && !error && split && (
            <>
              {/* Big split card */}
              <div style={{ background: T.card, border: `1px solid rgba(181,101,29,0.3)`, borderRadius: 12, padding: 28, marginBottom: 28, display: "flex", flexWrap: "wrap", gap: 24, alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.2em", marginBottom: 8 }}>YOU KEEP</div>
                  <div style={{ fontSize: 52, fontWeight: 900, color: TIER_COLORS[currentTierKey] || T.copper, lineHeight: 1 }}>
                    {split.creator_pct}%
                  </div>
                  <div style={{ fontSize: 13, color: T.muted, marginTop: 6 }}>Platform takes {split.platform_pct}%</div>
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <CreatorSplitBadge split={split} nextTier={nextTier} />
                </div>
              </div>

              {/* Tier ladder */}
              <div style={{ background: T.card, border: `1px solid rgba(181,101,29,0.2)`, borderRadius: 12, padding: 24, marginBottom: 28 }}>
                <h2 style={{ fontSize: 14, color: T.copper, letterSpacing: "0.15em", marginBottom: 18, textTransform: "uppercase" }}>Tier Ladder</h2>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {TIERS.map((tier) => {
                    const active = tier.key === currentTierKey;
                    const color = TIER_COLORS[tier.key];
                    return (
                      <div
                        key={tier.key}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          padding: "10px 14px",
                          borderRadius: 8,
                          border: active ? `1px solid ${color}` : "1px solid transparent",
                          background: active ? "rgba(181,101,29,0.08)" : "transparent",
                          opacity: active ? 1 : 0.4,
                        }}
                      >
                        {!active && <span style={{ fontSize: 14 }}>🔒</span>}
                        {active && <span style={{ color, fontSize: 14 }}>★</span>}
                        <div>
                          <div style={{ fontSize: 13, color: active ? color : T.muted, fontWeight: active ? 700 : 400 }}>{tier.label}</div>
                          <div style={{ fontSize: 11, color: T.muted }}>{tier.pct}% creator split</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Level-up card */}
              {nextTier && currentTierKey !== "certified_instructor" && (
                <div style={{ background: T.card, border: `1px solid rgba(181,101,29,0.2)`, borderRadius: 12, padding: 24, marginBottom: 28 }}>
                  <h2 style={{ fontSize: 14, color: T.copper, letterSpacing: "0.15em", marginBottom: 12, textTransform: "uppercase" }}>Level Up</h2>
                  <div style={{ fontSize: 13, color: T.text, marginBottom: 6 }}>{nextTier.label}</div>
                  <div style={{ fontSize: 12, color: T.muted, marginBottom: 16 }}>{nextTier.action}</div>
                  <a
                    href={nextTier.link}
                    style={{ display: "inline-block", background: T.copper, color: "#0a0805", padding: "8px 18px", textDecoration: "none", borderRadius: 6, fontWeight: 700, fontSize: 12 }}
                  >
                    Get Started →
                  </a>
                </div>
              )}

              {/* Earnings table */}
              <div style={{ background: T.card, border: `1px solid rgba(181,101,29,0.2)`, borderRadius: 12, padding: 24 }}>
                <h2 style={{ fontSize: 14, color: T.copper, letterSpacing: "0.15em", marginBottom: 18, textTransform: "uppercase" }}>Recent Earnings</h2>
                {bookings.length === 0 ? (
                  <div style={{ color: T.muted, fontSize: 13 }}>No earnings recorded yet.</div>
                ) : (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                      <thead>
                        <tr style={{ borderBottom: `1px solid rgba(181,101,29,0.2)` }}>
                          {["Date", "Event", "Offer", `Your Cut (${split.creator_pct}%)`, `Platform (${split.platform_pct}%)`].map((h) => (
                            <th key={h} style={{ textAlign: "left", padding: "6px 10px", color: T.muted, fontWeight: 400, letterSpacing: "0.1em", fontSize: 10, textTransform: "uppercase" }}>
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {bookings.map((b, i) => (
                          <tr key={b.id || i} style={{ borderBottom: `1px solid rgba(255,255,255,0.04)` }}>
                            <td style={{ padding: "8px 10px", color: T.muted }}>
                              {b.created_at ? new Date(b.created_at).toLocaleDateString() : "—"}
                            </td>
                            <td style={{ padding: "8px 10px", color: T.text }}>{b.event_name || b.gig_title || "Booking"}</td>
                            <td style={{ padding: "8px 10px", color: T.text }}>{fmtCents(b.offer_cents)}</td>
                            <td style={{ padding: "8px 10px", color: T.green }}>{fmtCents(b.creator_cut_cents)}</td>
                            <td style={{ padding: "8px 10px", color: T.muted }}>{fmtCents(b.platform_cut_cents)}</td>
                          </tr>
                        ))}
                        <tr style={{ borderTop: `1px solid rgba(181,101,29,0.3)` }}>
                          <td colSpan={3} style={{ padding: "10px 10px", color: T.copper, fontWeight: 700, textTransform: "uppercase", fontSize: 11, letterSpacing: "0.1em" }}>
                            Total Earned
                          </td>
                          <td style={{ padding: "10px 10px", color: T.green, fontWeight: 700, fontSize: 14 }}>
                            {fmtCents(totalEarned)}
                          </td>
                          <td />
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
