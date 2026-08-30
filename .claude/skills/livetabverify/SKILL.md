---
name: livetabverify
description: "Prove a UI tab renders REAL backend data end-to-end (not empty/placeholder/mock)"
---

# livetabverify

Verify that a specific frontend tab/panel shows real data fetched from the live
API — the strict "does the rendered DOM match the backend response" test. This
is the check that catches write/read shape mismatches (e.g. backend stores
`{check: result}` but the UI reads `row.objective`), empty tables, and mocked
fallbacks that look done but aren't.

## Steps

1. Identify the tab and the exact API calls it makes — read the JSX to find
   `api.get(...)` / `useEffect` handlers and the fields the JSX renders.
2. Boot the backend (requires `pip` deps + `JWT_SECRET`; uses MongoDB if
   `MONGO_URL` set, else in-memory fallback). Authenticate as the role the tab
   requires (Hybrid NAM tabs need `executive_admin`).
3. Call each GET the tab depends on with a real (or seeded) token; capture the
   actual JSON response.
4. For each field the JSX displays, assert it exists and is non-empty in the
   API response AND is rendered. Map response keys → JSX render path.
5. If a displayed field is missing/empty in the response, or the JSX reads a
   nested key the API doesn't return flat, mark that tab BROKEN with file:line.
6. Report DONE only if every rendered field is backed by real API data.

## Constraints

- Must EXECUTE the API call; never infer "works" from the JSX alone.
- If the environment can't boot the server (missing deps, no Mongo), report
  UNVERIFIED / ENVIRONMENT BLOCKED — do not claim pass.
- Cite both the API response shape and the JSX render line for each finding.
- Mock/placeholder data rendered in place of a real response = BROKEN, not done.
