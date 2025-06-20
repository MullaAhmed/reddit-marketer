"""
Document storage manager.
"""

import logging
from typing import List, Dict, Any, Optional

from app.storage.json_storage import JsonStorage

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    Manager for document metadata storage and retrieval.
    """
    
    def __init__(self, json_storage: JsonStorage):
        """Initialize document manager."""
        self.json_storage = json_storage
        self.logger = logger
        
        # Initialize JSON files
        self.json_storage.init_file("organizations.json", [])
        self.json_storage.init_file("documents.json", [])
    
    # ========================================
    # ORGANIZATION OPERATIONS
    # ========================================
    
    def save_organization(self, org_data: Dict[str, Any]) -> bool:
        """Save organization data."""
        try:
            return self.json_storage.update_item("organizations.json", org_data)
        except Exception as e:
            self.logger.error(f"Error saving organization: {str(e)}")
            return False
    
    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID."""
        try:
            return self.json_storage.find_item("organizations.json", org_id)
        except Exception as e:
            self.logger.error(f"Error getting organization {org_id}: {str(e)}")
            return None
    
    def list_organizations(self) -> List[Dict[str, Any]]:
        """List all organizations."""
        try:
            return self.json_storage.load_data("organizations.json")
        except Exception as e:
            self.logger.error(f"Error listing organizations: {str(e)}")
            return []
    
    def delete_organization(self, org_id: str) -> bool:
        """Delete organization and all its documents."""
        try:
            # Delete all documents for this organization
            documents = self.get_documents_by_organization(org_id)
            for doc in documents:
                self.delete_document(doc["id"])
            
            # Delete organization
            return self.json_storage.delete_item("organizations.json", org_id)
        except Exception as e:
            self.logger.error(f"Error deleting organization {org_id}: {str(e)}")
            return False
    
    # ========================================
    # DOCUMENT OPERATIONS
    # ========================================
    
    def save_document(self, doc_data: Dict[str, Any]) -> bool:
        """Save document data."""
        try:
            return self.json_storage.update_item("documents.json", doc_data)
        except Exception as e:
            self.logger.error(f"Error saving document: {str(e)}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        try:
            return self.json_storage.find_item("documents.json", doc_id)
        except Exception as e:
            self.logger.error(f"Error getting document {doc_id}: {str(e)}")
            return None
    
    def get_documents_by_organization(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all documents for an organization."""
        try:
            return self.json_storage.filter_items(
                "documents.json", 
                {"organization_id": org_id}
            )
        except Exception as e:
            self.logger.error(f"Error getting documents for org {org_id}: {str(e)}")
            return []
    
    def list_documents(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """List documents with optional filters."""
        try:
            if filters:
                return self.json_storage.filter_items("documents.json", filters)
            else:
                return self.json_storage.load_data("documents.json")
        except Exception as e:
            self.logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document."""
        try:
            return self.json_storage.delete_item("documents.json", doc_id)
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False
    
    def update_document_stats(self, doc_id: str, stats: Dict[str, Any]) -> bool:
        """Update document statistics."""
        try:
            doc_data = self.get_document(doc_id)
            if doc_data:
                doc_data.update(stats)
                return self.save_document(doc_data)
            return False
        except Exception as e:
            self.logger.error(f"Error updating document stats for {doc_id}: {str(e)}")
            return False
    
    # ========================================
    # SEARCH AND FILTERING
    # ========================================
    
    def search_documents(
        self, 
        query: str, 
        org_id: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search documents by title or metadata."""
        try:
            # Get documents for organization if specified
            if org_id:
                documents = self.get_documents_by_organization(org_id)
            else:
                documents = self.list_documents()
            
            # Simple text search in title and metadata
            query_lower = query.lower()
            matching_docs = []
            
            for doc in documents:
                # Search in title
                if query_lower in doc.get("title", "").lower():
                    matching_docs.append(doc)
                    continue
                
                # Search in metadata
                metadata = doc.get("metadata", {})
                for key, value in metadata.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        matching_docs.append(doc)
                        break
            
            return matching_docs
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_documents_by_title(self, title: str, org_id: str = None) -> List[Dict[str, Any]]:
        """Get documents by exact title match."""
        try:
            filters = {"title": title}
            if org_id:
                filters["organization_id"] = org_id
            
            return self.json_storage.filter_items("documents.json", filters)
        except Exception as e:
            self.logger.error(f"Error getting documents by title '{title}': {str(e)}")
            return []