"""
Reddit-related data app.models.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class SubredditDiscoveryRequest(BaseModel):
    """Request model for subreddit discovery."""
    
    content: str = Field(..., min_length=1, description="Content to analyze for subreddit discovery")
    min_subscribers: int = Field(default=10000, ge=0, description="Minimum subscriber count")


class SubredditInfo(BaseModel):
    """Model for subreddit information."""
    
    name: str = Field(..., description="Subreddit name")
    subscribers: int = Field(default=0, description="Number of subscribers")
    description: str = Field(default="", description="Subreddit description")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score")


class PostInfo(BaseModel):
    """Model for Reddit post information."""
    
    id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title")
    content: str = Field(default="", description="Post content")
    author: str = Field(..., description="Post author")
    subreddit: str = Field(..., description="Subreddit name")
    score: int = Field(default=0, description="Post score")
    num_comments: int = Field(default=0, description="Number of comments")
    created_utc: float = Field(..., description="Creation timestamp")
    permalink: str = Field(..., description="Reddit permalink")


class SubredditResponse(BaseModel):
    """Response model for subreddit operations."""
    
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class RedditCredentials(BaseModel):
    """Model for Reddit API credentials."""
    
    client_id: str = Field(..., description="Reddit client ID")
    client_secret: str = Field(..., description="Reddit client secret")
    username: Optional[str] = Field(None, description="Reddit username")
    password: Optional[str] = Field(None, description="Reddit password")
    user_agent: Optional[str] = Field(None, description="User agent string")