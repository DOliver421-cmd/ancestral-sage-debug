# SECURITY AUDIT REPORT: WAI Institute
**Date:** May 22, 2026  
**Auditor:** Independent Security Review  
**Risk Level:** CRITICAL (14 critical issues, 12 high-risk issues)

---

## EXECUTIVE SUMMARY

The WAI Institute platform has a **strong foundational security model** (RBAC, encryption requirements, audit logging) but suffers from **critical implementation gaps** that could lead to:
- Unauthorized access to creator payouts and financial data
- Privilege escalation (student → steward → director)
- Data leakage through unprotected endpoints
- Account takeover via hardcoded credentials
- Full authorization bypass on public endpoints

**Verdict:** NOT PRODUCTION-READY. Requires immediate fixes before launch.

---

## CRITICAL ISSUES

### 🔴 CRITICAL-1: Hardcoded Executive Admin Credentials

**File:** `backend/server.py:685-710`

**Issue:**
```python
BACKUP_EXEC_EMAIL = "youpickeddoliver@gmail.com"
BACKUP_EXEC_DEFAULT_PASSWORD = "..."  # In code or env

# Every startup, recreates/resets account
if existing_backup:
    if EXEC_FORCE_RESET:
        _upd["password_hash"] = hash_pw(BACKUP_EXEC_DEFAULT_PASSWORD)
```

**Risk:**
- Backup executive admin account created on every startup
- If password leaked/exposed, anyone can become director
- `EXEC_FORCE_RESET` flag in code forces password reset even if already changed
- Creates **two** hardcoded director accounts (primary + backup)

**Fix:**
```python
# ❌ WRONG: This code
# backend/server.py (remove this entire section)

# ✅ CORRECT: Replace with
async def bootstrap_exec_admin():
    """
    ONE-TIME bootstrap only. Should not run on every startup.
    """
    SEED_FILE = Path("./.exec_admin_bootstrapped")
    
    if SEED_FILE.exists():
        logger.info("Executive admin already bootstrapped. Skipping.")
        return
    
    # Create one admin account from env variable
    exec_email = os.environ.get("EXEC_ADMIN_EMAIL")
    if not exec_email:
        logger.warning("EXEC_ADMIN_EMAIL not set. Skipping bootstrap.")
        return
    
    # Generate temporary password (force user to set their own)
    temp_password = secrets.token_urlsafe(16)
    
    await db.users.insert_one({
        "id": str(uuid.uuid4()),
        "email": exec_email,
        "full_name": "Executive Admin",
        "role": "executive_admin",
        "password_hash": hash_pw(temp_password),
        "must_change_password": True,  # Force password change on first login
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    
    logger.critical("Executive admin created: %s (password in startup logs or env)", exec_email)
    logger.critical("Temporary password: %s", temp_password)  # Or send via Slack/email
    
    # Mark bootstrap complete
    SEED_FILE.touch()

# Call ONCE on initial startup:
# if not db_already_initialized:
#     await bootstrap_exec_admin()
```

**Compliance Impact:**
- SOC 2: Hardcoded credentials violate access control requirements
- GDPR: Account with hardcoded password is a data breach waiting to happen

---

### 🔴 CRITICAL-2: Missing Authorization on Course Endpoints

**File:** `backend/billing/creator_course_routes.py:51-70`

**Issue:**
```python
@router.post("/create")
async def create_new_course(
    creator_id: str,  # ❌ Client-provided, never verified!
    title: str,
    description: str,
    course_type: str,
    category: str,
    request: Request,
    language: str = "en",
):
    """Create a new course draft"""
    db = request.app.state.db
    
    # No authentication check!
    # No verification that creator_id == current_user.id
    
    result = await create_course(db, creator_id, title, description, ...)
```

**Risk:**
- Any authenticated user can pass any `creator_id` and create courses on another user's account
- Student can create courses as Creator
- Attacker can enumerate all user IDs and create content for them
- **Privilege escalation:** Student (role) creates course claiming to be Creator

**Attack Flow:**
```
1. Student logs in (bearer token for user_123)
2. POST /api/creator-courses/create
   {
     "creator_id": "attacker_user_id",  // Different from logged-in user
     "title": "Malware Course",
     "course_type": "electrical"
   }
3. Course is created under attacker_user_id
4. Attacker is now credit for student's creation
```

**Fix:**
```python
from server import current_user  # Import auth dependency

@router.post("/create")
async def create_new_course(
    course_data: CourseCreate,  # Pydantic model, no creator_id
    current_user: User = Depends(current_user),  # ✅ Verify identity
    request: Request,
):
    """Create a new course draft"""
    db = request.app.state.db
    
    # Verify user has creator role
    if current_user.role not in ["creator", "mentor", "steward", "elder", "admin"]:
        raise HTTPException(status_code=403, detail="Must be creator to create courses")
    
    # Use current_user.id, NOT client-provided creator_id
    result = await create_course(
        db,
        creator_id=current_user.id,  # ✅ From auth, not request
        title=course_data.title,
        description=course_data.description,
        course_type=course_data.course_type,
        category=course_data.category,
        language=course_data.language,
    )
    
    if result["status"] != "success":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result
```

