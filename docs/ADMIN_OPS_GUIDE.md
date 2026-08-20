# M.O.R.E. Help Center — Admin & Exec Operations Guide

**Last verified:** August 20, 2026  
**Platform:** www.morehelp.center (this repo) + www.wai-institute.org (separate build)  
**Stack:** FastAPI (Python 3.11) + MongoDB (Motor) + React (CRA/craco) + Railway  

---

## PLATFORM ARCHITECTURE (Verified Reality)

Two doors, two deployments. The MORE help center (this repo) and WAI Institute are separate builds behind different domains. They share the same owner account but do NOT share a database.

| Component | Status | Location |
|-----------|--------|----------|
| Backend API | `backend/server.py` — monolith, ~2365 lines | Railway (charming-analysis) |
| Frontend SPA | `frontend/` — React + Tailwind | Served by backend (SERVE_FRONTEND=1) |
| Database | MongoDB (Motor async driver) | Railway Mongo or external |
| Auth | JWT HS256, 8-tier RBAC | `backend/roles.py` |
| LLM Gateway | 10-tier free-first chain | `backend/ai/llm_gateway.py` |
| Personas | 12 AI personas (prompt strings) | `backend/ai/persona_loader.py` + `backend/prompts/` |

### Role Hierarchy (backend/roles.py)
```
0  public          — unauthenticated visitor
1  student         — registered learner
2  trial_pass      — trial / priority member
3  instructor      — instructor / moderator
4  support_staff   — site support operations
5  oversight       — oversight / governance
6  admin           — platform administrator
7  executive_admin — owner / executive
```

---

## DAILY ROUTINES (5-15 minutes)

### 1. Platform Health Check
- Visit `https://www.morehelp.center/api/version` — should return 200 with `{"status": "healthy"}`
- Visit `https://www.morehelp.center/api/health` — checks MongoDB connection
- Check Railway dashboard for deployment status (should show "Active")

### 2. Review New Users
- Go to `/admin` → User list
- Check for new registrations since yesterday
- Review role assignments — students auto-get `student` role, no manual intervention needed
- Flag any suspicious registrations (unusual emails, rapid signups)

### 3. Check AI Spend
- The LLM gateway enforces a 200K token/hour budget (env: `HOURLY_TOKEN_CAP`)
- If you see frequent "budget exceeded" errors, the cap may need adjusting
- All LLM calls go through `call_llm()` — never direct to providers
- **Anthropic is DISABLED by owner directive.** Do not re-enable without explicit approval.

### 4. Review Audit Log
- Go to `/admin/audit` — shows all privileged actions
- Look for: role changes, user deletions, failed login attempts
- Each audit entry includes: who, what, when, IP

### 5. Verify Payments (if active)
- Check `/payment/history` for recent transactions
- Payment providers (Lemon Squeezy, Gumroad, Stripe) require env keys:
  - `PAYMENTS_ENABLED=1`
  - `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID`
  - `GUMROAD_API_KEY`
  - `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET`
- If any keys are missing, checkout returns 503 — add them in Railway env vars

---

## WEEKLY ROUTINES (30-60 minutes)

### 1. Security Review
- Check `/admin/audit` for failed login patterns (lockouts after 5 attempts)
- Review IP whitelist entries (`/admin/accounts` → exec access list)
- Verify no unauthorized role escalations in the audit log
- Check that `exec` passwords are strong (rotate via `python reset_exec_accounts.py`)

### 2. Content & Curriculum Check
- Review `/modules` — ensure all course content renders correctly
- Check `/courses` page for broken links or missing content
- Verify handbooks at `/api/handbooks/{student|instructor|admin|persona}` return valid HTML
- Test the AI Tutor (`/ai`) — send a test question, verify response

### 3. Payment Flow Test
- If payments are enabled, do a test purchase on a $0 item (if available)
- Verify `/payment/history` records the transaction
- Check that Lemon Squeezy/Gumroad webhook endpoints are reachable

### 4. Partner System Health
- Check `/partnership` dashboard — verify points are accumulating correctly
- Review `/partnership/discounts` — ensure tier thresholds are correct
- Partner tiers: free → bronze → silver → gold → platinum (points-based)

### 5. Database Maintenance
- MongoDB requires no manual maintenance, but check:
  - Collection sizes in Railway Mongo dashboard
  - Index health (indexes are created on startup via `ensure_indexes()`)
  - No orphaned documents in `users`, `progress`, `modules` collections

---

## MONTHLY ROUTINES (2-4 hours)

### 1. Full System Audit
- Run `cd backend && python -m pytest tests/ -v` — all tests should pass
- Run `cd backend && python scripts/tools/verify_endpoints.py` — endpoint smoke tests
- Run `cd backend && python -m tests.revenue_simulation` — revenue scenario testing
- Check `/admin/health` for system health metrics

### 2. Security Rotation
- Rotate JWT_SECRET if it's been >90 days (set new value in Railway env)
- Rotate `PROVIDER_KEY_ENCRYPTION_SECRET` if compromised
- Review and prune IP whitelist entries
- Check that `EXEC_PASSWORD_1/2/3` (or `EXEC_RESET_PASSWORD`) are strong and current

### 3. LLM Provider Review
- Go to `/admin/providers` (Provider Gateway)
- Check which free-tier providers are active and healthy
- Verify fallback chain: Groq → Cerebras → SambaNova → Gemini → Grok → Cohere → Mistral → Together → OpenRouter → HuggingFace
- If a provider's free tier is exhausted, it auto-degrades to next tier
- Anthropic stays DISABLED unless explicitly re-enabled

