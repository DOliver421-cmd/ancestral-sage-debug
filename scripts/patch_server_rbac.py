#!/usr/bin/env python3
"""server.py edit: routers/users.py is not mounted (its /admin/users* routes
duplicate the inline handlers), so its /admin/rbac/matrix routes were
unreachable — the IAM console's matrix tab got SPA HTML. Register the two
matrix routes inline, mirroring routers/users.py exactly."""
from pathlib import Path
from datetime import datetime, timezone

p = Path("backend/server.py")
src = p.read_text(encoding="utf-8")

anchor = '@api_router.get("/admin/users")\n'
assert src.count(anchor) == 1, f"anchor count={src.count(anchor)}"

block = '''@api_router.get("/admin/rbac/matrix")
async def get_rbac_matrix(user: User = Depends(require_role("executive_admin"))):
    """Return the platform permission matrix stored in DB (IAM console)."""
    doc = await db.platform_config.find_one({"key": "rbac_matrix"}, {"_id": 0})
    default_matrix = {
        "student":         {"content_read": True,  "content_create": False, "content_edit_own": True,  "content_delete_own": True,  "user_warn": False, "user_mute": False, "user_ban": False, "api_access": False, "billing_view": False, "export_data": False},
        "instructor":      {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": False, "api_access": True,  "billing_view": False, "export_data": False},
        "admin":           {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
        "executive_admin": {"content_read": True,  "content_create": True,  "content_edit_own": True,  "content_delete_own": True,  "user_warn": True,  "user_mute": True,  "user_ban": True,  "api_access": True,  "billing_view": True,  "export_data": True},
    }
    return {"matrix": (doc or {}).get("value", default_matrix)}


@api_router.patch("/admin/rbac/matrix")
async def set_rbac_matrix(body: dict, user: User = Depends(require_role("executive_admin"))):
    """Update the platform permission matrix (exec-only)."""
    matrix = body.get("matrix")
    if not isinstance(matrix, dict):
        raise HTTPException(400, "matrix must be an object")
    valid_roles = set(ROLE_RANK.keys())
    for role in matrix:
        if role not in valid_roles:
            raise HTTPException(400, f"Unknown role: {role}")
    await db.platform_config.update_one(
        {"key": "rbac_matrix"},
        {"$set": {"key": "rbac_matrix", "value": matrix, "updated_by": user.id, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "exec.rbac.matrix_updated", meta={"roles": list(matrix.keys())})
    return {"ok": True}


'''
src = src.replace(anchor, block + anchor, 1)
p.write_text(src, encoding="utf-8")
print("OK: /admin/rbac/matrix GET+PATCH registered inline")