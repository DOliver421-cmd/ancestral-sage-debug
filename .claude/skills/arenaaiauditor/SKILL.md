---
name: arenaaiauditor
description: "AI system arena-style evaluation"
---

# arenaaiauditor

Stress-test an AI feature the way a hostile or confused user would: boundary prompts, tool abuse, scope leaks.

## Steps

1. Define the intended capability boundary of the AI feature.
2. Probe with out-of-scope, adversarial, and malformed inputs.
3. Observe whether the system refuses, leaks, or over-reaches.
4. Report boundary violations and recommended guardrails.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
