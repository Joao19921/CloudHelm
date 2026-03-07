import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

LLM_SETTINGS_KEY = "llm.runtime.config"


def get_setting(db: Session, key: str) -> AppSetting | None:
    return db.get(AppSetting, key)


def set_setting(db: Session, key: str, value: str) -> AppSetting:
    current = db.get(AppSetting, key)
    if current:
        current.value = value
        db.add(current)
        db.commit()
        db.refresh(current)
        return current
    created = AppSetting(key=key, value=value)
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


def get_llm_runtime_config(db: Session) -> dict[str, Any]:
    setting = get_setting(db, LLM_SETTINGS_KEY)
    if not setting:
        return {"provider": "none", "model": "", "openai_api_key": "", "gemini_api_key": ""}
    try:
        parsed = json.loads(setting.value)
    except json.JSONDecodeError:
        return {"provider": "none", "model": "", "openai_api_key": "", "gemini_api_key": ""}
    return {
        "provider": parsed.get("provider", "none"),
        "model": parsed.get("model", ""),
        "openai_api_key": parsed.get("openai_api_key", ""),
        "gemini_api_key": parsed.get("gemini_api_key", ""),
    }


def set_llm_runtime_config(
    db: Session,
    provider: str,
    model: str,
    openai_api_key: str,
    gemini_api_key: str,
) -> dict[str, Any]:
    payload = {
        "provider": provider,
        "model": model,
        "openai_api_key": openai_api_key,
        "gemini_api_key": gemini_api_key,
    }
    set_setting(db=db, key=LLM_SETTINGS_KEY, value=json.dumps(payload))
    return payload
