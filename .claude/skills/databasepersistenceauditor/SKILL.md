---
name: databasepersistenceauditor
description: "Database persistence reality check"
---

# databasepersistenceauditor

Verify that data written by the app can be read back in the shape the app expects — the write/read contract.

## Steps

1. Identify a write path (POST/store.create) and its paired read path (GET/store.find).
2. Execute a write with representative data.
3. Execute the read and inspect the returned document shape.
4. Diff stored shape vs the consumer's expected fields; report mismatches and missing fields.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
