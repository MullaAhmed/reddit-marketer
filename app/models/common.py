"""
Shared/common data app.models.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum


class ResponseStatus(str, Enum):
    """Generic response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class APIResponse(BaseModel):
    """Generic API response model."""
    
    status: ResponseStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Model for pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Model for paginated responses."""
    
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(
        cls, 
        items: List[Dict[str, Any]], 
        total: int, 
        pagination: PaginationParams
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )


class HealthStatus(BaseModel):
    """Model for health check responses."""
    
    status: str
    timestamp: datetime
    version: str
    service: str
    checks: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """Model for detailed error information."""
    
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationError(BaseModel):
    """Model for validation error responses."""
    
    field: str
    message: str
    value: Optional[Any] = None


class BulkOperationResult(BaseModel):
    """Model for bulk operation results."""
    
    total_items: int
    successful_items: int
    failed_items: int
    errors: List[ErrorDetail] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.successful_items / self.total_items) * 100