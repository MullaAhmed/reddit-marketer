"""
Vector storage using Haystack and ChromaDB.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from haystack import Document

from src.clients.haystack_client import HaystackClient
from src.utils.text_utils import chunk_text
from src.config.settings import settings

logger = logging.getLogger(__name__)


class VectorStorage:
    """
    Vector storage manager using Haystack and ChromaDB.
    """
    
    def __init__(self):
        """Initialize vector storage with Haystack client."""
        self.haystack_client = HaystackClient()
        self.logger = logger
    
    def store_document_chunks(
        self,
        org_id: str,
        document_id: str,
        title: str,
        chunks: List[str],
        metadata: Dict[str, Any] = None
    ) -> tuple[bool, str]:
        """
        Store document chunks in vector storage using Haystack.
        
        Args:
            org_id: Organization ID
            document_id: Document ID
            title: Document title
            chunks: List of text chunks
            metadata: Additional metadata
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not chunks:
                return False, "No chunks provided"
            
            # Create Haystack Document objects
            documents = []
            base_metadata = metadata or {}
            
            for i, chunk in enumerate(chunks):
                # Create unique ID for each chunk
                chunk_id = f"{document_id}_chunk_{i}"
                
                doc_metadata = {
                    **base_metadata,
                    "document_id": document_id,
                    "organization_id": org_id,
                    "title": title,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    "chunk_id": chunk_id
                }
                
                # Create Haystack Document
                doc = Document(id=chunk_id, content=chunk, meta=doc_metadata)
                documents.append(doc)
            
            # Store documents using Haystack
            success = self.haystack_client.store_documents(org_id, documents)
            
            if success:
                self.logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
                return True, f"Successfully stored {len(chunks)} chunks"
            else:
                return False, "Failed to store document chunks"
                
        except Exception as e:
            self.logger.error(f"Error storing document chunks: {str(e)}")
            return False, f"Error storing chunks: {str(e)}"
    
    def query_documents(
        self,
        org_id: str,
        query: str,
        method: str = "semantic",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from vector storage using Haystack.
        
        Args:
            org_id: Organization ID
            query: Search query
            method: Retrieval method ("semantic" or "keyword")
            top_k: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of document results
        """
        try:
            if method == "semantic":
                documents = self.haystack_client.query_documents_semantic(
                    org_id=org_id,
                    query=query,
                    top_k=top_k,
                    filters=filters
                )
            elif method == "keyword":
                documents = self.haystack_client.query_documents_keyword(
                    org_id=org_id,
                    query=query,
                    top_k=top_k,
                    filters=filters
                )
            else:
                raise ValueError(f"Unsupported search method: {method}")
            
            # Format results
            results = []
            for doc in documents:
                result = {
                    "content": doc.content,
                    "score": getattr(doc, 'score', 0.0),
                    "metadata": doc.meta,
                    "document_id": doc.meta.get("document_id", "unknown"),
                    "title": doc.meta.get("title", "Untitled")
                }
                results.append(result)
            
            self.logger.debug(f"Retrieved {len(results)} documents for query '{query}' using {method} search")
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying documents: {str(e)}")
            return []
    
    def get_document_chunks_by_document_id(
        self,
        org_id: str,
        document_id: str,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document ID using Haystack.
        
        Args:
            org_id: Organization ID
            document_id: Document ID to retrieve chunks for
            query: Optional query for relevance-based retrieval
            
        Returns:
            List of document chunks
        """
        try:
            if query:
                # Use semantic search with document_id filter
                documents = self.haystack_client.query_documents_semantic(
                    org_id=org_id,
                    query=query,
                    top_k=50,  # Get more chunks for comprehensive context
                    filters={"document_id": document_id}
                )
            else:
                # Get all chunks for the document
                documents = self.haystack_client.get_documents_by_filters(
                    org_id=org_id,
                    filters={"document_id": document_id}
                )
            
            # Sort chunks by chunk_index to maintain order
            documents.sort(key=lambda doc: doc.meta.get("chunk_index", 0))
            
            # Format results
            results = []
            for doc in documents:
                result = {
                    "content": doc.content,
                    "metadata": doc.meta,
                    "document_id": doc.meta.get("document_id", "unknown"),
                    "title": doc.meta.get("title", "Untitled"),
                    "chunk_index": doc.meta.get("chunk_index", 0)
                }
                results.append(result)
            
            self.logger.debug(f"Retrieved {len(results)} chunks for document {document_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    def delete_document(self, org_id: str, document_id: str) -> bool:
        """Delete all chunks of a document using Haystack."""
        try:
            # Get all chunks for this document
            chunks = self.get_document_chunks_by_document_id(org_id, document_id)
            
            if not chunks:
                self.logger.info(f"No chunks found to delete for document {document_id}")
                return True
            
            # Extract chunk IDs
            chunk_ids = []
            for chunk in chunks:
                chunk_id = chunk["metadata"].get("chunk_id")
                if chunk_id:
                    chunk_ids.append(chunk_id)
            
            # Delete chunks using Haystack
            if chunk_ids:
                success = self.haystack_client.delete_documents(org_id, chunk_ids)
                if success:
                    self.logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
                return success
            else:
                self.logger.warning(f"No chunk IDs found for document {document_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def get_storage_info(self, org_id: str) -> Dict[str, Any]:
        """Get storage information for organization using Haystack."""
        try:
            return self.haystack_client.get_storage_stats(org_id)
        except Exception as e:
            self.logger.error(f"Error getting storage info for org {org_id}: {str(e)}")
            return {
                "organization_id": org_id,
                "error": str(e)
            }
    
    def update_document_chunks(
        self,
        org_id: str,
        document_id: str,
        title: str,
        new_content: str,
        metadata: Dict[str, Any] = None,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> tuple[bool, str]:
        """
        Update document by replacing all its chunks using Haystack.
        
        Args:
            org_id: Organization ID
            document_id: Document ID
            title: Document title
            new_content: New document content
            metadata: Document metadata
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Delete existing chunks
            self.delete_document(org_id, document_id)
            
            # Chunk new content
            chunk_size = chunk_size or settings.CHUNK_SIZE
            chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
            chunks = chunk_text(new_content, chunk_size, chunk_overlap)
            
            # Store new chunks
            return self.store_document_chunks(
                org_id=org_id,
                document_id=document_id,
                title=title,
                chunks=chunks,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error updating document {document_id}: {str(e)}")
            return False, f"Error updating document: {str(e)}"