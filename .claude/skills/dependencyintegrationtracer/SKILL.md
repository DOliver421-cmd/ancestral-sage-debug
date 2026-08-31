---
name: dependencyintegrationtracer
description: "Dependency wiring trace"
---

# dependencyintegrationtracer

Trace how a library or internal module is actually wired end-to-end, including env and config.

## Steps

1. Locate every import/instantiation of the dependency.
2. Follow config/env flow from startup to call site.
3. Confirm the version and behavior match the assumption in code.
4. Report wiring gaps where the code expects something the integration doesn't provide.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
