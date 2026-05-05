# LCE-WAI — Changelog

## Feb 2026 — P1 hotfix: /admin/cohorts N+1 elimination
- **server.py** `cohort_summary()` — replaced per-cohort `find` +
  `count_documents` loop with a single `progress.aggregate` pipeline
  (`$match` + `$lookup` users + `$group` by associate). Wire commands
  per request: 2 (constant), regardless of cohort count.
- **server.py** `ensure_indexes()` — added
  `progress(status, user_id)` and `users(associate, role)` indexes.
- **migrations/2026_02_cohorts_n1_indexes.py** — standalone idempotent
  migration with `up`/`down` for the new indexes.
- **scripts/perf_check.py** — PyMongo `CommandListener`-based proof
  that demonstrates O(1) query count at K=5/20/50 cohorts.
- **tests/test_cohorts_perf.py** — 2 new pytests:
  `test_cohorts_endpoint_is_constant_query_count` (perf invariant) and
  `test_cohorts_returns_correct_completion_counts` (functional).
- Full backend suite: **161/161 passing** (was 159).

## Iteration 6 (carried forward) — Admin/User hardening + CSV exports
See `PRD.md` for full detail. EXECUTIVE_ADMIN role, RBAC matrix,
domain-portable API resolution, 401 interceptor, force-password-rotation,
user-management CRUD all stable.
