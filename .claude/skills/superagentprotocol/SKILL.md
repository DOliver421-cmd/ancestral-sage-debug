---
name: superagentprotocol
description: "Multi-agent orchestration protocol"
---

# superagentprotocol

Coordinate sub-agents to divide and conquer a large task without duplication.

## Steps

1. Decompose the task into independent work units.
2. Dispatch units to sub-agents with explicit inputs/outputs.
3. Reconcile outputs and resolve overlaps.
4. Report the consolidated result and any conflicts.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
