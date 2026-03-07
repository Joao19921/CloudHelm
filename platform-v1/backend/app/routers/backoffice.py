from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.app_settings_repository import get_llm_runtime_config, set_llm_runtime_config
from app.repositories.user_repository import get_user_by_id, list_users, update_user_approval
from app.schemas.backoffice import BackofficeUserItem, LLMConfigPayload, LLMConfigResponse

router = APIRouter(prefix="/api/backoffice", tags=["backoffice"])


def _mask_secret(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return f"{secret[:2]}****"
    return f"{secret[:4]}****{secret[-4:]}"


@router.get("/users", response_model=list[BackofficeUserItem])
def backoffice_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return [
        BackofficeUserItem(
            id=user.id,
            name=user.name,
            email=user.email,
            github_login=user.github_login,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            auth_provider=user.auth_provider,
        )
        for user in list_users(db)
    ]


@router.post("/users/{user_id}/approve", response_model=BackofficeUserItem)
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    updated = update_user_approval(db, user, approved=True)
    return BackofficeUserItem(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        github_login=updated.github_login,
        is_admin=updated.is_admin,
        is_approved=updated.is_approved,
        auth_provider=updated.auth_provider,
    )


@router.post("/users/{user_id}/revoke", response_model=BackofficeUserItem)
def revoke_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot revoke admin access.")
    updated = update_user_approval(db, user, approved=False)
    return BackofficeUserItem(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        github_login=updated.github_login,
        is_admin=updated.is_admin,
        is_approved=updated.is_approved,
        auth_provider=updated.auth_provider,
    )


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
