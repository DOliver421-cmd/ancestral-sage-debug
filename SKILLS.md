# Repository Skills

Operational skills for making changes in this repository. These are execution skills, not suggestions: inspect the actual implementation, make the smallest correct change, and verify the user path.

## 1. Extensive API Engineering Skill

### Mission
Build, repair, and verify production API behavior across the existing Python/FastAPI backend, MongoDB persistence, React client, authentication, RBAC, AI providers, payments, webhooks, media, courses, and administrative workflows.

### API inventory procedure

1. Search the frontend for every API call, including `fetch`, the shared API client, upload helpers, polling, websocket/event clients, and hard-coded URLs.
2. Search the backend for every route decorator, router prefix, router registration, dependency, schema, and error handler.
3. Normalize paths before comparing them: account for prefixes, version prefixes, trailing slashes, path parameters, query parameters, and proxy/base-URL behavior.
4. Produce an inventory containing:
   - method and effective path;
   - caller file and function;
   - authentication requirement;
   - role, tier, feature, and ownership requirements;
   - request headers, query, path, and JSON/body schema;
   - response schema and status codes;
   - database collections and writes;
   - external providers and environment dependencies;
   - loading, retry, timeout, and error behavior;
   - evidence and current status.
5. Mark each route as `implemented`, `frontend-mismatch`, `backend-mismatch`, `unreferenced`, `environment-blocked`, `broken`, or `verified`.

### Request-path tracing
Trace every important request in this order:

```text
browser action
→ frontend API helper
→ resolved API base URL
→ HTTP method/path/headers/body
→ proxy/CORS
→ FastAPI route registration
→ authentication dependency
→ normalized identity
→ RBAC/feature/ownership checks
→ validation/schema parsing
→ database read/write
→ external provider call
→ response normalization
→ frontend state update/render
```

Never infer a route from a document or filename. Confirm route registration and effective prefixes in code.

### Contract discipline

- Match frontend field names, casing, types, required fields, enum values, and response nesting to the backend schema.
- Check whether Pydantic models reject fields the frontend sends or require fields the frontend omits.
- Check status-code handling for 200, 201, 202, 204, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503, and provider-specific failures.
- Ensure the frontend does not treat an error object as a successful payload.
- Ensure empty results are distinct from errors.
- Keep error responses consistent enough for the existing client to display them.
- Preserve backwards compatibility unless the caller and all dependents are updated together.

### Authentication and authorization

- Trace the actual token/session extraction and current-user dependency.
- Verify anonymous, authenticated, wrong-role, wrong-tier, inactive-account, and wrong-owner behavior.
- Ensure every user-specific query is scoped to the authenticated identity.
- Ensure admin endpoints do not trust client-supplied user IDs or roles.
- Ensure protected routes are not accidentally public because a dependency was omitted.
- Ensure public routes do not accidentally require a stale or unrelated session.

### Database correctness

- Verify collection names, query filters, projections, sort order, pagination, and update operators.
- Check upsert and duplicate behavior.
- Check ObjectId/string ID consistency.
- Check required indexes, especially unique keys used for idempotency.
- Check concurrent writes and lost-update risks where the workflow can be retried.
- Check that database failures produce truthful failures rather than empty success responses.
- Preserve existing document shapes and migration assumptions.

### External-provider correctness

For every provider call, verify:

- credential source and server-only handling;
- endpoint and API version;
- request format and headers;
- timeout and retry policy;
- response parsing and validation;
- rate-limit and quota handling;
- idempotency key behavior where applicable;
- safe logging that excludes secrets and sensitive content;
- fallback behavior and final status code.

A configured environment variable proves only configuration presence. It does not prove that the credential is read, accepted, or used successfully.

### AI API specialization

Use `backend/ai/llm_gateway.py` as the sole provider router. Verify:

1. authenticated identity reaches the gateway;
2. feature permission is checked before spending;
3. BYOK is resolved before platform credentials when policy allows;
4. platform allowance is checked before the provider waterfall;
5. provider eligibility honors enabled state, credentials, capability, cooldown, and request type;
6. fallback stays within one budget-accounted logical request;
7. response text is non-empty and usable before success is returned;
8. token usage is recorded only for platform-funded calls;
9. exhausted allowance stops platform spending and clearly offers BYOK;
10. KB fallback is labeled as fallback, never presented as live AI.

