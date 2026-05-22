# Creator Course System — WAI Institute

## Overview
Creators (poets, healers, artists, teachers, community leaders) can build and sell their own courses at **extremely low, tiered pricing**. This democratizes online education and gives creators another income stream.

---

## Pricing Model: SUPER DUPER CHEAP + Dynamic Escalation

### Launch Pricing (Phase 1: Build Audience)

| Type | Launch Price | Creator Earns (70%) | WAI Earns (30%) | Use Case |
|------|--------------|-------------------|-----------------|----------|
| **Workshop** | $1.99 | $1.39 | $0.60 | Single 1-3 hr session |
| **Mini Course** | $3.99 | $2.79 | $1.20 | 2-5 focused lessons |
| **Full Course** | $7.99 | $5.59 | $2.40 | 6+ comprehensive lessons |
| **Certification** | $9.99 | $6.99 | $3.00 | With completion cert + badge |

### Dynamic Price Escalation (As Demand Grows)

**Workshop escalates:**
- 0-49 students: $1.99
- 50-199 students: $2.99
- 200-499 students: $3.99
- 500-999 students: $4.99
- 1000+ students: $5.99

**Mini Course escalates:**
- 0-99 students: $3.99
- 100-299 students: $4.99
- 300-749 students: $6.99
- 750-1499 students: $8.99
- 1500+ students: $9.99

**Full Course escalates:**
- 0-199 students: $7.99
- 200-499 students: $12.99
- 500-999 students: $16.99
- 1000-1999 students: $19.99
- 2000+ students: $24.99

**Certification escalates:**
- 0-149 students: $9.99
- 150-399 students: $14.99
- 400-799 students: $19.99
- 800-1499 students: $24.99
- 1500+ students: $29.99

### Why This Strategy?
- **Launch cheap** = zero friction, fast audience growth
- **Reward popular teachers** = prices auto-increase as courses prove value
- **Students win first** = early adopters pay pennies
- **Fair to all** = same formula applies to everyone
- **Creator incentive** = better economics as you grow
- **Never punish success** = prices increase slowly, existing students keep original price

---

## Creator Workflow

### 1. Create Course (Draft)
```
POST /api/creator-courses/create
  creator_id: "poet_123"
  title: "Poetry for Healing Trauma"
  description: "4-lesson journey through poetry as medicine"
  course_type: "mini"  // workshop, mini, full, cert
  category: "healing"  // healing, art, crafts, business, wellness, education, etc.
  language: "en"       // en, es, pt, fr, hi, ar, ps, sw
```

**Response:**
```json
{
  "status": "success",
  "course_id": "course_abc123",
  "course_type": "mini",
  "price": 9.99
}
```

### 2. Add Lessons
```
POST /api/creator-courses/course/{course_id}/lesson
  title: "Lesson 1: Finding Your Voice"
  content: "<video>, text, exercises, etc"
  duration_minutes: 45
```

**Lesson Limits by Type:**
- Workshop: 1 lesson max
- Mini Course: 2-5 lessons
- Full Course: 6+ lessons
- Certification: Unlimited

### 3. Publish Course
```
POST /api/creator-courses/course/{course_id}/publish
```

**Requirements:**
- ✓ At least 1 lesson
- ✓ Title & description
- ✓ Cover image (optional)
- ✓ Preview video (optional)

Once published, immediately available in marketplace.

### 4. View Dashboard
```
GET /api/creator-courses/dashboard/{creator_id}
```

**Response:**
```json
{
  "status": "success",
  "total_courses": 5,
  "published_courses": 3,
  "draft_courses": 2,
  "courses": [
    {
      "id": "course_abc123",
      "title": "Poetry for Healing",
      "type": "mini",
      "price": 9.99,
      "students": 47,
      "revenue": 469.53,
      "creator_earnings": 328.68,
      "rating": 4.8,
      "published": true
    }
  ],
  "earnings": {
    "total_students": 250,
    "total_revenue": 4295.50,
    "total_earnings": 3006.85,
    "monthly_revenue": 890.12,
    "monthly_earnings": 623.08,
    "last_payout_date": "2026-05-01",
    "next_payout_date": "2026-06-01"
  }
}
```

---

## Student Workflow

### 1. Browse Marketplace
```
GET /api/creator-courses/marketplace
  ?category=healing
  ?language=es
  ?skip=0
  ?limit=20
```

### 2. View Course Details
```
GET /api/creator-courses/course/{course_id}
```

### 3. Enroll (Purchase)
```
POST /api/creator-courses/enroll
  student_id: "student_456"
  course_id: "course_abc123"
```

Payment handled by Stripe Billing system.

### 4. Complete Lessons
```
POST /api/creator-courses/complete
  student_id: "student_456"
  course_id: "course_abc123"
```

Student gets completion certificate + digital badge.

### 5. Leave Review
```
POST /api/creator-courses/review/{course_id}
  student_id: "student_456"
  rating: 5
  review_text: "This saved my life. Thank you."
```

---

## Course Categories
Creators can build courses in any of these areas:

- **Healing**: Trauma recovery, mental health, grief, resilience
- **Art**: Poetry, spoken word, visual art, performance
- **Crafts**: Woodworking, textiles, DIY, sustainable making
- **Business**: Freelancing, small business, finance, entrepreneurship
- **Wellness**: Yoga, meditation, nutrition, movement
- **Education**: Language, academic skills, personal development
- **Music**: Production, performance, songwriting
- **Spirituality**: Meditation, ceremony, indigenous practices
- **Community**: Organizing, activism, social change
- **Other**: Whatever the community needs

---

## Revenue Sharing Model

### Example: Mini Course (Dynamic Pricing)

**Launch Phase (First 100 students):** $3.99

Student pays: **$3.99**

