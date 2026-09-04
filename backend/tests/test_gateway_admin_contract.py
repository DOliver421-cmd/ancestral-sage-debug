"""Regression tests for gateway-admin mutation contracts."""

import pytest


class _Result:
    modified_count = 1


class _Collection:
    def __init__(self):
        self.docs = []

    async def find_one(self, *_args, **_kwargs):
        return None

    async def update_one(self, *_args, **_kwargs):
        return _Result()


class _Db:
    provider_rankings = _Collection()
    platform_budgets = _Collection()


@pytest.mark.asyncio
async def test_gateway_mutations_use_supported_audit_meta(monkeypatch):
    import routers.gateway_admin as gateway

    audit_calls = []

    async def audit(*args, **kwargs):
        audit_calls.append((args, kwargs))

    gateway.db = _Db()
    gateway.audit = audit
    user = gateway.User(email="admin@morehelp.center", full_name="Admin", role="executive_admin")

    await gateway.gateway_set_ranking(
        gateway.RankingReq(ranking=["groq", "gemini"]), user=user
    )
    await gateway.gateway_set_budget(gateway.BudgetReq(hourly_cap=1000), user=user)

    monkeypatch.setattr(gateway, "_gateway", lambda: type(
        "Gateway", (), {"HOURLY_TOKEN_CAP": 1000, "_hour_tokens_used": 12}
    )())
    await gateway.gateway_reset_budget(user=user)

    assert [kwargs["meta"] for _, kwargs in audit_calls] == [
        {"before": {"ranking": None}, "after": {"ranking": ["groq", "gemini"]}},
        {"before": {"limit": 200000}, "after": {"limit": 1000}},
        {"before": {"tokens_used": 12}, "after": {"tokens_used": 0}},
    ]
