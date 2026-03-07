import secrets
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import (
    count_users,
    create_github_user,
    create_user,
    get_user_by_email,
    get_user_by_github_id,
)
from app.schemas.auth import (
    GithubAuthUrlResponse,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _github_oauth_enabled() -> bool:
    return bool(settings.github_client_id and settings.github_client_secret)


def _build_github_oauth_url() -> str:
    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email",
        }
    )
    return f"https://github.com/login/oauth/authorize?{query}"


def _exchange_github_code_for_token(code: str) -> str:
    try:
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GitHub OAuth failed: {exc}") from exc
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub token exchange failed.")
    return token


def _fetch_github_profile(access_token: str) -> tuple[str, str, str, str]:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
    try:
        user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=20)
        user_resp.raise_for_status()
        user_data = user_resp.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"GitHub profile fetch failed: {exc}") from exc

    github_id = str(user_data.get("id") or "")
    github_login = user_data.get("login") or ""
    display_name = user_data.get("name") or github_login or "GitHub User"

    if not github_id or not github_login:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub profile is incomplete.")

    email = user_data.get("email")
    if not email:
        try:
            email_resp = requests.get("https://api.github.com/user/emails", headers=headers, timeout=20)
            email_resp.raise_for_status()
            emails = email_resp.json()
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub email fetch failed: {exc}",
            ) from exc
        primary = next((item for item in emails if item.get("primary")), None)
        email = (primary or (emails[0] if emails else {})).get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account must expose at least one email.",
        )
    return github_id, github_login, display_name, email


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    user = create_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    return UserResponse(id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User pending approval by CloudHelm administrator.",
        )
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/github/url", response_model=GithubAuthUrlResponse)
def github_auth_url():
    if not _github_oauth_enabled():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
        )
    return GithubAuthUrlResponse(auth_url=_build_github_oauth_url())


@router.get("/github/callback")
def github_callback(
    code: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
):
    if not _github_oauth_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub OAuth not configured.")
    token = _exchange_github_code_for_token(code)
    github_id, github_login, display_name, email = _fetch_github_profile(token)

    existing = get_user_by_github_id(db, github_id) or get_user_by_email(db, email)
    admin_by_allowlist = github_login.lower() in settings.github_admin_allowlist
    bootstrap_admin = count_users(db) == 0

    if existing:
        existing.github_id = github_id
        existing.github_login = github_login
        existing.name = display_name
        existing.email = email
        existing.auth_provider = "github"
        if admin_by_allowlist or bootstrap_admin:
            existing.is_admin = True
            existing.is_approved = True
        db.add(existing)
        db.commit()
        db.refresh(existing)
        user = existing
    else:
        user = create_github_user(
            db=db,
            name=display_name,
            email=email,
            github_id=github_id,
            github_login=github_login,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            is_admin=admin_by_allowlist or bootstrap_admin,
            is_approved=admin_by_allowlist or bootstrap_admin,
        )

    if not user.is_approved:
        return RedirectResponse(url="/?pending=approval", status_code=status.HTTP_302_FOUND)

    app_token = create_access_token(subject=str(user.id))
    return RedirectResponse(url=f"/?token={app_token}", status_code=status.HTTP_302_FOUND)


@router.get("/session", response_model=SessionResponse)
def current_session(current_user: User = Depends(get_current_user)):
    return SessionResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_admin=current_user.is_admin,
        is_approved=current_user.is_approved,
    )
