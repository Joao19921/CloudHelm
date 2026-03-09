from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.app_settings_repository import get_llm_runtime_config, set_llm_runtime_config
from app.repositories.user_repository import get_user_by_id, list_users, update_user_approval
from app.schemas.backoffice import BackofficeUserItem, LLMConfigPayload, LLMConfigResponse
from app.services.audit_service import AuditService
from app.services.email_service import get_email_service

router = APIRouter(prefix="/api/backoffice", tags=["backoffice"])


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return f"{secret[:2]}****"
    return f"{secret[:4]}****{secret[-4:]}"


# Pydantic models
class BulkApprovalRequest(BaseModel):
    user_ids: list[int]


class RoleChangeRequest(BaseModel):
    role: str  # admin | reviewer | user


class TemporaryAccessRequest(BaseModel):
    user_ids: list[int]
    days: int = 7  # Default 7 days


class BackofficeUserDetailedItem(BackofficeUserItem):
    """Extended user info with additional fields."""
    role: str
    approved_at: Optional[datetime] = None
    access_expires_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


@router.get("/users", response_model=list[BackofficeUserDetailedItem])
def backoffice_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """List all users with detailed information."""
    return [
        BackofficeUserDetailedItem(
            id=user.id,
            name=user.name,
            email=user.email,
            github_login=user.github_login,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            auth_provider=user.auth_provider,
            role=user.role,
            approved_at=user.approved_at,
            access_expires_at=user.access_expires_at,
            last_login_at=user.last_login_at,
        )
        for user in list_users(db)
    ]


@router.post("/users/{user_id}/approve", response_model=BackofficeUserDetailedItem)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Approve a single user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    # Update user
    user.is_approved = True
    user.approved_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log action
    AuditService.log_action(
        db=db,
        action="user_approved",
        description=f"User {user.email} approved by {admin.email}",
        admin_user_id=admin.id,
        target_user_id=user.id,
    )
    
    # Send email notification
    email_svc = get_email_service()
    if email_svc:
        email_svc.send_approval_notification(user.email, user.name)
    
    return BackofficeUserDetailedItem(
        id=user.id,
        name=user.name,
        email=user.email,
        github_login=user.github_login,
        is_admin=user.is_admin,
        is_approved=user.is_approved,
        auth_provider=user.auth_provider,
        role=user.role,
        approved_at=user.approved_at,
        access_expires_at=user.access_expires_at,
        last_login_at=user.last_login_at,
    )


