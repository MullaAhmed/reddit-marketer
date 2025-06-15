"""
Document processing service using RAG.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from models.document import (
    Organization, Document, DocumentQuery, DocumentResponse, QueryResponse
)
from managers.document_manager import DocumentManager
from storage.vector_storage import VectorStorage
from utils.text_processing import chunk_text, clean_text

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Document processing service that handles document ingestion,
    storage, and retrieval using RAG techniques.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the document service."""
        self.data_dir = data_dir
        self.document_manager = DocumentManager(data_dir)
        self.vector_storage = VectorStorage(data_dir)
        self.logger = logger
    
    # ========================================
    # ORGANIZATION MANAGEMENT
    # ========================================
    
    def get_or_create_organization(self, org_id: str, org_name: str = None) -> Organization:
        """Get existing organization or create a new one."""
        # Check if organization exists
        org_data = self.document_manager.get_organization(org_id)
        
        if org_data:
            # Load existing documents for this org
            existing_docs = self.document_manager.get_documents_by_organization(org_id)
            org_data['documents'] = [Document(**doc) for doc in existing_docs]
            org_data['documents_count'] = len(existing_docs)
            return Organization(**org_data)
        
        # Create new organization
        new_org = Organization(
            id=org_id,
            name=org_name or f"Organization {org_id}",
            description=f"Auto-created organization for {org_id}"
        )
        
        # Save organization
        self.document_manager.save_organization(new_org.model_dump())
        
        return new_org
    
    # ========================================
    # DOCUMENT INGESTION
    # ========================================
    
    def ingest_documents(
        self, 
        documents: List[Dict[str, Any]], 
        org_id: str,
        org_name: str = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Ingest a list of documents for an organization.
        
        Args:
            documents: List of dicts with 'title', 'content', and optional 'metadata'
            org_id: Organization ID
            org_name: Optional organization name (for auto-creation)
            
        Returns:
            Tuple of (success: bool, message: str, document_ids: List[str])
        """
        try:
            if not documents:
                return False, "No documents provided", []
            
            # Ensure organization exists
            organization = self.get_or_create_organization(org_id, org_name)
            
            # Process each document
            ingested_doc_ids = []
            total_chunks = 0
            
            for doc_dict in documents:
                # Validate required fields
                if 'title' not in doc_dict or 'content' not in doc_dict:
                    continue
                
                # Create document metadata
                doc = Document(
                    title=doc_dict['title'],
                    organization_id=org_id,
                    rag_id=f"{org_id}_{doc_dict['title']}",
                    metadata=doc_dict.get('metadata', {}),
                    content_length=len(doc_dict['content'])
                )
                
                # Check for duplicate documents
                if self._check_for_duplicate_documents(org_id, doc.title):
                    self.logger.info(f"Document '{doc.title}' already exists for organization {org_id}, skipping...")
                    continue
                
                # Clean and chunk the content
                clean_content = clean_text(doc_dict['content'])
                chunks = chunk_text(
                    clean_content,
                    chunk_size=doc_dict.get('chunk_size', 1000),
                    chunk_overlap=doc_dict.get('chunk_overlap', 200)
                )
                
                # Store document chunks in vector storage
                success, message = self.vector_storage.store_document_chunks(
                    org_id=org_id,
                    document_id=doc.id,
                    title=doc.title,
                    chunks=chunks,
                    metadata=doc.metadata
                )
                
                if success:
                    # Update document with chunk count
                    doc.chunk_count = len(chunks)
                    total_chunks += len(chunks)
                    
                    # Save document metadata
                    self.document_manager.save_document(doc.model_dump())
                    ingested_doc_ids.append(doc.id)
                else:
                    self.logger.error(f"Failed to store document '{doc.title}': {message}")
            
            # Update organization document count
            organization.documents_count = len(self.document_manager.get_documents_by_organization(org_id))
            self.document_manager.save_organization(organization.model_dump())
            
            if ingested_doc_ids:
                self.logger.info(f"Ingested {len(ingested_doc_ids)} documents ({total_chunks} chunks) for org {org_id}")
                return True, f"Successfully ingested {len(ingested_doc_ids)} documents ({total_chunks} chunks)", ingested_doc_ids
            else:
                return False, "No documents were successfully ingested", []
                
        except Exception as e:
            self.logger.error(f"Error during document ingestion for org {org_id}: {str(e)}")
            return False, f"Error during ingestion: {str(e)}", []
    
    def _check_for_duplicate_documents(self, org_id: str, title: str) -> bool:
        """Check if a document with the same title and org already exists."""
        existing_docs = self.document_manager.get_documents_by_organization(org_id)
        for doc_data in existing_docs:
            if doc_data.get('title') == title:
                return True
        return False
    
    # ========================================
    # DOCUMENT RETRIEVAL
    # ========================================
    
    def query_documents(self, query: DocumentQuery) -> QueryResponse:
        """
        Query documents based on the provided query.
        
        Args:
            query: DocumentQuery object with search parameters
            
        Returns:
            QueryResponse with results and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Validate organization
            if not query.organization_id:
                return QueryResponse(
                    query=query.query,
                    method=query.method,
                    total_results=0,
                    documents=[],
                    processing_time_ms=0
                )
            
            # Perform retrieval using vector storage
            results = self.vector_storage.query_documents(
                org_id=query.organization_id,
                query=query.query,
                method=query.method,
                top_k=query.top_k,
                filters=query.filters
            )
            
            # Format results
            formatted_results = []
            for result in results:
                doc_response = DocumentResponse(
                    document_id=result.get('document_id', 'unknown'),
                    title=result.get('title', 'Untitled'),
                    content=result.get('content', ''),
                    score=result.get('score', 0.0),
                    organization_id=query.organization_id,
                    metadata=result.get('metadata', {})
                )
                formatted_results.append(doc_response)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            self.logger.info(f"Retrieved {len(formatted_results)} documents for query '{query.query}' in {processing_time:.2f}ms")
            
            return QueryResponse(
                query=query.query,
                method=query.method,
                total_results=len(formatted_results),
                documents=formatted_results,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Error querying documents: {str(e)}")
            
            return QueryResponse(
                query=query.query,
                method=query.method,
                total_results=0,
                documents=[],
                processing_time_ms=processing_time
            )
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    async def get_campaign_context(
        self, 
        organization_id: str, 
        document_ids: List[str]
    ) -> str:
        """Get combined context from campaign documents."""
        try:
            contents = []
            
            for doc_id in document_ids:
                # Query for all chunks of this document
                query = DocumentQuery(
                    query="",  # Empty query to get all content
                    organization_id=organization_id,
                    filters={"document_id": doc_id},
                    top_k=100  # Get all chunks
                )
                
                results = self.query_documents(query)
                
                # Combine all chunks for this document
                doc_content = "\n".join([doc.content for doc in results.documents])
                if doc_content.strip():
                    contents.append(doc_content)
            
            return "\n\n".join(contents)
            
        except Exception as e:
            self.logger.error(f"Error getting campaign context: {str(e)}")
            return ""
    
    def get_organization_stats(self, org_id: str) -> Dict[str, Any]:
        """Get statistics for an organization."""
        try:
            org_data = self.document_manager.get_organization(org_id)
            if not org_data:
                return {"error": "Organization not found"}
            
            documents = self.document_manager.get_documents_by_organization(org_id)
            
            total_chunks = sum(doc.get('chunk_count', 0) for doc in documents)
            total_content_length = sum(doc.get('content_length', 0) for doc in documents)
            
            return {
                "organization_id": org_id,
                "organization_name": org_data.get('name', ''),
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "total_content_length": total_content_length,
                "average_chunks_per_document": total_chunks / len(documents) if documents else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting organization stats for {org_id}: {str(e)}")
            return {"error": str(e)}