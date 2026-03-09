from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Demand(Base):
    __tablename__ = "demands"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    input_type: Mapped[str] = mapped_column(String(30), default="text")
    raw_input: Mapped[str] = mapped_column(Text)
    provider_selected: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    architecture_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    costs_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    terraform_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    owner = relationship("User", back_populates="demands")
