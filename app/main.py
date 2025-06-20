"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI

from app.core.settings import settings
from app.core.middleware import setup_middleware
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Reddit Marketing AI Agent API",
    openapi_url=f"{settings.API_BASE_URL}/openapi.json"
)

# Set up middleware
setup_middleware(app)

# Include API router
app.include_router(api_router, prefix=settings.API_BASE_URL)

@app.get("/")
async def root():
    return {
        "message": "Reddit Marketing AI Agent API", 
        "version": "2.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)