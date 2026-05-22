# WAI-Institute Emergency Access Recovery

**Last Updated:** 2026-05-22  
**For:** Delon Oliver / NAM Oshun (Executive Director)  
**Status:** ✅ ACTIVE — Multiple redundant recovery mechanisms

---

## Overview

You have **THREE GUARANTEED WAYS** to regain access to your executive account, even if locked out completely:

1. **IMMEDIATE (Railway Environment Variable)** — 2 minutes, no code needed
2. **RECOVERY CODES** — One-time use codes generated and stored securely
3. **BACKUP EXECUTIVE ACCOUNTS** — Alternative email addresses with full executive access

Each layer is independent. If one fails, the next is available.

---

## Layer 1: IMMEDIATE Recovery (EXEC_FORCE_RESET)

**Use this if:** You forgot your password and need access within 2 minutes.

**Guaranteed to work:** Yes, always.

### Step-by-Step

1. **Open Railway Dashboard**
   - Go to https://railway.app/project/ancestral-sage-debug
   - Log in with your Railway account

2. **Navigate to Backend Service Variables**
   - Click "ancestral-sage-debug" backend service
   - Click "Variables" tab
   - Click "New Variable"

3. **Add the Recovery Variable**
   - Key: `EXEC_FORCE_RESET`
   - Value: `1`
   - Click Save

4. **Wait for Redeploy**
   - Railway auto-redeploys (~60 seconds)
   - Watch the "Deployments" tab for green checkmark

5. **Log In With Reset Password**
   - Go to https://ancestral-sage-debug-production.up.railway.app/login
   - Email: `youpickeddoliver@gmail.com` (or your other exec email)
   - Password: `NamOshun@WAI2026`
   - You are now logged in

6. **CRITICAL: Delete the Recovery Variable Immediately**
   - Go back to Variables tab
   - Delete `EXEC_FORCE_RESET` variable
   - **⚠️ If you leave this set to 1, password resets on every deploy**

7. **Change Your Password**
   - Once logged in, go to Settings → Change Password
   - Set a new password you'll remember

### What EXEC_FORCE_RESET Does

On startup, this checks all three executive accounts:
- `delon.oliver@lightningcityelectric.com` → resets to `Executive@LCE2026`
- `youpickeddoliver@gmail.com` → resets to `NamOshun@WAI2026`
- `souppoetry@gmail.com` → resets to `NamOshun@WAI2026`

One-time use only. Remove immediately after using.

---

## Layer 2: Recovery Codes

**Use this if:** You have your recovery codes saved and want a permanent recovery method.

**What they are:** 4 one-time-use codes (format: `YYYY-XXXX-XXXX-XXXX`) generated on account creation.

**How to find them:** They should be saved in your secure vault (password manager, encrypted document, etc).

### If You Have a Recovery Code

1. **Go to Emergency Recovery Page**
   - URL: https://ancestral-sage-debug-production.up.railway.app/recovery
   - Or: From login page, click "Lost access? Use recovery code"

2. **Enter Your Information**
   - Email: Your executive email (delon.oliver@, youpickeddoliver@, souppoetry@)
   - Recovery Code: One of your 4 codes (type it exactly)
   - New Password: Any password 6+ characters

3. **Click Recover**
   - System verifies the code is valid and unused
   - Resets your password immediately
   - Logs you in with a JWT token
   - Code is marked as used (cannot be reused)

4. **Save Your Remaining Codes**
   - You now have 3 recovery codes left
   - When you have < 2 codes, generate new ones (see below)

### If You Don't Have Your Codes

**Go to Layer 1 (EXEC_FORCE_RESET) to regain access, then generate new codes.**

### Generate New Recovery Codes

Once logged in:

1. **Via API (Recommended)**
   ```bash
   curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/recovery-codes-generate \
     -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
     -H "Content-Type: application/json"
   ```

2. **Via Frontend**
   - Go to Account Settings → Security
   - Click "Generate Recovery Codes"
   - Save the 4 new codes immediately

3. **Response Format**
   ```json
   {
     "ok": true,
     "recovery_codes": [
       "1234-ABCD-EFGH-IJKL",
       "5678-MNOP-QRST-UVWX",
       "9012-YZAB-CDEF-GHIJ",
       "3456-KLMN-OPQR-STUV"
     ],
     "message": "SAVE THESE CODES IN A SECURE LOCATION..."
   }
   ```

**⚠️ SAVE THESE IMMEDIATELY — you will not see them again.**

---

## Layer 3: Backup Executive Accounts

**Use this if:** You have access to one of your other executive email addresses.

**What they are:** Three executive accounts under your control:

| Email | Password | Status |
|---|---|---|
| `delon.oliver@lightningcityelectric.com` | `Executive@LCE2026` | Primary |
| `youpickeddoliver@gmail.com` | `NamOshun@WAI2026` | Backup 1 |
| `souppoetry@gmail.com` | `NamOshun@WAI2026` | Backup 2 |

