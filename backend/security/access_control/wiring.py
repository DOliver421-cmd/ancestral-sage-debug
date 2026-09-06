"""security/access_control/wiring.py — server.py mounting helper.

server.py is a ~10.6k-line monolith that some editing tools cannot patch
reliably, so the AccessGateway mounting sequence (documented in the package
__init__ docstring) lives here as one callable. server.py calls it once,
after every route is registered, with:

    access_gateway = mount_access_gateway(
        app=app, api_router=api_router, db=db,
        audit=audit, current_user=current_user,
    )

Behavior:
  - binds db/audit/current_user plus the encrypted DenialAuditBuffer
    (compliance trail; write-only, degrades to unencrypted records when
    AUDIT_ENCRYPTION_KEY is absent — never breaks the gate)
  - exposes the executive route-access dashboard under /api
  - wraps the app with the hard ASGI gate AFTER all routes exist, so the
    gate derives every route's handler rank at wrap time
  - the gate is an ADDITIONAL exec-configurable restriction layer: with no
    exec route policy written it changes nothing about existing behavior and
    never loosens any handler's own dependency
  - failure to mount is logged and non-fatal (app boots exactly as before)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("access_control.wiring")


def mount_access_gateway(
    *,
    app: Any,
    api_router: Any,
    db: Any,
    audit: Any,
    current_user: Any,
) -> Optional[Any]:
    """Bind + mount the AccessGateway and its exec dashboard. Returns the
    gateway instance (also importable as server.access_gateway), or None if
    mounting failed (reason logged; app left untouched)."""
    try:
        from security.access_control import AccessGateway
        from security.access_control.audit import DenialAuditBuffer
        from security.access_control.dashboard import bind as bind_dashboard
        from security.access_control.dashboard import router as access_control_router

        gateway = AccessGateway()
        gateway.bind(db, audit, current_user, DenialAuditBuffer())
        bind_dashboard(gateway)
        api_router.include_router(access_control_router)
        app = gateway.wrap(app)  # returns the SAME FastAPI instance

        logger.info(
            "AccessGateway mounted: %d handler-derived requirements, "
            "%d intentionally-public exclusions",
            len(gateway._handler_requirements),
            len(gateway._public_route_patterns),
        )
        return gateway
    except Exception as exc:  # never block app startup on the gate itself
        logger.warning("AccessGateway not mounted: %s", exc)
        return None
