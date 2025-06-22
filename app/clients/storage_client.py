"""
Storage clients for different storage backends using Haystack.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever, ChromaQueryTextRetriever
from haystack import Document
from haystack.utils import Secret

from app.core.settings import settings

logger = logging.getLogger(__name__)


class VectorStorageClient:
    """
    Client for vector storage operations using Haystack.
    """
    
    def __init__(self):
        """Initialize the vector storage client."""
        self.logger = logger
        
        # Storage instances cache
        self._document_stores = {}
        self._embedders = {}
        self._retrievers = {}
        self._query_text_retrievers = {}
    
    def get_document_store(self, org_id: str, store_type: str = "chroma") -> ChromaDocumentStore:
        """Get or create document store for organization."""
        cache_key = f"{org_id}_{store_type}"
        
        if cache_key in self._document_stores:
            return self._document_stores[cache_key]
        
        # Create ChromaDB directory for organization
        chroma_dir = os.path.join(settings.DATA_DIR, "chromadb", org_id)
        Path(chroma_dir).mkdir(parents=True, exist_ok=True)
        
        document_store = ChromaDocumentStore(
            collection_name=f"org_{org_id}_docs",
            persist_path=chroma_dir
        )
        
        self._document_stores[cache_key] = document_store
        return document_store
    
    def get_document_embedder(self, model: str = "text-embedding-3-large") -> OpenAIDocumentEmbedder:
        """Get or create document embedder."""
        if model not in self._embedders:
            self._embedders[model] = OpenAIDocumentEmbedder(
                model=model,
                api_key=Secret.from_token(settings.OPENAI_API_KEY)
            )
        return self._embedders[model]
    
    def get_text_embedder(self, model: str = "text-embedding-3-large") -> OpenAITextEmbedder:
        """Get or create text embedder."""
        embedder_key = f"text_{model}"
        if embedder_key not in self._embedders:
            self._embedders[embedder_key] = OpenAITextEmbedder(
                model=model,
                api_key=Secret.from_token(settings.OPENAI_API_KEY)
            )
        return self._embedders[embedder_key]
    
    def get_retriever(self, org_id: str, store_type: str = "chroma") -> ChromaEmbeddingRetriever:
        """Get or create embedding retriever for organization."""
        cache_key = f"{org_id}_{store_type}_retriever"
        
        if cache_key in self._retrievers:
            return self._retrievers[cache_key]
        
        document_store = self.get_document_store(org_id, store_type)
        
        retriever = ChromaEmbeddingRetriever(document_store=document_store)
        
        self._retrievers[cache_key] = retriever
        return retriever
    
    def get_query_text_retriever(self, org_id: str, store_type: str = "chroma") -> ChromaQueryTextRetriever:
        """Get or create ChromaQueryTextRetriever for keyword search on ChromaDB."""
        cache_key = f"{org_id}_{store_type}_query_text"
        
        if cache_key in self._query_text_retrievers:
            return self._query_text_retrievers[cache_key]
        
        document_store = self.get_document_store(org_id, store_type)
        retriever = ChromaQueryTextRetriever(document_store=document_store)
        
        self._query_text_retrievers[cache_key] = retriever
        return retriever
    
    def get_document_by_id(self, org_id: str, document_id: str, store_type: str = "chroma") -> Optional[Document]:
        """
        Get a document in the collection by its ID using ChromaDB's direct get method.
        
        Args:
            org_id: Organization ID
            document_id: ID of the document to get
            store_type: Storage type
            
        Returns:
            Document: The document with the given ID, or None if not found
        """
        try:
            document_store = self.get_document_store(org_id, store_type)
            
            if hasattr(document_store, 'get'):
                # Use ChromaDB's direct get method
                result = document_store.get(ids=[document_id])
                
                if result and "documents" in result and result["documents"]:
                    return Document(
                        id=document_id,
                        content=result["documents"][0], 
                        meta=result["metadatas"][0] if result["metadatas"] else {}
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting document by ID {document_id}: {str(e)}")
            return None
    
    def store_documents(
        self, 
        org_id: str, 
        documents: List[Document], 
        store_type: str = "chroma"
    ) -> bool:
        """Store documents in vector storage."""
        try:
            # Get components
            document_store = self.get_document_store(org_id, store_type)
            embedder = self.get_document_embedder()
            
            # Embed documents
            embedded_docs = embedder.run(documents)["documents"]
            
            # Ensure documents have IDs for direct retrieval
            for i, doc in enumerate(embedded_docs):
                if not hasattr(doc, 'id') or not doc.id:
                    # Generate ID from metadata if available
                    chunk_id = doc.meta.get("chunk_id")
                    if chunk_id:
                        doc.id = chunk_id
                    else:
                        # Fallback ID generation
                        doc_id = doc.meta.get("document_id", f"doc_{i}")
                        chunk_idx = doc.meta.get("chunk_index", i)
                        doc.id = f"{doc_id}_chunk_{chunk_idx}"
            
            # Store in document store
            document_store.write_documents(embedded_docs)
            
            self.logger.info(f"Stored {len(documents)} documents for org {org_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing documents for org {org_id}: {str(e)}")
            return False
    
    def query_documents(
        self, 
        org_id: str, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        store_type: str = "chroma"
    ) -> List[Document]:
        """Query documents from vector storage using semantic search."""
        try:
            # Get components
            text_embedder = self.get_text_embedder()
            retriever = self.get_retriever(org_id, store_type)
            
            # Embed query
            query_embedding = text_embedder.run(query)["embedding"]
            
            # Format filters for ChromaDB if needed
            formatted_filters = None
            if filters:
                formatted_filters = self._format_filters_for_chroma(filters)
            
            # Retrieve documents
            result = retriever.run(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=formatted_filters
            )
            
            return result["documents"]
            
        except Exception as e:
            self.logger.error(f"Error querying documents for org {org_id}: {str(e)}")
            return []
    
    def query_documents_bm25(
        self,
        org_id: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        store_type: str = "chroma"
    ) -> List[Document]:
        """Query documents using BM25 keyword search."""
        try:
            # Format filters for ChromaDB if needed
            formatted_filters = None
            if filters:
                formatted_filters = self._format_filters_for_chroma(filters)
            
            # Use ChromaQueryTextRetriever for ChromaDB
            retriever = self.get_query_text_retriever(org_id, store_type)
            
            # Perform keyword search
            result = retriever.run(
                query=query,
                top_k=top_k,
                filters=formatted_filters
            )
            
            return result["documents"]
            
        except Exception as e:
            self.logger.error(f"Error in keyword search for org {org_id}: {str(e)}")
            # Fallback to semantic search if keyword search fails
            self.logger.info(f"Falling back to semantic search for org {org_id}")
            return self.query_documents(org_id, query, top_k, filters, store_type)
    
    def get_documents_by_filters(
        self,
        org_id: str,
        filters: Dict[str, Any],
        store_type: str = "chroma"
    ) -> List[Document]:
        """Get all documents matching the given filters without top_k limitation."""
        try:
            document_store = self.get_document_store(org_id, store_type)
            
            # Format filters for ChromaDB if needed
            formatted_filters = self._format_filters_for_chroma(filters)
            self.logger.debug(f"Original filters: {filters}")
            self.logger.debug(f"Formatted filters for ChromaDB: {formatted_filters}")
            
            # Use the document store's filter_documents method to get all matching documents
            # This bypasses the top_k limitation of retrievers
            documents = document_store.filter_documents(filters=formatted_filters)
            
            self.logger.debug(f"Retrieved {len(documents)} documents with filters {filters}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents by filters for org {org_id}: {str(e)}")
            return []
    
    def _format_filters_for_chroma(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Format filters for ChromaDB compatibility using proper where clause structure."""
        if not filters:
            return {}
        
        # ChromaDB expects filters in a where clause format
        # For simple equality filters, we can use the direct format
        # For complex filters, we need to use the $and, $or operators
        
        if len(filters) == 1:
            # Single filter - use direct format
            key, value = next(iter(filters.items()))
            if isinstance(value, (str, int, float, bool)):
                return {key: {"$eq": value}}
            elif isinstance(value, list):
                return {key: {"$in": value}}
            elif isinstance(value, dict) and any(op in value for op in ["$eq", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte"]):
                # Already properly formatted
                return {key: value}
            else:
                return {key: {"$eq": str(value)}}
        else:
            # Multiple filters - use $and operator
            conditions = []
            for key, value in filters.items():
                if isinstance(value, (str, int, float, bool)):
                    conditions.append({key: {"$eq": value}})
                elif isinstance(value, list):
                    conditions.append({key: {"$in": value}})
                elif isinstance(value, dict) and any(op in value for op in ["$eq", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte"]):
                    conditions.append({key: value})
                else:
                    conditions.append({key: {"$eq": str(value)}})
            
            return {"$and": conditions}
    
    def get_storage_stats(self, org_id: str, store_type: str = "chroma") -> Dict[str, Any]:
        """Get storage statistics for organization."""
        try:
            document_store = self.get_document_store(org_id, store_type)
            
            # Get document count
            doc_count = document_store.count_documents()
            
            return {
                "organization_id": org_id,
                "store_type": store_type,
                "document_count": doc_count,
                "status": "healthy"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats for org {org_id}: {str(e)}")
            return {
                "organization_id": org_id,
                "store_type": store_type,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }