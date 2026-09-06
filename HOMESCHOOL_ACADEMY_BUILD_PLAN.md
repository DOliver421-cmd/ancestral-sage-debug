# HOMESCHOOL ACADEMY — MASTER BUILD PLAN (MHC V1)

**Owner deliverable:** The WAI Institute Homeschool Academy as a working feature of
MoreHelp Center (this repository). This document is the working plan for the whole
feature. Companion tracker: `HOMESCHOOL_ACADEMY_PROGRESS.md`.

**Live target:** https://charming-analysis-morehelpcenter.up.railway.app
**Stack (verified in this checkout):** Python FastAPI monolith (`backend/server.py` +
modular routers in `backend/routers/`) with MongoDB (Motor); React SPA
(`frontend/src/`, CRA + craco, Tailwind) served by the backend.

---

## 1. Product purpose

A sequenced **K–12 + trade-track homeschool academy** for families who want real
academics, real skills, and real credentials — with full parental control. A family
(parent account + student profiles) should be able to:

> discover → enroll → select a pathway → learn → complete lessons → demonstrate
> mastery → track progress → produce records → continue into the broader WAI
> Institute experience (www.wai-institute.org).

The Academy is built **inside MoreHelp Center** so it reuses the site's existing
accounts, AI gateway, and content patterns, and positions WAI Institute as the next
step for families ready to go further.

## 2. Current MHC capabilities (implementation matrix)

| Requirement (from the spec) | Already Exists | Partial | Must Build | Reuse |
| --- | --- | --- | --- | --- |
| Accounts / auth (register, login, JWT, reset) | ✅ `routers/auth.py`, inline `server.py` | | | Accounts for parent |
| Roles / IAM (8-rank ladder) | ✅ `backend/roles.py` | | | No new site role needed — family model is app-level |
| LMS catalog (courses/modules) | ✅ `db.modules` + `/api/modules` (LCE trade) | | | Catalog patterns, public-listing gating |
| Unit → lesson structure | | ⚠️ modules have tasks/quiz, no unit/lesson tree | ✅ academy course tree | Content schema patterns |
| Real lesson content (material + checks) | ✅ LCE module quizzes | | ✅ academy lessons w/ instructional material | Authoring style, grading helpers |
| Assessments / scoring | ✅ module quiz scoring (70% pass) | | ✅ 80% mastery per lesson + retry | `score` math, attempt records |
| Lesson sequencing / unlock gating | ❌ (all modules reachable) | | ✅ previous-passed-unlocks-next | — |
| Progress persistence | ✅ `db.progress` (module level) | | ✅ `db.academy_progress` per lesson | Persistence pattern |
| Parent account + student profiles | ❌ | | ✅ `db.academy_students` under parent | — |
| Grade + track selection | ❌ | | ✅ grade (K–12) + track on profile | — |
| Student dashboard (“what do I do next?”) | ✅ `/dashboard` (trade program) | | ✅ `/academy/student/:id` | Dashboard patterns |
| Parent dashboard (“how is my child progressing?”) | ❌ | | ✅ `/academy/parent` | — |
| Curriculum explorer (grade/track/subject/keyword) | ❌ (`/courses` is flat list) | | ✅ `/academy/curriculum` | `/modules` catalog pattern |
| Transcripts / printable records | ✅ credential/portfolio PDF | | ✅ `/academy/records` (records doc, no legal claims) | PDF/print patterns |
| Certificates | ✅ (trade) | | Deferred for academy (see Deferred) | |
| AI learning assistant | ✅ `/api/ai/chat` + AI Tutor page (member-gated) | | ✅ lesson “Coach” panel reusing the gateway | AI Tutor patterns |
| Admin for curriculum management | ✅ large admin surfaces exist | | Deferred (avoid second admin system) | Admin system audit later |
| Payments / access | ✅ tiers, plans, FCC | | | FCC default allows new academy paths (free start) |
| Navigation | ✅ AppShell / PublicNav / routes registry | | ✅ add Academy links + routes | Existing nav components |
| Reusable UI | ✅ shadcn/ui + `card-flat`/`btn-*` tokens | | | Reuse heavily |

## 3. Sitemap

Public (no login):
- `/wai-institute` — Academy gateway (landing: Homeschool, done right.; tracks;
  3-step how-it-works; WAI Institute bridge). Alias of the Academy home.
- `/academy/curriculum` — Curriculum explorer (filter grade / track / subject / search).
- `/academy/courses/:slug` — Course page: description, objectives, unit/lesson list
  (metadata). Content is gated behind an enrolled family student.

Authenticated (parent account):
- `/academy/parent` — family dashboard AND the 3-step onboarding surface: step 1
  (parent account) is satisfied by signing in; step 2 is the add-a-student form
  (name + grade + track, auto-enroll; as many profiles as needed); step 3 is the
  dashboard itself — student cards, progress, records links, controls. There is
  no separate `/academy/start` route in v1.
