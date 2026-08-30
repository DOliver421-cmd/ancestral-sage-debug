---
name: frgk
description: "Frontend/backend gap check"
---

# frgk

Find where the frontend calls an API the backend doesn't satisfy (or vice-versa).

## Steps

1. Extract frontend API call signatures (method, path, body).
2. Match each to a backend route and its real response shape.
3. Flag calls with no route, wrong method, or shape mismatch.
4. Report the gap list with the specific field/route mismatches.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