Personas and frontend code remain provider-agnostic.

### Commerce API specialization

Trace:

```text
catalog/product
→ offer/price mapping
→ checkout request
→ payment-provider session
→ customer redirect
→ webhook raw-body verification
→ idempotent transaction
→ entitlement/membership update
→ fulfillment/download/access
```

Do not change existing prices or invent a payment system. Verify duplicate webhook delivery, invalid signatures, unknown products, expired sessions, refunds, subscription changes, and missing provider configuration.

### Webhook specialization

- Read the raw body before parsing JSON.
- Verify signatures with constant-time comparison.
- Reject missing or invalid signatures with the expected 401/403 behavior.
- Validate event type and required identifiers.
- Deduplicate by provider event ID or the existing unique business key.
- Return 2xx for safe duplicates.
- Avoid performing irreversible side effects twice.
- Record processing status and failures without exposing secrets.

### API testing ladder

1. Static route and contract inspection.
2. Python syntax/import checks.
3. Focused unit tests with mocked dependencies.
4. Router tests using representative authenticated identities.
5. Database integration tests with safe test data.
6. Provider calls only when explicitly safe and configured.
7. Browser/user-path verification through the actual frontend.
8. Production endpoint verification after deployment.

If infrastructure, credentials, or a running database is unavailable, report that exact limitation. Do not call an unexecuted path working.

## 2. Working-in-Code Implementation and Debugging Skill

### Mission
Turn a defect or request into a real, maintainable code change while preserving existing behavior and unrelated user work.

### Before editing

1. Identify the exact files and runtime path involved.
2. Read local project instructions and existing conventions.
3. Inspect callers, callees, schemas, tests, configuration, and route registration.
4. Reproduce the defect with the smallest safe command or test.
5. State the root cause in terms of actual code behavior.
6. Define the smallest change that fixes the root cause.

Do not start by creating a parallel abstraction, route, provider, database, or billing flow.

### Implementation rules

- Prefer editing existing files and abstractions.
- Match naming, formatting, typing, error-handling, and async conventions already used.
- Keep authentication, authorization, validation, persistence, and side effects explicit.
- Do not hide failures with broad catches that return success.
- Do not replace live integrations with canned responses.
- Do not disable security checks to make a test pass.
- Do not leak credentials, tokens, stack traces, or private content.
- Keep secrets out of frontend bundles and logs.
- Make one coherent change at a time when debugging multiple defects.
- Preserve pre-existing modifications and never overwrite unrelated work.

### Root-cause debugging loop

```text
observe failure
→ locate exact request/code path
→ reproduce narrowly
→ identify first incorrect assumption/state/contract
→ patch root cause
→ run focused verification
→ inspect changed path again
→ run regression tests
→ verify complete user path
```

Distinguish these failure classes:

- route absent;
- route unreachable due to prefix/base URL;
- authentication failure;
- authorization failure;
- request validation failure;
- database unavailable or query incorrect;
- external provider failure;
- response-shape mismatch;
- frontend rendering/state bug;
- configuration/deployment mismatch;
- browser policy/CORS/CSP failure.

Do not label all failures “API unavailable.” Identify the first failing boundary.

### Safe code patterns

- Validate external responses before returning success.
- Use explicit timeouts for network calls.
- Preserve provider fallback ordering and capability checks.
- Use idempotent database updates for retried operations.
- Use unique indexes where deduplication is required.
- Scope reads and writes to the authenticated user or authorized resource.
- Return structured, actionable errors.
- Keep fallback results visibly distinguishable from real provider results.
- Use temporary files and atomic replacement for state files where the existing code does so.

### Anti-patterns to reject

