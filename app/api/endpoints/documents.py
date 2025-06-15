"""
Document management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Dict, Any

from app.core.dependencies import DocumentServiceDep, validate_organization_id
from app.models.document import (
    DocumentCreateRequest, DocumentResponse, DocumentQuery,
    QueryResponse, Organization
)

router = APIRouter()


@router.post("/ingest", response_model=DocumentResponse)
async def ingest_documents(
    documents: List[DocumentCreateRequest],
    organization_id: str = Query(..., description="Organization ID"),
    organization_name: str = Query(None, description="Organization name for auto-creation"),
    document_service: DocumentServiceDep = None
):
    """Ingest multiple documents for an organization."""
    org_id = validate_organization_id(organization_id)
    
    # Convert requests to dict format expected by service
    doc_dicts = []
    for doc_req in documents:
        doc_dict = {
            "title": doc_req.title,
            "content": doc_req.content,
            "metadata": doc_req.metadata,
            "chunk_size": doc_req.chunk_size,
            "chunk_overlap": doc_req.chunk_overlap
        }
        doc_dicts.append(doc_dict)
    
    success, message, document_ids = document_service.ingest_documents(
        doc_dicts, org_id, organization_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return DocumentResponse(
        success=success,
        message=message,
        data={
            "document_ids": document_ids,
            "documents_ingested": len(document_ids)
        }
    )


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    query: DocumentQuery,
    document_service: DocumentServiceDep = None
):
    """Query documents using semantic or keyword search."""
    if query.organization_id:
        validate_organization_id(query.organization_id)
    
    response = document_service.query_documents(query)
    return response


@router.get("/organizations/{organization_id}", response_model=DocumentResponse)
async def get_organization_documents(
    organization_id: str,
    document_service: DocumentServiceDep = None
):
    """Get all documents for an organization."""
    org_id = validate_organization_id(organization_id)
    
    try:
        organization = document_service.get_or_create_organization(org_id)
        
        return DocumentResponse(
            success=True,
            message=f"Found organization with {organization.documents_count} documents",
            data={
                "organization": organization.model_dump(),
                "documents": [doc.model_dump() for doc in organization.documents]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=DocumentResponse)
async def upload_document_file(
    file: UploadFile = File(...),
    organization_id: str = Query(..., description="Organization ID"),
    title: str = Query(None, description="Document title (defaults to filename)"),
    document_service: DocumentServiceDep = None
):
    """Upload and process a document file."""
    org_id = validate_organization_id(organization_id)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read file content
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    
    # Create document request
    doc_title = title or file.filename
    doc_dict = {
        "title": doc_title,
        "content": text_content,
        "metadata": {
            "filename": file.filename,
            "content_type": file.content_type,
            "source": "file_upload"
        }
    }
    
    success, message, document_ids = document_service.ingest_documents(
        [doc_dict], org_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return DocumentResponse(
        success=success,
        message=message,
        data={
            "document_id": document_ids[0] if document_ids else None,
            "filename": file.filename,
            "title": doc_title
        }
    )


@router.delete("/organizations/{organization_id}/documents/{document_id}")
async def delete_document(
    organization_id: str,
    document_id: str,
    document_service: DocumentServiceDep = None
):
    """Delete a specific document."""
    org_id = validate_organization_id(organization_id)
    
    # This would need to be implemented in the document service
    raise HTTPException(
        status_code=501, 
        detail="Document deletion not yet implemented"
    )


@router.get("/organizations", response_model=DocumentResponse)
async def list_organizations(
    document_service: DocumentServiceDep = None
):
    """List all organizations."""
    try:
        # This would need to be implemented in the document service
        raise HTTPException(
            status_code=501,
            detail="Organization listing not yet implemented"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))