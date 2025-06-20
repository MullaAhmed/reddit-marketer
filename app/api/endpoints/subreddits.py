"""
Subreddit discovery API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.core.app_dependencies import RedditConnectorDep, validate_organization_id
from app.models.reddit import SubredditDiscoveryRequest, SubredditResponse

router = APIRouter()


@router.post("/discover", response_model=SubredditResponse)
async def discover_subreddits(
    content: str,
    organization_id: str = Query(..., description="Organization ID"),
    min_subscribers: int = Query(10000, description="Minimum subscriber count"),
    reddit_connector: RedditConnectorDep = None
):
    """Discover relevant subreddits based on content analysis."""
    org_id = validate_organization_id(organization_id)
    
    success, message, discovery_data = await reddit_connector.discover_subreddits(
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
    reddit_connector: RedditConnectorDep = None
):
    """Extract topics from content for subreddit discovery."""
    org_id = validate_organization_id(organization_id)
    
    success, message, topics = await reddit_connector.extract_topics_from_content(
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
    reddit_connector: RedditConnectorDep = None
):
    """Search for subreddits by name or topic."""
    try:
        # This would implement direct subreddit search
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Search for '{query}' completed",
            "data": {
                "query": query,
                "results": [],
                "total": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subreddit_name}/info")
async def get_subreddit_info(
    subreddit_name: str,
    reddit_connector: RedditConnectorDep = None
):
    """Get information about a specific subreddit."""
    try:
        # This would implement subreddit info retrieval
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Information for r/{subreddit_name}",
            "data": {
                "name": subreddit_name,
                "subscribers": 0,
                "description": "",
                "rules": []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))