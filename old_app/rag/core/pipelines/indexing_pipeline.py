from typing import List, Tuple, Optional, Dict, Union, Any

from haystack import Pipeline, Document
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.components.embedders import (
    OpenAIDocumentEmbedder, 
    SentenceTransformersDocumentEmbedder
)
from rag.core.managers.document_stores import DocumentStoreManager
from rag.core.managers.embedders import EmbedderManager
from rag.core.managers.documents import DocumentManager


class IndexingPipeline:
    """
    Indexing pipeline that handles both low-level indexing operations
    and high-level document ingestion orchestration.
    """
   
    def __init__(
        self,
        embedder_instance: Optional[Union[OpenAIDocumentEmbedder, SentenceTransformersDocumentEmbedder]] = None,
        document_store: Optional[Union[InMemoryDocumentStore, ChromaDocumentStore]] = None,
        document_manager: Optional[DocumentManager] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize IndexingPipeline with all required components.
        
        Args:
            embedder_instance: Embedder to use in the pipeline
            document_store: Document store to write to
            document_manager: DocumentManager instance for processing
            chunk_size: Default chunk size for document processing
            chunk_overlap: Default chunk overlap for document processing
        """
        # Initialize document store and embedder
        self.document_store = document_store or DocumentStoreManager.initialize_document_store()
        self.embedder_instance = embedder_instance or EmbedderManager.initialize_embedder(embedding_type="document")
        
        # Initialize document manager
        self.document_manager = document_manager or DocumentManager(
            default_chunk_size=chunk_size,
            default_chunk_overlap=chunk_overlap
        )
        
        # Initialize the indexing pipeline
        self.pipeline = self._build_pipeline()
    
    def _build_pipeline(self) -> Pipeline:
        """
        Build the internal Haystack pipeline for indexing.
        
        Returns:
            Configured Haystack Pipeline
        """
        pipeline = Pipeline()
        
        # Add embedder component
        pipeline.add_component(
            instance=self.embedder_instance, 
            name="doc_embedder"
        )
        
        # Add document writer component
        pipeline.add_component(
            instance=DocumentWriter(document_store=self.document_store), 
            name="doc_writer"
        )
        
        # Connect components
        pipeline.connect("doc_embedder.documents", "doc_writer.documents")
        
        return pipeline

    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_document_store_info(self) -> Dict[str, Any]:
        """
        Get information about the current document store.
        
        Returns:
            Dictionary with document store information
        """
        try:
            store_type = type(self.document_store).__name__
            
            # Try to get document count
            doc_count = 0
            if hasattr(self.document_store, 'count_documents'):
                doc_count = self.document_store.count_documents()
            
            return {
                "store_type": store_type,
                "document_count": doc_count,
                "embedder_type": type(self.embedder_instance).__name__
            }
        except Exception as e:
            return {
                "store_type": "unknown",
                "document_count": 0,
                "error": str(e)
            }
    
    def update_chunk_settings(self, chunk_size: int, chunk_overlap: int) -> None:
        """
        Update the default chunk settings for the document manager.
        
        Args:
            chunk_size: New default chunk size
            chunk_overlap: New default chunk overlap
        """
        self.document_manager.default_chunk_size = chunk_size
        self.document_manager.default_chunk_overlap = chunk_overlap
   
    # ========================================
    # LOW-LEVEL INDEXING OPERATIONS
    # ========================================
    
    def index_documents(self, documents: List[Document]) -> Tuple[bool, str]:
        """
        Index a list of documents using the pipeline.
        
        Args:
            documents: List of Document objects to index
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not documents:
            return False, "No documents provided to index"
        
        try:
            # Run the indexing pipeline
            result = self.pipeline.run({"doc_embedder": {"documents": documents}})
            
            # Check if indexing was successful
            if result and "doc_writer" in result:
                indexed_count = result["doc_writer"]["documents_written"]
                return True, f"Successfully indexed {indexed_count} documents"
            else:
                return True, f"Successfully processed {len(documents)} documents"
                
        except Exception as e:
            return False, f"Failed to index documents: {str(e)}"
    
    def index_document(self, document: Document) -> Tuple[bool, str]:
        """
        Index a single document using the pipeline.
        
        Args:
            document: Document object to index
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        return self.index_documents([document])
    
    # ========================================
    # LOW-LEVEL UPDATE INGESTION OPERATIONS
    # ========================================

    def update_document_by_filter(
        self, 
        filters: Dict[str, Any], 
        new_content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Tuple[bool, str, int]:
        """
        Update documents matching the given filters.
        
        Args:
            filters: Dictionary of filters to identify documents to update
            new_content: New content for the document
            title: New title (optional)
            metadata: Additional metadata to merge
            chunk_size: Chunk size for re-processing
            chunk_overlap: Chunk overlap for re-processing
            
        Returns:
            Tuple of (success: bool, message: str, new_document_count: int)
        """
        try:
            # Find existing documents
            existing_docs = self.document_store.filter_documents(filters=filters)
            
            if not existing_docs:
                return False, f"No documents found matching filters: {filters}", 0
            
            # Extract metadata from first matching document for continuity
            base_metadata = existing_docs[0].meta.copy()
            
            # Update with new metadata if provided
            if metadata:
                base_metadata.update(metadata)
            
            # Update title if provided
            if title:
                base_metadata["title"] = title
            
            # Delete existing documents
            deleted_count = self.document_store.delete_documents(
                document_ids=[doc.id for doc in existing_docs]
            )
            
            # Process new content into documents
            if base_metadata.get("source_type") == "text" or not base_metadata.get("source_type"):
                new_documents = self.document_manager.process_text(
                    text=new_content,
                    title=base_metadata.get("title", ""),
                    rag_id=base_metadata.get("rag_id", ""),
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata={k: v for k, v in base_metadata.items() 
                            if k not in ["chunk_index", "chunk_start_word", "chunk_end_word"]}
                )
            else:
                # For other source types, create single document and chunk if needed
                clean_metadata = {k: v for k, v in base_metadata.items() 
                                if k not in ["chunk_index", "chunk_start_word", "chunk_end_word"]}
                new_documents = self.document_manager.chunk_text(
                    text=new_content,
                    metadata=clean_metadata,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            
            # Index new documents
            success, message = self.index_documents(new_documents)
            
            if success:
                return True, f"Successfully updated document. Replaced {deleted_count} chunks with {len(new_documents)} new chunks", len(new_documents)
            else:
                return False, f"Documents deleted but re-indexing failed: {message}", len(new_documents)
                
        except Exception as e:
            return False, f"Error updating documents: {str(e)}", 0

    # =======================================
    # HIGH-LEVEL INGESTION OPERATIONS
    # ========================================
    
    async def ingest_text(
        self,
        text: str,
        title: str,
        rag_id: str = "",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, int]:
        """
        Complete text ingestion: process text and index documents.
        
        Args:
            text: Raw text to process
            title: Title for the document
            rag_id: RAG identifier to link related documents
            chunk_size: Size of text chunks (uses default if None)
            chunk_overlap: Overlap between chunks (uses default if None)
            metadata: Additional metadata to include
            
        Returns:
            Tuple of (success: bool, message: str, document_count: int)
        """
        try:
            if not text.strip():
                return False, "No text content provided", 0
            
            # Process text into documents
            documents = self.document_manager.process_text(
                text=text,
                title=title,
                rag_id=rag_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata
            )
            
            if not documents:
                return False, "Failed to process text", 0
            
            # Index the documents
            success, message = self.index_documents(documents)
            
            if success:
                return True, f"Successfully processed and indexed text into {len(documents)} chunks", len(documents)
            else:
                return False, f"Text processed but indexing failed: {message}", len(documents)
                
        except Exception as e:
            return False, f"Error processing text: {str(e)}", 0