from app.services.llm_service import LLMService


def test_openai_failure_uses_deterministic_fallback(monkeypatch):
    def fail_openai(*args, **kwargs):
        raise RuntimeError("provider timeout")

    monkeypatch.setattr(LLMService, "_call_openai", fail_openai)

    result = LLMService.generate_brief(
        raw_input="Build a resilient API platform with database and observability.",
        cloud_provider="aws",
        llm_provider="openai",
        llm_api_key="invalid-key",
        llm_model="gpt-test",
    )

    assert result.provider == "openai"
    assert result.model == "gpt-test"
    assert result.used_fallback is True
    assert "deterministic fallback" in result.content


def test_gemini_failure_uses_deterministic_fallback(monkeypatch):
    def fail_gemini(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(LLMService, "_call_gemini", fail_gemini)

    result = LLMService.generate_brief(
        raw_input="Build a resilient API platform with database and observability.",
        cloud_provider="gcp",
        llm_provider="gemini",
        llm_api_key="invalid-key",
        llm_model="gemini-test",
    )

    assert result.provider == "gemini"
    assert result.model == "gemini-test"
    assert result.used_fallback is True
    assert "deterministic fallback" in result.content
