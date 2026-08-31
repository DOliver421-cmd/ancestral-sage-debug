---
name: fra
description: "Functional reality audit — does a feature actually fulfil its purpose for a human user of this WAI app, traced click → request → handler → Mongo → response → render. The strictest 'does it work' gate."
---

# fra — functional reality audit

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Determine whether a feature actually fulfils its intended purpose for a human
user. This is the strictest gate in the set: it fails on any broken link in the
chain, including links that look fine in source.

## The chain you must trace (all six links)

1. **Control** — the actual element in `frontend/src/pages/**` the user clicks.
2. **Request** — the `api.*` call it fires. The client is the single axios
   instance in `frontend/src/lib/api.js:23`; the `lce_token` bearer is attached
   by the request interceptor at `:51-55`.
3. **Registration** — the route is present in `server.app.openapi()['paths']`.
   Not "the decorator exists" — *registered*. See P3/P5 in the anchor.
4. **Authorization** — which gate really ran: a router-local
   `_require_rank` copy, `deps.require_rank`, or the outer
   `AccessGatewayMiddleware`. These are three different mechanisms and the
   router-local copies are the majority (`backend/deps.py:1-17`).
5. **Persistence** — the handler's DB handle. Establish whether it is the
   `bind()`-injected module global, `deps.get_db()` (returns `None` pre-startup),
   or `app.state.db`. Confirm the collection it writes is the one the read path
   reads.
6. **Render** — the component consumes the *actual* response shape and displays
   real data, not a placeholder, not an empty list styled as success.

If you cannot demonstrate all six, the feature is **not** DONE.

## Steps

1. Write the intended user path and the success criterion as one sentence,
   in the user's words ("an instructor can see their cohort's lab scores").
2. Locate the control (`file:line`) and the request it makes (`file:line`).
3. Prove the route is registered (Recipe B) and not shadowed (Recipe C) —
   seven `(method,path)` duplicates are live right now, including
   `GET /personas` and `GET /providers/usage-log` (x3).
4. Execute the request with a representative identity for each relevant rank in
   `backend/roles.py:26-36`, including one identity that should be **denied**.
5. Compare the response body field-by-field against what the component reads.
   A missing field that the component accesses without optional chaining is a
   render crash, not a cosmetic gap.
6. Report DONE only if the end-to-end outcome matches. Otherwise
   `BROKEN` / `INCOMPLETE` / `ENVIRONMENT BLOCKED`, with the failing link named.

## Repo-specific failure modes to check every time

- **Feature exists in source, absent at runtime** — router import swallowed by
  `try/except → logger.warning` (`backend/server.py:2786-2822`). Confirmed live
  for the CRM router.
- **Stale-role render window** — `frontend/src/lib/auth.jsx:22-32` seeds `user`
  from the `lce_user` localStorage cache and sets `loading=false` immediately, so
  `Protected` (`frontend/src/App.js:158-166`) authorizes on a cached role while
  `/auth/me` is still in flight. Check whether the feature's UI leaks
  higher-privilege content in that window.
- **Fail-open page gate** — `AccessGate` renders children until gates load and
  on load failure (`frontend/src/components/AccessGate.jsx:26`). A page the exec
  team disabled can flash visible.
- **Empty-state masquerading as success** — a 200 with `[]` because the DB was
  never seeded (see the two-DB-layer split, anchor §4) looks identical to a
  working feature with no data. Distinguish them.
- **Nav link to nothing** — cross-check `frontend/src/lib/routes.js` and
  `frontend/src/App.js` (168 `<Route>` elements) against the pages that exist.

## Constraints

- Verification requires **execution**. Source inspection can only prove BROKEN,
  never DONE.
- A passing backend request is not a passing feature — the render link is not
  optional. **There are zero frontend tests in this repo**
  (`frontend/package.json:62` defines `craco test`; no test file exists), so
  render verification is manual and must be described as such.
- No `mongod` in this container: persistence links are `ENVIRONMENT BLOCKED`,
  not PASS.
- Cite `file:line` for all six links. Paste real request/response output.
- Do not carry a finding between wai-institute.org and morehelp.center — the
  deployment topology is undeclared (anchor §0).
