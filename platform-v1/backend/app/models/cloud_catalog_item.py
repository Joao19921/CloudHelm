from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CloudCatalogItem(Base):
    __tablename__ = "cloud_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    service: Mapped[str] = mapped_column(String(160), index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(12), default="USD")
    unit: Mapped[str] = mapped_column(String(60), default="Unit")
    icon: Mapped[str] = mapped_column(String(255), default="/static/icons/generic.svg")
    source: Mapped[str] = mapped_column(String(40), default="seed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
