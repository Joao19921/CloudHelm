from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudHelm"
    secret_key: str = "dev-secret"
    access_token_expire_minutes: int = 120
    database_url: str = "sqlite:///./cloudhelm.db"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-1.5-flash"
    transcribe_model: str = "whisper-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
