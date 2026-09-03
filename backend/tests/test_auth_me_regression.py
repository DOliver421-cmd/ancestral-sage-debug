"""Regression test for the live /auth/me 500 (2026-09-02 QA account proof).

Live evidence: POST /api/auth/register 200 → GET /api/auth/me (valid bearer)
returned plain-text 500 "Internal Server Error" on production, while
GET /api/auth/sessions and /api/media/products returned 200 for the same
token. Every failing route resolves the user through server.current_user
(server.User) rather than routers' lenient UserOut.

This suite executes the /auth/me handler chain verbatim against the real
server.User model and the document shape /auth/register actually stores.
It must pass with zero exceptions; any failure here is the root cause of
the live 500.
"""
import pytest

from server import User
from security.field_authorization import FieldAuthorization


# Exactly what routers/auth.register persists (UserOut.model_dump() + extras)
REGISTER_SHAPED_DOC = {
    "id": "b24fb04e-7659-498f-a71a-0868930a73a3",
    "email": "qa.api.proof.1788382944@morehelp.center",
    "full_name": "QA API Proof",
    "role": "student",
    "is_active": True,
    "must_change_password": False,
    "created_at": "2026-09-02T21:01:22.123456+00:00",
    "password_hash": "$2b$12$notarealhashnotarealhashnotarealhash",
    "token_version": 0,
    "terms_accepted_at": "2026-09-02T21:01:22.123456+00:00",
    "over_13_confirmed": True,
    "feature_tier": "free",
}


def test_user_model_accepts_register_shaped_doc():
    """current_user does User(**user_doc) — must not raise for a fresh account."""
    user = User(**REGISTER_SHAPED_DOC)
    assert user.email == REGISTER_SHAPED_DOC["email"]
    assert user.role == "student"


def test_auth_me_handler_chain_end_to_end():
    """The verbatim body of GET /auth/me, plus FastAPI's response_model round-trip."""
    user = User(**REGISTER_SHAPED_DOC)

    visible_fields = FieldAuthorization.get_visible_fields(
        viewer_role=user.role,
        target_role=user.role,
        is_own_profile=True,
    )
    user_dict = user.model_dump()
    filtered = FieldAuthorization.filter_response(user_dict, visible_fields)

    # Handler returns User(**filtered); FastAPI then serializes response_model=User.
    out = User(**filtered)
    dumped = out.model_dump(mode="json")
    assert dumped["email"] == REGISTER_SHAPED_DOC["email"]
    assert "password_hash" not in dumped


def test_user_model_roundtrip_from_find_one_projection():
    """current_user fetches with {'_id': 0, 'password_hash': 0} projection;
    the login path re-serializes the full doc. Both must survive the model."""
    doc = dict(REGISTER_SHAPED_DOC)
    doc.pop("password_hash")
    user = User(**doc)
    # login's post-processing: created_at str → datetime
    from datetime import datetime
    d = user.model_dump()
    assert isinstance(d["created_at"], datetime)
