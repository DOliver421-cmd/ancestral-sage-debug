"""
Platform & security services — CORS origins, security headers, static serving.

Extracted verbatim from backend/server.py (monolith refactor, slice 3).
Pure helpers with no dependency on the server module, so there are no
circular-import concerns. server.py registers the middleware at the same
positions as before so execution order is unchanged.
"""
import logging

from fastapi import Request

logger = logging.getLogger("lcewai")

# First-party origins are ALWAYS allowed (mirrors the BACKUP_ORIGIN auto-append).
# This keeps www.morehelp.center / morehelp.center / wai-institute.org and the
# Railway origin working even when CORS_ORIGINS is set to a partial list.
AUTO_CORS_ORIGINS = [
    "https://www.morehelp.center",
    "https://morehelp.center",
    "https://wai-institute.org",
    "https://www.wai-institute.org",
    "https://ancestral-sage-debug-production.up.railway.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
]


def build_cors_origins(env_origins: str = "*", backup_origin: str = "") -> list:
    """Compute the effective CORS allowlist.

    * ``env_origins`` is the raw ``CORS_ORIGINS`` env value (comma-separated).
    * First-party origins are always appended unless ``*`` is present.
    * ``backup_origin`` (e.g. a tunnel URL) is auto-appended so the home/backup
      server is always allowed without touching ``CORS_ORIGINS``.
    """
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    if "*" not in origins:
        for origin in AUTO_CORS_ORIGINS:
            if origin not in origins:
                origins.append(origin)
    if backup_origin and backup_origin not in origins and "*" not in origins:
        origins.append(backup_origin)
        logger.info("CORS: Backup origin added: %s", backup_origin)
    return origins


async def security_headers(request: Request, call_next):
    """Response security headers (extracted verbatim from server.py).

    Registered via ``app.middleware("http")`` at the same position as before,
    so middleware ordering relative to enforce_platform_flags is unchanged.
    """
    response = await call_next(request)
    # Prevent clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Enable XSS protection (supported by older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Strict transport security (force HTTPS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content Security Policy (restrict resource loading)
    # Font CDNs (Google Fonts, Fontshare) must be allowed or the custom brand
    # fonts never load and the site falls back to system fonts. Self-hosting
    # the fonts (audit item) will let us remove these hosts later.
    _FONT_HOSTS = "https://fonts.gstatic.com https://cdn.fontshare.com"
    _STYLE_HOSTS = "https://fonts.googleapis.com https://api.fontshare.com"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        f"style-src 'self' 'unsafe-inline' {_STYLE_HOSTS}; "
        "img-src 'self' data: https:; "
        f"font-src 'self' data: {_FONT_HOSTS}; "
        "connect-src 'self' https:; "
        "frame-src https://namoshun.gumroad.com https://gumroad.com; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    # Referrer policy (limit referrer disclosure)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Permissions policy — allow microphone for voice input surfaces (Director, Supervisor, AI Tutor,
    # Sovereign, Orchestrator, Helper). Camera and geolocation remain blocked.
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=()"
    # CSP: media-src includes blob: for TTS audio (createObjectURL) and data: for inline assets
    # CSP: media-src includes blob: for TTS audio (createObjectURL) and data: for inline assets
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        f"style-src 'self' 'unsafe-inline' {_STYLE_HOSTS}; "
        "img-src 'self' data: https:; "
        f"font-src 'self' data: {_FONT_HOSTS}; "
        "connect-src 'self' https:; "
        "frame-src https://namoshun.gumroad.com https://gumroad.com; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; "
        "media-src 'self' blob:"
    )
    return response


def mount_frontend(app, build_paths) -> bool:
    """Serve the built React SPA (static assets + catch-all). Returns True if served."""
    for bp in build_paths:
        if bp.exists() and (bp / "index.html").exists():
            from fastapi.staticfiles import StaticFiles
            from fastapi.responses import FileResponse

            # Serve static assets
            app.mount("/static", StaticFiles(directory=str(bp / "static")), name="static")

            # SPA catch-all — must come AFTER api_router is included
            @app.get("/{full_path:path}", include_in_schema=False)
            async def _spa_catchall(full_path: str, _bp=bp):
                return FileResponse(str(_bp / "index.html"))

            logger.info("STARTUP: Serving React frontend from %s", bp)
            return True
    return False
