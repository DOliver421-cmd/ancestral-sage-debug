# www.morehelp.center — Launch Repair Plan

## Overview

Nine critical blockers identified in the operational audit must be resolved before public launch.
The work proceeds in four phases: repair each blocker (C-1 → C-9) → regression test each fix →
run the full public workflow end-to-end → tag anything non-blocking as post-launch hardening.

No architectural redesign. No new features. Fixes are surgical and minimal.

---

## Repair Targets by Blocker

### C-1: In-Memory Rate Limiter — Race Condition + Process Death

**File:** `backend/server.py:238-247`

**Problem:** `_RATE = defaultdict(list)` is a plain Python dict mutated by concurrent async
handlers without a lock. Two simultaneous requests to the same key both read the counter,
both pass the `>= max_calls` check, and both append — bypassing the limit. On restart or
horizontal scale, the dict is wiped and the limit resets.

**Fix:** Wrap the rate-limit dict in `asyncio.Lock()`. Add a module-level
`_RATE_LOCK = asyncio.Lock()` and acquire it inside `check_rate()` for the read-filter-append
sequence. This keeps the in-memory approach (no Redis dependency) but makes it atomic within
a single process. Add a comment that horizontal scale requires Redis.

**Target lines:** 238–247

**Expected outcome:** Concurrent flood of login or registration requests against the same key
cannot bypass the per-window limit. The behavior is serialized.

---

### C-2: JWT Token Revocation Not Enforced

**Files:** `backend/server.py:694-699` (make_token), `backend/server.py:702-715` (current_user),
`backend/server.py:9369-9376` (revoke_all_sessions)

**Problem:** `revoke_all_sessions()` at line 9373 increments `token_version` on the user document.
`make_token()` at line 694 never embeds `token_version` in the JWT payload. `current_user()` at
line 707 decodes only signature and expiry — never checks `token_version`. A revoked token is
indistinguishable from a live one until natural expiry (168 hours).

**Fix:**
1. In `make_token()`: fetch `token_version` from the user document and embed it in the JWT
   payload as `"tv"`.
2. In `current_user()`: after decoding the JWT, compare `payload.get("tv", 0)` against
   `user_doc.get("token_version", 0)`. If they differ, raise 401 "Token revoked".
3. In `revoke_all_sessions()`: no change needed — it already increments correctly.
4. Login must embed `token_version` in the token at issuance. Read the user doc at login time
   and pass `token_version` as `extra` to `make_token()`.

**Note:** `make_token()` currently accepts `user_id` and `role` only. It needs to accept an
optional `token_version` int (defaulting to 0) to embed as `"tv"`.

**Expected outcome:** After `DELETE /api/auth/sessions`, any existing JWT is rejected on the
next request with 401. Re-login issues a new token with the updated `token_version`.

---

### C-3: Startup Is Fire-and-Forget

**File:** `backend/server.py:1086-1097`

**Problem:** `_on_startup_impl()` is launched as `asyncio.create_task()` and returns
immediately. The server accepts traffic before DB indexes are created, before seed users exist,
and before `STARTUP_COMPLETE` is set. The comment (lines 1088-1097) cites a real historical
reason: Railway's `/api/version` health check was timing out during heavy Mongo init.

**Fix:** Keep the background task pattern to preserve Railway health-check compatibility, BUT:
1. Add a done-callback to the startup task that logs the exception at ERROR level if the task
   fails, so startup failures are visible in Railway logs.
2. The `/api/health` endpoint already gates on `STARTUP_COMPLETE`. No change needed there.
3. Add a `try/except` wrapper around the entire body of `_on_startup_impl()` that sets a
   module-level `STARTUP_ERROR` string on failure, which `/api/health` can surface.

This is the minimal fix: the fire-and-forget behavior is intentional and documented, but
silent failures must become visible.

**Target lines:** 1086–1097, 1100–1346

**Expected outcome:** If `_on_startup_impl()` crashes (e.g., Mongo is unreachable), Railway
logs show an ERROR with the full traceback and `/api/health` returns unhealthy with the error
reason.

---

### C-4: Background Tasks Silently Die

**File:** `backend/server.py:1238, 1301, 1326, 1339`

