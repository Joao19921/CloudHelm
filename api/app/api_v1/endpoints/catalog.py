from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.catalog_repository import list_catalog_items, providers_summary
from app.schemas.catalog import CatalogItemResponse, CatalogSyncRequest, CatalogSyncResponse
from app.services.cloud_catalog_service import CloudMasterEngine, get_service_type

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.post("/sync", response_model=CatalogSyncResponse)
def sync_catalog(
    payload: CatalogSyncRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    providers = [provider.lower() for provider in payload.providers]
    providers = [provider for provider in providers if provider in {"aws", "gcp", "azure", "oci"}]
    if not providers:
        providers = ["aws", "gcp", "azure", "oci"]

    engine = CloudMasterEngine()
    synced, exported_file = engine.sync_database(
        db=db,
        providers=providers,
        limit_per_provider=payload.limit_per_provider,
    )
    return CatalogSyncResponse(synced=synced, exported_file=exported_file)


@router.get("/items", response_model=list[CatalogItemResponse])
def get_catalog_items(
    provider: str = Query(default="all"),
    search: str = Query(default=""),
    limit: int = Query(default=120, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items = list_catalog_items(
        db=db,
        provider=provider.lower() if provider else None,
        search=search.strip(),
        limit=limit,
    )
    icon_engine = CloudMasterEngine()
    return [
        CatalogItemResponse(
            id=item.id,
            provider=item.provider,
            service=item.service,
            service_type=get_service_type(item.service, item.provider),
            display_name=item.display_name,
            region=item.region,
            price=item.price,
            currency=item.currency,
            unit=item.unit,
            icon=icon_engine.get_smart_icon(item.service, item.provider),
            source=item.source,
        )
        for item in items
    ]


@router.get("/summary")
def get_catalog_summary(db: Session = Depends(get_db)):
    return {"providers": providers_summary(db)}
