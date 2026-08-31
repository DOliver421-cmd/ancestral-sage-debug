---
name: ura
description: "Usage/risk analysis"
---

# ura

Analyze how a system or feature is used and where risk concentrates.

## Steps

1. Collect usage signals (logs, access patterns).
2. Identify high-value/high-risk paths.
3. Quantify exposure and dependency.
4. Report usage hotspots and risk concentration.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
