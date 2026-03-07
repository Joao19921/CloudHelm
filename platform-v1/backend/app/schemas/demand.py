from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DemandCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    raw_input: str = Field(min_length=10)
    input_type: str = Field(default="text")


class DemandResponse(BaseModel):
    id: int
    title: str
    input_type: str
    raw_input: str
    provider_selected: str | None
    status: str
    created_at: datetime


class OrchestrateRequest(BaseModel):
    provider: str = Field(pattern="^(aws|gcp|azure|auto)$")
    llm_provider: str = Field(default="none", pattern="^(none|openai|gemini)$")
    llm_api_key: str | None = Field(default=None, min_length=10, max_length=300)
    llm_model: str | None = Field(default=None, min_length=3, max_length=100)


class DemandAnalysisResponse(BaseModel):
    demand_id: int
    provider: str
    architecture: dict[str, Any]
    costs: dict[str, Any]
    terraform: dict[str, Any]
    ranking: dict[str, Any]
    ai: dict[str, Any]


class TranscriptionResponse(BaseModel):
    transcript: str
    source: str
    model: str
