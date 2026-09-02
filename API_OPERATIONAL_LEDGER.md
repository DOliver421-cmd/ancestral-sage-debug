# MoreHelp.center — Complete API Operationalization Ledger

Generated 2026-09-02 from live-mounted route resolution of the deployed backend (571 unique paths, 647 route-method entries).

## Classification standard
- **PASS** = runtime-verified: live HTTP 200 against the production backend, OR a passing route-level/contract test suite exercised the handler including its auth/authorization matrix.
- **FAIL** = broken. None remain — every defect found in this pass was fixed and re-verified before generation.
- **BLOCKED** = cannot be operationally executed from this environment: the authorized path needs session credentials, a live MongoDB, or a provider secret (all unavailable here as secrets), or the deployment intentionally fail-closes until an env secret is configured. BLOCKED is NOT PASS; verified negative-path evidence (401/422/400/404) is stated per row where it exists.

## Totals

| Bucket | Count |
|---|---|
| PASS | 36 |
| FAIL | 0 |
| BLOCKED | 611 |

## PASS

| Method | Path | Evidence |
|---|---|---|
| GET | `/api/admin/system/health` | route-level HTTP suite (7/7): 401 anon / 200 admin |
| GET | `/api/admin/system/restore-points` | route-level HTTP suite (7/7): 401/403/200 + create/list |
| GET | `/api/admin/system/restore-points/{restore_point_id}` | handler suite (16/16) |
| GET | `/api/admin/system/webhook-queue` | handler suite (16/16) |
| GET | `/api/ai/consent/health` | live public 200 (JSON) |
| GET | `/api/emergency` | live public 200 (Emergency UI HTML page) |
| GET | `/api/emergency/` | live public 200 (Emergency UI HTML page) |
| GET | `/api/features` | FCC contract suites: fcc_wiring 30/30, feature_control 23/23, access_gateway 30/30 |
| GET | `/api/features/` | FCC contract suites (same as /features) |
| GET | `/api/features/gate-map` | FCC contract suites (gate-map wiring 30/30) |
| GET | `/api/features/matrix/role` | FCC contract suites (role matrix 30/30 + 23/23) |
| GET | `/api/features/matrix/tier` | FCC contract suites (tier matrix 30/30 + 23/23) |
| GET | `/api/health` | live public 200 (JSON) |
| GET | `/api/more/needs` | live public 200 (JSON) |
| GET | `/api/more/posts` | live public 200 (JSON) |
| GET | `/api/my-projects` | member_projects suite 9/9 (dep auth gate, tier/staff/deactivated) |
| GET | `/api/my-projects/{project_id}` | member_projects suite 9/9 (owner gate, stage/advance paths) |
| GET | `/api/payments/products` | live public 200 (JSON) |
| GET | `/api/pricing` | live public 200 (JSON) |
| GET | `/api/puzzles/next` | live public 200 (JSON) |
| GET | `/api/ready` | live public 200 (JSON) |
| GET | `/api/revenue/api-keys/tiers` | live public 200 (JSON) |
| GET | `/api/revenue/courses/public` | live public 200 (JSON) |
| GET | `/api/version` | live public 200 (JSON) |
| POST | `/api/admin/system/restore-points` | route-level HTTP suite (7/7): 401/403/200 + create/list |
| POST | `/api/admin/system/rollback` | route-level HTTP suite: 400 no-confirm / auth matrix |
| POST | `/api/consent/cookie` | live public 200 (JSON) |
| POST | `/api/my-projects` | member_projects suite 9/9 (dep auth gate, tier/staff/deactivated) |
| POST | `/api/my-projects/{project_id}/advance` | member_projects handler suite 9/9 |
| POST | `/api/my-projects/{project_id}/approve` | member_projects handler suite 9/9 |
| POST | `/api/my-projects/{project_id}/archive` | member_projects handler suite 9/9 |
| POST | `/api/my-projects/{project_id}/comments` | member_projects handler suite 9/9 |
| POST | `/api/my-projects/{project_id}/run-stage` | member_projects suite: 403 without BYOK (9/9) |
| POST | `/api/v1/system/emergency-revert` | route-level HTTP suite: 401 bad sig / 200 valid |
| POST | `/api/v1/system/visual-state` | route-level HTTP suite: 200 ingest / 401 bad sig |
| PUT | `/api/features/{feature_id}` | FCC update_feature: real DB write + audit + 503-on-store-down (30/30) |

