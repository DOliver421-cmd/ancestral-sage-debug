# SECURITY AUDIT (Phase 20)

**Method:** source inspection this session. **No penetration testing and no live security testing were performed** — this is a code review only.

## Verified controls (SRC)

| Control | Evidence |
|---|---|
| Password hashing | bcrypt via passlib `CryptContext` (server.py) |
| JWT | HS256, `JWT_EXPIRE_HOURS` default 168, `token_version` (tv) in payload; stale tv rejected |
| Session tracking | `db.auth_sessions`; list + revoke endpoints |
| Registration abuse | rate limit 5/min per email-prefix; role forced to `student`; consent + age gates |
| Webhook auth | HMAC-SHA256 `x-signature` verified with `compare_digest`; 404 when secret unset |
| Rate limiting | in-memory sliding window → 429 (register 5/min, public helper 15/min, ai_chat 20/min, ai_tool_chat 15/min) |
| Audit PII redaction | `_PII_KEYS` → `[REDACTED]` before `audit_log` insert |
| Security headers | `security_headers` middleware |
| CORS | env-configurable; default `*` with `allow_credentials` **off** (credentials only when explicit origins set) |
| IP whitelist | opt-in middleware; **open mode when collection empty** |
| API docs | disabled unless `ENABLE_API_DOCS=1` |
| Media | upload requires auth; file serving requires auth + entitlement-aware preview byte cap; GridFS |
| Public AI | prompt_guard on both helper endpoints; IP rate/budget bounds |
| Secrets | server-side env keys only; BYOK keys Fernet-encrypted, masked in responses |
| Password reset | single-use TTL links; recovery codes; secret-gated break-glass (`EXEC_RESET_SECRET`) |

## Notable exposures / risks (SRC)

1. **First-registrant bootstrap:** on an empty DB the first account becomes `executive_admin` (auth.py). On a publicly reachable fresh instance, the first visitor to register claims the owner role. Must be pre-seeded/claimed before campaign.
2. **BYOK entitlement without payment:** `POST /api/byok/activate` flips `byok_enabled` for any authenticated user with no payment check; `POST /api/byok/checkout` has a free "grace path" when payments are unconfigured/failing (routers/byok.py). Revenue control, not platform-cost control.
3. **In-memory rate limiter:** per-process state — a multi-worker deployment silently resets limits per worker.
4. **`is_active` (suspended) enforcement:** field exists; the authorizing path in `current_user` was not traced to a live block this session — **UNVERIFIED** (needs a targeted check/test).
5. **CORS default `*`:** safe only because `allow_credentials` is off; confirm `CORS_ORIGINS` is set explicitly in production.
6. **Untested classes:** IDOR depth across user-scoped routers, XSS in rendered user content, CSRF (token-based auth mitigates), upload abuse (media), GridFS access control, injection, escalation chains. **No automated tests cover these; no live test was possible.**

## Not claimed

- No penetration test. No live security scan. No browser-based security verification. "Code review only."
