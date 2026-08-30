---
name: pca
description: "Pattern/code analysis"
---

# pca

Analyze code for anti-patterns, consistency, and improvement opportunities.

## Steps

1. Select the target module or pattern.
2. Apply static reasoning for duplication, coupling, error handling.
3. Rank findings by impact.
4. Report concrete refactors with file:line references.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
