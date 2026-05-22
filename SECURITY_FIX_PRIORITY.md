# Security Fix Priority & Action Plan

## Phase 1: IMMEDIATE (Block Production Launch)
**Effort:** 8-10 hours | **Risk if skipped:** CRITICAL

### 1.1 Remove Hardcoded Executive Admin Bootstrap
**File:** `backend/server.py:635-710`

```python
# ❌ DELETE THIS ENTIRE SECTION:
# Lines 635-684 (primary exec bootstrap)
# Lines 685-715 (backup exec bootstrap)

# ✅ REPLACE WITH ONE-TIME BOOTSTRAP:
# Create new file: backend/scripts/bootstrap_exec_admin.py

async def bootstrap_exec():
    """
    ONE-TIME manual bootstrap script.
    Run once, then this script is no longer needed.
    """
    from pathlib import Path
    
    DONE_FILE = Path("./.exec_admin_bootstrapped")
    if DONE_FILE.exists():
        print("Already bootstrapped. Remove .exec_admin_bootstrapped to re-run.")
        return
    
    email = input("Executive admin email: ").strip()
    temp_pass = secrets.token_urlsafe(16)
    
    await db.users.insert_one({
        "id": str(uuid.uuid4()),
        "email": email,
        "role": "executive_admin",
        "password_hash": hash_pw(temp_pass),
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    
    print(f"Admin created: {email}")
    print(f"Temporary password: {temp_pass}")
    print("IMPORTANT: Change password immediately on first login")
    
    DONE_FILE.touch()

# Run with: python -m backend.scripts.bootstrap_exec_admin
```

**How to deploy:**
1. In `backend/server.py`, remove ALL bootstrap code (lines 635-715)
2. Create `backend/scripts/bootstrap_exec_admin.py` as above
3. On first production startup (manual):
   ```bash
   export MONGO_URL=production_url
   export DB_NAME=wai_institute
   python -m backend.scripts.bootstrap_exec_admin
   ```
4. Delete both accounts created by old bootstrap
   ```javascript
   db.users.deleteMany({email: "youpickeddoliver@gmail.com"})
   ```

**Checklist:**
- [ ] Removed bootstrap code from server.py
- [ ] Created bootstrap script
- [ ] Tested bootstrap script locally
- [ ] Production account created via script
- [ ] Old hardcoded accounts deleted
- [ ] Verified only ONE executive admin exists

---

### 1.2 Add Authentication to Course Endpoints
**File:** `backend/billing/creator_course_routes.py:51-160`

```python
from server import current_user, require_role  # Add import

# ❌ WRONG - Currently:
@router.post("/create")
async def create_new_course(creator_id: str, ...):
    pass

# ✅ CORRECT - New:
@router.post("/create")
async def create_new_course(
    course_data: CourseCreate,  # Pydantic model, no creator_id!
    current_user: User = Depends(current_user),  # Verify auth
    request: Request,
):
    """Create a new course draft"""
    # Check user has creator role
    if current_user.role not in ["creator", "mentor", "steward", "elder", "admin"]:
        raise HTTPException(403, "Must be creator to create courses")
    
    db = request.app.state.db
    
    # Use current_user.id, NOT client input
    result = await create_course(
        db,
        creator_id=current_user.id,  # ✅ FROM AUTH
        title=course_data.title,
        description=course_data.description,
        course_type=course_data.course_type,
        category=course_data.category,
        language=course_data.language,
    )
    
    if result["status"] != "success":
        raise HTTPException(400, result.get("message"))
    
    # ✅ Log action
    await audit(
        user_id=current_user.id,
        action="course_created",
        resource=f"course:{result['course_id']}",
        details={"title": course_data.title}
    )
    
    return result
```

**Apply to ALL course endpoints:**
- `/create` — Creator must match current_user.id
- `/course/{id}/lesson` — Creator must own course
- `/course/{id}/publish` — Creator must own course
- `/dashboard/{creator_id}` — Only creator or admins can view financials
- `/enroll` — Use current_user.id, not client input

**Checklist:**
- [ ] Updated /create endpoint
- [ ] Updated /lesson endpoint
- [ ] Updated /publish endpoint
- [ ] Updated /dashboard endpoint
- [ ] Updated /enroll endpoint
- [ ] All endpoints verify ownership
- [ ] All endpoints log actions
- [ ] Tested with mismatched user/creator_id (should fail with 403)

---

### 1.3 Protect CRM Endpoints
**File:** `backend/crm/routes.py:18-100`

