# End-to-End Transaction Test Plan — EXECUTION READY

**Goal:** Verify that a student can subscribe, pay, and receive a certificate  
**Timeline:** 4 hours (one session)  
**Status:** READY TO RUN THIS WEEK

---

## TEST ENVIRONMENT

**Stripe Mode:** Test (not live charges)  
**Test Card:** 4242 4242 4242 4242 (always succeeds in test mode)  
**Test Email:** test-student@wai-institute.com  
**Password:** TestPassword123!

---

## TEST SCENARIO: Complete Student Journey

### PHASE 1: SIGNUP (30 minutes)

**Step 1.1: Create Student Account**
```
[ ] Navigate to: https://wai-institute-production.railway.app
[ ] Click "Sign Up"
[ ] Email: test-student@wai-institute.com
[ ] Password: TestPassword123!
[ ] Name: Test Student
[ ] Click "Register"
[ ] Verify: Welcome email received
```

**Expected Result:** Account created, student logged in, on dashboard

**Verify in Database:**
```bash
db.users.findOne({email: "test-student@wai-institute.com"})
→ Should show: id, email, name, role="student", is_active=true
```

---

### PHASE 2: SUBSCRIPTION (45 minutes)

**Step 2.1: View Subscription Options**
```
[ ] Navigate to: /api/billing/pricing (or frontend pricing page)
[ ] See 4 tiers: BASIC, ADVANCED, PREMIUM, ENTERPRISE
[ ] BASIC: $9.99/month
[ ] ADVANCED: $29.99/month
[ ] PREMIUM: $99.99/month
```

**Step 2.2: Add Payment Method**
```
[ ] Click "Add Payment Method"
[ ] Card number: 4242 4242 4242 4242
[ ] Exp: 12/25
[ ] CVC: 123
[ ] Billing zip: 12345
[ ] Click "Save"
[ ] Verify: Payment method stored + last 4 showing (****4242)
```

**Verify in Database:**
```bash
db.payment_methods.findOne({user_id: "test-student-id"})
→ Should show: type="card", last_4="4242", stripe_payment_method_id
```

**Step 2.3: Subscribe to BASIC Tier ($9.99/mo)**
```
[ ] Click "Subscribe to BASIC"
[ ] Select billing cycle: MONTHLY
[ ] Click "Confirm Payment"
[ ] Wait for Stripe response (should be <5 seconds)
[ ] Verify: "Subscription active" message
[ ] Verify: Welcome email received (with receipt)
```

**Verify in Database:**
```bash
db.subscriptions.findOne({user_id: "test-student-id"})
→ Should show: 
   tier="basic"
   status="active"
   billing_cycle="monthly"
   stripe_subscription_id=[VALID_ID]
   billing_period_end=[30_DAYS_FROM_NOW]
```

**Verify in Stripe (test dashboard):**
```
Dashboard → Test mode → Subscriptions
→ Find subscription for test-student@wai-institute.com
→ Status should be "Active"
→ Amount: $9.99
```

---

### PHASE 3: COURSE ACCESS (30 minutes)

**Step 3.1: Access Module 1**
```
[ ] Navigate to: /api/modules or course list
[ ] Find "Module 1: Electrical Safety & Lockout/Tagout"
[ ] Click "View Module"
[ ] Verify: Can see lessons (Lesson 1.1, 1.2, 1.3, etc.)
[ ] Verify: Can access video (if embedded)
[ ] Verify: Can download PDF materials
```

**Step 3.2: Complete Module 1 Quiz**
```
[ ] Click "Take Quiz"
[ ] Answer 4 questions (randomized or static)
[ ] Score needed: 70%+ to pass
[ ] Submit answers
[ ] Verify: Score displayed (e.g., "You scored 75%")
[ ] Verify: "Module complete" badge shown
```

**Verify in Database:**
```bash
db.progress.findOne({user_id: "test-student-id", module_slug: "safety-loto"})
→ Should show:
   status="completed"
   score=75 (or whatever you scored)
   completed_at=[TIMESTAMP]
```

---

### PHASE 4: INVOICE & RECEIPT (15 minutes)

**Step 4.1: Check Invoice**
```
[ ] Navigate to: /api/billing/invoices or billing dashboard
[ ] Find invoice for subscription
[ ] Verify: Invoice number, date, amount ($9.99), status="paid"
[ ] Verify: Payment method (Visa ****4242)
[ ] Verify: Billing period (May 22 - June 21, 2026)
```

**Verify in Database:**
```bash
db.invoices.findOne({subscription_id: "[SUBSCRIPTION_ID]"})
→ Should show:
   status="paid"
   amount_due=9.99
   amount_paid=9.99
   stripe_invoice_id=[VALID_ID]
```

**Step 4.2: Check Email Receipt**
```
[ ] Check email: test-student@wai-institute.com
[ ] Verify: Receipt email received
[ ] Verify: Email contains:
   - Amount: $9.99
   - Billing period
   - How to download certificate
   - How to access courses
   - How to request refund
```

---

### PHASE 5: AUDIT LOGGING (10 minutes)

**Step 5.1: Verify Audit Log**
```bash
db.audit_log.findOne({action: "subscription.created", target: "test-student-id"})
→ Should show:
   actor_id=[ADMIN_OR_SYSTEM]
   action="subscription.created"
   target="test-student-id"
   meta={tier: "basic", cycle: "monthly", amount: 9.99}
   severity="high" or "medium"
   at=[TIMESTAMP]
```

**Step 5.2: Verify Financial Metrics Updated**
```bash
db.creator_earnings.findOne() or financial snapshot
→ Should show:
   new_subscriber_count=1
   new_mrr=[9.99 or accumulated]
   churn_count=0
```

