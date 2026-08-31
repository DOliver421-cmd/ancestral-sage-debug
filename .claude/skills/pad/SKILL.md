---
name: pad
description: "Planning & architecture docs"
---

# pad

Produce or audit architecture/planning documents that match the real system, not aspiration.

## Steps

1. Interview the codebase (structure, data flow, boundaries).
2. Draft or revise the doc to reflect reality.
3. Flag sections that describe unbuilt functionality.
4. Report doc/system divergences for correction.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
