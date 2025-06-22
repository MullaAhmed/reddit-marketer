"""
Vector storage using ChromaDB.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config.settings import settings

logger = logging.getLogger(__name__)


class VectorStorage:
    """Vector storage manager using ChromaDB."""
    
    def __init__(self):
        """Initialize vector storage."""
        self.logger = logger
        self.chroma_dir = os.path.join(settings.DATA_DIR, "chromadb")
        Path(self.chroma_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collections = {}
    
    def _get_collection(self, org_id: str):
        """Get or create collection for organization."""
        collection_name = f"org_{org_id}_docs"
        
        if collection_name not in self._collections:
            try:
                collection = self.client.get_collection(collection_name)
            except ValueError:
                collection = self.client.create_collection(collection_name)
            
            self._collections[collection_name] = collection
        
        return self._collections[collection_name]
    
    def store_document_chunks(
        self,
        org_id: str,
        document_id: str,
        title: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> bool:
        """Store document chunks with embeddings."""
        try:
            collection = self._get_collection(org_id)
            
            # Prepare data for ChromaDB
            ids = []
            metadatas = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_metadata = {
                    **metadata,
                    "document_id": document_id,
                    "organization_id": org_id,
                    "title": title,
                    "chunk_index": i,
                    "chunk_count": len(chunks)
                }
                
                ids.append(chunk_id)
                metadatas.append(chunk_metadata)
            
            # Store in ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
            self.logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing document chunks: {str(e)}")
            return False
    
    def query_documents(
        self,
        org_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query documents using vector similarity."""
        try:
            collection = self._get_collection(org_id)
            
            # Format filters for ChromaDB
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    result = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "document_id": results["metadatas"][0][i].get("document_id", "unknown"),
                        "title": results["metadatas"][0][i].get("title", "Untitled")
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error querying documents: {str(e)}")
            return []
    
    def query_documents_bm25(
        self,
        org_id: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query documents using BM25 keyword search."""
        try:
            collection = self._get_collection(org_id)
            
            # Format filters for ChromaDB
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}
            
            # ChromaDB doesn't have built-in BM25, so we'll use basic text search
            # This is a simplified implementation
            all_results = collection.get(where=where_clause)
            
            # Simple keyword matching (in a real implementation, you'd use proper BM25)
            query_words = set(query_text.lower().split())
            scored_results = []
            
            if all_results["documents"]:
                for i, doc in enumerate(all_results["documents"]):
                    doc_words = set(doc.lower().split())
                    score = len(query_words.intersection(doc_words)) / len(query_words)
                    
                    if score > 0:
                        scored_results.append({
                            "content": doc,
                            "metadata": all_results["metadatas"][i],
                            "score": score,
                            "document_id": all_results["metadatas"][i].get("document_id", "unknown"),
                            "title": all_results["metadatas"][i].get("title", "Untitled")
                        })
            
            # Sort by score and return top_k
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in BM25 search: {str(e)}")
            return []
    
    def get_document_chunks_by_document_id(
        self,
        org_id: str,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document."""
        try:
            collection = self._get_collection(org_id)
            
            results = collection.get(
                where={"document_id": {"$eq": document_id}}
            )
            
            # Format and sort results by chunk_index
            chunks = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    chunk = {
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "document_id": document_id,
                        "chunk_index": results["metadatas"][i].get("chunk_index", 0)
                    }
                    chunks.append(chunk)
            
            # Sort by chunk_index
            chunks.sort(key=lambda x: x["chunk_index"])
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    def delete_document(self, org_id: str, document_id: str) -> bool:
        """Delete all chunks of a document."""
        try:
            collection = self._get_collection(org_id)
            
            # Get all chunk IDs for this document
            results = collection.get(
                where={"document_id": {"$eq": document_id}}
            )
            
            if results["ids"]:
                collection.delete(ids=results["ids"])
                self.logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False