"""
Data validation utility functions.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_reddit_url(url: str) -> bool:
    """Validate Reddit URL format."""
    reddit_patterns = [
        r'https?://(?:www\.)?reddit\.com/r/[^/]+/comments/[a-zA-Z0-9]+',
        r'https?://(?:www\.)?reddit\.com/r/[^/]+',
        r'https?://(?:www\.)?reddit\.com/user/[^/]+',
    ]
    
    return any(re.match(pattern, url) for pattern in reddit_patterns)


def is_valid_reddit_post_id(post_id: str) -> bool:
    """Validate Reddit post ID format."""
    # Reddit post IDs are typically 6-7 characters, alphanumeric
    pattern = r'^[a-zA-Z0-9]{6,7}$'
    return bool(re.match(pattern, post_id))


def is_valid_reddit_comment_id(comment_id: str) -> bool:
    """Validate Reddit comment ID format."""
    # Reddit comment IDs are typically 7 characters, alphanumeric
    pattern = r'^[a-zA-Z0-9]{7}$'
    return bool(re.match(pattern, comment_id))


def validate_text_length(text: str, min_length: int = 0, max_length: int = None) -> bool:
    """Validate text length."""
    if not isinstance(text, str):
        return False
    
    length = len(text.strip())
    
    if length < min_length:
        return False
    
    if max_length is not None and length > max_length:
        return False
    
    return True


def is_valid_organization_id_format(org_id: str) -> bool:
    """Validate organization ID format."""
    if not isinstance(org_id, str):
        return False
    
    # Organization ID should be 3-50 characters, alphanumeric with hyphens/underscores
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, org_id))


def validate_campaign_name(name: str) -> bool:
    """Validate campaign name."""
    return validate_text_length(name, min_length=1, max_length=200)


def validate_document_title(title: str) -> bool:
    """Validate document title."""
    return validate_text_length(title, min_length=1, max_length=200)


def validate_subreddit_name(subreddit: str) -> bool:
    """Validate subreddit name format."""
    if not isinstance(subreddit, str):
        return False
    
    # Remove 'r/' prefix if present
    if subreddit.startswith('r/'):
        subreddit = subreddit[2:]
    
    # Subreddit names: 3-21 characters, alphanumeric with underscores
    pattern = r'^[a-zA-Z0-9_]{3,21}$'
    return bool(re.match(pattern, subreddit))


def validate_reddit_credentials(credentials: Dict[str, Any]) -> List[str]:
    """Validate Reddit API credentials."""
    errors = []
    
    required_fields = ['client_id', 'client_secret']
    for field in required_fields:
        if field not in credentials or not credentials[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate client_id format (typically 14 characters)
    if 'client_id' in credentials:
        client_id = credentials['client_id']
        if not isinstance(client_id, str) or len(client_id) < 10:
            errors.append("Invalid client_id format")
    
    # Validate client_secret format (typically 27 characters)
    if 'client_secret' in credentials:
        client_secret = credentials['client_secret']
        if not isinstance(client_secret, str) or len(client_secret) < 20:
            errors.append("Invalid client_secret format")
    
    # Validate username if provided
    if 'username' in credentials and credentials['username']:
        username = credentials['username']
        if not isinstance(username, str) or len(username) < 3:
            errors.append("Invalid username format")
    
    return errors


def validate_pagination_params(page: int, page_size: int) -> List[str]:
    """Validate pagination parameters."""
    errors = []
    
    if not isinstance(page, int) or page < 1:
        errors.append("Page must be a positive integer")
    
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        errors.append("Page size must be between 1 and 100")
    
    return errors


def validate_chunk_parameters(chunk_size: int, chunk_overlap: int) -> List[str]:
    """Validate text chunking parameters."""
    errors = []
    
    if not isinstance(chunk_size, int) or chunk_size < 100 or chunk_size > 5000:
        errors.append("Chunk size must be between 100 and 5000")
    
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        errors.append("Chunk overlap must be non-negative")
    
    if chunk_overlap >= chunk_size:
        errors.append("Chunk overlap must be less than chunk size")
    
    return errors


def validate_query_parameters(query: str, top_k: int, method: str) -> List[str]:
    """Validate document query parameters."""
    errors = []
    
    if not validate_text_length(query, min_length=1):
        errors.append("Query cannot be empty")
    
    if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
        errors.append("top_k must be between 1 and 50")
    
    valid_methods = ['semantic', 'keyword']
    if method not in valid_methods:
        errors.append(f"Method must be one of: {', '.join(valid_methods)}")
    
    return errors


def sanitize_input(text: str, max_length: int = None) -> str:
    """Sanitize user input."""
    if not isinstance(text, str):
        return ""
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_upload(filename: str, content: bytes, max_size: int = 10 * 1024 * 1024) -> List[str]:
    """Validate file upload."""
    errors = []
    
    if not filename:
        errors.append("Filename is required")
    
    if not content:
        errors.append("File content is required")
    
    if len(content) > max_size:
        errors.append(f"File size exceeds maximum of {max_size} bytes")
    
    # Check file extension
    allowed_extensions = ['.txt', '.md', '.pdf', '.doc', '.docx']
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{ext}' not in allowed_extensions:
            errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    return errors


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no path traversal)."""
    if not filename:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for reserved names (Windows)
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
    if filename.upper() in reserved_names:
        return False
    
    return True