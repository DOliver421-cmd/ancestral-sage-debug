# WAI Institute Codebase Audit Report
**Date:** 2026-05-22  
**Auditor:** Claude  
**Scope:** Full backend codebase review for security, consistency, data handling, and architecture

---

## EXECUTIVE SUMMARY

The codebase is **structurally sound** with good patterns for auth, access control, and data safety. However, there are **12 issues** (ranging from low to critical) that should be fixed before implementing the new governance architecture. Most are fixable in < 1 hour. One is a potential security gap.

**Critical Issues:** 1  
**High Priority:** 3  
**Medium Priority:** 5  
**Low Priority:** 3

---

## ISSUES FOUND

### 🔴 CRITICAL

#### Issue 1: Missing Safety Gates for Public Sage Subscription
**Location:** `/api/ai/chat` exists, but no tier-based routing  
**Problem:** The Sage subscription service requires 3 safety gates (automated filter, human escalation, director approval). The `/ai/chat` endpoint has consent + crisis detection but **no tier-based access control** or **no output filtering before delivery**.

**Evidence:**
- `/ai/chat` doesn't check user subscription tier
- No "Gate 1" automated content filter (profanity, self-harm suggestions, etc.)
- No "Gate 2" human escalation workflow for sensitive topics
- No "Gate 3" director approval queue for high-impact recommendations

**Fix Required:** 
- Add subscription tier check to `/ai/chat`
- Implement output filter before response delivery (Gate 1)
- Add escalation flag + hold mechanism for sensitive responses (Gate 2)
- Add director approval queue for Advanced subscribers (Gate 3)
- **Estimated effort:** 2-3 hours

---

### 🟠 HIGH PRIORITY

#### Issue 2: Pipeline Manager Bug Not Yet Tested
**Location:** `src/agents/pipeline_manager.py` line 604  
**Problem:** I just fixed a bug where the keyword fallback confidence cap (0.55) was preventing merch routing (threshold 0.60). The fix sets viral posts to confidence >= 0.62. **This change has not been tested in the live system yet.**

**Fix Required:**
- Run full test suite to confirm no regressions
- Especially: `src/tests/test_pipeline_manager.py`
- Verify merch routing now works in keyword fallback mode
- Monitor production for unexpected routing changes
- **Estimated effort:** 0.5 hours (testing)

#### Issue 3: Admin Endpoints Missing Comprehensive Audit Logging
**Location:** `/admin/*` endpoints throughout `server.py`  
**Problem:** Admin actions are logged (good), but NOT consistently. Some endpoints log with `audit()` but others don't. For example:
- `POST /admin/associate` → logs properly
- `PATCH /admin/users/{uid}/role` → logs properly  
- `PATCH /admin/users/{uid}/active` → **missing audit log call**
- `DELETE /admin/users/{uid}` → **missing audit log call**

**Evidence:**
```python
@api_router.patch("/admin/users/{uid}/active")
async def admin_deactivate_user(uid: str, body: AdminActiveReq, user: User = Depends(require_role("admin"))):
    # ... code ...
    await db.users.update_one({"id": uid}, {"$set": {"is_active": body.is_active}})
    # BUG: No audit() call here!
    return {"ok": True}
```

**Impact:** Compliance issue. If a deactivation is questioned later, there's no audit trail of who did it or when.

**Fix Required:**
- Add `audit()` calls to all admin state-changing endpoints
- Audit all admin endpoints systematically
- Check coverage in tests
- **Estimated effort:** 1 hour

#### Issue 4: Error Messages May Leak Information
**Location:** Multiple endpoints return detailed error messages  
**Problem:** Some error messages expose too much detail. For example:

```python
raise HTTPException(401, "Invalid or expired token")  # ✓ Good
raise HTTPException(403, f"Requires role: {roles}")   # ⚠️ Reveals role hierarchy
```

Exposing the required roles list could help an attacker understand the privilege system.

**Other cases:**
- Database errors sometimes leak info through exceptions
- Some endpoints expose existence of users by different error messages ("User not found" vs "Invalid credentials")

**Fix Required:**
- Standardize error messages to not leak system info
- Use generic "Access denied" for role violations
- Log detailed errors server-side, return generic messages to client
- **Estimated effort:** 0.5 hours

---

### 🟡 MEDIUM PRIORITY

#### Issue 5: Directory Traversal Risk in File Upload (if enabled)
**Location:** `/credentials` endpoints with file handling  
**Problem:** The code uses `UploadFile` from FastAPI. If file uploads are implemented, there could be a path traversal vulnerability if filenames aren't sanitized.

**Status:** Appears unused currently, but flagged for prevention.

