---
name: rdaud
description: "Red-team / risk audit"
---

# rdaud

Adversarially hunt for security and safety risks across the app.

## Steps

1. Enumerate trust boundaries and untrusted inputs.
2. Attempt auth bypass, injection, privilege escalation, data exfil.
3. Assess blast radius of each finding.
4. Report risks ranked with remediation.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
