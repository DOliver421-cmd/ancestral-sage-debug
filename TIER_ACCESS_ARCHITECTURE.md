# TIER ACCESS ARCHITECTURE

**Date:** August 23, 2026
**Status:** AUDIT COMPLETE — tier-first model defined; navigation is NOT yet tier-derived (documented gap)

## 1. THE REAL TIER LADDER (source of truth)

Verified against `security/feature_control.py` `TIER_RANK`, `routers/exec_control.py`
`_BUILTIN_TIERS`, `frontend/src/lib/tiers.js`, `routers/payments.py`. **No invented
tiers** — `creator`/`studio`/`director` do not exist and have been removed from the
registry.

| Rank | Tier | Meaning |
|------|------|---------|
| — | **PUBLIC** | anonymous visitor (never a stored tier) |
| 0 | free | registered, no payment |
| 1 | member | first paid tier ("Basic" in conceptual docs) |
| 2 | plus | expanded courses + studio |
| 3 | pro | advanced courses, labs, full AI suite |
| 4 | patron | founders circle |
| 5 | executive | admin-granted, all features |

The user's tier is stored as `user.feature_tier` (default `"free"`), granted by the
payment webhook and overridable by admins. **Cumulative:** rank N inherits ranks < N
unless a feature is explicitly excluded.

## 2. THE $3 BYOK UNLOCK (verified implemented)

A distinct, low-cost access path that is NOT a replacement for tiers:

- **Entitlement:** `db.users.byok_enabled` + `byok_activated_at`, flipped by
  `POST /api/byok/activate` (post-payment hook; `BYOK_PRICE_USD` default 3).
- **Pricing:** `byok_price_for(role)` — $3 for member/student roles; **free** for
  staff/partner/support roles (`FREE_BYOK_ROLES` in `roles.py`).
- **Semantics:** BYOK changes the AI **funding** dimension only. It grants the user the
  right to attach their own key from the 3 approved free providers (Groq, Cerebras,
  Gemini) and have their AI calls routed through that key so **the platform pays
  nothing**. It does NOT grant: internal features, role-restricted features,
  proprietary features, executive features, or paid-tier features.
- **Enforcement:** `resolve_byok()` returns a key ONLY when entitlement + active key;
  the gateway uses it FIRST (before any platform key) and never counts BYOK tokens
  against platform budgets.
- **Gap:** the gateway uses BYOK whenever a user has it, without consulting the
  per-feature `byok_allowed` funding flag (see §5).

## 3. ACCESS DECISION MODEL (tier-first, role separate, funding separate)

```
can_access(user, feature, capability):

  enabled?                 (FCC)                 — false → DENY
  internal_only?           (FCC)                 — true → DENY unless role allowed
  customer_access_allowed? (FCC)                 — false → DENY for customers
  tier eligible?           (FCC allowed_tiers)   — user.feature_tier rank ≥ lowest
  role eligible?           (FCC allowed_roles)   — user.role rank ≥ lowest
  funding:
     platform-funded AI?   — requires tier eligibility AND platform_ai allowed
     BYOK AI?              — requires eligibility AND byok_allowed
  budget:                  — global hourly cap + per-user daily budget
```

Order of evaluation in the live middleware
(`security/feature_control.py` `check_user_feature_access`):
per-user exec override → AI-access override → **FCC config (enabled, internal,
roles, tiers)** → tier requirement matrix. Funding mode is evaluated at the gateway
AFTER this function has passed — **authorization always precedes credential
selection/provider invocation**.

## 4. CURRENT STATE PER TIER (from FEATURE_ACCESS_MATRIX.md)

- **PUBLIC:** landing, plans, login/register, legal/help — no dashboard, no AI.
- **FREE:** community, learning content, music/games basics, BYOK page, AI Tutor +
  Personal Helper + Site Guide (registry marks these `free`; platform-funded AI is
  budget-capped, never unlimited).
- **MEMBER/BASIC:** Creator Studio + course manager + lounge + band + earnings
  (registry `member+`; exec flags enforce `member`/`plus` tiers at the API).
- **PLUS:** labs, tracks, full publishing, payouts.
- **PRO:** Council (Sage), adaptive path.
- **PATRON:** (mass-post per tiers.js; no registry default uses patron+ yet).
- **EXECUTIVE:** admin-granted tier; internal features are role-gated separately.

## 5. GAPS (documented — not silently fixed)

| # | Gap | Impact | Required change |
|---|-----|--------|-----------------|
| G1 | **Sidebar is role-derived, not tier-derived.** Every customer section is `hasRank("student")`; a free user sees Creator Studio, Ghost Producer, Social Blast, Membership, etc. in nav. | Navigation implies access the user does not have (violates Phase 18 §3). | Derive nav item visibility from the FCC tier matrix (see TIERED_NAVIGATION_AUDIT.md STEP 5–6). |
| G2 | **No `public_access` field** in the registry/FCC. Public/anonymous eligibility is implicit (no-auth routes). | Public exposure is not an explicit, auditable decision. | Add `public_access` (default false for cost-bearing) to registry + FCC + gate map. |
| G3 | **Gateway ignores per-feature `byok_allowed`/`platform_ai`.** BYOK is used whenever a key exists. | Declared funding mode is not honored (a `byok_allowed=false` feature still uses the user's key — saves platform money but violates the policy). | Pass a funding hint (`allow_byok`/`platform_funded`) from the FCC into `call_llm`; do NOT change provider infrastructure. |
| G4 | **BYOK-unlock tier isn't represented in the FCC matrices.** | Admin cannot see "BYOK" as an access column. | Represent the unlock as a special column in the FCC tier matrix (not a new tier name). |
| G5 | No per-feature quota model (global caps only). | Platform-funded AI is capped globally, not per feature. | CONFIGURATION REQUIRED — design quota fields in FCC. |

## 6. ACCEPTANCE STATUS (tier dimension)

Verified now: tiers are cumulative and rank-enforced at the API (`FEATURE_MIN_TIER` +
FCC `allowed_tiers` rank check — tested); free users cannot bypass paid tiers via
direct API (`check_user_feature_access` tier block tested); `executive` is
admin-granted, not purchasable.

Blocked: tier-derived navigation (G1) — requires the FCC/nav work in STEP 5–6, which
is intentionally not implemented before this audit is complete.
