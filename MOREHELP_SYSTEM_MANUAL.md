# MoreHelp Center — System Description & User Manual

**Audience:** real people who will use the site — learners, members, creators,
community participants, staff, and executives.
**Purpose:** explain what MoreHelp Center is, who each role and tier is, what
every feature does, who can access and control what, and how the AI personas
work.
**Document status:** describes the system as built on `main` (2026-09-03).
Live availability of some features depends on deployment configuration — see
§9 and `PUBLIC_READINESS_REPORT.md` for dated, verified status.

---

## 1. What MoreHelp Center is

MoreHelp Center (M.O.R.E. — Michael Oliver Resource Exchange) is a learning,
community, and creator platform. It helps people move from confusion to action
through:

- **Practical knowledge** — a public curriculum catalog, course library,
  workforce labs, competencies, credentials, and certificates.
- **Responsible technology** — AI assistants (tutor, guides, and personas) that
  work under clear human authority, never instead of it.
- **Creative work** — a creator studio with writing, music, publishing, and
  product tools.
- **Community-centered opportunity** — membership, community spaces, and
  creator earnings.

### How the platform is organized

The site has one account system with two independent ideas that work together:

- **Role** — *who you are* on the platform (authority, responsibility, and
  what you may operate). Roles rank from public visitor to executive.
- **Tier** — *what you have paid for or been granted* (entitlement to content
  and features). Tiers rank from Free to Executive.

A role and a tier are **not the same thing**. A staff member has a role that
grants operational authority regardless of tier; a customer has a tier that
grants product entitlements regardless of role. The server checks both, plus a
feature's own settings, before anything unlocks — *access is a deliberate
configuration, not a side effect of code existing.*

Six checks decide whether you can use something (simplified from the Feature
Control policy):

1. **Visible** — do you see it exists?
2. **Discoverable** — can you find it (navigation grouping)?
3. **Authorized** — does your **role** permit it?
4. **Entitled** — does your **tier** permit it?
5. **Funded** — who pays for the resources the feature consumes (your own AI
   key, the platform, or nobody)?
6. **Usable** — is it enabled and within budget?

You can see a feature without having access. You can be authorized without the
platform funding the AI behind it. Seeing ≠ access, and access ≠ free compute.

---

## 2. Roles (who you are)

