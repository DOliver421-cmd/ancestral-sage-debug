---
name: seca
description: "Security audit"
---

# seca

Systematic review of the app for security defects: authn/authz, injection, secrets, CORS.

## Steps

1. Review auth dependencies on every route.
2. Scan for secret exposure, unsafe deserialization, injection vectors.
3. Check CORS/allowed origins and rate limits.
4. Report findings by severity with fix guidance.

## Constraints

- Verify by execution where possible; never report working on source inspection alone.
- Cite file:line evidence for every finding.
- Report DONE/PASS only when the live behavior matches the intended purpose.
