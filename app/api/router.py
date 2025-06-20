"""
Main API router that combines all endpoint routers.
"""

from fastapi import APIRouter

from api.endpoints.campaigns import router as campaigns_router
from api.endpoints.documents import router as documents_router
from api.endpoints.subreddits import router as subreddits_router
from api.endpoints.health import router as health_router
from api.endpoints.stats import router as stats_router

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
    stats_router,
    prefix="/stats",
    tags=["Statistics"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)