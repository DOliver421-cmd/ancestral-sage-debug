# Homeschool Academy — issue ledger

Every item below was found by execution (running the server or rendering the
components), not by reading the code. Statuses are live.

| # | Issue | Found by | Status | PR |
|---|---|---|---|---|
| 1 | Adult tracks (life skills, leadership, career, entrepreneurship) rejected by the API — a 422 whose detail array crashed the parent dashboard | Button audit | Fixed | #469 |
| 2 | Compliance documents dropped data: quarterly report had no reporting period; Notice of Intent shipped without DOB, address, or a signature line | Button audit | Fixed | #469 |
| 3 | `/academy/records` with no `?student=` was a dead end (no student picker) | Button audit | Fixed | #469 |
| 4 | Course-page links pointed at the paid platform catalog instead of the Academy curriculum | Button audit | Fixed | #469 |
| 5 | Build-tracker back link pointed at an admin-only route, bouncing non-admin staff | Button audit | Fixed | #469 |
| 6 | Hardcoded "54 courses · 4 tracks" against a live catalog of 95/9 | Button audit | Fixed | #469 |
| 7 | `pymongo` bumped past `motor`'s support — the deploy built green and never became healthy | Running the server | Fixed | #475 |
| 8 | `grade` capped at 2 characters, so **no adult student could be created** | Running the tests | Fixed | #475 |
| 9 | Family-history projects could never be completed (artifact save replaced the whole map) | e2e run | Fixed | #476 |
| 10 | `GET /api/academy/courses/{slug}` returned 401 to anonymous visitors — the public front door was closed | e2e run | Fixed | #476 |
| 11 | `EDUCATOR_RESOURCES` (17 curated creator links) defined and never exposed to any endpoint | Feature audit | Fixed | #476 |
| 12 | Transcript GPA was a flat 4.0 for every completed course, on a document parents sign | Handbook audit | Fixed | #477 |
| 13 | The Coach's "never gives answers" promise was enforced nowhere (it ran an electrical-apprentice persona) | Handbook audit | Fixed | #477 |
| 14 | Add-student "auto-enroll" was advertised for adult tracks that the API then rejected; later fixed by #1 | Button audit | Fixed | #469 |
| 15 | **A user could not edit their own profile** — `PATCH /auth/me` worked, but the profile page had no editor for name or email | Reported by owner | Fixed | #478 |
| 16 | Elementary/middle handbooks thinnest on instruction (336 / 396 words) | Handbook audit | Fixed | #477 |
| 17 | Two `suspect` enrichment video IDs served to families as if verified | Feature audit | Fixed | #476 |
| 18 | Staff video coverage was a hardcoded mirror, misreporting coverage | Feature audit | Fixed | #476 |

## Not yet delivered (planned)

- K–8 cultural deepening for the ~35 remaining grade K–8 courses (#474 covered adult and 9–12).
- Parent/teacher review comments on projects.
- Project artifacts cited in the printed Records page.
- Co-op (shared view across two families) — the design is in the scope audit.
- Weekly parent report (email/SMS).
- Afro-Latin and Portuguese/Spanish strands — named in the original spec, still thin relative to Caribbean content.

## Runtime audit 2026-10-10 (all found by execution — see docs/RUNTIME_AUDIT_2026-10-10.md)

| # | Issue | Found by | Status | PR |
|---|---|---|---|---|
| 19 | Legal Workflow Engine "sync to account" is dead: GET returns a bare array (frontend reads `.workflows`), POST demands query params (frontend sends JSON → 422); both swallowed by `.catch(() => {})` | Live probe + jsdom render of the real component | Open | — |
| 20 | Race: concurrent course enrollment loses 1–2 of 3 enrollments, all returning 200 (read-modify-write on `course_slugs`) | 8-round concurrency loop | Open | — |
| 21 | Race: concurrent artifact saves drop earlier artifacts (4/6 rounds) and can resurrect stale values | 6-round concurrency loop | Open | — |
| 22 | Hybrid NAM knowledge seed fails 31/31 on any real DB (`if _db` truth-tests a motor Database); `nam_knowledge` empty in production; standalone "success" is the in-memory fallback | Fresh-DB cold boot + Mongo count | Open | — |
| 23 | Creator money surface ungated: free member POST `/api/creator/courses` → 201; courses/payout-profile/enrollments/me open (missing from `FEATURE_API_PATHS`) | Live probes with a free test account | Open | — |
| 24 | Tier drift: `ai_chat` frontend=member/backend=free (student got a 200 AI reply); `courses` plus/free; `resource_hub` plus/handler-member | Live probes + constants diff | Open | — |
| 25 | `PipelineManager` init fails every boot (`No module named 'src'`) — keyword fallback only | Boot log | Open | — |
| 26 | Resource Hub guides are inert rows (`in_product`/`steps` absent, `url: ""`); the "Read-only guide · no workflow" badge the owner rejected still renders | Live probe + real-component render | Open | — |
| 27 | Production masks API 404/405 with the SPA catch-all (200 HTML where local returns JSON) — probes lie | Prod-vs-local side-by-side probes | Open | — |
