import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.application_log import ApplicationLog

logger = logging.getLogger(__name__)


class ApplicationLogService:
    @staticmethod
    def record(
        db: Session,
        event_name: str,
        *,
        user_id: int | None = None,
        demand_id: int | None = None,
        event_category: str = "application",
        event_status: str = "success",
        route: str | None = None,
        duration_ms: int | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ApplicationLog:
        safe_metadata = _sanitize_metadata(metadata or {})
        entry = ApplicationLog(
            user_id=user_id,
            demand_id=demand_id,
            event_name=event_name,
            event_category=event_category,
            event_status=event_status,
            route=route,
            duration_ms=duration_ms,
            metadata_json=json.dumps(safe_metadata, ensure_ascii=False),
            ip_address=ip_address,
            user_agent=(user_agent or "")[:512] or None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info("application_event=%s status=%s demand_id=%s user_id=%s", event_name, event_status, demand_id, user_id)
        return entry

    @staticmethod
    def recent(db: Session, limit: int = 100) -> list[ApplicationLog]:
        return db.query(ApplicationLog).order_by(ApplicationLog.created_at.desc()).limit(limit).all()