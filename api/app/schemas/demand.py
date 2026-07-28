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
    has_analysis: bool = False


class OrchestrateRequest(BaseModel):
    provider: str = Field(pattern="^(aws|gcp|azure|oci|auto)$")


class DemandAnalysisResponse(BaseModel):
    demand_id: int
    provider: str
    architecture: dict[str, Any]
    costs: dict[str, Any]
    terraform: dict[str, Any]
    ranking: dict[str, Any]
    ai: dict[str, Any]
    executive_summary: dict[str, Any] = {}
    discovery: dict[str, Any] = {}
    architecture_options: list[dict[str, Any]] = []
    security_baseline: list[dict[str, Any]] = []
    platform_blueprint: dict[str, Any] = {}
    delivery_estimate: dict[str, Any] = {}
    support_model: list[str] = []
    next_steps: list[str] = []
    engineering_principles: list[str] = []
    service_decisions: list[dict[str, Any]] = []
    tradeoffs: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    implementation_plan: list[dict[str, Any]] = []


class TranscriptionResponse(BaseModel):
    transcript: str
    source: str
    model: str
