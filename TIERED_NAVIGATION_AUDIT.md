# TIERED NAVIGATION AUDIT

**Date:** August 23, 2026
**Status:** AUDIT COMPLETE — sidebar is ROLE-gated today, not TIER-gated (the Phase 18 gap). No sidebar rewrite performed yet (gated on this audit + FCC review).

Source: `frontend/src/components/AppShell.jsx` (all `nl()` nav items) cross-referenced
with the Feature Registry (`backend/routers/features.py`).

## CURRENT STRUCTURE (role-first)

| Section | Gate | Items → feature_id |
|---------|------|--------------------|
| Home | always | Home/Landing (—), Dashboard (—) |
| Account | always | My Profile, Settings |
| NAM | student+ | AI Tutor `nam.chat`, Personal Helper `nam.helper`, Admin Assistant `nam.assistant`*, Site Guide `nam.site_guide`, Council (Sage) `nam.council`, Jamil `nam.jamil`*, My AI (BYOK) `nam.byok` |
| Create | student+ | Creator Studio `create.studio`, Course Manager `create.courses`, Ghost Producer `create.ghost`, Social Blast `create.social`, Creator Lounge `create.lounge`, My Earnings `create.earnings`, Payout Dashboard `create.payouts` |
| Learn | student+ | Modules `learn.modules`, Learning Path `learn.adaptive`, Competencies `learn.competencies`, Workforce Labs `learn.labs`, Lab Simulations `learn.simulations`, Compliance `learn.compliance`, Credentials `learn.credentials`, Certificates `learn.certificates`, Portfolio `learn.portfolio` |
| Community | student+ | Members' Palace `community.palace`, XP Leaderboard `community.leaderboard`, Community Chat `community.chat`, Legal Tools `community.legal`, Report Incident `community.incidents`, Vonns Saga `community.saga`, Ascension Protocols `community.ascension` |
| Marketplace | student+ | Media Store `marketplace.store`, Plans & Pricing `marketplace.plans`, Membership `marketplace.subscribe`, Donate `marketplace.donate`, Payment History `marketplace.payments`, Partnerships `marketplace.partnerships` |
| Sanctuary | student+ | Sanctuary `sanctuary.reflection`*, Knowledge Base `sanctuary.knowledge` |
| Music | student+ | Band on a Page `music.band`, Playlist Manager `music.playlist` |
| Games | student+ | Virtual Arcade `games.arcade`, M.O.R.E. Pantheon `games.pantheon` |
| Agent Wellness | oversight+ | Agent Registry, Certification |
| Director | admin+ | Admin Overview `admin.dashboard`, IAM `admin.iam`, Business Office, Command Center `admin.command`, System Health `admin.health`, Payments, Billing, Prices, Revenue, Analytics, Audit Log, Moderation, Sage Audit, **The Arena `games.arena`**, Feature Control, Sites & Inventory, AI Team Bridge, Provider Gateway, Site Report |
| Instructor | instructor+ | My Roster, Lab Approvals, Attendance |
| Site Support | support_staff+ | (support tools) |

\* = internal-only feature (`internal_only=true` in registry). Hidden from
non-authorized users by the gate map (Phase 17 fix) — the section wrapper is a coarse
`hasRank("student")` but `isPageEnabled()` does the fine-grained hiding.

## FINDINGS

### F1 — Tier-blind customer sections (PRIMARY Phase 18 gap)
Every customer section gates on `hasRank("student")` — ANY registered user of ANY tier
sees ALL customer features. A free user sees Creator Studio, Ghost Producer, Social
Blast, Membership, Band, earnings/payouts — features they cannot use. **Navigation
implies access.** The backend enforces tiers correctly; the nav does not.

### F2 — No PUBLIC navigation model
The sidebar is auth-gated. Anonymous visitors have no tier-aware nav (landing only).
Fine per policy, but there is no explicit `public_access` flag driving it (see
TIER_ACCESS_ARCHITECTURE.md G2).

### F3 — BYOK unlock not surfaced as an access state
"My AI (BYOK)" is a single nav item under NAM. There is no representation of the
BYOK-unlock state in nav visibility (e.g., which AI features unlock once BYOK is
enabled).

### F4 — Internal features inside customer sections (mitigated)
`Admin Assistant`, `Jamil` sit in the NAM section (student+ wrapper). Phase 17's gate
map hides them from unauthorized users — verified by unit test — but the cleaner fix
is moving them out of customer sections entirely (Director/internal only).

### F5 — Misleading / vague labels
| Item | Issue | Recommended treatment |
|------|-------|-----------------------|
| Sanctuary | `/sanctuary` redirects to `/helper` — the item implies a feature that has no page | Decide canonical home or remove item (exec decision) |
| M.O.R.E. Pantheon | route is `/trash` | Rename route/label |
| Ascension Protocols, Vonns Saga, Members' Palace, AAWAB, Agent Wellness | brand names without descriptors | Add functional descriptors (already flagged in NAVIGATION_LABEL_AUDIT) |
| Business Office / Command / Sage Audit / Sites & Inventory / AI Team Bridge | internal jargon — acceptable for Director audience | Keep (staff-facing), add descriptors if needed |

### F6 — Duplicates / shortcuts
- `/admin/business-office` + `/business-office` (route alias, earlier audit) — one
  canonical home, keep redirect.
- Legal Tools appears once (Community) — fine.

### F7 — Missing from nav (canonical-home gaps)
- **Orchestrator** — no canonical page (dead link removed in Phase 17; the internal
  API exists at `/api/ai/orchestrator`). Council page `/council` renders the
  OrchestratorChat component. Documented; needs decision whether the internal
  orchestrator needs its own admin page.
- **Sanctuary** — no canonical home (F5).

## TARGET TIER-FIRST STRUCTURE (design, not yet implemented)

Derived from the registry + tier matrix — NOT a second access system; AppShell must
consume the canonical gate map (already does via `isPageEnabled`).

1. **PUBLIC (anonymous):** Explore, Courses, Creators, Store, Community/Public, Help,
   Plans, Sign In, Register — no dashboard.
2. **FREE (registered):** Home/Dashboard (free), Learn, Community, Music, Games,
   Library/Portfolio, Profile, Settings, Access/Upgrade.
3. **BYOK UNLOCK:** AI features with `byok_allowed=true` become visible/unlocked
   (funding = user key).
4. **MEMBER/BASIC → PLUS → PRO → PATRON:** add each tier's bundle from the FCC tier
   matrix (cumulative).
5. **EXECUTIVE:** separate internal nav (Director etc.), never customer-facing.

Implementation rule (STEP 5–6, gated): every `nl()` item stays; its VISIBILITY is
derived by `isPageEnabled(route, user)` + a tier-rank check computed from the same
`FEATURE_REGISTRY` `allowed_tiers` used by the backend — no new hardcoded access logic
in AppShell.

## ACCEPTANCE STATUS (navigation dimension)

- Test 1 (anonymous no dashboard): PASS by structure (sidebar auth-gated; `/dashboard`
  is `Protected`).
- Test 3/7/8 (free sees free only; tier inheritance in nav): **FAIL today** — nav is
  tier-blind (F1). Requires STEP 5–6.
- Test 16 (FCC tier change → nav change without code edit): **FAIL today** — nav does
  not read `allowed_tiers`; only `enabled`/`allowed_roles` reach the gate map.
  Requires extending the gate map with tier visibility.
- Test 17 (FCC role change → access change without page edits): PASS at API level
  (FCC `allowed_roles` enforced by middleware); nav role-hiding PASSES via gate map.
