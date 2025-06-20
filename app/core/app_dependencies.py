"""
FastAPI dependencies - Updated to use new orchestrators and processors.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Header

from app.orchestrators.campaign_orchestrator import CampaignOrchestrator
from app.processors.document_processor import DocumentProcessor
from app.connectors.reddit_connector import RedditConnector
from app.orchestrators.llm_orchestrator import LLMOrchestrator
from app.services.stats_service import StatsService


def get_campaign_orchestrator() -> CampaignOrchestrator:
    """Get campaign orchestrator instance."""
    return CampaignOrchestrator()


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor()


def get_reddit_connector() -> RedditConnector:
    """Get Reddit connector instance."""
    return RedditConnector()


def get_llm_orchestrator() -> LLMOrchestrator:
    """Get LLM orchestrator instance."""
    return LLMOrchestrator()


def get_stats_service() -> StatsService:
    """Get stats service instance."""
    return StatsService()


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
CampaignOrchestratorDep = Annotated[CampaignOrchestrator, Depends(get_campaign_orchestrator)]
DocumentProcessorDep = Annotated[DocumentProcessor, Depends(get_document_processor)]
RedditConnectorDep = Annotated[RedditConnector, Depends(get_reddit_connector)]
LLMOrchestratorDep = Annotated[LLMOrchestrator, Depends(get_llm_orchestrator)]
StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]

# Legacy aliases for backward compatibility
CampaignServiceDep = CampaignOrchestratorDep
DocumentServiceDep = DocumentProcessorDep
RedditServiceDep = RedditConnectorDep
LLMServiceDep = LLMOrchestratorDep