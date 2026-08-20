"""
Re-export canonical role definitions for router imports.

The single source of truth is backend/roles.py. This module exists so that
routers can do `from routers.roles import Role, ROLE_RANK` while the rest
of the backend uses `from roles import ...`. Both resolve to the same objects.
"""

from roles import (  # noqa: F401 — re-exports
    ALL_ROLES,
    FREE_BYOK_ROLES,
    LEGACY_ROLE_MAP,
    ROLE_PERSONA_DEFAULTS,
    ROLE_RANK,
    Role,
    normalize_role,
    role_rank,
)
