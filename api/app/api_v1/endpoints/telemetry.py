from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.application_log import ApplicationEventRequest
from app.services.application_log_service import ApplicationLogService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events", status_code=204)
def record_event(
    payload: ApplicationEventRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ApplicationLogService.record(
        db,
        event_name=payload.event_name,
        event_category=payload.event_category,
        event_status=payload.event_status,
        demand_id=payload.demand_id,
        route=payload.route,
        duration_ms=payload.duration_ms,
        metadata=payload.metadata,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
