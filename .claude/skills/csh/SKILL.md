---
name: csh
description: "Codebase structure & health check"
---

# csh

Assess structural health: layering, duplication, dead code, and convention adherence.

## Steps

1. Map top-level modules and their dependencies.
2. Detect circular imports, duplicate implementations, and unreachable code.
3. Check naming/style consistency against existing conventions.
4. Report structural risks ranked by blast radius.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
