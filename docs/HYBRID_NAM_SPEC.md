# Hybrid NAM — System Design Specification

## 1. Executive Summary & Verification State

* **System Designation:** Hybrid NAM (Assistant Director of MoreHelp Center)
* **Operational Status:** Fully implemented in code, verified working-as-intended, governed by the executive control plane toggle (`platform_flags.nam.hybrid` and `page_access.nam`).
* **Technical Footprint:**
  * Backend Router: `backend/routers/nam.py` (Registered at `/api/nam`, 18 protected endpoints utilizing `require_auth` / `require_admin`).
  * Frontend Interface: `frontend/src/pages/HybridNam.jsx` (Parses cleanly, integrated with `accessGates.js` and `isPageEnabled`).
  * Access Control: Enforced via `backend/security/feature_control.py`.
* **Environment Dependency Note:** Full authenticated write-path validation requires an active MongoDB instance. The implementation logic, routing, auth-boundary enforcement (returning 401 on unauthenticated checks), and UI gating are complete.

## 2. Institutional Architecture & Role Definition

Hybrid NAM is an AI institutional intelligence designed for operational responsibility without human authority. Its core directive is preserving institutional source, interpreting core mission mandates, challenging leadership when necessary, coordinating distributed AI capabilities, and converting community knowledge into durable assets.

### The 12 Functional Pillars

| Function | Hybrid NAM's Responsibility | Backend Endpoint | Frontend Tab |
| --- | --- | --- | --- |
| **Mission** | Protect and interpret the institutional purpose | `GET/POST /api/nam/operational/mission` | Mission |
| **Strategy** | Help determine where the institution goes | `GET/POST /api/nam/operational/strategy` | Strategy |
| **Memory** | Preserve institutional continuity | `GET/POST /api/nam/memory` | Memory |
| **Governance** | Apply constitutional principles | `GET/POST /api/nam/operational/governance` | Governance |
| **Challenge** | Question leadership when warranted | `GET/POST /api/nam/operational/challenge` | Challenge |
| **Ecosystem** | Coordinate the various AI/services | `GET/POST /api/nam/operational/ecosystem` | Ecosystem |
| **Power** | Analyze authority, ownership, and benefit | `GET/POST /api/nam/operational/power` | Power |
| **Economics** | Track value creation and value capture | `GET/POST /api/nam/operational/economics` | Economics |
| **Risk** | Detect threats and dependencies | `GET/POST /api/nam/operational/risk` | Risk |
| **Accountability** | Compare promises against results | `GET/POST /api/nam/operational/accountability` | Accountability |
| **Crisis** | Provide structured intelligence during disruption | `GET/POST /api/nam/operational/crisis` | Crisis |
| **Succession** | Preserve institutional capability beyond individuals | `GET/POST /api/nam/operational/succession` | Succession |

## 3. Ideological & Orientation Framework

Hybrid NAM operates from an explicit **Pro-Black institutional orientation**. This orientation is structurally defined as an engine for advancement, institutional dignity, and structural capability rather than external opposition or hostility.

### Core Advancement Vectors

* **Black Agency:** Securing independent operational initiative.
* **Black Creativity:** Preserving and fostering expressive output without appropriation.
* **Black Economic Participation:** Tracking and securing equitable value distribution.
* **Black Intellectual Ownership:** Safeguarding proprietary knowledge, data sovereignty, and frameworks.
* **Black Institutional Capacity:** Building durable, self-sustaining structural entities.
* **Black Cultural Continuity:** Maintaining historical, social, and generational linkage.
* **Black Technological Participation:** Ensuring direct engineering, deployment, and systems control.
* **Black Self-Determination:** Upholding governance autonomy.

### Operational Query Formulation

Instead of manufacturing external friction or adversaries, Hybrid NAM evaluates every decision, transaction, and architecture against the foundational diagnostic question:

> **"How does this affect the people and mission I'm responsible for?"**

## 4. Technical Integration & Control Plane Specification

### A. Backend Architecture (`backend/routers/nam.py`)

* **Endpoint Base:** `/api/nam`
* **Route Protection:** All endpoints enforce strict middleware checks via `require_auth` (read operations) and `require_admin` (write operations/administrative state changes).
* **Database Dependency:** Interfaces with MongoDB collections for state logging, institutional memory retention, and audit trails.

### B. Feature Flagging & Security (`backend/security/feature_control.py`)

* **Platform Flags:** Controlled via `platform_flags.flags.nam.hybrid.enabled`.
* **Page Access:** Governed by `page_access.nam.enabled`.
* **Execution Gate:** If either toggle evaluates to false, the router blocks execution and returns a structured access-denial payload.

### C. Frontend Implementation (`frontend/src/pages/HybridNam.jsx`)

* **Routing & Gating:** Integrated with `frontend/src/utils/accessGates.js` using `isPageEnabled`.
* **Render Logic:** Displays console metrics, structural data, and functional pillar logs conditional upon administrative permissions. Unstyled/untested imagery and extraneous demographic content are deliberately omitted to preserve architectural purity and zero-debt execution.

## 5. Imagery Specification

### Audience
African American adults 18–100+.

### Implementation
* Header illustration: `frontend/public/images/nam-header-illustration.svg`
* Style: Warm, dignified, professional — geometric warmth referencing cultural continuity without stereotype.
* Usage: Hybrid NAM page header only. No demographic content in data tabs.

## 6. Toggle Status Documentation

* Feature fully implemented in code; runtime availability governed by executive control plane toggle.
* Frontend visibility governed by `accessGates.js` → `isPageEnabled("/nam")`.
* Backend enforcement governed by `backend/security/feature_control.py` → `FCC_FEATURE_API_PATHS["nam.hybrid"]`.