### How to Use

1. **If One Email is Locked**
   - Log in with a different email address
   - Full executive access from that account

2. **If You Forget That Password**
   - Use Layer 1 (EXEC_FORCE_RESET) or Layer 2 (Recovery Code)
   - Both methods work for any of the three emails

3. **Check Which Account You're In**
   - Click your avatar/menu → Account
   - Shows currently logged-in email
   - Switch accounts by logging out and logging in again

---

## API Endpoints for Recovery

### 1. Check Recovery Code Status

```bash
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/recovery-status \
  -H "Content-Type: application/json" \
  -d '{"email": "youpickeddoliver@gmail.com"}'
```

**Response:**
```json
{
  "ok": true,
  "remaining_codes": 4,
  "total_codes": 4,
  "generated_at": "2026-05-22T14:30:00Z"
}
```

### 2. Use a Recovery Code to Regain Access

```bash
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/emergency-recovery \
  -H "Content-Type: application/json" \
  -d '{
    "email": "youpickeddoliver@gmail.com",
    "recovery_code": "1234-ABCD-EFGH-IJKL",
    "new_password": "YourNewPassword123"
  }'
```

**Response:**
```json
{
  "ok": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "email": "youpickeddoliver@gmail.com",
  "message": "Account recovered. You are now logged in. Please update your password in settings."
}
```

### 3. Generate New Recovery Codes (requires auth)

```bash
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/recovery-codes-generate \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "ok": true,
  "recovery_codes": ["1234-...", "5678-...", "9012-...", "3456-..."],
  "message": "SAVE THESE CODES IN A SECURE LOCATION...",
  "valid_for_days": 365
}
```

---

## Security Features

### Recovery Codes
- **One-time use** — Each code can only be used once, then it's marked as used
- **Hashed storage** — Codes are SHA256 hashed in database, never stored plaintext
- **4 per account** — Multiple codes protect against single code loss
- **1-year TTL** — Codes expire 1 year after generation (auto-deleted from DB)
- **Audit logged** — Every recovery code use is logged with timestamp and IP

### Recovery Log
- **7-year retention** — All recovery actions logged for compliance
- **Immutable trail** — Cannot be deleted or modified after creation
- **IP tracking** — Records the IP address of every recovery attempt
- **Action types** — `codes_generated`, `password_reset`, `recovery_used`

### Rate Limiting
- Max 10 recovery attempts per IP per 5 minutes
- Max 3 recovery attempts per email per 10 minutes
- EXEC_FORCE_RESET can only be used once per deploy
- After 5 failed attempts, manual password reset required

---

## Disaster Scenarios

### Scenario 1: Forgot Password, No Access

1. Use **Layer 1 (EXEC_FORCE_RESET)**
   - Add `EXEC_FORCE_RESET=1` to Railway variables
   - Wait 60 seconds for redeploy
   - Log in with reset password
   - DELETE the variable immediately
   - Change to a new password

### Scenario 2: Forgot Password, Have Recovery Code

1. Use **Layer 2 (Recovery Code)**
   - Go to recovery page
   - Enter email + recovery code + new password
   - Immediately logged in

### Scenario 3: Forgot Password, Have Backup Email Access

1. Use **Layer 3 (Backup Account)**
   - Log in with different executive email
   - Change password on the locked account via admin tools
   - Log back in

### Scenario 4: All Three Recovery Methods Failed

Contact your system administrator or database expert to:
1. Verify your identity (who you are, your role)
2. Look up your user record in MongoDB
3. Hash a new password using bcrypt
4. Update the password_hash field directly in the database
5. Send you a one-time login link

**Prevention:** Always maintain at least 2 of 3 recovery methods active.

---

## Maintenance & Best Practices

### Monthly Checklist
- [ ] Verify you can still access all 3 executive email accounts
- [ ] Check that your recovery codes are saved in your password manager
- [ ] Test one recovery code (use it, verify it marks as used)
- [ ] Generate new recovery codes if < 2 codes remaining
- [ ] Update passwords on any account you haven't accessed in 30 days

### When to Generate New Codes
- When you have fewer than 2 codes remaining
- After a security incident or suspected compromise
- Every 90 days as a preventive measure
- When you lose the document where codes are stored

### Where to Store Recovery Codes
✅ **Good:**
- 1Password, Bitwarden, or other password manager
- Encrypted document on your personal computer
- Bank safe deposit box (printed)
- Spouse's password manager (for spousal access if needed)

❌ **Bad:**
- In plaintext file on your desktop
- In email drafts
- In Slack messages
- Screenshots without encryption
- Sticky notes

### Audit Trail

Every recovery action is logged. To review:

