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

from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.config import (
    _DOCS_ENABLED,
    APP_VERSION,
    BACKUP_ORIGIN,
    SERVE_FRONTEND,
)
from app.database import db, client, _DB_SOURCE, _backup_db
from app.security.rate_limit import _RATE
from app.core.storage import MAX_UPLOAD_SIZE_BYTES, store_upload_from_bytes
from app.core.supabase import resolve_keyword_fallback

# ── Route imports (fault-tolerant) ────────────────────────────────────────────
# Any single import failure is logged but does NOT crash the server.
# /api/version and /api/health always remain available.
import importlib as _importlib

_failed_routes: list = []

def _load(mod_path: str, attr: str = "router"):
    """Import a route module; return its router or None on failure."""
    try:
        m = _importlib.import_module(mod_path)
        return getattr(m, attr, None)
    except Exception as _e:
        import logging as _log
        _log.getLogger("lcewai").error("STARTUP route import failed — %s: %s", mod_path, _e)
        _failed_routes.append(mod_path)
        return None

# Critical — always load these first (health, auth, version)
from app.routes import system, auth   # noqa: E402 (after _load definition)

# Priority routes — direct imports with stderr output so Railway always shows errors
import sys as _sys
import traceback as _tb

def _load_priority(mod_path: str):
    """Import a priority route module. Prints to stderr so errors appear in Railway logs."""
    try:
        import importlib as _il
        m = _il.import_module(mod_path)
        r = getattr(m, "router", None)
        paths = [getattr(ro, "path", "?") for ro in getattr(r, "routes", [])] if r else []
        print(f"[STARTUP] LOADED {mod_path}: {paths}", file=_sys.stderr, flush=True)
        return m
    except Exception as _e:
        print(f"[STARTUP] FAILED {mod_path}: {_e}", file=_sys.stderr, flush=True)
        _tb.print_exc(file=_sys.stderr)
        _sys.stderr.flush()
        return None

_jamil_mod = _load_priority("app.routes.jamil")
_competition_mod = _load_priority("app.routes.competition")
_projects_mod = _load_priority("app.routes.projects")
_missing_mod = _load_priority("app.routes.missing")

# All other routes loaded fault-tolerantly
_route_mods = [
    "app.routes.modules", "app.routes.labs", "app.routes.credentials",
    "app.routes.compliance", "app.routes.notifications", "app.routes.attendance",
    "app.routes.incidents", "app.routes.analytics", "app.routes.community",
    "app.routes.admin", "app.routes.supervisor", "app.routes.auditor",
    "app.routes.payments", "app.routes.adaptive", "app.routes.ai",
    "app.routes.exec", "app.routes.executive_control", "app.routes.legal",
    "app.routes.misc", "app.routes.providers", "app.routes.billing",
    "app.routes.supervisor_v2", "app.routes.site_editor", "app.routes.team_ops",
    "app.routes.partnership", "app.routes.playlist", "app.routes.social",
    "app.routes.position", "app.routes.personas",
    "app.routes.sovereign_pipeline", "app.routes.media_store",
]
_loaded_routers: dict = {}  # mod_path -> router
for _mp in _route_mods:
    _r = _load(_mp)
    if _r is not None:
        _loaded_routers[_mp] = _r

try:
    from app.security.enforcement import TierEnforcementMiddleware as _TEM
    TierEnforcementMiddleware = _TEM
except Exception as _e:
    TierEnforcementMiddleware = None  # type: ignore
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
           @app.on_event("startup")
async def on_startup():
    await _on_startup_impl()
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

# ── Serve built frontend when available (Railway / self-hosted) ─────────────
_build_dir = None
if SERVE_FRONTEND:
    _build_candidates = [
        Path(__file__).resolve().parent.parent / "frontend" / "build",
        Path(__file__).resolve().parent.parent / "frontend" / "dist",
        Path("/app/frontend/build"),
        Path("/app/frontend/dist"),
    ]
    for _candidate in _build_candidates:
        if _candidate.exists() and (_candidate / "index.html").exists():
            _build_dir = _candidate
            break