```python
from server import require_role, current_user  # Add import

# ❌ WRONG - Currently:
@router.post("/leads")
async def create_lead(lead_create: LeadCreate, request: Request):
    pass

# ✅ CORRECT - New:
@router.post("/leads")
async def create_lead(
    lead_create: LeadCreate,
    request: Request,
    current_user: User = Depends(require_role("admin", "steward")),
):
    """Create sales lead (admin/steward only)"""
    leads = request.app.state.db.leads
    
    lead_doc = { ... }
    result = await leads.insert_one(lead_doc)
    
    await audit(
        user_id=current_user["_id"],
        action="lead_created",
        resource=f"lead:{result.inserted_id}",
        details={"company": lead_create.company_name}
    )
    
    return Lead(**lead_doc, id=str(result.inserted_id))

@router.get("/leads")
async def list_leads(
    request: Request,
    current_user: User = Depends(require_role("admin", "steward")),
    status: Optional[str] = Query(None),
    # ... rest of params
):
    """List leads (admin/steward only)"""
    leads = request.app.state.db.leads
    # ... rest of logic
```

**All CRM endpoints need:**
- [ ] `@Depends(require_role("admin", "steward"))`
- [ ] Audit logging of access
- [ ] Field validation (max_length, regex, etc.)

---

### 1.4 Require JWT_SECRET on Startup
**File:** `backend/config.py:32`

```python
# ❌ WRONG - Currently:
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")

# ✅ CORRECT - New:
JWT_SECRET: str = os.getenv("JWT_SECRET")

def __init__(self, **data):
    super().__init__(**data)
    
    if not self.JWT_SECRET:
        raise ValueError(
            "FATAL: JWT_SECRET not configured.\n"
            "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
            "Then set: export JWT_SECRET='<generated-key>' or add to .env"
        )
    
    if self.ENVIRONMENT == "production" and len(self.JWT_SECRET) < 32:
        raise ValueError("FATAL: JWT_SECRET must be 32+ characters for production")

# .env file (git-ignored):
JWT_SECRET=<your-generated-secret-key-here>
```

**Checklist:**
- [ ] Generated new JWT_SECRET
- [ ] Added to .env file
- [ ] Tested startup fails if JWT_SECRET not set
- [ ] All running instances use new secret
- [ ] Old tokens invalidated/users re-login

---

## Phase 2: CRITICAL (First Week)
**Effort:** 20-25 hours | **Risk if skipped:** HIGH

### 2.1 Add Field-Level Authorization to All Endpoints

**Pattern:** Every GET endpoint that returns user data must filter by role

```python
# ✅ PATTERN FOR ALL ENDPOINTS:
@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(current_user),
    request: Request
):
    db = request.app.state.db
    target = await db.users.find_one({"id": user_id})
    
    if not target:
        raise HTTPException(404, "Not found")
    
    # ✅ Determine visible fields
    visible_fields = AccessControl.get_visible_profile_fields(
        viewer_user_id=current_user["_id"],
        target_user_id=user_id,
        viewer_role=current_user["role"],
        target_role=target.get("role"),
    )
    
    # ✅ Filter response
    filtered = {k: v for k, v in target.items() if k in visible_fields}
    
    # ✅ Remove internal fields
    filtered.pop("_id", None)
    filtered.pop("password_hash", None)
    
    # ✅ Log sensitive access
    if "totalEarnings" in visible_fields or "payoutMethod" in visible_fields:
        await audit(
            user_id=current_user["_id"],
            action="financial_data_accessed",
            resource=f"user:{user_id}:financial",
            severity="high"
        )
    
    return filtered
```

**Apply to endpoints:**
- [ ] GET /users/{id} — Filter by role
- [ ] GET /users/{id}/earnings — Only user or admin
- [ ] GET /users/{id}/payouts — Only user or admin
- [ ] GET /courses/{id} — Only published or owner/admin
- [ ] GET /creator/dashboard — Only creator or admin

### 2.2 Implement Audit Logging on All Sensitive Actions

Add `await audit(...)` to:
- [ ] Create course
- [ ] Publish course
- [ ] Enroll student
- [ ] Request payout
- [ ] Change user role
- [ ] Ban user
- [ ] Delete content
- [ ] Access financial data

### 2.3 Add Request Validation

Use Pydantic with field constraints:

```python
from pydantic import BaseModel, Field

class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    course_type: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", regex="^[a-z]{2}$")  # ISO 639-1

# Automatically validates all fields
```

Apply to:
- [ ] All POST endpoints
- [ ] All PATCH endpoints
- [ ] File upload endpoints

### 2.4 Encrypt Sensitive Data at Rest

```python
from cryptography.fernet import Fernet

cipher = Fernet(os.environ["ENCRYPTION_KEY"].encode())

def encrypt(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()

# Store encrypted:
await db.payout_accounts.insert_one({
    "user_id": user_id,
    "account_encrypted": encrypt(bank_account),  # ✅ Encrypted
    "created_at": datetime.utcnow(),
})
```

