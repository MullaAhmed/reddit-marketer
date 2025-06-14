import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from rag.models import Organization, Document, DocumentQuery, DocumentResponse, QueryResponse
from rag.core.pipelines.retrieving_pipeline import RetrievalPipeline
from rag.core.managers.document_stores import DocumentStoreManager


class DocumentRetrieval:
    """Service for retrieving documents from multi-organization RAG system."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the retrieval service."""
        self.data_dir = data_dir
        self.json_dir = os.path.join(data_dir, "json")
        self.chromadb_dir = os.path.join(data_dir, "chromadb")
        
        # JSON file paths
        self.orgs_file = os.path.join(self.json_dir, "organizations.json")
        self.docs_file = os.path.join(self.json_dir, "documents.json")
        
        # Cache for retrieval pipelines (one per organization)
        self._retrieval_pipelines = {}
    
    def _load_json(self, file_path: str) -> List[Dict]:
        """Load data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _get_organization(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        orgs_data = self._load_json(self.orgs_file)
        
        for org_data in orgs_data:
            if org_data['id'] == org_id:
                return Organization(**org_data)
        return None
    
    def _get_retrieval_pipeline(self, org_id: str) -> Optional[RetrievalPipeline]:
        """Get or create retrieval pipeline for organization."""
        if org_id in self._retrieval_pipelines:
            return self._retrieval_pipelines[org_id]
        
        # Check if organization exists
        organization = self._get_organization(org_id)
        if not organization:
            return None
        
        try:
            # Get ChromaDB document store for this organization
            persist_dir = os.path.join(self.chromadb_dir, org_id)
            
            # Check if the organization has any data
            if not Path(persist_dir).exists():
                print(f"No data found for organization {org_id}")
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
            print(f"Error creating retrieval pipeline for org {org_id}: {str(e)}")
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
                    # Handle range queries like {"$gte": "2024-01-01", "$lte": "2024-12-31"}
                    for op, val in value.items():
                        if op == "$gte":
                            conditions.append({
                                "field": field,
                                "operator": ">=",
                                "value": val
                            })
                        elif op == "$lte":
                            conditions.append({
                                "field": field,
                                "operator": "<=", 
                                "value": val
                            })
                        elif op == "$gt":
                            conditions.append({
                                "field": field,
                                "operator": ">",
                                "value": val
                            })
                        elif op == "$lt":
                            conditions.append({
                                "field": field,
                                "operator": "<",
                                "value": val
                            })
                        elif op == "$eq":
                            conditions.append({
                                "field": field,
                                "operator": "==",
                                "value": val
                            })
                        elif op == "$ne":
                            conditions.append({
                                "field": field,
                                "operator": "!=",
                                "value": val
                            })
                else:
                    # Simple equality filter
                    conditions.append({
                        "field": field,
                        "operator": "==",
                        "value": value
                    })
        
        # Return None if no conditions, single condition, or AND combined conditions
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
                    # Extract metadata from Document object
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
                    
                # Handle dictionary format (fallback for other implementations)
                elif isinstance(result, dict):
                    # Extract metadata from dictionary
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
                    
                else:
                    print(f"Unexpected result format: {type(result)}")
                    continue
                    
            except Exception as e:
                print(f"Error formatting result: {str(e)}")
                print(f"Result type: {type(result)}")
                print(f"Result: {result}")
                continue
        
        return formatted_results

    def query_documents(self, query: DocumentQuery) -> QueryResponse:
        """
        Query documents based on the provided query.
        
        Args:
            query: DocumentQuery object with search parameters
            
        Returns:
            QueryResponse with results and metadata
        """
        start_time = time.time()
        
        # try:
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
        
        return QueryResponse(
            query=query.query,
            method=query.method,
            total_results=len(formatted_results),
            documents=formatted_results,
            processing_time_ms=processing_time
        )
            
        # except Exception as e:
        #     processing_time = (time.time() - start_time) * 1000
        #     print(f"Error during document retrieval: {str(e)}")
            
        #     return QueryResponse(
        #         query=query.query,
        #         method=query.method,
        #         total_results=0,
        #         documents=[],
        #         processing_time_ms=processing_time
        #     )
    

# Example usage
if __name__ == "__main__":
    # Simple search example
    print("=== Simple Semantic Search ===")
    query_text="company policy vacation",
    org_id="1",
    method="semantic",
    top_k=3
    data_dir = "data"

    retrieval_service = DocumentRetrieval(data_dir)
    
    query = DocumentQuery(
        query=query_text,
        organization_id=org_id,
        method=method,
        top_k=top_k,
        filters= {}
    )
    
    results = retrieval_service.query_documents(query)

    print(f"Query: {results.query}")
    print(f"Method: {results.method}")
    print(f"Total Results: {results.total_results}")
    print(f"Processing Time: {results.processing_time_ms:.2f}ms")
    print("\nTop Results:")
    
    for i, doc in enumerate(results.documents[:3], 1):
        print(f"{i}. {doc.title} (Score: {doc.score:.3f})")
        print(f"   Content: {doc.content[:100]}...")
        print(f"   Metadata: {doc.metadata}")
        print()
    