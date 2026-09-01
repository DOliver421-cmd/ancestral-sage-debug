# MoreHelp API Operationalization Handoff

## Target

- Repository: `DOliver421-cmd/ancestral-sage-debug`
- Branch: `main`
- Live target: `https://charming-analysis-morehelpcenter.up.railway.app`
- Latest pushed commit: `f3168354 route payment webhook through Lemon Squeezy`

## Runtime Inventory

The current in-process FastAPI schema contains:

- 616 paths
- 693 HTTP operations
- 328 GET operations
- 365 POST, PUT, PATCH, and DELETE operations
- 0 duplicate method/path registrations

## Live Execution Completed

### Unauthenticated GET matrix

All 328 GET operations were requested against the live target using safe path
parameter probes. Latest status distribution:

| Status | Count |
| --- | ---: |
| 200 | 46 |
| 400 | 3 |
| 401 | 263 |
| 404 | 11 |
| 410 | 1 |
| 422 | 4 |

There were zero live GET server errors, connection failures, timeouts, or SPA
HTML fallbacks in the final pass.

### Unauthenticated mutation matrix

All 365 POST, PUT, PATCH, and DELETE operations were called with empty JSON and
without authentication. This exercised route registration, request validation,
and unauthenticated authorization behavior. The pre-repair matrix had two
server-class results:

- `POST /api/payments/webhook`: inline Stripe-only handler returned 503.
- `POST /api/bridge/receive`: returned 500 when exercised with the test double.

The payment webhook is repaired in `f3168354`. The bridge test failure came
from the test double lacking Motor's `replace_one`, at `routers/bridge.py:267`;
it did not establish a production bridge handler defect. This endpoint requires
a valid configured bridge/database path to complete runtime verification.

### Authenticated student GET matrix

A temporary live student account was created through `/api/auth/register`,
logged in through `/api/auth/login`, and used to request all 328 GET operations.
The account was then sent through `/api/auth/account` self-erasure. The status
distribution before the latest deployment completed was:

| Status | Count |
| --- | ---: |
| 200 | 144 |
| 400 | 3 |
| 401 | 1 |
| 403 | 132 |
| 404 | 22 |
| 410 | 1 |
| 422 | 6 |
| 500 | 18 |
| 503 | 1 |

The 14 AI-router 500s were repaired by `9c067113` and subsequently verified on
the live target as 401 rather than 500. The remaining social and playlist 500s
were repaired by `6517bde4` and subsequently verified live as 401 rather than
500. The final unauthenticated GET matrix confirms no remaining GET 5xx.

## Repairs Delivered

- `68c35e25`: fixed duplicate API router inclusion and routed Sovereign chat
  through the existing provider-neutral LLM gateway.
- `9693dc6d`: clarified authoritative MoreHelp operating policy and retained
  WAI material as historical/non-authoritative.
- `a95a527a`: removed unused OpenCode configuration.
- `f6ef453d`: binds shared database and canonical dependencies at startup.
- `eccb5886`: CRM uses the canonical authentication dependency.
- `dabff625`, `cf5c967b`, `a786367d`: registered non-conflicting frontend API
  router modules after resolving registration ordering.
- `a412f11d`: binds all mounted modular routers to shared runtime dependencies.
- `96974ea5`, `9c067113`: fixes explicit modular AI-router binding.
- `6517bde4`: fixes `User.id` versus legacy Mongo `_id` access in Social and
  Playlist APIs.
- `15af31ee`: effective customer portal delegates to the existing
  provider-aware payment implementation.
- `f3168354`: effective payment webhook delegates to the existing signed,
  idempotent Lemon Squeezy implementation.

## Current Verification State

### Verified

- Live endpoint registration is no longer producing HTML SPA fallbacks for the
  complete GET inventory.
- Final unauthenticated GET matrix has zero 5xx/timeouts.
- `scripts/tools/verify_endpoints.py` passes 14/14 focused route/auth/response
  checks locally.
- Modular router dependencies are bound in the normal server import path.
- Social and Playlist authenticated empty-state responses return their expected
  200 response structures locally.
- Lemon webhook returns explicit 404 when unconfigured and 400 on invalid
  signature locally; it no longer routes through the Stripe-only handler.

### Not Yet Complete

The full API operationalization task is not complete until the following are
executed on the live deployment:

1. Re-run all 365 mutation operations after `f3168354` is deployed, with
   contract-valid payloads for each route rather than the safe empty-body pass.
2. Re-run the authenticated 328-GET matrix after the latest deploy.
3. Establish executive and admin test identities to cover role-success paths
   without using an owner account or exposing credentials.
4. Execute database write/read/delete round trips for every mutating API.
5. Execute real Lemon Squeezy webhook signature, checkout, fulfillment, and
   owner-exemption flows using approved non-production test records.
6. Execute media upload/download and external provider integrations with their
   configured approved credentials.
7. Verify each frontend call contract in a browser: method, headers, request
   shape, response rendering, and error presentation.

No secrets, test tokens, credentials, or payment-provider values are recorded
in this file.