**ALL affected endpoints:**
- `/create` — missing auth
- `/course/{course_id}/lesson` — missing creator ownership check
- `/course/{course_id}/publish` — missing creator ownership check
- `/dashboard/{creator_id}` — missing auth (anyone can view any creator's financials)
- `/enroll` — missing auth (anyone can enroll anyone in courses)

---

### 🔴 CRITICAL-3: CRM Endpoints Completely Unprotected

**File:** `backend/crm/routes.py:25-100`

**Issue:**
```python
@router.post("/leads")
async def create_lead(
    lead_create: LeadCreate,
    request: Request  # NO AUTH!
):
    """Create a new sales lead"""
    leads = request.app.state.db.leads
    
    # Anyone can create leads with any company data
    lead_doc = {
        "company_name": lead_create.company_name,
        "decision_maker": lead_create.decision_maker.dict(),  # Can include phone, email
        # ...
    }
    result = await leads.insert_one(lead_doc)

@router.get("/leads")
async def list_leads(
    request: Request,
    status: Optional[str] = Query(None),
    # NO AUTH! Anyone can list all leads/sales pipeline
):
    """List leads with filtering"""
    leads = request.app.state.db.leads
    filter_query = {}
    # ... returns all leads
```

**Risk:**
- **Full CRM data breach:** Anyone can view all leads, opportunities, decision-makers
- **DoS:** Attacker can create 1M fake leads, crashing CRM
- **Data exfiltration:** All company information, contact details publicly accessible
- **Privacy violation:** Decision-maker emails/phones leaked

**Attack:**
```bash
# 1. List all sales leads (no auth needed)
curl https://api.wai-institute.com/api/crm/leads

# Returns all decision-makers, budgets, company info
[
  {
    "company_name": "Fortune 500 Corp",
    "decision_maker": {
      "name": "Jane Doe",
      "email": "jane@fortune500.com",
      "phone": "+1-555-0123"
    },
    "budget_range": "5-10M"
  }
]

# 2. Create 1000s of fake leads
for i in {1..10000}; do
  curl -X POST https://api.wai-institute.com/api/crm/leads \
    -d '{"company_name":"Fake '$i'"}'
done

# 3. Export all data
curl https://api.wai-institute.com/api/crm/leads?limit=10000 > crm_dump.json
```

**Fix:**
```python
from server import require_role, current_user

@router.post("/leads")
async def create_lead(
    lead_create: LeadCreate,
    request: Request,
    current_user: User = Depends(require_role("admin", "steward")),  # ✅ Only admins/stewards
):
    """Create a new sales lead (admins only)"""
    # ... rest of code

@router.get("/leads")
async def list_leads(
    request: Request,
    current_user: User = Depends(require_role("admin", "steward")),  # ✅ Only admins
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    score_min: int = Query(0),
    limit: int = Query(50, le=100),  # Also enforce limit
    skip: int = Query(0),
):
    """List leads (admin/steward only)"""
    leads = request.app.state.db.leads
    
    filter_query = {}
    
    if status:
        filter_query["status"] = status
    # ... rest of filtering
```

---

### 🔴 CRITICAL-4: Payment/Payout Data Exposure

**File:** `backend/billing/routes.py` (multiple endpoints)

**Issue:**
```python
@router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """Get the current user's active subscription"""
    subscription = await stripe_service.get_subscription(current_user["_id"])
    return subscription  # ❌ Returns payment method, last 4 digits, etc
```

**Risk:**
- Returns full subscription data (payment methods, billing history)
- No field-level filtering
- Endpoints may leak Stripe customer IDs (PII)
- No audit log of who accessed financial data

**Fix:**
```python
from security.rbac import AccessControl, UserRole

@router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """Get the current user's active subscription"""
    subscription = await stripe_service.get_subscription(current_user["_id"])
    
    if not subscription:
        return None
    
    # ✅ Filter sensitive fields
    safe_subscription = {
        "tier": subscription.get("tier"),
        "billing_cycle": subscription.get("billing_cycle"),
        "status": subscription.get("status"),
        "current_period_end": subscription.get("current_period_end"),
        "next_billing_date": subscription.get("next_billing_date"),
        # ❌ DON'T return:
        # - full payment method details
        # - card numbers (even last 4)
        # - Stripe customer ID
        # - billing address
    }
    
    # ✅ Log access to financial data
    await audit(
        user_id=current_user["_id"],
        action="subscription_viewed",
        resource=f"subscription:{current_user['_id']}",
        details={"subscription_id": subscription.get("id")}
    )
    
    return safe_subscription
```

---

### 🔴 CRITICAL-5: Missing CSRF Protection with Credentials

**File:** `backend/server.py:8210-8216`

**Issue:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,  # ✅ Good
    allow_origins=_cors_origins,     # ✅ Good
    allow_methods=["*"],              # ❌ Problem
    allow_headers=["*"],              # ❌ Problem
)
```

**Risk:**
- `allow_credentials=True` + Bearer tokens + `allow_methods=["*"]` = CSRF possible
- Browser can make requests from `evil.com` to `wai-institute.com`
- No CSRF token validation
- Any state-changing operation (POST, DELETE, PATCH) is vulnerable

**Attack:**
```html
<!-- On evil.com -->
<img src="https://api.wai-institute.com/api/admin/users/user123/password" 
     onerror="alert('CSRF')">

