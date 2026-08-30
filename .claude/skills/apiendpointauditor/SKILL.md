---
name: apiendpointauditor
description: "REST/HTTP API endpoint audit"
---

# apiendpointauditor

Verify every API endpoint does what its route, docs, and UI promise — no silent 500s, no auth gaps, no shape drift.

## Steps

1. Enumerate routes from the router source (not just docs).
2. For each: check auth dependency, request model, response shape, and error paths.
3. Cross-check against the frontend call sites that consume it.
4. Report endpoints that 404/400/401 unexpectedly or return a shape the UI can't render.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
