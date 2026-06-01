# WAI Institute — Admin Handbook

**Author:** Delon Oliver  
**Publication:** WAI Institute, NAM Oshun Mission  
**Version:** 1.0

---

## 1. Organizational Structure

```
NAM Oshun (Delon Oliver)
└── Director
    ├── Assistant Director
    ├── Revenue Director
    ├── Finance Director
    ├── Customer Success
    ├── Production Team (7)
    └── M.O.R.E. Help Center
```

You are responsible for the operational backbone that enables every other role to function.

---

## 2. Core Systems

### AI Persona Engine
The WAI backend runs 17 AI personas across 5 tiers. These personas handle curriculum delivery, student support, revenue operations, and creative production. Admin ensures the server stays running and secrets stay secret.

### Key Endpoints (local)
- API Server: `http://localhost:8001`
- M.O.R.E. Hub: `/more` route
- Creator Courses: `/api/creator-courses/`

### Environment Variables
Stored in `backend/.env` (gitignored). Critical vars:

- `OPENAI_API_KEY` — Powers all AI personas
- `GUMROAD_API_KEY` — Digital product sales
- `STRIPE_SECRET_KEY` — Payment processing
- `ANTHROPIC_API_KEY` — Additional AI models

Never commit these to version control.

---

## 3. Daily Operations

### Startup
```bash
cd backend
python -m server           # API server (port 8001)
```

### Health Checks
```bash
python scripts/tools/verify_endpoints.py    # Smoke test all routes
python scripts/tools/deploy_sim.py          # Deploy simulation data
```

### Monitoring
- Check server logs for persona errors
- Monitor API response times
- Track student enrollment and revenue data
- Verify Stripe webhook delivery

---

## 4. Revenue Administration

### Current Products
| Product | Price | Platform |
|---------|-------|----------|
| Book I: Deep Roots | $9.99 | Gumroad |
| M.O.R.E. Membership (Monthly) | $9.99 | WAI |
| M.O.R.E. Membership (Annual) | $79.99 | WAI |
| Certification Exams | $49 | WAI |
| Creator Courses | Variable | WAI Marketplace |

### Revenue Streams
1. Student subscriptions ($9.99-$99.99/mo)
2. Creator marketplace (70/30 split)
3. Certification exams ($49)
4. Corporate training ($5K-$15K/cohort)
5. Premium support ($99/mo)

---

## 5. Safety & Compliance

- All `rm`, `git reset --hard`, and `git push --force` commands are prohibited from automated execution
- `git push` requires human confirmation
- Secrets must never appear in logs or commit history
- Student PII must never be exposed via API

---

## 6. Persona System Overview

| Tier | Personas |
|------|----------|
| 1 | NAM Oshun, Delon Oliver |
| 2 | Director |
| 3 | Assistant Director |
| 4 | Ancestral Sage, Revenue Director, Cipher, Oracle, Ambassador, Architect, Savant Scholar, Apprentice, Product Designer, Risk Officer, Strategic Navigator, WAI Success Engine, Confidentiality Sentinel, PRT |
| 5 | Elder Council |
| Fusion | The 9 |

Each T4 persona has specific tools and produces sellable digital products ($9.99-$349.00). Revenue projection: $16K-$71K/yr at slow-to-moderate demand.

---

## 7. Escalation Matrix

| Incident | Response | Timeline |
|----------|----------|----------|
| Server down | Restart service | < 5 min |
| API errors | Check logs, rollback if needed | < 15 min |
| Payment failure | Check Stripe dashboard | < 1 hr |
| Security breach | Revoke keys, notify Director | Immediate |
| Student complaint | Escalate to Customer Success | < 24 hrs |

---

## 8. Deployment

- Code deploys automatically via Railway from `origin/main`
- Environment variables must be set manually in Railway dashboard
- Test locally before pushing to main

---

*"You do not run the Institute. You serve the mission by running the systems."*
