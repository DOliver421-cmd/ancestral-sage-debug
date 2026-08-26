# BUSINESS ACCESS POLICY

**Date:** August 23, 2026
**Status:** LIVE POLICY — enforced by the Feature Control Center + `security/feature_control.py`
**Supersedes:** ad-hoc lockdown decisions from earlier phases

---

## 1. THE BUSINESS RULE

The platform is a commercial product. A capability that consumes platform resources —
AI/API tokens, image generation, paid provider calls, significant compute, paid
third-party services, operational labor, or proprietary process/IP — is **cost-bearing**
and must never become publicly available merely because it exists in the codebase.

**Access is a deliberate configuration, not a side effect of code existing.**

## 2. THE SIX ACCESS DIMENSIONS (independent, not interchangeable)

| Dimension | Answers | Examples |
|-----------|---------|----------|
| VISIBLE | Does the user see it exists? | nav + search visibility |
| DISCOVERABLE | Can the user find it? | navigation grouping |
| AUTHORIZED | Does the user's ROLE permit it? | student / support / admin / executive_admin |
| ENTITLED | Does the user's TIER permit it? | free / member / plus / pro / patron / executive |
| FUNDED | Who pays for the resource consumed? | platform-funded / BYOK / none |
| USABLE | Is it enabled and within budget? | enabled flag, rate limits |

A user can see a feature without receiving access. A user can be authorized without the
platform funding the AI call. A user can have a BYOK key without access to a proprietary
capability.

## 3. ROLE vs TIER (verified real definitions)

**ROLE** (authorization identity — `backend/roles.py`, `frontend/src/lib/roles.js`):
`public` (0, unauthenticated) → `student` (1) → `trial_pass` (2) → `instructor` (3) →
`support_staff` (4) → `oversight` (5) → `admin` (6) → `executive_admin` (7).

**TIER** (commercial entitlement — `security/feature_control.py TIER_RANK`,
`routers/exec_control.py _BUILTIN_TIERS`, `frontend/src/lib/tiers.js`):
`free` (0) → `member` (1) → `plus` (2) → `pro` (3) → `patron` (4) → `executive` (5).

**No `creator`, `studio`, or `director` tier exists.** Legacy labels from early builds are
normalized (`creator→member`, `studio→plus`, `director→patron`) at every read and
enforcement boundary and have been cleaned from the registry source data (Phase 17).

## 4. FEATURE CLASSIFICATION (9 required fields)

Every feature in `FEATURE_REGISTRY` (`backend/routers/features.py`) carries:

`enabled` · `internal_only` · `customer_access_allowed` · `cost_bearing` ·
`allowed_roles` · `allowed_tiers` · `navigation_visible` · `platform_ai` · `byok_allowed`

### Fail-closed default for a NEW feature

```
enabled = false
internal_only = true
customer_access_allowed = false
cost_bearing = true
allowed_roles = []
allowed_tiers = []
navigation_visible = false
platform_ai = false
byok_allowed = false
```

Nothing becomes available because a developer created a route or component. Existing
features were audited individually (Phase 17A) and keep their legitimate configuration.

## 5. INTERNAL / PROPRIETARY (never customer-facing by default)

These are platform operations/IP, not products:

- **Arena** — `internal_only`, `allowed_roles=["executive_admin"]` only. NOT a customer,
  free-tier, or paid-tier feature. Proprietary executive reasoning infrastructure.
- **Jamil** — `internal_only`, `allowed_roles=["admin","executive_admin"]`.
- **Orchestrator** — `internal_only`, `allowed_roles=["admin","executive_admin"]`.
- **Admin Assistant** — `internal_only`, `allowed_roles=["admin","executive_admin"]`.
- **Admin surfaces** (dashboard, IAM, command, health) — `internal_only`, router-level
  rank checks + `/api/admin/*` exemption + exec AccessGateway.

Enforcement: FCC middleware denies 403 unless the user's role rank ≥ lowest allowed
rank. Frontend nav is hidden for unauthorized users via the gate map (registry defaults
for internal-only features) — see ACCESS_CONTROL_ARCHITECTURE.md.

## 6. COST-BEARING (platform-funded resources are never free by default)

Customer-accessible AND cost-bearing today (registry, verified API surfaces):

| Feature | API surface | Enforcement |
|---------|-------------|-------------|
| AI Tutor (nam.chat) | `/api/ai/chat`, `/api/nam` | FCC + `ai_chat` flag |
| Personal Helper | `/api/ai/helper` | FCC + `ai_chat` flag |
| Site Guide | `/api/site-guide/*` | FCC |
| Council (Sage) | `/api/ai/sage/*` | FCC + `ai_chat` flag |
| Creator Studio | `/api/studio/*` | `studio` flag + tier (plus) |
| Ghost Producer | page admin-gated; calls `/api/ai/chat` | admin page gate + ai_chat |
| Social Blast | `/api/ai/social-blast` | `publisher_ai` flag + tier (member) |
| Learning Path | `/api/adaptive/me` | **auth-only — no feature gate (GAP)** |
| Sanctuary | `/sanctuary` redirects to `/helper` | no dedicated API (N/A) |

