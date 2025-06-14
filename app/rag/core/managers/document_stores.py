from typing import Optional, Literal, Dict, Any
import os

from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.chroma import ChromaDocumentStore


class DocumentStoreManager:
    """Manager for document store initialization and operations."""
    
    # Class-level dictionary to store document stores by rag_id
    _document_stores: Dict[str, Any] = {}
    
    @classmethod
    def initialize_document_store(
        cls,
        document_store_provider: Literal["in_memory", "chroma"] = "in_memory",
        rag_id: Optional[str] = None,
        **kwargs
    ) -> InMemoryDocumentStore | ChromaDocumentStore:
        """
        Initialize a document store based on the provided type.
        If rag_id is provided, creates or retrieves a dedicated document store for that ID.
        
        Args:
            document_store_provider: Type of document store to initialize
            rag_id: Optional RAG ID for dedicated document store
            **kwargs: Additional keyword arguments for the document store
            
        Returns:
            Initialized document store instance
        """
        # If no rag_id, return a new document store (for temporary operations)
        if rag_id is None:
            if document_store_provider == "in_memory":
                return InMemoryDocumentStore(**kwargs)
            elif document_store_provider == "chroma":
                return ChromaDocumentStore(**kwargs)
            else:
                raise ValueError(f"Unsupported document store provider: {document_store_provider}")
        
        # Check if document store for this rag_id already exists
        if rag_id in cls._document_stores:
            return cls._document_stores[rag_id]
        
        # Create a new document store for this rag_id
        if document_store_provider == "in_memory":
            document_store = InMemoryDocumentStore(**kwargs)
        elif document_store_provider == "chroma":
            if "collection_name" not in kwargs:
                kwargs["collection_name"] = f"collection_{rag_id}"
            
            if "persist_path" in kwargs:
                base_dir = kwargs["persist_path"]
                kwargs["persist_path"] = os.path.join(base_dir, rag_id)
                os.makedirs(kwargs["persist_path"], exist_ok=True)
            document_store = ChromaDocumentStore(**kwargs)
        else:
            raise ValueError(f"Unsupported document store provider: {document_store_provider}")
        
        # Store this document store for future use
        cls._document_stores[rag_id] = document_store
        return document_store
    
    @classmethod
    def get_document_store(cls, rag_id: str):
        """Get an existing document store for a rag_id."""
        if rag_id in cls._document_stores:
            return cls._document_stores[rag_id]
        return None
