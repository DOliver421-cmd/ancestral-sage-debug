# Partnership Discount System — Complete Design

## Core Concept

**"The deeper your partnership, the better our economics work for you."**

Users earn pricing discounts as they deepen their partnership level. Not as a marketing tactic, but as a real dividend of shared investment. The more you build with us, the more we share the margin with you.

---

## Discount Structure

| Partnership Level | Points Range | Course Discount | WAI Margin | Example: $9.99 Course |
|---|---|---|---|---|
| **Seed** | 0-100 | 0% | 30% | $9.99 (no savings) |
| **Rooted** | 100-300 | 5% | 25% | $9.49 (save $0.50) |
| **Builder** | 300-800 | 10% | 20% | $8.99 (save $1.00) |
| **Steward** | 800-2000 | 15% | 15% | $8.49 (save $1.50) |
| **Elder** | 2000+ | 15% | 15% | $8.49 (save $1.50) |

---

## Why 15% Max?

At 15% discount, WAI's margin drops from 30% → 15%. This is the equilibrium point where:

1. **Partners feel the value** — Real savings on every purchase
2. **Platform remains sustainable** — 15% margin covers ops, infrastructure, support
3. **Creators stay protected** — They still get 70%+ of every dollar customers pay
4. **It's a true partnership** — Shared economics, not a charity discount

### The Math
- Customer pays $9.99
- **Seed level:** Creator gets $6.99, WAI gets $3.00 (30%)
- **Elder level:** Creator gets $6.99 (same), WAI gets $1.50 (15%)
- WAI's margin cuts in half, but volume makes up the difference (+ retention)

---

## Cumulative Savings

### One Year (12 courses @ $9.99 avg)
- **Seed → Rooted:** Save $6
- **Seed → Builder:** Save $12
- **Seed → Steward/Elder:** Save $18

### Five Years (60 courses @ $9.99 avg)
- **Seed → Rooted:** Save $30
- **Seed → Builder:** Save $60
- **Seed → Steward/Elder:** Save $90

### Perception
For a $9.99 course, $1.50 savings doesn't sound like much. But:
- Over a year of learning: $18 savings
- Over 5 years: $90 savings
- Over 10 years: $180 savings
- Compounds with course count growth

**Key insight:** It's not about the individual discount—it's about proving "the longer you're here, the better the deal gets." That builds loyalty.

---

## How It Works on the Platform

### On Course Cards
```
Course Title: "Poetry for Healing"
Price: $9.99 (struck through)
Your Price: $8.49
Discount: ✓ 15% off as a Steward
Save: $1.50
```

### On Checkout
```
Subtotal: $9.99
Your Partnership Discount (15%): -$1.50
═══════════════════════════════════
Total: $8.49

Economics:
Creator Earns: $5.94 (70%)
WAI Earns: $1.55 (15%)
```

### On User Profile
Shows current discount + path to next level:
```
Your Partnership Level: Builder
Current Discount: 10% off courses

Next Milestone: Steward (450 more points)
Unlock: 15% discount
```

---

## Implementation Details

### Frontend Files

**`partnership_pricing.js`** — Utilities
```javascript
getPartnershipLevel(points)           // → returns level object
calculatePartnershipPrice(basePrice, points) // → pricing breakdown
getNextLevelDiscount(points)          // → what they unlock next
calculatePartnershipSavings(spent, points) // → lifetime savings
```

**`PartnershipPricing.jsx`** — Display component
- Props: basePrice, partnershipPoints, size (compact/normal/large)
- Shows current price, discount, next level unlock
- Optionally displays economics breakdown

**`PartnershipDiscounts.jsx`** — Education page
- /discounts route
- Full discount structure visual
- Savings calculator (1yr and 5yr projections)
- "Why we do this" explanation

### Backend Integration (TODO)

1. **Partnership Point System**
   - Track user points in MongoDB: `partnership_points` field on user document
   - Update on every action (see partnership_system.md for point values)

2. **Price Calculation**
   - When enrolling, call `calculatePartnershipPrice(basePrice, user.partnershipPoints)`
   - Return both original and discounted price
   - Store both in enrollment record for transparency

3. **Payout Calculation**
   - Creator always gets 70% of what student paid (no reduction for discounts)
   - WAI's share varies by partnership level
   - Track in ledger: original_price, discount_amount, final_price, creator_payout, wai_payout

4. **Reporting**
   - Admin dashboard: revenue impact of discounts
   - Creator dashboard: "Your students' average discount level" (shows how engaged audience is)
   - Financial: track margin erosion vs. retention gains

---

## User Psychology

This system leverages several psychological principles:

### 1. **Reciprocity**
"We're giving you real discounts → you're incentivized to stay invested"

### 2. **Commitment & Consistency**
"I'm already a Builder, might as well keep building to Steward"

### 3. **Progress**
"Look how much I've saved already. Imagine in 5 years..."