1. **Via API** (if you have access)
   ```bash
   curl https://ancestral-sage-debug-production.up.railway.app/api/admin/audit-log?action=recovery \
     -H "Authorization: Bearer <JWT_TOKEN>"
   ```

2. **In MongoDB**
   ```javascript
   db.recovery_log.find({
     email: "youpickeddoliver@gmail.com"
   }).sort({at: -1}).limit(10)
   ```

---

## Troubleshooting

### "Recovery code invalid or already used"
- Code was already used → Generate new codes
- Code has wrong format → Check spacing (YYYY-XXXX-XXXX-XXXX)
- Code is expired → Codes expire after 1 year; generate new ones

### "Too many requests, slow down"
- You've tried 10+ times in 5 minutes
- Wait 5 minutes, then try again
- If persistent, use a different recovery method

### "Recovery code endpoint 404"
- Update is still deploying
- Wait 2 minutes, refresh the page
- Check Railway deployments to see if build completed

### "EXEC_FORCE_RESET not working"
- Variable not set correctly (check spelling: `EXEC_FORCE_RESET=1`)
- Deploy not yet complete (wait 60 seconds, refresh Railway dashboard)
- Variable was deleted before redeploy completed (add it again)
- Port number mismatch (Railway config changed)

### "Can't access backup email"
- Try EXEC_FORCE_RESET on any of the 3 emails
- All 3 emails are valid, use whichever you can access

---

## Implementation Details

### Recovery Module
- **File:** `backend/recovery.py`
- **Functions:**
  - `generate_recovery_codes(db, email)` → List[str]
  - `verify_recovery_code(db, email, code)` → bool
  - `get_recovery_code_status(db, email)` → dict
  - `emergency_password_reset(db, email, new_password, reason)` → bool
  - `ensure_recovery_codes_exist(db, emails)` → None

### API Endpoints
- **File:** `backend/server.py`
- **Routes:**
  - `POST /api/auth/recovery-status` — Check remaining codes
  - `POST /api/auth/emergency-recovery` — Use code to regain access
  - `POST /api/auth/recovery-codes-generate` — Generate 4 new codes

### Database Collections
- **recovery_codes** — Hashed codes per email (TTL: 1 year)
- **recovery_log** — Audit trail (TTL: 7 years)
- **password_reset_tokens** — Traditional password reset (TTL: 24 hours)
- **users** — User accounts with password_hash

### Indexes
- `recovery_codes` → `email` (unique)
- `recovery_codes` → `generated_at` (TTL 365 days)
- `recovery_log` → `(email, at)` (for queries)
- `recovery_log` → `at` (TTL 7 years)

---

## Testing Recovery Methods

### Test Layer 1 (EXEC_FORCE_RESET)
```bash
# In Railway:
# 1. Add EXEC_FORCE_RESET=1
# 2. Wait 60 seconds
# 3. Try login with default password

curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "youpickeddoliver@gmail.com",
    "password": "NamOshun@WAI2026"
  }'
```

### Test Layer 2 (Recovery Codes)
```bash
# Check status
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/recovery-status \
  -H "Content-Type: application/json" \
  -d '{"email": "youpickeddoliver@gmail.com"}'

# Use a code (requires a real code from the account)
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/emergency-recovery \
  -H "Content-Type: application/json" \
  -d '{
    "email": "youpickeddoliver@gmail.com",
    "recovery_code": "XXXX-XXXX-XXXX-XXXX",
    "new_password": "TestPassword123"
  }'
```

### Test Layer 3 (Backup Accounts)
```bash
# Just log in with a different email
curl -X POST https://ancestral-sage-debug-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "souppoetry@gmail.com",
    "password": "NamOshun@WAI2026"
  }'
```

---

## Emergency Contact

If all recovery methods fail:

1. **Verify your identity** (photo ID, email verification, etc)
2. **Contact your system administrator** with:
   - Your full name
   - Executive email address
   - Proof of role (employment letter, etc)
   - Phone verification

3. **Manual recovery** (database-level reset):
   - Admin verifies your identity
   - Admin uses MongoDB to update your password hash
   - Admin generates a one-time reset link
   - You receive link via verified email
   - You set new password

---

## Final Checklist

✅ **Before considering yourself fully set up:**

- [ ] You've tested EXEC_FORCE_RESET (add/remove the variable)
- [ ] You've saved your 4 recovery codes in your password manager
- [ ] You've tested using a recovery code to regain access
- [ ] You've verified access to all 3 executive email accounts
- [ ] You've changed all passwords to something you'll remember
- [ ] You understand the recovery process well enough to explain it
- [ ] You have a backup person who can help in emergencies
- [ ] You've documented this in your personal security notes

---

## Questions?

This system is designed to GUARANTEE you can always regain access to your executive account. Three independent recovery methods means even if two fail, the third will work.

**You will never be permanently locked out of your system.**
