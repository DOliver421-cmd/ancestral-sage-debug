# DELON'S DIRECTOR BRIEF — Your Complete Role & Playbook

**For:** Delon Oliver (NAM Oshun), Executive Director, WAI-Institute & M.O.R.E. Help Center  
**Version:** 1.0 — PRODUCTION READY  
**Date:** 2026-05-22

---

## YOUR CORE ROLE

You are the **Founder, Owner, and Final Decision Authority** for two organizations:

1. **WAI-Institute** — 12-module electrical apprenticeship training (Camper-to-Classroom)
2. **M.O.R.E. Help Center** — Community guidance (financial, legal, health, government programs)

**Strategic Leadership:**
- Define mission and values
- Decide what we build next
- Approve major spending
- Make partnership decisions
- Represent organization publicly

**You Do NOT:**
- Code (Claude does that)
- Teach (instructors do that)
- Process refunds (staff does that)
- Fix servers (Claude does that)

---

## YOUR DIRECTOR SYSTEM — 8 Tools + 12 Personas

You have AI support with **8 integrated tools** and **12 specialist personas**.

### The 8 Tools

**web_search** — Find current info (market trends, competitor pricing, news)
- Use: "Who are my top 3 competitors in electrical apprenticeship?"
- Use: "What's the average electrician apprentice salary in [state]?"

**fetch_url** — Read any webpage or document (contract, proposal, article)
- Use: "Review this partnership proposal: [URL]"

**send_email** — Compose and queue emails (requires GMAIL_USER + GMAIL_APP_PASSWORD in Railway)
- Use: "Send thank you email to [person] for [reason]"

**get_incident_register** — View all system errors (database, server, API crashes)
- Use: "What errors happened in the last 24 hours?"

**create_incident** — Log and alert on problems
- Use: "Log incident: student payment failed, escalate to Delon"

**get_system_health** — Server status, database health, memory usage
- Use: "Is the system healthy enough for launch tomorrow?"

**set_mode** — Adjust Director's risk tolerance
- Use: "Set mode to 'conservative'" (for major decisions)

**read_file** — Upload and analyze documents
- Use: "Review this audit report" [upload PDF]

### The 12 Personas

Each is an AI specialist coordinated by Director:

| # | Persona | Role | Ask Them |
|---|---------|------|----------|
| 1 | **Scholar** | Research expert | Deep analysis, academic context |
| 2 | **Sage** | Wisdom keeper | Ethics, history, big-picture implications |
| 3 | **PRT Enforcer** | Guardrails monitor | "Does this violate our principles?" |
| 4 | **Executive Oversight** | Risk manager | Financial, legal, operational risks |
| 5 | **Revenue Director** | Growth strategist | Pricing, new income, scaling |
| 6 | **Product Designer** | Learning experience | Course design, UX, outcomes |
| 7 | **Strategic Navigator** | Market analyst | Competitors, timing, positioning |
| 8 | **Apprentice** | Learner voice | "What's hard for students?" |
| 9 | **Oliver Guardian** | M.O.R.E. moderator | Community safety, content quality |
| 10 | **Cultural Scout** | Trend watcher | Emerging needs, community voice |
| 11 | **The 9 Synthesis** | Integrated wisdom | Complex decisions (all perspectives) |
| 12 | **Orchestrator** | Coordinator | "How do we balance everything?" |

---

## YOUR DAILY RHYTHM

### MORNING (10 min)
```
Ask Director: "Morning briefing. 
Overnight status? Any incidents? Anything I need to decide?"
```

Get back:
- System health ✓/✗
- New feedback/testimonials
- Failed operations (payment, email, etc.)
- Pending decisions

### MID-MORNING (Decision Time)
Based on your priorities, pick one:

```
"Shall we launch creator courses next month or Q4?"
→ Ask Revenue Director (revenue timing)
→ Ask Product Designer (readiness)
→ Ask Strategic Navigator (market timing)
→ Ask The 9 (integrated view)
→ You decide.
```

```
"What should our 13th module be?"
→ Ask Scholar (what skills missing?)
→ Ask Apprentice (what do students want?)
→ Ask Cultural Scout (community needs?)
→ You decide.
```

```
"Can we raise student subscription from $10 to $15?"
→ Ask Revenue Director (price elasticity)
→ Ask Product Designer (value delivered)
→ Ask Sage (mission integrity)
→ You decide.
```

### AFTERNOON (Handle Escalations)
- Unhappy student → Director can draft thoughtful response
- Partnership inquiry → Director researches + summarizes
- Feature request → Director gathers requirements
- You review, approve, or redirect

### WEEKLY (1 hour Strategy)
```
"What are our priorities for next 30 days?
What risks should we be tracking?
Are we on track for revenue?"

Director summarizes + suggests adjustments.
```

---

## CRITICAL DECISIONS (You Decide, Director Advises)

These always come to you:

1. **New Programs** — Does it fit mission?
2. **Major Hires** — Who joins team?
3. **Pricing/Revenue** — What do we charge?
4. **Partnerships** — Who do we work with?
5. **Spending >$10K** — Capital decisions?
6. **Mission Changes** — Still true to purpose?
7. **Escalations** — Unhappy customers, legal, PR