- “Fixing” a 404 by changing the frontend to a different unverified endpoint.
- Returning HTTP 200 with an error string.
- Treating a configured key as proof of a working provider.
- Catching every exception and emitting a fake successful reply.
- Adding a second gateway because the first one is hard to trace.
- Copying a route or model instead of fixing the existing one.
- Making a feature appear complete without frontend-to-backend wiring.
- Editing generated files instead of fixing their source.
- Changing prices, permissions, or production secrets without explicit authorization.

### Completion checklist

- Root cause identified from code or execution evidence.
- Change is limited to relevant files.
- Existing callers remain compatible or were updated.
- Focused tests pass.
- Relevant regression tests pass.
- Syntax/import/type checks pass where available.
- No secrets or unrelated changes were introduced.
- Complete user path is traced and executed when the environment allows it.
- Any blocked verification is stated plainly.

## 3. Deep Audit Skill

### Mission
Audit the actual production capability of the repository from discovery through usable result, with priority on API reliability, AI access, commerce, payment handoff, entitlement, and fulfillment.

### Audit principles

- Audit implementation, not documentation alone.
- Follow real callers and real storage paths.
- Treat UI presence as a lead, never as proof.
- Treat environment-variable presence as configuration evidence only.
- Separate `source-confirmed`, `locally-executed`, `integration-tested`, `browser-verified`, and `production-verified` evidence.
- Never mark a feature complete when any required link in the chain is missing.
- Record defects even when the environment prevents reproducing them.
- Repair every concrete, safe, in-scope defect found; do not merely report it.

### Full capability chain

Audit each important feature through:

```text
customer discovery
→ navigation
→ authentication/account
→ permission
→ content or product selection
→ frontend request
→ backend route
→ validation
→ database/provider operation
→ response
→ payment handoff where applicable
→ webhook
→ transaction
→ entitlement
→ fulfillment/media delivery
→ usable rendered result
```

For each boundary, record the caller, target, input, output, failure modes, and evidence.

### Phase A — Repository reconnaissance

- Map backend, frontend, scripts, configuration, tests, deployment files, and generated artifacts.
- Locate actual entrypoints and router registration.
- Locate frontend routing and API clients.
- Locate auth/session code and role/tier definitions.
- Locate database initialization and collection access.
- Locate all external integrations and credential names without printing values.
- Locate test fixtures and smoke/verification tools.
- Check for stale docs that disagree with source.

### Phase B — API capability audit

Build a matrix with:

| Endpoint | Caller | Auth | Authorization | Request | Response | DB/external dependency | Status | Evidence |
|---|---|---|---|---|---|---|---|---|

Specifically identify:

- frontend calls with no backend route;
- backend routes with no frontend caller;
- wrong method or prefix;
- mismatched body/query/path fields;
- missing `user_id` or equivalent identity propagation;
- incorrect role/tier gates;
- unhandled exceptions;
- wrong status codes;
- response shapes the frontend cannot consume;
- provider calls that never execute;
- routes disabled by configuration;
- CORS/CSP/base-URL failures;
- silent frontend catches that hide errors.

### Phase C — Auth and access audit

Test or reason from executable code for:

- anonymous visitor;
- ordinary authenticated user;
- each subscription tier;
- instructor/creator roles;
- admin and executive admin;
- inactive or suspended account;
- resource owner versus non-owner;
- expired/invalid session;
- missing authorization header.

Verify that permissions are enforced server-side and that frontend visibility is not treated as authorization.

### Phase D — AI and provider audit

Trace one real AI request through:

1. route and authentication;
2. user identity and role;
3. feature permission;
4. BYOK lookup and entitlement;
5. platform allowance check;
6. provider registry/credential resolution;
7. capability-aware eligibility;
8. provider request;
9. response validation;
10. token accounting;
11. fallback;
12. final response and status.

Test ordinary user access, exhausted allowance, BYOK, provider failure, multiple failures, unsupported tools, and KB fallback labeling. Do not mistake static KB output for live AI.

### Phase E — Commerce and revenue audit

For each product and membership:

- verify catalog identifier and price mapping;
- verify displayed and submitted price consistency;
- verify checkout route and provider configuration;
- verify customer identity propagation;
- verify payment redirect URL;
- verify webhook signature and raw-body handling;
- verify event idempotency;
- verify transaction persistence;
- verify membership/entitlement update;
- verify fulfillment and access after payment;
- verify duplicate, failed, refunded, and expired flows.

