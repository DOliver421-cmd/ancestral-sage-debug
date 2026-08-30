---
name: featureduplicatedetector
description: "Duplicate feature detection"
---

# featureduplicatedetector

Find two or more implementations of the same feature that can drift apart.

## Steps

1. Cluster features by intent (route, UI label, capability).
2. Compare implementations for behavioral divergence.
3. Identify which is canonical and which is dead/competing.
4. Report duplication pairs and a recommended single source of truth.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
