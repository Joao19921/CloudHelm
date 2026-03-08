import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import AppSetting, CloudCatalogItem, Demand, User  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.backoffice import router as backoffice_router
from app.routers.catalog import router as catalog_router
from app.routers.demands import router as demands_router
from app.routers.ui import router as ui_router

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


logger = logging.getLogger(__name__)


def wait_for_database(max_attempts: int = 20, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            logger.warning(
                "Database not ready yet (attempt %s/%s). Retrying in %ss.",
                attempt,
                max_attempts,
                delay_seconds,
            )
            time.sleep(delay_seconds)


def ensure_users_schema_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    dialect = engine.dialect.name.lower()

    migrations: list[str] = []
    if "auth_provider" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(20) DEFAULT 'local'")
    if "github_id" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN github_id VARCHAR(64) NULL")
    if "github_login" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN github_login VARCHAR(120) NULL")
    if "is_admin" not in existing_columns:
        migrations.append(
            "ALTER TABLE users ADD COLUMN is_admin TINYINT(1) DEFAULT 0"
            if dialect == "mysql"
            else "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"
        )
    if "is_approved" not in existing_columns:
        migrations.append(
            "ALTER TABLE users ADD COLUMN is_approved TINYINT(1) DEFAULT 0"
            if dialect == "mysql"
            else "ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT FALSE"
        )
    if "approved_at" not in existing_columns:
        migrations.append(
            "ALTER TABLE users ADD COLUMN approved_at DATETIME NULL"
            if dialect == "mysql"
            else "ALTER TABLE users ADD COLUMN approved_at TIMESTAMP NULL"
        )
    if "role" not in existing_columns:
        migrations.append("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
    if "access_expires_at" not in existing_columns:
        migrations.append(
            "ALTER TABLE users ADD COLUMN access_expires_at DATETIME NULL"
            if dialect == "mysql"
            else "ALTER TABLE users ADD COLUMN access_expires_at TIMESTAMP NULL"
        )

    with engine.begin() as connection:
        for statement in migrations:
            connection.execute(text(statement))
        connection.execute(text("UPDATE users SET auth_provider='local' WHERE auth_provider IS NULL"))
        approved_condition = "is_approved = 1" if dialect == "mysql" else "is_approved IS TRUE"
        approved_count = connection.execute(
            text(f"SELECT COUNT(*) FROM users WHERE {approved_condition}")
        ).scalar()
        if int(approved_count or 0) == 0:
            if dialect == "mysql":
                connection.execute(
                    text(
                        "UPDATE users u "
                        "JOIN (SELECT id FROM users ORDER BY id ASC LIMIT 1) seed ON u.id = seed.id "
                        "SET u.is_approved = 1, u.is_admin = 1"
                    )
                )
            else:
                connection.execute(
                    text(
                        "UPDATE users SET is_approved = TRUE, is_admin = TRUE "
                        "WHERE id = (SELECT id FROM users ORDER BY id ASC LIMIT 1)"
                    )
                )


@app.on_event("startup")
def startup() -> None:
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    try:
        ensure_users_schema_columns()
    except Exception as e:
        logger.warning("Failed to ensure user schema columns: %s", e)
    
    # Log GitHub OAuth configuration status
    if settings.github_client_id and settings.github_client_secret:
        logger.info("GitHub OAuth is configured")
    else:
        logger.warning("GitHub OAuth is NOT configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to enable GitHub login.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ui_router)
app.include_router(auth_router)
app.include_router(demands_router)
app.include_router(catalog_router)
app.include_router(backoffice_router)
