"""
missing — Case resolved. Kameron McMullen has been safely recovered.
This router is kept as a stub so existing imports don't break.
All endpoints return a "found safe" message.
"""
from fastapi import APIRouter

router = APIRouter(tags=['missing'])

# Shared state, bound by server.py via bind()
db = current_user = None


def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


@router.get("/missing/photos/{case_id}")
async def get_missing_photos(case_id: str):
    return {"photos": [], "message": "Case resolved — Kameron has been found safe."}


@router.post("/missing/photo")
async def upload_missing_photo():
    return {"ok": False, "message": "Case resolved — no longer accepting photos."}


@router.post("/missing/tip")
async def submit_missing_tip(body: dict):
    return {"ok": False, "message": "Case resolved — Kameron has been found safe."}


@router.get("/missing/file/{file_id}")
async def get_missing_file(file_id: str):
    from fastapi import HTTPException
    raise HTTPException(410, "Case resolved — file no longer available.")