### 4. Revenue & Pricing Review
- Run `/admin/prices` — review all product prices
- Check `/revenue` (Revenue Division) for income tracking
- Adjust partnership tiers if needed
- Review any discount codes or promotions

### 5. Backup Verification
- If using MongoDB Atlas backup (`MONGO_BACKUP_URL`), verify backup is current
- Test restore procedure (don't actually restore — just verify backup exists)
- Check Railway environment variables are current and complete

### 6. Frontend Build Check
- `cd frontend && npm run build` — should pass cleanly
- Review bundle size (currently ~287KB)
- Check for any new security advisories in dependencies

---

## CRITICAL ENVIRONMENT VARIABLES

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGO_URL` | YES | MongoDB connection string |
| `JWT_SECRET` | YES | JWT signing secret |
| `DB_NAME` | No | Database name (default: ancestral_sage) |
| `SERVE_FRONTEND` | No | Serve React SPA (default: 1) |
| `PAYMENTS_ENABLED` | No | Enable checkout (default: 0) |
| `LEMON_SQUEEZY_API_KEY` | For payments | Lemon Squeezy integration |
| `GUMROAD_API_KEY` | For payments | Gumroad integration |
| `STRIPE_SECRET_KEY` | For payments | Stripe integration |
| `GROQ_API_KEY` | For AI | Primary free LLM provider |
| `CEREBRAS_API_KEY` | For AI | Secondary free LLM provider |
| `GEMINI_API_KEY` | For AI | Google Gemini free tier |
| `ANTHROPIC_IS_ENABLED` | No | Must be "true" to enable (default: false) |
| `HOURLY_TOKEN_CAP` | No | LLM budget limit (default: 200000) |
| `PROVIDER_KEY_ENCRYPTION_SECRET` | For Provider Gateway | Encrypts stored API keys |
| `EXEC_PASSWORD_1/2/3` | For password reset | Per-seat exec passwords |
| `EXEC_RESET_PASSWORD` | Alternative | Shared exec password |

---

## HUMAN ERROR PREVENTION CHECKLIST

### Before Any Production Change:
- [ ] Did you read the file first? (Don't edit blind)
- [ ] Is there a backup of what you're about to change?
- [ ] Did you test locally before deploying?
- [ ] Are you modifying `backend/prompts/`? **STOP** — SHA-256 integrity enforced at runtime
- [ ] Are you calling an LLM directly? **STOP** — use `call_llm()` from gateway
- [ ] Did you check the audit log for related changes?

### Before Changing User Data:
- [ ] Are you on the right user account?
- [ ] Did you verify the user ID, not just the email?
- [ ] Is this change reversible?
- [ ] Did you log the action in the audit system?

### Before Deploying Code:
- [ ] Does `cd frontend && npm run build` pass?
- [ ] Does `cd backend && python -m pytest tests/ -v` pass?
- [ ] Did you check for merge conflicts?
- [ ] Are you committing only files related to your change?

### Common Mistakes to Avoid:
1. **Never delete files** — the owner has been burned by AI sessions deleting paid features
2. **Never commit passwords** — use env vars, never hardcoded values
3. **Never bypass RBAC** — every privileged action goes through `require_role()`
4. **Never expose exec-only content** — Business Office, internal docs, persona prompts
5. **Never modify `backend/prompts/`** — SHA-256 hash check breaks if changed

---

## TROUBLESHOOTING GUIDE

### "Healthcheck failed" on Railway deploy
- The deploy runs `uvicorn backend.server:app` on port 8080
- Healthcheck hits `/api/version` — if it fails, the server isn't starting
- Check Railway logs for Python import errors or missing env vars
- Most common: `MONGO_URL` not set, or a missing Python package

### "403 Forbidden" on admin pages
- Your role must be `admin` (rank 6) or `executive_admin` (rank 7)
- Check your role at `/api/auth/me`
- If you're locked out, use `python reset_exec_accounts.py` (requires `EXEC_PASSWORD_*` env vars)

### "Budget exceeded" on AI chat
- The LLM gateway enforces `HOURLY_TOKEN_CAP` (default 200K tokens/hour)
- This is a safety feature, not a bug
- Wait for the next hour window, or increase the cap in Railway env

### "Payment checkout failed (503)"
- Payments are disabled by default (`PAYMENTS_ENABLED=0`)
- Need: `PAYMENTS_ENABLED=1` + provider API keys in Railway env
- Test with a $0 item first

### Frontend shows 404 for all routes
- `SERVE_FRONTEND` must be `1` (default)
- The built React app must exist at `/app/frontend/build/`
- Rebuild: `cd frontend && npm run build` then redeploy

### AI responses are generic/wrong
- Check that the correct persona prompt is being loaded
- Persona prompts are in `backend/prompts/` — DO NOT MODIFY
- The gateway falls through all 10 tiers if providers fail
- Check `/admin/providers` to see which providers are active

---

## USEFUL COMMANDS

```bash
# Start backend locally
cd backend && python -m server

# Run all tests
cd backend && python -m pytest tests/ -v

# Run endpoint smoke tests
cd backend && python scripts/tools/verify_endpoints.py

# Run revenue simulation
cd backend && python -m tests.revenue_simulation

# Run backend diagnostics
cd backend && python scripts/tools/backend_doctor.py

# Rebuild frontend
cd frontend && npm run build

# Reset exec passwords (requires env vars)
python reset_exec_accounts.py

# Check API version
curl https://www.morehelp.center/api/version

# Check API health
curl https://www.morehelp.center/api/health
```

---

*This guide is based on verified code inspection as of August 20, 2026. If something doesn't match what you see, report it — do not assume the guide is correct over the actual system state.*
