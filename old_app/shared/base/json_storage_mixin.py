"""
Mixin for JSON storage operations.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class JsonStorageMixin:
    """
    Mixin providing unified JSON storage operations.
    """
    
    def _get_json_file_path(self, filename: str) -> str:
        """Get full path for JSON file."""
        if not hasattr(self, 'data_dir'):
            raise AttributeError("JsonStorageMixin requires 'data_dir' attribute")
        
        json_dir = os.path.join(self.data_dir, "json")
        Path(json_dir).mkdir(parents=True, exist_ok=True)
        return os.path.join(json_dir, filename)
    
    def _load_json(self, filename: str) -> List[Dict]:
        """Load data from JSON file."""
        file_path = self._get_json_file_path(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_json(self, filename: str, data: Any):
        """Save data to JSON file."""
        file_path = self._get_json_file_path(filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            if hasattr(self, 'logger'):
                self.logger.info(f"Successfully saved data to {filename}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error saving data to {filename}: {str(e)}")
            raise
    
    def _init_json_file(self, filename: str, default_data: Any = None):
        """Initialize JSON file if it doesn't exist."""
        file_path = self._get_json_file_path(filename)
        
        if not Path(file_path).exists():
            default_data = default_data if default_data is not None else []
            self._save_json(filename, default_data)
    
    def _update_item_in_json(
        self, 
        filename: str, 
        item: Dict[str, Any], 
        id_field: str = 'id'
    ) -> bool:
        """Update or add an item in JSON file."""
        data = self._load_json(filename)
        
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
        
        self._save_json(filename, data)
        return updated
    
    def _find_item_in_json(
        self, 
        filename: str, 
        item_id: str, 
        id_field: str = 'id'
    ) -> Optional[Dict[str, Any]]:
        """Find an item in JSON file by ID."""
        data = self._load_json(filename)
        
        for item in data:
            if item.get(id_field) == item_id:
                return item
        
        return None
    
    def _filter_items_in_json(
        self, 
        filename: str, 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter items in JSON file by criteria."""
        data = self._load_json(filename)
        
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