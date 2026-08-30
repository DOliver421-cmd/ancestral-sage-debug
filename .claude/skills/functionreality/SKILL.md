---
name: functionreality
description: "Single-function reality check"
---

# functionreality

Prove one specific function does what its name/doc claims.

## Steps

1. Read the function and state its contract.
2. Call it with representative inputs in isolation.
3. Assert outputs/side-effects match the contract.
4. Report PASS/FAIL with the concrete evidence.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