@router.post("/users/bulk-approve", response_model=dict)
def bulk_approve_users(
    request: BulkApprovalRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Approve multiple users at once."""
    if not request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user IDs provided.",
        )
    
    approved_count = 0
    for user_id in request.user_ids:
        user = get_user_by_id(db, user_id)
        if user and not user.is_approved:
            user.is_approved = True
            user.approved_at = datetime.now(timezone.utc)
            db.add(user)
            
            # Log action
            AuditService.log_action(
                db=db,
                action="user_approved",
                description=f"User {user.email} approved (bulk)",
                admin_user_id=admin.id,
                target_user_id=user.id,
            )
            
            # Send email
            email_svc = get_email_service()
            if email_svc:
                email_svc.send_approval_notification(user.email, user.name)
            
            approved_count += 1
    
    db.commit()
    return {
        "message": f"Approved {approved_count}/{len(request.user_ids)} users",
        "approved_count": approved_count,
    }


@router.post("/users/{user_id}/revoke", response_model=BackofficeUserDetailedItem)
def revoke_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Revoke user access."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke admin access.",
        )
    
    user.is_approved = False
    user.access_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log action
    AuditService.log_action(
        db=db,
        action="access_revoked",
        description=f"Access revoked for {user.email}",
        admin_user_id=admin.id,
        target_user_id=user.id,
    )
    
    # Send email
    email_svc = get_email_service()
    if email_svc:
        email_svc.send_access_revoked_notification(user.email, user.name)
    
    return BackofficeUserDetailedItem(
        id=user.id,
        name=user.name,
        email=user.email,
        github_login=user.github_login,
        is_admin=user.is_admin,
        is_approved=user.is_approved,
        auth_provider=user.auth_provider,
        role=user.role,
        approved_at=user.approved_at,
        access_expires_at=user.access_expires_at,
        last_login_at=user.last_login_at,
    )


@router.post("/users/{user_id}/role", response_model=BackofficeUserDetailedItem)
def change_user_role(
    user_id: int,
    request: RoleChangeRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Change user role (admin, reviewer, user)."""
    if request.role not in ["admin", "reviewer", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'admin', 'reviewer', or 'user'.",
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    old_role = user.role
    user.role = request.role
    
    # Update is_admin for backwards compatibility
    user.is_admin = (request.role == "admin")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log action
    AuditService.log_action(
        db=db,
        action="role_changed",
        description=f"Role changed from {old_role} to {request.role}",
        admin_user_id=admin.id,
        target_user_id=user.id,
        details={"old_role": old_role, "new_role": request.role},
    )
    
    # Send email
    email_svc = get_email_service()
    if email_svc:
        email_svc.send_role_change_notification(user.email, user.name, request.role)
    
    return BackofficeUserDetailedItem(
        id=user.id,
        name=user.name,
        email=user.email,
        github_login=user.github_login,
        is_admin=user.is_admin,
        is_approved=user.is_approved,
        auth_provider=user.auth_provider,
        role=user.role,
        approved_at=user.approved_at,
        access_expires_at=user.access_expires_at,
        last_login_at=user.last_login_at,
    )


@router.post("/users/temporary-access", response_model=dict)
def grant_temporary_access(
    request: TemporaryAccessRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Grant temporary access to users for testing."""
    if request.days < 1 or request.days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 90.",
        )
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.days)
    updated_count = 0
    
    for user_id in request.user_ids:
        user = get_user_by_id(db, user_id)
        if user:
            user.is_approved = True
            if not user.approved_at:
                user.approved_at = datetime.now(timezone.utc)
            user.access_expires_at = expires_at
            db.add(user)
            
            # Log action
            AuditService.log_action(
                db=db,
                action="temporary_access_granted",
                description=f"Temporary access granted for {request.days} days",
                admin_user_id=admin.id,
                target_user_id=user.id,
                details={"days": request.days, "expires_at": expires_at.isoformat()},
            )
            
            updated_count += 1
    
    db.commit()
    return {
        "message": f"Temporary access granted to {updated_count} user(s)",
        "expires_at": expires_at.isoformat(),
        "updated_count": updated_count,
    }


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """Get recent audit logs."""
    logs = AuditService.get_recent_logs(db, limit)
    return [
        {
            "id": log.id,
            "action": log.action,
            "description": log.description,
            "admin_id": log.user_id,
            "target_user_id": log.target_user_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/llm-config", response_model=LLMConfigResponse)
def read_llm_config(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    config = get_llm_runtime_config(db)
    return LLMConfigResponse(
        provider=config.get("provider", "none"),
        model=config.get("model", ""),
        openai_api_key_masked=_mask_secret(config.get("openai_api_key", "")),
        gemini_api_key_masked=_mask_secret(config.get("gemini_api_key", "")),
    )


@router.put("/llm-config", response_model=LLMConfigResponse)
def update_llm_config(
    payload: LLMConfigPayload,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    provider = payload.provider
    if provider != "none" and not payload.model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model is required.")
    config = set_llm_runtime_config(
        db=db,
        provider=provider,
        model=payload.model.strip(),
        openai_api_key=payload.openai_api_key.strip(),
        gemini_api_key=payload.gemini_api_key.strip(),
    )
    return LLMConfigResponse(
        provider=config["provider"],
        model=config["model"],
        openai_api_key_masked=_mask_secret(config["openai_api_key"]),
        gemini_api_key_masked=_mask_secret(config["gemini_api_key"]),
    )
