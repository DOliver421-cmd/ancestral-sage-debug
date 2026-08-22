# NAVIGATION LABEL AUDIT

**Date:** August 22, 2026

---

## METHODOLOGY

Every nav label was evaluated against: "Can a new user understand what this does within 2 seconds?"

**RATINGS:**
- ✅ CLEAR — self-explanatory
- ⚠️ AMBIGUOUS — needs context
- ❌ CONFUSING — internal jargon or unclear
- 🔄 DUPLICATE — same capability appears twice

---

## SECTION: HOME

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Home / Landing | `/` | ✅ | — |
| Dashboard | `/dashboard` | ✅ | — |
| My Profile | `/profile` | ✅ | — |
| Settings | `/settings` | ✅ | — |

---

## SECTION: NAM

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| AI Tutor | `/ai` | ⚠️ | What is "NAM"? What does "Tutor" teach? |
| Personal Helper | `/helper` | ⚠️ | How is this different from AI Tutor? |
| Admin Assistant | `/assistant` | ⚠️ | Sounds like a tool for admins, not a persona |
| Orchestrator | `/orchestrator` | ❌ | Internal jargon — user doesn't know what this does |
| Site Guide | `/site-guide` | ⚠️ | Sounds like documentation, not a persona |
| Council (Sage) | `/council` | ⚠️ | "Council" suggests many, "Sage" is one — confusing |
| Jamil | `/jamil` | ⚠️ | Name means nothing to new users |
| My AI (BYOK) | `/byok` | ❌ | "BYOK" is developer jargon |

**RECOMMENDATION:** Rename to functional descriptions:
- "AI Tutor" → "AI Assistant" or "Chat with NAM"
- "Orchestrator" → "Team Coordinator" or "AI Workflows"
- "Jamil" → "Jamil — AI Director" or "Director AI"
- "My AI (BYOK)" → "My AI Keys" or "Connect Your AI"

---

## SECTION: CREATE

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Creator Studio | `/studio` | ✅ | — |
| Course Manager | `/creator/courses` | ✅ | — |
| Ghost Producer | `/ghost-producer` | ⚠️ | Music industry term — not all users know it |
| Social Blast | `/social/publish` | ⚠️ | "Blast" is informal — unclear what it does |
| Creator Lounge | `/creator-lounge` | ⚠️ | What happens here? Chat? Resources? |
| My Earnings | `/creator/earnings` | ✅ | — |
| Payout Dashboard | `/creator/payouts` | ✅ | — |

---

## SECTION: LEARN

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Modules | `/modules` | ⚠️ | "Modules" of what? Too generic |
| Learning Path | `/adaptive` | ⚠️ | Route says "adaptive", label says "Learning Path" |
| Competencies | `/competencies` | ⚠️ | Corporate/HR jargon |
| Workforce Labs | `/labs` | ⚠️ | "Labs" is ambiguous — experiments? Simulations? |
| Lab Simulations | `/lab-simulations` | ⚠️ | How is this different from Labs? |
| Compliance | `/compliance` | ✅ | — |
| Credentials | `/credentials` | ✅ | — |
| Certificates | `/certificates` | ✅ | — |
| Portfolio | `/portfolio` | ✅ | — |

**DUPLICATE:** "Workforce Labs" and "Lab Simulations" are very similar. Consider merging.

---

## SECTION: COMMUNITY

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Members' Palace | `/palace` | ⚠️ | "Palace" is a brand name — what happens here? |
| XP Leaderboard | `/leaderboard` | ✅ | — |
| Community Chat | `/more/chat` | ⚠️ | Route is `/more/chat` but label says "Community Chat" |
| Legal Tools | `/more/litigation` | ❌ | "Litigation" sounds adversarial — this should be helpful |
| Report Incident | `/incidents` | ⚠️ | Sounds like security reporting, not general |
| Vonns Saga | `/vonns-saga` | ⚠️ | Brand name — no context for new users |
| Ascension Protocols | `/ascension-protocols` | ❌ | Internal brand name — completely opaque |

---

## SECTION: MARKETPLACE

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Media Store | `/store` | ✅ | — |
| Plans & Pricing | `/plans` | ✅ | — |
| Membership | `/subscribe` | ✅ | — |
| Donate | `/donate` | ✅ | — |
| Payment History | `/payment/history` | ✅ | — |
| Partnerships | `/partnership` | ⚠️ | What kind of partnerships? |

---

## SECTION: SANCTUARY

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Sanctuary | `/sanctuary` | ⚠️ | What is Sanctuary? Healing? Journaling? |
| Knowledge Base | `/knowledge-base` | ✅ | — |

---

## SECTION: MUSIC

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Band on a Page | `/band` | ⚠️ | Clever name but unclear function |
| Playlist Manager | `/playlist/dashboard` | ✅ | — |

---

## SECTION: GAMES

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Virtual Arcade | `/arcade` | ✅ | — |
| M.O.R.E. Pantheon | `/trash` | ❌ | Route is `/trash` — extremely confusing |

---

## SECTION: AGENT WELLNESS

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Agent Registry | `/aawab` | ⚠️ | "AAWAB" is opaque acronym |
| Certification | `/aawab/chamber` | ⚠️ | "Chamber" is internal terminology |

---

## SECTION: DIRECTOR (admin only)

| Label | Route | Rating | Issue |
|-------|-------|--------|-------|
| Admin Overview | `/admin` | ✅ | — |
| IAM Console | `/admin/iam` | ⚠️ | "IAM" is developer jargon |
| Business Office | `/admin/office` | ✅ | — |
| Command Center | `/admin/command` | ⚠️ | Military/military jargon |
| System Health | `/admin/health` | ✅ | — |
| Payments | `/admin/payments` | ✅ | — |
| Billing | `/admin/billing` | ✅ | — |
| Prices | `/admin/prices` | ✅ | — |
| Revenue | `/revenue` | ✅ | — |
| Analytics | `/admin/analytics` | ✅ | — |
| Audit Log | `/admin/audit` | ✅ | — |
| Moderation | `/admin/moderation` | ✅ | — |
| Sage Audit | `/admin/sage-audit` | ⚠️ | "Sage" context unclear |
| Sites & Inventory | `/admin/tools` | ⚠️ | "Tools" is vague |
| AI Team Bridge | `/admin/bridge` | ❌ | Internal jargon |
| Provider Gateway | `/admin/providers` | ⚠️ | "Gateway" is technical |
| Site Report | `/admin/exec-report` | ✅ | — |
| The Arena | `/arena` | ⚠️ | "Arena" sounds like a game |

---

## TOP ISSUES

1. **7 confusing labels** need renaming (Orchestrator, BYOK, Ascension Protocols, etc.)
2. **3 duplicates** (Labs vs Lab Simulations, Community Chat vs chat, etc.)
3. **5 ambiguous labels** need functional descriptions
4. **Route mismatches** where label doesn't match route name
5. **Brand names without context** (Vonns Saga, AAWAB, Palace)