**Problem:** Four `asyncio.create_task()` calls (rate-limiter cleanup, failover watchdog, GDPR
purge loop, memory consolidation loop) have no `.add_done_callback()`. If any background task
raises an unhandled exception outside its inner `try/except`, the task silently terminates.
No alert, no restart.

**Fix:** Create a helper function `_supervised_task(coro, name)` that:
1. Wraps the coroutine in a `try/except Exception` that logs at ERROR level with the task name
   and full traceback.
2. After logging, re-raises so the task actually dies visibly (rather than being swallowed).
3. Replace all four bare `asyncio.create_task(...)` calls with `asyncio.create_task(_supervised_task(..., name="..."))`.

Additionally, add an `@app.on_event("shutdown")` handler that cancels all tracked background
tasks cleanly, preventing zombie task leaks on container stop.

**Expected outcome:** Any background task that exits unexpectedly appears in Railway logs as
an ERROR with a full traceback. The container does not silently lose rate-limiting, GDPR purges,
or failover watching.

---

### C-5: `asyncio.gather()` in AI Routes Crashes on One Tool Failure

**Files:** `backend/server.py:4186-4189` (Director), `backend/server.py:4589` (Revenue Director),
`backend/server.py:4693` (Sage)

**Problem:** All three agentic loops call `asyncio.gather(*[dispatch_tool(...) for ...])` without
`return_exceptions=True`. If any single tool dispatch raises (network timeout, DB down, invalid
tool name), `gather()` propagates the first exception immediately and aborts the entire tool
batch. The calling `try/except` in the model loop catches it, logs a warning, and drops to the
next model tier — so the user gets a downgraded response with no explanation.

**Fix:** Add `return_exceptions=True` to all three `asyncio.gather()` calls. After the gather,
check each result: if it is an `Exception` instance, substitute a string like
`"[tool error: {type(r).__name__}]"` as the tool result content. This allows the model to
continue the agentic loop with partial tool results rather than crashing entirely.

**Expected outcome:** A single failing tool (e.g., web_search times out) produces an inline
error string in the tool result. The AI continues responding with the available results. No 500,
no silent model downgrade.

---

### C-6: TTS Shared State Race Conditions

**File:** `backend/server.py:2874-2934`

**Problem:** Three in-process data structures are mutated by concurrent async handlers without
locks:
- `_tts_failures: list[float]` — appended and sliced concurrently
- `_tts_metrics: list[tuple]` — appended and pop(0)'d concurrently
- `_TTS_SESSION_USAGE: dict[str, int]` — read-compute-write race allows quota bypass

**Fix:** Add `_TTS_LOCK = asyncio.Lock()` at module level. Wrap all mutations of these three
structures in `async with _TTS_LOCK:`. The functions affected are:
- `_tts_breaker_state()` (slices `_tts_failures`)
- `_tts_record_success()` (clears `_tts_failures`)
- `_tts_record_failure()` (appends to `_tts_failures`, writes `_tts_breaker_opened_at`)
- `_tts_record_metric()` (appends to `_tts_metrics`, pops from `_tts_metrics`)
- `_tts_check_cost_cap()` (reads and writes `_TTS_SESSION_USAGE`)

Note: `_tts_breaker_state()` is currently a sync function. Convert to `async def` to support
`await _TTS_LOCK.acquire()`, or restructure to call it within a locked context.

**Expected outcome:** Concurrent TTS requests correctly serialize quota accounting. A user
submitting two simultaneous requests cannot double-spend their character allowance. The circuit
breaker opens reliably when the threshold is hit.

---

### C-7: GDPR Account Deletion Is Incomplete and Silently Fails

**File:** `backend/server.py:2004-2022`

**Problem:**
1. Only 4 collections are cleaned: `progress`, `lab_submissions`, `portfolio`, `ai_consents`.
   User data also lives in `auth_sessions`, `notifications`, `chat_history`, `certificates`,
   `incidents`, `tts_usage`, `password_reset_tokens`, and `audit_log` (actor references).
2. Each `delete_many()` is wrapped in `except Exception: pass` — silent failure means a
   partially completed deletion looks like success to the user.

**Fix:**
1. Expand the deletion collection list to include all user-data collections:
   `progress`, `lab_submissions`, `portfolio`, `ai_consents`, `auth_sessions`, `notifications`,
   `chat_history`, `certificates`, `tts_usage`, `password_reset_tokens`.
   (Do NOT delete from `audit_log` or `incidents` — these are compliance records that must
   be retained but can be anonymized by replacing `actor_id`/`user_id` with `"[deleted]"`.)
