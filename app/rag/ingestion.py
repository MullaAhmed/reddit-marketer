import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

from rag.models import Organization, Document
from rag.core.pipelines.indexing_pipeline import IndexingPipeline
from rag.core.managers.document_stores import DocumentStoreManager


class DocumentIngestion:
    """Service for ingesting documents and managing JSON metadata."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the ingestion service."""
        self.data_dir = data_dir
        self.json_dir = os.path.join(data_dir, "json")
        self.chromadb_dir = os.path.join(data_dir, "chromadb")
        
        # Ensure directories exist
        Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chromadb_dir).mkdir(parents=True, exist_ok=True)
        
        # JSON file paths
        self.orgs_file = os.path.join(self.json_dir, "organizations.json")
        self.docs_file = os.path.join(self.json_dir, "documents.json")
        
        # Initialize JSON files if they don't exist
        self._init_json_files()
    
    def _init_json_files(self):
        """Create empty JSON files if they don't exist."""
        for file_path in [self.orgs_file, self.docs_file]:
            if not Path(file_path).exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _load_json(self, file_path: str) -> List[Dict]:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, file_path: str, data: List[Dict]):
        """Save data to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _get_documents_for_org(self, org_id: str) -> List[Document]:
        """Get all documents for a specific organization."""
        docs_data = self._load_json(self.docs_file)
        org_documents = []
        
        for doc_data in docs_data:
            if doc_data.get('organization_id') == org_id:
                org_documents.append(Document(**doc_data))
        
        return org_documents
    
    def _get_or_create_organization(self, org_id: str, org_name: str = None) -> Organization:
        """Get existing organization or create a new one."""
        orgs_data = self._load_json(self.orgs_file)
        
        # Check if organization exists
        for org_data in orgs_data:
            if org_data['id'] == org_id:
                # Load existing documents for this org
                existing_docs = self._get_documents_for_org(org_id)
                org_data['documents'] = existing_docs
                org_data['documents_count'] = len(existing_docs)
                return Organization(**org_data)
        
        # Create new organization
        new_org = Organization(
            id=org_id,
            name=org_name or f"Organization {org_id}",
            description=f"Auto-created organization for {org_id}"
        )
        
        return new_org
    
    def _update_organization_in_json(self, organization: Organization):
        """Update organization in JSON file."""
        orgs_data = self._load_json(self.orgs_file)
        
        # Find and update existing org, or add new one
        updated = False
        for i, org_data in enumerate(orgs_data):
            if org_data['id'] == organization.id:
                orgs_data[i] = organization.model_dump()
                updated = True
                break
        
        if not updated:
            orgs_data.append(organization.model_dump())
        
        self._save_json(self.orgs_file, orgs_data)
    
    def _check_for_duplicate_documents(self, docs_data: List[Dict], new_doc: Document) -> bool:
        """Check if a document with the same title and org already exists."""
        for doc_data in docs_data:
            if (doc_data.get('title') == new_doc.title and 
                doc_data.get('organization_id') == new_doc.organization_id):
                return True
        return False
    
    def _setup_indexing_pipeline(self, org_id: str) -> IndexingPipeline:
        """Set up the indexing pipeline for the organization."""
        # Get ChromaDB document store for this organization
        persist_dir = os.path.join(self.chromadb_dir, org_id)
        
        document_store = DocumentStoreManager.initialize_document_store(
            document_store_provider="chroma",
            rag_id=org_id,
            persist_path=persist_dir,
            collection_name=f"org_{org_id}_docs"
        )
        
        # Initialize indexing pipeline
        pipeline = IndexingPipeline(
            document_store=document_store,
            chunk_size=8000,
            chunk_overlap=1000
        )
        
        return pipeline
    
    def ingest_documents(
        self, 
        documents: List[Dict[str, Any]], 
        org_id: str,
        org_name: str = None
    ) -> Tuple[bool, str, List[str]]:
        # """
        # Ingest a list of documents for an organization.
        
        # Args:
        #     documents: List of dicts with 'title', 'content', and optional 'metadata'
        #     org_id: Organization ID
        #     org_name: Optional organization name (for auto-creation)
            
        # Returns:
        #     Tuple of (success: bool, message: str, document_ids: List[str])
        # """
        # try:
            if not documents:
                return False, "No documents provided", []
            
            # Ensure organization exists
            organization = self._get_or_create_organization(org_id, org_name)
   
            # Set up indexing pipeline
            pipeline = self._setup_indexing_pipeline(org_id)
            
            # Load existing documents metadata
            docs_data = self._load_json(self.docs_file)
            
            # Process each document
            ingested_doc_ids = []
            new_documents = []
            total_chunks = 0
            
            for doc_dict in documents:
                # Validate required fields
                if 'title' not in doc_dict or 'content' not in doc_dict:
                    continue
                
                # Create document metadata
                doc = Document(
                    title=doc_dict['title'],
                    organization_id=org_id,
                    rag_id=f"{org_id}_{doc_dict['title']}",
                    metadata=doc_dict.get('metadata', {}),
                    content_length=len(doc_dict['content'])
                )
                
                # Check for duplicate documents (optional - you can remove this if you want to allow duplicates)
                if self._check_for_duplicate_documents(docs_data, doc):
                    print(f"Document '{doc.title}' already exists for organization {org_id}, skipping...")
                    continue
                
                # Process text into documents using document manager
                processed_docs = pipeline.document_manager.process_text(
                    text=doc_dict['content'],
                    title=doc_dict['title'],
                    rag_id=doc.rag_id,
                    chunk_size=doc_dict.get('chunk_size'),
                    chunk_overlap=doc_dict.get('chunk_overlap'),
                    metadata={
                        'document_id': doc.id,
                        'organization_id': org_id,
                        'title': doc.title,
                        **doc.metadata
                    }
                )
                
                # Index the processed documents
                success, message = pipeline.index_documents(processed_docs)
                chunk_count = len(processed_docs)
                
                if success:
                    # Update document with chunk count
                    doc.chunk_count = chunk_count
                    total_chunks += chunk_count
                    
                    # Add to documents list for JSON update
                    docs_data.append(doc.model_dump())
                    new_documents.append(doc)
                    ingested_doc_ids.append(doc.id)
                else:
                    print(f"Failed to ingest document '{doc.title}': {message}")
            
            # Save updated documents metadata to JSON
            self._save_json(self.docs_file, docs_data)
            
            # Update organization with all documents (existing + new)
            updated_org_documents = organization.documents + new_documents
            organization.documents = updated_org_documents
            organization.documents_count = len(updated_org_documents)
            
            # Update organization in JSON
            self._update_organization_in_json(organization)
            
            if ingested_doc_ids:
                return True, f"Successfully ingested {len(ingested_doc_ids)} documents ({total_chunks} chunks) for organization {org_id}", ingested_doc_ids
            else:
                return False, "No documents were successfully ingested", []
                
        # except Exception as e:
        #     return False, f"Error during ingestion: {str(e)}", []


