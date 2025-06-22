"""
Text processing utilities.
"""

import re
from html import unescape
from typing import List


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


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with provided arguments."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required prompt argument: {e}")