2. Replace `except Exception: pass` with `except Exception as e: errors.append(str(e))`.
3. After the loop, if `errors` is non-empty, log at ERROR level and return a 207 response
   indicating partial deletion with the collection names that failed.
4. The anonymization of `audit_log` and `incidents` references should use `update_many` to
   replace the user's ID with `"[deleted]"` — this preserves the audit trail without storing PII.

**Expected outcome:** A GDPR deletion request clears user data from all 10 collections.
Failures in individual collections are reported, not silently swallowed. The audit trail is
preserved but anonymized.

---

### C-8: Last-Admin Deactivation Guard Is Not Atomic

**File:** `backend/server.py:1928-1940`

**Problem:** The guard is a read-then-decide pattern:
```python
active_admin_class = await db.users.count_documents(...)
if active_admin_class <= 1:
    raise HTTPException(...)
await db.users.update_one(...)
```
Two concurrent deactivation requests both read `count = 2`, both pass the guard, both update —
leaving 0 active admins. The system is permanently locked.

**Fix:** Replace the read-then-decide with a conditional MongoDB `update_one` that atomically
checks and updates in a single operation:
```python
result = await db.users.update_one(
    {
        "id": uid,
        "is_active": {"$ne": False},  # only if currently active
        # guard: there must be more than 1 active admin
        # (enforced via a findOneAndUpdate with a pre-aggregation count is not atomic in Mongo)
    },
    {"$set": {"is_active": body.is_active}}
)
```
Since MongoDB does not support count-based conditional updates atomically, use a two-step
approach with a unique "deactivation lock" document, or use `find_one_and_update` with
`return_document=True` and then immediately verify the count and roll back if needed within
a single-document transaction.

The practical fix given MongoDB without transactions: use `find_one_and_update` to atomically
flip `is_active` to False only if the document is currently active, THEN do an immediate
count check, and roll back the update (set `is_active: True`) if count is now 0. Log the
rollback. This reduces the race window to near-zero without requiring replica set transactions.

**Expected outcome:** Concurrent deactivation requests cannot both succeed when only one admin
remains. At worst, one request succeeds and the other gets a 400 on the post-update count check
and the flag is immediately restored.

---

### C-9: Frontend Null-Crash Paths and Missing Error Isolation

**Files:**
- `frontend/src/pages/AdminTools.jsx:14-20` — four concurrent API calls with no `.catch()`
- `frontend/src/pages/MoreHub.jsx:284` — `posts.filter(...)` crashes if `posts` is null
- `frontend/src/pages/MoreHub.jsx:50` — `new Date(post.expires_at) - Date.now()` yields NaN
- `frontend/src/pages/MoreAdmin.jsx:143` — `[...queue.posts, ...queue.needs]` crashes if either is undefined
- `frontend/src/pages/MoreOps.jsx:144` — optimistic rollback `prev.slice(0, -1)` removes the wrong message when messages are queued

**Fix per file:**

**AdminTools.jsx:** Add `.catch(err => toast.error(...))` to each of the four `.then()` chains.
Add a defensive check before calling `.filter()` on `r.data`: `(r.data || []).filter(...)`.

**MoreHub.jsx line 284:** Change to `(posts || []).filter(p => p.category === catFilter)`.

**MoreHub.jsx line 50 (PostCard):** Guard `expires_at`:
```js
const expires = post.expires_at ? new Date(post.expires_at) : null;
const daysLeft = expires && !isNaN(expires) ? Math.max(0, Math.ceil((expires - Date.now()) / 86400000)) : null;
```
Render `{daysLeft !== null ? `${daysLeft}d` : "—"}`.

**MoreAdmin.jsx line 143:** Change to:
```js
const reviewItems = [...(queue.posts || []), ...(queue.needs || [])];
```

**MoreOps.jsx optimistic rollback:** Track the user message by a stable key (timestamp or uuid)
rather than position. Store the message ID at send time and remove by ID on failure, not by
`.slice(0, -1)`.

**Error boundary:** Wrap the admin route subtree in `App.js` with a second `<ErrorBoundary>`
component so a crash inside any admin page does not take down the full app.

