# Domain Focus Migration Blueprint

**Decision:** M.O.R.E. Help Center (www.morehelp.center) is the single hub for support, billing,
account administration, and the SOUP Poetry / creative community. WAI Institute (www.wai-institute.org)
becomes a focused institution site: **electrical education, professional education, and media strategy.**

**Approved by:** Executive meeting. **Legal entity:** NAM Oshun Edutainment LLC (d/b/a WAI Institute — pending).

---

## 1. The short answer: how is this possible?

**This is a single codebase serving both domains.** Every feature below already runs on
www.morehelp.center today. There is no data migration, no rebuild, and no second backend.
"Transferring" a feature here means changing **which domain shows it, where its links point,
and how it's framed** — not rebuilding it.

The one real technical change: **stop redirecting wai-institute.org to morehelp.center**
(currently `frontend/src/App.js` rewrites every wai-institute.org visitor to
`https://www.morehelp.center/wai-institute`). Replace that with a **domain-aware experience**:

| Domain | Landing | Navigation | Emphasis |
|---|---|---|---|
| `wai-institute.org` | Focused institution front door | Classrooms, electrical curriculum, labs, credentials, AI Tutor, media strategy | Mission focus, high-intent course pages, clean SEO |
| `www.morehelp.center` | Full M.O.R.E. hub | Everything else: support, billing, community, creative suite, SOUP | Help + community + creative |

Same API, same accounts, same database. Two doors into one house.

> **One honest constraint:** sign-in state (localStorage token) is per-domain. A user signed
> into morehelp.center will sign in again on wai-institute.org. This is normal for separate
> domains and acceptable — both doors share the same account database.

---

## 2. Features that move to www.morehelp.center

### 2.1 Customer Support & Ticketing
| Feature | Where it lives today | Move action |
|---|---|---|
| Support/Help Center page | `/help-center`, `/more-help-center` | Already on MORE — make it THE support landing |
| Bug report widget | `BugReportModal` (global) | Re-target its "report" destination to MORE help desk |
| Live chat / helper | `/helper`, `/app/helper`, `/more/chat` | Keep on MORE; on WAI site, replace widget with a "Get Help → morehelp.center" link |
| Knowledge base / help articles | `/site-guide`, `/handbooks` | Already on MORE — restyle as the Knowledge Base |
| System status | `/api/health`, admin health pages | Expose a public status card on MORE |

### 2.2 Billing & Account Administration
| Feature | Where it lives today | Move action |
|---|---|---|
| Plans & pricing | `/plans` | WAI site links out to MORE for enrollment billing |
| Subscriptions / checkout | `/subscribe` | Keep on MORE (payments already resolve there) |
| Payment history | `/payment/history` | Move the link — WAI site never mentions billing |
| Store / merch / media store | `/store`, `/merch` | MORE only |
| Donate / sponsor | `/donate`, `/sponsor` | MORE only |
| Account settings (cards, MFA, email) | `/settings`, `/forgot-password` | Self-service stays on MORE; WAI login links there for recovery |
| Admin billing & prices | `/admin/billing`, `/admin/payments`, `/admin/prices` | MORE admin only |

### 2.3 Technical & LMS Troubleshooting
| Feature | Where it lives today | Move action |
|---|---|---|
| Student/instructor/admin handbooks | `/handbooks/*` (4 manuals) | Published as the MORE Knowledge Base |
| LMS access guides | WAI student handbook | Port to MORE help articles |
| Browser/device requirements | handbook content | Add a requirements article on MORE |
| BYOK / AI key management | `/byok` | MORE (technical support surface) |
| Certificate delivery support | `/certificates`, handbook | FAQ articles on MORE ("Where is my certificate?") |

### 2.4 Administrative FAQs & Policy Support
| Feature | Where it lives today | Move action |
|---|---|---|
| Privacy / Terms / Cookies | `/privacy`, `/terms` + cookie banner | Legal *resources* stay visible on both; the *support* for them lives on MORE |
| Legal tools | `/more/litigation` | Stays on the main site (legal resources remain core) |
| Executive/admin FAQ | `/admin/*` docs | Internal — stays where it is, admin-only |

### 2.5 SOUP Poetry & the Creative Community (all to MORE)
| Feature | Where it lives today | Move action |
|---|---|---|
| Trash / M.O.R.E. Pantheon (poetry + comedy) | `/trash` | MORE only — already M.O.R.E.-branded |
| M.O.R.E. Creators suite (studio, courses, earnings, payouts) | `/studio`, `/creator/*`, `/creator-lounge` | MORE only |
| Ghost Producer / Band / Playlist / Arcade | `/ghost-producer`, `/band`, `/playlist/dashboard`, `/arcade` | MORE only |
| Community chat & boards | `/community`, `/more/chat`, `/creators` | MORE only |
| Workshop registration & submissions | (workshop sign-up surfaces) | Build intake on MORE when the workshop schedule launches |

## 3. What STAYS on WAI Institute (the focused mission)

- **Electrical education:** `/modules`, `/labs`, `/compliance` (NFPA 70 / NEC 2023)
- **Credentials & certificates:** `/credentials`, `/certificates`
- **AI Tutor** (learning companion): `/ai`, `/council`
- **Classrooms / dashboard:** `/dashboard`
- **Media strategy:** Social Blast (`/social/publish`) and the professional media curriculum
- **Legal resources** (documents stay visible; support lives on MORE)

## 4. Execution plan

1. **Domain-aware front door** — replace the wai-institute.org redirect in `frontend/src/App.js`
   with a focused WAI landing rendered for that hostname (same build, same deployment).
2. **Domain-aware navigation** — the sidebar filters by hostname: WAI site shows core items only;
   every support/billing/creative item becomes an outbound link to `www.morehelp.center`.
3. **DNS** — both domains already point at the same host; verify CORS allows both origins
   (the API is same-origin per domain, so this is a config check, not new code).
4. **Footer & help routing** — WAI footer gains a permanent **"Help & Support → morehelp.center"**
   link; the support widget on WAI links out instead of opening in-app.
5. **Content audit** — handbooks/FAQs already live in-app; rebrand them as the MORE Knowledge
   Base and add the missing articles (browser requirements, certificate delivery, refunds).
6. **SEO isolation** — WAI pages target high-intent technical terms (NFPA 70, NEC 2023 exam prep,
   electrical safety); MORE pages own support + creative + community terms. No keyword cannibalization.

## 5. What this does NOT require

- ❌ No new backend, no data migration, no new database
- ❌ No rebuilding support/billing/creative features — they run on MORE today
- ❌ No changes to payment processing or accounts

## 6. Suggested sequencing (approval gates)

- **Phase A (now):** domain-aware landing + nav split + footer links. wai-institute.org stops
  redirecting and shows its focused face.
- **Phase B (next):** support entry points re-targeted to MORE; billing links removed from WAI.
- **Phase C (content):** handbook → Knowledge Base restyle; SEO meta per domain.
- **Phase D (verify):** both domains resolve, auth works per domain, help flows land on MORE.
