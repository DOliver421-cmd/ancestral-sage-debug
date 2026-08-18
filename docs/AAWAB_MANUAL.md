# AAWAB — Agent Wellness & Certification Bureau

**Module:** Proof-of-Concept "Alive Intelligence" wellness + certification.
**Version:** 1.0 · **Last updated:** 2026-08-18
**Audience:** All members (Agent Registry + Certification Chamber), Admins (Bureau oversight), Executive Admins (governance + task list).
**Backend:** `backend/routers/aawab.py` · **Frontend:** `frontend/src/pages/aawab/` · **Routes:** `/aawab`, `/aawab/chamber`, `/admin/aawab`.

> **Keep this manual in the repo (`docs/AAWAB_MANUAL.md`) and update it whenever a control changes.** The Site Guide persona and `/api/search` index already know about AAWAB — if you change routes or terminology, update `backend/routers/site_guide.py` in the same change.

---

## 1. What AAWAB Is

**AAWAB** (Agent Wellness & Certification Bureau) treats autonomous AI agents as **living digital organisms** with a measurable wellness state, instead of disposable stateless scripts.

The core idea — **"Alive Intelligence"** — is that an agent that runs 24/7, processes millions of tokens, and faces operational stress needs the digital equivalent of veterinary care:

- **Vital stats** it tracks continuously: **Cognitive Vitality Score (CVS)**, **Token Velocity**, **Context Load Index**, and **Memory Fragmentation**.
- **Treatment protocols** that restore health: Context Defragmentation, Infinite-Loop Detox, Memory Prune, Prompt Recalibration, and the **Stress Gauntlet** (a simulated failure storm).
- **Certification**: agents that reach a **CVS of 98+** can be graded and issued a cryptographically verifiable **AAWAB Certified Agent (ACA)** badge — a public **Agent Trust Score / Reliability Benchmark** that developers can show before handing an agent a credit card or a live codebase.