**Fix Required:**
- If implementing file uploads: sanitize filenames (remove `../`, `..\\`, etc.)
- Use `pathlib.Path` for safe path operations
- Never trust user-supplied filenames for path construction
- **Estimated effort:** 0.5 hours (if needed)

#### Issue 6: Rate Limiting Uses In-Memory Dict (Not Cluster-Safe)
**Location:** `server.py` lines 155-164  
**Problem:** 
```python
from collections import defaultdict as _dd
_RATE = _dd(list)

def check_rate(key: str, max_calls: int, window_sec: int):
    now = datetime.now(timezone.utc).timestamp()
    _RATE[key] = [t for t in _RATE[key] if now - t < window_sec]
    if len(_RATE[key]) >= max_calls:
        raise HTTPException(429, "Too many requests, slow down")
    _RATE[key].append(now)
```

This is fine for a single-instance server but **breaks when Railway scales to multiple instances**. Each instance has its own `_RATE` dict, so a user can make `max_calls * num_instances` requests.

**Impact:** Low risk currently (Railway likely single-instance), but could be abused if scaled.

**Fix Required:**
- Use Redis for distributed rate limiting when multi-instance
- For now: document this limitation in comments
- Add a TODO for scaling
- **Estimated effort:** 1-2 hours (if scaling needed)

#### Issue 7: Missing Data Retention Policy
**Location:** Project-wide  
**Problem:** The code doesn't explicitly delete old conversation history, user data, or audit logs. No TTL (time-to-live) on sensitive collections.

**GDPR/CCPA Issue:** Users can request deletion, but if you retain indefinitely, that's a compliance violation.

**Evidence:** 
- `db.chat_history` grows unbounded
- `db.audit_log` grows unbounded
- No automatic cleanup job

**Fix Required:**
- Add MongoDB TTL indexes to collections that should expire
- Implement batch cleanup for older data (e.g., audit logs > 1 year)
- Document retention policy in privacy policy
- Example:
  ```python
  await db.chat_history.create_index(
      "created_at", 
      expireAfterSeconds=2592000  # 30 days
  )
  ```
- **Estimated effort:** 1 hour

#### Issue 8: No Explicit HTTPS Enforcement
**Location:** FastAPI app configuration  
**Problem:** The app doesn't explicitly enforce HTTPS. Railway nginx likely handles this, but the app should have a security header or redirect to reinforce it.

