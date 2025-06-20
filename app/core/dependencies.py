"""
FastAPI dependencies - Updated to include LLM service.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Header

from app.services.campaign_service import CampaignService
from app.services.document_service import DocumentService
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService


def get_campaign_service() -> CampaignService:
    """Get campaign service instance."""
    return CampaignService()


def get_document_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService()


def get_reddit_service() -> RedditService:
    """Get Reddit service instance."""
    return RedditService()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService()


def validate_organization_id(organization_id: str) -> str:
    """Validate organization ID format."""
    if not organization_id or len(organization_id) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Invalid organization ID"
        )
    return organization_id


def validate_api_key(x_api_key: Annotated[str, Header()] = None) -> str:
    """Validate API key if required."""
    # For now, we'll skip API key validation
    # In production, implement proper API key validation
    return x_api_key


# Type aliases for dependency injection
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
RedditServiceDep = Annotated[RedditService, Depends(get_reddit_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]