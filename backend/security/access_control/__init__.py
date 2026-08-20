"""security/access_control — the unified Access Control Interface & Gateway.

One module location bundling:
    tiers.py       — centralized tier registry + monitored control surface
    gateway.py     — AccessGateway: hard ASGI middleware + per-route FastAPI gate
    dashboard.py   — Executive (Tier 3) dashboard router + HTML UI

Server wiring (server.py):
    from security.access_control import AccessGateway
    from security.access_control.dashboard import router as access_control_router, bind as bind_access_control
    access_gateway = AccessGateway()
    access_gateway.bind(db, audit, current_user)
    bind_access_control(access_gateway)
    api_router.include_router(access_control_router)
    app = access_gateway.wrap(app)   # after ALL routes are registered
"""

from .tiers import (
    ACCESS_TIERS,
    TIER_BY_LEVEL,
    TIER_ORDER,
    ROLE_HIERARCHY,
    STORED_ROLES,
    CONTROL_REGISTRY,
    tier_key_for_role,
    tier_level_for_role,
    find_control,
    registry_snapshot,
    rbac_hierarchy,
)
from .gateway import AccessGateway

__all__ = [
    "ACCESS_TIERS",
    "TIER_BY_LEVEL",
    "TIER_ORDER",
    "ROLE_HIERARCHY",
    "STORED_ROLES",
    "CONTROL_REGISTRY",
    "tier_key_for_role",
    "tier_level_for_role",
    "find_control",
    "registry_snapshot",
    "rbac_hierarchy",
    "AccessGateway",
]
