from typing import List, Dict, Any, Optional
from haystack import Document


class DocumentManager:
    """
    Pure document processing manager.
    Converts various input types (PDF, URL, text) into Haystack Document objects.
    """
    
    def __init__(self, default_chunk_size: int = 1000, default_chunk_overlap: int = 200):
        """
        Initialize DocumentManager with default chunking settings.
        
        Args:
            default_chunk_size: Default size of text chunks to create
            default_chunk_overlap: Default overlap between consecutive chunks
        """
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap

    # ========================================
    # LOW-LEVEL DOCUMENT OPERATIONS
    # ========================================
    
    def process_text(
        self,
        text: str,
        title: str = "",
        rag_id: str = "",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process raw text into chunked Document objects.
        
        Args:
            text: Raw text to process
            title: Title for the document
            rag_id: RAG identifier to link related documents
            chunk_size: Size of text chunks (uses default if None)
            chunk_overlap: Overlap between chunks (uses default if None)
            metadata: Additional metadata to include
            
        Returns:
            List of Document objects (one per chunk)
        """
        # Prepare base metadata
        base_metadata = {
            "source_type": "text",
            "title": title,
            "rag_id": rag_id
        }
        
        # Add custom metadata if provided
        if metadata:
            base_metadata.update(metadata)
        
        # Create chunked documents
        return self.chunk_text(
            text=text,
            metadata=base_metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Dict[str, Any], 
        chunk_size: Optional[int] = None, 
        chunk_overlap: Optional[int] = None
    ) -> List[Document]:
        """
        Split text into overlapping chunks and create Document objects.
        
        Args:
            text: Text to split
            metadata: Base metadata to include in each document
            chunk_size: Size of text chunks (uses default if None)
            chunk_overlap: Overlap between chunks (uses default if None)
            
        Returns:
            List of Document objects (one per chunk)
        """
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        
        # Split text into chunks with overlap
        words = text.split()
        chunks = []
        
        if not words:
            # Return single empty document if no text
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = 0
            return [Document(content="", meta=chunk_metadata)]
        
        # Calculate words per chunk (approximate)
        # Assuming average word length of 5 characters + 1 space
        words_per_chunk = max(1, chunk_size // 6)
        overlap_words = max(0, chunk_overlap // 6)
        
        i = 0
        while i < len(words):
            # Get the chunk of words
            end_idx = min(i + words_per_chunk, len(words))
            chunk_words = words[i:end_idx]
            chunk_text = " ".join(chunk_words)
            
            # Add chunk-specific metadata
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunk_metadata["chunk_start_word"] = i
            chunk_metadata["chunk_end_word"] = end_idx - 1
            
            # Create Document
            chunks.append(Document(content=chunk_text, meta=chunk_metadata))
            
            # Move to next chunk position with overlap
            next_i = i + words_per_chunk - overlap_words
            
            # Ensure we make progress (avoid infinite loop)
            if next_i <= i:
                i = end_idx
            else:
                i = next_i
        
        return chunks
 
    # ========================================
    # LOW-LEVEL DOCUMENT OPERATIONS
    # ========================================

    def update_document_metadata(
        self,
        document: Document,
        new_metadata: Dict[str, Any]
    ) -> Document:
        """
        Update document metadata while preserving existing metadata.
        
        Args:
            document: Original document
            new_metadata: New metadata to merge
            
        Returns:
            Document with updated metadata
        """
        updated_meta = document.meta.copy()
        updated_meta.update(new_metadata)
        
        return Document(content=document.content, meta=updated_meta)
