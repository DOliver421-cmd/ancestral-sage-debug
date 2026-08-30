---
name: rgaud
description: "Regression audit"
---

# rgaud

Confirm a change didn't break existing behavior.

## Steps

1. Capture the pre-change baseline (tests or behavior).
2. Apply the change and re-run the baseline path.
3. Diff observed vs expected.
4. Report regressions with the triggering change.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
