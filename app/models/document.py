"""
Document-related data app.models.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4


class Organization(BaseModel):
    """Organization model for grouping documents."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    documents: List[Document] = Field(default_factory=list)
    documents_count: int = Field(default=0, description="Number of documents in this organization")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Document(BaseModel):
    """Document model for tracking document metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    organization_id: str = Field(..., description="ID of the organization this document belongs to")
    rag_id: str = Field(..., description="RAG ID for grouping related document chunks")
    
    # Custom metadata for filtering
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Document stats
    chunk_count: int = Field(default=0, description="Number of chunks this document was split into")
    content_length: int = Field(default=0, description="Original content length in characters")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response Models

class DocumentCreateRequest(BaseModel):
    """Request model for creating new documents."""
    
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Optional chunking parameters
    chunk_size: Optional[int] = Field(None, ge=100, le=5000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)


class DocumentIngestURLRequest(BaseModel):
    """Request model for ingesting documents from URLs."""
    
    url: str = Field(..., min_length=1, description="URL to scrape content from")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Optional title for the document")
    organization_id: str = Field(..., description="Organization ID")
    organization_name: Optional[str] = Field(None, description="Optional organization name for auto-creation")
    
    # Optional chunking parameters
    chunk_size: Optional[int] = Field(None, ge=100, le=5000, description="Size of text chunks")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="Overlap between chunks")
    
    # Scraping method
    scraping_method: str = Field(default="auto", description="Scraping method: 'auto', 'firecrawl', or 'requests'")


class DocumentQuery(BaseModel):
    """Model for document query requests."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    organization_id: Optional[str] = Field(None, description="Filter by organization")
    
    # Retrieval parameters
    method: str = Field(default="semantic", description="Retrieval method: semantic or keyword")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of documents to retrieve")
    
    # Filtering options
    filters: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters to apply")


class DocumentResponse(BaseModel):
    """Model for document retrieval responses."""
    
    document_id: str
    title: str
    content: str  # The chunk content
    score: float
    organization_id: str
    metadata: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueryResponse(BaseModel):
    """Model for complete query responses."""
    
    query: str
    method: str
    total_results: int
    documents: List[DocumentResponse]
    processing_time_ms: float


class DocumentOperationResponse(BaseModel):
    """Generic response model for document operations."""
    
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None