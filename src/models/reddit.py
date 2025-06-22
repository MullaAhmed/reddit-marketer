"""
Reddit data models.
"""

from typing import List, Dict, Any
from pydantic import BaseModel


class SubredditInfo(BaseModel):
    """Subreddit information model."""
    
    name: str
    subscribers: int
    description: str


class CommentInfo(BaseModel):
    """Reddit comment information model."""
    
    id: str
    author: str
    body: str
    created_utc: float
    permalink: str
    score: int


class PostInfo(BaseModel):
    """Reddit post information model."""
    
    id: str
    title: str
    content: str
    author: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: float
    permalink: str
    comments: List[CommentInfo] = []


class ResponseTarget(BaseModel):
    """Target for response (post or comment)."""
    
    target_id: str
    response_type: str  # "post_comment" or "comment_reply"
    target_content: str
    reasoning: str


class GeneratedResponse(BaseModel):
    """Generated response data."""
    
    content: str
    target: ResponseTarget
    confidence: float
    context_used: List[str]