| Rank | Role | Who it is | What they can do | How it is assigned |
|---|---|---|---|---|
| 0 | **Public (visitor)** | Someone not signed in | Browse public content: landing, curriculum catalog, help/resources, personas directory, plans and products. No account features, no AI beyond the built-in knowledge base. | No sign-in. |
| 1 | **Student** | A registered member | Everything public plus their own account: profile, curriculum browsing, AI chat with their own key (BYOK), community read, participation in free features. The default role for everyone who registers. | Automatic on registration. |
| 2 | **Trial Pass** | Someone on a trial / priority pass | Student access plus the trial window's granted tier (a trial can raise your effective tier for a limited time). | Granted by promotion or by the $3 trial product (§3). |
| 3 | **Instructor** | A teacher / moderator / course author | Teaches and leads: may access course and track content regardless of paid tier, moderate their areas, and create course content they are granted. | Appointed by admin/executive. |
| 4 | **Support Staff** | Site support operations | Helps members: support tools, account help, and (with the team's key pool) approved AI assistance. Staff roles get free BYOK entitlement. | Appointed by admin/executive. |
| 5 | **Oversight** | Governance / oversight | Reviews incidents and governance matters, and (per role grants) approves content and community actions. | Appointed by executive. |
| 6 | **Admin** | Platform administrator | Operates the platform: user administration, feature controls, system health, personas console, financial administration — all with platform-funded AI. Admins bypass tier gates (staff, not customers). | Appointed by executive. |
| 7 | **Executive** (executive_admin) | Owner / executive leadership | Everything an admin can do, plus executive-only controls: Command Center, executive business office, persona priority, restore-points and rollback, and the most sensitive toggles. | Owner-designated seats only. |

Legacy labels from early builds (creator, mentor, moderator, steward, elder,
guest, priority_member) are normalized to this ladder automatically.

**Who controls what (roles):**

- **Executives** control the platform: roles, tiers, feature toggles, AI
  personas, payments configuration, and the audit trail. Only the executive
  role can change executive-only settings or use rollback.
- **Admins** operate day-to-day: manage users, review content/incidents, run
  the Feature Control Center, and use platform-funded AI. Admins cannot change
  executive-only restrictions.
- **Instructors / Support / Oversight** lead and serve: teach, moderate, and
  support. They never control platform policy.
- **Members and customers** control their own content: profile, projects,
  products, earnings, community contributions, and their own AI keys. They
  never control platform policy, and no customer purchase grants staff
  authority.

---

## 3. Tiers (what you have access to)

| Tier | What it means | Retail plan (monthly) |
|---|---|---|
| **Free** | Registered account, curriculum catalog and directory, community read, AI chat powered by **your own key**, knowledge-base answers without a key. | $0 |
| **Member** | Everything in Free plus community participation and AI-assisted publishing (Social Blast). | $9/mo |
| **Plus** | Everything in Member plus the course library, learning tracks, Creator Studio premium chambers, Ghost Producer, publishing toolkit, Band on a Page, creator earnings and payouts, Council (Sage) AI. | $15/mo |
| **Pro** | Everything in Plus plus deeper creator/artist tooling (e.g., artist management features). | $29/mo |
| **Patron** | Everything in Pro plus patron-tier tools (e.g., mass-posting capabilities). | $59/mo |
| **Executive** | Platform seat for owner/executive staff — never sold through customer checkout. | Staff only |

Two notes:

- **Platinum** exists inside the tier ladder but is not currently sold as a
  retail plan; it is reserved/legacy until an executive plan adopts it.
- **The $3 trial** grants a short window of **Pro-tier access** (3 days), then
  reverts to your previous tier. It is an entry point, not a permanent tier.

**Tier changes are automatic:** when you complete a purchase, the payment
webhook upgrades your `feature_tier`. Admins can override a tier from the Exec
panel. Staff roles (admin/executive) bypass tier gates entirely — they are
operators, not paying customers. Instructors get course/track access
regardless of tier because they teach.

**The single most important funding rule (owner policy):** customers never
receive platform-funded AI at any tier. Customers use **their own AI key
(BYOK)**; without a key, AI surfaces answer from the built-in knowledge base.
Only admin/executive staff receive platform-funded AI. This is enforced by the
AI gateway *before* any provider is called — a non-staff caller without a
BYOK key gets the knowledge-base answer, never platform tokens.

---

## 4. Feature catalog — by area

Each row: **what it is** and **who can use it**. Tiers are minimums per the
current authorization matrix (`FEATURE_MIN_TIER`) and the feature registry;
see §8 for operator notes and §9 for live status.

### Learning

| Feature | What it is | Access |
|---|---|---|
| **Curriculum catalog** (`/modules`) | The public directory of every module — always visible, never hidden behind a paywall. | Public (no sign-in needed) |
| **Module content / Course library** | Full module/course content, progress tracking, labs, and credentials. | **Plus** and above (instructors bypass) |
| **Learning Path / Tracks** (`learn.adaptive`) | Personalized adaptive path through the curriculum. | **Plus** and above |
| **Workforce Labs, simulations, compliance** | Hands-on practice, sims, and compliance quizzes. | **Plus** and above (registry default: Free+) |
| **Competencies, Credentials, Certificates, Portfolio** | Track mastery, earn credentials/certificates, and present your work. | Registry default: Free+; content-bearing issuance follows the course/credential contract (Plus) |

*Catalog rows list in the public directory even when a visitor has no tier;
opening a module asks for the required tier.*

### AI (see §6 for the persona section)

| Feature | What it is | Access |
|---|---|---|
| **AI Tutor** (`/ai`, AI chat) | Guided chat with selectable AI voices for learning (Master Electrician, Scripture Mentor, Explain for a Trainee, Quiz Generator, NEC Lookup, Blueprint Reader, Ancestral Sage, Conspiracy Brother). | Registered accounts; AI funded by BYOK or staff (see §3) |
| **Hybrid NAM** (`/nam`) | Personal AI leadership assistant — identity, memory, intentions, reflections, leadership ledger. | Registered accounts (AI chat); NAM write surfaces require staff roles |
| **Personal Helper** (`/helper`) | Everyday-task AI assistant. | Registered accounts; anonymous visitors get knowledge-base answers only |
| **Site Guide** | Navigation and how-to help. | Registered accounts |
| **Council / Ancestral Sage** (`/council`) | Guided wisdom/reflection persona with session parameters and consent controls. | **Plus** and above |
| **My AI Keys (BYOK)** (`/byok`) | Connect your own AI provider key so your AI features run on your account's resources. | All registered accounts |

### Community

| Feature | What it is | Access |
|---|---|---|
| **M.O.R.E. posts & needs board** | Community posts and needs. | Posting/participation: **Member**+ (community area visible to all) |
| **Members' Palace, XP Leaderboard, Community Chat** | Community spaces and engagement. | Registered accounts (registry: Free+) |
| **Legal Tools, Report Incident** | Legal help content and incident reporting. | Registered accounts |
| **Vonns Saga, Ascension Protocols** | Community lore/engagement surfaces. | Registered accounts |

### Creator economy (Create ecosystem)

| Feature | What it is | Access |
|---|---|---|
| **Creator Studio** (`/studio`) | Content creation workbench (chambers: writing, music/Sound Lab, visual, script, publishing gate, and more). The studio door is open; premium chambers and AI generators carry their own tier. | Logged-in accounts; premium chambers **Plus**+; Sovereign (executive-grade) is exec-restricted |
| **Ghost Producer** | AI-assisted content production attached to your project deliverables. | **Plus** and above |
| **Course Manager** | Create and manage your own courses. | **Plus** and above |
| **Social Blast** | AI-assisted publishing/social tooling. | **Member** and above |
| **Creator Lounge** | Creator community space. | **Member** and above |
| **Band on a Page / Playlist Manager** | Music pages and playlist publishing. | **Plus** and above |
| **My Earnings / Payout Dashboard** | Track sales and request payouts. | **Plus** and above |
| **Artist management / Mass posting** | Deeper creator automation. | Artist management **Pro**+; mass posting **Patron**+ |
| **My Projects** (`/my-projects`) | Your AI-team project lane: list, deliverables, approvals, archive. | **Member** and above |

### Marketplace & commerce

| Feature | What it is | Access |
|---|---|---|
| **Plans & Pricing / Membership / Subscribe** | Buy your tier (monthly or annual). | Public |
| **Media Store** | Buy merchandise and products. | Public (checkout) |
| **Donate** | Support the mission. | Public |
| **Payment History / Partnerships** | Your transactions and partnership status. | Signed-in accounts |

### Wellness & entertainment

| Feature | What it is | Access |
|---|---|---|
| **Sanctuary** | Reflection/wellness experience. | **Plus** and above |
| **Knowledge Base** | Reference articles. | Public |
| **Virtual Arcade / M.O.R.E. Pantheon** | Games and engagement. | Registered accounts (public scores) |
| **Arena** | Executive reasoning infrastructure — **not** a customer feature. | Executive only |

### Staff-only (never customer features)

| Feature | What it is | Who |
|---|---|---|
| **Admin Dashboard, System Health, IAM Console** | Users, roles, tiers, health. | Admin, Executive |
| **Feature Control Center** | The 9-field feature registry + toggles (see §5). | Admin, Executive |
| **Command Center** | Highest-sensitivity operations. | Executive only |
| **Personas Console** | Create/edit/prioritize/disable AI personas. | Admin, Executive |
| **Audit trail, restore-points & rollback** | Verify and undo platform state. | Admin, Executive (sensitive: Executive) |
| **Arena** | Proprietary executive reasoning. | Executive only |

---

## 5. Access & control matrix (who can do what)

| Can do this… | Visitor | Customer (any tier) | Instructor | Support / Oversight | Admin | Executive |
|---|---|---|---|---|---|---|
| Browse public content & catalogs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Own account, profile, BYOK keys | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| Learn (modules/courses per tier) | catalog only | ✓ (per tier) | ✓ (bypass) | per tier | ✓ | ✓ |
| Chat AI with **own** key | – | ✓ | ✓ (free BYOK) | ✓ (free BYOK) | ✓ | ✓ |
| **Platform-funded** AI | – | **never** | – | – | ✓ | ✓ |
| Post & participate in community | – | ✓ (Member+) | ✓ | ✓ | ✓ | ✓ |
| Create & publish (studio/courses/products) | – | ✓ (per tier) | ✓ | – | ✓ | ✓ |
| Earn & request payouts | – | ✓ (Plus+) | – | – | ✓ | ✓ |
| Moderate / support members | – | – | ✓ (area) | ✓ | ✓ | ✓ |
| Manage users, roles, tiers | – | – | – | – | ✓ | ✓ |
| Toggle features / FCC | – | – | – | – | ✓ | ✓ |
| Manage AI personas | – | – | – | – | ✓ | ✓ |
| Executive-only toggles, rollback | – | – | – | – | – | ✓ |
| View encrypted audit trail | – | – | – | – | ✓ | ✓ (full) |

**Enforcement layers:** the frontend hides what you cannot use (UX only); the
backend is authoritative. The server checks, in order: your session (401 if
absent), your role (403 if not authorized), the feature registry (enabled /
internal-only / roles / tiers), your per-user grants or revocations, and the
minimum-tier matrix. If the server cannot *verify* a policy because its policy
database is unavailable, the request is rejected with a 503 — never silently
allowed.

---

## 6. The AI personas

### What a persona is

A persona is a **defined AI voice and role** — a named assistant with a
specific identity, mission, boundaries, and optional memory — so that talking
to "the Ancestral Sage" is a different, dependable experience from talking to
"the AI Tutor". Personas do not act autonomously on the platform. They answer
questions, draft, explain, and reflect; every consequential platform action
belongs to a human with the right role.

### Where personas appear

- **AI Tutor chat** — mode buttons switch the assistant's voice: Master
  Electrician (tutor), Scripture Mentor, Explain for a Trainee, Quiz
  Generator, NEC Lookup, Blueprint Reader, Ancestral Sage, Conspiracy Brother.
- **Hybrid NAM** — your personal leadership assistant; students and staff
  receive the persona matched to their role by default (students are paired
  with the Assistant Director voice; staff with the Director voice).
- **Council (Ancestral Sage)** — the wisdom/reflection persona with session
  parameters (intensity, safety level, divination mode) and an explicit
  consent step before personalized or deeper sessions.
- **Personal Helper** and **Site Guide** — lighter assistants for tasks and
  navigation.
- **Ghost Producer / Studio AI chambers** — assistants embedded in creation
  tools that produce drafts and deliverables you review and approve.
- **Staff-only personas** (Director, Jamil, Orchestrator, Admin Assistant) —
  internal operational AI for admins/executives. Never customer features.

### Roster at a glance

| Persona / voice | Where | Who can use it |
|---|---|---|
| AI Tutor modes (Master Electrician, Scripture Mentor, Explain, Quiz, NEC, Blueprint, Conspiracy Brother) | `/ai` chat | Registered accounts (BYOK or staff funding) |
| Ancestral Sage (teaching / reading / practice modes) | `/ai` chat + `/council` | **Plus**+ via Council; Tutor mode for registered accounts |
| Hybrid NAM (Assistant Director voice for members) | `/nam` | Registered accounts |
| Personal Helper / Site Guide | `/helper`, site guide | Registered accounts (KB answers anonymous) |
| Director, Jamil, Orchestrator, Admin Assistant | internal AI | Admin / Executive only |
| Arena | internal | Executive only |

### Human authority — the ground rules every persona follows

1. **People lead, AI assists.** Personas explain, advise, draft, and warn —
   they do not make platform decisions, spend money, or change policy.
2. **Unsafe requests are refused with a reason.** If a request is unsafe,
   unethical, or outside the persona's role, the persona says so plainly and
   declines — it never "plays along".
3. **No persona overrides the human executive.** Staff-facing personas are
   required to state that the human executive (owner) holds final authority;
   AI may flag or refuse, never silently act above a human decision-maker.
4. **Personalized sessions require consent.** Deep/personalized Ancestral
   Sage sessions ask for consent first, and default to privacy-protective
   settings.
5. **Integrity is checked.** Persona prompts are hash-verified; if a prompt
   fails its integrity check, the persona falls back to a restricted
   educational mode instead of running an unverified prompt.

### Who funds the AI, and what happens when it cannot run

- **Anonymous visitors:** knowledge-base answers only — never an AI call.
- **Customers (all tiers):** their own BYOK key funds live AI; without a key,
  the AI answers from the knowledge base. The platform never spends on
  customer AI.
- **Staff (admin/executive):** platform-funded AI through the provider
  gateway.
- **If the provider cannot be reached** (no key configured, provider error,
  budget exceeded): the surface returns a **clear, structured failure** —
  never a fake success. This platform fails closed by design.

### Controls you have over personas

- **Every user** can revoke their own AI keys at any time (`/byok`).
- **Admins/executives** can, per user: grant or revoke a specific persona,
  revoke the whole AI suite, disable a platform feature, and audit the change.
- **Admins/executives** operate the personas console: activate/deactivate
  personas, edit metadata, reorder execution priority, and review the audit
  log of persona changes. Customers cannot modify personas — they choose among
  the ones offered.

---

## 7. Practical day-to-day questions

**What does "401" mean?** You are not signed in (or your session expired).
Sign in and try again.

**What does "403" mean?** Your role or a per-user restriction does not permit
the action. If you believe this is an error, contact support.

**"This feature requires the Plus plan or higher."** Your tier is below the
feature's minimum. Follow the upgrade button to checkout; entitlements apply
automatically after purchase.

**AI says it is unavailable / returns a service error.** An AI provider key is
missing or the provider failed. Add your own key at `/byok`, or wait — the
knowledge base still answers many questions without any key.

**I bought a tier — when does it unlock?** Immediately after the payment
webhook confirms the purchase. If it has not appeared, check Payment History,
then contact support.

**Can a purchase make me an admin?** No. Staff roles are appointed by the
executive team only. No customer entitlement grants platform control.

**How do I delete my data?** Use the account controls in your profile (delete
account), or contact support.

---

## 8. Operator notes (internal — not marketing copy)

- The **Feature Control Center registry** (9 fields per feature:
  enabled, internal-only, customer-access, cost-bearing, allowed roles,
  allowed tiers, navigation-visible, platform AI, BYOK) is the canonical
  catalog. `BUSINESS_ACCESS_POLICY.md` is the policy; `feature_control.py`
  is its enforcement; the Exec panel writes overrides.
- **Minimum-tier defaults in code** (`FEATURE_MIN_TIER`): profile/ai_chat/
  curriculum/studio = free; posts/publisher_ai/lounge/projects = member;
  courses/tracks/band/publisher/earnings/payouts = plus; sovereign =
  executive. The frontend's `TIER_FOR_FEATURE` mirrors this contract with one
  documented drift: **Studio is free-access in the enforcement matrix while
  the registry default tiers for `create.studio` are Plus+** — premium
  chambers carry the real gates. Executives should confirm and publish the
  intended matrix (DB `authz_matrix` overrides code defaults).
- The AI funding rule (§3) is enforced before any provider call
  (`llm_gateway.py`); anonymous AI endpoints contain no LLM call path.
- Per-feature AI budgets/quotas beyond the global caps are still
  configuration-required; see `BUSINESS_ACCESS_POLICY.md` §12.

## 9. Live availability (verified 2026-09-03)

Per `PUBLIC_READINESS_REPORT.md` Update 2 (verified live against the Railway
target):

- Public catalogs, curriculum listing, arcade games, personas directory, and
  payment products all return live JSON.
- Guarded routes correctly reject anonymous/invalid sessions with 401.
- **AI is fail-closed by design until an AI provider key is configured** —
  `/api/health` reports `ai_api_key_missing`; Sovereign and platform AI return
  structured 503s rather than pretending to succeed.
- **Checkout is blocked until payment-provider keys are set**
  (`publishable_key` empty).
- The full register → pay → entitlement journey has not yet been demonstrated
  on production by a real user; that remains the launch gate.

**Source-of-truth map:** this manual's tables follow `BUSINESS_ACCESS_POLICY.md`
(roles/tiers/AI funding), `backend/roles.py` and
`backend/security/feature_control.py` (enforcement), the FCC registry in
`backend/routers/features.py` (feature catalog), `frontend/src/lib/tiers.js`
and `frontend/src/lib/plans.js` (user-facing ladder and pricing), and the
persona surfaces in `backend/routers/ai.py`, `backend/routers/nam.py`, and
`backend/ai/persona_loader.py`.

---

## 10. Technical appendix — precise API/AI access, budget framework, and BYOK

*This appendix is the exact specification as implemented on `main`
(2026-09-03), read from the source files listed in each section. Where a
documented policy and the code differ, the code is quoted here.*

### 10.1 The Ethical AI Mandate: Bring Your Own Key (BYOK)

*Owner-approved public statement (included verbatim):*

> The Ethical AI Mandate: Bring Your Own Key (BYOK)
>
> This platform operates on a sovereignty principle: we do not profit from
> your data, and we do not subsidize unlimited compute costs, which often
> leads to centralized control.
>
> To ensure grassroots resilience, we require that you fund your own AI chat
> usage. This keeps the system decentralized and ensures your intent remains
> your own.
>
> If you do not have a key, please use the platform's built-in knowledge
> base. Alternatively, you may utilize a free quota provided by the following
> sovereign partners. Paste your personal key below to activate unlimited
> access for this persona stack.
>
> **Groq (Free Tier) | Cerebras (Free Tier) | Google Gemini (Free Tier)**
>
> [ Input Field ]

*Precision note for the public copy above:* "unlimited access" means
*unlimited relative to the platform budget* — the three partner free tiers
are themselves rate-limited (for example Gemini: 15 requests/minute, 1M
token context). A BYOK user's real ceiling is their own provider key's free
quota, not a platform limit and not literally unlimited. The phrase is
retained verbatim per owner approval; support should describe the actual
quota when asked.

### 10.2 Public API / AI access (from `backend/routers/ai.py`, `routers/chat.py`, `ai/llm_gateway.py`)

**Authenticated AI chat surfaces** (`POST /api/ai/chat`, `/api/ai/tool-chat`,
Sage, NAM, etc.) require a valid session. Per-user rate limit:
**20 calls/minute** (`check_rate("ai_chat:{user.id}", max_calls=20,
window_sec=60)`). Before any LLM spend the router runs the FCC persona gate
(`check_persona_access` → 403/503), then Sage consent and exec safety caps.

**Public/anonymous AI endpoints** — all answer from the keyword knowledge
base only; none of them contains an LLM call path:

| Endpoint | In-code rate limit | Guard rails |
|---|---|---|
| `POST /api/ai/helper` | 15/min per IP | 4,000-char cap; prompt-guard scan |
| `POST /api/public/helper/ask` | 15/min per IP | 4,000-char cap; prompt guard |
| `POST /api/helper/ask` | 15/min per IP | 4,000-char cap; prompt guard |
| `POST /api/supervisor/public-chat` | none in code ("rate-limited by upstream proxy") | none in code |

The KB itself (`ai/keyword_kb.py` + `ai/knowledge_finder.py`) matches in
four layers — exact intent → token-overlap → category fallback → warm
generic fallback — sourced from built-in critical entries (crisis/988),
`ai/kb_entries.json` (hot-reloaded), and optional MongoDB `kb_entries`.

**Funding gate inside `call_llm`** (single choke point, in execution order):

1. Global hourly budget check → KB if over (`provider: "kb_fallback"`).
2. **BYOK branch first** for any authenticated user with entitlement + key.
3. Role lookup; then the owner-policy staff gate: only `admin` /
   `executive_admin` may spend platform tokens. Customers at **any** tier,
   anonymous callers, and unverifiable callers → knowledge-base reply.
4. Staff only — provider chain: Groq → Cerebras → SambaNova → Gemini → Grok
   → Cohere → Mistral → Together → OpenRouter → HuggingFace → shared
   support-staff BYOK pool → last-resort OpenAI/DeepSeek (owner free-tier
   keys, `LAST_RESORT_AI_ENABLED=1`) → knowledge base.

Anthropic is **hard-disabled** in the gateway and stays off unless
`ANTHROPIC_IS_ENABLED=true` is set deliberately (owner directive; the file
header says paid providers require explicit consent).

### 10.3 Budget framework (from `ai/llm_gateway.py`, `user_budget.py`)

| Layer | Parameter | Default | Notes |
|---|---|---|---|
| Global hourly platform cap | `HOURLY_TOKEN_CAP` | **200,000 tokens/hour** | In-process counter; over cap → KB for everyone; recorded via `ai_cost_tracker` → `/admin/ai-costs` |
| Per-user daily cap | `USER_DAILY_TOKEN_CAP` | **50,000 tokens/day** | For budgeted roles only; never cuts a user off — KB + honest "resumes at midnight" notice (`provider: "user_budget"`) |
| Tier multiplier (daily cap) | — | free ×1.0 · member ×1.25 · plus ×1.35 · pro ×1.45 · patron ×1.50 | Unknown tier = free (safest) |
| Exempt roles | — | rank ≥ 3 (instructor, support_staff, oversight, admin, executive_admin) | Unlimited; nothing recorded |
| Anonymous | — | IP budget key (`ip:...`) | KB-only anyway under §7A |

**Precision finding:** the per-user daily cap is currently *structurally
dormant* for gateway traffic. The §7A staff gate runs before the daily check,
so only admin/executive calls reach it — and both are exempt (rank ≥ 3 →
unlimited). The multiplier ladder becomes live only if a non-staff caller is
ever granted platform-funded spend. Operative budget today: the **hourly
global cap**; customer spend is bounded by their own BYOK provider quota.
BYOK calls are **never counted** against either platform budget.
Per-feature AI quotas remain CONFIGURATION REQUIRED (executive decision) —
no per-feature limits exist yet.

### 10.4 BYOK function and contract (from `byok.py`, `routers/byok.py`)

**Purpose:** the user funds their own AI calls so the platform spends nothing
for them. BYOK is an *access mechanism, not a permission system*: FCC
authorization (role/tier/internal) is decided first; BYOK only decides who
pays. It never grants access to internal/proprietary features.

**Entitlement — $3 one-time unlock** (`BYOK_PRICE_USD`, env-configurable,
default 3):

- Free by role: `instructor`, `support_staff`, `oversight`, `admin`,
  `executive_admin` (`FREE_BYOK_ROLES`).
- Everyone else: **$3**, requires proof of payment (`byok_paid`) —
  `POST /api/byok/activate` returns **402** without it;
  `POST /api/byok/checkout` returns **501** when payments are unconfigured
  (deliberately locked — no silent free grant).
- Stored as `byok_enabled` + `byok_activated_at` on the user document.

**Approved providers (all free tier, no credit card, OpenAI-compatible):**

| Provider | Model | Free tier |
|---|---|---|
| Groq | `llama-3.3-70b-versatile` | Fast free tier |
| Cerebras | `llama3.3-70b` | Free tier, fast inference |
| Google Gemini | `gemini-2.0-flash` | 15 RPM, 1M context |

Resolution priority: groq → cerebras → gemini.

**Key handling:** stored in `db.user_byok_keys`, Fernet-encrypted via the
shared vault (`PROVIDER_KEY_ENCRYPTION_SECRET`; env → MongoDB-persisted →
ephemeral). Save is **refused (503)** if encryption is unavailable — plaintext
is never silently stored. Keys are never returned to the frontend; only a
masked suffix (`••••abcd`) is shown. `POST /api/byok/key/{provider}/test`
makes a real 1-token verification call and never stores the key.

**Gateway behavior:** with entitlement + key, the user's request routes to
their key first (`provider: "byok:{name}"`); tokens never hit platform
budgets. If their key call fails: staff fall to the platform chain, non-staff
to the knowledge base — never platform tokens.

**Support-staff shared pool:** a `support_staff` key is also shared with the
platform (`_SHARED_BYOK_POOL`), used only when all free providers fail;
every use is audited (`shared_byok.used`, identity + provider, never key
material).

**Endpoints:** `GET /api/byok/status` · `POST /api/byok/activate` ·
`POST /api/byok/checkout` · `POST /api/byok/key` ·
`POST /api/byok/key/{provider}/test` · `DELETE /api/byok/key/{provider}` ·
`GET /api/byok/admin` (admin+).
