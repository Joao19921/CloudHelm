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
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_redirect_uri: str = "http://localhost:8000/api/auth/github/callback"
    github_admin_logins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def github_admin_allowlist(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.github_admin_logins.split(",")
            if item.strip()
        }


settings = Settings()
