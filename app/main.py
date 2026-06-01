"""app/main.py — FastAPI application entrypoint for the modular monolith.

Replaces backend/server.py as the application object.
All route modules are imported and registered here.
Middleware, startup/shutdown, and CORS are configured here.

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.config import (
    _DOCS_ENABLED,
    APP_VERSION,
    BACKUP_ORIGIN,
    SERVE_FRONTEND,
)
from app.database import db, client, _DB_SOURCE, _backup_db
from app.security.rate_limit import _RATE
from app.routes import (
    adaptive,
    admin,
    ai,
    analytics,
    attendance,
    auth,
    auditor,
    community,
    compliance,
    credentials,
    incidents,
    labs,
    misc,
    modules,
    notifications,
    payments,
    supervisor,
    system,
)
from app.routes import exec as exec_routes
from app.routes import executive_control, legal
from app.routes import providers, billing, supervisor_v2, site_editor
from app.routes import partnership, playlist, social
from app.security.enforcement import TierEnforcementMiddleware
from app.config import APP_ENV, _DOCS_ENABLED as _DOCS_ENABLED_CFG
from app.utils.alerting import init_sentry
from app.utils.logging_config import (
    configure_logging,
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
)

# ── Logging — must run before anything else emits log records ─────────────────
configure_logging(APP_ENV)
logger = logging.getLogger("lcewai")

# ── Sentry — initialise before the app object so exceptions during startup ─────
# ── are captured. No-op if SENTRY_DSN is not set. ────────────────────────────
init_sentry()

# ── FastAPI app ───────────────────────────────────────────────────────────────
_show_docs = _DOCS_ENABLED or APP_ENV != "production"
app = FastAPI(
    title="W.A.I. Training Platform",
    version=APP_VERSION,
    description="W.A.I. — Workforce Apprentice Institute API.",
    redirect_slashes=False,
    docs_url="/api/docs" if _show_docs else None,
    redoc_url="/api/redoc" if _show_docs else None,
    openapi_url="/api/openapi.json" if _show_docs else None,
)

# ── Optional routers from unfinished refactor packages ───────────────────────
try:
    from routers import ai as _ai_router_pkg
    app.include_router(_ai_router_pkg.router, prefix="/api")
except Exception as _ai_router_err:
    logging.getLogger("server").warning(
        "Optional 'routers.ai' package not present (%s) — inline /api/ai handlers remain active.",
        _ai_router_err,
    )


# ── Middleware: security headers ──────────────────────────────────────────────
_CSP_PRODUCTION = (
    "default-src 'self'; "
    "script-src 'self'; "                       # no unsafe-inline/eval in prod
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "media-src 'self' blob:; "
    "upgrade-insecure-requests"
)
_CSP_DEVELOPMENT = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # dev HMR needs these
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self' ws: wss: https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "media-src 'self' blob:"
)
_CSP = _CSP_PRODUCTION if APP_ENV == "production" else _CSP_DEVELOPMENT


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"
    response.headers["Content-Security-Policy"] = _CSP
    return response


# ── Middleware: platform lock ─────────────────────────────────────────────────
@app.middleware("http")
async def enforce_platform_flags(request: Request, call_next):
    path = request.url.path
    exempt = (
        path in ("/api/health", "/api/version", "/")
        or path.startswith("/api/auth/")
        or path.startswith("/api/admin/platform/flags")
        or path.startswith("/api/admin/")
    )
    if not exempt and db is not None:
        try:
            doc = await db.platform_flags.find_one(
                {"_id": "flags"}, {"_id": 0, "flags.platform_locked": 1}
            )
            if doc and doc.get("flags", {}).get("platform_locked", {}).get("enabled"):
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Platform is currently locked by the executive team. Please check back shortly."},
                )
        except Exception:
            pass
    return await call_next(request)


# ── Middleware: IP whitelist ───────────────────────────────────────────────────
@app.middleware("http")
async def enforce_ip_whitelist(request: Request, call_next):
    exec_paths = (
        "/api/admin/system",
        "/api/admin/access",
        "/api/admin/sage-audit",
        "/api/admin/director",
        "/api/sovereign/",
        "/api/admin/mfa",
        "/api/admin/staff-meetings",
        "/api/exec/control/",   # Executive control layer — all writes IP-gated
    )
    path = request.url.path
    if not any(path.startswith(p) for p in exec_paths):
        return await call_next(request)
    if db is None:
        return await call_next(request)
    try:
        entries = await db.ip_whitelist.find(
            {"role": "executive_admin"}, {"_id": 0, "ip": 1}
        ).to_list(length=500)
        if not entries:
            return await call_next(request)
        import ipaddress as _ipmod
        allowed_nets = []
        for e in entries:
            raw = (e.get("ip") or "").strip()
            if not raw:
                continue
            try:
                allowed_nets.append(_ipmod.ip_network(raw, strict=False))
            except ValueError:
                pass
        if not allowed_nets:
            return await call_next(request)
        forwarded_for = request.headers.get("x-forwarded-for", "")
        raw_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (
            request.client.host if request.client else ""
        )
        try:
            client_addr = _ipmod.ip_address(raw_ip)
        except ValueError:
            return JSONResponse(status_code=403, content={"detail": "Access denied: unresolvable source IP."})
        if any(client_addr in net for net in allowed_nets):
            return await call_next(request)
        logger.warning("IP whitelist block: %s → %s", raw_ip, path)
        return JSONResponse(status_code=403, content={"detail": "Access denied: your IP is not on the executive access list."})
    except Exception:
        return await call_next(request)


# ── Structured request logging + correlation IDs — added via add_middleware ───
# (registered after router wiring so middleware stack order is correct)


# ── Include all routers ───────────────────────────────────────────────────────
_PREFIX = "/api"

app.include_router(system.router,        prefix=_PREFIX)
app.include_router(auth.router,          prefix=_PREFIX)
app.include_router(modules.router,       prefix=_PREFIX)
app.include_router(labs.router,          prefix=_PREFIX)
app.include_router(credentials.router,   prefix=_PREFIX)
app.include_router(compliance.router,    prefix=_PREFIX)
app.include_router(notifications.router, prefix=_PREFIX)
app.include_router(attendance.router,    prefix=_PREFIX)
app.include_router(incidents.router,     prefix=_PREFIX)
app.include_router(analytics.router,     prefix=_PREFIX)
app.include_router(community.router,     prefix=_PREFIX)
app.include_router(admin.router,         prefix=_PREFIX)
app.include_router(supervisor.router,    prefix=_PREFIX)
app.include_router(auditor.router,       prefix=_PREFIX)
app.include_router(payments.router,      prefix=_PREFIX)
app.include_router(adaptive.router,      prefix=_PREFIX)
app.include_router(ai.router,                  prefix=_PREFIX)
app.include_router(exec_routes.router,         prefix=_PREFIX)
app.include_router(executive_control.router,   prefix=_PREFIX)
app.include_router(legal.router,               prefix=_PREFIX)
app.include_router(misc.router,                prefix=_PREFIX)
# Phase 2–3: Supervisor reconstruction modules
app.include_router(providers.router,           prefix=_PREFIX)
app.include_router(billing.router,             prefix=_PREFIX)
app.include_router(supervisor_v2.router,       prefix=_PREFIX)
app.include_router(site_editor.router,        prefix=_PREFIX)
app.include_router(partnership.router,        prefix=_PREFIX)
app.include_router(playlist.router)   # prefix="/api/playlist" built-in
app.include_router(social.router)     # prefix="/api/social" built-in

# Revenue operations routers (wired at startup)
try:
    from revenue_operations_integration import get_revenue_routers
    for _rev_router in get_revenue_routers():
        app.include_router(_rev_router, prefix=_PREFIX)
except Exception as _rev_err:
    logger.warning("Revenue operations routers unavailable: %s", _rev_err)


# ── Middleware: Tier + Role enforcement (second line of defence) ──────────────
app.add_middleware(TierEnforcementMiddleware)

# ── Middleware: Structured request logging (innermost — runs last, sees status) ─
app.add_middleware(RequestLoggingMiddleware, app_env=APP_ENV)

# ── Middleware: Correlation ID (outermost — runs first, echoed in all responses) ─
app.add_middleware(CorrelationIdMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
if BACKUP_ORIGIN and BACKUP_ORIGIN not in _cors_origins and "*" not in _cors_origins:
    _cors_origins.append(BACKUP_ORIGIN)
    logger.info("CORS: Backup origin added: %s", BACKUP_ORIGIN)
_allow_creds = _cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_creds,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(_on_startup_impl())


async def _on_startup_impl():
    from app.services.startup import run_startup
    await run_startup(app)


# ── Shutdown ──────────────────────────────────────────────────────────────────
@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        from wai_institute.scripts.system_activation import stop_scout_scheduler
        stop_scout_scheduler()
    except Exception:
        pass
    try:
        from revenue_operations_integration import stop_revenue_operations
        stop_revenue_operations()
    except Exception:
        pass
    if client:
        client.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
