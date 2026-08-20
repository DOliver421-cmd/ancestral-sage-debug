"""gateway.py — AccessGateway: the hard server-side gatekeeper.

Two enforcement layers, both driven by the single registry in tiers.py:

1. ASGI middleware  (AccessGateway.wrap) — intercepts EVERY request whose path
   belongs to the monitored control surface BEFORE any handler runs.  A user
   with insufficient tier gets a 403 (or 401 when unauthenticated) and the
   denial is written to the audit log.  This severs public access to all
   scattered control endpoints in one place — no handler edit required.

2. FastAPI dependency (AccessGateway.guard / authorize) — the per-route gate
   used by the executive dashboard itself and available for any future route.

The gateway never loosens an existing handler guard: where a control's
required tier is lower than its handler's own check, the handler still
enforces the stricter rule.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from .audit import DenialAuditBuffer
from .tiers import (
    ACCESS_TIERS,
    CONTROL_REGISTRY,
    find_control,
    tier_key_for_role,
    tier_level_for_role,
)

logger = logging.getLogger("lcewai.access_control")


class AccessGateway:
    """Centralized access-control gateway. Bound to shared deps by server.py."""

    def __init__(self) -> None:
        self._db = None
        self._audit_fn = None
        self._current_user_fn = None
        self._denial_buffer: DenialAuditBuffer | None = None
        self.active = False

    # ── Wiring (called by server.py at startup) ────────────────────────────────
    def bind(self, db, audit_fn, current_user_fn, denial_buffer: DenialAuditBuffer | None = None) -> None:
        """Inject shared dependencies: db, audit(), current_user() and the
        encrypted write-only denial buffer (see security/access_control/audit.py)."""
        self._db = db
        self._audit_fn = audit_fn
        self._current_user_fn = current_user_fn
        self._denial_buffer = denial_buffer
        self.active = True
        if denial_buffer is not None:
            logger.info(
                "AccessGateway denial buffer attached (encryption=%s)",
                "ON" if denial_buffer.encrypted else "OFF - AUDIT_ENCRYPTION_KEY missing",
            )
        logger.info(
            "AccessGateway active: %d controls monitored across %d tiers",
            len(CONTROL_REGISTRY), len(ACCESS_TIERS),
        )

    # ── Core decision ──────────────────────────────────────────────────────────
    def _enforce(self, user, spec) -> tuple:
        """Return (allowed: bool, reason: str, detail: dict)."""
        user_role = getattr(user, "role", "") or ""
        user_tier = tier_key_for_role(user_role)
        user_level = tier_level_for_role(user_role)
        req_level = ACCESS_TIERS[spec["required_tier"]]["level"]

        if user_level < req_level:
            return (
                False,
                "insufficient_tier",
                {
                    "user_role": user_role,
                    "user_tier": user_tier,
                    "user_tier_level": user_level,
                    "required_tier": spec["required_tier"],
                    "required_tier_level": req_level,
                },
            )

        min_role = spec.get("min_role")
        if min_role:
            from roles import role_rank
            if role_rank(user_role) < role_rank(min_role):
                return (
                    False,
                    "insufficient_role",
                    {
                        "user_role": user_role,
                        "user_tier": user_tier,
                        "required_role": min_role,
                        "required_tier": spec["required_tier"],
                    },
                )

        return True, "", {}

    # ── Audit logging (compliance trail) ───────────────────────────────────────
    async def _log_denial(self, user, spec, path, method, reason, detail) -> None:
        actor = getattr(user, "id", None) or getattr(user, "email", None)
        control_key = spec.get("key", "unknown")
        meta = {
            "control": control_key,
            "control_label": spec.get("label"),
            "path": path,
            "method": method,
            "reason": reason,
            "user_role": getattr(user, "role", None),
            "user_tier": tier_key_for_role(getattr(user, "role", "") or ""),
            "required_tier": spec.get("required_tier"),
            **detail,
        }
        if self._audit_fn is not None:
            try:
                await self._audit_fn(actor, "access_denied", target=control_key, meta=meta)
            except Exception:  # pragma: no cover - audit must never break the gate
                logger.exception("access_denied audit write failed")
        if self._denial_buffer is not None:
            try:
                await self._denial_buffer.record({"actor_id": actor, **meta})
            except Exception:  # pragma: no cover - buffer must never break the gate
                logger.exception("access_denied buffer write failed")
        logger.warning(
            "ACCESS_DENIED control=%s path=%s method=%s actor=%s reason=%s",
            control_key, path, method, actor, reason,
        )

    async def _log_anonymous_denial(self, spec, path, method, reason) -> None:
        control_key = spec.get("key", "unknown")
        meta = {
            "control": control_key,
            "control_label": spec.get("label"),
            "path": path,
            "method": method,
            "reason": reason,
            "user_role": None,
            "user_tier": "public",
            "required_tier": spec.get("required_tier"),
        }
        if self._audit_fn is not None:
            try:
                await self._audit_fn(None, "access_denied", target=control_key, meta=meta)
            except Exception:  # pragma: no cover
                logger.exception("access_denied audit write failed")
        if self._denial_buffer is not None:
            try:
                await self._denial_buffer.record({"actor_id": None, **meta})
            except Exception:  # pragma: no cover
                logger.exception("access_denied buffer write failed")
        logger.warning(
            "ACCESS_DENIED control=%s path=%s method=%s actor=None reason=%s",
            control_key, path, method, reason,
        )

    # ── FastAPI dependency (per-route hard gate) ───────────────────────────────
    async def authorize(self, authorization: Optional[str], control_key: str):
        """Resolve the current user and enforce the control's tier.

        Raises HTTPException(401) when unauthenticated, HTTPException(403) when
        clearance is insufficient (denial is audit-logged).  Returns the user
        on success.
        """
        from fastapi import HTTPException

        spec = {**CONTROL_REGISTRY[control_key], "key": control_key}
        user = await self._current_user_fn(authorization)  # raises 401 when missing/invalid
        allowed, reason, detail = self._enforce(user, spec)
        if not allowed:
            await self._log_denial(user, spec, f"/api/.../{control_key}", "dependency", reason, detail)
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — {spec['label']} requires {ACCESS_TIERS[spec['required_tier']]['label']} clearance.",
            )
        return user

    def guard(self, control_key: str):
        """Return a FastAPI dependency that hard-gates *control_key*."""
        from fastapi import Depends, Header

        async def dep(authorization: Optional[str] = Header(None)):
            return await self.authorize(authorization, control_key)

        return dep

    # ── ASGI middleware (defense-in-depth for the whole control surface) ──────
    def middleware(self, app):
        """Return an ASGI callable that gates the registered control surface."""

        async def dispatch(scope, receive, send):
            if scope.get("type") != "http":
                return await app(scope, receive, send)

            path = scope.get("path") or ""
            method = (scope.get("method") or "GET").upper()
            if method == "OPTIONS":  # let CORS preflight through
                return await app(scope, receive, send)

            spec = find_control(path, method)
            if spec is None:
                return await app(scope, receive, send)

            # ── Registered control route: hard gate before the handler ──
            auth_header = None
            for key, value in (scope.get("headers") or []):
                if key.lower() == b"authorization":
                    auth_header = value.decode("latin-1")
                    break

            try:
                user = await self._current_user_fn(auth_header)
            except Exception as exc:
                status = getattr(exc, "status_code", None)
                if status == 401:
                    await self._log_anonymous_denial(spec, path, method, "unauthenticated")
                    return await self._reject(send, 401, "Authentication required for this control.")
                if status == 403:
                    await self._log_anonymous_denial(spec, path, method, "account_deactivated")
                    return await self._reject(send, 403, "Account deactivated.")
                # Fail closed: if we cannot verify clearance, the control stays shut.
                logger.exception("AccessGateway could not resolve user for %s", path)
                return await self._reject(send, 503, "Access control unavailable — request rejected.")

            allowed, reason, detail = self._enforce(user, spec)
            if not allowed:
                await self._log_denial(user, spec, path, method, reason, detail)
                req = ACCESS_TIERS[spec["required_tier"]]
                return await self._reject(
                    send,
                    403,
                    f"Access denied — {spec['label']} requires {req['label']} clearance.",
                )

            return await app(scope, receive, send)

        return dispatch

    def wrap(self, app):
        """Wrap a Starlette/FastAPI app so the middleware runs for every request."""
        return self.middleware(app)

    @staticmethod
    async def _reject(send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail, "error": "ACCESS_DENIED"}).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"cache-control", b"no-store"),
        ]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    # ── Dashboard data helpers ─────────────────────────────────────────────────
    async def denial_stats(self, limit: int = 500) -> dict:
        """Per-control denial counts + last-denied timestamps.

        Prefers the encrypted write-only buffer (access_control_denials),
        falls back to the legacy audit_log collection.
        """
        if self._denial_buffer is not None:
            return await self._denial_buffer.stats(limit=limit)
        stats: dict = {}
        if self._db is None:
            return stats
        try:
            cursor = self._db.audit_log.find(
                {"action": "access_denied"},
                {"_id": 0, "meta.control": 1, "at": 1, "meta.reason": 1},
            ).sort("at", -1).limit(limit)
            rows = await cursor.to_list(length=limit)
        except Exception:
            logger.exception("denial_stats query failed")
            return stats
        for row in rows:
            control = ((row.get("meta") or {}).get("control")) or "unknown"
            entry = stats.setdefault(control, {"denials": 0, "last_denied_at": None})
            entry["denials"] += 1
            if entry["last_denied_at"] is None:
                entry["last_denied_at"] = row.get("at")
        return stats

    async def recent_denials(self, limit: int = 50) -> list:
        """Most recent access-denied audit entries (executive dashboard feed).

        Prefers the encrypted write-only buffer, falls back to audit_log.
        """
        if self._denial_buffer is not None:
            return await self._denial_buffer.recent(limit=limit)
        if self._db is None:
            return []
        try:
            cursor = self._db.audit_log.find(
                {"action": "access_denied"},
                {"_id": 0, "actor_id": 1, "target": 1, "meta": 1, "at": 1},
            ).sort("at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception:
            logger.exception("recent_denials query failed")
            return []
