from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.catalog_repository import list_catalog_items
from app.schemas.pricing import PricingEstimateRequest, PricingEstimateResponse
from app.services.pricing_service import estimate_infrastructure_costs

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/estimate", response_model=PricingEstimateResponse)
def estimate_pricing(
    payload: PricingEstimateRequest,
    db: Session = Depends(get_db),
):
    catalog_items = list_catalog_items(db=db, provider="all", search="", limit=500)
    return estimate_infrastructure_costs(catalog_items=catalog_items, request=payload)
