"""
Shared/common data app.models.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class ResponseStatus(str, Enum):
    """Generic response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


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