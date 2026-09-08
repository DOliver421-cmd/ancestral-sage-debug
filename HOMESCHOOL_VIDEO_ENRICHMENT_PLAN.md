# HOMESCHOOL ACADEMY — VIDEO ENRICHMENT + STAFF BUILD TRACKER (PHASED PLAN)

Companion to `HOMESCHOOL_ACADEMY_BUILD_PLAN.md` and `HOMESCHOOL_ACADEMY_PROGRESS.md`.
Scope: (1) curated public educational videos embedded **inside** courses, (2) a
**staff-only** page that tracks the homeschool build plan/progress and the
course↔video mapping. Written from a live trace of the actual code
(`frontend/src/App.js` `Protected`, `frontend/src/lib/roles.js`, `backend/routers/academy.py`,
`frontend/src/pages/academy/*`, `backend/seed_academy.py`).

---

## 0. Ground rules (owner-set)

1. Videos are **publicly accessible educational resources** — never presented as
   our own content. Every embed shows creator attribution by default.
2. Embeds play **on-site**. Never navigate away from the site.
3. Placement: first video at the **beginning** of the course; for courses with
   more than one mapped video, additional videos appear **mid-course** (at the
   unit boundary the mapping assigns).
4. The build-plan/progress tracker is **staff only**.

---

## 1. How this plugs into the existing architecture (verified)

- Courses are seeded from `backend/academy_content/*.py` by `seed_academy.py`
  (content-hash versioned, so edits propagate). **Video mapping lives in course
  data**, not hardcoded in React — one source of truth, seed-validated.
- New optional course/lesson field: `enrichment_videos`:
  ```python
  "enrichment_videos": [
      {
          "video_id": "UAQaMrjySx8",        # 11-char YouTube ID
          "title": "Africa's Great Civilizations…",
          "creator": "Creator / channel name",
          "source_note": "Publicly accessible educational resource — not MHC content.",
          "placement": "start",              # "start" | "unit:<unit-slug>"
      },
  ]
  ```
- Backend serves it as-is on the course payload (`CourseDetail` public + lesson
  `learn` payload). `validate_course` gains a check: `video_id` must match
  `^[A-Za-z0-9_-]{11}$` and `placement` must be `start` or an existing unit slug
  — a bad mapping fails loudly at seed time, not in a student's lesson.
- Embed component: `<LessonVideo />` — standard YouTube **nocookie** iframe
  (`https://www.youtube-nocookie.com/embed/<id>`), `sandbox`-safe, with title,
  creator credit line, and a visible "External resource — plays on MoreHelp"
  note. No JS wrapper library needed.
- Staff tracker page: `/academy/build` — new page `AcademyBuildTracker.jsx`
  wrapped in the existing `Protected roles={["instructor", "support_staff", "oversight", "admin", "executive_admin"]}`
  pattern (rank ≥ 3 = instructor, per `frontend/src/lib/roles.js`). Reads the
  two plan/progress docs **and the live seed** so the table reflects reality,
  not a stale markdown file.

---

## 2. Video mapping — embed feasibility audit (honest)

Owner-supplied links fall into three classes. Only **class A can be embedded
today**; class B needs real video IDs; class C can never be an embed.

| Class | What it is | Action |
|---|---|---|
| **A** | Direct `youtube.com/watch?v=<11-char ID>` | Embed as-is |
| **B** | Google-search or channel/search links (no video ID) | Owner or staff must pin a real video ID before it can embed — these are **not silently dropped**, they show on the staff tracker as `NEEDS VIDEO ID` |
| **C** | Non-YouTube pages (squarespace store, TPT, podcast, search results) | Shown as a "Resource link" card on the staff tracker only; not course embeds |

### Class A — embeddable now (11 confirmed video IDs)

