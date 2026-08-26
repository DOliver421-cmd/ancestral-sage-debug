# HANDOFF — AI Team Bridge: Build the Receiving Side in the WAI-Institute Repo

**Created:** August 26, 2026
**From:** Freebuff session working in `DOliver421-cmd/ancestral-sage-debug` (morehelp.center)
**To:** The next Freebuff session that has read/write access to `DOliver421-cmd/Wai-Institute`

---

## 1. The task, in one sentence

Implement and verify the **receiving half** of the AI Team Bridge on the WAI-Institute site
(`DOliver421-cmd/Wai-Institute`, https://www.wai-institute.org) so that assignments
("dispatches") sent from the M.O.R.E. Help Center AI Team Bridge (morehelp.center) are
authenticated, stored exactly once, and surface in the WAI Executive Deck's conference room.

The **sending half is DONE and shipped** on morehelp.center `main` (commit `5511bc9`).
This task is only the WAI-side receiver.

---

## 2. Why this handoff exists

The previous session could not reach `DOliver421-cmd/Wai-Institute`: the Freebuff GitHub App
("Freebuff Web", developed by CodebuffAI) is **installed with All-repositories access** on the
owner's account (verified via the installation page, install id `152783043`), but the credential
minted for the morehelp.center workspace is **repository-scoped to
`ancestral-sage-debug` only** (verified: `GET /installation/repositories` returns exactly one repo).
Connecting the second repo at the Freebuff workspace level did not succeed, so the owner asked for
this handoff instead. **Do not re-litigate access** — if this session can read the repo, proceed.
The GitHub App install itself is already correct.

Owner context (for the work, from Delon Oliver / NAM Oshun, owner of NAM Oshun Edutainment LLC,
DBA WAI-Institute):
- **wai-institute.org** = Executive Branch / umbrella + vocational training site (the "Executive Deck").
- **morehelp.center** = student + administrative support, virtual community center; AI with human oversight.
- The bridge connects the two sites' AI teams. The WAI side is "the Executive Branch"; the M.O.R.E.
  Director (with NAM Oshun Scholar) sends assignments to the WAI team.

---

## 3. The contract (already implemented on the sender — implement the mirror)

Sender behavior is in `backend/routers/bridge.py` (morehelp.center, commit `5511bc9`),
`POST /bridge/dispatch` (admin+). Exact outbound request:

```
POST <webhook_url>
Content-Type: application/json
X-Bridge-Signature: sha256=<hex>

body = JSON with separators (",", ":") — i.e. json.dumps(payload, separators=(",", ":"))
```

Payload shape (stable per dispatch, retries re-send the SAME dispatch_id):

```json
{
  "type": "wai.bridge.dispatch",
  "dispatch_id": "<uuid>",
  "kind": "task | project | update | ack",
  "title": "<short title>",
  "task": "<full brief>",
  "project_id": null,
  "from": "WAI-Institute AI Director",
  "body": "<full assembled dispatch text incl. coordination notes>",
  "sent_at": "<ISO-8601 UTC>"
}
```

Signature scheme (HMAC-SHA256):
```
hex = hmac.new(secret.encode("utf-8"), raw_body_bytes, hashlib.sha256).hexdigest()
X-Bridge-Signature = "sha256=" + hex
```
`raw_body_bytes` are the **exact bytes of the body as received** — verify the signature against the
raw request body, never a re-serialized copy.

Sender retry behavior: **up to 3 attempts** with 1s/2s backoff; any 2xx counts as delivered; a
non-2xx or network error after 3 attempts is recorded as `failed`. Therefore the receiver MUST be
**idempotent** and MUST return 2xx for duplicates.

Sender status vocabulary (already in the UI): `delivered` / `failed` / `logged` (manual).
A fallback must never be presented as success.

### Minimum receiver requirements

1. **Authenticate:** read `X-Bridge-Signature`, compute the HMAC-SHA256 of the raw body with the
   shared secret, compare in constant time. Mismatch/missing → `401`.
2. **Idempotent:** dedupe on `dispatch_id`. Persist the first delivery; on a repeat, return 2xx with
   the same stored id and a `duplicate: true` flag (do NOT create a second record, notification, or
   any side effect). Use a unique index on `dispatch_id` plus a pre-check.
3. **Persist:** store the dispatch with at least: `dispatch_id`, `title`, `kind`, `body`, `sent_at`,
   `received_at`, `source` (`morehelp.center`). Make it queryable for the conference-room feed.
4. **Ack:** return `{"status": "ok", "message_id": "<id>", "duplicate": false|true}`.
5. **Reject cleanly:** bad signature → 401; malformed JSON → 400.

---

## 4. Shared secret — provisioning (required for the two sites to talk)

Both sites must use the **same** shared secret.

1. Generate one, e.g. `python3 -c "import secrets; print(secrets.token_hex(32))"`.
2. **WAI side (this repo):** store it server-side as an env var / config the receiver endpoint reads
   (e.g. `WAI_BRIDGE_SHARED_SECRET`). Never expose it to the frontend.
3. **morehelp.center side:** set the same value in the bridge admin UI
   (`/admin/bridge` → Settings → "Shared secret (signs deliveries, protects inbound)") and save.
   That value is persisted in Mongo `bridge_config.shared_secret`.
4. **Webhook URL:** in the same Settings screen, set:
   - "How assignments leave this site" = **Webhook — deliver to partner's site**
   - "Inbound webhook URL" (the field labeled for the partner endpoint) = the WAI receiver URL,
     e.g. `https://www.wai-institute.org/api/bridge/receive` (exact path depends on WAI's stack —
     see §6).
5. Before go-live, test with the shared secret configured on BOTH sides (see §7).

---

## 5. Where the dispatches should appear on the WAI side

The WAI site's bridge is the **Executive Deck** (per the owner's screenshot):
- Left nav: Super Exec Command ("Conference + chat + orchestration + both sites"), Jamil AI Director,
  Course Manager, Curriculum & Outcomes, Project Dashboard, Analytics, Email Center, User Controls,
  Member Management, Persona Manager, API Key Manager.
