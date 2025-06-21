"""
Campaign management API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.core.dependencies import CampaignServiceDep, validate_organization_id
from app.models.campaign import (
    Campaign, CampaignCreateRequest, CampaignResponse,
    SubredditDiscoveryRequest, SubredditDiscoveryByTopicsRequest, PostDiscoveryRequest,
    ResponseGenerationRequest, ResponseExecutionRequest
)

router = APIRouter()


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    organization_id: str,
    campaign_service: CampaignServiceDep = None
):
    """Create a new Reddit marketing campaign."""
    org_id = validate_organization_id(organization_id)
    
    success, message, campaign = await campaign_service.create_campaign(
        org_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    campaign_service: CampaignServiceDep = None
):
    """Get a campaign by ID."""
    success, message, campaign = await campaign_service.get_campaign(campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign
    )


@router.get("/", response_model=CampaignResponse)
async def list_campaigns(
    organization_id: str,
    campaign_service: CampaignServiceDep = None
):
    """List all campaigns for an organization."""
    org_id = validate_organization_id(organization_id)
    
    success, message, campaigns = await campaign_service.list_campaigns(org_id)
    
    return CampaignResponse(
        success=success,
        message=message,
        data={"campaigns": [campaign.model_dump() for campaign in campaigns]}
    )


@router.post("/{campaign_id}/discover-topics", response_model=CampaignResponse)
async def discover_topics(
    campaign_id: str,
    request: SubredditDiscoveryRequest,
    campaign_service: CampaignServiceDep = None
):
    """Discover relevant topics based on selected documents."""
    success, message, data = await campaign_service.discover_topics(
        campaign_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.post("/{campaign_id}/discover-subreddits", response_model=CampaignResponse)
async def discover_subreddits(
    campaign_id: str,
    request: SubredditDiscoveryByTopicsRequest,
    campaign_service: CampaignServiceDep = None
):
    """Discover relevant subreddits based on provided topics."""
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


@router.post("/{campaign_id}/discover-posts", response_model=CampaignResponse)
async def discover_posts(
    campaign_id: str,
    request: PostDiscoveryRequest,
    campaign_service: CampaignServiceDep = None
):
    """Discover relevant posts and comments in target subreddits."""
    success, message, data = await campaign_service.discover_posts(
        campaign_id, request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        data=data
    )


@router.post("/{campaign_id}/generate-responses", response_model=CampaignResponse)
async def generate_responses(
    campaign_id: str,
    request: ResponseGenerationRequest,
    campaign_service: CampaignServiceDep = None
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


@router.post("/{campaign_id}/execute-responses", response_model=CampaignResponse)
async def execute_responses(
    campaign_id: str,
    request: ResponseExecutionRequest,
    campaign_service: CampaignServiceDep = None
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


@router.get("/{campaign_id}/status", response_model=CampaignResponse)
async def get_campaign_status(
    campaign_id: str,
    campaign_service: CampaignServiceDep = None
):
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
        "successful_posts": len([r for r in campaign.posted_responses.values() if r.posting_successful]),
        "failed_posts": len([r for r in campaign.posted_responses.values() if not r.posting_successful])
    }
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign,
        data=progress_data
    )