### 4. **Status**
"I'm a Steward now" (higher status = better economics = real social signal)

### 5. **Transparency**
"I can see exactly how much I'm saving and why. The math is honest."

---

## Competitive Advantage

### vs. Udemy (30% creator, hidden margins)
- We show exact margins and how they decrease
- Creators still get 70%+ always
- Transparent, not hidden

### vs. Skillshare (50% creator, random revenue share)
- We're clearer: 70% always, margins decrease, not revenue pools
- Predictable, not luck-based

### vs. Patreon (per-creator subscriptions)
- We make discounts part of platform engagement, not individual creator choice
- Scales globally, not creator-by-creator

### vs. Traditional Education (fixed pricing)
- We reward loyalty with actual savings
- Partner gets better over time, not stagnant

---

## Messaging

### To New Users (Seed Level)
"**Pay full price today. Build your partnership, unlock savings tomorrow.**"
- Full transparency that they're not getting discounts yet
- But they see the path to unlocking them
- Empowering, not punitive

### To Growing Users (Rooted/Builder)
"**You're saving more as you grow with us.**"
- Show cumulative savings on dashboard
- Celebrate the discount unlock at each level
- Reinforce: "The more you invest, the more we share"

### To Committed Users (Steward/Elder)
"**You're at our deepest partnership. You've earned maximum savings.**"
- Celebrate with level-up notification
- Show lifetime savings (might be $50-200)
- Emphasize: "You're now part of the core economic model"

---

## Questions This Answers

**Q: Why should users care about 15% off a $9.99 course?**
A: They don't... at first. But $18/year becomes $90 over 5 years. More importantly, it proves "the system is built to reward loyalty," not extract from it.

**Q: Won't this hurt revenue?**
A: Short-term margin erosion (~5-10%), offset by:
- Better retention (cheaper existing customers vs. cheaper new acquisition)
- Increased LTV (longer customers spend more total)
- Higher engagement (partnership motivation)
- Word-of-mouth (people tell friends about the better deal)

**Q: Can creators see they're getting paid less?**
A: No. They always get 70% of what the customer paid. If customer got 15% off, they're also getting less, but the revenue model is transparent: we share the cost of discounts.

**Q: What prevents abuse (creating throwaway accounts to get discounts)?**
A: Partnership points require real actions (courses created/completed, mentorship, community). Can't fake 2000 points without genuine engagement. System tracks actions, not just points.

---

## Integration with Creator Courses

For the creator course system specifically:

**Dynamic pricing + partnership discounts = amazing economics**

Example: Creator publishes mini course at $3.99 launch price
- Seed user: pays $3.99
- Builder user: pays $3.59 (10% off)
- Steward user: pays $3.39 (15% off)

As course grows to 300+ students, base price escalates to $6.99
- Seed user: pays $6.99
- Builder user: pays $6.29 (10% off)
- Steward user: pays $5.94 (15% off)

Early students still get the original price (locked in). New students get escalated price minus their discount. Everyone wins.

---

## Rollout Plan

### Phase 1: Display Layer (Week 1)
- Add PartnershipPricing component to course cards
- Show what discount current user has
- Display next level unlock info
- Launch /discounts education page

### Phase 2: Calculation Layer (Week 2)
- Backend calculates discounted price on enrollment
- Store original + discounted price in database
- Adjust creator payout calculation
- Track margin changes in admin dashboard

### Phase 3: Messaging & Celebration (Week 3)
- Add level-up notifications for discount unlocks
- Show cumulative savings on user dashboard
- Email: "Congrats, you've saved $X as a Builder"
- Leaderboard: show most-saved users

### Phase 4: Optimization (Week 4+)
- A/B test messaging (what resonates?)
- Monitor revenue impact
- Adjust discount tiers if needed (can scale up to 20% if margins support)
- Creator feedback loop (do they like the transparency?)

---

## Success Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Avg partnership level on platform | 2.5+ (Rooted) | Most users should be growing |
| % users at Builder+ | 20%+ | Meaningful discount adoption |
| Retention (users with 10+ purchases) | 40%+ | Discounts reward loyalty |
| ARR impact of discounts | -10% to -5% | Acceptable margin erosion |
| Revenue growth | +30% YoY | Should outpace discount loss |
| Creator satisfaction | 4.5+ stars | Should feel transparency is fair |

---

## Key Principles

1. **Transparency Always** — Every number visible, verified, auditable
2. **Creator Protected** — They never earn less per customer
3. **Real Benefit** — Not cosmetic, actual savings over time
4. **Aligned Incentives** — Platform benefits from long-term customer commitment
5. **Scalable** — Can extend to 20%+ discounts if business model supports
6. **Celebration** — Make every level-up feel special and earned

---

**The bottom line:** Partnership discounts aren't a loyalty program. They're proof of the economic alignment between platform, creators, and users. Everyone benefits when we're building together.
