# Rollback & Recovery Improvement Plan

## Current State

The platform has a **configuration-only rollback system** (`backend/routers/system_rollback.py`) that:
- Keeps an N-3 FIFO queue of restore points in `system_restore_points`
- Snapshots only config collections: `feature_configs`, `platform_flags`, `page_access`, `user_feature_overrides`, `authz_matrix`
- Triggers via admin endpoint (`/api/admin/system/rollback`) or HMAC webhook
- Has ledger lockdown that explicitly excludes `users`, `audit_log`, and other data collections
- Is tested and functional for config changes

There is also a **GDPR soft-delete** path with a 30-day grace period, but it's scoped to GDPR-initiated deletions only and doesn't help for accidental admin deletions.

There are **no change streams**, no generic soft-delete, and no point-in-time recovery for user data.

## Problem

Accidental deletion of user accounts (like today) is unrecoverable. The system rollback explicitly skips user data, and there is no backup/restore integration callable from the application.

## Proposed Improvement: User Data Rollback via System Rollback Extension

### Decision 1: Scope
Extend the existing system rollback to include **user accounts** in restore points, but keep ledger lockdown for financial collections (`payments`, `creator_earnings`, `scholarship_pledges`).

**Rationale:** Reusing the existing rollback engine avoids building a parallel system. The restore point queue, admin gating, HMAC webhook, and Railway redeploy flow already work.

### Decision 2: What Gets Snapshotted
Add these collections to restore points:
- `users` — full documents except `password_hash` (store hash version/iteration count only for rollback validation)
- `user_feature_overrides` — already included
- `iam_identities` — sync with users
- `user_xp` — sync with users

Keep excluded (ledger lockdown):
- `payments`, `creator_earnings`, `media_purchases`, `scholarship_pledges`, `api_keys`, `user_credentials`, `audit_log`, `system_restore_points`

### Decision 3: Soft-Delete as Safety Net
Add a `deleted_at` soft-delete flag to the `users` collection. The existing GDPR code already uses this pattern. Any admin deletion route (e.g., `DELETE /api/admin/users/{id}`) should:
1. Set `deleted_at` and `is_active=False` instead of hard delete
2. Create a restore point automatically if no recent one exists
3. Log the deletion to `audit_log` and `exec_audit_log`

This gives a 30-day recovery window (matching GDPR grace period) without relying on full restores.

### Decision 4: Restore Point Trigger
Automatically create a restore point before any:
- Admin user deletion
- Admin bulk user modification
- Admin role/tier changes

This prevents data loss without requiring manual restore point creation.

### Decision 5: Validation
After rollback:
- Verify user count matches restore point
- Verify no orphaned `iam_identities` or `user_xp` records
- Run existing test suite for system rollback plus new user-data rollback tests

## Implementation Tasks

1. **Update `backend/routers/system_rollback.py`**
   - Add `users`, `iam_identities`, `user_xp` to `_ALLOWED_ROLLBACK_COLLECTIONS`
   - Strip `password_hash` from user snapshots; store `password_hash_version` only
   - Update `_restore_config()` to handle user documents safely

2. **Update admin user deletion routes**
   - In `backend/routers/users.py` and `backend/server.py` admin endpoints
   - Replace `delete_one` with soft-delete (`deleted_at` + `is_active=False`)
   - Auto-create restore point before deletion

3. **Add automatic restore point trigger**
   - New helper `_ensure_restore_point()` called before destructive admin actions
   - Checks `system_restore_points` for recent point (e.g., last 1 hour); creates one if stale

4. **Add tests**
   - Test user data in restore points
   - Test soft-delete + restore flow
   - Test auto-trigger before admin deletion
   - Test that password_hash is excluded from snapshots

5. **Update `scripts/backup/db-restore.sh`**
   - Add point-in-time restore from `system_restore_points` collection
   - Document the restore procedure in `scripts/backup/README.md`

## Out of Scope
- Automatic failover to backup DB (existing dual-DB connection is health-check only)
- Change streams / real-time CDC
- Restore of financial ledger collections
- UI for restore point management (admin API is sufficient)

## Open Question
Should soft-deleted users be visible in admin UI with a "restore" action, or should restoration only happen via system rollback? Soft-delete + restore button is more user-friendly but requires frontend work.
