from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""
    CREATED = "created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    SUBREDDITS_DISCOVERED = "subreddits_discovered"
    POSTS_FOUND = "posts_found"
    RESPONSES_PLANNED = "responses_planned"
    RESPONSES_POSTED = "responses_posted"
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseTone(str, Enum):
    """Response tone options"""
    HELPFUL = "helpful"
    PROMOTIONAL = "promotional"
    EDUCATIONAL = "educational"
    CASUAL = "casual"
    PROFESSIONAL = "professional"


class ResponseType(str, Enum):
    """Type of response to make"""
    POST_COMMENT = "post_comment"
    COMMENT_REPLY = "comment_reply"


class Campaign(BaseModel):
    """Campaign model for tracking Reddit marketing campaigns"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str = Field(..., description="Organization ID this campaign belongs to")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Campaign configuration
    response_tone: ResponseTone = Field(default=ResponseTone.HELPFUL)
    max_responses_per_day: int = Field(default=10, ge=1, le=100)
    
    # Campaign state
    status: CampaignStatus = Field(default=CampaignStatus.CREATED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Selected documents for subreddit discovery
    selected_document_ids: List[str] = Field(default_factory=list)
    
    # Discovered subreddits
    target_subreddits: List[str] = Field(default_factory=list)
    
    # Found posts and comments
    target_posts: List[TargetPost] = Field(default_factory=list)
    
    # Planned responses
    planned_responses: List[PlannedResponse] = Field(default_factory=list)
    
    # Posted responses
    posted_responses: List[PostedResponse] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TargetPost(BaseModel):
    """Model for posts/comments identified for potential responses"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    reddit_post_id: str = Field(..., description="Reddit post ID")
    reddit_comment_id: Optional[str] = Field(None, description="Reddit comment ID if targeting a comment")
    
    subreddit: str = Field(..., description="Subreddit name")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post or comment content")
    author: str = Field(..., description="Author username")
    
    score: int = Field(default=0, description="Post/comment score")
    num_comments: int = Field(default=0, description="Number of comments")
    created_utc: float = Field(..., description="Creation timestamp")
    permalink: str = Field(..., description="Reddit permalink")
    
    # AI analysis
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_reason: str = Field(default="", description="Why this post is relevant")
    
    # Response targeting
    response_type: ResponseType = Field(..., description="Type of response to make")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlannedResponse(BaseModel):
    """Model for planned responses before posting"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    target_post_id: str = Field(..., description="ID of the target post")
    
    response_content: str = Field(..., description="Generated response content")
    response_type: ResponseType = Field(..., description="Type of response")
    
    # Context used for generation
    relevant_documents: List[str] = Field(default_factory=list, description="Document IDs used for context")
    tone: ResponseTone = Field(..., description="Tone used for response")
    
    # AI confidence
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PostedResponse(BaseModel):
    """Model for responses that have been posted to Reddit"""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    planned_response_id: str = Field(..., description="ID of the planned response")
    target_post_id: str = Field(..., description="ID of the target post")
    
    # Reddit response details
    reddit_comment_id: str = Field(..., description="Reddit comment ID of posted response")
    reddit_permalink: str = Field(..., description="Permalink to the posted comment")
    
    # Posting details
    posted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    posted_content: str = Field(..., description="Actual content that was posted")
    
    # Success tracking
    posting_successful: bool = Field(default=True)
    error_message: Optional[str] = Field(None, description="Error message if posting failed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CampaignCreateRequest(BaseModel):
    """Request model for creating a new campaign"""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    response_tone: ResponseTone = Field(default=ResponseTone.HELPFUL)
    max_responses_per_day: int = Field(default=10, ge=1, le=100)


class SubredditDiscoveryRequest(BaseModel):
    """Request model for discovering subreddits"""
    
    document_ids: List[str] = Field(..., min_items=1, description="Document IDs to use for subreddit discovery")


class PostDiscoveryRequest(BaseModel):
    """Request model for discovering posts"""
    
    subreddits: List[str] = Field(..., min_items=1, description="Subreddits to search in")
    max_posts_per_subreddit: int = Field(default=25, ge=1, le=100)
    time_filter: str = Field(default="day", description="Time filter for posts (day, week, month)")


class ResponseGenerationRequest(BaseModel):
    """Request model for generating responses"""
    
    target_post_ids: List[str] = Field(..., min_items=1, description="Target post IDs to generate responses for")
    tone: Optional[ResponseTone] = Field(None, description="Override campaign tone for this generation")


class ResponseExecutionRequest(BaseModel):
    """Request model for executing planned responses"""
    
    planned_response_ids: List[str] = Field(..., min_items=1, description="Planned response IDs to execute")
    reddit_credentials: Dict[str, str] = Field(..., description="Reddit API credentials")


class CampaignResponse(BaseModel):
    """Response model for campaign operations"""
    
    success: bool
    message: str
    campaign: Optional[Campaign] = None
    data: Optional[Dict[str, Any]] = None