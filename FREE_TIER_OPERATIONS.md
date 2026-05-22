# WAI INSTITUTE - FREE TIER OPERATIONS
## Run Everything Free. Pay Only When You Earn.
**Everything works 100% free locally. Zero paid services required until you have revenue.**

---

## THE PRINCIPLE

You don't pay **anything** until the system generates revenue that justifies the cost.

- **Development/Testing:** 100% FREE
- **Production (small scale):** 100% FREE
- **When to upgrade:** Only when annual costs << annual revenue from that service

---

## WHAT'S FREE

### Stripe (Payment Processing)
✅ **Test Mode:** Completely FREE
- Process test payments with card `4242 4242 4242 4242`
- No transaction fees
- Unlimited test transactions
- Full webhook testing

**When you switch to Production:**
- 2.9% + $0.30 per transaction (unavoidable - you're collecting money)
- **Breakeven:** ~$100/month revenue (platform takes $3 in fees)
- Don't switch until you have real payments

### MongoDB (Database)
✅ **Free Tier (Atlas Cloud):** 
- 512 MB storage (enough for ~100K users with moderate data)
- No credit card required
- Full query functionality

✅ **Or: Run Locally (Best for Development)**
- MongoDB Community Edition: FREE & OPEN SOURCE
- Zero cloud costs
- Full control
- Perfect for development/staging

**When to upgrade:**
- Reach 512 MB data limit (~100K active users or significant data)
- Need global redundancy (multi-region)
- **Cost:** $57/month for M10 (1 GB, 3-replica set)

### FastAPI/Python
✅ **100% FREE** - Open source

### Scheduled Jobs (APScheduler)
✅ **100% FREE** - Runs on your server, no cloud service needed

### Email (SendGrid)
✅ **Free Plan:** 100 emails/day
- Enough for 3,000 monthly users (1 email per month each)
- No credit card required
- When you hit limit, upgrade to paid ($20-100/month)

**When to upgrade:** Only if you send >3,000 emails/month (meaning you have major user base)

### Monitoring (No fancy tools needed yet)
✅ **Free:**
- Built-in logging to files
- Simple error tracking via Slack (free tier)
- Database monitoring via MongoDB Atlas UI (free)

---

## TOTAL COST: $0 UNTIL REVENUE

| Component | Free Option | Cost | When to Upgrade |
|-----------|------------|------|-----------------|
| **Payments** | Stripe test mode | $0 | When in production w/ real payments (2.9% fee) |
| **Database** | Local MongoDB OR Atlas free tier | $0 | 512 MB limit (~100K users) |
| **Code** | FastAPI, Python | $0 | Never - open source |
| **Jobs** | APScheduler (local) | $0 | Never - included in app |
| **Email** | SendGrid free tier | $0 | When > 3K emails/month |
| **Hosting** | Your laptop / free tier (Railway) | $0 | When needing 24/7 uptime (start paying) |
| **Monitoring** | Built-in logging | $0 | When needing serious observability |
| **CRM** | Built-in system | $0 | Never - included |
| **Contracts** | Generated templates | $0 | Never - included |
| **Accounting** | Revenue recognition queries | $0 | Never - included |
| **Slack alerts** | Free plan | $0 | When team >10 people (Slack starts charging) |

**Total:** $0/month for the first 100K users

---

## SETUP: COMPLETELY FREE

### Option A: Local Development (Laptop)
```bash
# Everything runs on your machine
# Zero cloud costs
# Perfect for development and early testing

# Install MongoDB locally
brew install mongodb-community  # macOS
# OR download from https://www.mongodb.com/try/download/community

# Start MongoDB
brew services start mongodb-community
# OR
mongod

# Start FastAPI
python -m uvicorn backend.app_init:app --reload --port 8000

# Cost: $0/month
# Storage: As much as your disk (probably 100+ GB available)
# Database limit: None (local storage)
# Process payouts: Done. $0 to process.
```

### Option B: Railway Free Tier (Hosted)
```bash
# 5 dollars free credit every month (essentially free)
# Perfect for production with low traffic

# 1. Go to https://railway.app
# 2. Sign up with GitHub
# 3. Deploy this repo
# 4. Set environment variables
# 5. Uses your free $5/month credit
# 6. Additional usage: ~$0.000927/hour (negligible for small scale)

# Example monthly cost for low traffic:
# - App hosting: $2-3
# - Database: Included free tier
# - Bandwidth: Free for first 100 GB
# Total: $0-5/month (covered by free credit)

# Cost: $0/month (5 dollar free credit renews monthly)
```

### Option C: AWS/GCP/Azure Free Tier (12 months)
```bash
# AWS: 12-month free tier
# - 750 hours EC2 t2.micro per month
# - 5 GB RDS database
# - Full Stripe integration support

# Deploy same code to EC2
# Run MongoDB on RDS free tier
# Cost: $0 for 12 months
```

---

## STRIPE: HOW TO USE FREE TEST MODE

### Test Mode Setup (Takes 5 minutes)
```bash
# 1. Create Stripe account: https://stripe.com (free)
# 2. Go to https://dashboard.stripe.com/test/apikeys
# 3. Copy Secret key that starts with "sk_test_"
# 4. Add to .env:
STRIPE_API_KEY=sk_test_1234567890abcdefghijklmnop
```

### Test Everything Free
```bash
# Create subscription (no charge)
curl -X POST http://localhost:8000/api/billing/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "tier": "basic",
    "billing_cycle": "monthly",
    "payment_method_id": "pm_card_visa"
  }'

# Test payment succeeds (automatic in test mode)
# See invoice in database (paid)
# Process creator payout (test, no real transfer)
# Check financial reports

# All free. No transaction fees. Full testing.
```

### Test Cards (Never Charged)
```
4242 4242 4242 4242  - Success
4000 0000 0000 0002  - Decline
5555 5555 5555 4444  - Mastercard success
3782 822463 10005    - American Express success
```

Every test transaction: $0 cost

### Switch to Production When Ready
```bash
# 1. Get REAL Stripe keys: https://dashboard.stripe.com/apikeys (production)
# 2. Update .env
# 3. Cost: 2.9% + $0.30 per transaction
# 4. Example: $9.99 basic tier = you receive $9.69

# Don't do this until you have:
# - Real users signing up
# - Revenue > $300/month (so fees < $10)
```

---

## DATABASE: LOCAL VS. CLOUD

### Option 1: Local MongoDB (ZERO COST)
**Perfect for development, small production**
```bash
# Install: 2 minutes
brew install mongodb-community

# Start: 1 command
mongod

# Storage: Unlimited (your disk space)
# Cost: $0/month forever
# Data: Stays on your computer

# Downside: Not available if your laptop is off
# Solution: Run on cheap server ($5-10/month)
```

### Option 2: MongoDB Atlas Free Tier
```bash
# Go to https://www.mongodb.com/cloud/atlas
# Sign up (free)
# Create free cluster
# Get connection string
# Cost: $0/month forever (for 512 MB)

# When you outgrow 512 MB (~100K users):
# Upgrade to paid: $57/month for 1GB
# But at 100K users you're making money to cover it
```

### The Truth About Database Scaling
- **0-10K users:** 512 MB is plenty (local or free cloud)
- **10K-100K users:** A few GB ($57/month) is fine
- **100K+ users:** At this point you're earning millions, buy proper database

**Cost:** $0 until you're successful enough to afford $57/month

---

## EMAIL: SEND FOR FREE (MOSTLY)

### SendGrid Free Tier
```bash
# Sign up: https://sendgrid.com (free)
# Get API key
# Add to .env:
SENDGRID_API_KEY=SG.1234567890abc...

# Free limit: 100 emails/day
# Cost: $0/month
```

### What You Can Do for Free
- Welcome emails to new users
- Subscription confirmation emails
- Monthly invoice emails
- Renewal reminders

### Real Numbers
- 1,000 active users = ~100 emails/month (1 email per user per month)
- 3,000 active users = ~300 emails/month (easily under 100/day limit)
- 10,000 active users = might hit 100/day limit

### When You Scale Beyond Free
```bash
# SendGrid paid: $20/month = 300,000 emails/month
# At 10K users, that's $20/month
# At that scale you're making $10K+/month, easy to afford

# Cost: $0 until thousands of users
```

---

## SLACK ALERTS: FREE UNTIL YOU GROW

### Setup (Free)
```bash
# 1. Create free Slack workspace: https://slack.com
# 2. Create #alerts channel
# 3. Create webhook: https://api.slack.com/messaging/webhooks
# 4. Add to .env:
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# Cost: $0 if team < 10 people (unlimited free messages)
```

### Slack Pricing Reality
- **Free:** 10K most recent messages (you'll hit this eventually)
- **Pro:** $12.50/person/month when you need full history
- **At what scale?** When you have 5+ person team obsessing over metrics
- **Cost:** $0 until you can afford it

---

## HOSTING: WHERE TO RUN THIS FREE

### Option 1: Your Laptop (Development)
```bash
python -m uvicorn backend.app_init:app --reload

# Cost: $0 (electricity)
# Uptime: Only when laptop is on
# Use case: Development, testing
```

### Option 2: Railway Free Tier (Production - Recommended)
```bash
# https://railway.app
# Sign up with GitHub
# Deploy this repo
# Get free $5/month credit (renews every month)

# Performance: Plenty for 1M requests/month
# Storage: Free MongoDB with 512 MB
# Bandwidth: Free (limited but ample for most traffic)

# Example loads and cost:
# - 10K users/month: Costs $0-1/month (covered by credit)
# - 100K users/month: Costs $3-5/month (covered by credit)
# - 1M users/month: Costs $20-50/month (now you have revenue to cover)

# Cost: $0/month (free credit covers it)
```

### Option 3: Oracle Cloud Free Tier (1 year)
```bash
# https://www.oracle.com/cloud/free/
# Get 1 year of:
# - 2 ARM-based Ampere Compute (forever)
# - 1 AMD-based Compute (1 year)
# - 100 GB of Block Storage
# - 10 GB of Object Storage
# - Plenty for WAI system

# Deploy FastAPI + MongoDB
# Cost: $0 for 1 year, then ~$10/month
```

### Option 4: AWS/GCP Free Tier (12 months)
```bash
# AWS: https://aws.amazon.com/free/
# Free for 12 months:
# - 750 hours/month EC2 t2.micro
# - 5 GB RDS database
# - Perfect for WAI system

# Cost: $0 for 12 months, then ~$20-40/month
```

---

## ACTUAL COST TIMELINE

### Months 0-6 (Development & Testing)
| Component | Cost | Notes |
|-----------|------|-------|
| Database | $0 | Local MongoDB on laptop |
| Code hosting | $0 | Run on your machine |
| Stripe | $0 | Test mode only |
| Email | $0 | SendGrid free tier |
| Total | $0 | |

### Months 6-12 (Early Production, First Users)
| Component | Cost | Notes |
|-----------|------|-------|
| Database | $0 | MongoDB local or free Atlas |
| Code hosting | $0 | Railway free tier ($5 credit) |
| Stripe | $20-100 | 2.9% + $0.30 per transaction (you're getting paid) |
| Email | $0 | SendGrid free tier (under 3K emails) |
| Total | $20-100 | But you're receiving $500-5K in revenue |

### Months 12-24 (Growth Phase)
| Component | Cost | Notes |
|-----------|------|-------|
| Database | $57 | MongoDB Atlas M10 (1 GB) |
| Code hosting | $20-100 | Railway or EC2 as you grow |
| Stripe | $300-1000 | 2.9% of revenue (you're making 10K+) |
| Email | $20 | SendGrid Pro if hitting limits |
| Monitoring | $0 | Built-in for now |
| Total | $397-1177 | Your revenue: $10K-50K/month |

### Revenue Required to Cover Costs
- **$20/month costs:** Breakeven at $700/month revenue
- **$100/month costs:** Breakeven at $3,500/month revenue
- **$1,000/month costs:** Breakeven at $35K/month revenue

**Rule:** Never upgrade until revenue > 10x the service cost

---

## CONCRETE EXAMPLE: FIRST YEAR FREE

```
Month 1-2: Development
- Laptop development: $0
- Testing on Railway free tier: $0
- Stripe test mode: $0
- Total: $0
- You have 0 revenue, needs 0 costs ✓

Month 3-6: Soft launch, first users
- 100 users sign up
- Each pays $9.99/month basic tier
- Revenue: $1,000/month
- Stripe fees: 2.9% + $0.30 = $30
- Database: Free tier (50 MB used)
- Hosting: Railway free tier
- Email: SendGrid free tier (100 emails/month)
- Total cost: $30/month
- Profit: $970/month ✓

Month 7-12: Growing to 1K users
- 1,000 users sign up
- Average tier: Advanced ($29.99)
- Revenue: $30K/month
- Stripe fees: $900
- Database: Free tier (100 MB used)
- Hosting: Railway free tier
- Email: SendGrid free tier
- Total cost: $900/month
- Profit: $29K/month ✓

Month 13+: Scaled to 10K users
- 10,000 users
- Average tier: Advanced
- Revenue: $300K/month
- Stripe fees: $9K
- Database: $57/month (1 GB tier)
- Hosting: $50/month (scaled Railway)
- Email: $20/month (SendGrid Pro)
- Monitoring: $100/month (Datadog)
- Total cost: $9,227/month
- Profit: $290K/month ✓

At every stage: Profit > Costs × 10-100x
Never paying for anything unnecessary
```

---

## THE PHILOSOPHY: PAY AS YOU GROW

### Don't Do This ❌
- Pay $1,000/month for "enterprise" database when free tier works
- Subscribe to fancy monitoring with 0 users
- Deploy to 3-region multi-continent setup day 1
- Buy $500/month Slack workspace when you have 2 people

### Do This Instead ✅
- Start completely free
- Run locally until it's too inconvenient
- Move to cheapest paid tier only when free is insufficient
- Scale deliberately after validating demand
- Never pay for something that doesn't make you money

---

## WHEN TO FINALLY PAY FOR THINGS

| Trigger | Service | Action |
|---------|---------|--------|
| Database >512MB | MongoDB Atlas | Upgrade to M10: $57/month |
| Hosting always offline | Railway | Already free, but pay if you want guarantee |
| Emails >100/day | SendGrid | Upgrade Pro: $20/month |
| Need realtime alerts | Slack | Upgrade from free: $12.50/person/month |
| Needs are complex | Monitoring | Subscribe to proper tool: $100+/month |
| Team >10 people | Infrastructure | Hire DevOps expert: Varies |

**Trigger for each:** When NOT paying costs you more in revenue lost

---

## SETUP INSTRUCTIONS: FREE VERSION

```bash
# 1. Clone repo
git clone <repo>

# 2. Local MongoDB (free)
brew install mongodb-community
brew services start mongodb-community

# 3. Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configuration (FREE)
cp .env.example .env

# Edit .env:
# STRIPE_API_KEY=sk_test_... (get free from Stripe test mode)
# MONGODB_URI=mongodb://localhost:27017/wai_institute
# SENDGRID_API_KEY=(leave blank if not sending emails)
# SLACK_WEBHOOK_URL=(leave blank if no alerts)
# All optional features disabled in free mode

# 5. Initialize database
python -c "import asyncio; from backend.database import init_database; asyncio.run(init_database())"

# 6. Run
python -m uvicorn backend.app_init:app --port 8000

# 7. Test
curl http://localhost:8000/health

# Cost: $0
# Uptime: While running
# Limitation: Only available on your laptop
# What to do: Works perfect for development and soft launch
```

---

## BOTTOM LINE

**You're never paying for anything you don't need.**

- Start free on your laptop
- Keep using free as long as it works
- Move to cheapest paid option only when volume justifies it
- At scale where costs matter, you're making 100x those costs in revenue

This is how real companies operate. Netflix didn't buy 5 datacenters day 1.

**Total first year cost: $0-500**
**Revenue from system: $0-100K**

Pay nothing until you can afford it.

---

**See:** `OPERATIONS_SETUP.md` for step-by-step deployment (all free)
