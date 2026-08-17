"""routers/handbooks.py — serve the WAI handbooks to students & instructors.

Serves the static handbook documents (backend/handbooks/html/*.html) as public
routes so the flagship curriculum and the original instructor/student guides are
readable in-app. No auth required — these are public reference documents.

Routes:
  GET /handbooks            — list available handbooks
  GET /handbooks/{name}     — render a handbook (instructor | student | admin | persona)
"""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["handbooks"])

# backend/handbooks/html — resolved relative to this file (routers/ -> backend/)
_HANDBOOKS_DIR = Path(__file__).resolve().parent.parent / "handbooks" / "html"

# name -> (filename, display title)
HANDBOOKS = {
    "instructor": ("WAI_Instructor_Handbook.html", "WAI Institute — Instructor Handbook"),
    "student":    ("WAI_Student_Handbook.html",    "WAI Institute — Student Handbook"),
    "admin":      ("WAI_Admin_Handbook.html",      "WAI Institute — Admin Handbook"),
    "persona":    ("AI_Persona_Creation_Manual.html", "WAI Institute — AI Persona Creation Manual"),
}


@router.get("/handbooks")
async def handbooks_index():
    """List the available handbooks (public)."""
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
async def get_handbook(name: str):
    """Render a handbook as an HTML page (public)."""
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
async def get_handbook_raw(name: str):
    """Return the handbook HTML as a raw string (public, for embedding/tools)."""
    entry = HANDBOOKS.get(name.lower())
    if not entry:
        raise HTTPException(404, f"Unknown handbook '{name}'.")
    fname, _title = entry
    path = _HANDBOOKS_DIR / fname
    if not path.exists():
        raise HTTPException(404, "Handbook file not found on server.")
    return HTMLResponse(path.read_text(encoding="utf-8"))