## BLOCKED

| Method | Path | Blocking cause |
|---|---|---|
| DELETE | `/api/admin/prices/{price_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/admin/promo-codes/{code}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/admin/users/{uid}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/ai/ai/memory/policy/{persona}/{order_id}` | AI op: needs AI provider key + member/role session (secrets) |
| DELETE | `/api/ai/memory/policy/{persona}/{order_id}` | AI op: needs AI provider key + member/role session (secrets) |
| DELETE | `/api/auth/account` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| DELETE | `/api/auth/sessions` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| DELETE | `/api/auth/sessions/{session_id}` | identity operation: registration/writes touch prod user DB; login needs credentials |
| DELETE | `/api/byok/key/{provider}` | AI op: needs AI provider key + member/role session (secrets) |
| DELETE | `/api/creator-lounge/projects/{project_id}` | community/user op: requires session + live DB records |
| DELETE | `/api/creator/courses/{course_id}` | learning op: requires session + live DB records |
| DELETE | `/api/exec/control/tiers/{tier_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/executive/archive/{asset_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/iam/resources/{resource_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/media/products/{product_id}` | media/content op: requires session + live DB records |
| DELETE | `/api/projects/{project_id}` | community/user op: requires session + live DB records |
| DELETE | `/api/providers/keys/{key_id}` | AI op: needs AI provider key + member/role session (secrets) |
| DELETE | `/api/revenue/api-keys/{key_hash}` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| DELETE | `/api/saga/images/{image_id}` | media/content op: requires session + live DB records |
| DELETE | `/api/saga/tracks/{track_id}` | media/content op: requires session + live DB records |
| DELETE | `/api/sentinel/protocols/{protocol_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/sentinel/research/{note_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| DELETE | `/api/sovereign/memory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/aawab/admin/overview` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/aawab/agents` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/aawab/agents/{agent_id}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/aawab/badge/{badge_id}/verify` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/aawab/registry` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/admin/overview` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/abo/agenda` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/config` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/deals` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/exchange` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/jobs` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/overview` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/public-status` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/redteam` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/source` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/source/controls` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/tools` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/abo/verify` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/adaptive/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/ai-costs` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/audit` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/checkouts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/cohorts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/control-panel` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/admin/discounts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/inventory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/payments` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/prices` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/admin/promo-codes` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/admin/recent-activity` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/sage/audit` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/sage/cap` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/sage/metrics` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/sage/status` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/sites` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/stats` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/admin/users` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/admin/sage/audit` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/admin/sage/cap` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/admin/sage/metrics` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/admin/sage/status` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/ai/consent/health` | identity operation: registration/writes touch prod user DB; login needs credentials |
| GET | `/api/ai/ai/director/greeting` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/director/pulse` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/history/{session_id}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/memory` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/memory/{persona}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/orchestrator/integrity` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/personas/exec` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/ai/sage/integrity` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/ai/scholar/integrity` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/director/greeting` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/director/pulse` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/history/{session_id}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/knowledge/search` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/memory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/memory/{persona}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/orchestrator/integrity` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/personas` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/personas/exec` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/ai/personas/{slug}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/personas/{slug}/controls` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/provider-test` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/ai/sage/integrity` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/ai/scholar/integrity` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/analytics/benchmark` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/analytics/program` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/attendance/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/attendance/roster` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/auditor/debt` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/auditor/ledger` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/auditor/report` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/auditor/risks` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/auditor/summary` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/auth/account/export` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/auth/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/auth/sessions` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/band/bookings` | media/content op: requires session + live DB records |
| GET | `/api/band/listings` | media/content op: requires session + live DB records |
| GET | `/api/band/my-listing` | media/content op: requires session + live DB records |
| GET | `/api/billing/credits/balance` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| GET | `/api/billing/sage-sessions` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| GET | `/api/bridge/config` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/bridge/log` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/bridge/personas` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/byok/admin` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/byok/status` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/certificates/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/certificates/{slug}.pdf` | learning op: requires session + live DB records |
| GET | `/api/competencies` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/competition/leaderboard` | learning op: requires session + live DB records |
| GET | `/api/competition/ping` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/competition/projects` | community/user op: requires session + live DB records |
| GET | `/api/competition/projects/{project_id}` | community/user op: requires session + live DB records |
| GET | `/api/competition/status` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/compliance` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/compliance/{slug}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creative-partner/contributions` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator-lounge/my-projects` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator-lounge/projects` | community/user op: requires session + live DB records |
| GET | `/api/creator/bank-account` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/courses` | learning op: requires session + live DB records |
| GET | `/api/creator/courses/published` | media/content op: requires session + live DB records |
| GET | `/api/creator/courses/{course_id}` | learning op: requires session + live DB records |
| GET | `/api/creator/earnings` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/enrollments/me` | learning op: requires session + live DB records |
| GET | `/api/creator/payout-profile` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/payout-summary` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/payouts` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/profile/me` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/profile/{slug}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/profiles/public` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/creator/split` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/credentials` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/credentials/assertion/{assertion_id}.json` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/credentials/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/credentials/transcript.pdf` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/credentials/{key}/manifest.json` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/exec/analytics` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/audio` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/audio/{asset_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/access/public` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/audit` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/authz-matrix` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/break-glass/active` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/break-glass/history` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/route-access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/state` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/control/tiers` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/dashboard` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/free-backup-matrix` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/merch` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/panel` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/panel/health` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/personas` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/products` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/scout/leads` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/scout/status` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/staff-meetings` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/system` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/exec/tools/incident-register` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/exec/tools/system-health` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/archive` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/discovery` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/pipeline` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/projects` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/projects/{project_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/projects/{project_id}/comments` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/executive/tools` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/handbooks` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/handbooks/{name}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/handbooks/{name}/raw` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/iam/actions` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/authority-chain` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/consent` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/delegations` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/identities` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/identities/{identity_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/resources` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/who-can-do-what` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/iam/who-has-access-to-me` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/incidents` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/instructor/lab-report` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/instructor/submissions` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/jamil/history` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/jamil/knowledge` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/jamil/ping` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/jamil/status` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/labs` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/labs/submissions/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/labs/{slug}` | learning op: requires session + live DB records |
| GET | `/api/me/position` | community/user op: requires session + live DB records |
| GET | `/api/me/position/history` | community/user op: requires session + live DB records |
| GET | `/api/me/proceeds-preference` | community/user op: requires session + live DB records |
| GET | `/api/media/content/{file_path:path}` | media/content op: requires session + live DB records |
| GET | `/api/media/file/{file_id}` | media/content op: requires session + live DB records |
| GET | `/api/media/products` | media/content op: requires session + live DB records |
| GET | `/api/media/products/mine` | media/content op: requires session + live DB records |
| GET | `/api/media/products/{product_id}/download` | media/content op: requires session + live DB records |
| GET | `/api/media/purchases` | media/content op: requires session + live DB records |
| GET | `/api/missing/file/{file_id}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/missing/photos/{case_id}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/modules` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/modules/{slug}` | learning op: requires session + live DB records |
| GET | `/api/more/admin/flags` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/more/admin/moderation-log` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/more/admin/moderation-stats` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/more/admin/queue` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/more/chat/{session_id}` | community/user op: requires session + live DB records |
| GET | `/api/more/department/integrity` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/nam/autobiography` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/chat/history` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/constitution` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/development` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/dreams` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/escalations` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/identity` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/intentions` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/intentions/drift` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/jamil/autonomy/{action_type}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/jamil/protocol` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/knowledge/search` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/knowledge/{knowledge_id}` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/leadership/ledger` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/memory` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/mission/alignment` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/accountability` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/challenge` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/crisis` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/economics` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/ecosystem` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/governance` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/mission` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/power` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/risk` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/strategy` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/operational/succession` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/reflections` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/reflections/tensions` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/nam/state` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/notifications/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/partnership/status` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/payments/history` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/payments/portal` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/portfolio/export.pdf` | live 422 verified (validation enforced); operation needs valid params/record |
| GET | `/api/portfolio/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/portfolio/public/{slug}` | community/user op: requires session + live DB records |
| GET | `/api/prices/public` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/progress/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/projects` | community/user op: requires session + live DB records |
| GET | `/api/projects/{project_id}` | community/user op: requires session + live DB records |
| GET | `/api/providers` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/providers/keys` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/providers/quick-setup/status` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/providers/usage-log` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/revenue/api-keys` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/api-keys/stats` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/courses/my-licenses` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/employer/compliance` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/employer/verify-batch` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/exec-overview` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/revenue/resume/preview` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/revenue/sovereign/workspaces` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/roster` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/saga/concerts` | media/content op: requires session + live DB records |
| GET | `/api/saga/images` | media/content op: requires session + live DB records |
| GET | `/api/saga/tracks` | media/content op: requires session + live DB records |
| GET | `/api/saga/videos` | media/content op: requires session + live DB records |
| GET | `/api/scholarships/admin/applications` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/scholarships/admin/awards` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/scholarships/admin/pledges` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/scholarships/applications/me` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| GET | `/api/scholarships/funds` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| GET | `/api/scholarships/sponsor/mine` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| GET | `/api/search` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/sentinel/protocols` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/sentinel/research` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/sentinel/reversals` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/sentinel/sovereign-drift` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/sentinel/status` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/site-guide/status` | AI op: needs AI provider key + member/role session (secrets) |
| GET | `/api/sovereign/memory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/supervisor/backup/free-matrix` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/backup/status` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/dashboard` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/escalations` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/greeter/config` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/sage/sessions` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/system/continuity-check` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/supervisor/visitor-flow` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| GET | `/api/team/actions` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/team/monitor/status` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/verify/{code}` | DB-backed operation: requires live MongoDB + session credentials |
| GET | `/api/xp/leaderboard` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| GET | `/api/xp/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| PATCH | `/api/abo/agenda/{item_id}` | AI op: needs AI provider key + member/role session (secrets) |
| PATCH | `/api/abo/deals/{deal_id}` | AI op: needs AI provider key + member/role session (secrets) |
| PATCH | `/api/admin/prices/{price_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/admin/promo-codes/{code}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/admin/users/{uid}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/admin/users/{uid}/active` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/admin/users/{uid}/role` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/auditor/ledger/{entry_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/auth/me` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| PATCH | `/api/band/bookings/{booking_id}/status` | media/content op: requires session + live DB records |
| PATCH | `/api/creator-lounge/projects/{project_id}` | community/user op: requires session + live DB records |
| PATCH | `/api/creator/courses/{course_id}` | learning op: requires session + live DB records |
| PATCH | `/api/executive/projects/{project_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/iam/identities/{identity_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/media/products/{product_id}` | media/content op: requires session + live DB records |
| PATCH | `/api/projects/{project_id}` | community/user op: requires session + live DB records |
| PATCH | `/api/projects/{project_id}/milestone/{milestone_id}` | community/user op: requires session + live DB records |
| PATCH | `/api/providers/{provider_id}/status` | AI op: needs AI provider key + member/role session (secrets) |
| PATCH | `/api/scholarships/admin/applications/{app_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/scholarships/admin/awards/{award_id}/milestones/{milestone_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/sentinel/protocols/{protocol_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/supervisor/greeter/config` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PATCH | `/api/supervisor/visitor-flow` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/aawab/admin/agents/{agent_id}/override` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/aawab/admin/agents/{agent_id}/revoke` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/aawab/agents/{agent_id}/certify` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/aawab/agents/{agent_id}/diagnose` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/aawab/agents/{agent_id}/treat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/aawab/register` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/deals` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/deals/{deal_id}/propose` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/exchange/contracts` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/goals` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/jobs` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/redteam/engagements` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/abo/source/controls` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/admin/ai-spend-budget` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/associate` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/checkout` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/checkout/{checkout_id}/return` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/control-panel/broadcast` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/creator-payouts/process` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/discounts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/inventory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/prices` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/promo-codes` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/run-checks` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/sites` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/users` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/admin/users/{uid}/password` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/admin/users/{uid}/reset-link` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/ai/ai/ambassador` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/architect` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/cipher` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/cipher/generate-audio` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/cipher/tts` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/consent` | identity operation: registration/writes touch prod user DB; login needs credentials |
| POST | `/api/ai/ai/director` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/director/tts` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/director/upload` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/griot` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/helper` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/memory/policy` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/oracle` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/orchestrator` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/personas/{slug}/toggle` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/revenue-director` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/ai/ai/revenue-director/tts` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/ai/ai/sage/create` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/sage/elevenlabs/tts` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/sage/resolve_mode` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/sage/tts` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/scholar` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ai/tool-chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/ambassador` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/architect` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/chat` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/cipher` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/cipher/generate-audio` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/cipher/tts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/consent` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/director` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/director/tts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/director/upload` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/helper` | live 400 verified (validation); operation needs valid body/record |
| POST | `/api/ai/helper/ask` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/memory/policy` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/oracle` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/orchestrator` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/personas/{slug}/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/personas/{slug}/controls` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/personas/{slug}/toggle` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/public/helper/ask` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/ai/revenue-director` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/revenue-director/tts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/sage/create` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/sage/elevenlabs/tts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/sage/resolve_mode` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/sage/tts` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/scholar` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/ai/social-blast` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/assistant/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/attendance` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/auditor/ledger` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/auth/change-password` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/auth/emergency-recovery` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/auth/exec-unlock` | live 404 = intentional fail-closed (env secret not configured) or param-gated |
| POST | `/api/auth/forgot-password` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/auth/login` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/auth/reconsent` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/auth/recovery-codes-generate` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/auth/recovery-status` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/auth/register` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/auth/reset-password` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/band/book` | media/content op: requires session + live DB records |
| POST | `/api/band/listings` | media/content op: requires session + live DB records |
| POST | `/api/billing/credits/grant` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/billing/refunds/cash` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/billing/refunds/site-credits` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/billing/sage-sessions/{session_id}/resolve` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/bridge/dispatch` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/bridge/receive` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/bug-report` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/byok/activate` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/byok/checkout` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/byok/key` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/byok/key/{provider}/test` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/competition/score` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/competition/task` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/compliance/{slug}/quiz` | learning op: requires session + live DB records |
| POST | `/api/creative-partner/chat` | community/user op: requires session + live DB records |
| POST | `/api/creative-partner/contribution` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/creator-lounge/projects` | community/user op: requires session + live DB records |
| POST | `/api/creator-lounge/projects/{project_id}/collab` | community/user op: requires session + live DB records |
| POST | `/api/creator/bank-account` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/creator/courses` | learning op: requires session + live DB records |
| POST | `/api/creator/courses/{course_id}/checkout` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/creator/payout-profile` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/creator/payout-request` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/exec/checkout/conversion` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/control/access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/ai-access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/authz-matrix` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/break-glass/activate` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/break-glass/revoke` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/budget` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/failover` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/feature-flag` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/ip-whitelist` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/legal-access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/mfa` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/page-mode` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/price` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/provider-ranking` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/route-access` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/sage-cap` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/tiers` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/user/role` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/user/tier` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/control/visibility` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/failover` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/merch/create` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/panel/heartbeat` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/exec/panel/reset` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/panel/toggle` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/personas/{name}/activate` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/personas/{name}/deactivate` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/personas/{name}/evolve` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/pipeline/process` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/pipeline/process-batch` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/products/create` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/products/publish-all` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/scout/craft-response` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/scout/match-all` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/scout/run` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/staff-meeting` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/exec/tools/fetch-url` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/tools/knowledge-ingest` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/tools/knowledge-search` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/tools/send-email` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/exec/tools/web-search` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/archive` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects/{project_id}/advance` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects/{project_id}/approve` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects/{project_id}/comments` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects/{project_id}/deliverables` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/executive/projects/{project_id}/run-stage` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/help/guide` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/iam/actions` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/actions/check` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/delegations` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/delegations/{delegation_id}/revoke` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/identities` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/identities/{identity_id}/rotate-token` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/iam/resources` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/incidents` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/incidents/{iid}/resolve` | community/user op: requires session + live DB records |
| POST | `/api/instructor/submissions/{sub_id}/review` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/jamil/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/jamil/digest` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/jamil/speak` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/jamil/transcribe` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/labs/submissions/{sub_id}/ai-feedback` | learning op: requires session + live DB records |
| POST | `/api/labs/{slug}/submit` | learning op: requires session + live DB records |
| POST | `/api/me/cancel-exit` | community/user op: requires session + live DB records |
| POST | `/api/me/emergency-exit` | community/user op: requires session + live DB records |
| POST | `/api/me/leave-more` | community/user op: requires session + live DB records |
| POST | `/api/me/proceeds-preference` | community/user op: requires session + live DB records |
| POST | `/api/me/request-exit` | community/user op: requires session + live DB records |
| POST | `/api/me/step-down` | community/user op: requires session + live DB records |
| POST | `/api/media/products` | media/content op: requires session + live DB records |
| POST | `/api/media/products/{product_id}/checkout` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/media/upload` | media/content op: requires session + live DB records |
| POST | `/api/missing/photo` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/missing/tip` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/more/admin/queue/{content_type}/{content_id}/approve` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/more/admin/queue/{content_type}/{content_id}/reject` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/more/appeal` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/chat/send` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/department/chat` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/flag` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/need` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/post` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/more/purge` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/nam/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/development/evaluate` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/dream` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/escalate` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/escalations/{escalation_id}/resolve` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/intentions` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/jamil/review` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/knowledge/import` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/knowledge/ingest` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/knowledge/{knowledge_id}/approve` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/leadership/evaluate` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/leadership/review` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/memory` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/mission/evaluate` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/accountability` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/challenge` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/conflict` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/crisis` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/economics` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/ecosystem` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/governance` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/memory` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/mission` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/power` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/risk` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/strategy` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/operational/succession` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/persona` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/nam/reflect` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/notifications/read-all` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/notifications/{nid}/read` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/payments/checkout` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/payments/webhook` | live 404 = intentional fail-closed (env secret not configured) or param-gated |
| POST | `/api/portfolio/publish` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/progress/quiz` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/progress/start` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/projects` | community/user op: requires session + live DB records |
| POST | `/api/projects/{project_id}/milestone` | community/user op: requires session + live DB records |
| POST | `/api/promo/validate` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/providers` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/providers/keys` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/providers/keys/{key_id}/test` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/providers/quick-setup` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/puzzles/answer` | live 422 verified (validation enforced); operation needs valid params/record |
| POST | `/api/revenue/api-keys` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/revenue/courses/license` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/revenue/sovereign/workspace` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/revenue/sovereign/workspace/{ws_id}/chat` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/revenue/verify-credential` | live 400 verified (validation); operation needs valid body/record |
| POST | `/api/saga/concerts` | media/content op: requires session + live DB records |
| POST | `/api/saga/concerts/{concert_id}/checkout` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/saga/images` | media/content op: requires session + live DB records |
| POST | `/api/saga/tracks` | media/content op: requires session + live DB records |
| POST | `/api/saga/videos` | media/content op: requires session + live DB records |
| POST | `/api/scholarships/admin/funds` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/scholarships/apply` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/scholarships/pledge` | commerce op: payment provider secret not configured / requires authorized purchase flow |
| POST | `/api/sentinel/ai-brief` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/sentinel/protocols` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/sentinel/protocols/unlock` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/sentinel/research` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/sentinel/respond` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/sentinel/reverse/{action_id}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/site-guide/chat` | AI op: needs AI provider key + member/role session (secrets) |
| POST | `/api/sovereign/chat` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/sovereign/memory` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| POST | `/api/supervisor-integrity-alert` | DB-backed operation: requires live MongoDB + session credentials |
| POST | `/api/supervisor/backup/emergency-broadcast` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/backup/reset-gateway` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/backup/switch-provider` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/content/{content_type}/{content_id}/approve` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/content/{content_type}/{content_id}/reject` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/escalations` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/escalations/{esc_id}/resolve` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/public-chat` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| POST | `/api/supervisor/sage/sessions/{session_id}/flag` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/abo/config` | AI op: needs AI provider key + member/role session (secrets) |
| PUT | `/api/admin/sage/cap/global` | live 401 verified (auth enforced); authorized path needs session credentials (secrets) |
| PUT | `/api/admin/sage/cap/user/{uid}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/ai/admin/sage/cap/global` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/ai/admin/sage/cap/user/{uid}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/bridge/config` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/bridge/personas/{persona_key}` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |
| PUT | `/api/creator/profile` | DB-backed operation: requires live MongoDB + session credentials |
| PUT | `/api/executive/projects/{project_id}/packet` | privileged-role operation: requires admin/exec session credentials (secrets) + live DB |

## FAIL

None.
