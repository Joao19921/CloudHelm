import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import CloudCatalogItem, Demand, User  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.demands import router as demands_router
from app.routers.ui import router as ui_router

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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


@app.on_event("startup")
def startup() -> None:
    wait_for_database()
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ui_router)
app.include_router(auth_router)
app.include_router(demands_router)
app.include_router(catalog_router)
