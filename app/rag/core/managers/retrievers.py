from typing import Literal, Optional, Union, Tuple, Any, Dict

from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever, InMemoryBM25Retriever
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever, ChromaQueryTextRetriever

from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.chroma import ChromaDocumentStore

from rag.core.managers.document_stores import DocumentStoreManager


class RetrieverManager:
    """Manager for retriever initialization and operations."""
    
    @staticmethod
    def initialize_retriever(
        retriever_type: Literal["semantic", "keyword-based"] = "semantic",
        document_store: Optional[Union[InMemoryDocumentStore, ChromaDocumentStore]] = None,
        **kwargs
    ) -> Union[InMemoryEmbeddingRetriever, InMemoryBM25Retriever]:
        """
        Initialize a retriever based on the provided type.
        
        Args:
            retriever_type: Type of retriever to initialize
            document_store: Document store to use with the retriever
            **kwargs: Additional keyword arguments for the retriever
            
        Returns:
            Initialized retriever instance
        """
        if document_store is None:
            document_store = DocumentStoreManager.initialize_document_store()
        
        if isinstance(document_store, InMemoryDocumentStore):
            if retriever_type == "semantic":
                retriever = InMemoryEmbeddingRetriever(document_store=document_store, **kwargs)
            elif retriever_type == "keyword-based":
                retriever = InMemoryBM25Retriever(document_store=document_store, **kwargs)
            else:
                raise ValueError(f"Unsupported retriever type: {retriever_type}")
        elif isinstance(document_store, ChromaDocumentStore):
            if retriever_type == "semantic":
                retriever = ChromaEmbeddingRetriever(document_store=document_store, **kwargs)
            elif retriever_type == "keyword-based":
                retriever = ChromaQueryTextRetriever(document_store=document_store, **kwargs)
            else:
                raise ValueError(f"Unsupported retriever type: {retriever_type}")
        return retriever
