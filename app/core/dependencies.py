"""
Core dependencies - Updated to remove FastAPI dependencies.
"""

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
from app.services.scraper_service import WebScraperService
from app.utils.validator_utils import is_valid_organization_id_format
from app.core.settings import settings


class ServiceContainer:
    """
    Service container for dependency injection without FastAPI.
    """
    
    def __init__(self):
        """Initialize all services."""
        self._services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services in the correct order."""
        # Storage layer
        self._services['json_storage'] = JsonStorage()
        self._services['vector_storage_client'] = VectorStorageClient()
        self._services['vector_storage'] = VectorStorage(self._services['vector_storage_client'])
        
        # Managers
        self._services['document_manager'] = DocumentManager(self._services['json_storage'])
        self._services['campaign_manager'] = CampaignManager(self._services['json_storage'])
        self._services['embeddings_manager'] = EmbeddingsManager(self._services['vector_storage_client'])
        self._services['analytics_manager'] = AnalyticsManager(
            self._services['campaign_manager'],
            self._services['document_manager']
        )
        
        # Clients
        self._services['llm_client'] = LLMClient()
        self._services['reddit_client'] = RedditClient(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            username=getattr(settings, 'REDDIT_USERNAME', None),
            password=getattr(settings, 'REDDIT_PASSWORD', None)
        )
        self._services['web_scraper_service'] = WebScraperService()
        
        # Services
        self._services['document_service'] = DocumentService(
            self._services['document_manager'],
            self._services['vector_storage'],
            self._services['web_scraper_service']
        )
        self._services['reddit_service'] = RedditService(
            self._services['json_storage'],
            self._services['reddit_client']
        )
        self._services['llm_service'] = LLMService(self._services['llm_client'])
        self._services['analytics_service'] = AnalyticsService(self._services['analytics_manager'])
        self._services['campaign_service'] = CampaignService(
            self._services['campaign_manager'],
            self._services['document_service'],
            self._services['reddit_service'],
            self._services['llm_service']
        )
    
    def get_service(self, service_name: str):
        """Get a service by name."""
        if service_name not in self._services:
            raise ValueError(f"Service '{service_name}' not found")
        return self._services[service_name]
    
    def get_campaign_service(self) -> CampaignService:
        """Get campaign service."""
        return self._services['campaign_service']
    
    def get_document_service(self) -> DocumentService:
        """Get document service."""
        return self._services['document_service']
    
    def get_reddit_service(self) -> RedditService:
        """Get reddit service."""
        return self._services['reddit_service']
    
    def get_llm_service(self) -> LLMService:
        """Get LLM service."""
        return self._services['llm_service']
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service."""
        return self._services['analytics_service']


def validate_organization_id(organization_id: str) -> str:
    """Validate organization ID format."""
    if not is_valid_organization_id_format(organization_id):
        raise ValueError("Invalid organization ID format")
    return organization_id


# Global service container instance
service_container = ServiceContainer()