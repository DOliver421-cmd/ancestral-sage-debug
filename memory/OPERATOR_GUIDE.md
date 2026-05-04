# W.A.I. — Workforce Apprentice Institute
## Complete Operator Setup & Management Guide

**App URL (preview/production):** `https://apprentice-academy.preview.emergentagent.com`
**Login page:** `…/login`  •  **Register page:** `…/register`

---

## 1. Become the Administrator (First-Time Setup)

The system seeds three demo accounts on first backend startup. Use the seeded admin to bootstrap; then create your own permanent admin and disable/repurpose the demo.

### Step 1 — Sign in as the seeded Admin
1. Open the app URL → click **Login**.
2. Email: `admin@lcewai.org`
3. Password: `Admin@LCE2026`
4. You will land on the **Admin Dashboard**.

### Step 2 — Create your personal admin account
You have two paths:

**Path A — Self-register, then promote (recommended)**
1. Log out of the demo admin.
2. Click **Register** → fill name, email (use your real address), password, choose role *Student* temporarily (registration only allows student/instructor self-signup for safety).
3. Log back in as the demo admin (`admin@lcewai.org`).
4. Open **Admin → Users** (`/admin/users`).
5. Find your account, click **Promote → Admin**. You are now a permanent admin.
6. Log out, log back in with your own email.

**Path B — Direct DB bootstrap (only if needed)**
Run from the server: `POST /api/auth/register` with `{role:"admin"}` while no admin exists, OR ask me to add a one-time `make-admin` CLI script.

### Step 3 — Lock down the demo accounts
Once your real admin works:
- **Admin → Users** → open `admin@lcewai.org` → either delete OR change password and store it offline as the break-glass account.
- Same for `instructor@lcewai.org` and `student@lcewai.org` (or keep them as sandbox accounts for training).

### Step 4 — Set your Associate (cohort) names
- **Admin → Users → Associate Manager** (`/admin/associate`).
- Default seeded value: `Associate-Alpha`. Add new ones such as `Associate-Beta-2026`, `Veterans-Cohort-Q3`, etc.
- Every student/instructor must belong to one Associate. Reassign in bulk from this page.

---

## 2. Admin Capabilities & Where to Find Them

| Area | Path | What you can do |
|---|---|---|
| Dashboard | `/admin` | Top-level KPIs, totals, quick links |
| Users | `/admin/users` | Create, promote/demote, change Associate, deactivate |
| Associates (Cohorts) | `/admin/associate` | Add/rename/assign cohort groups |
| Sites & Locations | `/admin/tools` → **Sites** | Add classrooms / training yards / partner sites |
| Tool Inventory | `/admin/tools` → **Inventory** | Add tools, set quantity, assign to site |
| Tool Checkouts | `/admin/tools` → **Checkouts** | View/approve/return tool loans |
| Program Analytics | `/admin/analytics` | Heatmaps, completion rates, expiring credentials |
| Audit Log | `/admin/audit` | Every privileged action (login, lab review, incident, etc.) |
| Incident Reports | `/incidents` | Review safety incidents, mark resolved |
| Attendance | `/attendance` | Same view as instructor + global |
| AI Tutor / NEC | `/ai-tutor` | All 6 modes (Tutor, Scripture, Explain, Quiz Gen, NEC Lookup, Blueprint Reader) |
| API Docs (Swagger) | `/api/docs` | Live endpoint testing for engineers |

---

## 3. Adding & Managing Sites (Multi-Location)

W.A.I. supports multiple physical training sites (campus, satellite locations, partner shops).

1. Go to **Admin → Tools → Sites tab**.
2. Click **+ Add Site** → enter:
   - Name (e.g., `Detroit Main Campus`)
   - Address / city / state
   - Site contact (optional)
3. Save. The site immediately becomes selectable when:
   - Adding inventory
   - Reporting an incident
   - Logging in-person lab attendance
4. To rename or retire a site, open it from the same page and edit. Inventory tied to a retired site stays linked for audit history.

---

## 4. Onboarding Instructors

### Option A — Instructor self-registers
1. Send them the link `…/register`.
2. They choose **Instructor**, enter Associate (you provide them the exact Associate code, e.g., `Associate-Beta-2026`).
3. Admin verifies in **Users** page → confirms role.

### Option B — Admin creates the account
1. **Admin → Users → + New User**.
2. Email, temp password, role = `Instructor`, Associate = chosen cohort.
3. Send the temp password securely; instructor changes it on first login.

### What instructors can do
| Path | Capability |
|---|---|
| `/instructor` | Dashboard with roster KPIs |
| `/roster` (or instructor dashboard) | View all students in their Associate |
| `/instructor/labs` | Approve / reject in-person lab submissions, leave notes |
| `/attendance` | Mark present/absent/tardy/excused per day per student |
| `/instructor/lab-report` | Download CSV of lab activity |
| `/incidents` | File incident reports (with photo URL, severity) |
| `/ai-tutor` | All AI modes for lesson prep |

