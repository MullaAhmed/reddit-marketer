"""
Main FastAPI application with refactored imports.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from reddit.api.endpoints import router as reddit_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_BASE_URL}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reddit_router)

@app.get("/")
async def root():
    return {"message": "Reddit Marketing AI Agent API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)