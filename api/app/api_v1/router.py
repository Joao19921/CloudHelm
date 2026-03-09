from fastapi import APIRouter

from app.api_v1.endpoints import auth, backoffice, catalog, demands, ui

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(backoffice.router, tags=["backoffice"])
api_router.include_router(catalog.router, tags=["catalog"])
api_router.include_router(demands.router, tags=["demands"])
api_router.include_router(ui.router, tags=["ui"])