# Example usage
if __name__ == "__main__":
    # Example documents
    documents = [
        {
            "title": "Company Policy Manual",
            "content": "This is the company policy manual with all our standard operating procedures...",
            "metadata": {
                "category": "policy",
                "department": "HR",
                "version": "2024.1"
            }
        },
        {
            "title": "Technical Documentation",
            "content": "This document contains technical specifications and implementation details...",
            "metadata": {
                "category": "technical",
                "department": "Engineering",
                "project": "ProjectX"
            }
        }
    ]
    
    data_dir = "data"
    org_id = "1"
    org_name = "Test"
    
    # Ingest documents
    ingestion_service = DocumentIngestion(data_dir=data_dir)
    success, message, doc_ids = ingestion_service.ingest_documents(documents, org_id, org_name)
    
    result = {
        "success": success,
        "message": message,
        "document_ids": doc_ids,
        "count": len(doc_ids),
        "organization_id": org_id
    }    
    
    print("Ingestion Result:")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Document IDs: {result['document_ids']}")
    print(f"Count: {result['count']}")
    
    # Show JSON file contents for verification
    print("\n=== JSON Files Content ===")
    
    # Show organizations
    print("\nOrganizations JSON:")
    try:
        with open(os.path.join(data_dir, "json", "organizations.json"), 'r') as f:
            orgs = json.load(f)
            for org in orgs:
                print(f"  Org: {org['name']} (ID: {org['id']}) - {org['documents_count']} documents")
    except Exception as e:
        print(f"  Error reading organizations.json: {e}")
    
    # Show documents  
    print("\nDocuments JSON:")
    try:
        with open(os.path.join(data_dir, "json", "documents.json"), 'r') as f:
            docs = json.load(f)
            print(f"  Total documents: {len(docs)}")
            for doc in docs:
                print(f"    - {doc['title']} (ID: {doc['id'][:8]}...) - {doc['chunk_count']} chunks")
    except Exception as e:
        print(f"  Error reading documents.json: {e}")