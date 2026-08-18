# Sponsor a Scholarship — Operator's Manual

**Version:** 1.0 · **Last updated:** 2026-08-18
**Audience:** Executives, Admins, and the Scholarship Committee.
**Mission fit:** giving that feeds the mission loop — sponsors fund learners, learners become members/creators,
and every dollar is tracked against a verified milestone. No opacity, no lump-sum leaks.

---

## 1. The three-sided flow

```
SPONSOR → /sponsor → pledge (Full / Partial / Collective) → Lemon Squeezy → Gumroad checkout
        → webhook marks pledge paid → fund progress rises → office notified
APPLICANT → /scholarships/apply → need + community contribution + goal → committee queue
COMMITTEE → /admin/scholarships → approve/deny → approval AUTO-MATCHES oldest paid pledge
        → award created with 3 verified milestones → funds release only on verification
```

**Integrity rules**
- Sponsors must be signed in (free account) so pledges, receipts, and scholar updates stay in one place.
- If payments are not configured (`LEMON_SQUEEZY_API_KEY`/`STORE_ID` or `GUMROAD_API_KEY`), pledges are recorded
  with a `grace` audit trail (`scholarship.pledge_committed_grace`) — the office follows up; nothing is dropped.
- Awards are milestone-based: `enrolled → m1 → complete`. The committee verifies each; funds release against progress.
- Every transition is audited (`scholarship.*` actions) and the sponsor is notified at match time.

## 2. Committee desk — `/admin/scholarships`

| Tab | What you do |
|---|---|
| Applications | Review queue (submitted → under_review → approved/denied, filterable). Each card shows need, community contribution, goal. Approve → auto-match; Deny → applicant notified. |
| Awards & Milestones | Every award with its milestone track. "Verify milestone" releases the next stage. |
| Pledges | Full sponsor ledger: tier, amount, status (pending → committed → paid → matched). |
| Funds | Create funds (title, category, description, goal) and watch live progress. |

**Matching logic:** on approval, the oldest paid, un-assigned pledge is matched (same fund preferred, then the
general pool). If no paid pledge exists yet, the award is `reserved` and matches automatically when one arrives.

## 3. Sponsor view — `/sponsor`

Tiers: **Full** (complete cycle), **Partial** (targeted hurdles: fees, tools, licenses), **Collective** (cohort
funding for organizations). Sponsors see every pledge's status and every matched scholar's milestone progress.

## 4. Applicant view — `/scholarships/apply`

One active application per fund. Committee scores need, growth dedication, and community contribution. Applicants
are notified at every state change and can track status on the same page.

## 5. Default funds (seeded on first request)

- **Workforce & Arts Initiative** — certifications, tools, program costs.
- **Elder & Caregiver** — digital literacy, accessibility, connectivity.
- **Creator Tools & Studio** — equipment, software, course access.

Create more from the committee Funds tab; rename/adjust goals there without code.

## 6. Endpoints

| Method | Path | Access |
|---|---|---|
| GET | `/api/scholarships/funds` | Public |
| POST | `/api/scholarships/pledge` | Auth (sponsor) |
| GET | `/api/scholarships/sponsor/mine` | Auth (sponsor) |
| POST | `/api/scholarships/apply` | Auth (applicant) |
| GET | `/api/scholarships/applications/me` | Auth (applicant) |
| GET | `/api/scholarships/admin/applications?status=` | admin+ |
| PATCH | `/api/scholarships/admin/applications/{id}` | admin+ |
| GET | `/api/scholarships/admin/awards` · PATCH `/…/milestones/{mid}` | admin+ |
| GET | `/api/scholarships/admin/pledges` · POST `/api/scholarships/admin/funds` | admin+ |
| — | `/api/payments/webhook` | Payment webhook (product `scholarship`) |

## 7. Related surfaces

- Executive Command Center → Business tab (`/admin/command`) shows agenda + business live; Reports tab links this manual.
- Video Presentation Builder (`/studio/video-presenter`) makes sponsor impact videos (preloaded Impact Report template).
