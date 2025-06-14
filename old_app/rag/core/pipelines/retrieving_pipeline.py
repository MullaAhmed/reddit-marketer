from typing import Optional, List, Dict, Any, Union, Literal
from haystack import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever, InMemoryBM25Retriever
from haystack.components.embedders import (
    OpenAITextEmbedder, 
    SentenceTransformersTextEmbedder
)

from rag.core.managers.document_stores import DocumentStoreManager
from rag.core.managers.embedders import EmbedderManager
from rag.core.managers.retrievers import RetrieverManager


class RetrievalPipeline:
    """Pipeline for different types of document retrieval."""
    
    def __init__(
        self,
        document_store: Optional[Union[InMemoryDocumentStore, ChromaDocumentStore]] = None,
        embedder: Optional[Union[OpenAITextEmbedder, SentenceTransformersTextEmbedder]] = None,
        semantic_retriever: Optional[InMemoryEmbeddingRetriever] = None,
        keyword_retriever: Optional[InMemoryBM25Retriever] = None,
        default_top_k: int = 5
    ):
        """
        Initialize RetrievalPipeline with various retrieval components.
        
        Args:
            document_store: Document store to use
            embedder: Text embedder for semantic retrieval
            semantic_retriever: Semantic retriever component
            keyword_retriever: Keyword retriever component
            default_top_k: Default number of documents to retrieve
        """
        # Initialize core components
        self.document_store = document_store or DocumentStoreManager.initialize_document_store()
        self.embedder = embedder or EmbedderManager.initialize_embedder(embedding_type="text")
        self.default_top_k = default_top_k
        
        # Initialize retrievers
        self.semantic_retriever = semantic_retriever or RetrieverManager.initialize_retriever(
            retriever_type="semantic",
            document_store=self.document_store,
            top_k=default_top_k
        )
        
        self.keyword_retriever = keyword_retriever or RetrieverManager.initialize_retriever(
            retriever_type="keyword-based",
            document_store=self.document_store,
            top_k=default_top_k
        )
        
        # Build pipelines for different retrieval types
        self.semantic_pipeline = self._build_semantic_pipeline()
        self.keyword_pipeline = self._build_keyword_pipeline()
    
    def _build_semantic_pipeline(self) -> Pipeline:
        """Build semantic retrieval pipeline."""
        pipeline = Pipeline()
        pipeline.add_component("embedder", self.embedder)
        pipeline.add_component("retriever", self.semantic_retriever)
        pipeline.connect("embedder.embedding", "retriever.query_embedding")
        return pipeline
    
    def _build_keyword_pipeline(self) -> Pipeline:
        """Build keyword retrieval pipeline."""
        pipeline = Pipeline()
        pipeline.add_component("retriever", self.keyword_retriever)
        return pipeline
    
    def semantic_retrieve(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using semantic search (embeddings).
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        # Prepare inputs
        inputs = {"embedder": {"text": query}}
        
        # Add retriever parameters
        retriever_params = {}
        if top_k is not None:
            retriever_params["top_k"] = top_k
        if filters is not None:
            retriever_params["filters"] = filters
            
        if retriever_params:
            inputs["retriever"] = retriever_params
        
        # Run pipeline
        result = self.semantic_pipeline.run(inputs)
        
        return result["retriever"]["documents"]
    
    def keyword_retrieve(
        self, 
        query: str, 
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using keyword search (BM25).
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        # Prepare inputs
        inputs = {"retriever": {"query": query}}
        
        # Add optional parameters
        if top_k is not None:
            inputs["retriever"]["top_k"] = top_k
        if filters is not None:
            inputs["retriever"]["filters"] = filters
        
        # Run pipeline
        result = self.keyword_pipeline.run(inputs)
        
        return result["retriever"]["documents"]
    
    def retrieve(
        self, 
        query: str, 
        method: Literal["semantic", "keyword"] = "semantic",
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using specified method.
        
        Args:
            query: Search query
            method: Retrieval method ("semantic" or "keyword")
            top_k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents
        """
        if method == "semantic":
            return self.semantic_retrieve(query, top_k, filters)
        elif method == "keyword":
            return self.keyword_retrieve(query, top_k, filters)
        else:
            raise ValueError(f"Unsupported retrieval method: {method}")
    
    def multi_retrieve(
        self, 
        query: str, 
        methods: List[Literal["semantic", "keyword"]] = ["semantic", "keyword"],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve documents using multiple methods.
        
        Args:
            query: Search query
            methods: List of retrieval methods to use
            top_k: Number of documents to retrieve per method
            filters: Metadata filters to apply
            
        Returns:
            Dictionary with results from each method
        """
        results = {}
        
        for method in methods:
            try:
                results[method] = self.retrieve(query, method, top_k, filters)
            except Exception as e:
                results[method] = {"error": str(e)}
        
        return results