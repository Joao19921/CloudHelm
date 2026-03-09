from pydantic import BaseModel, Field


class BackofficeUserItem(BaseModel):
    id: int
    name: str
    email: str
    github_login: str | None = None
    is_admin: bool
    is_approved: bool
    auth_provider: str


class LLMConfigPayload(BaseModel):
    provider: str = Field(pattern="^(none|openai|gemini)$")
    model: str = Field(default="", max_length=100)
    openai_api_key: str = Field(default="", max_length=300)
    gemini_api_key: str = Field(default="", max_length=300)


class LLMConfigResponse(BaseModel):
    provider: str
    model: str
    openai_api_key_masked: str
    gemini_api_key_masked: str