---

### PHASE 6: STRIPE VERIFICATION (10 minutes)

**In Stripe Dashboard (test mode):**

```
[ ] Go to: Dashboard → Test mode → Payments
[ ] Find charge for test-student@wai-institute.com
[ ] Verify: Amount: $9.99 USD
[ ] Verify: Status: Succeeded (green checkmark)
[ ] Verify: Payment method: Visa ending in 4242
[ ] Verify: Timestamp: (should match subscription create time)

[ ] Go to: Dashboard → Test mode → Subscriptions
[ ] Find subscription for test-student@wai-institute.com
[ ] Verify: Status: Active
[ ] Verify: Plan: Monthly ($9.99)
[ ] Verify: Billing cycle anchor: May 22
[ ] Verify: Cancel at period end: false
```

---

### PHASE 7: REFUND TEST (15 minutes)

**Step 7.1: Request Refund (Within 7 Days)**
```
[ ] Email: refund@wai-institute.com
[ ] Subject: "Refund Request — test-student@wai-institute.com"
[ ] Body: "I request a full refund within 7 days of purchase"
[ ] Send

[ ] Verify: Automated response received within 1 hour
[ ] Wait: 24 hours for Delon to process
```

**Step 7.2: Verify Refund Processed**
```
[ ] Check: Payment method account (should show -$9.99 refund pending)
[ ] Check: Stripe dashboard → Refunds
   → Should show $9.99 refund for original charge
[ ] Check: Database
   db.subscriptions.findOne({user_id: "test-student-id"})
   → status should be "cancelled" or "refunded"
[ ] Check: Email
   → Receipt of refund processed email
```

**Verify in Stripe:**
```
Dashboard → Payments → [Original Charge]
→ Should show refund of $9.99 (full)
→ Refund status: Succeeded
→ Refund in: 3-5 business days
```

---

## FAILURE MODES & RECOVERY

If any step fails, **STOP and document:**

### Common Failures

**Stripe Fails to Authorize:**
- Check: Test card number correct (4242 4242 4242 4242)?
- Check: Expiration > today?
- Check: CVC is any 3 digits?
- Try: Different test card (see Stripe docs for test cards)
- Escalate: Something wrong with Stripe integration

**Subscription Created But No Invoice:**
- Check: Payment succeeded in Stripe?
- Check: Invoice creation endpoint exists?
- Check: Database query: `db.invoices.find({subscription_id: "..."})`
- If empty: Invoice creation failed → needs debugging
- Fix: Call invoice creation endpoint manually or check cron job

**Audit Log Missing:**
- Check: Audit function exists and is called?
- Check: Database has audit_log collection?
- Check: Database permissions?
- Fix: Manually create audit log entry (for testing) or debug function

**Email Not Sent:**
- Check: GMAIL_USER + GMAIL_APP_PASSWORD set in Railway?
- Check: Email queued in database?
- Check: Cron job for email delivery running?
- Workaround: Manually send email (for testing)

---

## SUCCESS CRITERIA

Test passes when ALL of these are true:

```
✅ Student account created
✅ Payment method added + masked correctly
✅ Subscription created (Stripe + database)
✅ Invoice generated + marked "paid"
✅ Courses accessible
✅ Module quiz passable
✅ Audit log entry created
✅ Welcome email received
✅ Receipt email received
✅ Refund request processed
✅ Refund issued (Stripe + database)
✅ Refund email received
```

If ALL 12 are ✅, system is production-ready.

If ANY are ❌, system needs fixes before going live.

---

## TIMELINE & EFFORT

**Phase 1 (Signup):** 30 min  
**Phase 2 (Subscription):** 45 min  
**Phase 3 (Course Access):** 30 min  
**Phase 4 (Invoice):** 15 min  
**Phase 5 (Audit):** 10 min  
**Phase 6 (Stripe Verify):** 10 min  
**Phase 7 (Refund):** 15 min + 24 hours waiting  

**Total Active Time:** 2 hours  
**Total Calendar Time:** 24+ hours (for refund processing)

---

## POST-TEST DOCUMENTATION

After test completes, document:

```markdown
## E2E Transaction Test Results — [DATE]

**Overall Status:** ✅ PASSED / ⚠️ ISSUES / ❌ FAILED

**Results:**
- ✅ Signup: PASSED
- ✅ Payment: PASSED
- ✅ Subscription: PASSED
- ✅ Course Access: PASSED
- ✅ Quiz: PASSED
- ✅ Invoice: PASSED
- ✅ Audit Log: PASSED
- ✅ Email: PASSED
- ✅ Refund: PASSED

**Issues Found:**
1. [Issue 1 + how to reproduce]
2. [Issue 2 + how to reproduce]

**Fixes Applied:**
1. [Fix for issue 1]
2. [Fix for issue 2]

**Sign-Off:** Delon Oliver — [APPROVED / NEED RETESTING]

**Conclusion:** [Ready for live / Not ready, need X fixes first]
```

---

## NEXT STEPS (After Test)

If test **PASSES:**
1. ✅ Switch Stripe to LIVE mode
2. ✅ Update pricing to show real prices
3. ✅ Launch with corporate sales
4. ✅ Accept first paying customers
5. ✅ Monitor first week closely

If test **FAILS:**
1. ❌ Document failures
2. ❌ Fix issues
3. ❌ Re-run test
4. ❌ Repeat until all ✅

---

**Status:** Ready to execute this week  
**Owner:** Claude (with Delon reviewing results)  
**Timeline:** Pick a date (1 afternoon + 24 hours for refund)