- `/academy/student` → redirect to default (first active) student.
- `/academy/student/:studentId` — student dashboard: “What do I do next?”, active
  courses, current lesson, progress, mastery, next lessons.
- `/academy/learn/:courseSlug/:lessonSlug?student=…` — lesson player: content →
  knowledge check → score → 80% mastery → next unlocked / review+retry; AI coach.
- `/academy/records?student=…` — printable student educational records /
  progress documentation (not a legal transcript).

## 4. Feature inventory

Architecture supports (built): tracks (foundations/builder/artist/scholar), grades
K–12, subjects, published vs planned courses, courses → units → lessons → material →
knowledge check → score → progress; per-student mastery; printable records.

Initial published curriculum (real content in this repo — see §6): one full course
per coverage band the owner prioritized: K–2 ELA, 3–5 Math, 6–8 Math, 9–12 Scholar
Science (Biology), and Builder/Trade Applied Electrical Engineering Year 1
(charge & current, Ohm's law, series, parallel, safety, code).

## 5. Curriculum inventory

Tracks:
- **Foundations (K–8):** core academics, mastery-paced.
- **Builder / Trade (6–12):** trade-ready math/science plus trade courses
  (Applied Electrical Engineering Year 1 first).
- **Artist (K–12):** arts pathway (planned catalog; content expansion deferred).
- **Scholar (9–12):** college-prep academics (Biology first).

Grades: K, 1–12. Subjects: English Language Arts, Mathematics, Science,
Social Studies + trade/art as track subjects.

Course applicability rule: a course is offered to a student when
`course.published && grade in course.grades && track in course.tracks`.

## 6. Content inventory (real content in repo — not placeholders)

Content lives as **structured seed data** (Python modules under `backend/academy_content/`),
seeded idempotently into `db.academy_courses` at startup (same pattern as the existing
module seed). No component rewrites are needed to add content — add a course dict,
restart/deploy, done.

Published (fully implemented — every lesson has instructional material, worked
examples/activities, and a scored knowledge check):
1. **Reading Foundations (Grade 1 ELA)** — units: Letters & Sounds · Reading Words ·
   First Stories (9 lessons).
2. **Multiplication, Division, and Fractions (Grade 4 Math)** (10 lessons).
3. **Ratios, Proportions, and Percent (Grade 7 Math)** — serves Foundations and
   Builder tracks (8 lessons).
4. **Biology: Cells — The Building Blocks of Life (Grade 9 Scholar)** (8 lessons).
5. **Applied Electrical Engineering — Year 1 (Grades 9–12 Builder)** — charge &
   current, voltage/resistance/Ohm's law, series circuits, parallel circuits,
   power & energy, electrical safety, grounding/GFCIs/code (8 lessons).

Planned (registered in the catalog with honest **PLANNED** labels — never presented
as complete): additional Foundations ELA/Math/Science/Social Studies across grades,
the Artist pathway, more Scholar electives, Electrical Year 2+, and trade expansion
(see `OWNER DECISIONS REQUIRED` + tracker).

## 7. Technical architecture

- **DB collections:** `academy_courses` (course tree incl. lessons + checks),
  `academy_students` (profile under parent `parent_user_id`),
  `academy_progress` (attempts & mastery per student/lesson).
  No separate enrollment collection: enrollment is a managed `course_slugs` array on
  the student doc, auto-populated from applicability when the profile is created or
  its grade/track changes.
- **Backend:** `backend/routers/academy.py` (modular router, mounted like the other
  `_ADDITIONAL_API_ROUTER_MODULES` routers and auto-bound by `_bind_router_dependencies`).
  Startup seeding via `seed_academy(db)` alongside the existing startup seeds.
- **API (all under `/api/academy`):** public course catalog/detail (metadata only);
  student CRUD + enroll/unenroll (owner-scoped); dashboard; learn payload (content
  only for owned, enrolled students); attempt grading + unlock; records.
- **Mastery:** passing threshold `80%` per lesson (course-level configurable
  `passing_score`, default 80). Lesson unlocked = first lesson, or previous lesson
  passed. Attempts persist; best score kept; retries allowed until passed; passed
  lessons cannot be un-passed. Server enforces locked lessons (403) — the UI cannot
  bypass the sequence.
- **Frontend:** new pages under `frontend/src/pages/academy/`, routes in `App.js`,
  existing `Protected` wrapper + `api` axios client + Tailwind tokens.
- **AI:** lesson “Coach” reuses the existing `/api/ai/chat` surface (same member /
  key policy the AI Tutor page already enforces). Coach prompt contract: explain,
  give examples, guide — never hand over the answer to the current knowledge check.
  When the gateway is unavailable (no provider key / not a member) the panel says so
  and stays out of the way; mastery gating is unaffected.
- **Permissions:** a student profile belongs to exactly one account
  (`parent_user_id = current user`). No new site-wide role was added — the site role
  ladder is untouched. Instructor/admin review surfaces are deferred to a later phase.

## 8. Parent experience (v1)

Add students (name + grade + track) → auto-enroll published courses that match →
see each child's courses, % complete, mastery averages, next lesson → open the child
dashboard or a specific course → print student records. Parent (owner) controls:
add/archive students, change grade/track (re-enrolls), enroll/unenroll courses.

## 9. Student experience (v1)

Open dashboard → see active courses + “Continue where you left off” → lesson player:
read/learn → practice → knowledge check → instant score → ≥80%: lesson complete, next
lesson unlocks (→ course complete at the end) · <80%: review explanations, retry.
Progress persists per lesson and is visible to the parent.

## 10. Admin experience

**Deferred by design** (Phase 8 in tracker). The site already has a large admin
surface; we deliberately do not build a second admin system in v1. Curriculum is
seed-driven (documented above) so admins/owners can ship content by adding structured
data. A dedicated curriculum-management admin (tracks/grades/courses/lessons/
assessments/thresholds/visibility) is recorded as a later phase against the existing
admin system.

## 11. Implementation phases (mirrors `HOMESCHOOL_ACADEMY_PROGRESS.md`)

1. Discovery (mapping) — done in-repo this pass.
2. Academy gateway + landing.
3. Curriculum architecture + starter content (real).
4. Learning engine (enroll, progression, 80% mastery, retry, persistence).
5. Student experience (dashboard, course, lesson, assessment, progress).
6. Parent experience (profiles, dashboard, monitoring, records).
7. AI assistance (gateway reuse, mastery-safe coach).
8. Admin (deferred → existing admin system).
9. QA (desktop/mobile, auth, permissions, persistence, mastery, API, broken routes,
   security review).
10. V1 release (production testing, content review, owner review, launch readiness).

## 12. Testing requirements

- Backend: pytest suite for the academy router with in-memory fake DB (pattern:
  `tests/test_academy_api.py`): catalog gating, content gating, ownership,
  enrollment applicability, unlock chain, 80% mastery pass/retry, records.
- Frontend: full production build (`craco build`) must pass; route-integrity script.
- Live (owner): real register → add student → complete a lesson against the Railway
  target, then verify parent dashboard + records (see tracker Phase 9/10).

## 13. Risks

- **Content breadth vs depth:** v1 ships depth on 5 courses and honest PLANNED labels
  elsewhere — never fake completeness (per §8 of the owner's plan).
- **AI availability:** the platform AI is fail-closed without provider keys; coach
  must degrade gracefully and never become a mastery bypass.
- **Scope of “records”:** presented as educational records / progress documentation;
  no universal legal or accreditation claims.
- **Existing app fragility:** the SPA/backend are large; changes are additive
  (new router, new routes, new collections) and avoid touching working surfaces.

## 14. Open questions

1. Where is the owner's full “supplied Academy specification/content” (course
   catalog, per-grade/track scope & sequence)? It is **not present** in this
   checkout or environment. Until it arrives, catalog breadth is derived from the
   owner plan + industry-standard scope, and anything not yet authored is marked
   PLANNED rather than invented as complete.
2. Which published content does the owner want first in production: the v1 five-course
   starter above, or a different slice?

## 15. Deferred work

- Artist pathway content; Foundations Social Studies content beyond structure;
  Scholar electives beyond Biology; Electrical Year 2+; certificate generation for
  Academy courses; admin curriculum-management UI; per-course scheduling/calendars;
  multi-teacher/instructor review; email notifications; mobile-app polish.
- Full K–12 catalog population to match the owner's definitive spec once supplied.

## 16. Owner decisions required

1. **Provide the definitive Academy curriculum spec** (tracks, grades, course list,
   scope & sequence, learning objectives per course) so catalog/content can be
   expanded to match it exactly.
2. **Grade/track model:** one parent account managing student profiles (no login for
   children) — confirm this is the intended family model for v1.
3. **AI for Academy:** reuse the member-gated AI Tutor surface as the lesson Coach
   (recommended) vs. a separate free academy quota.
4. **Content priority order** for the next expansion wave.
5. **Delivery:** whether this branch should be merged to `main` (Railway auto-deploy)
   and verified live once the owner has reviewed the preview.

## 17. Definition of complete (how statuses are recorded)

A feature is COMPLETE in the tracker only when: code exists · route works · UI works ·
API works · data persists · permissions hold · real content exists · tested ·
documentation updated. Anything less is IN PROGRESS / BLOCKED / NOT STARTED and is
labelled exactly that way.
