"""
Main API router that combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.endpoints.campaigns import router as campaigns_router
from app.api.endpoints.documents import router as documents_router
from app.api.endpoints.subreddits import router as subreddits_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.analytics import router as analytics_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    campaigns_router,
    prefix="/campaigns",
    tags=["Campaigns"]
)

api_router.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"]
)

api_router.include_router(
    subreddits_router,
    prefix="/subreddits",
    tags=["Subreddits"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"]
)