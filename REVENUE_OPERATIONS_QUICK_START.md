# WAI Institute Revenue Operations System
## Quick Start & Integration Guide

**Status:** Production-ready, integrated into main FastAPI application  
**Date:** 2026-05-22  
**Commit:** 90eed76

---

## What's Included

A complete revenue operations infrastructure for managing subscriptions, payments, financial reporting, sales pipeline, and creator payouts.

### Core Modules
- **Billing:** Stripe integration, subscriptions, invoices, payment methods
- **CRM:** Lead management, sales opportunities, pipeline forecasting
- **Financial Reporting:** MRR, churn, LTV/CAC, cohort analysis, forecasting
- **Jobs:** Scheduled payout processing, revenue recognition, renewal reminders
- **Contracts:** Dynamic contract generation (consumer, enterprise, research)

---

## Integration Points

### 1. Startup Initialization (`backend/server.py`)
```python
# Automatic on app startup:
await init_revenue_operations(db)  # Create collections and indexes
init_revenue_services(app, db)     # Attach services to app.state
await start_revenue_operations(db) # Start scheduled jobs
```

### 2. Dependency Injection
Services automatically attached to `app.state`:
- `app.state.stripe_service` - Stripe integration
- `app.state.creator_payout_service` - Creator earnings tracking
- `app.state.financial_service` - Financial metrics

### 3. API Routers
Automatically included in main `api_router`:
- `/api/billing/*` - Subscription and invoice endpoints
- `/api/billing/reporting/*` - Financial metrics endpoints
- `/api/crm/*` - Sales pipeline endpoints

### 4. Database Collections
Created automatically during startup (12 collections):
- `subscriptions`, `invoices`, `payment_methods`
- `creator_balances`, `creator_payouts`, `revenue_events`
- `leads`, `opportunities`, `activity_log`, `contracts`
- `job_execution_log`

### 5. Scheduled Jobs
Running on APScheduler:
- **1st of month, 2am UTC:** Creator monthly payouts
- **Last day of month, 3am UTC:** Revenue recognition
- **Daily, 6am UTC:** Enterprise renewal deadlines
- **Daily, 7am UTC:** Failed payment checks

---

## Environment Configuration

Add to `.env` file:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017/wai_institute

# Stripe (get keys from https://dashboard.stripe.com/apikeys)
STRIPE_API_KEY=sk_test_...           # Test mode key
STRIPE_WEBHOOK_SECRET=whsec_test_...

# JWT Authentication
JWT_SECRET=your-secret-key-32-chars-min

# Optional: Email Notifications
SENDGRID_API_KEY=SG.1234567890abc...
ADMIN_EMAIL=admin@wai-institute.com

# Optional: Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Business Settings
CREATOR_REVENUE_SHARE=0.7    # Creators get 70%
PLATFORM_COMMISSION=0.3       # Platform takes 30%
CREATOR_PAYOUT_MINIMUM=50     # Minimum $50 payout
MONTHLY_PAYOUT_DAY=1          # Pay on 1st of month

# Feature Flags
ENABLE_STRIPE=true
ENABLE_PAYOUTS=false          # Set to true in production
ENABLE_EMAILS=false           # Set to true after SendGrid setup
ENABLE_SLACK_ALERTS=false     # Set to true after Slack setup
```

---

## Testing the System

### 1. Start the Server
```bash
python -m uvicorn backend.server:app --reload --port 8000
```

### 2. Create a Test Subscription
```bash
curl -X POST http://localhost:8000/api/billing/subscribe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "tier": "basic",
    "billing_cycle": "monthly",
    "payment_method_id": "pm_card_visa"
  }'
```

### 3. Check Financial Dashboard
```bash
curl http://localhost:8000/api/billing/reporting/summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Create a Sales Lead
```bash
curl -X POST http://localhost:8000/api/crm/leads \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "industry": "Technology",
    "decision_maker": {
      "name": "John Doe",
      "title": "CTO",
      "email": "john@acme.com"
    },
    "source": "inbound"
  }'
```

---

## Key Endpoints

### Billing
- `POST /api/billing/subscribe` - Create subscription
- `GET /api/billing/subscription` - Get current subscription
- `POST /api/billing/subscription/upgrade` - Change tier
- `GET /api/billing/invoices` - Invoice history
- `POST /api/billing/webhook` - Stripe webhooks (auto-handled)

### Financial Reporting
- `GET /api/billing/reporting/summary` - Dashboard (all metrics)
- `GET /api/billing/reporting/mrr` - Monthly recurring revenue
- `GET /api/billing/reporting/revenue/{year}/{month}` - Monthly summary
- `GET /api/billing/reporting/ltv-cac` - Lifetime value & acquisition cost
- `GET /api/billing/reporting/forecast?months=12` - Cash flow forecast

