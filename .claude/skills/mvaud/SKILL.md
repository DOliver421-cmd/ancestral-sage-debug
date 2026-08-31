---
name: mvaud
description: "Minimum-viable / milestone audit"
---

# mvaud

Confirm a milestone delivers its promised minimum and nothing regresses.

## Steps

1. List the milestone's acceptance criteria.
2. Execute each criterion in the running system.
3. Check for regressions in adjacent features.
4. Report milestone as met / not-met with the failing criteria.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
