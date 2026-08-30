---
name: entitlementmembershipauditor
description: "Role/entitlement membership audit"
---

# entitlementmembershipauditor

Verify that role/tier membership grants and denies exactly the intended controls.

## Steps

1. List all roles/tiers and their assigned controls.
2. For a sample of controls, confirm the allow/deny matrix matches policy.
3. Check privilege-escalation paths (default-deny vs default-allow).
4. Report entitlements that are over- or under-permissioned.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
