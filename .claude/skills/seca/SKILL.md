---
name: seca
description: "Security audit of this FastAPI+Mongo app: three competing auth mechanisms across 50 routers, the access-gateway snapshot boundary, CORS wildcard, in-process rate limiting, secret handling, and cross-site SSO."
---

# seca — security audit

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Systematic review for security defects. The structural problem here is that
authorization is implemented **three different ways** across 50 routers, so a
per-route review is mandatory — a review of the shared helpers covers a minority
of the surface.

## The three authorization mechanisms

1. **Router-local copies.** `backend/deps.py:1-17` states plainly that "every
   router currently re-implements `_require_rank()` and `_dep_current_user()`
   because of the `bind()` pattern." These are the majority and they can drift
   individually.
2. **Canonical deps** — `dep_current_user`, `require_rank`, `require_tier`
   (`backend/deps.py:56-115`).
3. **`AccessGatewayMiddleware`** — outermost middleware, registered by
   `access_gateway.wrap(app)` (`backend/server.py:2783`), 30 controls monitored
   across 4 tiers.

## Confirmed / high-priority leads (verify each, do not copy the conclusion)

- **`require_tier` looks broken open.** `backend/deps.py:107` computes `needed`
  only if `min_tier` is in a hardcoded tuple of **role names**
  (`student`, `trial_pass`, `instructor`, `support_staff`, `oversight`, `admin`,
  `executive_admin`). The tier names it is documented to take — and the keys of
  `TIER_MIN_RANK` (`backend/roles.py:104-112`: `free`, `basic`, `premium`,
  `staff`, `oversight`, `admin`, `exec`) — mostly are **not** in that tuple, so
  `needed = 0` and the dependency admits everyone. `require_tier` also ignores
  `tier_min_rank()` entirely. Confirm by execution, then report severity.
- **Gateway snapshot boundary.** `wrap()`
  (`backend/security/access_control/gateway.py:628-650`) snapshots public route
  patterns and handler-derived requirements at call time (133 public / 541 with
  requirements, observed). `nam`, `saga`, `executive_pipeline`, `exec_tools` are
  included **after** (`backend/server.py:2789, 2798, 2809, 2818`) — the four
  highest-authority routers were in neither snapshot. Determine empirically
  whether an unknown route is allowed or denied.
- **First-user privilege escalation.** Importing the app logs
  `No executive admin email is configured (EXEC_ADMIN_EMAIL /
  BACKUP_EXEC_ADMIN_EMAIL / NAM_EXEC_EMAIL all empty). On a fresh database the
  first registered user would become executive_admin.` Confirm the seat emails are
  set in every deployed environment.
- **Unencrypted denial audit.** `AUDIT_ENCRYPTION_KEY is not set — denial records
  are stored UNENCRYPTED` (logged at import). Compliance-relevant.
- **`JWT_SECRET` unset does not stop the app.** It prints
  `FATAL: JWT_SECRET is not set...` and continues. Verify what tokens it then
  mints — a derived/ephemeral secret means sessions die on restart; a constant
  default would be critical.
- **CORS.** Observed middleware config: `allow_origins=['*']` with
  `allow_credentials=False`. Since auth is a `Bearer` header from `localStorage`
  (not a cookie), `allow_credentials=False` does not stop a token being replayed
  from any origin. Establish whether the wildcard is intentional and whether it
  should be pinned to the two known domains.
- **Rate limiting is in-process.** `backend/server.py:310` — a `defaultdict`
  "Simple in-memory rate limit (per IP, per route) — replace with redis in true
  HA prod". It resets on restart and is per-worker. With `>1` uvicorn worker or a
  Railway restart it is trivially defeated. Confirm the deployed worker count.
- **Cross-site SSO.** `backend/cross_site_auth.py` — 5-minute single-use tokens
  signed with `CROSS_SITE_SECRET`, redirect targets validated against
  `ALLOWED_PARTNER_DOMAINS` (`:46-51`). Verify: single-use is actually enforced
  (where is consumption recorded, and does it survive a restart?), signature
  comparison is constant-time (`hmac.compare_digest`), `CROSS_SITE_SECRET`
  unset does not degrade to an unsigned accept, and the open-redirect check
  cannot be bypassed by subdomain/userinfo tricks. Both
  `/auth/cross-site-token` (`backend/routers/auth.py:1047`) and
  `/auth/cross-site-login` (`:1064`) are served here.
- **Route shadowing as an authz hazard.** Seven live `(method,path)` duplicates
  (Recipe C) include `DELETE /admin/users/{uid}`,
  `GET /admin/users/{uid}/sessions`, and `GET /exec/control/route-access`. If the
  winning handler has the weaker gate, the stronger one is decorative. Test which
  handler runs.
- **Token at rest.** `lce_token` in `localStorage` (`frontend/src/lib/api.js:51-55`)
  is XSS-readable by design. Given 283 frontend files, audit for `dangerouslySetInnerHTML`
  and `react-markdown` rendering of user-supplied content.

## Steps

1. Enumerate the **registered** surface (Recipe B), then classify every route by
   which of the three mechanisms guards it. Flag any route with none.
2. Execute a rank matrix per sensitive route: unauthenticated, `student`,
   `instructor`, `support_staff`, `oversight`, `admin`, `executive_admin`, and a
   wrong-owner identity. Assert both allow and **deny**. An untested deny is not
   a control.
3. Test object-level authorization (IDOR): can `student A` read/modify
   `student B`'s resource by changing an id? Handler-level rank checks do not
   provide this.
4. Scan for secret exposure in logs, error responses, and the git diff. Report
   any plaintext credential found for **rotation**, never reuse it.
5. Review Mongo query construction for operator injection — a raw request dict
   passed into a filter lets a caller supply `$ne`/`$gt`/`$where`.
6. Check `redirect_slashes=False` (`backend/server.py:208`) does not create a
   path variant that bypasses a prefix-matching gate.
7. Report by severity with a concrete, minimal fix and the blast radius.

## Constraints

- Prove each finding by execution where the environment allows; where it does not
  (no `mongod` here), mark `ENVIRONMENT BLOCKED` rather than asserting.
- Never print or commit secrets. Name the variable, not the value.
- Do not run destructive or account-locking probes against a live deployment.
- Do not assume the morehelp.center deployment shares this one's environment
  variables, seat emails, or gateway state (anchor §0).
- Cite `file:line` and paste the request/response evidence for each finding.
