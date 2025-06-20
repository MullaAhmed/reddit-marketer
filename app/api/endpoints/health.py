"""
Health check API endpoints.
"""

from fastapi import APIRouter
from typing import Dict, Any
import time
from datetime import datetime, timezone

from app.core.settings import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "service": "Reddit Marketing AI Agent"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with service status."""
    start_time = time.time()
    
    # Check various service components
    checks = {
        "api": {"status": "healthy", "response_time_ms": 0},
        "database": {"status": "unknown", "response_time_ms": 0},
        "llm_service": {"status": "unknown", "response_time_ms": 0},
        "reddit_api": {"status": "unknown", "response_time_ms": 0}
    }
    
    # API check (always healthy if we reach this point)
    api_time = time.time()
    checks["api"]["response_time_ms"] = round((api_time - start_time) * 1000, 2)
    
    # Database check (placeholder)
    db_start = time.time()
    try:
        # TODO: Implement actual database health check
        checks["database"]["status"] = "healthy"
    except Exception as e:
        checks["database"]["status"] = "unhealthy"
        checks["database"]["error"] = str(e)
    checks["database"]["response_time_ms"] = round((time.time() - db_start) * 1000, 2)
    
    # LLM service check (placeholder)
    llm_start = time.time()
    try:
        # TODO: Implement actual LLM service health check
        if settings.OPENAI_API_KEY:
            checks["llm_service"]["status"] = "healthy"
        else:
            checks["llm_service"]["status"] = "unhealthy"
            checks["llm_service"]["error"] = "Missing API key"
    except Exception as e:
        checks["llm_service"]["status"] = "unhealthy"
        checks["llm_service"]["error"] = str(e)
    checks["llm_service"]["response_time_ms"] = round((time.time() - llm_start) * 1000, 2)
    
    # Reddit API check (placeholder)
    reddit_start = time.time()
    try:
        # TODO: Implement actual Reddit API health check
        checks["reddit_api"]["status"] = "healthy"
    except Exception as e:
        checks["reddit_api"]["status"] = "unhealthy"
        checks["reddit_api"]["error"] = str(e)
    checks["reddit_api"]["response_time_ms"] = round((time.time() - reddit_start) * 1000, 2)
    
    # Overall status
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "degraded"
    
    total_time = round((time.time() - start_time) * 1000, 2)
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "service": "Reddit Marketing AI Agent",
        "total_response_time_ms": total_time,
        "checks": checks,
        "config": {
            "data_dir": settings.DATA_DIR,
            "model_name": settings.MODEL_NAME,
            "embedding_provider": settings.EMBEDDING_PROVIDER
        }
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check for container orchestration."""
    try:
        # Check if all required services are ready
        required_keys = ["OPENAI_API_KEY", "GOOGLE_API_KEY"]
        missing_keys = []
        
        if not settings.OPENAI_API_KEY:
            missing_keys.append("OPENAI_API_KEY")
        if not settings.GOOGLE_API_KEY:
            missing_keys.append("GOOGLE_API_KEY")
        
        if missing_keys:
            return {
                "status": "not_ready",
                "message": f"Missing required configuration: {', '.join(missing_keys)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "status": "ready",
            "message": "Service is ready to accept requests",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "not_ready",
            "message": f"Readiness check failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check for container orchestration."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time()  # This would be more accurate with app start time
    }