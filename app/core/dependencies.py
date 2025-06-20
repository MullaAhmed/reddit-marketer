"""
FastAPI dependencies - Updated to include analytics service.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Header

from app.services.campaign_service import CampaignService
from app.services.document_service import DocumentService
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService
from app.services.analytics_service import AnalyticsService
from app.managers.analytics_manager import AnalyticsManager
from app.managers.campaign_manager import CampaignManager
from app.managers.document_manager import DocumentManager
from app.managers.embeddings_manager import EmbeddingsManager
from app.storage.vector_storage import VectorStorage
from app.storage.json_storage import JsonStorage
from app.clients.llm_client import LLMClient
from app.clients.reddit_client import RedditClient
from app.clients.storage_client import VectorStorageClient
from app.utils.data_validator_util import is_valid_organization_id_format
from app.core.settings import settings


def get_analytics_manager(
    campaign_manager: "CampaignManagerDep" = Depends(lambda: get_campaign_manager()),
    document_manager: "DocumentManagerDep" = Depends(lambda: get_document_manager())
) -> AnalyticsManager:
    return AnalyticsManager(
        campaign_manager=campaign_manager,
        document_manager=document_manager
    )


def get_campaign_manager(
    json_storage: "JsonStorageDep" = Depends(lambda: get_json_storage())
) -> CampaignManager:
    return CampaignManager(json_storage=json_storage)


def get_document_manager(
    json_storage: "JsonStorageDep" = Depends(lambda: get_json_storage())
) -> DocumentManager:
    return DocumentManager(json_storage=json_storage)


def get_embeddings_manager(
    vector_storage_client: "VectorStorageClientDep" = Depends(lambda: get_vector_storage_client())
) -> EmbeddingsManager:
    return EmbeddingsManager(vector_storage_client=vector_storage_client)


def get_vector_storage(
    vector_storage_client: "VectorStorageClientDep" = Depends(lambda: get_vector_storage_client())
) -> VectorStorage:
    return VectorStorage(vector_storage_client=vector_storage_client)


def get_json_storage() -> JsonStorage:
    return JsonStorage()


def get_llm_client() -> LLMClient:
    return LLMClient()


def get_reddit_client() -> RedditClient:
    return RedditClient(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        username=getattr(settings, 'REDDIT_USERNAME', None),
        password=getattr(settings, 'REDDIT_PASSWORD', None)
    )


def get_vector_storage_client() -> VectorStorageClient:
    return VectorStorageClient()


def get_campaign_service(
    campaign_manager: "CampaignManagerDep" = Depends(get_campaign_manager),
    document_service: "DocumentServiceDep" = Depends(lambda: get_document_service()),
    reddit_service: "RedditServiceDep" = Depends(lambda: get_reddit_service()),
    llm_service: "LLMServiceDep" = Depends(lambda: get_llm_service())
) -> CampaignService:
    return CampaignService(
        campaign_manager=campaign_manager,
        document_service=document_service,
        reddit_service=reddit_service,
        llm_service=llm_service
    )


def get_document_service(
    document_manager: "DocumentManagerDep" = Depends(get_document_manager),
    vector_storage: "VectorStorageDep" = Depends(get_vector_storage)
) -> DocumentService:
    return DocumentService(
        document_manager=document_manager,
        vector_storage=vector_storage
    )


def get_reddit_service(
    json_storage: "JsonStorageDep" = Depends(get_json_storage),
    reddit_client: "RedditClientDep" = Depends(get_reddit_client)
) -> RedditService:
    return RedditService(
        json_storage=json_storage,
        reddit_client=reddit_client
    )


def get_llm_service(
    llm_client: "LLMClientDep" = Depends(get_llm_client)
) -> LLMService:
    return LLMService(llm_client=llm_client)


def get_analytics_service(
    analytics_manager: "AnalyticsManagerDep" = Depends(get_analytics_manager)
) -> AnalyticsService:
    return AnalyticsService(analytics_manager=analytics_manager)


def validate_organization_id(organization_id: str) -> str:
    """Validate organization ID format."""
    if not is_valid_organization_id_format(organization_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid organization ID format"
        )
    return organization_id


def validate_api_key(x_api_key: Annotated[str, Header()] = None) -> str:
    """Validate API key if required."""
    # For now, we'll skip API key validation
    # In production, implement proper API key validation
    return x_api_key


# Type aliases for dependency injection
AnalyticsManagerDep = Annotated[AnalyticsManager, Depends(get_analytics_manager)]
CampaignManagerDep = Annotated[CampaignManager, Depends(get_campaign_manager)]
DocumentManagerDep = Annotated[DocumentManager, Depends(get_document_manager)]
EmbeddingsManagerDep = Annotated[EmbeddingsManager, Depends(get_embeddings_manager)]
VectorStorageDep = Annotated[VectorStorage, Depends(get_vector_storage)]
JsonStorageDep = Annotated[JsonStorage, Depends(get_json_storage)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
RedditClientDep = Annotated[RedditClient, Depends(get_reddit_client)]
VectorStorageClientDep = Annotated[VectorStorageClient, Depends(get_vector_storage_client)]
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
RedditServiceDep = Annotated[RedditService, Depends(get_reddit_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]