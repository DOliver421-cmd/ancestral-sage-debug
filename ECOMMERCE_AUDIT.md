# ECOMMERCE AUDIT (Phase 20)

**Method:** source inspection this session. No payment was processed — every money path is SRC-level unless noted.

## Provider architecture (SRC)

- **Lemon Squeezy (primary)** — digital products + subscriptions. **Gumroad (fallback)** — one-time only. Stripe removed by owner decision (no Stripe SDK/keys in payments router).
- Checkout: `POST /payments/checkout` (auth) → provider checkout URL; returns `{url, session_id}`; audit event on creation; 501 when providers unconfigured; physical products → 501 (by design, no fulfillment).
- Webhook: `POST /payments/webhook` — HMAC-SHA256 verified; handles **`order_created` only**.

## Products & pricing (verified, routers/payments.py)

member $9/mo · plus $15/mo · pro $29/mo · patron $59/mo · more membership $9.99/mo/$79.99/yr · BYOK $3 one-time · sanctuary trial $3 (Plus for 3d33m33s) · donation · scholarship · arena workbook/guide/license/album · credential cert $25 (physical → not sold online).

## Money-path status table

| Path | Status | Notes |
|---|---|---|
| Checkout session creation | IMPLEMENTED (SRC) | LS → Gumroad fallback |
| Webhook signature | IMPLEMENTED (SRC) | HMAC verified |
| Tier grant on order | IMPLEMENTED (SRC) | upgrade-only; notify + audit |
| BYOK grant on order | IMPLEMENTED (SRC) | sets `byok_enabled` |
| Scholarship pledge | IMPLEMENTED (SRC) | milestone-based |
| Billing history | IMPLEMENTED (SRC) | `GET /payments/history` |
| Customer portal | IMPLEMENTED (SRC) | LS customer portal URL |
| **Subscription cancellation** | **BROKEN (gap)** | no `subscription_cancelled`/`updated` handling → tier persists after cancel |
| **Refund** | **BROKEN (gap)** | refunded orders still recorded as paid; no downgrade |
| **Webhook idempotency** | **PARTIAL** | duplicate deliveries insert duplicate payment rows (tier grant upgrade-only limits damage) |
| Unregistered buyer | PARTIAL | payment row stores `user_id: None`; grants on email match only when buyer registers |
| Physical merchandise | BY DESIGN UNAVAILABLE | 501 |
| Admin refund tooling | IMPLEMENTED (SRC) | site-credit + cash refund routes, admin-only |
| **Real end-to-end money flow** | **NOT VERIFIED** | no keys/env; no automated payment tests exist |

## Top risks

1. **Cancellation/refund not handled** (P0) — subscribers keep entitlements after they stop paying.
2. **BYOK free activation** (P1) — see SECURITY_AUDIT.md.
3. **No automated webhook/payment tests** (P1) — add at least signature + order_created + cancelled unit tests before launch, and run one real $3 checkout in production.