if _build_dir is not None:
    app.mount("/static", StaticFiles(directory=str(_build_dir / "static")), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(full_path: str):
        return FileResponse(str(_build_dir / "index.html"))

    logger.info("STARTUP: Serving React frontend from %s", _build_dir)


@app.exception_handler(404)
async def _handle_not_found(request: Request, exc: Exception):
    """Return a structured fallback payload for unknown routes without masking real API errors."""
    path = request.url.path

    if path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Route not found",
                "path": path,
                "fallback": "api",
            },
        )

    keyword = path.strip("/").split("/")[-1]
    if keyword and keyword != "":
        match = await resolve_keyword_fallback(keyword)
        if match:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Route not found",
                    "path": path,
                    "fallback": "keyword",
                    "keyword": keyword,
                    "suggested_route": match.get("route"),
                    "description": match.get("description"),
                },
            )

    if _build_dir is not None and SERVE_FRONTEND:
        return FileResponse(str(_build_dir / "index.html"))

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Route not found",
            "path": path,
            "fallback": "none",
        },
    )


@app.exception_handler(Exception)
async def _handle_unexpected_error(request: Request, exc: Exception):
    """Avoid masking unhandled application errors with the SPA fallback."""
    logger.exception("Unhandled exception for %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
        },
    )


@app.post("/api/uploads", include_in_schema=False)
async def upload_phase1_asset(file: UploadFile = File(...)) -> JSONResponse:
    """Accept a file upload, enforce the 10MB limit, and store it safely."""
    if file.size and file.size > MAX_UPLOAD_SIZE_BYTES:
        return JSONResponse(status_code=413, content={"detail": "File exceeds the 10MB upload limit"})

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        return JSONResponse(status_code=413, content={"detail": "File exceeds the 10MB upload limit"})

    try:
        record = store_upload_from_bytes(
            filename=file.filename or "upload.bin",
            content=content,
            content_type=file.content_type or "application/octet-stream",
            metadata={"source": "phase1-upload"},
        )
    except ValueError as exc:
        return JSONResponse(status_code=413, content={"detail": str(exc)})

    return JSONResponse(status_code=200, content={"detail": "Upload stored", "record": record})

# Critical routes always included
app.include_router(system.router,             prefix=_PREFIX)
app.include_router(auth.router,               prefix=_PREFIX)
if _jamil_mod is not None:
    app.include_router(_jamil_mod.router,     prefix=_PREFIX)
if _competition_mod is not None:
    app.include_router(_competition_mod.router, prefix=_PREFIX)
if _projects_mod is not None:
    app.include_router(_projects_mod.router,  prefix=_PREFIX)
if _missing_mod is not None:
    app.include_router(_missing_mod.router,   prefix=_PREFIX)

# Playlist and social have built-in prefixes
_BUILTIN_PREFIX = {"app.routes.playlist", "app.routes.social"}

for _mp, _router in _loaded_routers.items():
    try:
        if _mp in _BUILTIN_PREFIX:
            app.include_router(_router)
        else:
            app.include_router(_router, prefix=_PREFIX)
        logger.info("STARTUP: registered router %s", _mp)
    except Exception as _re:
        logger.error("STARTUP: failed to register router %s: %s", _mp, _re)

# Revenue operations routers (wired at startup)
try:
    from revenue_operations_integration import get_revenue_routers
    for _rev_router in get_revenue_routers():
        app.include_router(_rev_router, prefix=_PREFIX)
except Exception as _rev_err:
    logger.warning("Revenue operations routers unavailable: %s", _rev_err)


# ── Middleware: Tier + Role enforcement (second line of defence) ──────────────
if TierEnforcementMiddleware is not None:
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
# ======================================================================
# PLATFORM HEALTHCHECK ENDPOINT
# ======================================================================
@app.get("/api/version")
def railway_healthcheck_endpoint():
    """
    Directly satisfies Railway's automated healthcheck ping.
    Returns a clean 200 OK status to verify the server is breathing.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "engine": "9-sphere-governance",
        "fallback_matrix": "8-tier-active"
    }

