"""Regression tests for the public-launch repairs (2026-10).

Each test below pins a behaviour that was broken and is now working, so the
defect cannot silently return:

  1. PATCH /auth/me persists avatar_url + social_handles (they used to be
     dropped by the request model while the UI reported success) and still
     refuses self-service role changes.
  2. GET /auth/me exposes social_handles on your OWN profile (the field
     authorization set omitted it, so a saved Social tab rendered empty).
  3. DELETE /auth/sessions hands back a fresh token so the caller stays
     signed in (it used to bump token_version and sign the caller out).
  4. The Academy parent-issued transcript derives grades from real mastery
     scores (it read stats.avg_score, a key nothing produces, so every
     grade printed as "—" / 0.0).
  5. seed_academy's idempotency hash covers enrichment videos, so a
     video-only content change re-seeds instead of being skipped forever.
  6. The commerce routes that used to 404 are registered with the paths the
     frontend calls: /api/digital/purchases, /api/digital/{key}/download,
     POST /api/payments/gumroad-webhook, and GET /api/ascension-protocols.
  7. A scholarship pledge left "committed" by the grace path can still be
     reconciled to paid by a webhook.

Live-executed where a request is required; pure-unit where the defect is in
a helper. Run:  cd backend && python -m pytest tests/test_launch_repairs.py -v
"""
import asyncio
import os
import sys
import time
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

import server  # noqa: E402
from routers import academy as academy_router  # noqa: E402
from seed_academy import seed_academy  # noqa: E402


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def client():
    with TestClient(server.app) as c:
        yield c


def _register(client):
    email = f"launch_regress_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "LaunchCheck#2026",
        "full_name": "Launch Regression",
        "agreed_terms": True,
        "over_13": True,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── 1. Profile edits persist ─────────────────────────────────────────────────