**Process:**
- Ask relevant personas for analysis
- Get their perspectives
- You make final call
- Director executes or escalates to Claude

---

## THE STAFF MEETING ENDPOINT

For major strategic decisions, use:

```
POST /api/exec/staff-meeting
{
  "brief": "Should we launch a healthcare finance module?",
  "participants": [],  // all 12 personas
  "priority": "high"   // invokes The 9 synthesis
}
```

**Response:**
- Each persona gives 5-7 key points
- If high priority, The 9 synthesizes integrated recommendation
- Results emailed + logged

**Use:** Quarterly planning, major pivots, complex decisions

---

## YOUR REVENUE AT A GLANCE

**Current (Deployed):**
- Student subscriptions: BASIC $9.99/mo, ADVANCED $29.99/mo, PREMIUM $99.99/mo
- Creator courses: 70% creator, 30% platform take
- Payment processing: Stripe test mode (needs live testing)

**Not Yet Monetized:**
- Certification exams ($49/attempt)
- Corporate training ($5K/cohort)
- Premium support ($99/mo)
- Affiliate partnerships
- Grant funding

**Your job:** Decide what to launch when. Director can model scenarios.

---

## FIRST MONTH CHECKLIST

**Week 1: System Confidence**
- [ ] Test login (all 3 accounts or recovered 1)
- [ ] Ask Director morning question
- [ ] Verify staff can escalate to you
- [ ] Check system health

**Week 2: Strategy Clarity**
- [ ] Ask Scholar: "State of electrical apprenticeship in [region]?"
- [ ] Ask Strategic Navigator: "Top 3 competitors + our differentiation?"
- [ ] Ask Revenue Director: "Realistic Y1 revenue projection?"
- [ ] Ask Sage: "Is our mission still relevant?"

**Week 3: Community Listening**
- [ ] Ask Oliver Guardian: "What's M.O.R.E. community saying?"
- [ ] Ask Cultural Scout: "What trends should we watch?"
- [ ] Ask Apprentice: "What's hardest for learners?"
- [ ] Summarize → quarterly priorities

**Week 4: Execution Planning**
- [ ] Ask Revenue Director: "What to launch first?"
- [ ] Ask Product Designer: "Next course ready?"
- [ ] Ask Executive Oversight: "Financial risks?"
- [ ] Present to team → confirm alignment

---

## COMMON SCENARIOS

### Student Wants Refund
```
Support staff process (7-day unconditional, then case-by-case).
If escalated to you:
→ Ask Executive Oversight: "Risk of approving?"
→ Ask Sage: "What honors their situation?"
→ Decide.
```

### Partnership Inquiry
```
→ Ask Strategic Navigator: "Fit our ecosystem?"
→ Ask Revenue Director: "Financial upside?"
→ Ask PRT Enforcer: "Mission-aligned?"
→ Ask Orchestrator: "Do this now or later?"
→ Decide.
```

### Course Not Working
```
→ Ask Apprentice: "Why are students struggling?"
→ Ask Product Designer: "How redesign?"
→ Ask Revenue Director: "Cost vs benefit?"
→ Decide.
```

### Raise Pricing?
```
→ Ask Revenue Director: "Market analysis? Elasticity?"
→ Ask Product Designer: "Impact on acquisition?"
→ Ask Sage: "Ethical for our community?"
→ Ask The 9: "Integrated view?"
→ Decide.
```

---

## ESCALATION PLAYBOOK

**If Director is slow:**
1. Check system health
2. Try simpler question
3. Tell Claude (mention issue)
4. Fallback: call team lead (don't wait)

**If you disagree with Director:**
You win. Ask different persona. Ask humans. Your call.

**If you need something beyond these tools:**
Tell Claude. Claude will expand the system.

---

## WHAT YOU HAVE ACCESS TO

✅ AI analysis & research  
✅ System health monitoring  
✅ Email composition + queue  
✅ Document reading  
✅ Multi-persona perspectives  
✅ Decision synthesis  
✅ Financial modeling  

❌ Live student data (privacy-protected)  
❌ Code changes (Claude does that)  
❌ Spending authority (final approval still you)  
❌ Personnel decisions (you hire/fire)  

---

## QUICK START — TRY NOW

```
1. Ask Director: "Morning briefing. Status?"

2. Ask The 9: "Should we launch creator courses next month?"

3. Ask Revenue Director: "What's our biggest revenue opportunity?"

4. Ask Scholar: "What's happening in electrical apprenticeship industry?"

5. Ask Orchestrator: "Given all these perspectives, what's our next move?"
```

These are good prompts. They'll get you good answers.

---

## YOUR SUCCESS METRIC

**You win when:**
1. Students complete courses → get better jobs (impact)
2. Community trusts WAI → refers friends (growth)
3. Revenue covers costs + enables reinvestment (sustainability)
4. Instructors feel supported (retention)
5. You can sleep knowing WAI runs well (peace of mind)

Director helps on all 5. But you're the engine.

---

## REMEMBER

This system was built for you to think better and faster.

But you're the wise one. Trust yourself. When something feels off, it is.

Go serve your community. That's your real job.

---

*Last updated: 2026-05-22*  
*Questions? Ask Claude.*
