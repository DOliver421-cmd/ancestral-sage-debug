"""
backend/routers/finder.py — Resource Finder (Wave 3).

One search surface over content that ALREADY exists on the platform:
  - media_products (starter-library / store digital products)
  - products       (creator products)
  - posts          (community posts)

No new provider, no new data. Public read (content is public), regex
case-insensitive match on title/description. Returns grouped, in-app links so
the frontend never guesses a URL.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

router = APIRouter()
db = None
current_user = None


def bind(_db, _current_user):
    global db, current_user
    db = _db
    current_user = _current_user


def _like(term: str) -> str:
    import re
    return re.escape(term)


@router.get("/finder/search")
async def search(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=25),
    user: Optional[Any] = Depends(lambda: None),
):
    term = q.strip()
    if not term:
        return {"query": term, "results": [], "total": 0}

    rx = {"$regex": _like(term), "$options": "i"}
    projection = {"_id": 0}
    results = []

    # Starter library / digital products
    try:
        async for d in db.media_products.find(
            {"published": True, "$or": [{"title": rx}, {"description": rx}]},
            {**projection, "id": 1, "slug": 1, "title": 1, "description": 1,
             "product_type": 1, "price_cents": 1},
        ).limit(limit):
            results.append({
                "kind": "book",
                "ref": d.get("slug") or d.get("id"),
                "title": d.get("title", "Untitled"),
                "snippet": (d.get("description") or "")[:180],
                "url": f"/store?product={d.get('id')}",
            })
    except Exception:
        pass

    # Creator products
    try:
        async for d in db.products.find(
            {"status": "published", "$or": [{"title": rx}, {"description": rx}]},
            {**projection, "id": 1, "title": 1, "description": 1, "price_cents": 1},
        ).limit(limit):
            results.append({
                "kind": "product",
                "ref": d.get("id"),
                "title": d.get("title", "Untitled"),
                "snippet": (d.get("description") or "")[:180],
                "url": f"/store?product={d.get('id')}",
            })
    except Exception:
        pass

    # Community posts (collection: more_posts, per routers/community.py)
    try:
        async for d in db.more_posts.find(
            {"$or": [{"title": rx}, {"content": rx}]},
            {**projection, "id": 1, "title": 1, "content": 1},
        ).sort("created_at", -1).limit(limit):
            body = d.get("content") or ""
            results.append({
                "kind": "post",
                "ref": d.get("id"),
                "title": d.get("title") or body[:60] or "Community post",
                "snippet": body[:180],
                "url": f"/community?post={d.get('id')}",
            })
    except Exception:
        pass

    return {"query": term, "results": results[: limit * 3], "total": len(results[: limit * 3])}
