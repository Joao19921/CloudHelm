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


def test_fallback_redacts_gemini_api_key_from_reason():
    result = LLMService._fallback(
        provider="gemini",
        model="gemini-2.5-flash",
        reason="request failed: https://generativelanguage.googleapis.com/v1beta/models/x:generateContent?key=secret-value",
    )

    assert "secret-value" not in result.content
    assert "key=[redacted]" in result.content


def test_gemini_uses_current_model_endpoint_and_header(monkeypatch):
    calls = []

    class Response:
        status_code = 200
        ok = True

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "analysis"}]}}]}

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr("app.services.llm_service.requests.post", fake_post)

    result = LLMService._call_gemini("prompt", "secret-key", "models/gemini-2.5-flash")

    assert result == "analysis"
    assert calls[0][0].endswith("/models/gemini-2.5-flash:generateContent")
    assert "key=" not in calls[0][0]
    assert calls[0][1]["headers"]["x-goog-api-key"] == "secret-key"
