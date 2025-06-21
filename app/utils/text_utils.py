"""
Text processing utility functions.
"""

import re
from html import unescape
from typing import List, Dict, Any


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and formatting."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text.strip()


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def chunk_text(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200
) -> List[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []
    
    words = text.split()
    if not words:
        return []
    
    # Calculate words per chunk (approximate)
    words_per_chunk = max(1, chunk_size // 6)  # Assuming avg 6 chars per word
    overlap_words = max(0, chunk_overlap // 6)
    
    chunks = []
    i = 0
    
    while i < len(words):
        # Get chunk of words
        end_idx = min(i + words_per_chunk, len(words))
        chunk_words = words[i:end_idx]
        chunk_text = " ".join(chunk_words)
        
        chunks.append(chunk_text)
        
        # Move to next chunk position with overlap
        next_i = i + words_per_chunk - overlap_words
        
        # Ensure progress
        if next_i <= i:
            i = end_idx
        else:
            i = next_i
    
    return chunks


def extract_reddit_id_from_url(url: str, id_type: str = "post") -> str:
    """Extract Reddit post or comment ID from URL."""
    if id_type == "post":
        pattern = r'reddit\.com(?:/r/[^/]+)?/comments/([a-zA-Z0-9]+)'
    else:  # comment
        pattern = r'reddit\.com(?:/r/[^/]+)?/comments/[a-zA-Z0-9]+/[^/]*/comment/([a-zA-Z0-9]+)'
    
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Invalid Reddit {id_type} URL: {url}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text."""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter by length and remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity based on common words."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def format_text_for_display(text: str, max_length: int = 500) -> str:
    """Format text for display with proper truncation."""
    # Clean the text
    clean = clean_text(text)
    
    # Truncate if needed
    if len(clean) > max_length:
        clean = truncate_text(clean, max_length)
    
    return clean


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    
    # Clean and filter sentences
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Minimum sentence length
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences