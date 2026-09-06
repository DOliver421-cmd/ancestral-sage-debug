# HOMESCHOOL ACADEMY — MHC V1 BUILD STATUS (PROGRESS TRACKER)

Companion to `HOMESCHOOL_ACADEMY_BUILD_PLAN.md`. Statuses: **NOT STARTED** ·
**IN PROGRESS** · **BLOCKED** · **COMPLETE**. Updated as work progresses. A row is
COMPLETE only per the Definition of Complete in the build plan (code + route + UI +
API + persistence + permissions + real content + tested + docs).

## PHASE 1 — DISCOVERY
- [x] Existing architecture mapped (FastAPI monolith + modular routers, MongoDB, React SPA)
- [x] Existing LMS mapped (`db.modules` trade catalog, module quizzes at 70%, `db.progress`)
- [x] Existing authentication mapped (JWT bearer, 8-rank role ladder, `current_user` dependency)
- [x] Existing AI mapped (`/api/ai/chat` gateway, member-gated AI Tutor, FCC `ai_chat` flag)
- [x] Existing admin mapped (large existing admin/exec surfaces — avoid a second admin system)
- [x] Existing curriculum/content systems mapped (seed-driven startup seeding pattern)
- [x] Implementation matrix written (BUILD_PLAN §2)

## PHASE 2 — ACADEMY GATEWAY
- [x] `/wai-institute` rebuilt as the Academy gateway (Homeschool, done right.)
- [x] Academy landing experience (tracks, features, 3-step model, live vs planned honesty)
- [x] Curriculum entry points (explorer + course pages)
- [x] WAI Institute bridge (www.wai-institute.org next-step section; no false integration claims)

## PHASE 3 — CURRICULUM
- [x] Tracks (Foundations K–8 · Builder/Trade · Artist · Scholar)
- [x] Grades (K–12) and applicability rules
- [x] Subjects (ELA, Math, Science, Social Studies, trade/art)
- [x] Courses (catalog architecture + published/planned status)
- [x] Course descriptions + learning objectives (all published courses)
- [x] Units & lessons (real lesson trees)
- [x] Assessments (per-lesson knowledge checks with explanations)
- [ ] Full K–12 content population (PLANNED catalog remains until owner spec supplied)

## PHASE 4 — LEARNING ENGINE
- [x] Student enrollment (auto by grade+track on profile create; parent-managed)
- [x] Lesson progression (sequence: learn → check → score → next)
- [x] 80% mastery gate (configurable `passing_score`, default 80)
- [x] Retry / remediation (explanations after failure; unlimited attempts; best kept)
- [x] Progress persistence (`db.academy_progress` per student/lesson)
- [x] Server-side unlock enforcement (locked lessons return 403 — UI cannot bypass)

## PHASE 5 — STUDENT
- [x] Student dashboard (“What do I do next?”, current lesson, progress, mastery)
- [x] Course experience (units/lessons listing, per-lesson status)
- [x] Lesson experience (instructional material + examples/activities)
- [x] Assessments (knowledge check UI + instant feedback)
- [x] Progress display (bars, counts, mastery scores)

## PHASE 6 — PARENT
- [x] Student profiles (name, grade, track; add/archive/edit; owner-scoped)
- [x] Parent dashboard (student cards, progress summaries, controls)
- [x] Progress monitoring (per-course completion, mastery averages)
- [x] Records / transcripts (printable student educational records page; no legal claims)

## PHASE 7 — AI
- [x] Existing AI gateway integrated (lesson Coach calls existing `/api/ai/chat`)
- [x] Learning assistance (explain/examples/guided practice prompt contract)
- [ ] Mastery-safe behavior verified live with a provider key (server enforces the
      same member/key policy as AI Tutor; coach prompt forbids handing over the answer;
      UI degrades gracefully when the gateway is unavailable)

## PHASE 8 — ADMIN
- [ ] Curriculum management (deferred by design — seed-driven content in v1; see build plan §10)
- [ ] Lesson management (deferred)
- [ ] Assessment management (deferred)
- [ ] Progress administration (deferred)

## PHASE 9 — QA
- [ ] Desktop manual pass (owner/preview)
- [ ] Mobile manual pass (owner/preview)
- [x] Authentication checks on academy routes (Protected wrapper + owner-scoped API)
- [x] Parent/student permission tests (backend pytest: cross-account access denied)
- [x] Progress persistence tests (backend pytest, in-memory DB)
- [x] Mastery enforcement tests (backend pytest: 80% pass/unlock, retry, locked 403)
- [x] API route tests (backend pytest: catalog/content gating, records shape)
- [x] Broken-route check (frontend production build + `route-integrity`/`nav-integrity` scripts pass)
- [ ] Security review (owner: session/role review of new endpoints before live launch)

### Verification log (this build pass)
- `backend`: `python3 -m pytest tests/test_academy_api.py` → 15 passed (ownership,
  catalog/content gating, enrollment applicability, unlock chain, 80% mastery,
  retry/best-score, records). `tests/test_router_completion.py` + related LMS/RBAC
  suites also green (34 passed). FCC-wiring suites that fail in this sandbox fail on
  async-fixture support, independent of these changes.
- `frontend`: `CI=false npx craco build` passes; `scripts/route-integrity.js` and
  `scripts/nav-integrity.js` pass.
- Content: `python3 -m seed_academy` → 24 courses valid (5 published, 19 planned).

### Verification pass 2026-09-06 (this session — proceed-on-plan review)
- Re-ran the academy suite after fixes: **16 passed** (added regression: learn
  deep link without `?student=` resolves the owner's enrolled student so attempts
  never fire with a null student id — the CourseDetail → "Open course" path).
- `python3 -m seed_academy` → OK, 24 courses valid (5 published, 19 planned).
- `CI=false npx craco build` green; `route-integrity.js` (all links resolve, no
  dead paths) and `nav-integrity.js` green.
- **Two real frontend defects found by review and fixed:**
  1. Curriculum explorer track filter matched a course's single primary `track`,
     hiding multi-track courses (e.g. Grade 7 Math serves Foundations AND Builder)
     from the spec's "Grade 7 → Builder → Mathematics" filter. Now filters on the
     course's full `tracks` applicability list — same rule the backend/enrollment uses.
  2. `CourseDetail`'s "Open course and start lesson 1" linked to the lesson player
     without `?student=`, so an attempt submission would have sent `student_id: null`
     and failed. The lesson player now resolves the enrolled student from the learn
     payload (`data.student_id`) for submissions and navigation.
- **Still open (owner/live):** desktop + mobile manual pass in a real browser,
  security/session review of the new endpoints, and the live Railway end-to-end
  journey (register → add student → complete a lesson → dashboard → records).
  Those are Phase 9/10 items — this sandbox cannot reach them without deploy/keys,
  so they are NOT marked complete.

## PHASE 10 — V1 RELEASE
- [ ] Production testing (live Railway target: register → add student → complete a lesson)
- [ ] Content review (owner reads a lesson/course for voice, accuracy, grade fit)
- [ ] Owner review of gateway + dashboards
- [ ] Launch readiness (merge to `main` → Railway auto-deploy → live verification)

---

## Owner decisions required (see BUILD_PLAN §16)
1. Definitive Academy curriculum spec (catalog + scope & sequence) — not present in
   this checkout; catalog breadth is currently derived from the owner plan.
2. Confirm family model: one parent account + managed student profiles (no child logins).
3. AI for Academy: reuse member-gated AI Tutor gateway vs separate free quota.
4. Next content wave priority.
5. Delivery: merge to `main` (live) once preview is reviewed.
