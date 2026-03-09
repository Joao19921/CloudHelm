from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_github_id(db: Session, github_id: str) -> User | None:
    return db.scalar(select(User).where(User.github_id == github_id))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def count_users(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)


def create_user(db: Session, name: str, email: str, password_hash: str) -> User:
    user = User(name=name, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_github_user(
    db: Session,
    name: str,
    email: str,
    github_id: str,
    github_login: str,
    password_hash: str,
    is_admin: bool,
    is_approved: bool,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        auth_provider="github",
        github_id=github_id,
        github_login=github_login,
        is_admin=is_admin,
        is_approved=is_approved,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_approval(db: Session, user: User, approved: bool) -> User:
    user.is_approved = approved
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
