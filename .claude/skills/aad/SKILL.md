---
name: aad
description: "Agent/AI-architecture discovery & audit"
---

# aad

Audit how autonomous agents and AI components are wired into the system: entry points, decision authority, human-in-the-loop gates, and failure blast radius.

## Steps

1. Inventory every agent/AI entry point (endpoints, schedulers, webhooks) that can take autonomous action.
2. Map each to its authority scope (read/write, which collections/resources, who can trigger it).
3. Identify human-in-the-loop gates and where they can be bypassed.
4. Report: autonomy surface, privilege concentration, and missing oversight.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