A purchase button that opens a page but cannot create a valid checkout is broken. A successful checkout without entitlement creation is incomplete.

### Phase F — Content, media, and learning audit

Trace:

- public versus protected content;
- course/catalog listing;
- enrollment;
- module access;
- progress writes;
- quiz submission and scoring;
- certificate generation;
- upload validation;
- storage and retrieval;
- media authorization;
- download/stream response;
- frontend rendering and error states.

Check ownership and entitlement at every protected read and write.

### Phase G — Execution and evidence

Use the strongest available evidence in this order:

1. focused automated test;
2. local endpoint execution with representative data;
3. browser interaction through the real frontend;
4. configured integration execution against safe external services;
5. deployed endpoint and browser verification.

For each result, record:

- command or user action;
- environment and configuration state without secret values;
- response/status or rendered outcome;
- relevant logs/error;
- whether the result proves source behavior, local behavior, or production behavior.

### Defect classification

Classify findings as:

- **P0 critical:** authentication bypass, payment/entitlement failure, data exposure, destructive side effect, or total outage;
- **P1 high:** core API unavailable, AI request cannot reach providers, checkout cannot complete, or purchased content cannot be used;
- **P2 medium:** important workflow partially works, fallback is misleading, or errors are silently swallowed;
- **P3 low:** observability, copy, non-critical UX, or cleanup issue.

Each defect must include:

```text
location
→ observed behavior
→ expected behavior
→ root cause
→ impact
→ repair
→ verification
→ remaining limitation
```

### Audit stop conditions

Do not claim “working,” “resolved,” or “complete” when:

- only source inspection was performed;
- only a module import passed;
- only a configuration variable exists;
- the API passed but the frontend user path was not tested;
- a fallback response hides provider failure;
- the deployment was not checked;
- required production credentials or database access were unavailable;
- a test was skipped because it was inconvenient.

Use `UNVERIFIED`, `ENVIRONMENT BLOCKED`, or `BROKEN` precisely.

### Final audit report format

1. **Executive result:** working, partially working, broken, or environment blocked.
2. **Critical defects repaired:** file, root cause, change, evidence.
3. **Remaining defects:** severity, exact location, impact, next safe action.
4. **API matrix:** endpoint, caller, auth, authorization, request, response, status, evidence.
5. **AI/provider matrix:** provider, model, credential source, priority, capability, fallback, evidence.
6. **Commerce chain:** product → checkout → payment → webhook → transaction → entitlement → fulfillment.
7. **Verification record:** commands, tests, browser actions, deployment checks.
8. **Honest limitations:** what could not be executed and why.

## 4. Supabase Specialist Skill

### Mission
Safely integrate, repair, and audit Supabase only where the repository actually uses it. Treat Supabase as a concrete service boundary—Postgres database, Auth, Storage, Realtime, Edge Functions, or client SDK—not as a generic replacement for the existing FastAPI/MongoDB architecture.

### First rule: verify actual usage

Before changing Supabase code:

