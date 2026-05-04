# LCE-WAI Training Platform — PRD

## Original Problem Statement
Full-stack training application for the Lightning City Electric Workforce & Apprenticeship Institute (LCE-WAI). Electrical apprenticeship training, 12-project Camper-to-Classroom curriculum, safety/solar/off-grid modules, student progress, instructor tools, assessments, certifications. Must serve youth, adults, returning citizens, and workforce trainees. Faith-forward + safety + hands-on.

User-added follow-up scope:
- Rename "Cohort" → "Associate" everywhere.
- Add a complete Electrical Apprentice Lab Module System with both online simulations (9) and in-person real-world labs (12), a Competency Matrix (8 areas), skill points/badges, and an Instructor Lab Approval Panel.

## User Choices (confirmed)
- Auth: JWT with email/password (Admin/Instructor/Student roles)
- AI: Claude Sonnet 4.5 via Emergent LLM key
- MVP: Full platform (all dashboards + all 12 modules + certificates)
- Certificates: Downloadable PDFs
- Design: Industrial trade-school (ink #0B203F, bone #F7F7F5, copper #C96A35, signal yellow #FFD100, Cabinet Grotesk + IBM Plex Sans)

## Architecture
- Backend: FastAPI + MongoDB (motor), JWT auth (pyjwt + passlib bcrypt), emergentintegrations for Claude Sonnet 4.5, ReportLab for certificates
- Frontend: React 19 + React Router + Tailwind + shadcn/ui + sonner + lucide-react
- Seed on startup: 12 modules, 9 online labs, 12 in-person labs, 8 competencies, 3 demo users

## Implemented (Feb 2026)
### Iteration 3 — PWA + Adaptive + Compliance + Admin Tools + AI Modes (May 2026)
- **PWA installable** — `/manifest.json` (W.A.I. icons, theme #0B203F, display:standalone), service worker at `/sw.js` (cache-first static, network-only API), index.html meta tags + apple-touch-icon, sw registered in index.js. Installable on Android (Chrome → Add to Home screen) and Desktop (install icon in URL bar).
- **Adaptive Learning Engine** at `/adaptive` and `/api/adaptive/me`: skill heatmap across 8 competencies (hot/warm/cold), top 3 weak areas, 4 lab/module/AI recommendations, prerequisite-locked labs (battery-inverter requires solar-charge-controller; loto-real-equipment requires loto-scenario).
- **4 Compliance Modules** in separate `compliance_modules` collection: OSHA 10 Electrical (36mo expiry), NFPA 70E Awareness (12mo), PPE Selection & Fitting (12mo), LOTO Certification (6mo, 80% pass). Auto-issues credentials.
- **Program-Level Admin Tools** at `/admin/tools`: 3 sites + 15 inventory items seeded. Admins can create sites, view inventory by site, instructors+admins can check out/return tools with quantity tracking.
- **AI Tutor expanded** with 2 new modes — `nec_lookup` (NEC article + plain-English summary + jurisdiction reminder) and `blueprint` (structured Circuits/Panels/Concerns analysis from a plan description).

### Iteration 2 — W.A.I. Rebrand + Credentialing + Portfolio (May 2026)
- Rebranded from "Lightning City Electric" to **W.A.I. — Workforce Apprentice Institute** (LCE-WAI partner program subtitle). New logo applied in Landing, Login, Register, sidebar, and footer. Color accent shifted from copper #C96A35 to W.A.I. blue #1E5BA8.
- **14 Digital Credentials** (OpenBadges v2 compatible): 3 level badges, 1 capstone, 6 skill badges tied to competencies, 4 compliance badges (LOTO 6mo, OSHA 10 36mo, NFPA 70E 12mo, Safety/PPE 12mo) + Solar Installer L1. Public manifest + assertion JSON endpoints.
- **Auto-award engine** — credentials issued automatically when triggers match (module completion, lab pass/approval, competency threshold, program complete). Runs on quiz submit, lab submit, lab review, and /credentials/me page load.
- **Portfolio Builder** at `/portfolio`: aggregates user profile, modules, labs, evaluations, credentials, competency matrix. Publish toggle creates shareable `/p/{slug}` public route (no auth, no email leak). Multi-page PDF export via ReportLab.
- **Frontend**: New pages Credentials.jsx, Portfolio.jsx, PublicPortfolio.jsx + shared PortfolioBody component. Student nav now includes Credentials + Portfolio items.

### Iteration 1 — MVP (Feb 2026)
### Backend routes (all /api)
- Auth: /auth/register, /auth/login, /auth/me
- Curriculum: /modules, /modules/{slug}
- Progress: /progress/me, /progress/start, /progress/quiz (auto-grades, 70%+ completes)
- Labs: /labs (optional ?track=), /labs/{slug}, /labs/{slug}/submit (auto-grade online, pending inperson)
- Labs meta: /labs/submissions/me, /competencies
- Instructor: /roster, /instructor/submissions, /instructor/submissions/{id}/review, /instructor/lab-report
- Admin: /admin/stats, /admin/users, /admin/associate
- AI: /ai/chat (Claude Sonnet 4.5, 4 modes: tutor/scripture/explain/quiz_gen), /ai/history/{session}
- Certs: /certificates/me, /certificates/{slug}.pdf?token= (JWT query auth)

### 9 Online Simulators (auto-graded)
basic-circuit-sim, switch-wiring-sim, panel-labeling-sim, conduit-bending-calc, voltage-drop-calc, solar-config-sim, loto-scenario, troubleshooting-sim, load-balancing-sim

### 12 In-Person Labs (photo URL + notes, instructor approval)
emt-conduit-install, switch-loop-wiring, three-four-way-circuit, load-center-install, breaker-termination, gfci-afci-install, branch-circuit-build, continuity-voltage-test, solar-charge-controller, solar-panel-mount, battery-inverter-build, loto-real-equipment

### 8 Competencies
wiring-fundamentals, safety-ppe, tools-equipment, conduit-bending, panels-breakers, troubleshooting, solar-off-grid, professionalism. Badge at 100 skill points.

### Frontend pages
Landing, Login, Register, StudentDashboard, InstructorDashboard, AdminDashboard, ModulesList, ModuleView, LabsHub, LabDetail (with 9 simulators), InstructorLabs (approvals + lab report CSV), Competencies, AITutor, Certificates, LabSimulations (legacy preview).

## Test Credentials
admin@lcewai.org / Admin@LCE2026
instructor@lcewai.org / Teach@LCE2026 (Associate-Alpha)
student@lcewai.org / Learn@LCE2026 (Associate-Alpha)

## Test Results (iteration 1)
Backend: 34/34 pytest passing (100%). Frontend: all critical flows verified. No critical bugs.

## Backlog / Next Actions
- P1: Real file upload for in-person lab photos (currently URL string). Integrate object storage playbook.
- P1: Richer interactive simulators (SVG wiring drag-and-drop instead of form-based).
- P1: Email notifications on lab approval/rejection (Resend or SendGrid).
- P2: Instructor can unlock/lock modules per student.
- P2: Video lesson uploads per module.
- P2: Mobile-optimized lab checklist with camera capture.
- P2: Scripture library curation panel for admin.
- P3: Electron desktop wrapper (app is already responsive web).