**Expected outcome:** No admin page crashes on a null API response. A failed API call shows
a toast error and leaves the page in a usable empty state. A crashed admin component shows
the ErrorBoundary fallback without crashing the whole app.

---

## Phase 2 — Regression Checkpoints

After each C-N fix, the following must hold before moving to the next:

| Blocker | Regression Check |
|---|---|
| C-1 | Fire 10 concurrent login requests with wrong password to same email. Rate limit triggers by request 6 at most. |
| C-2 | Login → call `DELETE /api/auth/sessions` → reuse old token → must receive 401. |
| C-3 | Simulate startup with Mongo unavailable → `/api/health` must return unhealthy with error detail. |
| C-4 | Kill a background task artificially → Railway logs must show ERROR with task name and traceback. |
| C-5 | Send a Director AI message that calls a tool that raises an exception → must receive a reply, not a 500. |
| C-6 | Send two concurrent TTS requests from the same session → total character count must equal the sum of both, not just the larger. |
| C-7 | Delete own account → verify `auth_sessions`, `notifications`, `chat_history` collections show no records for that user ID. |
| C-8 | With exactly 2 admins, concurrently deactivate both → only one must succeed; verify at least one admin remains active. |
| C-9 | With backend returning 500 for all endpoints, load AdminTools, MoreAdmin, MoreHub — no full crash, toast errors shown. |

---

## Phase 3 — Full Launch Workflow Pass

After all nine fixes are applied and regression checks pass, the following end-to-end workflow
must run without error:

```
visitor     → lands on /main or /more
register    → POST /api/auth/register → receives JWT
login       → POST /api/auth/login → receives JWT with token_version
user        → GET /api/auth/me → correct user object
AI          → POST /api/ai/chat or /more/department/chat → gets reply
content     → POST /more/posts or /more/needs → creates content
admin       → GET /admin/users, /admin/stats, /more/admin → all load
executive   → GET /exec/system, /admin/sage-audit → all load
payment     → Stripe payment flow (if keys set in Railway)
fulfillment → course/credential access after payment
logout      → DELETE /api/auth/sessions → old token rejected with 401
deletion    → DELETE /api/auth/account → data removed from all 10 collections
```

Any failure in this chain that is caused by a non-blocker issue becomes a post-launch
hardening ticket.

---

## Phase 4 — Post-Launch Hardening Backlog

These are real issues but do NOT prevent existing features from functioning:

- Redis-backed rate limiter for multi-pod scale
- `httpOnly` cookies instead of `localStorage` for JWT storage
- Cross-tab session synchronization via `storage` event
- Proactive token refresh before 168-hour expiry
- `window.prompt()` replacement in MoreAdmin rejection flow
- Per-component ErrorBoundary on all admin pages (beyond the route-level boundary added in C-9)
- Full queue reload on each approve/reject replaced with optimistic item removal
- Request timeout configuration on axios instance
- Offline detection and pending request queue
- Skeleton loaders on admin pages
- `max_pool_size` on MongoDB Motor client
- Legacy `seed_users()` migration made one-time (check a migration flag before running)

---

## File Change Map

| File | Blockers addressed |
|---|---|
| `backend/server.py` | C-1, C-2, C-3, C-4, C-5, C-6, C-7, C-8 |
| `frontend/src/pages/AdminTools.jsx` | C-9 |
| `frontend/src/pages/MoreHub.jsx` | C-9 |
| `frontend/src/pages/MoreAdmin.jsx` | C-9 |
| `frontend/src/pages/MoreOps.jsx` | C-9 |
| `frontend/src/App.js` | C-9 (ErrorBoundary around admin routes) |

---

## Status

- [ ] C-1: Rate limiter atomicity — pending
- [ ] C-2: JWT token_version enforcement — pending
- [ ] C-3: Startup task observability — pending
- [ ] C-4: Background task supervision — pending
- [ ] C-5: asyncio.gather return_exceptions — pending
- [ ] C-6: TTS shared state lock — pending
- [ ] C-7: GDPR deletion completeness — pending
- [ ] C-8: Last-admin atomic guard — pending
- [ ] C-9: Frontend null-crash paths — pending
- [ ] Phase 2: Regression pass — pending
- [ ] Phase 3: Full launch workflow — pending
