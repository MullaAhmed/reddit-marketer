"""
File utility functions.
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any


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
    extension: Optional[str] = None,
    recursive: bool = False
) -> List[str]:
    """List files in directory, optionally filter by extension."""
    if not os.path.exists(directory):
        return []
    
    files = []
    
    if recursive:
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if extension is None or filename.endswith(extension):
                    files.append(file_path)
    else:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if extension is None or filename.endswith(extension):
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


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """Calculate hash of file content."""
    try:
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    except Exception:
        return None


def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read text file content."""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """Write content to text file."""
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def get_directory_size(directory: str) -> int:
    """Get total size of directory in bytes."""
    total_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    continue
    except Exception:
        pass
    
    return total_size


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """Find files matching a pattern."""
    import glob
    
    search_pattern = os.path.join(directory, pattern)
    return glob.glob(search_pattern, recursive=True)


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information."""
    try:
        stat = os.stat(file_path)
        
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path),
            "extension": os.path.splitext(file_path)[1],
            "exists": True
        }
    except Exception:
        return {
            "path": file_path,
            "exists": False
        }


def cleanup_empty_directories(root_directory: str) -> int:
    """Remove empty directories recursively."""
    removed_count = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(root_directory, topdown=False):
            # Skip the root directory
            if dirpath == root_directory:
                continue
            
            # Check if directory is empty
            if not dirnames and not filenames:
                try:
                    os.rmdir(dirpath)
                    removed_count += 1
                except OSError:
                    pass
    except Exception:
        pass
    
    return removed_count