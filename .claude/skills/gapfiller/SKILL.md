---
name: gapfiller
description: "Intended-vs-implemented gap fill"
---

# gapfiller

Given a stated requirement and the current code, produce the minimal changes to close the gap.

## Steps

1. Capture the intended behavior (spec/owner statement).
2. Map current implementation state.
3. Enumerate missing pieces with lowest-blast-radius fixes.
4. Apply and re-verify; report what remains open.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
