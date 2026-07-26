from typing import Any

from pydantic import BaseModel, Field


class PricingEstimateRequest(BaseModel):
    providers: list[str] = Field(default_factory=lambda: ["aws", "gcp", "azure", "oci"])
    workload_size: str = Field(default="small", pattern="^(small|medium|large)$")
    monthly_hours: int = Field(default=730, ge=1, le=744)
    compute_units: int = Field(default=1, ge=0, le=500)
    database_units: int = Field(default=1, ge=0, le=100)
    cache_units: int = Field(default=0, ge=0, le=100)
    storage_gb: int = Field(default=100, ge=0, le=1_000_000)
    data_transfer_gb: int = Field(default=100, ge=0, le=1_000_000)
    observability_gb: int = Field(default=20, ge=0, le=1_000_000)


class PricingComponentResponse(BaseModel):
    component: str
    catalog_item_id: int | None
    service: str
    display_name: str
    unit: str
    unit_price: float
    quantity: float
    monthly_cost: float
    source: str


class ProviderPricingEstimate(BaseModel):
    provider: str
    currency: str
    monthly_total: float
    min: float
    max: float
    components: list[PricingComponentResponse]
    used_fallback: bool
    sources: list[str]


class PricingEstimateResponse(BaseModel):
    currency: str
    monthly_estimate: dict[str, dict[str, float]]
    providers: dict[str, ProviderPricingEstimate]
    assumptions: dict[str, Any]
    notes: list[str]
