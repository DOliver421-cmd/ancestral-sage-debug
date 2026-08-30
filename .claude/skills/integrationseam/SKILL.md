---
name: integrationseam
description: "Detect external integrations the deployed site depends on but the repo does not contain"
---

# integrationseam

Diagnose "missing integration" failures: the live site calls an external system
(Supabase, Stripe/Lemon, a cross-domain bridge) that is NOT present in this
repo's source. The `platform_liveness` 404 (Supabase project `phuymlvvxxvcejyfxwui`)
is the canonical case — documented as a missing seam in HANDOFF_FOR_WAI_SESSION.md.

## Steps

1. Collect deployed runtime signals: browser console errors (e.g.
   `*.supabase.co/rest/v1/...` 404), failed env lookups, CORS/origin rejections.
2. Grep the ENTIRE repo (all branches via `git grep $(git for-each-ref ...)`)
   for the integration: client init (`createClient`), project URL, env var,
   route, or table name.
3. If the integration code is absent in every branch, classify it as a
   **MISSING SEAM** — not a bug to patch here.
4. Check handoff/docs (HANDOFF*.md, SKILLS.md) for a prior decision about it.
5. Escalate to the owner with the evidence and the real options:
   (a) add the integration to this repo (client + table/migration + env), or
   (b) reroute the call to an existing in-repo endpoint (e.g. backend
   `/platform_liveness` instead of Supabase).
6. Do NOT claim the integration works, and do NOT fabricate the missing code.

## Constraints

- A missing seam is an owner decision when it spans repos or requires secrets
  (Supabase keys, payment keys). State that explicitly.
- Cross-reference the exact deployed error string and the repo grep result.
- If the integration IS in the repo but mis-wired, that's a bug — fix it; this
  skill is only for the truly-absent case.
