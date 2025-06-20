"""
Statistics and analytics API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.core.app_dependencies import StatsServiceDep, validate_organization_id
from app.models.common import APIResponse

router = APIRouter()


@router.post("/collect-engagement")
async def collect_engagement(
    reddit_comment_ids: List[str],
    reddit_credentials: Dict[str, str],
    stats_service: StatsServiceDep = None
):
    """Collect current engagement metrics for posted responses."""
    try:
        result = await stats_service.collect_response_engagement(
            reddit_comment_ids, reddit_credentials
        )
        
        return APIResponse(
            status="success",
            message=f"Collected engagement for {result.get('updated_successfully', 0)} comments",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-campaign-engagement/{campaign_id}")
async def collect_campaign_engagement(
    campaign_id: str,
    reddit_credentials: Dict[str, str],
    stats_service: StatsServiceDep = None
):
    """Collect engagement metrics for all responses in a campaign."""
    try:
        result = await stats_service.collect_campaign_engagement(
            campaign_id, reddit_credentials
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return APIResponse(
            status="success",
            message=f"Collected engagement for campaign {campaign_id}",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaign/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: str,
    stats_service: StatsServiceDep = None
):
    """Get comprehensive analytics for a campaign."""
    try:
        analytics = stats_service.get_campaign_analytics(campaign_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return APIResponse(
            status="success",
            message=f"Analytics for campaign {campaign_id}",
            data=analytics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization/{organization_id}")
async def get_organization_analytics(
    organization_id: str,
    stats_service: StatsServiceDep = None
):
    """Get comprehensive analytics for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        analytics = stats_service.get_organization_analytics(org_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return APIResponse(
            status="success",
            message=f"Analytics for organization {org_id}",
            data=analytics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subreddit/{subreddit}")
async def get_subreddit_performance(
    subreddit: str,
    stats_service: StatsServiceDep = None
):
    """Get performance analytics for a specific subreddit."""
    try:
        performance = stats_service.get_subreddit_performance(subreddit)
        
        if "error" in performance:
            raise HTTPException(status_code=404, detail=performance["error"])
        
        return APIResponse(
            status="success",
            message=f"Performance data for r/{subreddit}",
            data=performance
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending-subreddits")
async def get_trending_subreddits(
    organization_id: str = Query(None, description="Filter by organization"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    stats_service: StatsServiceDep = None
):
    """Get trending subreddits based on performance."""
    try:
        org_id = None
        if organization_id:
            org_id = validate_organization_id(organization_id)
        
        trending = stats_service.get_trending_subreddits(org_id, limit)
        
        return APIResponse(
            status="success",
            message=f"Top {len(trending)} trending subreddits",
            data={"trending_subreddits": trending}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement-insights")
async def get_engagement_insights(
    campaign_id: str = Query(None, description="Filter by campaign"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    stats_service: StatsServiceDep = None
):
    """Get engagement insights and trends."""
    try:
        insights = stats_service.get_engagement_insights(campaign_id, days)
        
        if "error" in insights:
            raise HTTPException(status_code=400, detail=insights["error"])
        
        return APIResponse(
            status="success",
            message=f"Engagement insights for {days} days",
            data=insights
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/campaign-report/{campaign_id}")
async def generate_campaign_report(
    campaign_id: str,
    stats_service: StatsServiceDep = None
):
    """Generate a comprehensive report for a campaign."""
    try:
        report = stats_service.generate_campaign_report(campaign_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return APIResponse(
            status="success",
            message=f"Campaign report for {campaign_id}",
            data=report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organization-report/{organization_id}")
async def generate_organization_report(
    organization_id: str,
    stats_service: StatsServiceDep = None
):
    """Generate a comprehensive report for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        report = stats_service.generate_organization_report(org_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return APIResponse(
            status="success",
            message=f"Organization report for {org_id}",
            data=report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(90, ge=30, le=365, description="Days of data to keep"),
    stats_service: StatsServiceDep = None
):
    """Clean up old statistics data."""
    try:
        result = stats_service.cleanup_old_data(days_to_keep)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return APIResponse(
            status="success",
            message=f"Cleaned up data older than {days_to_keep} days",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))