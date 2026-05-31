"""app/utils/logging_config.py — Structured JSON logging and correlation-ID middleware.

Provides:
  • configure_logging()     — call once at startup to set JSON vs text format
  • CorrelationIdMiddleware — injects X-Request-ID on every request/response
  • RequestLoggingMiddleware — structured JSON log per request with latency
  • get_request_id()        — retrieve the current request's correlation ID
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# ── Correlation ID context variable ───────────────────────────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return _request_id_var.get("")


# ── JSON log formatter ────────────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        doc: dict = {
            "ts":       self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":    record.levelname,
            "logger":   record.name,
            "msg":      record.getMessage(),
            "request_id": get_request_id() or None,
        }
        if record.exc_info:
            doc["exc"] = self.formatException(record.exc_info)
        # Extra fields attached by callers
        for key in ("latency_ms", "status_code", "method", "path", "provider",
                    "tokens_in", "tokens_out", "db_ms", "actor_id", "action"):
            if hasattr(record, key):
                doc[key] = getattr(record, key)
        return json.dumps(doc, default=str)


def configure_logging(app_env: str = "production", level: str | None = None) -> None:
    """Configure root logger: JSON in production, plain text in dev/staging."""
    effective_level = level or ("DEBUG" if app_env != "production" else "INFO")
    root = logging.getLogger()
    root.setLevel(effective_level)
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(effective_level)

    if app_env == "production":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s  %(message)s")
        )
    root.addHandler(handler)


# ── Correlation ID middleware ─────────────────────────────────────────────────

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Read X-Request-ID from inbound headers (or generate one) and echo it back."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token = _request_id_var.set(req_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_var.reset(token)
        response.headers["X-Request-ID"] = req_id
        return response


# ── Structured request logging middleware ─────────────────────────────────────

_req_logger = logging.getLogger("lcewai.requests")

_SKIP_PATHS = frozenset({"/api/health", "/api/version", "/"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured log line per request with method, path, status, latency."""

    def __init__(self, app: ASGIApp, app_env: str = "production") -> None:
        super().__init__(app)
        self._prod = app_env == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip noisy heartbeat paths
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        extra = {
            "method":      request.method,
            "path":        request.url.path,
            "status_code": response.status_code,
            "latency_ms":  latency_ms,
        }
        # Attach user-agent only in non-prod (PII-safe)
        if not self._prod:
            extra["ua"] = request.headers.get("user-agent", "")[:120]

        level = logging.WARNING if response.status_code >= 500 else logging.INFO
        _req_logger.log(level, "%s %s → %d (%dms)",
                        request.method, request.url.path,
                        response.status_code, latency_ms,
                        extra=extra)
        return response
