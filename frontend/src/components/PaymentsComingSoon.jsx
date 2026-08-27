/**
 * PaymentsComingSoon — honest customer-facing status banner for any surface
 * whose purchase action runs through online checkout (memberships, store,
 * donations, BYOK unlock).
 *
 * Reality (verified 2026-08-27): production has no payment provider keys
 * configured, so every checkout endpoint returns 501. Until a provider is
 * switched on, these surfaces must not present a live purchase button — the
 * customer would hit a dead end. This banner is the authorized "Coming Soon"
 * treatment: it changes presentation only. No backend, product, or checkout
 * code is removed or disabled by it; when payments go live, delete the banner
 * usage and the buttons re-enable automatically (they stay wired).
 */
export default function PaymentsComingSoon({ dark = false, context = "" }) {
  const fg = dark ? "rgba(255,255,255,0.85)" : "#3d3a33";
  const muted = dark ? "rgba(255,255,255,0.6)" : "#6b675e";
  const border = dark ? "rgba(232,165,30,0.55)" : "#E8A51E";
  const bg = dark ? "rgba(232,165,30,0.12)" : "rgba(232,165,30,0.14)";
  return (
    <div
      role="status"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 12,
        background: bg,
        border: `1.5px solid ${border}`,
        borderRadius: 12,
        padding: "14px 18px",
        marginBottom: 20,
      }}
    >
      <span style={{ fontSize: 20, lineHeight: 1.3 }} aria-hidden="true">⏳</span>
      <div style={{ fontSize: 13.5, lineHeight: 1.55, color: fg }}>
        <strong>Online payments are coming soon.</strong>{" "}
        <span style={{ color: muted }}>
          Checkout isn't switched on yet, so nothing can be charged and no paid
          action is available below{context ? ` — ${context}` : ""}. Free
          accounts and all free content remain fully available.
        </span>
      </div>
    </div>
  );
}
