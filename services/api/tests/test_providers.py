from app.config import settings
from app.providers import bounded_messages, demo_response, model_approval


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


def test_demo_tutor_creates_a_fresh_chapter_practice_prompt():
    response = demo_response("Help me practice the topics from this chapter on vectors")
    assert "u =" in response
    assert "dot" in response.lower()
    assert "component" in response.lower()


def test_demo_tutor_ignores_retrieval_excerpt_keywords():
    response = demo_response("15")
    assert "trace a loop" not in response.lower()


def test_demo_tutor_handles_vector_analysis_practice_and_guidance():
    practice = demo_response("Help me practice Chapter 15 line integrals")
    guidance = demo_response("How should I begin this vector field flux problem?")
    assert "parametrization" in practice
    assert "vector-field integral" in guidance
