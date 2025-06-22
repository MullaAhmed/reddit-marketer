"""
Document ingestion service with Haystack RAG integration.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional
from urllib.parse import urlparse

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

from src.storage.json_storage import JsonStorage
from src.storage.vector_storage import VectorStorage
from src.models.common import generate_id, get_current_timestamp
from src.models.document import Document
from src.utils.text_utils import clean_text, chunk_text
from src.config.settings import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for document ingestion and processing with Haystack RAG."""
    
    def __init__(
        self,
        json_storage: JsonStorage,
        vector_storage: VectorStorage
    ):
        """Initialize the ingestion service."""
        self.json_storage = json_storage
        self.vector_storage = vector_storage
        self.logger = logger
        
        # Initialize storage files
        self.json_storage.init_file("documents.json", [])
        self.json_storage.init_file("organizations.json", [])
    
    async def ingest_document(
        self,
        content: str,
        title: str,
        organization_id: str,
        is_url: bool = False,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Ingest a document from content or URL using Haystack RAG."""
        try:
            # If it's a URL, scrape the content
            if is_url:
                scraped_content = await self._scrape_url(content)
                if not scraped_content:
                    return False, f"Failed to scrape content from URL: {content}", None
                content = scraped_content
            
            # Clean and validate content
            clean_content = clean_text(content)
            if not clean_content.strip():
                return False, "No valid content found", None
            
            # Generate document ID and metadata
            document_id = generate_id()
            timestamp = get_current_timestamp()
            
            # Create document metadata
            document = Document(
                id=document_id,
                title=title,
                organization_id=organization_id,
                metadata={
                    "source": "url" if is_url else "direct",
                    "original_url": content if is_url else None,
                    "ingestion_method": "haystack_rag"
                },
                content_length=len(clean_content),
                chunk_count=0,
                created_at=timestamp
            )
            
            # Chunk the content using configured settings
            chunk_size = chunk_size or settings.CHUNK_SIZE
            chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
            chunks = chunk_text(clean_content, chunk_size, chunk_overlap)
            document.chunk_count = len(chunks)
            
            # Store in vector database using Haystack
            success, message = self.vector_storage.store_document_chunks(
                org_id=organization_id,
                document_id=document_id,
                title=title,
                chunks=chunks,
                metadata=document.metadata
            )
            
            if not success:
                return False, f"Failed to store document chunks: {message}", None
            
            # Save document metadata
            self.json_storage.update_item("documents.json", document.model_dump())
            
            # Update organization
            self._update_organization(organization_id)
            
            self.logger.info(f"Successfully ingested document '{title}' with {len(chunks)} chunks using Haystack")
            return True, f"Successfully ingested document with {len(chunks)} chunks", document_id
            
        except Exception as e:
            self.logger.error(f"Error ingesting document: {str(e)}")
            return False, f"Error ingesting document: {str(e)}", None
    
    async def delete_document(
        self,
        organization_id: str,
        document_id: str
    ) -> Tuple[bool, str]:
        """Delete a document and its chunks using Haystack."""
        try:
            # Delete from vector storage using Haystack
            vector_success = self.vector_storage.delete_document(organization_id, document_id)
            if not vector_success:
                return False, "Failed to delete document chunks from vector storage"
            
            # Delete metadata
            metadata_success = self.json_storage.delete_item("documents.json", document_id)
            if not metadata_success:
                return False, "Failed to delete document metadata"
            
            # Update organization
            self._update_organization(organization_id)
            
            self.logger.info(f"Successfully deleted document {document_id} using Haystack")
            return True, "Document deleted successfully"
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False, f"Error deleting document: {str(e)}"
    
    def query_documents(
        self,
        organization_id: str,
        query: str,
        method: str = "semantic",
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> Tuple[bool, str, list]:
        """Query documents using Haystack RAG."""
        try:
            results = self.vector_storage.query_documents(
                org_id=organization_id,
                query=query,
                method=method,
                top_k=top_k,
                filters=filters
            )
            
            if results:
                return True, f"Found {len(results)} documents", results
            else:
                return True, "No documents found", []
                
        except Exception as e:
            self.logger.error(f"Error querying documents: {str(e)}")
            return False, f"Error querying documents: {str(e)}", []
    
    def get_document_context(
        self,
        organization_id: str,
        document_ids: List[str],
        query: Optional[str] = None
    ) -> str:
        """Get combined context from multiple documents using Haystack."""
        try:
            all_content = []
            
            for doc_id in document_ids:
                chunks = self.vector_storage.get_document_chunks_by_document_id(
                    org_id=organization_id,
                    document_id=doc_id,
                    query=query
                )
                
                if chunks:
                    # Combine chunks for this document
                    doc_content = "\n".join([chunk['content'] for chunk in chunks])
                    if doc_content.strip():
                        all_content.append(doc_content)
            
            combined_content = "\n\n".join(all_content)
            self.logger.info(f"Retrieved context: {len(combined_content)} characters from {len(document_ids)} documents")
            
            return combined_content
            
        except Exception as e:
            self.logger.error(f"Error getting document context: {str(e)}")
            return ""
    
    def _update_organization(self, organization_id: str):
        """Update organization document count."""
        try:
            # Get current organization data
            org_data = self.json_storage.find_item("organizations.json", organization_id)
            
            if not org_data:
                # Create new organization
                org_data = {
                    "id": organization_id,
                    "name": f"Organization {organization_id}",
                    "created_at": get_current_timestamp(),
                    "document_count": 0,
                    "rag_enabled": True,
                    "storage_backend": "haystack_chroma"
                }
            
            # Count documents for this organization
            documents = self.json_storage.filter_items(
                "documents.json",
                {"organization_id": organization_id}
            )
            org_data["document_count"] = len(documents)
            
            # Save organization data
            self.json_storage.update_item("organizations.json", org_data)
            
        except Exception as e:
            self.logger.error(f"Error updating organization {organization_id}: {str(e)}")
    
    async def _scrape_url(self, url: str) -> Optional[str]:
        """Scrape content from URL using available methods."""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                self.logger.error(f"Invalid URL: {url}")
                return None
            
            # Try Firecrawl first if available and configured
            if FIRECRAWL_AVAILABLE and settings.FIRECRAWL_API_KEY:
                try:
                    app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
                    response = app.scrape_url(
                        url=url,
                        formats=['markdown'],
                        only_main_content=True
                    )
                    
                    if response and hasattr(response, 'markdown'):
                        content = clean_text(response.markdown)
                        if content.strip():
                            self.logger.info(f"Successfully scraped {url} with Firecrawl")
                            return content
                except Exception as e:
                    self.logger.warning(f"Firecrawl failed for {url}: {str(e)}")
            
            # Fallback to requests + BeautifulSoup
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script_or_style in soup(['script', 'style']):
                    script_or_style.extract()
                
                # Get text content
                text = soup.get_text()
                content = clean_text(text)
                
                if content.strip():
                    self.logger.info(f"Successfully scraped {url} with requests")
                    return content
                
            except Exception as e:
                self.logger.error(f"Requests scraping failed for {url}: {str(e)}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping URL {url}: {str(e)}")
            return None