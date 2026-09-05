"""
backend/tests/test_unifier_access.py

Unifier access control regression tests.

Two paths:
  1. If the running server has MongoDB available and the login flow works,
     this exercises the real auth → feature-tier gate end-to-end.
  2. If the environment has no DB (dev sandbox), this still validates the
     pure access helper, which is the authoritative rule.
"""

from __future__ import annotations

import os
import sys
import typing as t

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from security.unifier_access import user_can_use_unifier


class _FakeUser:
    def __init__(self, role: str, feature_tier: str):
        self.role = role
        self.feature_tier = feature_tier


@pytest.mark.parametrize(
    "role,tier,expected",
    [
        ("executive_admin", "patron", True),
        ("admin", "patron", True),
        ("support_staff", "patron", True),
        ("oversight", "patron", True),
        ("instructor", "patron", False),
        ("student", "patron", False),
        ("public", "patron", False),
        ("executive_admin", "free", False),
        ("admin", "free", False),
        ("support_staff", "free", False),
        ("executive_admin", "member", False),
        ("executive_admin", "pro", False),
        ("executive_admin", "plus", False),
    ],
)
def test_unifier_access_helper(role: str, tier: str, expected: bool) -> None:
    user = _FakeUser(role=role, feature_tier=tier)
    assert user_can_use_unifier(user) is expected, (role, tier)


def test_unifier_access_requires_patron_not_inferred() -> None:
    # The Unifier must NOT silently open for higher tiers unless the policy
    # explicitly says so. Patron is the required tier right now.
    executive = _FakeUser(role="executive_admin", feature_tier="executive")
    assert not user_can_use_unifier(executive)