For each cost-bearing feature the FCC must decide: internal-only? tiers? roles?
platform-funded AI allowed? BYOK allowed? budget/quota (CONFIGURATION REQUIRED — none
exist per-feature; global gateway caps apply: `HOURLY_TOKEN_CAP`, per-user daily budget).

## 7. PUBLIC / ANONYMOUS

Anonymous visitors get only genuinely free, low-cost public capabilities (landing,
discovery, legal/help, login/register). No platform-funded AI and no proprietary
persona is exposed to anonymous visitors. `platform_ai` + `customer_access_allowed`
must both be explicitly configured before any AI reaches an anonymous visitor.

## 7A. AI FUNDING POLICY — OWNER DECISION (AUGUST 2026)

**Platform-funded AI is reserved for `admin` / `executive_admin` staff ONLY.
Customers never receive platform-funded AI at any tier.**

| Audience | AI funding | What they get |
|----------|-----------|---------------|
| Anonymous / public | none | keyword KB only (never an LLM call) |
| Customer — any tier (free / member / plus / pro / patron / executive) | **their own BYOK key only** | live AI via BYOK; keyword KB when no key |
| instructor / support_staff / oversight | their own BYOK key (granted free by role) | live AI via BYOK; keyword KB when no key |
| admin / executive_admin (staff) | **platform-funded** | live AI via the platform gateway (plus BYOK when configured) |

Rules:
- The gateway (`ai/llm_gateway.py`) enforces this BEFORE any provider invocation:
  a non-staff authenticated caller with no BYOK key gets the keyword KB answer,
  never platform tokens. A caller whose staff status cannot be verified is
  treated as non-staff (fail-closed).
- Anonymous AI endpoints (`/api/ai/helper`, `/api/public/helper/ask`,
  `/api/helper/ask`, `/api/supervisor/public-chat`) answer from the keyword KB
  only — they contain no LLM call path.
- "If they want more AI, they upgrade their own keys": customers increase
  capacity by upgrading their own provider key/plan; the platform does not fund
  customer AI usage at any tier.
- The zero-cost fallback is the multi-layer keyword KB (`ai/keyword_kb.py` +
  `ai/kb_entries.json`, dynamically extendable; MongoDB `kb_entries` supported)
  — every AI surface degrades to a useful answer, never a dead end.

## 8. BYOK

BYOK = the user supplies provider resources. It is an **access mechanism, not a
permission system**:

- Feature access (role/tier/internal) is decided FIRST by the FCC middleware.
- `byok_allowed=true` only permits the user's own key to fund an *otherwise authorized*
  feature.
- BYOK never grants access to an internal/proprietary feature.
- Platform-funded AI and BYOK are independently controllable (`platform_ai` vs
  `byok_allowed`).

## 9. SUPPORT-STAFF SHARED PROVIDER POOL

The existing support-staff shared key pool is platform infrastructure, isolated from
customer permissions. Credential priority stays:

1. User BYOK
2. Platform provider keys
3. Approved shared support-staff pool
4. KB/fallback

Credential availability is NEVER an authorization mechanism. Feature access is decided
first, spend happens second.

## 10. ENFORCEMENT LAYERS (all must agree)

| Layer | Mechanism |
|-------|-----------|
| Frontend nav | `accessGates.js` gate map; internal-only defaults hide proprietary nav |
| Frontend routes | `BoundedAdmin` / `Protected` wrappers in App.js |
| Backend authorization | router `require_role` / `_require_rank` / `_dep_current_user` |
| Feature access | FCC middleware (`security/feature_control.py`) — enabled, internal, roles, tiers |
| Tier gates | exec `authz_matrix` + `FEATURE_MIN_TIER` |
| AI funding | gateway budget caps + BYOK resolution AFTER authorization |

The backend is authoritative. Frontend hiding is UX, never security.

## 11. PRESERVED FUNCTIONALITY

This policy protects value; it does not remove features. No working customer feature was
deleted or disabled without evidence it is internal/proprietary/cost-bearing. The only
navigation change in Phase 17: a dead `/orchestrator` nav link was removed (the route
never existed; the Council/Sage page at `/council` is the canonical persona home).

## 12. CONFIGURATION REQUIRED (not invented here)

- Per-feature AI quotas/budgets — global caps exist; per-feature limits are
  CONFIGURATION REQUIRED (see FEATURE_CONTROL_CENTER_SPEC.md).
- `learn.adaptive` API (`/api/adaptive/me`) has no feature gate — rule-based endpoint;
  requires an executive decision to map or reclassify (see FEATURE_ACCESS_MATRIX.md).
- Production env (`MONGO_URL`, `JWT_SECRET`, provider keys,
  `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`) — external, Railway.
