---
name: frontendworkflowauditor
description: "Frontend workflow audit"
---

# frontendworkflowauditor

Verify multi-step UI flows complete and show real state, not cosmetic placeholders.

## Steps

1. Walk each critical flow (form -> submit -> result render).
2. Confirm loading/error/success states are wired to real responses.
3. Check that inputs are labeled (aria) and accessible.
4. Report flows that silently no-op or render empty.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
