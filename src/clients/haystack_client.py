"""
Haystack client for RAG operations using ChromaDB and OpenAI embeddings.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from haystack import Document
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever, ChromaQueryTextRetriever
from haystack.utils import Secret

from src.config.settings import settings

logger = logging.getLogger(__name__)


class HaystackClient:
    """
    Haystack client for advanced RAG operations with ChromaDB.
    """
    
    def __init__(self):
        """Initialize the Haystack client."""
        self.logger = logger
        
        # Storage instances cache
        self._document_stores = {}
        self._embedders = {}
        self._retrievers = {}
        self._query_text_retrievers = {}
    
    def get_document_store(self, org_id: str) -> ChromaDocumentStore:
        """Get or create ChromaDB document store for organization."""
        cache_key = f"{org_id}_chroma"
        
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
    
    def get_document_embedder(self, model: str = None) -> OpenAIDocumentEmbedder:
        """Get or create document embedder."""
        model = model or settings.EMBEDDING_MODEL
        
        if model not in self._embedders:
            self._embedders[model] = OpenAIDocumentEmbedder(
                model=model,
                api_key=Secret.from_token(settings.OPENAI_API_KEY)
            )
        return self._embedders[model]
    
    def get_text_embedder(self, model: str = None) -> OpenAITextEmbedder:
        """Get or create text embedder."""
        model = model or settings.EMBEDDING_MODEL
        embedder_key = f"text_{model}"
        
        if embedder_key not in self._embedders:
            self._embedders[embedder_key] = OpenAITextEmbedder(
                model=model,
                api_key=Secret.from_token(settings.OPENAI_API_KEY)
            )
        return self._embedders[embedder_key]
    
    def get_embedding_retriever(self, org_id: str) -> ChromaEmbeddingRetriever:
        """Get or create embedding retriever for organization."""
        cache_key = f"{org_id}_embedding_retriever"
        
        if cache_key in self._retrievers:
            return self._retrievers[cache_key]
        
        document_store = self.get_document_store(org_id)
        retriever = ChromaEmbeddingRetriever(document_store=document_store)
        
        self._retrievers[cache_key] = retriever
        return retriever
    
    def get_query_text_retriever(self, org_id: str) -> ChromaQueryTextRetriever:
        """Get or create ChromaQueryTextRetriever for keyword search."""
        cache_key = f"{org_id}_query_text"
        
        if cache_key in self._query_text_retrievers:
            return self._query_text_retrievers[cache_key]
        
        document_store = self.get_document_store(org_id)
        retriever = ChromaQueryTextRetriever(document_store=document_store)
        
        self._query_text_retrievers[cache_key] = retriever
        return retriever
    
    def store_documents(
        self, 
        org_id: str, 
        documents: List[Document]
    ) -> bool:
        """Store documents with embeddings in ChromaDB."""
        try:
            # Get components
            document_store = self.get_document_store(org_id)
            embedder = self.get_document_embedder()
            
            # Generate embeddings
            embedded_docs = embedder.run(documents)["documents"]
            
            # Ensure documents have proper IDs
            for i, doc in enumerate(embedded_docs):
                if not hasattr(doc, 'id') or not doc.id:
                    chunk_id = doc.meta.get("chunk_id")
                    if chunk_id:
                        doc.id = chunk_id
                    else:
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
    
    def query_documents_semantic(
        self, 
        org_id: str, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Query documents using semantic search."""
        try:
            # Get components
            text_embedder = self.get_text_embedder()
            retriever = self.get_embedding_retriever(org_id)
            
            # Generate query embedding
            query_embedding = text_embedder.run(query)["embedding"]
            
            # Format filters for ChromaDB
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
            self.logger.error(f"Error in semantic search for org {org_id}: {str(e)}")
            return []
    
    def query_documents_keyword(
        self,
        org_id: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Query documents using keyword search."""
        try:
            # Format filters for ChromaDB
            formatted_filters = None
            if filters:
                formatted_filters = self._format_filters_for_chroma(filters)
            
            # Use ChromaQueryTextRetriever
            retriever = self.get_query_text_retriever(org_id)
            
            # Perform keyword search
            result = retriever.run(
                query=query,
                top_k=top_k,
                filters=formatted_filters
            )
            
            return result["documents"]
            
        except Exception as e:
            self.logger.error(f"Error in keyword search for org {org_id}: {str(e)}")
            # Fallback to semantic search
            return self.query_documents_semantic(org_id, query, top_k, filters)
    
    def get_documents_by_filters(
        self,
        org_id: str,
        filters: Dict[str, Any]
    ) -> List[Document]:
        """Get all documents matching filters."""
        try:
            document_store = self.get_document_store(org_id)
            
            # Format filters for ChromaDB
            formatted_filters = self._format_filters_for_chroma(filters)
            
            # Use document store's filter method
            documents = document_store.filter_documents(filters=formatted_filters)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents by filters for org {org_id}: {str(e)}")
            return []
    
    def get_document_by_id(self, org_id: str, document_id: str) -> Optional[Document]:
        """Get a document by its ID."""
        try:
            document_store = self.get_document_store(org_id)
            
            # Use ChromaDB's direct get method
            if hasattr(document_store, 'get'):
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
    
    def delete_documents(self, org_id: str, document_ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            document_store = self.get_document_store(org_id)
            
            # Use ChromaDB's delete method
            if hasattr(document_store, 'delete') and document_ids:
                document_store.delete(ids=document_ids)
                self.logger.info(f"Deleted {len(document_ids)} documents for org {org_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting documents for org {org_id}: {str(e)}")
            return False
    
    def get_storage_stats(self, org_id: str) -> Dict[str, Any]:
        """Get storage statistics for organization."""
        try:
            document_store = self.get_document_store(org_id)
            
            # Get document count
            doc_count = document_store.count_documents()
            
            return {
                "organization_id": org_id,
                "document_count": doc_count,
                "status": "healthy"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats for org {org_id}: {str(e)}")
            return {
                "organization_id": org_id,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def _format_filters_for_chroma(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format filters for ChromaDB compatibility.
        
        ChromaDB prefers simple key-value pairs for basic equality filters.
        Only use explicit operators for complex conditions.
        """
        if not filters:
            return {}
        
        # For single, simple equality filters, use direct key-value format
        if len(filters) == 1:
            key, value = next(iter(filters.items()))
            
            # If it's a simple value (string, int, float, bool), use direct format
            if isinstance(value, (str, int, float, bool)):
                return {key: value}
            elif isinstance(value, list):
                return {key: {"$in": value}}
            elif isinstance(value, dict) and any(op in value for op in ["$eq", "$ne", "$in", "$nin", "$gt", "$gte", "$lt", "$lte"]):
                # Already properly formatted with operators
                return {key: value}
            else:
                # Convert to string and use direct format
                return {key: str(value)}
        else:
            # Multiple filters - use $and operator with explicit conditions
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