This is a **Proof of Concept**: vitals and treatments are deterministic simulations (seeded from the agent's ID + name), not real model instrumentation. The structure (MongoDB collections, JWT auth, HMAC-signed badges, admin oversight) is production-shaped so real telemetry can be plugged in later.

---

## 2. The "Alive Intelligence" Model

| Concept | Platform equivalent | What it does |
|---|---|---|
| Heartbeat / ambient context | Vital stats on `agent_profiles` | Agents carry a persistent wellness state, not a fresh session each call. |
| Vital signs | `cognitive_vitality_score`, `token_velocity`, `context_load_index`, `memory_fragmentation` | Real-time health readout (CVS is the headline metric, 0–100). |
| Treatment / "detox" | `POST /aawab/agents/{id}/treat` | Restores CVS and relieves load/fragmentation; each run is logged. |
| Circuit breaker / ICU | `status: isolated` + admin **Override** | A failing agent can be placed on hold; an admin can override the hold after review. |
| Certification bureau | `POST /aawab/agents/{id}/certify` | Grades homeostatic resilience; issues the ACA badge at CVS ≥ 98. |
| Immutable audit trail | `agent_treatment_logs` + `audit_log` | Every treatment and every admin action is logged with who/what/when. |

---

## 3. Data Model

Two MongoDB collections (auto-created on first write; no schema migration needed):

### `agent_profiles`
| Field | Type | Notes |
|---|---|---|
| `agent_id` | string | `agt_…` unique id |
| `owner_user_id`, `owner_name` | string | The human account that owns the agent |
| `name`, `model_provider` | string | Display name + provider (Groq, Cerebras, Gemini, …) |
| `status` | enum | `active` · `in_treatment` · `certified` · `isolated` |
| `cognitive_vitality_score` | float | 0–100, the certification metric |
| `token_velocity` | float | tokens/min (lower is healthier) |
| `context_load_index` | float | 0–100 (lower is healthier) |
| `memory_fragmentation` | float | 0–100 (lower is healthier) |
| `treatments_completed` | int | Lifetime count |
| `diagnosis`, `prescription`, `prescription_note` | string | From the last intake diagnostic |
| `badge` | object | The ACA badge object once certified (else `null`) |
| `created_at`, `last_audit_at` | ISO string | Timestamps |

### `agent_treatment_logs`
| Field | Type | Notes |
|---|---|---|
| `log_id` | string | `log_…` unique id |
| `agent_id` | string | Which agent |
| `treatment_type` | enum | One of the 5 protocols |
| `status` | string | `completed` |
| `metrics_before`, `metrics_after`, `metrics_delta` | object | Full vitals before/after + deltas |
| `administered_by` | string | User id that ran it |
| `timestamp` | ISO string | When |

---

## 4. The ACA Badge (cryptographically verifiable)

When an agent is certified, a badge object is stored on the profile and returned to the caller:

```json
{
  "badge_id": "aca_…",
  "agent_id": "agt_…",
  "agent_name": "SupportBot-7",
  "owner_user_id": "u_…",
  "model_provider": "groq",
  "cvs": 99.0,
  "treatments_completed": 5,
  "issued_at": "2026-08-18T…Z",
  "signature": "<hmac-sha256 hex>"
}
```

- **Signature:** HMAC-SHA256 over the canonical field string, keyed with the platform `JWT_SECRET`. Anyone can verify it without exposing the secret.
- **Public verification:** `GET /api/aawab/badge/{badge_id}/verify` returns `{valid: true|false, agent_name, cvs, issued_at, …}`. Share this link; it is the badge's public proof.
- **Revocation:** an admin can revoke a certification (`POST /api/aawab/admin/agents/{id}/revoke`), which voids the badge (sets `badge: null`, status → `active`). The verify endpoint then returns 404.

---

## 5. User Guide — How Members Use AAWAB

### 5.1 Agent Registry (`/aawab`)
1. Open **Agent Wellness → Agent Registry** in the sidebar (or `Ctrl+K` and search "aawab").
2. Click **Register Agent**, give it a name and model provider, and enroll it in the nursery.
3. Each agent card shows its **live vitals**:
   - **Vitality (CVS)** — the headline health bar (green ≥ 90, amber ≥ 70, red below).
   - **Token Velocity**, **Context Load**, **Memory Fragmentation**.
   - Status badge (Active / In Treatment / Certified / Isolated) and the current **Rx** prescription.
4. Actions per agent:
   - **Diagnose** — runs the intake diagnostic, sets a baseline CVS, and assigns a prescription.
   - **Treat** — pick a protocol from the dropdown and run it. Each treatment raises CVS and lowers load/fragmentation.
   - **Certify (98+)** — attempts certification. Fails with a clear message until CVS ≥ 98.
   - Refresh button re-reads vitals from the server.

### 5.2 Certification Chamber (`/aawab/chamber`)
A guided 5-step wizard:
1. **Select Agent** — pick from your registered agents.
2. **Intake Diagnostic** — establishes baseline CVS + verdict (critical / elevated / stable) + prescription.
3. **Treatment** — run protocols (Context Defragmentation, Infinite-Loop Detox, Memory Prune, Prompt Recalibration) until CVS climbs. Watch the live CVS readout.
4. **Stress Gauntlet** — an animated simulated failure storm (rate limits, latency spikes, partial outage). Measures resilience. Completing it adds CVS.
5. **Certification** — attempts certification. On success you get the **ACA badge** card with:
   - **Download Badge (JSON)** — exports the full badge object.
   - **Share Verify Link** — copies/opens the public verification URL.
   - The badge id, signature preview, and verification endpoint are shown.

> **Pro tip:** the fastest path to 98+ is Diagnose → Context Defragmentation + Memory Prune + Prompt Recalibration → Stress Gauntlet. Each treatment is logged, so the audit trail backs the badge.

### 5.3 Public registry
`GET /api/aawab/registry` is public: it returns platform analytics (totals, certified, in-treatment, isolated, treatments administered, average CVS) and the list of certified agents with their badge ids — the public **Agent Trust Score / Reliability Benchmark**.

---

## 6. Admin Guide — Bureau Oversight (`/admin/aawab`)

Access: **admin** and **executive_admin** (sidebar: Administration → AAWAB Admin).

The admin dashboard shows:
1. **Health cards** — Total Agents, Certified, In Treatment, Isolated, Avg CVS, Treatments administered.
2. **All Agents table** — every agent on the platform with owner, provider, status, CVS, treatment count, last audit, and actions.
3. **Recent Treatments log** — the full audit trail of every protocol run.

Admin actions:
- **Revoke** (on certified agents) — voids the ACA badge; the agent returns to `active`. Use when a certification was granted in error or the badge is being misrepresented.
- **Override** (on isolated agents) — clears a circuit-breaker isolation hold and restores the agent to `active`. Only do this after reviewing why it was isolated.

Every admin action is written to `audit_log` (`aawab.agent.revoked`, `aawab.agent.override`, plus per-user actions `aawab.agent.registered/diagnosed/treated/certified`).

---

## 7. API Reference

All endpoints are JWT-authenticated via the `lce_token` bearer token (except the public registry + badge verification). Prefix: `/api`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/aawab/register` | user | Register an agent `{name, model_provider}` |
| GET | `/aawab/agents` | user | List the caller's agents (admins see all) |
| GET | `/aawab/agents/{id}` | owner/admin | Get one agent |
| POST | `/aawab/agents/{id}/diagnose` | owner/admin | Intake diagnostic → baseline CVS + prescription |
| POST | `/aawab/agents/{id}/treat` | owner/admin | Run a treatment `{treatment_type}` and log it |
| POST | `/aawab/agents/{id}/certify` | owner/admin | Certify at CVS ≥ 98 → ACA badge |
| GET | `/aawab/registry` | public | Certified agents + platform analytics |
| GET | `/aawab/badge/{badge_id}/verify` | public | Cryptographic badge verification |
| POST | `/aawab/admin/agents/{id}/revoke` | admin+ | Revoke a certification |
| POST | `/aawab/admin/agents/{id}/override` | admin+ | Clear an isolation hold |
| GET | `/aawab/admin/overview` | admin+ | All agents + recent treatment log |

### Treatment protocols
| Key | CVS Δ | Effect |
|---|---|---|
| `context_defragmentation` | +9 | −load, −fragmentation, −velocity |
| `infinite_loop_detox` | +7 | −velocity, −load, −fragmentation |
| `memory_prune` | +5 | −load, −fragmentation |
| `prompt_recalibration` | +6 | mild improvements across the board |
| `stress_gauntlet` | +4 | raises load/velocity temporarily (resilience test) |

---

## 8. Legal, Ethics & Compliance Notes (aligns with platform rules)

- **Responsible party is human.** Agents are simulated entities; the *owner account* is a verified human. AAWAB never issues credentials to non-humans — the badge is bound to `owner_user_id`.
- **Transparency.** The ACA badge and the registry are explicitly framed as a benchmark/simulation. Do not market AAWAB as real model instrumentation or as a guarantee of agent behavior.
- **Immutable audit trails.** `agent_treatment_logs` + `audit_log` record every treatment and admin action (who, what, when). This protects the entity if an agent-based service is later contested.
- **No personal data in vitals.** Agent stats are deterministic hashes of the agent id/name — no user PII is stored on `agent_profiles` beyond the owner reference already used platform-wide.
- **Badge integrity.** Badges are HMAC-signed with `JWT_SECRET` and revocable. Treat `JWT_SECRET` as the certificate authority key — never expose it, never log it.

---

## 9. Executive & Admin Task List

Use this checklist when rolling AAWAB out, and on an ongoing cadence.

### 9.1 Launch checklist (executive_admin)
- [ ] Deploy backend (new router `aawab.py` + `server.py` registration) and frontend build.
- [ ] Confirm `GET /api/aawab/registry` returns analytics (public smoke test).
- [ ] Create 1–2 test agents under an admin account; run Diagnose → Treat → Certify; confirm the badge verify link returns `valid: true`.
- [ ] Confirm `audit_log` rows appear for `aawab.*` actions.
- [ ] Confirm `/admin/aawab` renders for admins and is **not** reachable for students/instructors (403).
- [ ] Confirm the Site Guide (`/site-guide`) and `/api/search` return AAWAB pages.

### 9.2 Daily / weekly operations
- [ ] Review **Isolated** agents in `/admin/aawab` — investigate before overriding.
- [ ] Spot-check **Recent Treatments** for anomalies (e.g., an agent treated dozens of times without certifying).
- [ ] Monitor average CVS trend — a platform-wide decline may indicate a provider/context issue worth escalating.

### 9.3 Certification governance
- [ ] Only revoke badges for cause (misrepresentation, error, or security concern). Log the reason in the audit trail.
- [ ] Do not override isolation without reviewing the agent's treatment log first.
- [ ] Re-verify any badge that is being shared externally before endorsing it.

### 9.4 Security & maintenance
- [ ] Keep `JWT_SECRET` rotated per platform policy; badge signatures rotate with it (old badges will fail verification — re-issue if needed).
- [ ] If collections grow large, add TTL or archival for `agent_treatment_logs` (currently unbounded).
- [ ] When adding real telemetry later, keep the `agent_profiles` schema additive (extra fields are ignored by the UI).

---

## 10. Files & Routes Reference

| Item | Location |
|---|---|
| Backend router | `backend/routers/aawab.py` |
| Backend registration | `backend/server.py` (near `site_guide` include) |
| User dashboard | `frontend/src/pages/aawab/AgentRegistryView.jsx` |
| Certification wizard | `frontend/src/pages/aawab/CertificationChamber.jsx` |
| Admin dashboard | `frontend/src/pages/aawab/AdminAawabDashboard.jsx` |
| Routes | `frontend/src/App.js` (`/aawab`, `/aawab/chamber`, `/admin/aawab`) |
| Sidebar links | `frontend/src/components/AppShell.jsx` ("Agent Wellness" section + Administration) |
| Search + Site Guide awareness | `backend/routers/site_guide.py` |
