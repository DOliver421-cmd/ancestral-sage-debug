---
name: databasepersistenceauditor
description: "MongoDB persistence reality check for this repo: two competing DB layers, two env vars, two default DB names, bind()-injected handles that can be None, and indexes that may never have been created."
---

# databasepersistenceauditor

Read `.claude/skills/_shared/REPO-REALITY.md` first, especially §4.

Verify that data written by the app can be read back in the shape the app
expects. In this repo the write/read contract is complicated by the fact that
**there are two independent database layers pointing at two different databases.**

## The split you must resolve before auditing anything

| | `backend/server.py` (live path) | `backend/database.py` (near-dead) |
|---|---|---|
| Env var | `MONGO_URL` | `MONGODB_URI` (`backend/config.py:17-18`) |
| DB name | `DB_NAME`, default `ancestral_sage` | `DATABASE_NAME` = `wai_institute` (`backend/config.py:21`) |
| Handle | module global `db` (`backend/server.py:117-126`) | `db_manager.db` |

`database.py`'s `init_database()` is **never called from `server.py` startup.**
Its only consumer is `backend/jobs.py:12`, which guards `if not db_manager.db:`
at `:91, :170, :221, :261, :293` — so those billing/revenue/invoice jobs are
permanently no-ops. And every index declared in `backend/database.py:44-160`
(subscriptions, invoices, payment_methods, usage_events, creator_balances,
creator_payouts, revenue_events, leads, opportunities, activity_log, contracts,
support_tickets, audit_log TTL, notifications TTL) may never have been created.

**Never conclude an index exists because you found `create_index` in source.**

## How handlers get a DB handle (three ways, all fallible)

1. `bind(db, ...)`-injected module global — 47 routers. If `bind()` was skipped
   because the router's import was swallowed, the global is `None`.
2. `deps.get_db()` — returns the module global `_db`, which is **`None` until
   `set_db()` runs during startup** (`backend/deps.py:45-51`).
3. `app.state.db` — set inside `_on_startup_impl` (`backend/server.py:1378`).

Because startup is a fire-and-forget task (`backend/server.py:1350-1362`),
requests are served while all three may still be unset. Commit `afb1c8b`
("harden API against NoneType db crashes") is this exact class, and hardening a
symptom is not the same as removing the race.

## Steps

1. Identify the write path (`insert_one` / `update_one` / `replace_one`) and its
   paired read path (`find` / `find_one` / `aggregate`). Cite both `file:line`.
2. Confirm **both sides address the same database and the same collection.**
   Cross-layer pairs (`server.py` global writes, `jobs.py` `db_manager` reads)
   are broken by construction — different env var, different default DB name.
3. Confirm the handle cannot be `None` on the path — or that the handler
   explicitly tolerates it and returns something the frontend can render rather
   than a 500.
4. With a real Mongo: execute the write, execute the read, and **diff the stored
   document shape against every consumer's expected fields.** Include the
   frontend consumer.
5. Check the identifier contract: `_id` `ObjectId` vs `str`, and timezone-aware
   vs naive datetimes. Mixed conventions across 50 routers are a live drift risk.
6. Check legacy role values. `backend/roles.py:41-52` (`LEGACY_ROLE_MAP`) proves
   documents in Mongo may hold `priority_member`, `site_support`,
   `creative_partner`, `guest`, `creator`, `mentor`, `moderator`, `steward`, or
   `elder`. Any read path comparing `user["role"] == "instructor"` directly,
   instead of via `normalize_role`, is wrong for migrated data.
   `normalize_role` silently defaults unknown values to `student`
   (`backend/roles.py:79-87`) — a typo becomes a permission change, not an error.
7. Verify indexes by querying the live DB (`list_indexes()`), never from source.
8. Confirm whether TTL indexes (`audit_log`, `notifications`) actually exist —
   if not, retention policy claims in the root `*.md` reports are unfounded.

## Constraints

- **There is no `mongod` in this container.** Steps 4, 7, and 8 are
  `ENVIRONMENT BLOCKED` here. Say so; do not substitute source reading.
- Source inspection may prove a mismatch BROKEN. It can never prove persistence
  works.
- `supabase==2.9.1` is in `backend/requirements.txt`. Confirm whether it is used
  at all before treating it as part of the data layer. Mongo is the live store.
- Do not run destructive operations. `DatabaseManager.drop_all()`
  (`backend/database.py:163`) exists and is guarded only by
  `settings.ENVIRONMENT == "production"`.
- Never assume the wai-institute and morehelp.center deployments share a database
  (anchor §0) — `cross_site_auth` explicitly "finds or creates the local user".
- Cite `file:line`; paste the actual stored document and the actual read result.
