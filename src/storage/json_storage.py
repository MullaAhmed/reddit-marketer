"""
Simple JSON file storage for logs and metadata.
"""

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


class JsonStorage:
    """Simple JSON file storage manager."""
    
    def __init__(self):
        """Initialize JSON storage."""
        self.json_dir = os.path.join(settings.DATA_DIR, "json")
        Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def _get_file_path(self, filename: str) -> str:
        """Get full path for JSON file."""
        return os.path.join(self.json_dir, filename)
    
    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        file_path = self._get_file_path(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to JSON file."""
        file_path = self._get_file_path(filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {str(e)}")
            return False
    
    def update_item(
        self,
        filename: str,
        item: Dict[str, Any],
        id_field: str = 'id'
    ) -> bool:
        """Update or add an item in JSON file."""
        data = self.load_data(filename)
        
        # Find and update existing item
        updated = False
        for i, existing_item in enumerate(data):
            if existing_item.get(id_field) == item.get(id_field):
                data[i] = item
                updated = True
                break
        
        # Add new item if not found
        if not updated:
            data.append(item)
        
        return self.save_data(filename, data)
    
    def find_item(
        self,
        filename: str,
        item_id: str,
        id_field: str = 'id'
    ) -> Optional[Dict[str, Any]]:
        """Find an item in JSON file by ID."""
        data = self.load_data(filename)
        
        for item in data:
            if item.get(id_field) == item_id:
                return item
        
        return None
    
    def filter_items(
        self,
        filename: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter items in JSON file by criteria."""
        data = self.load_data(filename)
        
        filtered_items = []
        for item in data:
            match = True
            for key, value in filters.items():
                if item.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_items.append(item)
        
        return filtered_items
    
    def delete_item(
        self,
        filename: str,
        item_id: str,
        id_field: str = 'id'
    ) -> bool:
        """Delete an item from JSON file."""
        data = self.load_data(filename)
        
        for i, item in enumerate(data):
            if item.get(id_field) == item_id:
                del data[i]
                return self.save_data(filename, data)
        
        return False
    
    def init_file(self, filename: str, default_data: Any = None) -> bool:
        """Initialize JSON file if it doesn't exist."""
        file_path = self._get_file_path(filename)
        
        if not Path(file_path).exists():
            default_data = default_data if default_data is not None else []
            return self.save_data(filename, default_data)
        
        return True