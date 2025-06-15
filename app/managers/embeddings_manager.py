"""
Embeddings management for vector app.storage.
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
    
    def __init__(self, data_dir: str = "data"):
        """Initialize embeddings manager."""
        self.data_dir = data_dir
        self.storage_client = VectorStorageClient(data_dir)
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
    
    def optimize_storage(self, org_id: str) -> Dict[str, Any]:
        """Optimize vector storage for organization."""
        try:
            # This would implement storage optimization strategies
            # For now, just return current stats
            stats = self.get_storage_stats(org_id)
            
            return {
                "organization_id": org_id,
                "optimization_performed": False,
                "message": "Storage optimization not yet implemented",
                "current_stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing storage for org {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def backup_embeddings(self, org_id: str, backup_path: str = None) -> bool:
        """Backup embeddings for organization."""
        try:
            # This would implement embedding backup functionality
            self.logger.info(f"Backup embeddings for org {org_id} (not implemented)")
            return True
        except Exception as e:
            self.logger.error(f"Error backing up embeddings for org {org_id}: {str(e)}")
            return False
    
    def restore_embeddings(self, org_id: str, backup_path: str) -> bool:
        """Restore embeddings for organization."""
        try:
            # This would implement embedding restore functionality
            self.logger.info(f"Restore embeddings for org {org_id} from {backup_path} (not implemented)")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring embeddings for org {org_id}: {str(e)}")
            return False
    
    # ========================================
    # EMBEDDING ANALYSIS
    # ========================================
    
    def analyze_embedding_distribution(self, org_id: str) -> Dict[str, Any]:
        """Analyze the distribution of embeddings for an organization."""
        try:
            # This would analyze embedding clusters, outliers, etc.
            stats = self.get_storage_stats(org_id)
            
            return {
                "organization_id": org_id,
                "analysis_performed": False,
                "message": "Embedding analysis not yet implemented",
                "storage_stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing embeddings for org {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def find_embedding_clusters(
        self, 
        org_id: str, 
        num_clusters: int = 5
    ) -> Dict[str, Any]:
        """Find clusters in organization's embeddings."""
        try:
            # This would implement clustering analysis
            return {
                "organization_id": org_id,
                "num_clusters": num_clusters,
                "clustering_performed": False,
                "message": "Embedding clustering not yet implemented"
            }
            
        except Exception as e:
            self.logger.error(f"Error clustering embeddings for org {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def detect_embedding_outliers(self, org_id: str) -> Dict[str, Any]:
        """Detect outlier embeddings for an organization."""
        try:
            # This would implement outlier detection
            return {
                "organization_id": org_id,
                "outlier_detection_performed": False,
                "message": "Outlier detection not yet implemented"
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting outliers for org {org_id}: {str(e)}")
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