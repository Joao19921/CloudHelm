from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    auth_provider: Mapped[str] = mapped_column(String(20), default="local")
    github_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    github_login: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    
    # Access control
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Role-based access (enum-like: admin, reviewer, user)
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin | reviewer | user
    
    # Legacy field (kept for compatibility, use role instead)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Access expiration (for temporary access)
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    demands = relationship("Demand", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
