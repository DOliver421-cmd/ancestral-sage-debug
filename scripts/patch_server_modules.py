#!/usr/bin/env python3
"""server.py edits (file tools cannot match this large file — Vly snapshot is stale):

1. Add `optional_current_user` dependency after `current_user`.
2. GET /api/modules listing: optional auth so the catalog is public.
"""
from pathlib import Path

p = Path("backend/server.py")
src = p.read_text(encoding="utf-8")

# 1. optional_current_user after current_user's return line (unique anchor:
# the token_version check block end + require_role definition start).
anchor = "    return User(**user_doc)\n\n\ndef require_role(*roles):"
assert src.count(anchor) == 1, f"anchor1 count={src.count(anchor)}"
optional_dep = (
    "    return User(**user_doc)\n\n\n"
    "async def optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:\n"
    "    \"\"\"Like current_user, but anonymous visitors are allowed (None).\n"
    "    Used for public catalog surfaces whose CONTENT stays auth-gated.\"\"\"\n"
    "    try:\n"
    "        return await current_user(authorization)\n"
    "    except HTTPException:\n"
    "        return None\n\n\n"
    "def require_role(*roles):"
)
src = src.replace(anchor, optional_dep, 1)

# 2. Public listing
old_listing = (
    '@api_router.get("/modules", response_model=List[Module])\n'
    "async def list_modules(user: User = Depends(current_user)):\n"
)
new_listing = (
    '@api_router.get("/modules", response_model=List[Module])\n'
    "# Public catalog directory — the /modules page must always list what\n"
    "# exists. Per-module CONTENT stays auth-gated via GET /modules/{slug}.\n"
    "async def list_modules(user: Optional[User] = Depends(optional_current_user)):\n"
)
assert src.count(old_listing) == 1, f"listing count={src.count(old_listing)}"
src = src.replace(old_listing, new_listing, 1)

p.write_text(src, encoding="utf-8")
print("OK: optional_current_user added; /modules listing is public")