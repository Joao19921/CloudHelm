from pathlib import Path
from dataclasses import dataclass

import requests

from app.core.config import settings


@dataclass
class LLMResult:
    provider: str
    model: str
    content: str
    used_fallback: bool = False


class LLMService:
    @staticmethod
    def _load_playbook() -> str:
        candidates = [
            Path("/app/docs/architecture-analysis-playbook.md"),
            Path(__file__).resolve().parents[2] / "docs" / "architecture-analysis-playbook.md",
            Path(__file__).resolve().parents[3] / "docs" / "architecture-analysis-playbook.md",
        ]
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8")
        return ""

    @staticmethod
    def _build_prompt(raw_input: str, provider: str) -> str:
        playbook = LLMService._load_playbook()
        return (
            "You are a principal cloud architect following the CloudHelm Architecture Analysis Playbook. "
            "Produce a deep, execution-oriented technical analysis, not a generic technology list.\n\n"
            f"PLAYBOOK:\n{playbook}\n\n"
            f"DEMAND: {raw_input}\n\n"
            f"PREFERRED CLOUD REFERENCE: {provider}.\n"
            "Apply the playbook strictly. Separate facts, assumptions, gaps and recommendations. "
            "Return structured Markdown with diagrams when useful, explicit alternatives, trade-offs, risks, costs, delivery and operations. "
            "Never invent missing requirements; formulate objective questions instead."
        )

    @staticmethod
    def _fallback(provider: str, model: str, reason: str) -> LLMResult:
        return LLMResult(
            provider=provider,
            model=model,
            content=f"{provider.title()} unavailable. Using deterministic fallback for the architectural foundation. Reason: {reason}",
            used_fallback=True,
        )

    @staticmethod
    def _call_openai(prompt: str, api_key: str, model: str) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                input=prompt,
                temperature=0.2,
            )
            text = getattr(response, "output_text", "") or ""
            return text.strip()
        except Exception as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    @staticmethod
    def _call_gemini(prompt: str, api_key: str, model: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {"temperature": 0.2},
        }
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
        return text.strip()

    @classmethod
    def generate_brief(
        cls,
        raw_input: str,
        cloud_provider: str,
        llm_provider: str = "none",
        llm_api_key: str | None = None,
        llm_model: str | None = None,
    ) -> LLMResult:
        llm_provider = (llm_provider or "none").lower().strip()
        if llm_provider not in {"openai", "gemini", "none"}:
            llm_provider = "none"

        prompt = cls._build_prompt(raw_input=raw_input, provider=cloud_provider)

        if llm_provider == "openai":
            key = llm_api_key or settings.openai_api_key
            model = llm_model or settings.openai_chat_model
            if not key:
                return LLMResult(
                    provider="openai",
                    model=model,
                    content="OpenAI API key missing. Using deterministic fallback for the architectural foundation.",
                    used_fallback=True,
                )
            try:
                text = cls._call_openai(prompt=prompt, api_key=key, model=model)
            except RuntimeError as exc:
                return cls._fallback(provider="openai", model=model, reason=str(exc))
            if not text:
                return cls._fallback(provider="openai", model=model, reason="OpenAI returned empty content.")
            return LLMResult(provider="openai", model=model, content=text, used_fallback=False)

        if llm_provider == "gemini":
            key = llm_api_key or settings.gemini_api_key
            model = llm_model or settings.gemini_model
            if not key:
                return LLMResult(
                    provider="gemini",
                    model=model,
                    content="Gemini API key missing. Using deterministic fallback for the architectural foundation.",
                    used_fallback=True,
                )
            try:
                text = cls._call_gemini(prompt=prompt, api_key=key, model=model)
            except RuntimeError as exc:
                return cls._fallback(provider="gemini", model=model, reason=str(exc))
            if not text:
                return cls._fallback(provider="gemini", model=model, reason="Gemini returned empty content.")
            return LLMResult(provider="gemini", model=model, content=text, used_fallback=False)

        return LLMResult(
            provider="none",
            model="deterministic",
            content="Deterministic fallback mode active for the architectural foundation (no LLM key selected).",
            used_fallback=True,
        )
