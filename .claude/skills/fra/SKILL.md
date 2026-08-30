---
name: fra
description: "Functional reality audit"
---

# fra

Determine whether a feature actually fulfills its intended purpose for a human user — the strictest 'does it work' test.

## Steps

1. Define the intended user path and success criterion.
2. Execute the full path in the real interface (click/request/render).
3. Compare observed outcome to intended outcome.
4. Report DONE only if end-to-end outcome matches; otherwise BROKEN/INCOMPLETE with evidence.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
