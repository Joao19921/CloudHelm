"""Audit logging service for security and compliance."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording and querying audit logs."""

    @staticmethod
    def log_action(
        db: Session,
        action: str,
        description: str,
        admin_user_id: int,
        target_user_id: int | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Log an administrative action.

        Args:
            db: Database session
            action: Action type (e.g., 'user_approved', 'role_changed', 'access_revoked')
            description: Human-readable description
            admin_user_id: ID of user performing the action
            target_user_id: ID of user being acted upon (if applicable)
            details: Additional context as dict
            ip_address: IP address of the requester

        Returns:
            Created AuditLog record
        """
        try:
            log_entry = AuditLog(
                user_id=admin_user_id,
                action=action,
                target_user_id=target_user_id,
                description=description,
                details=json.dumps(details or {}),
                ip_address=ip_address,
                created_at=datetime.now(timezone.utc),
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            logger.info(
                f"Audit log: {action} by user_id={admin_user_id} "
                f"target={target_user_id} description={description}"
            )
            return log_entry
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            db.rollback()
            raise

    @staticmethod
    def get_logs_for_user(db: Session, target_user_id: int, limit: int = 50):
        """Get all audit logs related to a specific user."""
        return (
            db.query(AuditLog)
            .filter(
                (AuditLog.target_user_id == target_user_id)
                | (AuditLog.user_id == target_user_id)
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_recent_logs(db: Session, limit: int = 100):
        """Get recent audit logs across all users."""
        return (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_logs_by_action(db: Session, action: str, limit: int = 50):
        """Get audit logs by action type."""
        return (
            db.query(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
