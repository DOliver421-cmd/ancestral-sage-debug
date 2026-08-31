---
name: frgk
description: "Frontend/backend gap check for this repo: diff frontend axios call sites in frontend/src against the 631 routes actually registered by backend/server.py, including shape and status-code contracts."
---

# frgk — frontend/backend gap check

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Find where the frontend calls an API the backend does not satisfy, or where the
backend returns something the frontend cannot render.

## How the frontend calls the backend (single choke point)

`frontend/src/lib/api.js`:
- one `axios.create({ baseURL: API })` instance (`:23`);
- base URL resolves `window.__WAI_BACKEND__` → `REACT_APP_BACKEND_URL` →
  same-origin `""` (`:17-21`). **There is deliberately no hardcoded fallback
  host** — the comment records that a dead baked URL once broke every call.
- request interceptor attaches `Bearer` from `localStorage.lce_token` (`:51-55`);
- `openAuthedUrl()` (`:29-47`) uses raw `fetch` for auth-gated binary downloads —
  a plain `<a href>` gets a 401 because no header is attached. Any new
  file/PDF/handbook link must use this, not an anchor.

So a gap check must cover **three** call styles: `api.*`, raw `fetch` via
`openAuthedUrl`, and any direct `axios`/`fetch` that bypasses the instance
(and therefore sends no token — always a defect).

## Steps

1. **Extract the real registered backend surface** (never grep the routers):
   ```bash
   cd backend && JWT_SECRET=testsecret python3 -c "
   import logging, json; logging.disable(logging.CRITICAL)
   import server
   print(json.dumps(sorted(server.app.openapi()['paths']), indent=1))"
   ```

2. **Extract frontend call sites**, all three styles:
   ```bash
   cd frontend && grep -rnoE "api\.(get|post|put|patch|delete)\(\s*[\`\"'][^\`\"']+" src
   grep -rn "fetch(" src
   grep -rn "axios\." src | grep -v "lib/api.js"
   ```
   Template literals (`` api.get(`/lms/courses/${id}`) ``) must be normalised to
   the FastAPI path form (`/lms/courses/{course_id}`) before diffing, or you will
   generate false "missing route" noise.

3. **Diff both directions.**
   - Frontend path with no registered route → **broken feature**. Remember the
     route may be missing because its router's import was swallowed
     (`backend/server.py:2786-2822`), not because nobody wrote it. Confirmed live:
     the CRM router fails to import, so its endpoints are absent.
   - Registered route no page calls → dead endpoint / unwired backend work. Per
     `AGENTS.md`, a backend endpoint with no caller **is not a feature.**

4. **Check method and prefix.** `api` already has `/api` in its base URL, so a
   frontend path must not repeat it. `app` mounts `api_router` with
   `prefix="/api"` (`backend/server.py:304`), but four routers are included on
   `app` directly (`nam`, `saga`, `executive_pipeline`, `exec_tools` —
   `:2789, :2798, :2809, :2818`) and carry their own prefixes. Verify, do not assume.

5. **Mind `redirect_slashes=False`** (`backend/server.py:208`). A trailing-slash
   mismatch is a hard 404 here — there is no redirect to save you.

6. **Diff response shape field-by-field** against what the component reads.
   Absent optional chaining, a missing field is a render crash. Execute the
   endpoint and compare the real body; do not read the Pydantic model and assume.

7. **Diff the status-code contract.** `frontend/src/lib/api.js:63-79` treats 401
   as "session dead" only for `AUTH_PATHS` and `ADMIN_SCOPE` prefixes
   (`/admin/`, `/exec/`, `/executive/`, `/abo/`, `/member-projects/`). A new
   admin-ish surface under a different prefix that 401s on expiry will show a
   broken page with **no sign-in prompt** — exactly the bug those lists were
   added to fix. Check every new prefix against them.

8. **Check shadowed routes** (Recipe C) — seven live duplicates including
   `GET /personas` and `GET /providers/usage-log` (3x). The frontend may be
   getting the losing handler's contract.

9. Report the gap list with specific route/method/field mismatches.

## Constraints

- Enumerate the backend surface from the **running app**, never from source.
  Source-based enumeration reports phantom endpoints in this repo.
- Report the direction of each gap and the user-visible consequence, not just
  the mismatch.
- Shape claims require an executed response. Mark DB-backed shapes
  `ENVIRONMENT BLOCKED` (no `mongod` here).
- The frontend has **zero tests** — render-side claims are manual.
- Cite `file:line` on both sides of every gap.
