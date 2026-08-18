# Free Google Stack — Evaluation for the Platform

**Base account:** `morehelpcenter@gmail.com`
**Last updated:** 2026-08-18
**Status:** Evaluated. Two of five features are worth integrating; the rest are deferred with reasons.

This document answers one question honestly: *does each free Google feature earn its place on this platform?*
The platform runs on a zero-cost stack (free-first LLM gateway, Railway, MongoDB). A feature is integrated only
when it (a) serves the mission, (b) reduces cost or creates revenue, and (c) does not add fragile dependencies.

---

## 1. Gemini Developer API (AI Studio) — INTEGRATE ✅

**What it is:** Google's developer LLM API with a permanent free tier.
**Current facts (checked 2026-08):** Free tier covers Flash-class models only (Pro models excluded since early
2026). Rate limits were cut repeatedly through 2025–2026 and now sit around **5–15 requests/minute** depending on
model — e.g. Gemini 2.0 Flash ≈ 15 RPM / 1M tokens per minute, 2.5 Flash ≈ 10 RPM / 250K TPM. Daily request
ceilings apply per project.

**Platform status — already integrated:**
- Gateway Tier 2 (`ai/llm_gateway.py`, `GEMINI_API_KEY`, free, 1M context, text-only tier).
- BYOK provider (`byok.py` provider list includes `gemini`, priority after Groq/Cerebras).
- Admin key entry: `/admin/providers` (type: `gemini`).

**Benefit:** free fallback LLM capacity with a huge context window; BYOK users can bring their own free Gemini key.
**Risk:** free tier limits have been shrinking — that is exactly why Gemini must stay a fallback tier, never the
single provider. The platform's free-first chain (Groq → Cerebras → SambaNova → Gemini → … → KB) already treats it
that way.

**Setup (one-time, ~2 minutes):**
1. Sign in to AI Studio (`aistudio.google.com`) as `morehelpcenter@gmail.com`.
2. Create an API key (AI Studio → Get API key → Create key).
3. Paste it at `/admin/providers` (type `gemini`) — or set `GEMINI_API_KEY` in Railway env.
4. Verify in the Executive Command Center → AI & Providers tab (Gemini shows "Key set" / "available").

---

## 2. Free Google AI courses — INTEGRATE ✅ (as links, not embedded content)

**What they are:** Google AI Essentials (grow.google/ai-essentials), Google Cloud Skills Boost (~35 free learning
credits/month), skills.google, and the free Gemini Certified Educator track.

**Benefit:** directly serves the mission — free education for invisible communities — and feeds the Learn → Member
loop without the platform hosting any media (the courses' own servers pay the bandwidth).

**Action:** surface them in a "Free Learning lane" in the Help Center (curated links + platform credential on
completion). No backend needed.

---

## 3. Google Cloud free tier ($300 / 90 days) — DEFER ⏸️

**What it is:** $300 credit for 90 days + always-free compute/storage limits.

**Verdict:** not useful today. The platform already runs on a zero-cost stack with no GCP dependency; taking the
credit would add a second hosting surface, ops overhead, and a 90-day expiry that would force a migration decision
for no current benefit. Revisit only when there is a real need for GCP compute, storage, or Vertex AI.

---

## 4. Google Workspace (Gmail / Drive / Calendar) — ALREADY THE BASE ACCOUNT ✅

`morehelpcenter@gmail.com` already provides the daily ops layer (mail, drive, calendar) at no cost and requires no
platform integration. Keep using it as the canonical Google identity for AI Studio keys, course accounts, and
publishing.

---

## 5. Everything else (Vertex AI free tier, Colab, etc.) — NOT NEEDED NOW ⏸️

Vertex free tier overlaps with the Gemini API already integrated; Colab is a human tool, not a platform service.
Neither earns a dependency.

---

## Bottom line

| Feature | Verdict | Action |
|---|---|---|
| Gemini Developer API | Integrate | Key via AI Studio (base account) → `/admin/providers` |
| Free Google courses | Integrate | Free Learning lane links + credential |
| Google Cloud free tier | Defer | Revisit only with a real GCP need |
| Workspace | Already in use | No integration required |
| Vertex / Colab | Defer | Overlap with what's already wired |

The Executive Command Center (`/admin/command` → AI & Providers tab) shows live status for the Gemini key and the
full provider chain, so this evaluation stays observable in the exec interface.
