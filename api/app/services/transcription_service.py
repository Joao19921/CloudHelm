from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


@dataclass
class TranscriptResult:
    text: str
    source: str
    model: str


class TranscriptionService:
    allowed_types = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/m4a",
        "audio/webm",
        "audio/ogg",
        "video/mp4",
    }
    max_file_size = 25 * 1024 * 1024

    @classmethod
    async def transcribe(cls, audio_file: UploadFile) -> TranscriptResult:
        file_bytes = await audio_file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file is empty.",
            )
        if len(file_bytes) > cls.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Audio file too large. Max supported size is 25MB.",
            )
        if audio_file.content_type and audio_file.content_type not in cls.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported content type: {audio_file.content_type}",
            )

        if settings.openai_api_key:
            try:
                from openai import OpenAI

                suffix = Path(audio_file.filename or "audio").suffix or ".mp3"
                with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp.flush()
                    client = OpenAI(api_key=settings.openai_api_key)
                    with open(tmp.name, "rb") as payload:
                        transcript = client.audio.transcriptions.create(
                            model=settings.transcribe_model,
                            file=payload,
                        )
                text = (getattr(transcript, "text", "") or "").strip()
                if text:
                    return TranscriptResult(
                        text=text,
                        source="openai",
                        model=settings.transcribe_model,
                    )
            except Exception:
                # Falls back to deterministic local transcript stub.
                pass

        filename = audio_file.filename or "audio_file"
        fallback_text = (
            f"Transcricao automatica em modo local para '{filename}'. "
            "Defina OPENAI_API_KEY para transcricao completa por IA."
        )
        return TranscriptResult(text=fallback_text, source="fallback", model="local-stub")