def test_patch_me_persists_avatar_and_social(client):
    token = _register(client)
    avatar = ("data:image/png;base64,"
              "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
    r = client.patch("/api/auth/me", headers=_auth(token),
                     json={"avatar_url": avatar, "social_handles": {"twitter": "mhc_regress"}})
    assert r.status_code == 200, r.text
    me = client.get("/api/auth/me", headers=_auth(token)).json()
    assert me.get("avatar_url") == avatar
    assert (me.get("social_handles") or {}).get("twitter") == "mhc_regress"


def test_patch_me_refuses_self_role_change(client):
    token = _register(client)
    r = client.patch("/api/auth/me", headers=_auth(token), json={"role": "executive_admin"})
    assert r.status_code == 200  # the field is ignored, never honoured
    me = client.get("/api/auth/me", headers=_auth(token)).json()
    assert me.get("role") == "student"


def test_patch_me_rejects_javascript_avatar(client):
    token = _register(client)
    r = client.patch("/api/auth/me", headers=_auth(token),
                     json={"avatar_url": "javascript:alert(1)"})
    assert r.status_code == 400, r.text


# ── 3. Session revocation keeps the caller signed in ─────────────────────────
def test_revoke_all_sessions_returns_fresh_token(client):
    token = _register(client)
    # A second session to prove something actually gets revoked.
    email = client.get("/api/auth/me", headers=_auth(token)).json()["email"]
    client.post("/api/auth/login", json={"email": email, "password": "LaunchCheck#2026"})
    r = client.delete("/api/auth/sessions", headers=_auth(token))
    assert r.status_code == 200, r.text
    fresh = r.json().get("access_token")
    assert fresh, "revoke-all must re-issue the caller's token"
    me = client.get("/api/auth/me", headers=_auth(fresh))
    assert me.status_code == 200, me.text
    old = client.get("/api/auth/me", headers=_auth(token))
    assert old.status_code == 401  # the pre-revocation token is dead


# ── 4. Transcript grades come from real mastery ──────────────────────────────
def test_transcript_mastery_uses_mastery_avg():
    """_course_stats emits mastery_avg; the transcript must read that key.

    Before the fix it read stats.avg_score (never produced) so every row
    printed grade "—" / 0.0 points on a document a parent signs."""
    import inspect
    src = inspect.getsource(academy_router._compliance_payload)
    assert '"avg_mastery": r["stats"].get("mastery_avg")' in src, (
        "transcript must read mastery_avg from _course_stats")
    assert 'get("avg_score")' not in src


def test_course_stats_shape():
    course = {"slug": "x", "units": [{"lessons": [{"slug": "a"}, {"slug": "b"}]}]}
    progress = {"a": {"status": "passed", "best_score": 90}}
    stats = academy_router._course_stats(course, progress)
    assert stats["mastery_avg"] == 90.0
    assert "avg_score" not in stats  # the key the transcript used to read


# ── 5. Seed version hash covers enrichment videos ────────────────────────────
def test_seed_academy_hash_covers_enrichment_videos():
    import inspect
    src = inspect.getsource(seed_academy)
    assert "enrichment_videos" in src.split("content_version")[0], (
        "the idempotency hash must include the enrichment video list, or a "
        "video-only change never re-seeds the course document")


def test_seed_academy_reapplies_video_change():
    """Video-only change → the course doc is re-written (not skipped)."""

    class _Coll:
        def __init__(self):
            self.docs = {}

        def find(self, *_a, **_k):
            outer = self

            class _C:
                async def to_list(self, _n):
                    return [dict(d) for d in outer.docs.values()]
            return _C()

        async def bulk_write(self, ops, ordered=False):
            for op in ops:
                doc = op._doc
                slug = doc.get("slug")
                if op.__class__.__name__ == "InsertOne":
                    self.docs[slug] = dict(doc)
                else:  # ReplaceOne upsert
                    existing = self.docs.get(slug) or {}
                    merged = {**existing, **doc}
                    self.docs[slug] = merged
            return type("_R", (), {"upserted_count": 0})()

    class _DB:
        def __init__(self):
            self.academy_courses = _Coll()

    db = _DB()

    async def _run():
        await seed_academy(db)
        # Mutate the course's video mapping the way a content edit would,
        # then re-seed: the doc must be updated, not skipped.
        from academy_content import enrichment
        original = enrichment.ENRICHMENT_VIDEOS
        try:
            slug = next(iter(original)) if original else None
            if slug is None:
                pytest.skip("no enrichment videos defined in this content set")
            enrichment.ENRICHMENT_VIDEOS = dict(original)
            enrichment.ENRICHMENT_VIDEOS[slug] = [{
                "video_id": "AAAAAAAAAAA",
                "title": "Regression Probe Video",
                "creator": "Regression",
                "placement": "start",
                "status": "ready",
            }]
            result = await seed_academy(db)
            after = [dict(d) for d in db.academy_courses.docs.values()]
            return slug, result, after
        finally:
            enrichment.ENRICHMENT_VIDEOS = original

    slug, result, after = asyncio.run(_run())
    # The changed course must be re-seeded (updated >= 1) rather than skipped.
    assert result.get("updated", 0) >= 1 or result.get("seeded", 0) >= 1, result
    changed = [d for d in after if d.get("slug") == slug]
    assert changed and len(changed[0].get("enrichment_videos") or []) >= 1


# ── 6. Commerce routes the frontend calls are registered ────────────────────
def _registered_paths():
    """Every path the running app can serve.

    app.routes holds _IncludedRouter wrappers, so walk each wrapper's
    original_router (an APIRouter) as well as api_router itself; a path is
    only "registered" if a real APIRoute serves it.
    """
    paths = set()

    def _walk(routes):
        for r in routes:
            p = getattr(r, "path", "")
            if p and type(r).__name__ == "APIRoute":
                paths.add(p)
            original = getattr(r, "original_router", None)
            if original is not None and hasattr(original, "routes"):
                _walk(original.routes)

    _walk(server.app.routes)
    _walk(server.api_router.routes)
    return paths


def test_digital_purchase_routes_registered():
    paths = _registered_paths()
    assert any(p.endswith("/digital/purchases") for p in paths), sorted(path for path in paths if "digital" in path)[:5]
    assert any("/digital/" in p and "download" in p for p in paths), "GET /api/digital/{product_key}/download must be registered"


def test_gumroad_webhook_registered():
    paths = _registered_paths()
    assert any(p.endswith("/payments/gumroad-webhook") for p in paths)


def test_ascension_protocols_route_registered():
    paths = _registered_paths()
    assert any(p.endswith("/ascension-protocols") for p in paths)


def test_ascension_protocols_returns_the_entry(client):
    r = client.get("/api/ascension-protocols")
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list) and body
    assert body[0]["slug"] == "ascension-protocols"
    assert body[0]["lesson_count"] > 0


# ── 7. Grace-path scholarship pledge reconciles ──────────────────────────────
def test_scholarship_webhook_matches_committed():
    import inspect
    from routers import payments
    src = inspect.getsource(payments)
    assert '"$in": ["pending", "committed"]' in src, (
        "webhooks must reconcile a pledge the grace path left 'committed'")