| Recipient | Amount | % |
|-----------|--------|-----|
| Creator | $2.79 | 70% |
| WAI Platform | $1.20 | 30% |
| Processing fees | -$0.18 | (Stripe) |
| **Net to Creator** | **$2.61** | |

**After 100 students, price escalates to $4.99**

| Recipient | Amount | % |
|-----------|--------|-----|
| Creator | $3.49 | 70% |
| WAI Platform | $1.50 | 30% |
| Processing fees | -$0.22 | (Stripe) |
| **Net to Creator** | **$3.27** | |

### Growth Trajectory

| Students | Price | Monthly Revenue | Creator Earns | WAI Earns |
|----------|-------|-----------------|---------------|-----------|
| **50** (launch) | $3.99 | $199.50 | $139.65 | $60.00 |
| **100** | $3.99 | $399 | $279.30 | $119.70 |
| **300** | $4.99 avg | $1,247 | $872.90 | $374.10 |
| **750** | $6.99 avg | $2,321 | $1,624.70 | $696.30 |
| **1500** | $8.99 avg | $3,745 | $2,621.50 | $1,123.50 |

**Key:** Each student pays their entry price once (lifetime access). New students pay current price tier.

---

## Payout Schedule

- **Payouts:** Monthly on 1st
- **Minimum payout:** $50 (otherwise held to next month)
- **Method:** Stripe Connect or bank transfer
- **Timing:** 2-3 business days to reach creator

---

## Quality & Trust

### Course Requirements
- Creators must have verified account
- Courses subject to basic moderation (no hate speech, illegal content)
- Ratings & reviews are public
- Refund policy: 7-day full refund if unsatisfied

### Creator Reputation
- Rating displayed (avg of student reviews)
- Review count visible
- Top creators get featured in "Trending" section
- Top category performers get promoted

---

## Market Opportunity

### Addressable Market
- **Immediate (WAI community):** 500+ registered users
- **Month 1-3:** 50-100 active creators, 200-300 courses
- **Month 6:** 300+ creators, 1000+ courses
- **Year 1:** 500+ creators, $50K-100K monthly course revenue

### Revenue Projections (WAI Gets 30%)
| Scenario | Creators | Courses | MRR (Course Sales) | WAI Share (30%) |
|----------|----------|---------|-------------------|-----------------|
| Conservative | 100 | 300 | $3,000 | $900 |
| Growth | 300 | 1000 | $12,000 | $3,600 |
| Optimistic | 500 | 2000 | $30,000 | $9,000 |

---

## API Endpoints Summary

### Creator Endpoints
```
POST   /api/creator-courses/create                 # Create course draft
GET    /api/creator-courses/course/{id}            # View course
POST   /api/creator-courses/course/{id}/lesson     # Add lesson
POST   /api/creator-courses/course/{id}/publish    # Publish course
GET    /api/creator-courses/dashboard/{id}         # Creator dashboard
GET    /api/creator-courses/pricing                # View pricing
GET    /api/creator-courses/categories             # Available categories
```

### Student/Marketplace Endpoints
```
GET    /api/creator-courses/marketplace            # Browse courses
GET    /api/creator-courses/trending               # Featured/top courses
POST   /api/creator-courses/enroll                 # Enroll in course
POST   /api/creator-courses/complete               # Mark complete
POST   /api/creator-courses/review/{id}            # Leave review
```

---

## Launch Timeline

### Week 1: MVP
- ✅ Core creator course system
- ✅ Create/publish/enroll flow
- ✅ Basic marketplace
- ✅ Creator dashboard

### Week 2: Marketing
- Email creators: "You can now sell courses"
- Feature: "Creator spotlight" in community
- Recruitment: Reach out to top 10 creators

### Week 3: Growth
- Featured "Trending" section
- Category-specific promotions
- Creator revenue leaderboard

### Month 2+
- White-label option for large creators
- Affiliate commissions (creators can earn by promoting others)
- Creator certification program
- Corporate team licensing

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Active creators | 50+ by month 1 | 🎯 |
| Published courses | 200+ by month 1 | 🎯 |
| Student enrollments | 500+ by month 1 | 🎯 |
| Monthly course MRR | $3K+ | 🎯 |
| Creator satisfaction | 4.5+ stars | 🎯 |
| Average course rating | 4.2+ stars | 🎯 |
| Churn (course abandonment) | <10% | 🎯 |

---

## Why This Works

1. **Creators own their content** — Build loyalty, not dependence on algorithm
2. **Super cheap for students** — No gatekeeping, anyone can afford to learn
3. **Better economics than legacy platforms**
   - Udemy: Creator gets ~30%, platform opaque
   - Skillshare: Creator gets 50%, but random revenue share model
   - WAI: Creator gets 70%, transparent, predictable

4. **Community-first** — Courses teach what community actually needs, not what algorithm promotes
5. **Decentralized learning** — Not reliant on one "expert," elevates community teachers

---

## Getting Started

**For Creators:**
1. Sign in to Dashboard
2. Click "Create Course"
3. Choose type ($4.99-$34.99)
4. Add lessons
5. Publish
6. Promote to students
7. Get paid monthly

**For Students:**
1. Browse marketplace by category/language
2. Preview course + reviews
3. Click "Enroll"
4. Pay once (lifetime access)
5. Learn at own pace
6. Leave review to help others

---

**Next Steps:**
- [ ] Onboard first 10 creators (personal outreach)
- [ ] Feature one course daily in community
- [ ] Track creator earnings + satisfaction
- [ ] Monthly creator payouts
- [ ] Quarterly revenue report

---

**Owner:** Delon Oliver / NAM Oshun  
**Launch:** 2026-06-01  
**Target:** $50K+ ARR from course sales by end of year
