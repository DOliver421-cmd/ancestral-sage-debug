"""Regression coverage for the Sovereign provider-response contract."""
import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_result",
    [
        {"provider": "kb_fallback", "text": "A keyword answer"},
        {"provider": "user_budget", "text": "Budget fallback"},
    ],
)
async def test_sovereign_rejects_non_provider_results(monkeypatch, provider_result):
    import routers.studio as studio
    import ai.llm_gateway as llm_gateway

    async def fake_current_user(_authorization=None):
        return studio.User(email="creator@example.test", full_name="Test Creator")

    studio.bind(object(), fake_current_user, lambda *args: 0, lambda *args: None)

    async def fake_call_llm(**_kwargs):
        return provider_result

    monkeypatch.setattr(llm_gateway, "call_llm", fake_call_llm)

    with pytest.raises(HTTPException) as caught:
        await studio.studio_sovereign(
            {"chamber": "lyric-forge", "action": "chat", "message": "Write a hook"},
            studio.User(email="creator@example.test", full_name="Test Creator"),
        )

    assert caught.value.status_code == 503
    assert caught.value.detail == {
        "code": "AI_PROVIDER_UNAVAILABLE",
        "message": "Sovereign AI is unavailable because no live AI provider returned a result.",
        "retryable": True,
    }


@pytest.mark.asyncio
async def test_sovereign_returns_live_provider_result(monkeypatch):
    import routers.studio as studio
    import ai.llm_gateway as llm_gateway

    async def fake_call_llm(**_kwargs):
        return {"provider": "test-provider", "text": "A live provider answer"}

    monkeypatch.setattr(llm_gateway, "call_llm", fake_call_llm)

    result = await studio.studio_sovereign(
        {"chamber": "lyric-forge", "action": "chat", "message": "Write a hook"},
        studio.User(email="creator@example.test", full_name="Test Creator"),
    )

    assert result["response"] == "A live provider answer"
    assert result["artifact"] is None
    assert result["artifact_type"] is None
