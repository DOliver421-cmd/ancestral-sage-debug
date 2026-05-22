# SYSTEM VERIFICATION, TESTING & BREAK PLAN

**Goal:** Verify WAI-Institute system actually works, try to break it, fix what breaks

**Status:** COMPREHENSIVE TEST PLAN READY

---

## PART 1: VERIFICATION CHECKLIST (Does It Work?)

### Auth System ✓/✗
```
[ ] Can Delon login to account 1: delon.oliver@lightningcityelectric.com?
[ ] Can Delon login to account 2: youpickeddoliver@gmail.com?
[ ] Can Delon login to account 3: souppoetry@gmail.com?
[ ] Are tokens valid (not expired)?
[ ] Can recover account with recovery codes?
[ ] Can reset password (if forgotten)?
```

### M.O.R.E. Help Center ✓/✗
```
[ ] Can student access Helper AI?
[ ] Does Helper respond to financial questions?
[ ] Does Helper respond to legal questions?
[ ] Does Helper respond to government program questions?
[ ] Does Guardian moderate (flag inappropriate)?
[ ] Can flagged content be reviewed + corrected?
```

### Educational System ✓/✗
```
[ ] Can student enroll in Module 1 (Safety-LOTO)?
[ ] Can student access course materials?
[ ] Can student complete module quiz?
[ ] Can student track progress?
[ ] Do competencies update after quiz pass?
[ ] Can student see credentials earned?
```

### Director System ✓/✗
```
[ ] Can Delon access /api/exec/staff-meeting endpoint?
[ ] Does Director respond to morning briefing request?
[ ] Does Director route to correct personas?
[ ] Does The 9 synthesis work (high priority request)?
[ ] Can Delon set Director mode (conservative/aggressive)?
[ ] Are responses logged + retrievable?
```

### Billing System ✓/✗
```
[ ] Can student add payment method (Stripe test)?
[ ] Can student subscribe to BASIC tier ($9.99)?
[ ] Is subscription created in database?
[ ] Is invoice generated?
[ ] Is charge successful in Stripe?
[ ] Can creator see earnings tracked?
[ ] Can Delon view financial reports (admin)?
```

### Security ✓/✗
```
[ ] Are non-admins blocked from /api/billing/reporting/*?
[ ] Do payment methods get masked (****6789)?
[ ] Are audit logs created for sensitive access?
[ ] Can Delon export audit logs?
[ ] Are recovery codes working?
[ ] Is password hashing working (bcrypt)?
```

---

## PART 2: BREAK TESTS (Try to Crash It)

### Stress Test — High Concurrency
```
[ ] Simulate 100 simultaneous logins
[ ] Simulate 50 concurrent subscriptions
[ ] Simulate 20 concurrent file uploads
Expected: No 502, all operations succeed
Risk: Connection pool exhaustion, timeout
```

### Edge Cases — Invalid Input
```
[ ] Subscribe with negative amount
[ ] Create user with SQL injection in name: "'; DROP TABLE users; --"
[ ] Create course with 10MB description
[ ] Upload 1GB file (should reject)
[ ] Send 1000 concurrent requests from one IP
Expected: 400/422 errors, not 500
Risk: Injection, buffer overflow, DoS
```

### Database Failures
```
[ ] Unplug MongoDB connection mid-transaction
[ ] Fill database disk to 99%
[ ] Delete payment_methods collection (with live subscriptions)
[ ] Set TTL indexes to expire data instantly
Expected: Graceful degradation, error logging, recovery
Risk: Data loss, corruption, inconsistency
```

### Encryption Edge Cases
```
[ ] Decrypt with wrong key
[ ] Decrypt null value
[ ] Encrypt value, change value in DB, try to decrypt
[ ] Fill encryption cache
Expected: Graceful fallback, logging, no crashes
Risk: Data loss, system crash
```

### Payment Processing Attacks
```
[ ] Charge same card twice in 1 second
[ ] Cancel subscription, re-enroll, request refund
[ ] Create subscription, change tier 10 times (proration hell)
[ ] Attempt chargeback after 6 months
Expected: System handles idempotently, logs all
Risk: Financial loss, duplicate charges
```

### Access Control Bypass
```
[ ] Student tries to access /api/admin/users (should 403)
[ ] Student tries to access /api/billing/reporting (should 403)
[ ] Token expired, try to use it (should 401)
[ ] Admin token used by student (impersonation attempt)
[ ] JWT modified (signature invalid)
Expected: All rejected with proper error codes
Risk: Data breach, unauthorized access
```

