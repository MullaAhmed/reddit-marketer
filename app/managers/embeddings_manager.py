"""
Embeddings management for vector storage.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

from app.clients.storage_client import VectorStorageClient

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Manager for embeddings operations and vector storage management.
    """
    
    def __init__(self, vector_storage_client: VectorStorageClient):
        """Initialize embeddings manager."""
        self.storage_client = vector_storage_client
        self.logger = logger
    
    # ========================================
    # EMBEDDING OPERATIONS
    # ========================================
    
    def generate_text_embedding(self, text: str, model: str = "text-embedding-3-large") -> Optional[List[float]]:
        """Generate embedding for a single text."""
        try:
            embedder = self.storage_client.get_text_embedder(model)
            result = embedder.run(text)
            return result["embedding"]
        except Exception as e:
            self.logger.error(f"Error generating text embedding: {str(e)}")
            return None
    
    def generate_batch_embeddings(
        self, 
        texts: List[str], 
        model: str = "text-embedding-3-large"
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.generate_text_embedding(text, model)
            embeddings.append(embedding)
        return embeddings
    
    def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def find_similar_texts(
        self, 
        query_text: str, 
        candidate_texts: List[str],
        threshold: float = 0.7,
        model: str = "text-embedding-3-large"
    ) -> List[Dict[str, Any]]:
        """Find texts similar to query text."""
        try:
            # Generate query embedding
            query_embedding = self.generate_text_embedding(query_text, model)
            if not query_embedding:
                return []
            
            # Generate candidate embeddings
            candidate_embeddings = self.generate_batch_embeddings(candidate_texts, model)
            
            # Calculate similarities
            similar_texts = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                if candidate_embedding:
                    similarity = self.calculate_similarity(query_embedding, candidate_embedding)
                    if similarity >= threshold:
                        similar_texts.append({
                            "text": candidate_texts[i],
                            "similarity": similarity,
                            "index": i
                        })
            
            # Sort by similarity
            similar_texts.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_texts
            
        except Exception as e:
            self.logger.error(f"Error finding similar texts: {str(e)}")
            return []
    
    # ========================================
    # VECTOR STORAGE MANAGEMENT
    # ========================================
    
    def get_storage_stats(self, org_id: str) -> Dict[str, Any]:
        """Get vector storage statistics for organization."""
        try:
            return self.storage_client.get_storage_stats(org_id)
        except Exception as e:
            self.logger.error(f"Error getting storage stats for org {org_id}: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding format and values."""
        try:
            if not isinstance(embedding, list):
                return False
            
            if len(embedding) == 0:
                return False
            
            # Check if all values are numbers
            for value in embedding:
                if not isinstance(value, (int, float)):
                    return False
                
                # Check for NaN or infinity
                if np.isnan(value) or np.isinf(value):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to unit length."""
        try:
            vec = np.array(embedding)
            norm = np.linalg.norm(vec)
            
            if norm == 0:
                return embedding
            
            normalized = vec / norm
            return normalized.tolist()
            
        except Exception as e:
            self.logger.error(f"Error normalizing embedding: {str(e)}")
            return embedding
    
    def get_embedding_dimensions(self, model: str = "text-embedding-3-large") -> int:
        """Get the dimensions of embeddings for a specific model."""
        # Known dimensions for common models
        model_dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536
        }
        
        return model_dimensions.get(model, 1536)  # Default to 1536