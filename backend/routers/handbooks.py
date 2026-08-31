"""routers/handbooks.py — serve the WAI handbooks to authenticated users.

Handbooks are NOT public.  Auth + role check required.
Paid content — not freely downloadable.

Routes:
  GET /handbooks            — list available handbooks (auth required)
  GET /handbooks/{name}     — render a handbook (auth required, role-gated)
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["handbooks"])

# Auth dependency — imported from server.py via bind pattern
current_user = None

def bind(_current_user):
    global current_user
    current_user = _current_user

# backend/handbooks/html — resolved relative to this file (routers/ -> backend/)
_HANDBOOKS_DIR = Path(__file__).resolve().parent.parent / "handbooks" / "html"

# name -> (filename, display title)
HANDBOOKS = {
    "instructor": ("WAI_Instructor_Handbook.html", "M.O.R.E. Help Center — Instructor Handbook"),
    "student":    ("WAI_Student_Handbook.html",    "M.O.R.E. Help Center — Student Handbook"),
    "admin":      ("WAI_Admin_Handbook.html",      "WAI Institute — Admin Handbook"),
    "persona":    ("AI_Persona_Creation_Manual.html", "WAI Institute — AI Persona Creation Manual"),
    "blueprint":  ("Platform_Migration_Blueprint.html", "M.O.R.E. Help Center — Platform Migration Blueprint"),
}


@router.get("/handbooks")
async def handbooks_index(authorization: Optional[str] = Header(None)):
    """List the available handbooks (auth required)."""
    if not current_user:
        raise HTTPException(503, "Service starting up")
    user = await current_user(authorization)
    if not user:
        raise HTTPException(401, "Authentication required")
    available = []
    for name, (fname, title) in HANDBOOKS.items():
        available.append({
            "name": name,
            "title": title,
            "url": f"/api/handbooks/{name}",
            "present": (_HANDBOOKS_DIR / fname).exists(),
        })
    return {"handbooks": available}


@router.get("/handbooks/{name}")
async def get_handbook(name: str, authorization: Optional[str] = Header(None)):
    """Render a handbook as an HTML page (auth required)."""
    if not current_user:
        raise HTTPException(503, "Service starting up")
    user = await current_user(authorization)
    if not user:
        raise HTTPException(401, "Authentication required")
    entry = HANDBOOKS.get(name.lower())
    if not entry:
        raise HTTPException(
            404,
            f"Unknown handbook '{name}'. Available: {', '.join(HANDBOOKS.keys())}",
        )
    fname, _title = entry
    path = _HANDBOOKS_DIR / fname
    if not path.exists():
        logger.warning("handbook %s requested but file missing at %s", name, path)
        raise HTTPException(404, "Handbook file not found on server.")
    return FileResponse(str(path), media_type="text/html", filename=fname)


@router.get("/handbooks/{name}/raw")
async def get_handbook_raw(name: str, authorization: Optional[str] = Header(None)):
    """Return the handbook HTML as a raw string (auth required)."""
    if not current_user:
        raise HTTPException(503, "Service starting up")
    user = await current_user(authorization)
    if not user:
        raise HTTPException(401, "Authentication required")
    entry = HANDBOOKS.get(name.lower())
    if not entry:
        raise HTTPException(404, f"Unknown handbook '{name}'.")
    fname, _title = entry
    path = _HANDBOOKS_DIR / fname
    if not path.exists():
        raise HTTPException(404, "Handbook file not found on server.")
    return HTMLResponse(path.read_text(encoding="utf-8"))
