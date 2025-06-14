"""
File utility functions.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional


def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)


def ensure_directories(directories: List[str]) -> None:
    """Ensure multiple directories exist."""
    for directory in directories:
        ensure_directory(directory)


def safe_remove_file(file_path: str) -> bool:
    """Safely remove a file, return True if successful."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception:
        return False


def safe_remove_directory(directory: str) -> bool:
    """Safely remove a directory and its contents."""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        return True
    except Exception:
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes, return None if file doesn't exist."""
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return None


def list_files_in_directory(
    directory: str, 
    extension: Optional[str] = None
) -> List[str]:
    """List files in directory, optionally filter by extension."""
    if not os.path.exists(directory):
        return []
    
    files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            if extension is None or file.endswith(extension):
                files.append(file_path)
    
    return files


def copy_file(source: str, destination: str) -> bool:
    """Copy file from source to destination."""
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        ensure_directory(dest_dir)
        
        shutil.copy2(source, destination)
        return True
    except Exception:
        return False


def move_file(source: str, destination: str) -> bool:
    """Move file from source to destination."""
    try:
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        ensure_directory(dest_dir)
        
        shutil.move(source, destination)
        return True
    except Exception:
        return False