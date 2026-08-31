/**
 * PaymentsComingSoon — honest customer-facing status banner for any surface
 * whose purchase action runs through online checkout (memberships, store,
 * donations, BYOK unlock).
 *
 * Reality (verified 2026-08-27): production had no payment provider keys
 * configured, so every checkout endpoint returned 501 and the banner was
 * hardcoded into five surfaces with `disabled={true}` buttons.
 *
 * 2026-08-28 repair: the gating now follows the LIVE backend state instead of
 * a hardcoded constant. `/api/payments/products` publicly reports
 * `payments_enabled` (true the moment LEMON_SQUEEZY_API_KEY + STORE_ID — or a
 * fallback provider — resolve in the deployed process). While it is false the
 * banner shows exactly as before; when the provider keys go live the banner
 * disappears and the paid buttons re-enable on the next page load — no code
 * revert, no redeploy of the frontend needed. If the backend is unreachable
 * the flag stays false (honest default: never promise a purchase we can't
 * complete).
 */
import { useEffect, useState } from "react";
import { API } from "../lib/api";

// Module-level cache — one request per page load no matter how many surfaces
// ask, and every subscriber updates together.
let _stateKnown = false;
let _enabled = false;
const _subscribers = new Set();

function refreshPaymentsEnabled() {
  if (_stateKnown) return;
  fetch(`${API}/payments/products`)
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => {
      _enabled = !!(d && d.payments_enabled);
      _stateKnown = true;
      _subscribers.forEach((fn) => fn(_enabled));
    })
    .catch(() => {
      // Backend unreachable → stay honest: not enabled.
      _enabled = false;
      _stateKnown = true;
      _subscribers.forEach((fn) => fn(false));
    });
}

/** Live payments flag for purchase gating. False until the backend confirms. */
export function usePaymentsEnabled() {
  const [enabled, setEnabled] = useState(_stateKnown ? _enabled : false);
  useEffect(() => {
    _subscribers.add(setEnabled);
    refreshPaymentsEnabled();
    return () => {
      _subscribers.delete(setEnabled);
    };
  }, []);
  return enabled;
}

export default function PaymentsComingSoon({ dark = false, context = "" }) {
  const enabled = usePaymentsEnabled();
  // Payments are live — the banner must not block a working checkout.
  if (enabled) return null;

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
