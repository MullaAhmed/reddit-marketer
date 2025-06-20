"""
Vector storage operations using Haystack.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

from haystack import Document
from app.clients.storage_client import VectorStorageClient

logger = logging.getLogger(__name__)


class VectorStorage:
    """
    Vector storage manager for document embeddings and retrieval.
    """
    
    def __init__(self, vector_storage_client: VectorStorageClient):
        """Initialize vector storage."""
        self.storage_client = vector_storage_client
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
        Store document chunks in vector storage.
        
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
                # Create a unique ID for each chunk
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
                
                # Use chunk_id as the document ID for direct retrieval
                doc = Document(id=chunk_id, content=chunk, meta=doc_metadata)
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
        Query documents from vector storage.
        
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
            elif method == "keyword":
                # Use BM25/ChromaQueryText keyword search
                documents = self.storage_client.query_documents_bm25(
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
        store_type: str = "chroma",
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document ID using direct ChromaDB get method.
        
        Args:
            org_id: Organization ID
            document_id: Document ID to retrieve chunks for
            store_type: Storage type
            query: Optional query for relevance-based retrieval
            
        Returns:
            List of document chunks
        """
        try:
            document_chunks = []
            if query:
                # Use semantic search with document_id filter
                retrieved_docs = self.storage_client.query_documents(
                    org_id=org_id,
                    query=query,
                    top_k=10, # Retrieve more to ensure enough relevant chunks
                    filters={"document_id": document_id},
                    store_type=store_type
                )
                # Convert retrieved_docs (list of dicts) to Haystack Document objects
                for doc_data in retrieved_docs:
                    document_chunks.append(Document(
                        id=doc_data.get('metadata', {}).get('chunk_id', str(uuid4())),
                        content=doc_data.get('content', ''),
                        meta=doc_data.get('metadata', {})
                    ))
            else:
                # Fallback to filtering all documents if no query
                document_store = self.storage_client.get_document_store(org_id, store_type)
                all_documents = document_store.filter_documents()
                for doc in all_documents:
                    if doc.meta.get("document_id") == document_id:
                        document_chunks.append(doc)
            
            # Sort chunks by chunk_index to maintain order
            document_chunks.sort(key=lambda doc: doc.meta.get("chunk_index", 0))
            
            # Format results
            results = []
            for doc in document_chunks:
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
        """Delete all chunks of a document."""
        try:
            # Get all chunks for this document
            chunks = self.get_document_chunks_by_document_id(org_id, document_id)
            
            if not chunks:
                self.logger.info(f"No chunks found to delete for document {document_id}")
                return True
            
            # Get the document store
            document_store = self.storage_client.get_document_store(org_id)
            
            # Extract chunk IDs
            chunk_ids = []
            for chunk in chunks:
                chunk_id = chunk["metadata"].get("chunk_id")
                if chunk_id:
                    chunk_ids.append(chunk_id)
            
            # Delete chunks using ChromaDB's delete method
            if chunk_ids and hasattr(document_store, 'delete'):
                try:
                    document_store.delete(ids=chunk_ids)
                    self.logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
                    return True
                except Exception as e:
                    self.logger.error(f"Error deleting chunks for document {document_id}: {e}")
                    return False
            else:
                self.logger.warning(f"Could not delete document {document_id}: no chunk IDs found or delete method not available")
                return False
                
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
            # Delete existing chunks
            self.delete_document(org_id, document_id)
            
            # Chunk new content
            from app.utils.text_processing import chunk_text
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