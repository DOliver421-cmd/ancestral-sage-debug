# Railway Deployment Troubleshooting — May 22, 2026

## Current Status
- **API Status:** 502 (Application Failed to Respond)
- **Last Push:** 6b0c2b2 (Dockerfile fix to correct backend directory structure)
- **Time Since Push:** ~15 minutes
- **Expected Recovery:** 2-5 minutes (but may take longer for cold start)

## Likely Issues & Solutions

### Issue 1: Environment Variables Not Set
**Symptom:** App crashes on startup trying to read MONGO_URL or other env vars
**Check:** Railway project settings → Variables tab
**Required Variables:**
- MONGO_URL: MongoDB connection string (Railway's built-in or external Atlas)
- MONGO_BACKUP_URL: Optional fallback Atlas connection
- JWT_SECRET: For authentication token signing
- STRIPE_SECRET_KEY: For payment processing
- ANTHROPIC_API_KEY: For AI features
- OPENAI_API_KEY: For OpenAI integration

**Fix:** Add missing variables to Railway environment

### Issue 2: MongoDB Connection Timeout
**Symptom:** Server starts but can't connect to database
**Check:** Verify MongoDB instance is running and accessible
**Fix:** 
- If using Railway MongoDB: ensure service is running
- If using Atlas: verify IP whitelist includes Railway's IP range (0.0.0.0/0 for testing)

### Issue 3: Missing Python Dependencies
**Symptom:** ImportError for anthropic, motor, pymongo, etc.
**Check:** Verify requirements.txt is in backend/ directory
**Fix:** Dockerfile correctly copies backend/ so requirements.txt should install

### Issue 4: Port Configuration
**Symptom:** App runs but doesn't listen on PORT env variable
**Check:** Verify CMD in Dockerfile uses $PORT environment variable
**Current:** `CMD uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}`
**Status:** ✓ Correct (defaults to 10000 if $PORT not set)

---

## Manual Testing (Local)

### Test 1: Verify Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Test 2: Verify Backend Startup (if env vars available)
```bash
cd backend
export MONGO_URL="mongodb://..." 
export JWT_SECRET="test-secret"
export STRIPE_SECRET_KEY="sk_test_..."
export ANTHROPIC_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
python -m uvicorn server:app --reload --port 8000
```

### Test 3: Test Bug Report Endpoint (Once Running)
```bash
curl -X POST http://localhost:8000/api/bug-report \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "paymentMethod": "venmo",
    "paymentHandle": "@testuser",
    "whatYouTried": "Signed up and clicked around",
    "whatBroke": "Course page loaded but videos didn't play",
    "screenshot": "base64_encoded_image_here"
  }'
```

---

## Next Steps

### Option A: Check Railway Logs (Recommended)
1. Go to railway.app dashboard
2. Find ancestral-sage-debug project
3. Click "Logs" tab
4. Look for error messages after latest deploy
5. Post errors here for analysis

### Option B: Manual Deployment Check
1. Verify all environment variables are set in Railway
2. Trigger a redeploy manually from Railway dashboard
3. Wait 3-5 minutes for startup
4. Test /api/version endpoint again

### Option C: Rollback & Debug
1. Revert Dockerfile to known-working state
2. Deploy backend-only without complex Python setup
3. Test health endpoint
4. Add complexity back incrementally

---

## Campaign Launch Status

**BLOCKED:** Waiting for API verification. Cannot launch bug bounty campaign until backend is confirmed healthy.

**READY TO EXECUTE** (Once API Online):
1. Post bug bounty to Facebook
2. Monitor bug_reports collection
3. Execute mentor recruitment
4. Execute corporate training outreach

---

## Success Criteria for Deployment

- [ ] GET /api/version returns {"status":"ok"}
- [ ] POST /api/bug-report accepts requests and stores data
- [ ] No 502 errors from Railway
- [ ] Logs show clean startup with no errors
- [ ] MongoDB connection successful

Once all criteria met → Campaign Launch Phase begins