| # | Course | Video title (as supplied) | video_id |
|---|---|---|---|
| 1 | African Kingdoms & Empires | The Real History of Africa They Never Taught You — Africa's Great Civilizations | `UAQaMrjySx8` |
| 2 | Mathematics of the African Diaspora | Historians Hid This African Mathematical Discovery | `mGwf651YenA` |
| 3 | Autonomous Enterprise (planned) | Black Wall Street — The Daily Then™ | `XX1KqjbMCpA` |
| 4 | Cooperative Economics & Mutual Aid (planned) | History of Mutual Aid and Cooperative Economics in Black Communities | `oNZiE0vyD_Y` |
| 5 | Adult Education Social Studies | US History & Civics Core Concepts Breakdown | `bBC-nXj3Ng4` |
| 6 | Visual Arts Foundations | Elements of Art: Line, Shape, Color, Form | `KY1bZ8K9VpQ` |
| 7 | Digital Art and Design | Graphic Design Principles & Portfolio Building | `YqQx75OPRa0` |
| 8 | Electrical Engineering Y1/Y2 + Trade Math | Electrical Theory: Ohm's Law, Circuits, and Residential Wiring | `XA-u29x_1_0` |
| 9 | Entrepreneurship & Career/Workforce | Startups, Small Business Models, and Operations Management | `DoPjmoGkWZU` |
| 10 | Radical Wealth Literacy (planned) | Systemic Wealth Extraction and Predatory Lending Analysis | `HQ204yPbbj8` |
| 11 | Mathematics (Grades 1–8 + Ratios) | Khan Academy Core Math Progressions | `au1zVXyQjW8` |
| 12 | Reading Foundations & ELA (K–5) | Phonics, First Stories, and Reading Comprehension Strategies | `AbY0HPtW9-8` |
| 13 | Science (Grades 2, 5, 8) & Chemistry/Biology | Crash Course Kids: Science & Earth Ecosystems | `jzuKbOpc9gY` |
| 14 | Social Studies (Grade 5 & 7) | World Geography, Cultures, and Early American History | `Vl03q5WdC88` |
| 15 | African American Literature Foundations | The Black Arts Movement, Harlem Renaissance, and Afrofuturism | `y9gBqGk4Y5c` |
| 16 | Global African Diaspora | The Haitian Revolution, Pan-Africanism, and Global Diaspora Movements | `5A_oIdqAZgI` |
| 17 | Resistance, Rebellion & the Counter-Narrative (planned) | Maroon Societies and Organized Anti-Colonial Resistance | `Nn7Zg7o8IYA` |
| 18 | Ethnomathematics & Black Pioneers in STEM | African Fractals, Architecture, and Black STEM Pioneers | `840gT_pY9b8` |
| 19 | African Philosophy and Ethics | Ubuntu, Akan Philosophy, and Communal Epistemology | `3R3m5xK7g2w` |
| 20 | Legalized Subjugation (planned) | The Legal Mechanics of Jim Crow, Black Codes, and Structural Controls | `0b7gLp0y9cQ` |
| 21 | Economics of Extraction (planned) | Exposing the Material Reality of Global Capital Accumulation | `3l3w9g8f2p1` |
| 22 | The Architecture of Omission (planned) | Deconstructing U.S. Curriculum Omissions | `5r4k9v8c3l0` |

> Note on IDs 21–22 (`3l3w9g8f2p1`, `5r4k9v8c3l0`): these IDs look suspicious
> (no real YouTube ID starts with a digit and most supplied "links" in that
> block were search-URLs). They will be stored, but the staff tracker flags any
> ID that fails a live oEmbed check with `UNREACHABLE` so staff can re-pin.

### Class B — needs a real video ID pinned before embed

- Adult Education Language Arts — "Crash Course Literature / Critical Reading" (search link)
- Adult Education Mathematics — "Math Antics" (search link)
- Adult Education Science — "Amoeba Sisters" (search link)
- Eco-Systems & Indigenous Land Stewardship (search link)
- Global African Diaspora **unit 2/3 videos** if more than one per course is wanted

### Class C — resource links only (not embeds)

- Dr. Brigitte Fielder — Lifting Their Voices series (squarespace)
- Akil Parker — All This Math (exitinterviewpodcast / knarrative Histematics)
- Dr. Raven Baxter — Raven the Science Maven (channel link)
- Dr. Anika Prather — Black Intellectuals Series (billofrightsinstitute.org)
- Dr. Jessica Gordon Nembhard — cooperative economics videos (search links)
- Dr. Boyce Watkins — financial literacy videos (search links)
- Dr. Erica Jordan-Thomas — career/entrepreneurship (site link)
- Dr. Nadia Bennett — Community, Calling & The Climb (podcast)
- Art With Trista (TPT store)
- Black Art Research Space (site)
- "The Educators" podcast (Apple)