### Frontend Attack Surface
```
[ ] XSS: Input "<script>alert('xss')</script>" in course title
[ ] CSRF: Try form submission without token
[ ] Session fixation: Force session ID reuse
[ ] Clickjacking: Embed /api endpoint in iframe
Expected: All blocked or sanitized
Risk: Account takeover, data theft
```

---

## PART 3: SYSTEM HEALTH CHECK (Automated Daily)

Create `GET /api/admin/system-health` endpoint:

```json
{
  "timestamp": "2026-05-22T15:30:00Z",
  "status": "healthy|degraded|critical",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 45,
      "connections_used": 8,
      "connections_max": 20,
      "collections": 25,
      "indexed": true
    },
    "stripe": {
      "status": "healthy",
      "test_mode": true,
      "last_charge": "2026-05-22T14:00:00Z"
    },
    "storage": {
      "status": "healthy",
      "disk_used_percent": 45,
      "audit_logs_size_gb": 2.3,
      "backups_latest": "2026-05-22T10:00:00Z"
    },
    "auth": {
      "status": "healthy",
      "jwt_signing": true,
      "recovery_codes_valid": 47
    },
    "director": {
      "status": "healthy",
      "personas_responding": 12,
      "tools_available": 8,
      "last_request": "2026-05-22T15:15:00Z"
    },
    "api": {
      "status": "healthy",
      "endpoints_responding": 89,
      "errors_24h": 0,
      "latency_p95_ms": 280
    }
  },
  "alerts": [
    {
      "severity": "warning",
      "component": "storage",
      "message": "Disk usage at 45%, monitor for growth"
    }
  ]
}
```

---

## PART 4: TEST SCENARIOS (Real User Workflows)

### Scenario A: New Student Signup → Payment → Course Completion
```
1. [ ] Create account with email (student@example.com)
2. [ ] Verify email
3. [ ] Login
4. [ ] View course catalog
5. [ ] Click "Start Module 1"
6. [ ] Complete lesson 1
7. [ ] Take quiz (4 questions)
8. [ ] Pass quiz (70% required)
9. [ ] See progress updated (25% of module)
10. [ ] Click "Upgrade to ADVANCED" ($29.99)
11. [ ] Add payment method (Stripe test card: 4242 4242 4242 4242)
12. [ ] Complete payment
13. [ ] See invoice in email
14. [ ] Access premium content
15. [ ] Continue modules 2-12
16. [ ] Request certification exam ($49)
17. [ ] Pass exam (score 85%)
18. [ ] Download certificate
19. [ ] Share to LinkedIn

Expected: No errors, smooth flow, all data persisted
Time: 30 minutes (compressed)
```

### Scenario B: Creator Uploads Course → Gets Paid
```
1. [ ] Creator logs in
2. [ ] Navigate to /creator-courses/dashboard
3. [ ] Click "Create Course"
4. [ ] Enter title: "Python for Electricians"
5. [ ] Enter description, category, price ($49)
6. [ ] Upload lesson 1 (video + notes)
7. [ ] Publish course
8. [ ] Add to marketplace (make discoverable)
9. [ ] Share link
10. [ ] Student enrolls + pays $49
11. [ ] Creator sees $34.30 (70%) in dashboard
12. [ ] Creator requests payout
13. [ ] Check bank account (Stripe test)

Expected: Money transfers correctly (30% to WAI, 70% to creator)
Risk: Proration errors, double-charging
```

### Scenario C: Delon Uses Director for Decision
```
1. [ ] Delon logs in
2. [ ] Asks: "Should we launch corporate training?"
3. [ ] Director routes to:
   - Revenue Director: "What's the market size?"
   - Product Designer: "Can we customize curriculum?"
   - PRT Enforcer: "Is this mission-aligned?"
   - Strategic Navigator: "What's the competitive advantage?"
4. [ ] Delon receives 4 perspectives
5. [ ] Asks The 9: "Integrated recommendation?"
6. [ ] The 9 synthesizes all 12 personas
7. [ ] Delon reads briefing, makes decision
8. [ ] Decision logged + emailed

Expected: Clear, actionable advice in <5 min response time
```

### Scenario D: Refund Request Flow
```
1. [ ] Student requests refund (within 7 days)
2. [ ] Support staff views request in queue
3. [ ] System calculates refund (proration + processing fees)
4. [ ] Automatic refund issued (within 7 days)
5. [ ] Subscriber notified via email
6. [ ] Refund appears in bank account (3-5 business days)
7. [ ] Delon reviews refund logs

Expected: Refund processed accurately, audit trail clean
Risk: Proration math errors, duplicate refunds
```

---

## PART 5: FAILURE RECOVERY TESTS

