"""Tests for the Academy projects, family-history pathway, and portfolio
(routers/academy.py). The owner's requirements: family history projects,
portfolios, and creation-to-earning pathways, free for every registered
member, with family privacy by default.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from tests.test_academy_api import _auth, _add_student, client  # noqa: E402


PROJECT_KINDS = {"family_history", "research", "creative", "performance", "build", "business"}


def test_kinds_endpoint_is_open_to_members(client):
    r = client.get("/api/academy/projects/kinds")
    assert r.status_code == 200
    kinds = {k["id"] for k in r.json()["kinds"]}
    assert PROJECT_KINDS <= kinds, f"missing kinds: {PROJECT_KINDS - kinds}"
    assert len(r.json()["family_history_steps"]) >= 5
    assert "private to the family account" in r.json()["note"].lower()


def test_family_history_project_seeds_the_pathway(client):
    sid = _add_student(client, "fh1")
    r = client.post("/api/academy/projects", headers=_auth(),
                    json={"student_id": sid, "title": "Our family's move", "kind": "family_history"})
    assert r.status_code == 200, r.text
    p = r.json()["project"]
    assert p["kind"] == "family_history"
    assert [s["id"] for s in p["steps"]] == ["interview", "records", "tree", "migration", "story", "submit"]
    assert p["visibility"] == "family"
    assert p["status"] == "planning"
    assert p["progress_pct"] == 0


def test_artifacts_mark_steps_done_and_reopen_when_cleared(client):
    sid = _add_student(client, "fh2")
    pid = client.post("/api/academy/projects", headers=_auth(),
                      json={"student_id": sid, "title": "Pathway", "kind": "family_history"}).json()["project"]["id"]

    r = client.patch(f"/api/academy/projects/{pid}", headers=_auth(),
                     json={"artifacts": {"interview": "Grandma moved in 1968."}})
    assert r.status_code == 200
    steps = {s["id"]: s for s in r.json()["project"]["steps"]}
    assert steps["interview"]["done"] is True
    assert steps["records"]["done"] is False
    assert r.json()["project"]["steps_completed"] == 1

    r = client.patch(f"/api/academy/projects/{pid}", headers=_auth(),
                     json={"artifacts": {"interview": ""}})
    assert {s["id"]: s for s in r.json()["project"]["steps"]}["interview"]["done"] is False


def test_artifacts_only_accept_steps_of_that_project(client):
    """A project's record can only be written through its own steps: foreign
    keys, non-text values, and oversized values are dropped."""
    sid = _add_student(client, "fh3")
    pid = client.post("/api/academy/projects", headers=_auth(),
                      json={"student_id": sid, "title": "Sanitise", "kind": "family_history"}).json()["project"]["id"]

    r = client.patch(f"/api/academy/projects/{pid}", headers=_auth(),
                     json={"artifacts": {"interview": "ok text", "not-a-step": "x", ";drop": 5,
                                         "big": "y" * 40000, "$where": "hack"}})
    assert r.status_code == 200
    saved = r.json()["project"]["artifacts"]
    assert saved == {"interview": "ok text"}, f"unsafe artifacts survived: {sorted(saved)}"
    # and the unknown key did not create a step
    assert all(s["id"] != "not-a-step" for s in r.json()["project"]["steps"])


def test_submit_requires_complete_steps(client):
    sid = _add_student(client, "fh4")
    pid = client.post("/api/academy/projects", headers=_auth(),
                      json={"student_id": sid, "title": "Incomplete", "kind": "family_history"}).json()["project"]["id"]
    r = client.post(f"/api/academy/projects/{pid}/submit", headers=_auth())
    assert r.status_code == 400
    assert "Add the missing work first" in r.json()["detail"]


def test_submit_moves_the_project_into_the_portfolio(client):
    sid = _add_student(client, "fh5")
    pid = client.post("/api/academy/projects", headers=_auth(),
                      json={"student_id": sid, "title": "Complete", "kind": "family_history",
                           "artifacts": {s: "done" for s in
                                         ["interview", "records", "tree", "migration", "story", "submit"]}}).json()["project"]["id"]
    r = client.post(f"/api/academy/projects/{pid}/submit", headers=_auth())
    assert r.status_code == 200, r.text
    assert r.json()["project"]["status"] == "submitted"
    assert r.json()["project"]["submitted_at"]

    port = client.get(f"/api/academy/portfolio?student_id={sid}", headers=_auth())
    assert port.status_code == 200
    entries = port.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["title"] == "Complete"
    assert {s["title"] for s in entries[0]["steps"]}
    assert "Private to this family account" in port.json()["privacy"]


def test_portfolio_excludes_unsubmitted_projects(client):
    sid = _add_student(client, "fh6")
    client.post("/api/academy/projects", headers=_auth(),
                json={"student_id": sid, "title": "Still in progress", "kind": "family_history"})
    port = client.get(f"/api/academy/portfolio?student_id={sid}", headers=_auth())
    assert port.json()["entries"] == []


def test_non_family_history_projects_have_no_steps(client):
    sid = _add_student(client, "pb1")
    r = client.post("/api/academy/projects", headers=_auth(),
                    json={"student_id": sid, "title": "A business concept", "kind": "business",
                          "summary": "A cooperative laundry."})
    assert r.status_code == 200
    p = r.json()["project"]
    assert p["steps"] == []
    assert p["progress_pct"] == 0
    assert p["kind_label"] == "Business concept"
    # No steps means nothing to gate submission on.
    assert client.post(f"/api/academy/projects/{p['id']}/submit", headers=_auth()).status_code == 200


def test_project_create_rejects_unknown_kind(client):
    sid = _add_student(client, "uk1")
    r = client.post("/api/academy/projects", headers=_auth(),
                    json={"student_id": sid, "title": "x", "kind": "not-a-kind"})
    assert r.status_code == 400
    assert "kind must be one of" in r.json()["detail"]


def test_projects_are_scoped_to_the_owning_account(client):
    sid = _add_student(client, "own1", parent="u1")
    pid = client.post("/api/academy/projects", headers=_auth(),
                      json={"student_id": sid, "title": "Mine", "kind": "research"}).json()["project"]["id"]
    other_sid = _add_student(client, "own2", parent="someone_else")
    r = client.get(f"/api/academy/projects?student_id={other_sid}", headers=_auth())
    assert r.status_code in (403, 404)
    assert pid  # created fine for its owner
    # Another account cannot read, write, delete, or submit this project.
    for verb, method in (("get", "get"), ("patch", "patch"), ("delete", "delete")):
        kwargs = {"json": {"notes": "not yours"}} if method == "patch" else {}
        resp = getattr(client, method)(f"/api/academy/projects/{pid}", headers=_auth("someone_else"), **kwargs)
        assert resp.status_code in (403, 404), f"{verb} leaked across accounts"
    assert client.post(f"/api/academy/projects/{pid}/submit", headers=_auth("someone_else")).status_code in (403, 404)
    # The owner still can.
    assert client.get(f"/api/academy/projects/{pid}", headers=_auth()).status_code == 200


def test_projects_require_authentication(client):
    sid = _add_student(client, "anon1")
    assert client.post("/api/academy/projects", json={"student_id": sid, "title": "x", "kind": "research"}).status_code == 401
