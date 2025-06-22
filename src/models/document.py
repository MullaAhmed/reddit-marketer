"""
Document data models.
"""

from typing import Dict, Any
from pydantic import BaseModel


class Document(BaseModel):
    """Document model for tracking document metadata."""
    
    id: str
    title: str
    organization_id: str
    metadata: Dict[str, Any] = {}
    content_length: int = 0
    chunk_count: int = 0
    created_at: float