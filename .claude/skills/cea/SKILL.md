---
name: cea
description: "Code-execution / runtime verification"
---

# cea

Prove code works by executing it, not by reading it. The defining rule: implemented != working.

## Steps

1. Identify the claim to verify (endpoint, function, UI path).
2. Stand up the minimum runtime (server, in-memory or real DB, auth).
3. Execute the actual path and capture the real output.
4. Report PASS only if the live behavior matches the intended purpose.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
