from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.models.cloud_catalog_item import CloudCatalogItem


def replace_provider_items(db: Session, provider: str, items: list[dict]) -> int:
    db.execute(delete(CloudCatalogItem).where(CloudCatalogItem.provider == provider))
    objects = [CloudCatalogItem(**item) for item in items]
    db.add_all(objects)
    db.commit()
    return len(objects)


def list_catalog_items(
    db: Session,
    provider: str | None = None,
    search: str | None = None,
    limit: int = 120,
) -> list[CloudCatalogItem]:
    stmt = select(CloudCatalogItem)
    filters = []
    if provider and provider != "all":
        filters.append(CloudCatalogItem.provider == provider)
    if search:
        term = f"%{search.lower()}%"
        filters.append(
            or_(
                func.lower(CloudCatalogItem.display_name).like(term),
                func.lower(CloudCatalogItem.service).like(term),
            )
        )
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(CloudCatalogItem.provider.asc(), CloudCatalogItem.display_name.asc()).limit(limit)
    return list(db.scalars(stmt))


def providers_summary(db: Session) -> list[dict]:
    stmt = (
        select(
            CloudCatalogItem.provider.label("provider"),
            func.count(CloudCatalogItem.id).label("total"),
            func.min(CloudCatalogItem.price).label("min_price"),
            func.max(CloudCatalogItem.price).label("max_price"),
        )
        .group_by(CloudCatalogItem.provider)
        .order_by(CloudCatalogItem.provider.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "provider": row.provider,
            "total": int(row.total),
            "min_price": float(row.min_price) if row.min_price is not None else 0.0,
            "max_price": float(row.max_price) if row.max_price is not None else 0.0,
        }
        for row in rows
    ]