1. Search backend and frontend source for `supabase`, `createClient`, Supabase URLs, REST endpoints, PostgREST paths, storage URLs, auth listeners, realtime channels, and Edge Function invocations.
2. Identify whether Supabase is active runtime infrastructure, an unused dependency, a migration target, or documentation only.
3. Trace the actual configuration names without printing values. Typical names include `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and frontend-prefixed public variables.
4. Confirm which application layer is authoritative for each data domain. Do not silently move MongoDB-owned data to Supabase.
5. Inspect package/dependency versions and use the SDK already installed; do not add a second client library unnecessarily.

The current requirements file includes the Python `supabase` package, but dependency presence alone does not prove Supabase is configured or used in production.

### Architecture boundaries

- Keep service-role credentials exclusively server-side.
- Public/anonymous keys may be used in the frontend only according to Supabase policy and never for privileged operations.
- Never expose database passwords, service-role keys, JWT secrets, or private storage credentials.
- Do not replace existing FastAPI authentication, MongoDB persistence, or application RBAC without an explicit migration requirement.
- If Supabase and MongoDB coexist, document ownership and synchronization direction for every table/collection.

### Supabase API and client audit

For every Supabase operation, record:

| Operation | Caller | Client/key type | Table/bucket/function | RLS/policy | Filter/ownership | Response/error handling | Evidence |
|---|---|---|---|---|---|---|---|

Verify:

- project URL resolves to the intended environment;
- client is initialized exactly once per intended runtime;
- browser and server clients are not confused;
- auth session persistence and refresh are correct;
- queries select only required columns;
- filters are applied server-side;
- mutations cannot write another user's records;
- errors are checked rather than ignored;
- returned data matches the consuming code's shape;
- network timeouts and unavailable-project behavior are handled honestly.

### Row Level Security and authorization

Treat RLS as mandatory defense in depth, not optional frontend behavior.

- Confirm RLS is enabled on every user-sensitive table.
- Inspect SELECT, INSERT, UPDATE, and DELETE policies separately.
- Verify policies use the correct identity (`auth.uid()`) and do not trust a client-supplied user ID.
- Check ownership on both reads and writes.
- Test anonymous, authenticated owner, authenticated non-owner, privileged staff, and revoked-user cases.
- Ensure service-role access is used only in a trusted backend path and is never sent to React.
- Avoid broad policies such as unconditional `true` for private data.
- Ensure policy changes are tracked in migrations and applied consistently across environments.

### Supabase Auth specialist procedure

Trace:

```text
sign-up/sign-in
→ client session storage
→ access/refresh token handling
→ auth state listener
→ backend token verification
→ application user/profile mapping
→ role/tier/RBAC enforcement
→ sign-out and revocation behavior
```

Check expired tokens, refresh failures, multiple tabs, sign-out persistence, email verification, password reset, OAuth callback errors, and the distinction between a Supabase auth user and the application's own user record.

Never assume a valid Supabase session automatically grants an application role.

### Postgres and migrations

- Review migrations in order and check they are idempotent where the project convention requires it.
- Check foreign keys, unique constraints, nullability, defaults, indexes, timestamps, and cascade behavior.
- Prefer parameterized queries and typed SDK calls.
- Inspect transaction boundaries for multi-step writes.
- Check pagination limits and ordering for stable results.
- Verify migrations in a disposable/test project before production application.
- Never edit production data destructively as a shortcut for a schema defect.
- Do not claim a migration is applied because the SQL file exists; verify migration state through the available safe tooling.

### Storage specialist procedure

For each bucket and file flow, verify:

- bucket privacy and intended public/private behavior;
- upload policy and content-owner enforcement;
- MIME/type and size validation before upload;
- generated signed URL expiry;
- download authorization;
- object path ownership and traversal safety;
- replacement/deletion behavior;
- cache headers and frontend error handling;
- orphan cleanup and metadata consistency.

Do not expose private bucket objects through permanent public URLs.

### Realtime specialist procedure

- Confirm channel/topic names and authorization policies.
- Filter events server-side where possible.
- Avoid subscribing a user to another user's private records.
- Handle reconnect, duplicate events, stale subscriptions, and cleanup on unmount.
- Do not treat a realtime event as durable state until the database write is confirmed.
- Verify the UI remains correct when events arrive out of order or are missed.

### Edge Functions and webhooks

- Verify authentication and authorization at the function boundary.
- Validate JSON schema and reject malformed input.
- Keep secrets in managed server-side secrets.
- Verify webhook signatures against raw request bytes when the provider requires it.
- Make retries idempotent using a unique event/business key.
- Set explicit timeouts and return truthful status codes.
- Log request IDs and safe metadata, never tokens or sensitive payloads.
- Confirm deployment/version before claiming the function is live.

### Supabase failure modes to test

- missing or malformed URL/key;
- wrong project/environment;
- expired session;
- RLS denial;
- missing table or column;
- migration not applied;
- network timeout;
- rate limit;
- duplicate insert;
- stale realtime subscription;
- private storage URL expiry;
- Edge Function 4xx/5xx;
- frontend fallback that incorrectly displays success.

### Supabase completion gate

A Supabase task is complete only when:

- actual Supabase usage was confirmed;
- authority between Supabase and MongoDB is explicit;
- credentials remain protected;
- RLS/policies or backend authorization were verified;
- migrations/schema were executed or clearly marked environment-blocked;
- representative API calls were executed;
- frontend behavior was tested where applicable;
- failures and empty results are distinguishable;
- no duplicate architecture was introduced;
- production verification is explicitly labeled `production-verified` or `UNVERIFIED`.

## 5. Production Operations and Incident Response Skill

### Mission
Diagnose failures in running environments without guessing, hiding symptoms, or making unsafe production changes.

### Incident workflow

```text
signal
→ scope impact
→ identify affected user path
→ capture request ID/status/log evidence
→ locate first failing boundary
→ mitigate safely
→ repair root cause
→ verify recovery
→ document residual risk
```

- Establish whether the failure is frontend, API routing, authentication, authorization, database, provider, deployment, browser policy, or external dependency.
- Use health/readiness endpoints and existing logs before changing code.
- Compare local, staging, and production configuration by key names and non-secret values only.
- Preserve timestamps, status codes, request IDs, provider names, and safe error messages.
- Do not restart services, change production data, rotate secrets, or redeploy without explicit authorization where required.
- Never call a degraded fallback healthy merely because it returns HTTP 200.
- Define rollback or containment before applying a risky repair.

### Production verification

- Verify the deployed commit/version, effective API base URL, health/readiness, and route registration.
- Exercise one authenticated and one unauthenticated path where safe.
- Confirm response status, payload shape, logs, and rendered result.
- Check that the fix is present in the running artifact, not only in the workspace.
- Record `production-verified`, `UNVERIFIED`, or `ENVIRONMENT BLOCKED` explicitly.

## 6. Automated Testing and Contract-Test Skill

### Mission
Create focused tests that exercise real boundaries and prevent regressions without replacing integration verification with mocks.

### Test design

- Test behavior and contracts, not implementation trivia.
- Use representative identities: anonymous, ordinary user, paid tier, creator/instructor, admin, and wrong owner.
- Cover success, validation failure, auth failure, authorization failure, empty state, dependency failure, timeout, rate limit, duplicate request, and retry.
- Assert status code, response schema, side effects, and absence of unauthorized side effects.
- Mock external providers only for deterministic unit tests; keep provider contract and integration tests separate.
- Use isolated test data and clean up safely.
- Avoid tests that pass only because all dependencies are mocked away.

### API contract tests

For each critical frontend call, assert:

- effective method and path;
- required headers and auth behavior;
- request fields and validation;
- response fields and types;
- error payload shape;
- database/provider side effects;
- frontend handling of success and failure.

Generate or inspect OpenAPI only as a supplement; route source and executed behavior remain authoritative.

### Regression gate

After a repair:

1. run the narrow failing test;
2. run adjacent router/service tests;
3. run security and authorization tests;
4. run relevant full-suite tests;
5. execute the complete user path where infrastructure permits;
6. record skipped tests and why.

Never report tests as passing when collection, server startup, credentials, or external services prevented them from running.

## 7. Data Migration and Backward-Compatibility Skill

### Mission
Change persisted data and schemas without silently breaking existing users, deployments, webhooks, or older clients.

### Migration procedure

1. Inventory current documents, indexes, producers, consumers, and historical variants.
2. Define the invariant after migration and a reversible or forward-repair strategy.
3. Make readers tolerant before changing writers where possible.
4. Backfill in bounded, resumable batches.
5. Make backfill idempotent and observable.
6. Add indexes only after checking existing duplicates and write impact.
7. Keep old fields until all readers are migrated, then remove them in a separate deliberate change.
8. Verify representative old, migrated, partial, and malformed records.

- Preserve string/ObjectId and timestamp compatibility deliberately.
- Do not run destructive production migrations as an unverified script.
- Never assume a migration file has executed.
- Ensure webhook retries and old frontend clients remain safe during rollout.
- Document data ownership when MongoDB, Supabase, files, and provider records overlap.

## 8. Observability and Traceability Skill

### Mission
Make every important request explainable without exposing secrets or private content.

### Required signals

For critical flows, capture safe structured metadata:

- request/correlation ID;
- route and operation;
- authenticated subject hash or internal ID where policy permits;
- role/tier decision;
- dependency/provider selected;
- latency and outcome;
- retry/fallback reason;
- database operation category;
- payment/webhook event ID;
- error class and status code.

Never log passwords, API keys, bearer tokens, payment secrets, raw private messages, or full sensitive payloads.

### Trace consistency

- Propagate correlation IDs from frontend/request through backend and external calls where supported.
- Ensure logs distinguish attempted, successful, degraded, rejected, and failed states.
- Add metrics for route errors, latency, provider failures, budget exhaustion, webhook duplicates, and entitlement failures.
- Keep logs useful without turning every request into noisy unstructured text.
- Verify the observability path itself does not block the user response.

## 9. Performance, Capacity, and Resource-Safety Skill

### Mission
Prevent slow, expensive, or unbounded operations from taking down the monolith or exhausting provider/database capacity.

### Review areas

- request timeouts and cancellation propagation;
- async versus blocking calls in FastAPI handlers;
- database connection/client reuse;
- query indexes, projections, pagination, and N+1 access;
- upload and response size limits;
- AI context/max-token bounds;
- concurrency and rate limits;
- memory growth and in-process caches;
- background task failure and retry behavior;
- provider cost and fallback amplification.

- Bound every user-controlled list, text field, file, page, and context window.
- Do not add Redis or paid infrastructure merely to conceal an unbounded in-process design.
- Measure before optimizing where possible.
- Preserve correctness and authorization when introducing caching.
- Ensure cache keys include tenant/user/permission scope where required.

## 10. Accessibility and Resilient UX Skill

### Mission
Ensure core workflows remain usable for keyboard, screen-reader, mobile, slow-network, and error-state users.

### Verification

- Use semantic controls and labels.
- Ensure keyboard focus, visible focus state, logical tab order, and escape behavior.
- Provide accessible names and status announcements for loading, success, errors, and async updates.
- Ensure color is not the sole status indicator and contrast is sufficient.
- Verify forms expose field-level validation and preserve entered data after failure.
- Test responsive layouts and long content.
- Ensure API failures are visible, actionable, and not silently swallowed.
- Keep auth redirects and return paths intact.
- Do not declare a workflow complete because it works only on the happy-path desktop view.

## 11. Dependency, Supply-Chain, and Release-Safety Skill

### Mission
Keep runtime behavior reproducible and changes safe across development, deployment, and rollback.

### Dependency review

- Inspect the existing package manager, lockfiles, Python requirements, and runtime versions.
- Prefer existing dependencies and pinned versions when compatible.
- Check transitive conflicts before upgrading.
- Review security advisories and license constraints when adding or upgrading packages.
- Never install a dependency only to avoid understanding existing code.
- Do not modify generated lockfiles or package metadata without understanding the resulting diff.

### Release review

- Verify build/install commands match the actual deployment platform.
- Ensure build commands build and exit; they must not start a server.
- Ensure runtime commands bind to the required interface and honor injected ports.
- Check migrations, environment names, CORS, CSP, API base URLs, static assets, and health checks.
- Review the exact diff for secrets, debug flags, destructive scripts, unrelated files, and generated artifacts.
- Verify the deployed artifact and critical endpoints after release.
- Preserve a rollback path and do not claim deployment success from a local build alone.

## Existing System Anchors

- Backend: Python/FastAPI with MongoDB via Motor/PyMongo.
- Frontend: Create React App.
- AI authority: `backend/ai/llm_gateway.py`.
- Persona definitions: `backend/ai/persona_loader.py`.
- Existing auth, RBAC, feature control, payment, media, course, and content paths must be reused.
- Secrets remain server-side and are never printed or committed.
- Do not read or act on `Noisy Assets/`.
- Do not use destructive reset, clean, force-push, or history-rewrite operations.
