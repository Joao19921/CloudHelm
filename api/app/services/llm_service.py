from dataclasses import dataclass

import requests
from fastapi import HTTPException, status

from app.core.config import settings


@dataclass
class LLMResult:
    provider: str
    model: str
    content: str
    used_fallback: bool = False


class LLMService:
    @staticmethod
    def _build_prompt(raw_input: str, provider: str) -> str:
        return (
            "You are a principal cloud architect. "
            "Generate a concise implementation brief for CloudHelm.\n"
            "Requirements:\n"
            f"{raw_input}\n\n"
            f"Preferred cloud provider: {provider}.\n"
            "Return in plain text with sections:\n"
            "1) Architecture summary\n"
            "2) HA notes for RTO/RPO 15 minutes\n"
            "3) Recommended first sprint tasks\n"
            "Keep under 220 words."
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
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI request failed: {exc}",
            ) from exc

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
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini request failed: {exc}",
            ) from exc

        candidates = data.get("candidates", [])
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini returned no candidates.",
            )
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
            if not key:
                return LLMResult(
                    provider="openai",
                    model=llm_model or settings.openai_chat_model,
                    content="OpenAI API key missing. Using deterministic fallback architecture.",
                    used_fallback=True,
                )
            model = llm_model or settings.openai_chat_model
            text = cls._call_openai(prompt=prompt, api_key=key, model=model)
            if not text:
                text = "OpenAI returned empty content. Using deterministic fallback architecture."
            return LLMResult(provider="openai", model=model, content=text, used_fallback=False)

        if llm_provider == "gemini":
            key = llm_api_key or settings.gemini_api_key
            if not key:
                return LLMResult(
                    provider="gemini",
                    model=llm_model or settings.gemini_model,
                    content="Gemini API key missing. Using deterministic fallback architecture.",
                    used_fallback=True,
                )
            model = llm_model or settings.gemini_model
            text = cls._call_gemini(prompt=prompt, api_key=key, model=model)
            if not text:
                text = "Gemini returned empty content. Using deterministic fallback architecture."
            return LLMResult(provider="gemini", model=model, content=text, used_fallback=False)

        return LLMResult(
            provider="none",
            model="deterministic",
            content="Deterministic mode active (no LLM key selected).",
            used_fallback=True,
        )
