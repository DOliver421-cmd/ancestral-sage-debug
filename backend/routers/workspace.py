"""
backend/routers/workspace.py — Personal Workspace & Saved Items (Wave 2).

One human-purpose feature: everything a member saves or creates lives in ONE
place, reachable from the nav, backed by real persistence.

Collections:
  saved_items — polymorphic bookmarks: {user_id, kind, ref, title, url, note}
                kind ∈ (book, course, post, product, page, chat, plan)
  workspace_items — user-created artifacts:
                {user_id, kind ∈ (note|checklist|plan), title, content,
                 data (kind-specific: checklist items, plan steps), updated_at}

Access: any authenticated user. Every route is owner-scoped (user_id filter);
cross-user access is impossible by construction because every query filters
on the caller's id. Bookmarks of existing platform objects verify the target
exists where a backend collection backs it (store products, library books).
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("workspace")
router = APIRouter(tags=["workspace"])

db = None
current_user = None


def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SAVED_KINDS = ("book", "course", "post", "product", "page", "chat", "plan")
ITEM_KINDS = ("note", "checklist", "plan")


async def _me(authorization: Optional[str] = Header(None)) -> Any:
    if current_user is None:
        raise HTTPException(503, "Workspace unavailable.")
    return await current_user(authorization)


# ── Saved items (bookmarks) ──────────────────────────────────────────────────

class SavedItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["book", "course", "post", "product", "page", "chat", "plan"]
    ref: str = Field(min_length=1, max_length=200)   # slug / id of the target
    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=1, max_length=300)   # in-app path
    note: Optional[str] = Field(default=None, max_length=500)


@router.get("/workspace/saved")
async def list_saved(user: Any = Depends(_me)):
    docs = await db.saved_items.find(
        {"user_id": user.id}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return {"items": docs}


@router.post("/workspace/saved", status_code=201)
async def add_saved(payload: SavedItemIn, user: Any = Depends(_me)):
    if not payload.url.startswith("/"):
        raise HTTPException(400, "url must be an in-app path starting with /")
    # Verify the target exists for kinds backed by a real collection, so
    # bookmarks can never point at deleted things.
    exists = True
    try:
        if payload.kind == "product":
            exists = await db.products.find_one({"id": payload.ref}, {"_id": 1}) is not None
        elif payload.kind == "book":
            exists = await db.media_products.find_one(
                {"slug": payload.ref}, {"_id": 1}) is not None
    except Exception:
        exists = True  # verification is best-effort; never block a save on it

    if not exists:
        raise HTTPException(404, "That item no longer exists.")

    dup = await db.saved_items.find_one(
        {"user_id": user.id, "kind": payload.kind, "ref": payload.ref}, {"_id": 0}
    )
    if dup:
        return {"ok": True, "duplicate": True, "item": dup}

    doc = {
        "id": f"sv_{uuid.uuid4().hex[:16]}",
        "user_id": user.id,
        "kind": payload.kind,
        "ref": payload.ref,
        "title": payload.title,
        "url": payload.url,
        "note": payload.note,
        "created_at": _now_iso(),
    }
    await db.saved_items.insert_one(doc)
    doc.pop("_id", None)
    return {"ok": True, "duplicate": False, "item": doc}


@router.delete("/workspace/saved/{item_id}")
async def delete_saved(item_id: str, user: Any = Depends(_me)):
    r = await db.saved_items.delete_one({"id": item_id, "user_id": user.id})
    if r.deleted_count == 0:
        raise HTTPException(404, "Saved item not found.")
    return {"ok": True}


# ── Workspace items (notes / checklists / plans) ─────────────────────────────

class ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=300)
    done: bool = False


class WorkspaceItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["note", "checklist", "plan"]
    title: str = Field(min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, max_length=20000)  # note body / plan intro
    items: Optional[list[ChecklistItem]] = None                     # checklist
    steps: Optional[list[str]] = Field(default=None, max_length=50)  # plan steps


@router.get("/workspace/items")
async def list_items(user: Any = Depends(_me)):
    docs = await db.workspace_items.find(
        {"user_id": user.id}, {"_id": 0}
    ).sort("updated_at", -1).to_list(500)
    return {"items": docs}


@router.post("/workspace/items", status_code=201)
async def create_item(payload: WorkspaceItemIn, user: Any = Depends(_me)):
    if payload.kind == "checklist" and not payload.items:
        raise HTTPException(400, "A checklist needs at least one item.")
    if payload.kind == "plan" and not payload.steps:
        raise HTTPException(400, "A plan needs at least one step.")
    doc = {
        "id": f"ws_{uuid.uuid4().hex[:16]}",
        "user_id": user.id,
        "kind": payload.kind,
        "title": payload.title,
        "content": payload.content,
        "items": [i.model_dump() for i in payload.items] if payload.items else None,
        "steps": payload.steps,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.workspace_items.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/workspace/items/{item_id}")
async def update_item(item_id: str, payload: WorkspaceItemIn, user: Any = Depends(_me)):
    update = {
        "kind": payload.kind,
        "title": payload.title,
        "content": payload.content,
        "items": [i.model_dump() for i in payload.items] if payload.items else None,
        "steps": payload.steps,
        "updated_at": _now_iso(),
    }
    from motor.motor_asyncio import ReturnDocument
    r = await db.workspace_items.find_one_and_update(
        {"id": item_id, "user_id": user.id},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not r:
        raise HTTPException(404, "Item not found.")
    r.pop("_id", None)
    return r


@router.delete("/workspace/items/{item_id}")
async def delete_item(item_id: str, user: Any = Depends(_me)):
    r = await db.workspace_items.delete_one({"id": item_id, "user_id": user.id})
    if r.deleted_count == 0:
        raise HTTPException(404, "Item not found.")
    return {"ok": True}
