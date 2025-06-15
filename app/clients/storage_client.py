"""
Storage clients for different storage backends.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever, InMemoryBM25Retriever
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack import Document
from haystack.utils import Secret

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStorageClient:
    """
    Client for vector storage operations using Haystack.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the vector storage client."""
        self.data_dir = data_dir
        self.logger = logger
        
        # Storage instances cache
        self._document_stores = {}
        self._embedders = {}
        self._retrievers = {}
        self._bm25_retrievers = {}
    
    def get_document_store(self, org_id: str, store_type: str = "chroma") -> ChromaDocumentStore:
        """Get or create document store for organization."""
        cache_key = f"{org_id}_{store_type}"
        
        if cache_key in self._document_stores:
            return self._document_stores[cache_key]
        
        if store_type == "chroma":
            # Create ChromaDB directory for organization
            chroma_dir = os.path.join(self.data_dir, "chromadb", org_id)
            Path(chroma_dir).mkdir(parents=True, exist_ok=True)
            
            document_store = ChromaDocumentStore(
                collection_name=f"org_{org_id}_docs",
                persist_path=chroma_dir
            )
        elif store_type == "in_memory":
            document_store = InMemoryDocumentStore()
        else:
            raise ValueError(f"Unsupported store type: {store_type}")
        
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
                api_key=settings.OPENAI_API_KEY
            )
        return self._embedders[embedder_key]
    
    def get_retriever(self, org_id: str, store_type: str = "chroma") -> ChromaEmbeddingRetriever:
        """Get or create embedding retriever for organization."""
        cache_key = f"{org_id}_{store_type}_retriever"
        
        if cache_key in self._retrievers:
            return self._retrievers[cache_key]
        
        document_store = self.get_document_store(org_id, store_type)
        
        if store_type == "chroma":
            retriever = ChromaEmbeddingRetriever(document_store=document_store)
        elif store_type == "in_memory":
            retriever = InMemoryEmbeddingRetriever(document_store=document_store)
        else:
            raise ValueError(f"Unsupported store type: {store_type}")
        
        self._retrievers[cache_key] = retriever
        return retriever
    
    def get_bm25_retriever(self, org_id: str, store_type: str = "chroma") -> InMemoryBM25Retriever:
        """Get or create BM25 retriever for keyword search."""
        cache_key = f"{org_id}_{store_type}_bm25"
        
        if cache_key in self._bm25_retrievers:
            return self._bm25_retrievers[cache_key]
        
        document_store = self.get_document_store(org_id, store_type)
        
        # BM25 retriever only works with InMemoryDocumentStore
        # For ChromaDB, we'll need to create a separate in-memory store for BM25
        if store_type == "chroma":
            # Create a separate in-memory store for BM25 search
            in_memory_store = InMemoryDocumentStore()
            
            # Copy documents from ChromaDB to in-memory store for BM25
            try:
                # Get all documents from ChromaDB
                all_docs = document_store.filter_documents()
                if all_docs:
                    in_memory_store.write_documents(all_docs)
                    self.logger.debug(f"Copied {len(all_docs)} documents to in-memory store for BM25")
            except Exception as e:
                self.logger.warning(f"Could not copy documents for BM25: {e}")
            
            retriever = InMemoryBM25Retriever(document_store=in_memory_store)
        else:
            retriever = InMemoryBM25Retriever(document_store=document_store)
        
        self._bm25_retrievers[cache_key] = retriever
        return retriever
    
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
            
            # Store in document store
            document_store.write_documents(embedded_docs)
            
            # Update BM25 retriever cache if it exists
            bm25_cache_key = f"{org_id}_{store_type}_bm25"
            if bm25_cache_key in self._bm25_retrievers:
                # Clear the cache so it gets recreated with new documents
                del self._bm25_retrievers[bm25_cache_key]
            
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
            
            # Retrieve documents
            result = retriever.run(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
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
            # Get BM25 retriever
            bm25_retriever = self.get_bm25_retriever(org_id, store_type)
            
            # Perform BM25 search
            result = bm25_retriever.run(
                query=query,
                top_k=top_k,
                filters=filters
            )
            
            return result["documents"]
            
        except Exception as e:
            self.logger.error(f"Error in BM25 search for org {org_id}: {str(e)}")
            return []
    
    def get_documents_by_filters(
        self,
        org_id: str,
        filters: Dict[str, Any],
        store_type: str = "chroma"
    ) -> List[Document]:
        """Get all documents matching the given filters without top_k limitation."""
        try:
            document_store = self.get_document_store(org_id, store_type)
            
            # Use the document store's filter_documents method to get all matching documents
            # This bypasses the top_k limitation of retrievers
            documents = document_store.filter_documents(filters=filters)
            
            self.logger.debug(f"Retrieved {len(documents)} documents with filters {filters}")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents by filters for org {org_id}: {str(e)}")
            return []
    
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


class JSONStorageClient:
    """
    Client for JSON file storage operations.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the JSON storage client."""
        self.data_dir = data_dir
        self.json_dir = os.path.join(data_dir, "json")
        Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def get_file_path(self, filename: str) -> str:
        """Get full path for JSON file."""
        return os.path.join(self.json_dir, filename)
    
    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        file_path = self.get_file_path(filename)
        
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to JSON file."""
        file_path = self.get_file_path(filename)
        
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.debug(f"Saved data to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {str(e)}")
            return False
    
    def append_data(self, filename: str, item: Dict[str, Any]) -> bool:
        """Append item to JSON file."""
        data = self.load_data(filename)
        data.append(item)
        return self.save_data(filename, data)
    
    def update_item(
        self, 
        filename: str, 
        item: Dict[str, Any], 
        id_field: str = 'id'
    ) -> bool:
        """Update or add an item in JSON file."""
        data = self.load_data(filename)
        
        # Find and update existing item
        updated = False
        for i, existing_item in enumerate(data):
            if existing_item.get(id_field) == item.get(id_field):
                data[i] = item
                updated = True
                break
        
        # Add new item if not found
        if not updated:
            data.append(item)
        
        return self.save_data(filename, data)
    
    def find_item(
        self, 
        filename: str, 
        item_id: str, 
        id_field: str = 'id'
    ) -> Optional[Dict[str, Any]]:
        """Find an item in JSON file by ID."""
        data = self.load_data(filename)
        
        for item in data:
            if item.get(id_field) == item_id:
                return item
        
        return None
    
    def filter_items(
        self, 
        filename: str, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter items in JSON file by criteria."""
        data = self.load_data(filename)
        
        filtered_items = []
        for item in data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_items.append(item)
        
        return filtered_items