### CRM
- `POST /api/crm/leads` - Create lead
- `GET /api/crm/leads` - List leads (with filtering)
- `PUT /api/crm/leads/{id}` - Update lead (score, status, owner)
- `POST /api/crm/opportunities` - Create opportunity from lead
- `GET /api/crm/metrics/pipeline` - Pipeline by stage
- `GET /api/crm/metrics/summary` - All sales metrics

### Creator Payouts
- `GET /api/billing/creator/balance` - Earnings summary
- `POST /api/billing/creator/withdraw` - Request withdrawal
- `GET /api/billing/creator/payouts` - Payout history

---

## Database Schema

### Subscriptions Collection
```json
{
  "_id": ObjectId,
  "user_id": "user_123",
  "stripe_subscription_id": "sub_123",
  "tier": "basic",
  "status": "active",
  "billing_cycle": "monthly",
  "current_period_start": Date,
  "current_period_end": Date,
  "created_at": Date
}
```

### Invoices Collection
```json
{
  "_id": ObjectId,
  "user_id": "user_123",
  "subscription_id": ObjectId,
  "stripe_invoice_id": "in_123",
  "amount": 9.99,
  "status": "paid",
  "due_date": Date,
  "paid_at": Date,
  "created_at": Date
}
```

### Leads Collection
```json
{
  "_id": ObjectId,
  "company_name": "Acme Corp",
  "industry": "Technology",
  "decision_maker": {
    "name": "John Doe",
    "title": "CTO",
    "email": "john@acme.com"
  },
  "source": "inbound",
  "status": "lead",
  "score": 75,
  "owner_id": "sales_rep_123",
  "created_at": Date
}
```

### Opportunities Collection
```json
{
  "_id": ObjectId,
  "lead_id": ObjectId,
  "deal_name": "Enterprise License",
  "deal_value": 150000,
  "stage": "demo",
  "probability": 0.5,
  "owner_id": "sales_rep_123",
  "expected_close_date": Date,
  "created_at": Date
}
```

---

## Deployment Notes

### Free Tier
- MongoDB: Local or Atlas free tier (512 MB)
- Stripe: Test mode (zero transaction fees)
- APScheduler: Runs on main server (no external service)
- SendGrid: 100 emails/day free
- Slack: Free workspace (message history limit)

### Production Deployment
1. Update `.env` with production Stripe keys (`sk_live_*`)
2. Set `ENVIRONMENT=production` 
3. Generate new `JWT_SECRET`
4. Configure SendGrid for email notifications
5. Set `ENABLE_PAYOUTS=true` when ready to process creator payments
6. Configure Slack webhook for alerts
7. Deploy to Railway/Docker/EC2

### Monitoring
- Check MongoDB indexes creation during startup
- Monitor job execution log: `db.job_execution_log.find()`
- Watch Stripe webhook deliveries in dashboard
- Review payment failures in `db.invoices.find({status: "open"})`

---

## Common Tasks

### Process Creator Payouts (Manual)
```python
from backend.billing.stripe_service import CreatorPayoutService
import asyncio

async def payout():
    service = CreatorPayoutService(db, stripe_api_key)
    result = await service.process_monthly_payouts()
    print(result)

asyncio.run(payout())
```

### Get Financial Summary
```python
from backend.billing.financial_reporting import FinancialReportingService
import asyncio

async def report():
    service = FinancialReportingService(db)
    summary = await service.get_dashboard_summary()
    return summary

asyncio.run(report())
```

### Recognize Monthly Revenue
```python
from backend.billing.financial_reporting import RevenueRecognitionService
import asyncio
from datetime import datetime

async def recognize():
    service = RevenueRecognitionService(db)
    now = datetime.utcnow()
    count = await service.recognize_monthly_subscription_revenue(now.year, now.month)
    print(f"Recognized {count} revenue events")

asyncio.run(recognize())
```

---

## Troubleshooting

### Issue: Collections not created
**Fix:** Check `startup()` logs for database initialization errors. Verify MongoDB connection.

### Issue: Stripe webhooks not received
**Fix:** Verify webhook secret matches Stripe dashboard. Check Route53/DNS for domain issues.

### Issue: Jobs not running
**Fix:** Check `job_execution_log` collection. Verify APScheduler logs in application output.

### Issue: Creator payouts stuck
**Fix:** Check `creator_balances` and `creator_payouts` collections. Verify Stripe Connect account is set up.

---

## Next Steps

1. **Test locally** with Stripe test keys
2. **Configure email** for subscription confirmations
3. **Set up Slack alerts** for failed payments
4. **Deploy to staging** and run full flow test
5. **Monitor first week** of production use
6. **Document custom workflows** specific to WAI Institute

---

**See:** `OPERATIONS_SETUP.md` for detailed deployment instructions  
**See:** `FREE_TIER_OPERATIONS.md` for cost-free operation through growth  
**See:** `HANDOFF.md` for system state and debugging

---

**Integration Complete** ✅  
System is ready for testing and deployment.
