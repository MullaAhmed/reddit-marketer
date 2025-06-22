"""
Embedding client for text embeddings.
"""

import logging
from typing import List

from openai import AsyncOpenAI

from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for generating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding client."""
        self.logger = logger
        self._openai_client = None
    
    @property
    def openai_client(self) -> AsyncOpenAI:
        """Get OpenAI client (lazy loading)."""
        if not self._openai_client:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client
    
    async def generate_text_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-large"
    ) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = await self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error generating text embedding: {str(e)}")
            return []
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-large"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            response = await self.openai_client.embeddings.create(
                model=model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            self.logger.error(f"Error generating batch embeddings: {str(e)}")
            return []