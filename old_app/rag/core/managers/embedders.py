from typing import Literal, Optional, Union, Dict, Any

from haystack.components.embedders import (
    OpenAIDocumentEmbedder, 
    OpenAITextEmbedder,
    SentenceTransformersDocumentEmbedder, 
    SentenceTransformersTextEmbedder
)


class EmbedderManager:
    """Manager for embedder initialization and operations."""
    
    @staticmethod
    def initialize_embedder(
        embedding_provider: Literal["openai", "sentence_transformers"] = "openai",
        embedding_type: Literal["document", "text"] = "document",
        model: Optional[str] = None,
        **kwargs
    ) -> Union[
        OpenAIDocumentEmbedder, 
        SentenceTransformersDocumentEmbedder,
        OpenAITextEmbedder, 
        SentenceTransformersTextEmbedder
    ]:
        """
        Initialize an embedder based on the provided type and provider.
        
        Args:
            embedding_provider: Provider of the embedding model
            embedding_type: Type of embedder to initialize
            model: Name of the embedding model
            **kwargs: Additional keyword arguments for the embedder
            
        Returns:
            Initialized embedder instance
        """
        # Set default models based on provider
        if model is None:
            if embedding_provider == "openai":
                model = "text-embedding-3-large"
            elif embedding_provider == "sentence_transformers":
                model = "sentence-transformers/all-MiniLM-L6-v2"
        
        # Initialize embedder based on provider and type
        if embedding_provider == "openai":
            if embedding_type == "document":
                embedder = OpenAIDocumentEmbedder(model=model, **kwargs)
            elif embedding_type == "text":
                embedder = OpenAITextEmbedder(model=model, **kwargs)
            else:
                raise ValueError(f"Unsupported embedding type: {embedding_type}")
                
        elif embedding_provider == "sentence_transformers":
            if embedding_type == "document":
                embedder = SentenceTransformersDocumentEmbedder(model=model, **kwargs)
            elif embedding_type == "text":
                embedder = SentenceTransformersTextEmbedder(model=model, **kwargs)
            else:
                raise ValueError(f"Unsupported embedding type: {embedding_type}")
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")
            
        return embedder