---
name: cea
description: "Code-execution / runtime verification for this FastAPI+Mongo+CRA repo: import the app, prove what actually registered, execute the path. Use whenever a claim needs to move from 'implemented' to 'working'."
---

# cea — code-execution audit

Read `.claude/skills/_shared/REPO-REALITY.md` first. It is the evidence anchor
and it explains why source inspection is invalid in this repo.

Prove code works by executing it. The defining rule: **implemented != working**,
and in this codebase **source-confirmed != route-registered** (see P3 in the
shared anchor: the CRM router silently fails to import and its endpoints do not
exist at runtime even though the decorators are right there in the file).

## Environment (established, do not re-guess)

- Use **`python3`**, not `python` — `python` is not on PATH here. Every
  `python -m ...` command in `AGENTS.md`/`opencode.json` fails as written.
- `fastapi` and `motor` import successfully.
- **There is no `mongod`.** You cannot verify persistence, seeding, or indexes.
- Always set `JWT_SECRET`. Unset, the app prints
  `FATAL: JWT_SECRET is not set` and **continues anyway** with broken auth.

## Steps

1. **State the claim** as a single falsifiable sentence, naming the exact
   method + path, or the exact UI control, and the expected observable result.

2. **Import the app and read stderr, not just the exit code.**
   ```bash
   cd backend && JWT_SECRET=testsecret python3 -c "
   import logging; logging.disable(logging.CRITICAL)
   import server
   print(len(server.app.openapi()['paths']), 'paths')"
   ```
   Every `failed to load: ...` / `Could not load ... router:` warning is a
   feature that does not exist at runtime. Capture them all verbatim.

3. **Confirm the route is actually registered.** Do NOT use `len(app.routes)` —
   this FastAPI version returns lazy `_IncludedRouter` wrappers and reports **7**.
   Use `app.openapi()['paths']`, or recurse `original_router.routes`
   (Recipe B/C in the shared anchor).

4. **Execute the path.** Use `fastapi.testclient.TestClient` as a context manager
   so lifespan runs. For anything DB-backed, expect failure and say so — do not
   convert a Mongo timeout into a PASS.

5. **Account for the startup race before trusting any result.** Startup is
   `asyncio.create_task(_on_startup_impl())` (`backend/server.py:1350-1362`), so
   requests are served before `deps.set_db()`, indexes, keyvault, and seeds have
   run. If your first request succeeded only because the loop happened to
   schedule the task first, you have measured luck. Re-run with a completion flag
   (Recipe D) to know which side of the race you were on.

6. **Report with the shared vocabulary**, section 9. `route-registered` is the
   minimum bar for "the endpoint exists". `executed` requires a captured status
   and body. `persistence-verified` is unavailable in this container.

## Constraints

- Never report PASS from reading code. In this repo that is a known-false signal.
- Never report PASS from an HTTP 200 alone — `/api/version` returns 200 with a
  dead database, and `/api/health` will tell you `status: "critical"` while
  Railway's configured healthcheck (`/api/version`) still passes.
- A swallowed `logger.warning(... non-fatal ...)` is a finding, not noise.
- Distinguish **"failed"** from **"could not run."** Mark the latter
  `ENVIRONMENT BLOCKED`.
- Cite `file:line` for every claim, and paste the actual captured output.
