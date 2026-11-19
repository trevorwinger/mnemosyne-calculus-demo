from app.config import settings
import asyncio

import pytest
from fastapi import HTTPException

import app.providers as providers
from app.providers import AvailableModel, bounded_messages, demo_response, model_approval, resolve_reasoning_level


def test_context_keeps_newest_messages_within_server_budget():
    original = settings.max_context_chars
    settings.max_context_chars = 10
    try:
        result = bounded_messages([
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "second message"},
        ])
    finally:
        settings.max_context_chars = original
    assert result == [{"role": "assistant", "content": "nd message"}]


def test_embedding_only_model_cannot_become_chat_eligible():
    approved, reason = model_approval(["embedding"])
    assert not approved
    assert reason == "This installed model is not chat-capable."


def test_every_installed_chat_model_is_eligible_without_an_allowlist():
    approved, reason = model_approval(["completion"])
    assert approved
    assert reason is None


def test_reasoning_level_uses_only_the_selected_models_supported_values():
    model = AvailableModel("gpt-oss", None, None, None, None, "ollama", True, thinking_values=("low", "medium", "high"), thinking_default="medium")
    assert resolve_reasoning_level(model, "high") == "high"
    assert resolve_reasoning_level(model, None) == "medium"
    # Sessions created before the setting existed used false. Upgrade them to
    # a model-defined default instead of rejecting their first new message.
    assert resolve_reasoning_level(model, False) == "medium"
    with pytest.raises(HTTPException, match="not supported"):
        resolve_reasoning_level(model, "maximum")


def test_nonthinking_model_keeps_reasoning_disabled():
    model = AvailableModel("plain-chat", None, None, None, None, "ollama", True)
    assert resolve_reasoning_level(model, False) is False
    with pytest.raises(HTTPException, match="does not support"):
        resolve_reasoning_level(model, True)


def test_generation_sends_the_selected_reasoning_level_to_ollama(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "A guided hint."}}

    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): pass
        async def post(self, _url, json):
            captured.update(json)
            return Response()

    monkeypatch.setattr(providers.httpx, "AsyncClient", lambda **_kwargs: Client())
    model = AvailableModel("gpt-oss", None, None, None, None, "ollama", True, thinking_values=("low", "medium", "high"), thinking_default="medium")
    asyncio.run(providers.generate(model, [{"role": "user", "content": "Help me begin."}], "high"))
    assert captured["think"] == "high"


def test_demo_tutor_creates_a_fresh_chapter_practice_prompt():
    response = demo_response("Help me practice the topics from this chapter on limits")
    assert "fresh example" in response
    assert "x^2-16" in response
    assert "first" in response.lower()


def test_demo_tutor_ignores_retrieval_excerpt_keywords():
    response = demo_response("15")
    assert "trace a loop" not in response.lower()
