from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"
# use argon2 primarily (it avoids the 72‑byte issue) but keep bcrypt in
# the list so existing database hashes continue to verify.  The
# `deprecated="auto"` setting means new hashes will be argon2 while old
# bcrypt hashes are still accepted and automatically upgraded on login.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

# when still using bcrypt in the future we may need a max length; keep a
# generic constant for clarity but argon2 happily accepts long strings.
BCRYPT_MAX_LENGTH = 72


def hash_password(password: str) -> str:
    # we still truncate just in case callers pass extremely long values;
    # argon2 itself doesn't enforce a tight limit but this keeps behaviour
    # consistent with the previous implementation.
    truncated = password[:BCRYPT_MAX_LENGTH]
    return pwd_context.hash(truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate password to BCrypt's maximum length for consistency
    truncated = plain_password[:BCRYPT_MAX_LENGTH]
    return pwd_context.verify(truncated, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        subject: str | None = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        return subject
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