### Test: Database Connection Lost
```
[ ] Simulation: Kill MongoDB connection
[ ] Expected: Graceful error message to user
[ ] Expected: Automatic reconnect within 10 seconds
[ ] Expected: No data loss
[ ] Recovery: Auto-healthy? Or manual intervention?
```

### Test: Payment Gateway Timeout
```
[ ] Simulation: Stripe API hangs for 30 seconds
[ ] Expected: Transaction queued, user notified
[ ] Expected: Retry logic kicks in after 1 minute
[ ] Expected: If still hanging, escalate to Delon
[ ] Recovery: Manual payment processing procedure?
```

### Test: Email Delivery Failure
```
[ ] Simulation: GMAIL credentials invalid
[ ] Expected: Email queued to database
[ ] Expected: Retry every 5 minutes
[ ] Expected: Alert to Delon after 3 failures
[ ] Recovery: Update credentials, reprocess queue
```

### Test: Disk Space Critical
```
[ ] Simulation: Disk 95% full
[ ] Expected: Alert triggered
[ ] Expected: Archive old audit logs
[ ] Expected: Delon notified immediately
[ ] Recovery: Manual disk cleanup or add storage
```

---

## PART 6: PERFORMANCE BENCHMARKS

**Target Metrics:**
```
API Latency (p95):      < 300ms
Database Query (p95):   < 50ms
Page Load Time:         < 2 seconds
Auth Token Generation: < 10ms
Payment Processing:     < 5 seconds
Director Response Time: < 30 seconds
```

**How to Test:**
```bash
# Load test 100 simultaneous users
wrk -t4 -c100 -d30s https://api.wai-institute.com/api/auth/me

# Measure database latency
time mongodb_connection.ping()

# Check page load (frontend)
# Open Chrome DevTools → Network tab → measure
```

---

## PART 7: SECURITY AUDIT

### Checklist
```
[ ] No hardcoded secrets in code (grep for passwords)
[ ] No SQL injection vulnerabilities (all queries parameterized)
[ ] No XSS vulnerabilities (inputs sanitized)
[ ] No CSRF (CSRF tokens on forms)
[ ] No exposed sensitive data (password_hash never in response)
[ ] No CORS issues (only allow wai-institute.org)
[ ] HTTPS enforced (no http://)
[ ] Rate limiting on login (max 5/minute)
[ ] Session timeout (24 hours max)
[ ] Password requirements enforced (8+ chars)
```

### Penetration Test (Optional)
```
Hire security firm to test:
- Login bypass
- Payment manipulation
- Authorization bypass
- Data exfiltration
- DoS attacks

Cost: $2K-$5K
Timeline: 1-2 weeks
```

---

## EXECUTION PLAN

### This Week
```
[ ] Run Verification Checklist (2 hours)
[ ] Run Break Tests — Edge Cases (4 hours)
[ ] Document findings
[ ] Create issues for failures
```

### Next Week
```
[ ] Test Scenarios A-D (6 hours)
[ ] Database failure recovery tests (2 hours)
[ ] Security audit (4 hours)
[ ] Fix critical issues (ongoing)
```

### Month 2
```
[ ] Performance benchmarking (2 hours)
[ ] Load testing (2 hours)
[ ] Penetration test (if budget allows)
[ ] Final sign-off from Delon
```

---

## REPORTING

After each test phase, document:
1. **What was tested** (scenario, inputs, expected outcome)
2. **What actually happened** (pass/fail, actual outcome)
3. **Severity if failed** (critical/high/medium/low)
4. **Fix required** (what changes to code)
5. **Who fixes** (Claude, team, external)

Example:
```
TEST: Refund within 7 days
STATUS: FAIL
ISSUE: Proration calculation off by $0.47
SEVERITY: Medium (customer trust issue)
FIX: Fix proration math in calculate_proration()
OWNER: Claude
```

---

## SUCCESS CRITERIA

System is "production-ready" when:
```
✓ All Verification Checklist items pass
✓ All Break Tests don't crash (handle gracefully)
✓ All Test Scenarios complete without errors
✓ All Failure Recovery tests work
✓ All Performance benchmarks met
✓ All Security audit items pass
✓ Delon signs off: "I trust this system with real money"
```

---

## NEXT IMMEDIATE STEPS

1. **Today:** Run verification checklist (30 min)
2. **Tomorrow:** Test end-to-end transaction (4 hours)
3. **This week:** Complete break tests (8 hours)
4. **Next week:** Test all scenarios + recovery (8 hours)

If everything passes → ready to launch with real students/money.

If failures found → fix, retest → then launch.

---

**Prepared by:** Claude + DoIt Engine  
**For:** Delon Oliver  
**Status:** READY TO EXECUTE