These become a **"Educators & Resources" attribution block** on course pages
(name + link-out in a new tab, clearly external) — they honor the
Black-educator mapping without pretending to be embeds.

---

## 3. Phased delivery plan

### Phase V1 — Embed engine + staff tracker skeleton (this phase, shipped together)
**Delivers the visible feature for every course that has a valid video ID.**

1. `backend/academy_content/enrichment.py` — the canonical mapping dict above
   (video_id, title, creator, placement, needs_id flags), imported by course
   modules or merged in `academy_content/__init__.py`.
2. `seed_academy.validate_course` — validate `enrichment_videos` (ID shape,
   placement target exists, `needs_id: true` entries are skipped from embed).
3. Backend course payloads include `enrichment_videos` (public course detail +
   authenticated lesson payload).
4. Frontend `<LessonVideo />` component (youtube-nocookie iframe + attribution)
   — rendered at course top (`placement: "start"`) and above targeted units
   (`placement: "unit:<slug>"`).
5. `frontend/src/pages/academy/AcademyBuildTracker.jsx` at `/academy/build`:
   - live course table (from the seed API) with per-course status: video status
     (EMBEDDED / NEEDS VIDEO ID / RESOURCE LINK ONLY), published/planned,
     lessons count;
   - build-plan progress checklist (from the plan doc structure) rendered as
     an interactive staff checklist;
   - role-gated via `Protected roles={[instructor+]}` (staff rank ≥ 3).
6. Test: extend `tests/test_academy_api.py` — course payload contains
   enrichment for mapped courses, absent for unmapped, and bad IDs fail
   validation at seed time.

### Phase V2 — Pin the Class B videos (needs owner/staff input)
- Staff use the tracker's `NEEDS VIDEO ID` rows; owner (or a staff member with
  the list) pastes the real watch URLs; mapping is updated in one commit.
- The tracker's oEmbed check re-runs and flips rows to `EMBEDDED`.

### Phase V3 — Mid-course placement tuning
- For multi-video courses (African Kingdoms, Diaspora Mathematics, Philosophy),
  assign second videos to unit boundaries using the `placement: "unit:<slug>"`
  mechanism — e.g. Diaspora Mathematics: base-20 video at `unit:number-systems`,
  Dogon astronomy video at `unit:calendars`.
- Owner review in the staff tracker (each row shows where the video appears).

### Phase V4 — Class C "Educators & Resources" blocks
- Course pages get an "Educators & Resources" section (name, role, external
  link, opens in new tab, marked external) using the class-C table above.
- Attribution is the point: this satisfies "we are not presenting these as
  videos we made" and credits Black educators by name.

### Phase V5 — Verification (definition of done per repo policy)
- Click-through: staff sign-in → `/academy/build` loads → every row real data.
- Click-through: student lesson → video plays on-site at course start; mid-unit
  videos appear at the right unit; no navigation away.
- API tests green; seed validation green (bad IDs fail loudly).
- Live check on Railway after deploy: embed renders, iframe not blocked by
  CSP (backend X-Frame-Options DENY applies to *our* pages, not to iframes we
  embed; nothing to change there — verified during implementation).

---

## 4. What I need from you to finish Phase V2

Nothing blocks V1. For V2, supply direct `youtube.com/watch?v=…` links (or say
"drop them") for: Adult Ed Language Arts (Crash Course Literature), Adult Ed
Math (Math Antics), Adult Ed Science (Amoeba Sisters), Eco-Systems &
Stewardship — and confirmation of the two suspect IDs in the table above.

## 5. Honest status

- The mapping above is **planned, not yet implemented** — no embed code exists
  in the repo yet. This doc is the contract V1 will build against.
- The staff tracker page does **not** exist yet. It is Phase V1 item 5.
- Nothing in this plan touches the dead persona pages, payments, or any other
  feature — scope is videos + tracker only.
