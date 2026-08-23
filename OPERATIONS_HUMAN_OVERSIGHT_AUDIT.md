# OPERATIONS / HUMAN OVERSIGHT AUDIT (Phase 20)

**Method:** source inspection this session. "FUNCTIONAL" below means the code path exists — not that the process is proven.

## Function inventory (SRC)

| Function | Endpoint(s) | Status |
|---|---|---|
| Admin stats/activity | `/admin/stats`, `/admin/recent-activity` | FUNCTIONAL (code) |
| Cohort management | `/admin/cohorts` | FUNCTIONAL (code) |
| Course moderation | `/admin/courses/{id}/moderate` | FUNCTIONAL (code) |
| User management | admin users router | FUNCTIONAL (code) — live path UNVERIFIED |
| Incident reporting | `POST /incidents` (any auth) | FUNCTIONAL (code) |
| Incident triage | `GET /incidents` (instructor+) | FUNCTIONAL (code) |
| Incident resolution | `POST /incidents/{id}/resolve` (admin) | FUNCTIONAL (code) |
| Community moderation | `/more/admin/moderation-log` + `-stats` | FUNCTIONAL (code) |
| Finance ledger | `/auditor/ledger`, `/auditor/summary`, `/auditor/report`, `/auditor/debt` | FUNCTIONAL (code) |
| Refunds | `/billing/refunds/site-credits` (+ cash) admin-only | FUNCTIONAL (code) |
| Broadcast | `POST /admin/broadcast` | FUNCTIONAL (code) |
| Notifications | `/notifications/me`, read-all | FUNCTIONAL (code) |
| AI budget oversight | gateway health + hourly cap + budget alert ratio | FUNCTIONAL (code) |
| Break-glass | exec-unlock (secret-gated), factory-reset | FUNCTIONAL (code) |
| Site report | `/exec/site-report` | FUNCTIONAL (code) |

## Operational-process assessment

| Process | Status |
|---|---|
| Admin console | UI-only verified in code; browser UNVERIFIED |
| Support/moderation workflow | code exists; end-to-end UNVERIFIED |
| Escalation path | incidents exist; explicit escalation policy DOCUMENTED-ONLY (not found in code) |
| Payment disputes | admin refund tooling exists; dispute process DOCUMENTED-ONLY |
| Provider-failure response | gateway fallback chain is automatic (KB fallback); operator runbook NOT FOUND |
| Budget exhaustion response | automatic notices; operator alerting via Slack webhook env exists — UNVERIFIED |
| Account recovery | recovery codes + break-glass implemented (SRC) |
| Emergency shutdown / feature disablement | FCC `enabled=false` + middleware fail-closed (TEST 16/16); not live-tested |
| Incident response procedure | NOT FOUND in repo (may be external — UNKNOWN) |
| Content reports from users | incidents endpoint; per-content report UI not confirmed |

## Launch note

An admin page is not an operational process. Before campaign, confirm who is on-call, how incidents/budget alerts reach them (Slack webhook configured?), and that the moderation queue is actually monitored. Document a one-page runbook.