---

## 5. Onboarding Students

### Bulk method (preferred for a class)
1. Create the Associate first (`/admin/associate` → e.g., `Associate-Spring-2026`).
2. Email the cohort the registration link with the exact Associate code.
3. Students self-register, choose role **Student**, paste the Associate code.
4. Instructor confirms roster at `/roster`.

### Individual method
- Same as Option B for instructors but role = `Student`.

### What students see/do
| Path | Capability |
|---|---|
| `/student` | Dashboard: progress, next module, weak competencies |
| `/modules` | 12 Camper-to-Classroom modules + quizzes |
| `/labs` | 21 labs (9 online simulators + 12 in-person) |
| `/compliance` | OSHA 10, NFPA 70E, PPE, LOTO certifications |
| `/credentials` | Earned digital badges (OpenBadges) |
| `/portfolio` | Public portfolio toggle + PDF export |
| `/adaptive` | Personalized weak-area recommendations |
| `/ai-tutor` | Tutor / Scripture / Explain modes |
| `/certificates` | Downloadable PDF certificates |

---

## 6. Daily Operating Workflow

**Morning (Instructor)**
1. Open `/attendance` → mark today's roster.
2. Open `/instructor/labs` → review any submissions queued overnight.

**During class**
- Students complete modules → quizzes auto-grade at 70%+.
- Online lab simulators auto-grade and award skill points.
- In-person labs require instructor approval (with photo URL + notes).
- Any safety event → file at `/incidents` immediately.

**End of day (Admin)**
- `/admin/audit` — scan privileged actions.
- `/admin/analytics` — verify completion KPIs.
- `/incidents` — resolve any open items.

---

## 7. Credentials, Certificates & Portfolios

- **Auto-award engine** runs on every quiz submission, lab submission, and lab review. No manual issuance needed.
- Compliance badges have expiry windows — the system auto-emails (in-app notification today) at 30-days-to-expire.
- Each student can publish a public portfolio at `/p/{their-slug}` — share the link with employers.
- Multi-page PDF export is at `/portfolio/export.pdf` (student-side button).

---

## 8. AI Tutor Setup

Already wired to **Claude Sonnet 4.5** via the Emergent Universal LLM key. No setup required from you. To monitor:
- **Profile menu → Universal Key → Balance** in the Emergent platform UI.
- If usage spikes, enable **Auto Top-up** on the same screen.

---

## 9. Installing as an App (PWA)

W.A.I. is a Progressive Web App.

**Android / Chrome**
1. Open the URL in Chrome.
2. Tap the **⋮ menu → Install app** (or "Add to Home Screen").

**Desktop (Chrome / Edge)**
1. Open the URL.
2. Click the **install icon** in the address bar (right side).
3. Pin to taskbar.

**iOS (Safari)**
1. Tap **Share → Add to Home Screen**.

---

## 10. Routine Maintenance Tasks

| Cadence | Task | Where |
|---|---|---|
| Daily | Review audit log | `/admin/audit` |
| Daily | Resolve incidents | `/incidents` |
| Weekly | Tool checkouts overdue review | `/admin/tools → Checkouts` |
| Weekly | Expiring credentials (30-day window) | `/admin/analytics` |
| Monthly | Add/rotate Associates for new cohorts | `/admin/associate` |
| Monthly | Backup MongoDB (ask me to set up `mongodump` cron) | server |
| Quarterly | Rotate admin & service passwords | `/admin/users` |

---

## 11. Quick Troubleshooting

| Symptom | Fix |
|---|---|
| Can't log in | Verify caps lock; admin can reset password in `/admin/users`. |
| 404 in logs on `/api/graphql`, `/api/swagger.json` | **Ignore.** External vulnerability scanners; harmless. |
| 307 redirects in logs | Already disabled. If they reappear, ping me. |
| AI Tutor returns "key low" | Top up Universal Key in Emergent profile. |
| Student stuck on a locked lab | They must finish the prerequisite (e.g., `solar-charge-controller` before `battery-inverter-build`). Visible in `/adaptive`. |

---

## 12. Going Live / Deployment

- The preview URL above is live; share it as-is with your pilot cohort.
- For your own custom domain or a full production deploy, click **Deploy** in the Emergent UI (top right) and follow the wizard — I can walk you through it any time.
- Save GitHub repo via **"Save to GitHub"** in the chat input to get the source.

---

## 13. Backlog (when you're ready)

- 🔴 **P0** Add Level 2/3/4 advanced apprentice labs (~21 more)
- 🟠 **P1** Real file uploads (videos/photos) via object storage
- 🟡 **P2** Email/SMS notifications (Resend / Twilio)
- 🟡 **P2** Iframe-embeddable portfolio widget for partner sites
- 🟡 **P2** Refactor `server.py` into modular routers

Just say the word and I'll start any of these.

---

*Last updated: Feb 2026 — Workforce Apprentice Institute Platform*