<!-- Or in form submission -->
<form action="https://api.wai-institute.com/api/users/me/email" method="POST">
  <input name="new_email" value="attacker@evil.com">
</form>
<script>document.forms[0].submit();</script>
```

**Fix:**
```python
# ✅ CORRECT: Restrict methods
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["GET", "OPTIONS", "HEAD"],  # ✅ Only safe methods
    allow_headers=["Authorization", "Content-Type"],  # ✅ Whitelist needed headers
)

# For state-changing operations, require CSRF token
from fastapi import Header

@router.post("/users/me/email")
async def change_email(
    new_email: str,
    csrf_token: str = Header(...),  # ✅ Require CSRF token
    current_user: User = Depends(current_user),
):
    # Verify CSRF token in session
    if not verify_csrf_token(current_user.id, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    # ... change email
```

---

### 🔴 CRITICAL-6: Partnership Level Client-Controlled

**File:** `frontend/src/lib/security.js:186-217`

**Issue:**
The partnership level is computed/displayed on frontend, but backend must validate:

```javascript
// ❌ DANGEROUS: Frontend decides partnership level
export function canAccessFeature(partnershipLevel, feature) {
  // But partnershipLevel comes from where? 
  // If it comes from JWT or client state, it can be forged
}
```

**Risk:**
- If partnership level is in JWT token, user can modify it (JWT is base64, not encrypted)
- User can claim partnership level 5000 points without earning it
- Can access governance voting, allocate funds, access elder features

**Fix:**
```python
# ✅ CORRECT: Backend computes partnership level from history
async def get_user_partnership(user_id: str) -> int:
    """
    Compute partnership points from AUDIT LOG, not from user field.
    User cannot forge what they earned.
    """
    logs = await db.audit_logs.find({
        "user_id": user_id,
        "action": {"$in": [
            "course_completed",
            "forum_post_helpful",
            "mentored_user",
            "course_published",
            "voted_proposal"
        ]}
    }).to_list(None)
    
    points = 0
    for log in logs:
        points += POINT_VALUES.get(log["action"], 0)
    
    return points

@router.get("/user/me/partnership")
async def get_my_partnership(
    current_user: User = Depends(current_user)
):
    """Get current user's verified partnership points"""
    points = await get_user_partnership(current_user["_id"])
    level = get_partnership_level(points)
    
    return {
        "points": points,
        "level": level,
        "verified_at": datetime.now().isoformat()
    }

# Never store partnership in JWT or in User.partnership_level client-side
```

---

### 🔴 CRITICAL-7: No Rate Limiting Enforcement

**File:** `backend/server.py:183`

**Issue:**
```python
# Simple in-memory rate limit (per IP, per route) — replace with redis in true HA prod
from collections import defaultdict as _dd

# ✅ Comment says it exists but...
# Where is it actually used on endpoints?
# Not found on admin endpoints!
# Not found on course endpoints!
```

**Risk:**
- Attackers can brute-force passwords (admin/users/register)
- Create 1M fake courses/leads
- Spam forum/messaging
- API DDoS

**Fix:**
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import Redis

# Initialize Redis rate limiting
redis_client = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost"))
await FastAPILimiter.init(redis_client)

# Apply to all endpoints
@router.post("/auth/register")
@app.limiter.limit("3/minute")  # Max 3 registrations per minute per IP
async def register(email: str):
    pass

@router.post("/courses/create")
@app.limiter.limit("5/day")  # Max 5 courses per day per user
async def create_course(...):
    pass

@router.post("/admin/users")
@app.limiter.limit("10/hour")  # Max 10 user creates per hour per admin
async def create_user(...):
    pass
```

---

### 🔴 CRITICAL-8: No Request Validation/Sanitization

**File:** `backend/crm/routes.py:25-70`

**Issue:**
```python
@router.post("/leads")
async def create_lead(
    lead_create: LeadCreate,
    request: Request
):
    lead_doc = {
        "company_name": lead_create.company_name,  # ❌ No max length
        "decision_maker": lead_create.decision_maker.dict(),  # ❌ No validation
        "notes": lead_create.notes,  # ❌ Could be 10MB of text
    }
    result = await leads.insert_one(lead_doc)  # Could create 1GB documents
```

**Risk:**
- MongoDB injection (though Pydantic helps)
- Resource exhaustion (create gigantic documents)
- Buffer overflow attacks
- NoSQL injection if query construction is vulnerable

**Fix:**
```python
from pydantic import BaseModel, Field

class DecisionMaker(BaseModel):
    name: str = Field(..., max_length=200)
    title: str = Field(..., max_length=100)
    email: str = EmailStr
    phone: str = Field(..., regex=r"^\+?1?\d{9,15}$")

class LeadCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    company_size: int = Field(..., ge=1, le=1000000)
    industry: str = Field(..., max_length=100)
    budget_range: BudgetRange
    decision_maker: DecisionMaker
    source: LeadSource
    notes: str = Field(default="", max_length=5000)  # Max 5000 chars

# Pydantic will now validate all fields automatically
```

---

### 🔴 CRITICAL-9: Incomplete Audit Logging

**File:** `backend/SECURITY_AND_RBAC.md:154-169`

**Issue:**
```markdown
# Audit events
- User role changed: admin_id, user_id, old_role, new_role
- Payout requested: creator_id, amount, date
- Course published: creator_id, course_id, price
- User banned: moderator_id, user_id, reason
- Financial report accessed: admin_id, timestamp
- Course deleted: creator_id, admin_id (if force-deleted)
- Fund allocation voted: steward_id, amount, date
```

But in code:
```python
# ❌ No audit() calls found on most endpoints
# No logging of:
# - Who accessed what user's data?
# - Who created course?
# - Who published course?
# - Who enrolled in course?
```

**Risk:**
- Cannot detect who made a malicious change
- GDPR: No data access logs (required for audits)
- SOC 2: No audit trail

**Fix:**
```python
async def audit(
    user_id: str,
    action: str,
    resource: str,
    details: dict = None,
    status: str = "success",
    severity: str = "info"
):
    """Log all sensitive actions"""
    await db.audit_logs.insert_one({
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {},
        "status": status,
        "severity": severity,
        "timestamp": datetime.utcnow(),
        "ip_address": request.client.host,  # Track IP
        "user_agent": request.headers.get("user-agent"),  # Track browser
    })

# Add to EVERY sensitive endpoint:
@router.post("/courses/create")
async def create_course(...):
    result = await create_course(...)
    
    await audit(  # ✅ Log all creations
        user_id=current_user["_id"],
        action="course_created",
        resource=f"course:{result['course_id']}",
        details={
            "title": result["title"],
            "type": result["course_type"],
            "language": result["language"]
        }
    )
    return result
```

---

### 🔴 CRITICAL-10: No Data Encryption At Rest

**File:** `backend/config.py:1-119`

**Issue:**
```python
# ❌ Not specified anywhere
# Payment methods stored in plain MongoDB?
# Bank account numbers stored as text?
# API keys stored in plaintext?
```

**Risk:**
- Database breach = full compromise (bank accounts, card details)
- GDPR violation (requires encryption)
- PCI DSS violation (payment data must be encrypted)
- SOC 2 violation (encryption at rest required)

**Fix:**
```python
# ✅ CORRECT: Use encryption for sensitive fields
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY").encode()  # 32-byte key
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_sensitive(value: str) -> str:
    """Encrypt sensitive data before storing"""
    return cipher.encrypt(value.encode()).decode()

def decrypt_sensitive(encrypted_value: str) -> str:
    """Decrypt sensitive data after retrieval"""
    return cipher.decrypt(encrypted_value.encode()).decode()

# When storing payment method:
@router.post("/billing/payment-method")
async def add_payment_method(
    card_token: str,  # From Stripe (never store full card)
    current_user: User = Depends(current_user)
):
    db = request.app.state.db
    
    # Store Stripe token ID, NOT card details
    await db.payment_methods.insert_one({
        "user_id": current_user["_id"],
        "stripe_token_id": card_token,  # Stripe handles encryption
        "created_at": datetime.utcnow(),
        "last_4": "****",  # Never store actual digits
    })

# When storing payout bank account:
@router.post("/billing/payout-account")
async def add_payout_account(
    bank_account: str,
    current_user: User = Depends(current_user)
):
    # ✅ Encrypt before storing
    encrypted_account = encrypt_sensitive(bank_account)
    
    await db.payout_accounts.insert_one({
        "user_id": current_user["_id"],
        "account_encrypted": encrypted_account,  # Encrypted
        "created_at": datetime.utcnow(),
    })
```

---

### 🔴 CRITICAL-11: JWT Secret in Code

**File:** `backend/config.py:32`

**Issue:**
```python
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
```

**Risk:**
- If `JWT_SECRET` env var not set, uses hardcoded default
- Anyone can forge JWT tokens with default secret
- Can claim any user ID, any role

**Fix:**
```python
import sys

class Settings(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    
    def __init__(self, **data):
        super().__init__(**data)
        
        if not self.JWT_SECRET:
            raise ValueError(
                "FATAL: JWT_SECRET not set. Generate one:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "Then set: export JWT_SECRET='...' or add to .env"
            )
        
        if self.ENVIRONMENT == "production" and len(self.JWT_SECRET) < 32:
            raise ValueError(
                "FATAL: JWT_SECRET too short for production. Min 32 characters."
            )

# On startup:
settings = Settings()  # Fails if JWT_SECRET not set
```

---

### 🔴 CRITICAL-12: No Webhook Signature Validation

**File:** `backend/billing/routes.py` (Stripe webhook)

**Issue:**
```python
# No evidence of webhook signature validation
# Attacker can POST fake webhook to:
# - Create fake payments
# - Cancel subscriptions
# - Trigger payouts
```

**Fix:**
```python
import hmac
import hashlib

@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    """Verify and process Stripe webhook"""
    
    # ✅ Verify webhook signature
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    body = await request.body()
    
    expected_sig = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(stripe_signature, f"t={expected_sig}"):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
    
    # Now safe to process
    payload = json.loads(body)
    event_type = payload["type"]
    
    if event_type == "payment_intent.succeeded":
        await process_payment_success(payload["data"]["object"])
    elif event_type == "customer.subscription.deleted":
        await process_subscription_cancel(payload["data"]["object"])
```

---

### 🔴 CRITICAL-13: Frontend Authorization Bypass

**File:** `frontend/src/pages/ExecutiveDirectorDashboard.jsx:1-20`

**Issue:**
```jsx
export default function ExecutiveDirectorDashboard() {
  const [userRole] = useState("steward");  // ❌ Hardcoded for testing!
  
  // Everything is controlled by this frontend-only role
  const canDelete = ["moderator", "steward", ...].includes(userRole);
  
  // User can modify state, set userRole to "admin"
  // Open DevTools console:
  // React DevTools → setUserRole("admin")
  // Now they have all admin buttons
```

**Risk:**
- Frontend role is purely UX (doesn't prevent attacks)
- All protection is visual (hidden buttons)
- User can enable all features via DevTools
- Backend MUST verify role on every API call

**Fix:**
```jsx
// ✅ CORRECT: Get role from backend
const [userRole, setUserRole] = useState(null);

useEffect(() => {
    // Fetch from backend, not from frontend state
    api.get("/auth/me")
        .then(r => setUserRole(r.data.role))
        .catch(() => window.location.href = "/login");
}, []);

// Button is ONLY UX feedback
if (!canDelete) {
    return <button disabled>Delete (insufficient permissions)</button>;
}

// But the actual DELETE still requires backend to verify:
// POST /api/moderation/content/delete
// Backend checks: is user.role in ["moderator", "steward", ...]?
```

---

### 🔴 CRITICAL-14: No Privileged Operation Confirmation

**File:** `frontend/src/pages/ExecutiveDirectorDashboard.jsx:238`

**Issue:**
```jsx
<button className="px-6 py-3 bg-red-600 text-white rounded font-bold hover:bg-red-700">
    LOCK PLATFORM
</button>

// No confirmation, no MFA, no rate limiting
// One click = entire platform read-only
```

**Risk:**
- Accidental platform lock
- Compromised session = instant DoS
- No audit trail of who/when/why

**Fix:**
```jsx
const [lockConfirmation, setLockConfirmation] = useState(null);

const handleLockPlatform = async () => {
    // 1. Show confirmation with consequences
    if (!lockConfirmation) {
        setLockConfirmation({
            action: "lock_platform",
            message: "This will make the entire platform read-only. No one can post, enroll, or publish. Continue?"
        });
        return;
    }
    
    // 2. Require MFA (if enabled)
    // const mfaCode = prompt("Enter MFA code:");
    // if (!verify_mfa(mfaCode)) return;
    
    // 3. Log reason
    const reason = prompt("Reason for platform lock (required):");
    if (!reason) return;
    
    // 4. Send to backend
    try {
        await api.post("/admin/emergency/lock-platform", { reason });
        toast.success("Platform locked. Users notified.");
        
        // 5. Auto-unlock after 1 hour (safety mechanism)
        setTimeout(() => {
            toast.info("Platform auto-unlock triggered (1 hour timeout)");
        }, 3600000);
    } catch (e) {
        toast.error("Lock failed: " + e.message);
    }
    
    setLockConfirmation(null);
};

// Backend:
@router.post("/admin/emergency/lock-platform")
async def lock_platform(
    reason: str,
    current_user: User = Depends(require_role("admin", "elder")),
    request: Request
):
    """Lock platform (read-only mode)"""
    
    # ✅ Require MFA for directors
    if not request.state.mfa_verified:
        raise HTTPException(403, "MFA required for emergency controls")
    
    # ✅ Log action
    await audit(
        user_id=current_user["_id"],
        action="platform_lock",
        resource="platform:global",
        details={"reason": reason},
        severity="critical"
    )
    
    # ✅ Broadcast to all users
    await db.system_state.update_one(
        {"_id": "global"},
        {"$set": {"read_only_mode": True, "locked_at": datetime.utcnow()}},
        upsert=True
    )
```

---

## HIGH-RISK ISSUES

### 🟠 HIGH-1: No Field-Level Authorization on User Profiles

**File:** `frontend/src/lib/security.js:75-124`

**Issue:**
```javascript
export function getVisibleProfileFields(viewer, target) {
    // Frontend filters what fields to show
    // But backend may return all fields!
    
    if (viewer.userId === target.userId) {
        return [..., "totalEarnings", "payoutMethod", ...];
    }
    
    return baseFields;  // Should hide sensitive fields
}
```

**Risk:**
- Backend endpoint returns all fields
- Frontend tries to filter (but that's UX only)
- Network inspection reveals all data
- GraphQL/API exploration leaks data

**Fix:**
```python
# ✅ Backend filters BEFORE responding
@router.get("/users/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(current_user),
    request: Request
):
    db = request.app.state.db
    target = await db.users.find_one({"id": user_id})
    
    if not target:
        raise HTTPException(404, "User not found")
    
    # Determine visible fields
    visible_fields = AccessControl.get_visible_profile_fields(
        viewer_user_id=current_user["_id"],
        target_user_id=user_id,
        viewer_role=current_user["role"],
        target_role=target.get("role"),
    )
    
    # ✅ Filter response to only visible fields
    profile = {k: v for k, v in target.items() if k in visible_fields}
    
    # Remove MongoDB internal fields
    profile.pop("_id", None)
    profile.pop("password_hash", None)
    profile.pop("must_change_password", None)
    
    # ✅ Log access to sensitive data
    if "totalEarnings" in visible_fields or "payoutMethod" in visible_fields:
        await audit(
            user_id=current_user["_id"],
            action="financial_data_accessed",
            resource=f"user:{user_id}:financial",
            severity="high"
        )
    
    return profile
```

---

### 🟠 HIGH-2: Stripe Key Management

**File:** `backend/billing/stripe_service.py` (not provided, but critical)

**Issue:**
- STRIPE_API_KEY in environment variables
- Could be exposed in logs, error messages, Sentry
- Need to use restricted API keys

**Fix:**
```python
# ✅ Use restricted Stripe API keys
# 1. In Stripe Dashboard:
#    Create TWO keys:
#    - Publishable key (for frontend, no restrictions needed)
#    - Restricted secret key (backend, only permissions:
#      - read:payment_intents, write:payment_intents
#      - read:customers, write:customers
#      - read:subscription, write:subscription)
#
# 2. In code:
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY_RESTRICTED")
if not STRIPE_SECRET_KEY or len(STRIPE_SECRET_KEY) < 32:
    raise ValueError("Invalid STRIPE_SECRET_KEY")

# 3. Never log API key:
stripe.api_key = STRIPE_SECRET_KEY
# Don't do: logger.info(f"Stripe key: {STRIPE_SECRET_KEY}")

# 4. Use idempotency keys for payments:
import stripe
stripe.api_key = STRIPE_SECRET_KEY

idempotency_key = f"{user_id}:{course_id}:{int(datetime.now().timestamp())}"

payment = stripe.PaymentIntent.create(
    amount=int(amount * 100),  # Convert to cents
    currency="usd",
    customer=customer_id,
    idempotency_key=idempotency_key,  # ✅ Prevent duplicate charges
)
```

---

### 🟠 HIGH-3: No Device/Session Management

**Issue:**
- No way to revoke tokens
- User can't see active sessions
- Compromised session lasts 24 hours

**Fix:**
```python
# Add session tracking
@router.post("/auth/sessions")
async def list_sessions(
    current_user: User = Depends(current_user),
    request: Request
):
    """List all active sessions for this user"""
    db = request.app.state.db
    sessions = await db.user_sessions.find({
        "user_id": current_user["_id"]
    }).to_list(None)
    
    return {
        "sessions": [
            {
                "session_id": s["id"],
                "ip_address": s["ip_address"],
                "user_agent": s["user_agent"],
                "created_at": s["created_at"],
                "last_activity": s["last_activity"],
                "is_current": s["id"] == request.state.session_id,
            }
            for s in sessions
        ]
    }

@router.post("/auth/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(current_user),
    request: Request
):
    """Revoke a specific session"""
    db = request.app.state.db
    
    # Verify ownership
    session = await db.user_sessions.find_one({"id": session_id})
    if not session or session["user_id"] != current_user["_id"]:
        raise HTTPException(403, "Cannot revoke other user's sessions")
    
    # Revoke by adding to blacklist
    await db.token_blacklist.insert_one({
        "token_jti": session["token_jti"],
        "revoked_at": datetime.utcnow(),
    })
    
    return {"status": "success"}
```

---

### 🟠 HIGH-4: No SQL/NoSQL Injection Prevention Validation

**Issue:**
- Pydantic helps but not everywhere
- Query construction from user input could be unsafe
- Aggregation pipeline operations

**Fix:**
```python
# ✅ Always use parameterized queries
# ✅ WRONG:
# query_str = f"db.users.find_one({{'email': '{email}'}})"  # ❌ NEVER

# ✅ CORRECT:
user = await db.users.find_one({"email": email})  # Safe, parameterized

# ✅ For complex queries:
from pymongo import ASCENDING

pipeline = [
    {"$match": {"status": "active"}},  # Safe
    {"$match": {"role": role}},  # Safe, parameterized
    {"$limit": 100},  # Safe
]
users = await db.users.aggregate(pipeline).to_list(None)
```

---

### 🟠 HIGH-5: No API Rate Limiting Per User

**Issue:**
- Attackers can enumerate all course IDs
- Can brute-force user IDs
- Can spam 1M forum posts

**Fix:**
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.get("/courses/{course_id}")
@app.limiter.limit("100/minute")  # Per IP
async def get_course(
    course_id: str,
    current_user: User = Depends(current_user),  # Per user
):
    """Rate limit per user AND per IP"""
    # FastAPILimiter middleware will check:
    # 1. User_id: 100 requests/minute
    # 2. IP: 1000 requests/minute
    pass

@router.post("/forum/posts")
@app.limiter.limit("10/day")  # 10 posts per day
async def create_post(
    content: str,
    current_user: User = Depends(current_user),
):
    """Create forum post"""
    pass

@router.post("/auth/login")
@app.limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(
    email: str,
    password: str,
):
    """Login endpoint"""
    pass
```

---

## MEDIUM-RISK ISSUES

### 🟡 MEDIUM-1: No Environment Validation on Startup

**File:** `backend/config.py:90-106`

**Issue:**
```python
def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not settings.STRIPE_API_KEY:
        errors.append("STRIPE_API_KEY not set")
    
    # ✅ Good checks, but incomplete
    # Missing:
    # - MONGODB_URI must be set and reachable
    # - JWT_SECRET strength check
    # - Database indexes must exist
    # - Required environment variables all set
```

**Fix:**
```python
async def validate_startup():
    """Comprehensive startup validation"""
    errors = []
    
    # 1. Database connectivity
    try:
        ping = await db.command("ping")
        if not ping.get("ok"):
            errors.append("MongoDB ping failed")
    except Exception as e:
        errors.append(f"MongoDB unreachable: {e}")
    
    # 2. Stripe API key validity
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Account.retrieve()  # Test API key
    except Exception as e:
        errors.append(f"Stripe API key invalid: {e}")
    
    # 3. Email service (if enabled)
    if settings.ENABLE_EMAILS:
        # Test SendGrid API key
        pass
    
    # 4. Required collections exist
    collections = await db.list_collection_names()
    required = ["users", "courses", "audit_logs", "partnerships"]
    missing = [c for c in required if c not in collections]
    if missing:
        errors.append(f"Missing collections: {missing}")
    
    # 5. Indexes are created
    await ensure_indexes()
    
    # 6. Encryption key is strong
    if len(settings.ENCRYPTION_KEY) < 32:
        errors.append("ENCRYPTION_KEY too weak (min 32 bytes)")
    
    if errors:
        logger.critical("Startup validation failed:\n" + "\n".join(errors))
        raise RuntimeError("Cannot start: " + "; ".join(errors))
    
    logger.info("✅ All startup checks passed")
```

---

### 🟡 MEDIUM-2: No Incident Response Plan

**Issue:**
- What happens if database is breached?
- What's the plan if malicious admin takes over?
- No documented security incident process

**Fix:**
Create `INCIDENT_RESPONSE.md`:
```markdown
# Incident Response Plan

## Security Breach Discovery
1. Immediately deactivate all director/admin accounts
2. Revoke all API keys
3. Change all service credentials (Stripe, email, etc.)
4. Enable read-only mode on database
5. Notify affected users (within 24 hours per GDPR)

## Malicious Admin
1. Immediately revoke their session tokens
2. Check audit log for actions taken
3. Assess damage (what data was accessed/modified)
4. Restore from backup if needed
5. Change their password + force password reset

## Data Breach
1. Trigger incident response team
2. Preserve logs (don't delete for 30 days)
3. Contact GDPR/compliance officer
4. Notify users if personal data was accessed
5. Conduct security audit
```

---

### 🟡 MEDIUM-3: No Secrets Rotation

**Issue:**
- JWT_SECRET never rotated
- API keys manually managed
- No key rotation policy

**Fix:**
```python
# Implement secret rotation
SECRET_ROTATION_INTERVAL = 90  # Days

@app.on_event("startup")
async def check_secret_rotation():
    """Check if secrets need rotation"""
    db = request.app.state.db
    
    rotation_log = await db.secret_rotation.find_one(
        {"key": "jwt_secret"},
        sort=[("rotated_at", -1)]
    )
    
    if not rotation_log:
        logger.warning("No secret rotation log. Create one manually.")
        return
    
    days_since = (datetime.utcnow() - rotation_log["rotated_at"]).days
    if days_since > SECRET_ROTATION_INTERVAL:
        logger.critical(
            f"JWT_SECRET needs rotation (last rotated {days_since} days ago)"
        )
        # Don't auto-rotate; require manual action
        # But alert operator
```

---

## ARCHITECTURAL ISSUES

### 🔵 ARCH-1: Monolithic Permission Model

**Issue:**
- All permission checks in one file
- Hard to audit all permission rules
- Easy to miss checks on new endpoints
- No central permission manifest

**Recommendation:**
Create permission decorator:
```python
@require_permission("delete_content")
@router.post("/moderation/content/{id}/delete")
async def delete_content(
    id: str,
    current_user: User = Depends(current_user),
):
    """Delete content (requires permission)"""
    await audit(...)
    return {"status": "success"}

# Centralized permission check:
def require_permission(permission: str):
    async def dep(user: User = Depends(current_user)):
        if permission not in AccessControl.get_role_permissions(user.role):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep
```

---

### 🔵 ARCH-2: No Transaction Support

**Issue:**
- Race condition: creator publishes course + gets enrolled simultaneously
- Race condition: payout requested twice in quick succession
- No atomic updates across collections

**Fix:**
```python
async def publish_course_atomic(course_id: str, creator_id: str):
    """Atomically publish course with audit log"""
    async with await db.client.start_session() as session:
        async with session.start_transaction():
            # 1. Update course
            result = await db.courses.update_one(
                {"_id": ObjectId(course_id), "creator_id": creator_id},
                {"$set": {"status": "published"}},
                session=session
            )
            
            if result.matched_count == 0:
                raise HTTPException(403, "Course not found or not owned by you")
            
            # 2. Add audit log in SAME transaction
            await db.audit_logs.insert_one(
                {
                    "user_id": creator_id,
                    "action": "course_published",
                    "course_id": course_id,
                    "timestamp": datetime.utcnow(),
                },
                session=session
            )
            
            # If either fails, both roll back
```

---

### 🔵 ARCH-3: No Data Retention Policy

**Issue:**
- GDPR: User can request data deletion
- No mechanism to delete user data
- Audit logs kept forever

**Fix:**
```python
@router.post("/users/me/request-deletion")
async def request_data_deletion(
    current_user: User = Depends(current_user),
    request: Request
):
    """Request account deletion (GDPR right to be forgotten)"""
    db = request.app.state.db
    
    # Schedule deletion in 30 days (allows user to cancel)
    await db.deletion_requests.insert_one({
        "user_id": current_user["_id"],
        "requested_at": datetime.utcnow(),
        "deletion_date": datetime.utcnow() + timedelta(days=30),
    })
    
    return {
        "status": "success",
        "message": "Deletion scheduled for 30 days from now. You can cancel anytime."
    }

# Scheduled job (runs daily):
async def process_pending_deletions():
    """Delete user data after 30-day waiting period"""
    db = request.app.state.db
    
    expired = await db.deletion_requests.find({
        "deletion_date": {"$lt": datetime.utcnow()}
    }).to_list(None)
    
    for deletion in expired:
        user_id = deletion["user_id"]
        
        # Archive data before deletion (for legal holds)
        await db.archived_users.insert_one({
            "user_id": user_id,
            "archived_at": datetime.utcnow(),
            "original_data": await db.users.find_one({"_id": user_id})
        })
        
        # Delete all user data
        await db.users.delete_one({"_id": user_id})
        await db.courses.delete_many({"creator_id": user_id})
        await db.audit_logs.delete_many({"user_id": user_id})  # Or just mark as deleted
        
        logger.info(f"Deleted user data for {user_id}")
```

---

## COMPLIANCE GAPS

| Compliance | Status | Gap |
|-----------|--------|-----|
| **GDPR** | Partial | No data deletion mechanism, limited audit logs for data access, no data retention policy |
| **SOC 2** | Partial | No encrypted field-level data, incomplete audit logging, no MFA for directors |
| **PCI DSS** | Partial | API key management weak, no restriction on key permissions, no secure key rotation |
| **HIPAA** | Not applicable | Not a medical platform |

---

## SUMMARY OF FIXES

| Priority | Issue | Effort | Impact | Fix |
|----------|-------|--------|--------|-----|
| **CRITICAL** | Hardcoded exec credentials | 2h | High | Remove bootstrap on startup, only once manually |
| **CRITICAL** | Missing auth on courses | 4h | Critical | Add current_user check to all endpoints |
| **CRITICAL** | Unprotected CRM endpoints | 2h | Critical | Add require_role decorator |
| **CRITICAL** | Payment data exposure | 6h | Critical | Field-level filtering + encryption |
| **CRITICAL** | CSRF + Credentials | 3h | High | Restrict CORS methods, add CSRF tokens |
| **CRITICAL** | Client-controlled partnership | 4h | High | Compute from audit log, verify backend |
| **CRITICAL** | No rate limiting | 3h | Medium | Add FastAPILimiter to all endpoints |
| **CRITICAL** | Incomplete audit logs | 5h | High | Add audit() calls to all sensitive actions |
| **CRITICAL** | No encryption at rest | 8h | Critical | Encrypt payment methods, bank accounts |
| **HIGH** | JWT secret exposed | 1h | Critical | Require env variable, fail startup if missing |
| **HIGH** | No webhook validation | 2h | High | Verify Stripe signature on all webhooks |
| **HIGH** | Frontend auth bypass | 1h | Medium | Frontend is UX only, backend enforces |
| **HIGH** | No emergency controls confirmation | 2h | Medium | Require MFA + reason + auto-unlock timer |

---

## ESTIMATED REMEDIATION TIME

- **Week 1:** Critical auth/permission fixes (40 hours)
- **Week 2:** Encryption, audit logging, rate limiting (30 hours)
- **Week 3:** Testing, security review, deployment (20 hours)
- **Total:** ~5-6 weeks for comprehensive fix

---

## RECOMMENDED NEXT STEPS

1. **Immediate (Today):**
   - [ ] Remove hardcoded executive admin bootstrap
   - [ ] Add authentication to course and CRM endpoints
   - [ ] Set JWT_SECRET requirement to fail startup

2. **This Week:**
   - [ ] Implement field-level authorization on all endpoints
   - [ ] Add rate limiting framework
   - [ ] Encrypt payment/banking data

3. **This Month:**
   - [ ] Complete audit logging
   - [ ] Add CSRF protection
   - [ ] Implement MFA for directors
   - [ ] Security penetration test

4. **Before Launch:**
   - [ ] Pass SOC 2 audit
   - [ ] GDPR compliance review
   - [ ] Incident response plan
   - [ ] Data retention policy

---

## CONCLUSION

The WAI Institute has **strong security foundations** (RBAC model, good intentions on audit logging) but **critical execution gaps** that make it **unsuitable for production deployment** in current state.

**Estimated remediation effort:** 6-8 weeks of focused security development.

**Risk if launched without fixes:** High probability of data breach, privilege escalation, or regulatory violation.

**Recommendation:** Fix critical issues before accepting any real user data.