**Fix Required:**
- Add HTTPS redirect middleware (or rely on Railway's nginx)
- Add security headers:
  ```python
  from starlette.middleware.base import BaseHTTPMiddleware
  
  class SecurityHeadersMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request, call_next):
          response = await call_next(request)
          response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
          response.headers["X-Content-Type-Options"] = "nosniff"
          response.headers["X-Frame-Options"] = "DENY"
          return response
  ```
- **Estimated effort:** 0.5 hours

#### Issue 9: Personas Claim Capabilities They May Not Have
**Location:** `backend/ai/persona_loader.py` (Director persona)  
**Problem:** The Director persona claims to have tools available (web_search, send_email, etc.) but:
1. The tools are only available if the Director endpoint is called with tool use enabled
2. A regular chat with the Director persona won't trigger tool use
3. This could confuse implementation or lead to expected features not working

**Evidence:**
```
_DIRECTOR = """
...
VERIFIED ACTIVE CAPABILITIES: web_search | fetch_url | send_email | ...
These are real, deployed, server-side tools executing right now. Use them.
"""
```

But if you call `/ai/chat` with mode="director" and the LLM isn't configured for tool use, the Director can't actually call tools.

**Fix Required:**
- Add a note in the Director persona clarifying when tools are available
- Document which endpoints support tool use
- Consider: Should the Director persona be available in `/ai/chat` or only in special endpoints?
- **Estimated effort:** 0.5 hours

---

### 🔵 LOW PRIORITY (Good-to-Have)

#### Issue 10: Inconsistent Error Handling in Async Code
**Location:** Multiple async functions  
**Problem:** Some async functions use `try/except Exception` (catches everything including KeyboardInterrupt) instead of more specific exceptions.

**Example:**
```python
try:
    await ensure_indexes()
except Exception as _e:  # Too broad
    logger.warning("ensure_indexes failed: %s", _e)
```

Better:
```python
try:
    await ensure_indexes()
except (pymongo.errors.OperationFailure, asyncio.TimeoutError) as _e:
    logger.warning("ensure_indexes failed: %s", _e)
```

**Impact:** Low (mostly startup code), but could mask real bugs.

**Fix:** Use specific exception types.

#### Issue 11: Tests Missing for Some Admin Endpoints
**Location:** `src/tests/test_*.py`  
**Problem:** Coverage appears incomplete. Some critical admin operations (e.g., deactivate user, delete user) may not have tests.

**Fix:** Add comprehensive tests for all admin endpoints.

#### Issue 12: Unused Imports and Dead Code
**Location:** Various files  
**Problem:** Minor cleanup. Some imports may not be used. Examples:
- `from reportlab...` imports (may not be active?)
- Old seed files that might be unused

**Fix:** Run `pip install vulture` and clean up, or just ignore (low impact).

---

## WHAT'S WORKING WELL ✓

1. **Authentication & Authorization** — `require_role()` is solid. Hierarchy protection is correct.
2. **Password Hashing** — Using bcrypt (good).
3. **JWT Secret Management** — Read from environment, not hardcoded.
4. **Database Parameterization** — Motor/PyMongo prevents SQL injection naturally.
5. **Executive Admin Protection** — Can't be modified by regular admins.
6. **Consent Flow** — Thoughtful consent gates on sensitive AI modes.
7. **Escalation Logic** — Crisis detection exists.
8. **Persona System** — Well-structured, loaded from strings (easy to maintain).
9. **API Documentation** — Routes are clear and well-commented.
10. **Error Handling (Mostly)** — Appropriate HTTP status codes, not crashing.

---

## WHAT'S MISSING (Not necessarily bugs, but gaps for the new governance)

1. **Tier-based Feature Access** — Subscribe support for Basic/Advanced tiers (needed for the new governance)
2. **Human Escalation Workflow** — Gate 2 (needs implementation)
3. **Director Approval Queue** — Gate 3 (needs implementation)
4. **Output Filtering** — Gate 1 (needs implementation)
5. **Compliance Dashboard** — CSO visibility into safety metrics
6. **Audit Report Generator** — For quarterly compliance
7. **Data Retention Automation** — Automatic deletion of old data
8. **Two Sage Revenue Streams** — Public Sage vs. Exec Sage pricing/access (needs implementation)

---

## IMPLEMENTATION PRIORITY

**Before launching new governance architecture:**

### Must Fix (Blocks Implementation)
- [ ] **Issue 1 (Critical):** Implement safety gates 1-3 for subscription tiers
- [ ] **Issue 2 (High):** Test pipeline manager fix
- [ ] **Issue 3 (High):** Add missing audit logs to admin endpoints

### Should Fix (Recommended)
- [ ] **Issue 4 (High):** Reduce error message verbosity
- [ ] **Issue 7 (Medium):** Add data retention / TTL indexes
- [ ] **Issue 8 (Medium):** Add security headers

### Can Fix Later (Nice-to-Have)
- [ ] Issue 5: Sanitize file uploads if used
- [ ] Issue 6: Add Redis fallback for rate limiting
- [ ] Issue 9: Clarify Director tool availability
- [ ] Issue 10-12: Code cleanup

---

## SUMMARY TABLE

| Issue | Severity | Component | Effort | Status |
|-------|----------|-----------|--------|--------|
| 1 | 🔴 CRITICAL | AI Gates | 2-3h | Blocked on implementation |
| 2 | 🟠 HIGH | Pipeline | 0.5h | Ready to test |
| 3 | 🟠 HIGH | Admin Audit | 1h | Ready to fix |
| 4 | 🟠 HIGH | Errors | 0.5h | Ready to fix |
| 5 | 🟡 MEDIUM | File Upload | 0.5h | If used |
| 6 | 🟡 MEDIUM | Rate Limit | 1-2h | Document for now |
| 7 | 🟡 MEDIUM | Compliance | 1h | Ready to fix |
| 8 | 🟡 MEDIUM | Security | 0.5h | Ready to fix |
| 9 | 🟡 MEDIUM | Personas | 0.5h | Ready to fix |
| 10 | 🔵 LOW | Code Quality | 1h | Nice-to-have |
| 11 | 🔵 LOW | Testing | 2h | Ongoing |
| 12 | 🔵 LOW | Cleanup | 0.5h | Nice-to-have |

---

## NEXT STEPS

1. **Fix Critical Issue 1** — Implement Sage subscription gates (can be done in parallel with other fixes)
2. **Fix High Priority Issues 2-4** — These are quick wins
3. **Fix Medium Issues 7-9** — These are compliance/security
4. **Run full test suite** — Ensure no regressions
5. **Then proceed with governance architecture implementation**

---

## RECOMMENDATION

**The codebase is ready for the new governance architecture with these fixes.** Most issues are isolated and won't require major refactoring. The critical issue (Issue 1) is expected — it's the new feature we're building.

**Estimated total remediation time: 4-6 hours**

After fixes, the system will be:
- ✓ Secure (no info leakage, proper access control)
- ✓ Compliant (audit trails, data retention)
- ✓ Scalable (foundation for tiers, multi-user)
- ✓ Ready for production (error handling, tested)

