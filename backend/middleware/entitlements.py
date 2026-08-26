"""
entitlements_middleware.py — Tier-Based Access Enforcement
=========================================================

FastAPI decorators and dependencies for enforcing membership tier access.

Usage in routes:
    from middleware.entitlements import require_tier, require_capability
    
    @router.get("/some-endpoint")
    @require_tier("pro")
    async def my_endpoint(request: Request):
        ...
    
    @router.get("/analytics")
    @require_capability("publish.analytics")
    async def get_analytics(request: Request):
        ...
"""

from functools import wraps
from typing import Callable, Optional

from fastapi import Request, HTTPException


# ── Tier Enforcement ──────────────────────────────────────────────────────────

TIER_LEVELS = {"free": 0, "creator": 1, "pro": 2, "studio": 3, "director": 4}


def require_tier(minimum_tier: str):
    """Decorator that checks user's membership tier.
    
    Returns 403 if the user's tier is below the minimum.
    
    Usage:
        @router.get("/admin/settings")
        @require_tier("admin")
        async def get_admin_settings(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_tier = user.get("membership", {}).get("tier", "free")
            user_level = TIER_LEVELS.get(user_tier, 0)
            required_level = TIER_LEVELS.get(minimum_tier, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Upgrade required",
                        "current_tier": user_tier,
                        "required_tier": minimum_tier,
                        "upgrade_url": "/plans",
                    }
                )
            
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


def require_capability(capability: str):
    """Decorator that checks if user has a specific capability.
    
    Returns 403 if the capability is not enabled for the user's tier.
    
    Usage:
        @router.get("/publish/analytics")
        @require_capability("publish.analytics")
        async def get_publish_analytics(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            from services.entitlements import can_access
            
            if not can_access(user, capability):
                user_tier = user.get("membership", {}).get("tier", "free")
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Feature not available on your plan",
                        "capability": capability,
                        "current_tier": user_tier,
                        "upgrade_url": "/plans",
                    }
                )
            
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


def check_usage(resource: str, amount: int = 1):
    """Decorator that checks and increments resource usage.
    
    Returns 403 if the user has exceeded their limit.
    
    Usage:
        @router.post("/projects")
        @check_usage("projects", amount=1)
        async def create_project(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            from services.entitlements import get_limit
            
            limit = get_limit(user, resource)
            
            # Unlimited
            if limit == -1:
                return await func(*args, request=request, **kwargs)
            
            # Get current usage
            usage_key = f"usage_{resource}"
            current = user.get("membership", {}).get(usage_key, 0)
            
            if current + amount > limit:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Resource limit reached",
                        "resource": resource,
                        "current": current,
                        "limit": limit,
                        "upgrade_url": "/plans",
                    }
                )
            
            # Increment usage (caller should handle DB update)
            # For now, just pass through — the route handler will update usage
            request.state.usage_resource = resource
            request.state.usage_amount = amount
            
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator
