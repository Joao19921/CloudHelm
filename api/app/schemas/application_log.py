from typing import Any

from pydantic import BaseModel, Field


class ApplicationEventRequest(BaseModel):
    event_name: str = Field(min_length=3, max_length=80, pattern="^[a-zA-Z0-9_.-]+$")
    event_category: str = Field(default="interaction", max_length=30)
    event_status: str = Field(default="success", max_length=20)
    demand_id: int | None = Field(default=None, ge=1)
    route: str | None = Field(default=None, max_length=160)
    duration_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    metadata: dict[str, Any] = Field(default_factory=dict)