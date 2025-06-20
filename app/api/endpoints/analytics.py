"""
Analytics API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.dependencies import AnalyticsServiceDep, validate_organization_id

router = APIRouter()


@router.get("/campaigns/{campaign_id}/engagement")
async def get_campaign_engagement_report(
    campaign_id: str,
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get detailed engagement report for a specific campaign."""
    try:
        report = analytics_service.get_campaign_engagement_report(campaign_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}/performance")
async def get_organization_performance_report(
    organization_id: str,
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get comprehensive performance report for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        report = analytics_service.get_organization_performance_report(org_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}/quick-stats")
async def get_organization_quick_stats(
    organization_id: str,
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get quick overview stats for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        stats = analytics_service.get_quick_stats(org_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}/subreddit-effectiveness")
async def get_subreddit_effectiveness_report(
    organization_id: str,
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get report on subreddit effectiveness for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        report = analytics_service.get_subreddit_effectiveness_report(org_id)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizations/{organization_id}/trends")
async def get_campaign_trends(
    organization_id: str,
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get campaign trend analysis for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        trends = analytics_service.get_campaign_trends(org_id)
        
        if "error" in trends:
            raise HTTPException(status_code=404, detail=trends["error"])
        
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform/overview")
async def get_platform_overview(
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get overall platform metrics and insights."""
    try:
        overview = analytics_service.get_overall_platform_metrics()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform/subreddit-effectiveness")
async def get_global_subreddit_effectiveness(
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get global subreddit effectiveness report."""
    try:
        report = analytics_service.get_subreddit_effectiveness_report()
        
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform/trends")
async def get_global_campaign_trends(
    analytics_service: AnalyticsServiceDep = None
) -> Dict[str, Any]:
    """Get global campaign trend analysis."""
    try:
        trends = analytics_service.get_campaign_trends()
        
        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])
        
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))