---
name: pstest
description: "Prompt/system testing"
---

# pstest

Test prompts and system instructions for robustness and leakage.

## Steps

1. Define the prompt's intended constraint set.
2. Run probe inputs that attempt to bypass constraints.
3. Measure adherence and information leakage.
4. Report prompt weaknesses with example breaches.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