- Top bar: `WAI ↔ MORE Help Center` with a green **BRIDGE** badge, governance: ADVISORY, and actions
  Deliberate / Agenda / Roster / Voice Room / Copy bridge link.
- Conference Rooms: `# WAI ↔ MORE Help Center` — a message log of "Daily Standup" cards showing
  `Tasks open: N · Agenda: N · Decisions last 24h: N · AI activity last 24h: N`.
- AI Directors row: Jamil, Ancestral Sage, MORE Director, Portal Advisor (green dots, auto-respond to
  matching topics, @mention to direct), Auto-brief checkbox, Roundtable button. Input tabs: Message /
  Task / Voice.

**Integration target:** incoming M.O.R.E. dispatches should appear in the
`WAI ↔ MORE Help Center` conference room as messages/cards (like the Daily Standup cards), showing
title, kind, sender, and the dispatch body, with the same counters updated. Inspect how that
conference room's message log is stored and rendered, and insert received dispatches through the
EXISTING storage path — do not build a second chat system.

---

## 6. Recommended implementation steps (adapt to WAI's actual stack — inspect first!)

The WAI repo's stack is unknown to the handing-off session (it had no repo access). **Inspect before
writing code** — do not assume FastAPI/Python; it may be Django, Next.js, etc.

1. `ls` / read the repo layout; find the existing bridge/conference-room implementation
   (the Executive Deck screen the owner screenshotted). Locate where "Daily Standup" cards and the
   `# WAI ↔ MORE Help Center` room store messages.
2. Add the inbound endpoint at a sensible path (e.g. `/api/bridge/receive`) that:
   - reads the raw body,
   - verifies `X-Bridge-Signature` (constant-time) against `WAI_BRIDGE_SHARED_SECRET`,
   - dedupes on `dispatch_id` (unique index + pre-check; return 2xx + same id + `duplicate: true`),
   - persists the dispatch, returns `{"status": "ok", "message_id": ..., "duplicate": false}`.
3. Add the unique index on the inbound collection's `dispatch_id` (idempotent at startup, like the
   sender does).
4. Surface received dispatches in the conference room feed via the existing storage/query path.
5. Do NOT add any paid third-party service. All of this is plain HTTP + the site's existing storage.

---

## 7. End-to-end verification (required before calling this done)

Use the morehelp.center bridge UI (or `POST /api/bridge/dispatch` with an admin token):

1. **Happy path:** send a dispatch; confirm WAI receives it: correct title/kind/body/sender; message
   id returned; appears in the conference room feed; sender shows **Delivered** (1 attempt, HTTP 2xx).
2. **Idempotency:** replay the same raw request (same `dispatch_id`, same body, same signature) to the
   WAI endpoint; expect 2xx, same `message_id`, `duplicate: true`, and NO second record/card.
3. **Signature rejection:** POST with a wrong or missing signature; expect `401`.
4. **Malformed body:** POST garbage JSON; expect `400`.
5. **Manual mode unaffected:** with dispatch_mode = manual on the sender, no POST happens and the
   dispatch is logged for hand-off (sender status `logged`).
6. **Surfaces match:** the WAI side renders inbound dispatches with a visible sender label
   ("MORE Help Center" / "WAI-Institute AI Director").

If any link fails, fix the failing side — do not declare done on code presence alone.

---

## 8. Reference material (sender side, already shipped)

- `backend/routers/bridge.py` (morehelp.center, commit `5511bc9`) — the dispatch endpoint,
  signing, retry loop, delivery metadata, idempotent inbound receipt (`/bridge/receive` exists on the
  sender as the mirror for WAI→MORE traffic and can be reused as the reference implementation).
- `backend/tests/test_bridge_delivery.py` — sender tests proving signing, retry-then-fail, manual
  mode, invalid-URL fail-closed, inbound dedupe (6 tests).
- `frontend/src/pages/AITeamBridge.jsx` — sender UI (Send Assignment default, delivery status badges).
- The morehelp.center bridge config lives in Mongo `bridge_config`; dispatches in
  `bridge_dispatch_log`; inbound in `bridge_inbound` (unique sparse index on `dispatch_id`).

## 9. Definition of done (for the receiving session)

- [ ] Inbound endpoint exists, authenticates the signature, persists exactly-once per `dispatch_id`
- [ ] Dispatches appear in the WAI Executive Deck conference room feed
- [ ] Shared secret is set on BOTH sites and the end-to-end test (signed → received → rendered)
      passed with a real dispatch
- [ ] Duplicate replay, bad signature, and malformed body cases verified
- [ ] No paid services, no second chat/bridge system, no decorative "done"
