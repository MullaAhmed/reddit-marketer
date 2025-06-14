"""
Base service class with common functionality for all services.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class BaseService:
    """
    Base class for all services providing common functionality.
    """
    
    def __init__(
        self, 
        service_name: str,
        data_dir: str = "data",
        log_level: int = logging.INFO
    ):
        """
        Initialize base service.
        
        Args:
            service_name: Name of the service for logging
            data_dir: Base data directory
            log_level: Logging level
        """
        self.service_name = service_name
        self.data_dir = data_dir
        
        # Set up logging
        self.logger = self._setup_logging(log_level)
        
        # Ensure data directories exist
        self._ensure_directories()
    
    def _setup_logging(self, log_level: int) -> logging.Logger:
        """Set up logging for the service."""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            os.path.join(self.data_dir, "json"),
            os.path.join(self.data_dir, "chromadb"),
            os.path.join(self.data_dir, "daily")
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_timestamp(self) -> datetime:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc)
    
    def log_operation(self, operation: str, success: bool, message: str, **kwargs):
        """Log operation with consistent format."""
        level = logging.INFO if success else logging.ERROR
        status = "SUCCESS" if success else "FAILED"
        
        log_message = f"{operation} {status}: {message}"
        if kwargs:
            log_message += f" | Details: {kwargs}"
        
        self.logger.log(level, log_message)


class AsyncBaseService(BaseService):
    """
    Async version of base service for async operations.
    """
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self, 'cleanup'):
            await self.cleanup()