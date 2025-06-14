"""
Unified document service combining ingestion and retrieval.
"""

import os
import time
from typing import List, Dict, Any, Tuple, Optional

from shared.base.service_base import BaseService
from shared.base.json_storage_mixin import JsonStorageMixin
from rag.models import Organization, Document, DocumentQuery, DocumentResponse, QueryResponse
from rag.core.pipelines.indexing_pipeline import IndexingPipeline
from rag.core.pipelines.retrieving_pipeline import RetrievalPipeline
from rag.core.managers.document_stores import DocumentStoreManager


class DocumentService(BaseService, JsonStorageMixin):
    """
    Unified service for document ingestion and retrieval operations.
    Combines functionality from DocumentIngestion and DocumentRetrieval.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the document service."""
        super().__init__("DocumentService", data_dir)
        
        # Initialize JSON files
        self._init_json_file("organizations.json", [])
        self._init_json_file("documents.json", [])
        
        # Cache for retrieval pipelines
        self._retrieval_pipelines = {}
    
    # ========================================
    # ORGANIZATION MANAGEMENT
    # ========================================
    
    def get_or_create_organization(self, org_id: str, org_name: str = None) -> Organization:
        """Get existing organization or create a new one."""
        # Check if organization exists
        org_data = self._find_item_in_json("organizations.json", org_id)
        
        if org_data:
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
    
    def _get_documents_for_org(self, org_id: str) -> List[Document]:
        """Get all documents for a specific organization."""
        docs_data = self._filter_items_in_json("documents.json", {"organization_id": org_id})
        return [Document(**doc_data) for doc_data in docs_data]
    
    def _update_organization(self, organization: Organization):
        """Update organization in JSON file."""
        self._update_item_in_json("organizations.json", organization.model_dump())
    
    # ========================================
    # DOCUMENT INGESTION
    # ========================================
    
    def ingest_documents(
        self, 
        documents: List[Dict[str, Any]], 
        org_id: str,
        org_name: str = None
    ) -> Tuple[bool, str, List[str]]:
        """
        Ingest a list of documents for an organization.
        
        Args:
            documents: List of dicts with 'title', 'content', and optional 'metadata'
            org_id: Organization ID
            org_name: Optional organization name (for auto-creation)
            
        Returns:
            Tuple of (success: bool, message: str, document_ids: List[str])
        """
        try:
            if not documents:
                return False, "No documents provided", []
            
            # Ensure organization exists
            organization = self.get_or_create_organization(org_id, org_name)
            
            # Set up indexing pipeline
            pipeline = self._setup_indexing_pipeline(org_id)
            
            # Load existing documents metadata
            docs_data = self._load_json("documents.json")
            
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
                
                # Check for duplicate documents
                if self._check_for_duplicate_documents(docs_data, doc):
                    self.logger.info(f"Document '{doc.title}' already exists for organization {org_id}, skipping...")
                    continue
                
                # Process text into documents
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
                    
                    # Add to documents list
                    docs_data.append(doc.model_dump())
                    new_documents.append(doc)
                    ingested_doc_ids.append(doc.id)
                else:
                    self.logger.error(f"Failed to ingest document '{doc.title}': {message}")
            
            # Save updated documents metadata
            self._save_json("documents.json", docs_data)
            
            # Update organization
            updated_org_documents = organization.documents + new_documents
            organization.documents = updated_org_documents
            organization.documents_count = len(updated_org_documents)
            self._update_organization(organization)
            
            if ingested_doc_ids:
                self.log_operation(
                    "DOCUMENT_INGESTION", 
                    True, 
                    f"Ingested {len(ingested_doc_ids)} documents ({total_chunks} chunks)",
                    org_id=org_id,
                    document_count=len(ingested_doc_ids),
                    chunk_count=total_chunks
                )
                return True, f"Successfully ingested {len(ingested_doc_ids)} documents ({total_chunks} chunks) for organization {org_id}", ingested_doc_ids
            else:
                return False, "No documents were successfully ingested", []
                
        except Exception as e:
            self.log_operation("DOCUMENT_INGESTION", False, str(e), org_id=org_id)
            return False, f"Error during ingestion: {str(e)}", []
    
    def _check_for_duplicate_documents(self, docs_data: List[Dict], new_doc: Document) -> bool:
        """Check if a document with the same title and org already exists."""
        for doc_data in docs_data:
            if (doc_data.get('title') == new_doc.title and 
                doc_data.get('organization_id') == new_doc.organization_id):
                return True
        return False
    
    def _setup_indexing_pipeline(self, org_id: str) -> IndexingPipeline:
        """Set up the indexing pipeline for the organization."""
        chromadb_dir = os.path.join(self.data_dir, "chromadb")
        persist_dir = os.path.join(chromadb_dir, org_id)
        
        document_store = DocumentStoreManager.initialize_document_store(
            document_store_provider="chroma",
            rag_id=org_id,
            persist_path=persist_dir,
            collection_name=f"org_{org_id}_docs"
        )
        
        return IndexingPipeline(
            document_store=document_store,
            chunk_size=8000,
            chunk_overlap=1000
        )
    
    # ========================================
    # DOCUMENT RETRIEVAL
    # ========================================
    
    def query_documents(self, query: DocumentQuery) -> QueryResponse:
        """
        Query documents based on the provided query.
        
        Args:
            query: DocumentQuery object with search parameters
            
        Returns:
            QueryResponse with results and metadata
        """
        start_time = time.time()
        
        try:
            # Validate organization
            if not query.organization_id:
                return QueryResponse(
                    query=query.query,
                    method=query.method,
                    total_results=0,
                    documents=[],
                    processing_time_ms=0
                )
            
            # Get retrieval pipeline for organization
            pipeline = self._get_retrieval_pipeline(query.organization_id)
            if not pipeline:
                return QueryResponse(
                    query=query.query,
                    method=query.method,
                    total_results=0,
                    documents=[],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Build filters
            filters = self._build_filters(query)
            
            # Perform retrieval
            if query.method == "semantic":
                raw_results = pipeline.semantic_retrieve(
                    query=query.query,
                    top_k=query.top_k,
                    filters=filters
                )
            elif query.method == "keyword":
                raw_results = pipeline.keyword_retrieve(
                    query=query.query,
                    top_k=query.top_k,
                    filters=filters
                )
            else:
                raise ValueError(f"Unsupported retrieval method: {query.method}")
            
            # Format results
            formatted_results = self._format_results(raw_results, query.organization_id)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            self.log_operation(
                "DOCUMENT_QUERY",
                True,
                f"Retrieved {len(formatted_results)} documents",
                org_id=query.organization_id,
                query=query.query,
                method=query.method,
                processing_time_ms=processing_time
            )
            
            return QueryResponse(
                query=query.query,
                method=query.method,
                total_results=len(formatted_results),
                documents=formatted_results,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.log_operation(
                "DOCUMENT_QUERY", 
                False, 
                str(e), 
                org_id=query.organization_id,
                processing_time_ms=processing_time
            )
            
            return QueryResponse(
                query=query.query,
                method=query.method,
                total_results=0,
                documents=[],
                processing_time_ms=processing_time
            )
    
    def _get_retrieval_pipeline(self, org_id: str) -> Optional[RetrievalPipeline]:
        """Get or create retrieval pipeline for organization."""
        if org_id in self._retrieval_pipelines:
            return self._retrieval_pipelines[org_id]
        
        # Check if organization exists
        organization = self._find_item_in_json("organizations.json", org_id)
        if not organization:
            return None
        
        try:
            # Get ChromaDB document store for this organization
            chromadb_dir = os.path.join(self.data_dir, "chromadb")
            persist_dir = os.path.join(chromadb_dir, org_id)
            
            # Check if the organization has any data
            if not os.path.exists(persist_dir):
                self.logger.warning(f"No data found for organization {org_id}")
                return None
            
            document_store = DocumentStoreManager.initialize_document_store(
                document_store_provider="chroma",
                rag_id=org_id,
                persist_path=persist_dir,
                collection_name=f"org_{org_id}_docs"
            )
            
            # Initialize retrieval pipeline
            pipeline = RetrievalPipeline(
                document_store=document_store,
                default_top_k=10
            )
            
            # Cache the pipeline
            self._retrieval_pipelines[org_id] = pipeline
            return pipeline
        
        except Exception as e:
            self.logger.error(f"Error creating retrieval pipeline for org {org_id}: {str(e)}")
            return None
    
    def _build_filters(self, query: DocumentQuery) -> Dict[str, Any]:
        """Build metadata filters from query in Haystack ChromaDB format."""
        conditions = []
        
        # Always filter by organization
        if query.organization_id:
            conditions.append({
                "field": "organization_id",
                "operator": "==",
                "value": query.organization_id
            })
        
        # Add custom filters
        if query.filters:
            for field, value in query.filters.items():
                if isinstance(value, dict):
                    # Handle range queries
                    for op, val in value.items():
                        operator_map = {
                            "$gte": ">=", "$lte": "<=", "$gt": ">", 
                            "$lt": "<", "$eq": "==", "$ne": "!="
                        }
                        if op in operator_map:
                            conditions.append({
                                "field": field,
                                "operator": operator_map[op],
                                "value": val
                            })
                else:
                    # Simple equality filter
                    conditions.append({
                        "field": field,
                        "operator": "==",
                        "value": value
                    })
        
        # Return appropriate filter format
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {
                "operator": "AND",
                "conditions": conditions
            }
    
    def _format_results(self, raw_results: List[Any], org_id: str) -> List[DocumentResponse]:
        """Format raw retrieval results into DocumentResponse objects."""
        formatted_results = []
        
        for result in raw_results:
            try:
                # Handle Haystack Document objects
                if hasattr(result, 'meta') and hasattr(result, 'content'):
                    metadata = result.meta if result.meta else {}
                    content = result.content if result.content else ''
                    score = getattr(result, 'score', 0.0)
                    
                    response = DocumentResponse(
                        document_id=metadata.get('document_id', getattr(result, 'id', 'unknown')),
                        title=metadata.get('title', 'Untitled'),
                        content=content,
                        score=float(score),
                        organization_id=metadata.get('organization_id', org_id),
                        metadata=metadata
                    )
                    formatted_results.append(response)
                    
                # Handle dictionary format
                elif isinstance(result, dict):
                    metadata = result.get('meta', {})
                    
                    response = DocumentResponse(
                        document_id=metadata.get('document_id', 'unknown'),
                        title=metadata.get('title', 'Untitled'),
                        content=result.get('content', ''),
                        score=result.get('score', 0.0),
                        organization_id=metadata.get('organization_id', org_id),
                        metadata=metadata
                    )
                    formatted_results.append(response)
                    
            except Exception as e:
                self.logger.error(f"Error formatting result: {str(e)}")
                continue
        
        return formatted_results