from pydantic import BaseModel, Field


class CatalogItemResponse(BaseModel):
    id: int
    provider: str
    service: str
    service_type: str = "other"
    display_name: str
    region: str | None
    price: float
    currency: str
    unit: str
    icon: str
    source: str


class CatalogSyncRequest(BaseModel):
    providers: list[str] = Field(default_factory=lambda: ["aws", "gcp", "azure", "oci"])
    limit_per_provider: int = Field(default=50, ge=1, le=100)


class CatalogSyncResponse(BaseModel):
    synced: dict[str, int]
    exported_file: str
