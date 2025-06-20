"""
Campaign management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

from app.core.app_dependencies import CampaignOrchestratorDep, validate_organization_id
from app.models.campaign import (
    Campaign, CampaignCreateRequest, CampaignResponse,
    SubredditDiscoveryRequest, PostDiscoveryRequest,
    ResponseGenerationRequest, ResponseExecutionRequest
)

router = APIRouter()


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    organization_id: str = Query(..., description="Organization ID"),
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Create a new Reddit marketing campaign."""
    org_id = validate_organization_id(organization_id)
    
    success, message, campaign = await campaign_orchestrator.create_campaign(
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
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Get a campaign by ID."""
    success, message, campaign = await campaign_orchestrator.get_campaign(campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return CampaignResponse(
        success=success,
        message=message,
        campaign=campaign
    )


@router.get("/", response_model=CampaignResponse)
async def list_campaigns(
    organization_id: str = Query(..., description="Organization ID"),
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """List all campaigns for an organization."""
    org_id = validate_organization_id(organization_id)
    
    success, message, campaigns = await campaign_orchestrator.list_campaigns(org_id)
    
    return CampaignResponse(
        success=success,
        message=message,
        data={"campaigns": [campaign.model_dump() for campaign in campaigns]}
    )


@router.post("/{campaign_id}/discover-subreddits", response_model=CampaignResponse)
async def discover_subreddits(
    campaign_id: str,
    request: SubredditDiscoveryRequest,
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Discover relevant subreddits based on selected documents."""
    success, message, data = await campaign_orchestrator.discover_subreddits(
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
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Discover relevant posts and comments in target subreddits."""
    success, message, data = await campaign_orchestrator.discover_posts(
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
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Generate responses for target posts."""
    success, message, data = await campaign_orchestrator.generate_responses(
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
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Execute planned responses by posting to Reddit."""
    success, message, data = await campaign_orchestrator.execute_responses(
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
    campaign_orchestrator: CampaignOrchestratorDep = None
):
    """Get detailed campaign status and progress."""
    success, message, campaign = await campaign_orchestrator.get_campaign(campaign_id)
    
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