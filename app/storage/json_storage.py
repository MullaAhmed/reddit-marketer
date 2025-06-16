"""
JSON file storage operations.
"""

import json
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.utils.file_utils import ensure_directory

logger = logging.getLogger(__name__)


class JsonStorage:
    """
    JSON file storage manager for persistent data operations.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize JSON app.storage."""
        self.data_dir = data_dir
        self.json_dir = os.path.join(data_dir, "json")
        ensure_directory(self.json_dir)
        self.logger = logger
    
    def get_file_path(self, filename: str) -> str:
        """Get full path for JSON file."""
        return os.path.join(self.json_dir, filename)
    
    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        file_path = self.get_file_path(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure we always return a list
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.debug(f"Could not load {filename}: {str(e)}")
            return []
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to JSON file."""
        file_path = self.get_file_path(filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.debug(f"Saved data to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {str(e)}")
            return False
    
    def init_file(self, filename: str, default_data: Any = None) -> bool:
        """Initialize JSON file if it doesn't exist."""
        file_path = self.get_file_path(filename)
        
        if not Path(file_path).exists():
            default_data = default_data if default_data is not None else []
            return self.save_data(filename, default_data)
        
        return True
    
    def append_item(self, filename: str, item: Dict[str, Any]) -> bool:
        """Append item to JSON file."""
        data = self.load_data(filename)
        data.append(item)
        return self.save_data(filename, data)
    
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
        
        # Find and remove item
        for i, item in enumerate(data):
            if item.get(id_field) == item_id:
                del data[i]
                return self.save_data(filename, data)
        
        return False
    
    def count_items(self, filename: str, filters: Dict[str, Any] = None) -> int:
        """Count items in JSON file, optionally with filters."""
        if filters:
            items = self.filter_items(filename, filters)
            return len(items)
        else:
            data = self.load_data(filename)
            return len(data)
    
    def clear_file(self, filename: str) -> bool:
        """Clear all data from JSON file."""
        return self.save_data(filename, [])
    
    def backup_file(self, filename: str, backup_suffix: str = ".backup") -> bool:
        """Create a backup of JSON file."""
        source_path = self.get_file_path(filename)
        backup_path = source_path + backup_suffix
        
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error creating backup for {filename}: {str(e)}")
            return False
    
    def get_file_stats(self, filename: str) -> Dict[str, Any]:
        """Get statistics about JSON file."""
        file_path = self.get_file_path(filename)
        
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                data = self.load_data(filename)
                
                return {
                    "filename": filename,
                    "exists": True,
                    "size_bytes": stat.st_size,
                    "item_count": len(data),
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime
                }
            else:
                return {
                    "filename": filename,
                    "exists": False,
                    "size_bytes": 0,
                    "item_count": 0
                }
        except Exception as e:
            self.logger.error(f"Error getting stats for {filename}: {str(e)}")
            return {
                "filename": filename,
                "exists": False,
                "error": str(e)
            }