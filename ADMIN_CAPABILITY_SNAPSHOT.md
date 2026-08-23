# WAI Institute — Platform Capability Snapshot
*One-page spec sheet for admin staff. Source of truth: live navigation, plans catalog, role registry, and platform code. For support questions, see the M.O.R.E. Help Center.*

---

## 1. Core Functions

| Area | What it is |
|---|---|
| **M.O.R.E. Help Center** | The community + support hub: help articles, knowledge base, community chat, and human support. First stop for user questions. |
| **WAI Institute** | The training platform: courses, modules, labs, competencies, compliance training, credentials, certificates, portfolios. |
| **Our Legacy, Our Future** | The flagship book + campaign: *Building Thriving Black Communities with AI* — a practical manual (16 chapters + AI addendum + speculation section + appendices) for community-aligned AI across food, housing, education, economy, culture, worship, and governance. AI as partner, never replacement. |
| **Campaign pillars (from the book)** | 7 capability areas promoted to the community — AI-Powered Agriculture · AI-Enhanced Construction · AI-Enhanced Education · AI-Driven Businesses · AI Music Studio/Creativity · AI-Powered Worship & Outreach · AI Market Logistics — plus the book itself as the 8th pillar. |

Everything sits on one account: one login, one profile, one payment history.

---

## 2. User Roles
Real roles (source: `backend/roles.py`), lowest to highest authority:

| Role | What they can do |
|---|---|
| **student** | Default account after registration. Full member experience per their tier. |
| **trial_pass** | Student with priority access (e.g., paid trial). |
| **instructor** | Manages rosters, approves labs, takes attendance. |
| **support_staff** | Site support: moderation + audit access. May volunteer shared AI keys (never exposed). |
| **oversight** | Adds agent-wellness/registry capabilities. |
| **admin** | "Director" console: IAM, payments/billing, analytics, audit, moderation, Feature Control Center. |
| **executive_admin** | Executive-only systems: Command Center, The Arena. |

**Customer tiers are separate from roles.** Tiers (below) control *what you can use*; roles control *what you can administer*. A paying customer never gains staff powers; a staff member doesn't automatically get paid tiers.

---

## 3. Content Types

- **Spoken word / music** — Band on a Page, Playlist Manager, media store, creator studio
- **Courses & modules** — curriculum, learning paths, workforce labs, simulations
- **Resources** — knowledge base, Knowledge Finder (search), handbooks, site guide
- **Live & community** — community chat, members' palace, events/meetups via community tools
- **Games & engagement** — virtual arcade, daily puzzle, XP leaderboard, M.O.R.E. Pantheon

---

## 4. Revenue Systems

| Source | How it works |
|---|---|
| **Subscriptions** | Member $9 · Plus $15 · Pro $29 · Patron $59 /mo. Paid tiers stack (higher includes lower). Processed by Lemon Squeezy. |
| **$3 All-Access Trial** | One-time $3: everything through Pro for 3 days · 33 min · 33 sec, then auto-reverts. |
| **Book — *Our Legacy, Our Future*** | One-time **$89** digital purchase of the flagship manual. No tier grant — it's a product, not a membership. |
| **$3 BYOK Unlock** | One-time $3: lets a user connect their **own** AI key (free keys exist) so AI runs on their resources, not the platform's. |
| **Donations** | One-time giving via the Donate page. |
| **Creator payouts** | Course publishing + payouts (90% creator share) at Plus and above. |
| **B2B / partnerships** | Course licensing, team operations, partnership program, provider gateway. |

**Refund rule:** refunds are issued as **site credit** unless the issue was the platform's fault.

---

## 5. Community Tools

- Forums-style chat + members' palace (gated to members)
- Q&A via the Helper/Knowledge Finder and help center
- **Crisis resources:** 211 (life help, free, confidential 24/7) and 988 (mental health) built into the knowledge base
- Incident reporting, moderation queue, XP leaderboard, elder council, legal tools
- **Knowledge Finder** — free, zero-cost search across the platform's own content (no AI, no account needed)

---

## 6. Tech Stack (basics)

- **Frontend:** React (single-page app)
- **Backend:** Python / FastAPI, JWT-secured API
- **Database:** MongoDB (primary + backup)
- **Payments:** Lemon Squeezy (subscriptions + one-time products)
- **AI:** Central gateway with multiple providers (Groq, OpenAI, Together, Cohere, Mistral); user keys (BYOK) or staff/exec platform keys
- **Hosting:** Docker on Railway; static assets served from the backend

---

## 7. Accessibility — who gets in

| Audience | What they get |
|---|---|
| **Anonymous visitor** | Explore courses/creators/store/community, help center, Knowledge Finder. No dashboard, no AI. |
| **Free registered user** | Dashboard, Learn, Community, Music, Games, Sanctuary, profile/settings, Knowledge Finder. |
| **BYOK user** ($3 unlock) | Live AI on **their own key**; more capacity = upgrade their key. |
| **Paid tiers (member → patron)** | Everything below, plus that tier's bundle (creator tools, labs, credentials, etc.). |
| **Staff / admin / exec** | Role-based consoles (Director, Instructor, Site Support, Executive). |

**AI funding rule:** the platform funds AI for admin/executive staff only. Customers' AI always runs on their own BYOK key. No key = Knowledge Finder + human support — never a fake AI answer.

---

## 8. Limitations (be honest)

- ❌ **No platform-funded AI for customers.** BYOK is the only customer AI path; without a key, users get Knowledge Finder + the help center.
- ❌ **No customer access to internal systems.** The Arena, Command Center, admin consoles, and internal personas (e.g., Jamil, Orchestrator) are staff/exec-only — never customer features, at any tier.
- ❌ **Not an omniscient chatbot.** Knowledge Finder answers from curated, growing content (currently ~220 indexed documents). It is a search tool, not a replacement for human judgment.
- ❌ **No offline mode, no native mobile app.** The site is web-only; a stable connection is required.
- ❌ **Payments depend on a third-party processor** (Lemon Squeezy). Checkout and webhooks are live-verified via that provider; refunds are site credit per policy.
- ❌ **Feature availability can be toggled centrally** (Feature Control Center) — what an admin enables/disables changes the site instantly. A feature that's off for a user is off, even if they can navigate to it.
- ❌ **AI answers are not legal, medical, or financial advice.** Crisis entries point users to 211/988 and real humans.

---

*Questions? Escalate to the admin console (Director → System Health, Audit Log) or the M.O.R.E. Help Center. Updated by the Archivist per Director assignment.*
