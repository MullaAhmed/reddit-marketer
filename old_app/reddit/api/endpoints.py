"""
Updated Reddit API endpoints with refactored services.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from reddit.models import (
    Campaign, CampaignCreateRequest, SubredditDiscoveryRequest,
    PostDiscoveryRequest, ResponseGenerationRequest, ResponseExecutionRequest,
    CampaignResponse
)
from reddit.services.campaign_service import CampaignService

router = APIRouter(prefix="/api/v1/reddit", tags=["Reddit Marketing"])

# Initialize campaign service
campaign_service = CampaignService()


@router.post("/campaigns/", response_model=CampaignResponse)
async def create_campaign(
    organization_id: str,
    request: CampaignCreateRequest
):
    """Create a new Reddit marketing campaign."""
    success, message, campaign = await campaign_service.create_campaign(
        organization_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str):
    """Get a campaign by ID."""
    success, message, campaign = await campaign_service.get_campaign(campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign
    )


@router.get("/campaigns/", response_model=CampaignResponse)
async def list_campaigns(organization_id: str):
    """List all campaigns for an organization."""
    success, message, campaigns = await campaign_service.list_campaigns(organization_id)
    
    return CampaignResponse(
        success=success,
        message=message,
        data={"campaigns": [campaign.model_dump() for campaign in campaigns]}
    )


@router.post("/campaigns/{campaign_id}/discover-subreddits", response_model=CampaignResponse)
async def discover_subreddits(
    campaign_id: str,
    request: SubredditDiscoveryRequest
):
    """Discover relevant subreddits based on selected documents."""
    success, message, data = await campaign_service.discover_subreddits(
        campaign_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.post("/campaigns/{campaign_id}/discover-posts", response_model=CampaignResponse)
async def discover_posts(
    campaign_id: str,
    request: PostDiscoveryRequest,
    reddit_credentials: Dict[str, str]
):
    """Discover relevant posts and comments in target subreddits."""
    success, message, data = await campaign_service.discover_posts(
        campaign_id, request, reddit_credentials
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.post("/campaigns/{campaign_id}/generate-responses", response_model=CampaignResponse)
async def generate_responses(
    campaign_id: str,
    request: ResponseGenerationRequest
):
    """Generate responses for target posts."""
    success, message, data = await campaign_service.generate_responses(
        campaign_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.post("/campaigns/{campaign_id}/execute-responses", response_model=CampaignResponse)
async def execute_responses(
    campaign_id: str,
    request: ResponseExecutionRequest
):
    """Execute planned responses by posting to Reddit."""
    success, message, data = await campaign_service.execute_responses(
        campaign_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.get("/campaigns/{campaign_id}/status", response_model=CampaignResponse)
async def get_campaign_status(campaign_id: str):
    """Get detailed campaign status and progress."""
    success, message, campaign = await campaign_service.get_campaign(campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    # Calculate progress statistics
    progress_data = {
        "status": campaign.status,
        "documents_selected": len(campaign.selected_document_ids),
        "subreddits_found": len(campaign.target_subreddits),
        "posts_found": len(campaign.target_posts),
        "responses_planned": len(campaign.planned_responses),
        "responses_posted": len(campaign.posted_responses),
        "successful_posts": len([r for r in campaign.posted_responses if r.posting_successful]),
        "failed_posts": len([r for r in campaign.posted_responses if not r.posting_successful])
    }
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign,
        data=progress_data
    )