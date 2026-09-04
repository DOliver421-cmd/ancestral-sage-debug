"""Contract tests for the persistent short-form video studio surface."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class Cursor:
    def __init__(self, items):
        self.items = list(items)

    def sort(self, *_args):
        return self

    async def to_list(self, _limit):
        return list(self.items)


class Collection:
    def __init__(self, items=None):
        self.items = list(items or [])

    async def insert_one(self, doc):
        self.items.append(dict(doc))

    def find(self, query, _projection=None):
        return Cursor([d for d in self.items if all(d.get(k) == v for k, v in query.items())])

    async def find_one(self, query, _projection=None):
        for doc in self.items:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    async def update_one(self, query, update, **_kwargs):
        for doc in self.items:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update.get("$set", {}))
                return

    async def delete_one(self, query):
        for index, doc in enumerate(self.items):
            if all(doc.get(k) == v for k, v in query.items()):
                self.items.pop(index)
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def delete_many(self, query):
        self.items[:] = [d for d in self.items if not all(d.get(k) == v for k, v in query.items())]


class FakeDb:
    def __init__(self):
        self.video_projects = Collection()
        self.video_scenes = Collection()
        self.video_render_jobs = Collection()


@pytest.fixture
def studio():
    import routers.studio as module

    db = FakeDb()

    async def current_user(_authorization=None):
        return module.User(id="user-1", email="creator@morehelp.test", full_name="Creator", role="student", feature_tier="pro")

    module.bind(db, current_user, lambda *args: 0, lambda *args: None)
    return module, db, await_user(current_user)


def await_user(current_user):
    async def resolve():
        return await current_user()
    return resolve


@pytest.mark.asyncio
async def test_video_project_and_scene_persist_and_reload(studio):
    module, db, resolve_user = studio
    user = await resolve_user()
    project = await module.create_video_project(module.VideoProjectBody(title="Launch short"), user)
    scene = await module.add_video_scene(project["id"], module.VideoSceneBody(media_url="/api/media/file/abc", text="Open strong"), user)

    reopened = await module.get_video_project(project["id"], user)
    assert reopened["scenes"][0]["id"] == scene["id"]
    assert reopened["scenes"][0]["script_text"] == "Open strong"
    assert db.video_projects.items[0]["status"] == "Ready to Preview"

    duplicate = await module.duplicate_video_scene(project["id"], scene["id"], user)
    assert duplicate["id"] != scene["id"]
    assert len((await module.get_video_project(project["id"], user))["scenes"]) == 2
    await module.delete_video_scene(project["id"], duplicate["id"], user)
    assert len((await module.get_video_project(project["id"], user))["scenes"]) == 1


@pytest.mark.asyncio
async def test_video_project_rejects_non_pro_access():
    import routers.studio as module

    user = module.User(email="free@morehelp.test", full_name="Free User", role="student", feature_tier="free")
    with pytest.raises(HTTPException) as caught:
        module._video_access(user)
    assert caught.value.status_code == 403


@pytest.mark.asyncio
async def test_render_requires_scenes_and_media(studio):
    module, _db, resolve_user = studio
    user = await resolve_user()
    project = await module.create_video_project(module.VideoProjectBody(title="Incomplete"), user)
    with pytest.raises(HTTPException) as caught:
        await module.render_video_project(project["id"], user)
    assert caught.value.status_code == 400
    assert "scene" in str(caught.value.detail).lower()

    await module.add_video_scene(project["id"], module.VideoSceneBody(text="Missing media"), user)
    with pytest.raises(HTTPException) as caught:
        await module.render_video_project(project["id"], user)
    assert caught.value.status_code == 400
    assert "needs a picture" in str(caught.value.detail)
