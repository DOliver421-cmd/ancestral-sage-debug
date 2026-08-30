---
name: apicompleteness
description: "Gate skill: an API/feature is DONE only when proven working end-to-end (route → auth → request → backend → persistence → response → frontend render), not on source inspection"
---

# apicompleteness

Mandatory completion gate for ANY API, endpoint, or feature claim. Its only job
is to stop "done on source inspection" and require proof the full chain works.

## DONE means ALL of these are true (per endpoint / per feature):

1. **Route exists** — registered in the router source, reachable at the path the
   frontend calls (verify the path + method match, including any `/api` prefix).
2. **Auth is correct** — the dependency actually enforces the intended tier
   (public / any-authed / admin / exec). Not just "there's a Depends".
3. **Request shape matches the caller** — the frontend `api.post/get` body/params
   exactly match the backend request model. No field-name drift.
4. **Response shape matches the render** — every field the UI reads
   (`row.objective`, `data.total`, etc.) exists and is populated in the actual
   response. Nested-vs-flat mismatches count as BROKEN.
5. **Persistence round-trips** — a write via the real endpoint can be read back
   in the shape the UI expects (use databasepersistenceauditor).
6. **Live execution passes** — boot the server (or TestClient), authenticate as
   the required role, send a REAL request, and confirm the response + that the
   persisted doc is correct. If the environment can't boot the server, mark
   UNVERIFIED / ENVIRONMENT BLOCKED — never "works".

## Workflow

1. Enumerate every endpoint in scope (do NOT stop at the first one found).
2. For each: walk steps 1–6. Record PASS / FAIL / BLOCKED with file:line.
3. A single failing step = the whole endpoint is INCOMPLETE. Report it as such.
4. Only when ALL endpoints in scope pass 1–6 may the feature be called DONE.

## Constraints

- No endpoint is "done" on source inspection alone (AGENTS.md: Done Means Executed).
- Fix the WHOLE scope, not one representative example. If there are 12
  operational endpoints, verify 12 — not 1 and a claim the rest match.
- Never claim working when blocked; name the blocker and what's needed to verify.
- Cite file:line for every PASS and every FAIL.