Encrypt:
- [ ] Bank account numbers
- [ ] API keys
- [ ] Sensitive configuration

---

## Phase 3: HIGH (Second Week)
**Effort:** 15-20 hours | **Risk if skipped:** MEDIUM

### 3.1 Add Rate Limiting

```bash
pip install fastapi-limiter2 redis
```

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import Redis

redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost"))
await FastAPILimiter.init(redis)

@router.post("/auth/register")
@app.limiter.limit("3/minute")
async def register(...):
    pass

@router.post("/courses/create")
@app.limiter.limit("5/day")
async def create_course(...):
    pass

@router.get("/leads")
@app.limiter.limit("100/minute")
async def list_leads(...):
    pass
```

Rate limits to add:
- [ ] /auth/register: 3 per minute
- [ ] /auth/login: 5 per minute
- [ ] /courses/create: 5 per day
- [ ] /forum/posts: 10 per day
- [ ] /admin/users: 10 per hour

### 3.2 Add Stripe Webhook Validation

```python
import hmac
import hashlib

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Verify webhook signature"""
    
    signature = request.headers.get("stripe-signature")
    body = await request.body()
    secret = os.environ["STRIPE_WEBHOOK_SECRET"]
    
    expected_sig = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, f"t={expected_sig}"):
        raise HTTPException(403, "Invalid signature")
    
    # Safe to process
    payload = json.loads(body)
    event_type = payload["type"]
    
    if event_type == "payment_intent.succeeded":
        await process_payment(payload["data"]["object"])
```

- [ ] Verify Stripe signature on all webhooks
- [ ] Test with invalid signature (should fail)
- [ ] Log all webhook events

### 3.3 Add CSRF Protection

```python
# ✅ Restrict CORS methods
app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "HEAD", "OPTIONS"],  # ✅ Only safe methods
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

# ✅ Add CSRF token to state-changing operations
@router.post("/users/me/email")
async def change_email(
    new_email: EmailStr,
    csrf_token: str = Header(...),
    current_user: User = Depends(current_user),
):
    if not verify_csrf_token(current_user["_id"], csrf_token):
        raise HTTPException(403, "Invalid CSRF token")
    
    # Safe to proceed
    await db.users.update_one(
        {"id": current_user["_id"]},
        {"$set": {"email": new_email}}
    )
```

- [ ] Restrict CORS to GET/HEAD/OPTIONS
- [ ] Require CSRF token for POST/DELETE/PATCH
- [ ] Frontend obtains CSRF token from GET /csrf-token

---

## Phase 4: ARCHITECTURAL (Third Week+)
**Effort:** 10-15 hours | **Can be deferred to post-launch**

### 4.1 Add Session Management

```python
@router.get("/auth/sessions")
async def list_sessions(current_user: User = Depends(current_user)):
    """List active sessions"""
    sessions = await db.user_sessions.find({
        "user_id": current_user["_id"]
    }).to_list(None)
    
    return {
        "sessions": [
            {
                "id": s["id"],
                "ip": s["ip_address"],
                "agent": s["user_agent"],
                "created": s["created_at"],
                "is_current": s["id"] == request.state.session_id,
            }
            for s in sessions
        ]
    }

@router.post("/auth/sessions/{session_id}/revoke")
async def revoke_session(session_id: str, current_user: User = Depends(current_user)):
    """Revoke a session"""
    await db.token_blacklist.insert_one({
        "token": session_id,
        "revoked_at": datetime.utcnow(),
    })
    
    return {"status": "success"}
```

- [ ] Track all active sessions
- [ ] Allow users to revoke sessions
- [ ] Check blacklist on token validation

### 4.2 Add MFA for Directors

```python
@router.post("/auth/mfa/setup")
async def setup_mfa(current_user: User = Depends(current_user)):
    """Setup 2FA for account"""
    if current_user["role"] not in ["admin", "elder"]:
        return {"message": "MFA optional for this role"}
    
    secret = pyotp.random_base32()
    
    await db.mfa_secrets.insert_one({
        "user_id": current_user["_id"],
        "secret": secret,
        "verified": False,
    })
    
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user["email"])
    
    return {
        "secret": secret,
        "qr_code": uri,  # Display as QR code
    }

@router.post("/auth/mfa/verify")
async def verify_mfa(code: str, current_user: User = Depends(current_user)):
    """Verify MFA code"""
    mfa = await db.mfa_secrets.find_one({
        "user_id": current_user["_id"]
    })
    
    if not mfa:
        raise HTTPException(400, "MFA not setup")
    
    totp = pyotp.TOTP(mfa["secret"])
    if not totp.verify(code):
        raise HTTPException(400, "Invalid code")
    
    await db.mfa_secrets.update_one(
        {"_id": mfa["_id"]},
        {"$set": {"verified": True}}
    )
    
    return {"status": "success"}
```

- [ ] Require MFA for admin/elder roles
- [ ] Require MFA for emergency controls
- [ ] Generate backup codes

### 4.3 Add Data Deletion (GDPR)

```python
@router.post("/users/me/request-deletion")
async def request_deletion(current_user: User = Depends(current_user)):
    """Request account deletion (30-day waiting period)"""
    await db.deletion_requests.insert_one({
        "user_id": current_user["_id"],
        "requested_at": datetime.utcnow(),
        "deletion_date": datetime.utcnow() + timedelta(days=30),
    })
    
    return {
        "status": "success",
        "deletion_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    }

@router.post("/users/me/cancel-deletion")
async def cancel_deletion(current_user: User = Depends(current_user)):
    """Cancel deletion request"""
    await db.deletion_requests.delete_one({
        "user_id": current_user["_id"]
    })
    
    return {"status": "success"}

# Scheduled job (daily):
async def process_deletions():
    """Delete user data after 30 days"""
    expired = await db.deletion_requests.find({
        "deletion_date": {"$lt": datetime.utcnow()}
    }).to_list(None)
    
    for req in expired:
        # Delete all data
        await db.users.delete_one({"id": req["user_id"]})
        await db.courses.delete_many({"creator_id": req["user_id"]})
```

- [ ] 30-day waiting period
- [ ] User can cancel anytime
- [ ] All data deleted after period
- [ ] Audit log NOT deleted (legal holds)

---

## Testing Checklist

### Phase 1 Testing
- [ ] Try to create course as different user (should fail)
- [ ] Try to access CRM as non-admin (should fail)
- [ ] Try to login with invalid JWT secret (should fail)
- [ ] Try to post fake executive admin (should fail)

### Phase 2 Testing
- [ ] Try to view other user's earnings (should fail for non-owner/admin)
- [ ] Try to enroll with manipulated course_id (should fail)
- [ ] Check audit log has entries for all sensitive actions
- [ ] Try to create 10MB document (should fail)

### Phase 3 Testing
- [ ] Try to register 10 times in 1 minute (should be rate limited)
- [ ] Try to post fake Stripe webhook (should fail with invalid signature)
- [ ] Try CSRF attack from different origin (should fail)

### Phase 4 Testing
- [ ] Create session, logout, try to use old token (should fail)
- [ ] Request deletion, verify 30-day wait, verify deletion

---

## Deployment Steps

1. **Week 1 Launch:**
   - [ ] Deploy Phase 1 fixes
   - [ ] Rotate all hardcoded credentials
   - [ ] Test all auth endpoints
   - [ ] Run security test suite

2. **Week 2 Launch:**
   - [ ] Deploy Phase 2 fixes
   - [ ] Run compliance audit
   - [ ] Test with real payment flow

3. **Week 3+ Launch:**
   - [ ] Deploy Phase 3-4 fixes
   - [ ] Request SOC 2 audit
   - [ ] Request security penetration test

---

## Emergency Procedures

**If breach detected:**
1. Revoke all admin tokens: `db.token_blacklist.deleteMany({})` then `db.users.updateMany({role:"admin"}, {$set:{last_token_revoke: now}})`
2. Force password change for all admins
3. Review audit logs for unauthorized access
4. Notify affected users
5. Contact legal/compliance

**If malicious admin:**
1. Deactivate their account: `db.users.updateOne({_id:...}, {$set:{is_active:false}})`
2. Revoke all sessions
3. Check what they accessed/modified in audit logs
4. Restore from backup if data modified
5. Change all service credentials (Stripe, etc.)

---

## Success Criteria

- [ ] All critical issues resolved
- [ ] Audit logs show ALL sensitive actions
- [ ] Rate limiting prevents abuse
- [ ] Authorization enforced on backend only
- [ ] Encryption used for sensitive data
- [ ] No hardcoded credentials
- [ ] GDPR/SOC 2 gaps closed
- [ ] Incident response plan documented
- [ ] Security audit passed

---

## Q&A

**Q: Can we launch before fixing everything?**
A: No. The critical 14 issues MUST be fixed. Phases 3-4 can be post-launch if absolutely necessary, but high-risk issues should also be fixed.

**Q: How long will Phase 1 take?**
A: 8-10 hours of development + 2 hours testing = ~1 working day

**Q: Do we need external penetration test?**
A: Yes. Before accepting real user data, hire a security firm to audit. Budget $5-10K.

**Q: Can we skip encryption?**
A: No. PCI DSS and SOC 2 require it. It's also the right thing.

**Q: What about legacy code that needs auth?**
A: Go through EVERY endpoint in `backend/crm/routes.py`, `backend/billing/routes.py`, and anywhere without `@Depends(current_user)` or `require_role()`.
