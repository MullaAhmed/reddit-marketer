"""
File handling utilities.
"""

import os
from pathlib import Path
from typing import Optional


def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't."""
    Path(directory).mkdir(parents=True, exist_ok=True)


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