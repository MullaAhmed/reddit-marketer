"""
Subreddit discovery API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.core.dependencies import RedditServiceDep, validate_organization_id
from app.models.reddit import SubredditDiscoveryRequest, SubredditResponse

router = APIRouter()


@router.post("/discover", response_model=SubredditResponse)
async def discover_subreddits(
    content: str,
    organization_id: str = Query(..., description="Organization ID"),
    min_subscribers: int = Query(10000, description="Minimum subscriber count"),
    reddit_service: RedditServiceDep = None
):
    """Discover relevant subreddits based on content analysis."""
    org_id = validate_organization_id(organization_id)
    
    success, message, discovery_data = await reddit_service.discover_subreddits(
        content, org_id, min_subscribers
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return SubredditResponse(
        success=success,
        message=message,
        data=discovery_data
    )


@router.post("/extract-topics", response_model=SubredditResponse)
async def extract_topics(
    content: str,
    organization_id: str = Query(..., description="Organization ID"),
    reddit_service: RedditServiceDep = None
):
    """Extract topics from content for subreddit discovery."""
    org_id = validate_organization_id(organization_id)
    
    success, message, topics = await reddit_service.extract_topics_from_content(
        content, org_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return SubredditResponse(
        success=success,
        message=message,
        data={"topics": topics}
    )


@router.get("/search")
async def search_subreddits(
    query: str = Query(..., description="Search query"),
    limit: int = Query(25, description="Maximum results to return"),
    reddit_service: RedditServiceDep = None
):
    """Search for subreddits by name or topic."""
    try:
        success, message, results = await reddit_service.search_subreddits(query, limit)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {
            "success": True,
            "message": message,
            "data": {
                "query": query,
                "results": results,
                "total": len(results)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subreddit_name}/info")
async def get_subreddit_info(
    subreddit_name: str,
    reddit_service: RedditServiceDep = None
):
    """Get information about a specific subreddit."""
    try:
        info = await reddit_service.get_subreddit_info(subreddit_name)
        if not info.get("success", True):
            raise HTTPException(status_code=400, detail=info.get("error", "Unknown error"))
        return {
            "success": True,
            "message": f"Information for r/{subreddit_name}",
            "data": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))