"""
Refactored campaign service using the new unified services.
"""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from shared.base.service_base import BaseService
from shared.base.json_storage_mixin import JsonStorageMixin
from reddit.models import (
    Campaign, CampaignStatus, TargetPost, PlannedResponse, PostedResponse,
    ResponseType, ResponseTone, CampaignCreateRequest, SubredditDiscoveryRequest,
    PostDiscoveryRequest, ResponseGenerationRequest, ResponseExecutionRequest
)
from reddit.services.reddit_service import RedditService
from rag.services.document_service import DocumentService


class CampaignService(BaseService, JsonStorageMixin):
    """
    Refactored campaign service using unified services.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the campaign service."""
        super().__init__("CampaignService", data_dir)
        
        # Initialize JSON file
        self._init_json_file("campaigns.json", [])
        
        # Initialize services
        self.reddit_service = RedditService(data_dir)
        self.document_service = DocumentService(data_dir)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.reddit_service.cleanup()
    
    def _update_campaign(self, campaign: Campaign):
        """Update a campaign in the JSON file."""
        campaign.updated_at = datetime.now(timezone.utc)
        self._update_item_in_json("campaigns.json", campaign.model_dump())
    
    def _get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        campaign_data = self._find_item_in_json("campaigns.json", campaign_id)
        return Campaign(**campaign_data) if campaign_data else None
    
    # ========================================
    # CAMPAIGN MANAGEMENT
    # ========================================
    
    async def create_campaign(
        self, 
        organization_id: str, 
        request: CampaignCreateRequest
    ) -> Tuple[bool, str, Optional[Campaign]]:
        """Create a new Reddit marketing campaign."""
        try:
            campaign = Campaign(
                organization_id=organization_id,
                name=request.name,
                description=request.description,
                response_tone=request.response_tone,
                max_responses_per_day=request.max_responses_per_day
            )
            
            self._update_campaign(campaign)
            
            self.log_operation(
                "CAMPAIGN_CREATION",
                True,
                f"Created campaign '{campaign.name}'",
                org_id=organization_id,
                campaign_id=campaign.id
            )
            
            return True, f"Campaign '{campaign.name}' created successfully", campaign
            
        except Exception as e:
            self.log_operation("CAMPAIGN_CREATION", False, str(e), org_id=organization_id)
            return False, f"Error creating campaign: {str(e)}", None
    
    async def get_campaign(self, campaign_id: str) -> Tuple[bool, str, Optional[Campaign]]:
        """Get a campaign by ID."""
        try:
            campaign = self._get_campaign(campaign_id)
            if campaign:
                return True, "Campaign found", campaign
            else:
                return False, "Campaign not found", None
        except Exception as e:
            self.log_operation("CAMPAIGN_RETRIEVAL", False, str(e), campaign_id=campaign_id)
            return False, f"Error getting campaign: {str(e)}", None
    
    async def list_campaigns(self, organization_id: str) -> Tuple[bool, str, List[Campaign]]:
        """List all campaigns for an organization."""
        try:
            campaigns_data = self._filter_items_in_json("campaigns.json", {"organization_id": organization_id})
            campaigns = [Campaign(**camp_data) for camp_data in campaigns_data]
            
            return True, f"Found {len(campaigns)} campaigns", campaigns
            
        except Exception as e:
            self.log_operation("CAMPAIGN_LISTING", False, str(e), org_id=organization_id)
            return False, f"Error listing campaigns: {str(e)}", []
    
    # ========================================
    # SUBREDDIT DISCOVERY
    # ========================================
    
    async def discover_subreddits(
        self, 
        campaign_id: str, 
        request: SubredditDiscoveryRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover relevant subreddits based on selected documents."""
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get documents content
            campaign_context = await self.reddit_service.get_campaign_context(
                campaign.organization_id, 
                request.document_ids
            )
            
            if not campaign_context:
                return False, "No valid documents found", None
            
            # Discover subreddits using Reddit service
            success, message, discovery_data = await self.reddit_service.discover_subreddits(
                campaign_context, 
                campaign.organization_id
            )
            
            if not success:
                return False, message, None
            
            # Update campaign with results
            campaign.selected_document_ids = request.document_ids
            campaign.target_subreddits = list(discovery_data["relevant_subreddits"].keys())
            campaign.status = CampaignStatus.SUBREDDITS_DISCOVERED
            
            self._update_campaign(campaign)
            
            self.log_operation(
                "SUBREDDIT_DISCOVERY",
                True,
                f"Discovered {len(campaign.target_subreddits)} subreddits",
                campaign_id=campaign_id,
                subreddit_count=len(campaign.target_subreddits)
            )
            
            return True, f"Discovered {len(campaign.target_subreddits)} relevant subreddits", {
                "subreddits": campaign.target_subreddits,
                "topics": discovery_data.get("topics", []),
                "total_found": len(discovery_data.get("relevant_subreddits", {}))
            }
            
        except Exception as e:
            self.log_operation("SUBREDDIT_DISCOVERY", False, str(e), campaign_id=campaign_id)
            return False, f"Error discovering subreddits: {str(e)}", None
    
    # ========================================
    # POST DISCOVERY
    # ========================================
    
    async def discover_posts(
        self, 
        campaign_id: str, 
        request: PostDiscoveryRequest,
        reddit_credentials: Dict[str, str]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover relevant posts and comments in target subreddits."""
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get campaign context and topics
            campaign_context = await self.reddit_service.get_campaign_context(
                campaign.organization_id, 
                campaign.selected_document_ids
            )
            
            # Get topics from saved data
            topics_data = self._load_json("topics.json")
            topics = topics_data.get("extracted_topics", []) if isinstance(topics_data, dict) else []
            
            # Discover posts using Reddit service
            success, message, posts = await self.reddit_service.discover_posts(
                subreddits=request.subreddits,
                topics=topics,
                reddit_credentials=reddit_credentials,
                max_posts_per_subreddit=request.max_posts_per_subreddit,
                time_filter=request.time_filter
            )
            
            if not success:
                return False, message, None
            
            # Analyze posts for relevance
            target_posts = []
            for post in posts:
                try:
                    success, _, analysis = await self.reddit_service.analyze_post_relevance(
                        post, campaign_context, campaign.organization_id
                    )
                    
                    if success and analysis.get("should_respond") and analysis.get("relevance_score", 0) > 0.3:
                        target_post = TargetPost(
                            reddit_post_id=post["id"],
                            subreddit=post.get("search_subreddit", ""),
                            title=post.get("title", ""),
                            content=post.get("selftext", ""),
                            author=post.get("author", {}).get("name", ""),
                            score=post.get("score", 0),
                            num_comments=post.get("num_comments", 0),
                            created_utc=post.get("created_utc", 0),
                            permalink=post.get("permalink", ""),
                            relevance_score=analysis["relevance_score"],
                            relevance_reason=analysis["relevance_reason"],
                            response_type=ResponseType.POST_COMMENT
                        )
                        target_posts.append(target_post)
                        
                except Exception as e:
                    self.logger.warning(f"Error analyzing post {post.get('id')}: {str(e)}")
            
            # Update campaign
            campaign.target_posts = target_posts
            campaign.status = CampaignStatus.POSTS_FOUND
            self._update_campaign(campaign)
            
            self.log_operation(
                "POST_DISCOVERY",
                True,
                f"Found {len(target_posts)} relevant posts",
                campaign_id=campaign_id,
                post_count=len(target_posts)
            )
            
            return True, f"Found {len(target_posts)} relevant posts", {
                "posts_found": len(target_posts),
                "subreddits_searched": len(request.subreddits),
                "posts": [post.model_dump() for post in target_posts[:10]]
            }
            
        except Exception as e:
            self.log_operation("POST_DISCOVERY", False, str(e), campaign_id=campaign_id)
            return False, f"Error discovering posts: {str(e)}", None
    
    # ========================================
    # RESPONSE GENERATION
    # ========================================
    
    async def generate_responses(
        self, 
        campaign_id: str, 
        request: ResponseGenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate responses for target posts."""
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get campaign context
            campaign_context = await self.reddit_service.get_campaign_context(
                campaign.organization_id, 
                campaign.selected_document_ids
            )
            
            planned_responses = []
            
            # Generate responses for each target post
            for target_post_id in request.target_post_ids:
                target_post = self._find_target_post(campaign, target_post_id)
                if not target_post:
                    continue
                
                # Check if we already responded to this author
                if self._already_responded_to_author(campaign, target_post.author):
                    self.logger.info(f"Skipping post by {target_post.author} - already responded")
                    continue
                
                # Generate response using Reddit service
                post_data = {
                    "id": target_post.reddit_post_id,
                    "title": target_post.title,
                    "selftext": target_post.content,
                    "search_subreddit": target_post.subreddit
                }
                
                success, _, response_data = await self.reddit_service.generate_response(
                    post=post_data,
                    campaign_context=campaign_context,
                    tone=(request.tone or campaign.response_tone).value,
                    organization_id=campaign.organization_id
                )
                
                if success and response_data:
                    planned_response = PlannedResponse(
                        target_post_id=target_post_id,
                        response_content=response_data["content"],
                        response_type=target_post.response_type,
                        relevant_documents=campaign.selected_document_ids,
                        tone=request.tone or campaign.response_tone,
                        confidence_score=response_data["confidence"]
                    )
                    planned_responses.append(planned_response)
            
            # Update campaign
            campaign.planned_responses = planned_responses
            campaign.status = CampaignStatus.RESPONSES_PLANNED
            self._update_campaign(campaign)
            
            self.log_operation(
                "RESPONSE_GENERATION",
                True,
                f"Generated {len(planned_responses)} responses",
                campaign_id=campaign_id,
                response_count=len(planned_responses)
            )
            
            return True, f"Generated {len(planned_responses)} responses", {
                "responses_generated": len(planned_responses),
                "responses": [resp.model_dump() for resp in planned_responses]
            }
            
        except Exception as e:
            self.log_operation("RESPONSE_GENERATION", False, str(e), campaign_id=campaign_id)
            return False, f"Error generating responses: {str(e)}", None
    
    # ========================================
    # RESPONSE EXECUTION
    # ========================================
    
    async def execute_responses(
        self, 
        campaign_id: str, 
        request: ResponseExecutionRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Execute planned responses by posting to Reddit."""
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            posted_responses = []
            
            # Execute each planned response
            for planned_response_id in request.planned_response_ids:
                planned_response = self._find_planned_response(campaign, planned_response_id)
                if not planned_response:
                    continue
                
                target_post = self._find_target_post(campaign, planned_response.target_post_id)
                if not target_post:
                    continue
                
                # Post the response using Reddit service
                success, message, result = await self.reddit_service.post_response(
                    post_id=target_post.reddit_post_id,
                    response_content=planned_response.response_content,
                    reddit_credentials=request.reddit_credentials,
                    response_type=planned_response.response_type.value
                )
                
                # Create posted response record
                posted_response = PostedResponse(
                    planned_response_id=planned_response.id,
                    target_post_id=planned_response.target_post_id,
                    reddit_comment_id=result.get("id", "") if success else "",
                    reddit_permalink=result.get("permalink", "") if success else "",
                    posted_content=planned_response.response_content,
                    posting_successful=success,
                    error_message=message if not success else None
                )
                
                posted_responses.append(posted_response)
            
            # Update campaign
            campaign.posted_responses.extend(posted_responses)
            campaign.status = CampaignStatus.RESPONSES_POSTED
            self._update_campaign(campaign)
            
            successful_posts = len([r for r in posted_responses if r.posting_successful])
            
            self.log_operation(
                "RESPONSE_EXECUTION",
                True,
                f"Posted {successful_posts}/{len(posted_responses)} responses",
                campaign_id=campaign_id,
                successful_posts=successful_posts,
                total_attempts=len(posted_responses)
            )
            
            return True, f"Posted {successful_posts}/{len(posted_responses)} responses", {
                "responses_posted": successful_posts,
                "responses_failed": len(posted_responses) - successful_posts,
                "posted_responses": [resp.model_dump() for resp in posted_responses]
            }
            
        except Exception as e:
            self.log_operation("RESPONSE_EXECUTION", False, str(e), campaign_id=campaign_id)
            return False, f"Error executing responses: {str(e)}", None
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _find_target_post(self, campaign: Campaign, target_post_id: str) -> Optional[TargetPost]:
        """Find a target post by ID."""
        for post in campaign.target_posts:
            if post.id == target_post_id:
                return post
        return None
    
    def _find_planned_response(self, campaign: Campaign, planned_response_id: str) -> Optional[PlannedResponse]:
        """Find a planned response by ID."""
        for response in campaign.planned_responses:
            if response.id == planned_response_id:
                return response
        return None
    
    def _already_responded_to_author(self, campaign: Campaign, author: str) -> bool:
        """Check if we already responded to this author."""
        for posted_response in campaign.posted_responses:
            target_post = self._find_target_post(campaign, posted_response.target_post_id)
            if target_post and target_post.author == author:
                return True
        return False