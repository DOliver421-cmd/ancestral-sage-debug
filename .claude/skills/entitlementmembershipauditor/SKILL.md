---
name: entitlementmembershipauditor
description: "Verify this repo's 8-rank RBAC + feature-tier model grants and denies exactly the intended controls, across backend/roles.py, deps.py, the access gateway, legacy role strings in Mongo, and the frontend mirror."
---

# entitlementmembershipauditor

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Verify that role/tier membership grants and denies exactly the intended controls.

## The real model

**Ranks** — `backend/roles.py:26-36`, mirrored in `frontend/src/lib/roles.js:25-34`
(verified in sync at time of writing; re-verify, drift here is silent):

```
public 0 · student 1 · trial_pass 2 · instructor 3 · support_staff 4
oversight 5 · admin 6 · executive_admin 7
```

**Feature tiers** — `TIER_MIN_RANK` (`backend/roles.py:104-112`):
`free 1, basic 2, premium 3, staff 4, oversight 5, admin 6, exec 7`.

**Legacy stored values** — `LEGACY_ROLE_MAP` (`backend/roles.py:41-52`) proves
Mongo may contain `priority_member`, `site_support`, `creative_partner`, `guest`,
`creator`, `mentor`, `moderator`, `steward`, `elder`. `normalize_role`
(`:79-87`) maps these, and **silently defaults anything unknown to `student`** —
so a typo'd or renamed role is a silent permission change, never an error.

**Enforcement points (four, not one):**
1. router-local `_require_rank` copies (the majority — `backend/deps.py:1-17`);
2. `deps.require_rank` / `deps.require_tier` (`backend/deps.py:66-115`);
3. `AccessGatewayMiddleware` — 30 controls across 4 tiers
   (`backend/server.py:2783`, `backend/security/access_control/gateway.py`);
4. **frontend** `Protected` / `SupervisorProtected` (`frontend/src/App.js:158-187`),
   `frontend/src/lib/navAccess.js`, `accessGates.js`, `tiers.js`.

Only 1–3 are security. #4 is UX — but if #4 is *stricter* than the backend, a
paying user is locked out of something they bought; if *looser*, the UI advertises
what the API refuses. Both are entitlement defects.

## Known leads to confirm

- **`require_tier` appears to be a no-op for real tier names.**
  `backend/deps.py:107` only computes a rank if `min_tier` is in a hardcoded tuple
  of **role** names; the `TIER_MIN_RANK` keys (`free`, `basic`, `premium`, `staff`,
  `exec`) mostly are not, yielding `needed = 0` — admits everyone. It also never
  calls `tier_min_rank()`. Verify by execution before reporting severity.
- **`require_rank(*min_roles)` uses `min(...)`** (`backend/deps.py:83`), i.e.
  passing multiple roles gates on the **weakest**. Confirm each call site intends
  that; `require_rank("student", "admin")` admits students.
- **Gateway snapshot boundary** — the `nam`, `saga`, `executive_pipeline`, and
  `exec_tools` routers register after `wrap()` and were absent from the
  handler-requirement snapshot (`backend/server.py:2789-2822`).
- **Stale-role window on the client.** `frontend/src/lib/auth.jsx:22-32` seeds
  `user` from the `lce_user` localStorage cache and sets `loading=false`
  immediately, so `Protected` authorizes on a cached role while `/auth/me` is in
  flight. A server-side downgrade renders privileged UI until it resolves.
  The backend still enforces, so scope this as a data-exposure window / UI-truth
  defect and prove which — do not overclaim it as an authz bypass.
- **`FREE_BYOK_ROLES`** (`backend/roles.py:56-58`) grants free BYOK to
  `instructor`+ — a monetisation entitlement, so check it against
  `PRICING_VALUE_ANALYSIS.md` claims (treat that doc as an unverified claim).

## Steps

1. Build the intended matrix from `backend/roles.py` and the owner's stated
   policy — **not** from the root `*_MATRIX.md` / `*_ACCESS_*.md` files. Those are
   prior-audit output and must be re-verified, not cited as spec.
2. Enumerate the **registered** control surface (Recipe B) and record which of the
   four enforcement points guards each route.
3. Execute the matrix. For each sensitive control, one request per rank plus one
   wrong-owner request. **Assert the denials, not just the grants** — an untested
   deny is not a control. Record actual status codes: the gateway rejects with
   `403 {"error":"ACCESS_DENIED"}`
   (`backend/security/access_control/gateway.py:652-661`), handler-level checks
   with `403 "Insufficient permissions..."` (`backend/deps.py:88`), and a
   pre-startup request with `503 "Service starting up"` (`:58`) — do not score a
   503 as a successful denial.
4. Test object-level authorization separately. Rank checks do not stop IDOR.
5. Exercise legacy role values: create/emulate a user stored as `priority_member`
   or `creative_partner` and confirm the intended tier resolves, on both the API
   and the UI.
6. Diff the frontend gate against the backend gate for each control and report
   which is stricter.
7. Check the escalation surface: which routes can **write** `role`? Confirm
   default-deny, that no route lets a user raise their own rank, and that seat
   emails (`EXEC_ADMIN_EMAIL` etc.) are configured so first-registration does not
   mint an `executive_admin`.
8. Report over- and under-permissioned entitlements with severity.

## Constraints

- An entitlement claim requires an **executed** allow **and** an executed deny.
  Source inspection can only prove BROKEN.
- Full matrix execution needs a real Mongo with seeded users — unavailable in this
  container. Mark those cells `ENVIRONMENT BLOCKED`; do not infer them.
- Never carry a matrix result from one deployment to the other (anchor §0):
  cross-site SSO "finds or creates the **local** user", so roles are per-database.
- Do not modify production roles to test. Use a disposable environment.
- Cite `file:line` and paste status + body for every cell you claim.
