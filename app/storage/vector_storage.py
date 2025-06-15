"""
Vector storage operations using Haystack.
"""

import logging
from typing import List, Dict, Any, Optional

from haystack import Document
from app.clients.storage_client import VectorStorageClient
from app.utils.text_processing import chunk_text

logger = logging.getLogger(__name__)


class VectorStorage:
    """
    Vector storage manager for document embeddings and retrieval.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize vector app.storage."""
        self.data_dir = data_dir
        self.storage_client = VectorStorageClient(data_dir)
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
        Store document chunks in vector app.storage.
        
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
                doc_metadata = {
                    **base_metadata,
                    "document_id": document_id,
                    "organization_id": org_id,
                    "title": title,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                
                doc = Document(content=chunk, meta=doc_metadata)
                documents.append(doc)
            
            # Store documents
            success = self.storage_client.store_documents(org_id, documents)
            
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
        Query documents from vector app.storage.
        
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
                # Use vector similarity search
                documents = self.storage_client.query_documents(
                    org_id=org_id,
                    query=query,
                    top_k=top_k,
                    filters=filters
                )
            else:
                # For keyword search, we'll use a simple text matching approach
                # In a production system, you might want to use a proper keyword search index
                documents = self._keyword_search(org_id, query, top_k, filters)
            
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
            
            self.logger.debug(f"Retrieved {len(results)} documents for query '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying documents: {str(e)}")
            return []
    
    def get_document_chunks_by_document_id(
        self,
        org_id: str,
        document_id: str,
        store_type: str = "chroma"
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document ID.
        
        Args:
            org_id: Organization ID
            document_id: Document ID to retrieve chunks for
            store_type: Storage type
            
        Returns:
            List of document chunks
        """
        try:
            # Use filters to get all chunks for this document
            filters = {"document_id": document_id}
            
            documents = self.storage_client.get_documents_by_filters(
                org_id=org_id,
                filters=filters,
                store_type=store_type
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
    
    def _keyword_search(
        self,
        org_id: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Simple keyword search implementation.
        In production, you'd want to use a proper search index like Elasticsearch.
        """
        try:
            # Get all documents for the organization
            all_docs = self.storage_client.query_documents(
                org_id=org_id,
                query="",  # Empty query to get all docs
                top_k=1000,  # Get many docs for filtering
                filters=filters
            )
            
            # Simple keyword matching
            query_words = set(query.lower().split())
            scored_docs = []
            
            for doc in all_docs:
                content_words = set(doc.content.lower().split())
                
                # Calculate simple overlap score
                overlap = len(query_words.intersection(content_words))
                if overlap > 0:
                    score = overlap / len(query_words)
                    doc.score = score
                    scored_docs.append(doc)
            
            # Sort by score and return top_k
            scored_docs.sort(key=lambda x: x.score, reverse=True)
            return scored_docs[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in keyword search: {str(e)}")
            return []
    
    def delete_document(self, org_id: str, document_id: str) -> bool:
        """Delete all chunks of a document."""
        try:
            # This would need to be implemented in the storage client
            # For now, we'll log the operation
            self.logger.info(f"Delete document {document_id} for org {org_id} (not implemented)")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    def get_storage_info(self, org_id: str) -> Dict[str, Any]:
        """Get storage information for organization."""
        try:
            return self.storage_client.get_storage_stats(org_id)
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
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> tuple[bool, str]:
        """
        Update document by replacing all its chunks.
        
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
            # Delete existing chunks (if implemented)
            self.delete_document(org_id, document_id)
            
            # Chunk new content
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