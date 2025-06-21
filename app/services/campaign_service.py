"""
Campaign orchestration service - Updated to use analytics service.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from app.models.campaign import (
    Campaign, CampaignStatus, CampaignCreateRequest,
    SubredditDiscoveryRequest, SubredditDiscoveryByTopicsRequest, PostDiscoveryRequest,
    ResponseGenerationRequest, ResponseExecutionRequest,
    TargetPost, PlannedResponse, PostedResponse, ResponseType
)
from app.services.document_service import DocumentService
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService
from app.managers.campaign_manager import CampaignManager

logger = logging.getLogger(__name__)


class CampaignService:
    """
    Campaign orchestration service that coordinates between
    document processing, Reddit operations, and LLM services.
    """
    
    def __init__(
        self,
        campaign_manager: CampaignManager,
        document_service: DocumentService,
        reddit_service: RedditService,
        llm_service: LLMService
    ):
        """Initialize the campaign service."""
        self.campaign_manager = campaign_manager
        self.document_service = document_service
        self.reddit_service = reddit_service
        self.llm_service = llm_service
        self.logger = logger
    
    async def cleanup(self):
        """Clean up resources."""
        await self.reddit_service.cleanup()
    
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
            
            # Save campaign
            success = self.campaign_manager.save_campaign(campaign)
            
            if success:
                self.logger.info(f"Created campaign '{campaign.name}' for org {organization_id}")
                return True, f"Campaign '{campaign.name}' created successfully", campaign
            else:
                return False, "Failed to save campaign", None
                
        except Exception as e:
            self.logger.error(f"Error creating campaign: {str(e)}")
            return False, f"Error creating campaign: {str(e)}", None
    
    async def get_campaign(self, campaign_id: str) -> Tuple[bool, str, Optional[Campaign]]:
        """Get a campaign by ID."""
        try:
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if campaign:
                return True, "Campaign found", campaign
            else:
                return False, "Campaign not found", None
        except Exception as e:
            self.logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
            return False, f"Error getting campaign: {str(e)}", None
    
    async def list_campaigns(self, organization_id: str) -> Tuple[bool, str, List[Campaign]]:
        """List all campaigns for an organization."""
        try:
            campaigns = self.campaign_manager.list_campaigns_by_organization(organization_id)
            return True, f"Found {len(campaigns)} campaigns", campaigns
        except Exception as e:
            self.logger.error(f"Error listing campaigns for org {organization_id}: {str(e)}")
            return False, f"Error listing campaigns: {str(e)}", []
    
    def _update_campaign(self, campaign: Campaign) -> bool:
        """Update campaign with new timestamp."""
        campaign.updated_at = datetime.now(timezone.utc)
        return self.campaign_manager.save_campaign(campaign)
    
    # ========================================
    # TOPIC DISCOVERY
    # ========================================
    
    async def discover_topics(
        self, 
        campaign_id: str, 
        request: SubredditDiscoveryRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover relevant topics based on selected documents."""
        try:
            # Get campaign
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get documents content
            campaign_context = await self._get_relevant_campaign_context(
                campaign.organization_id, 
                request.document_ids
            )
            
            if not campaign_context:
                return False, "No valid documents found", None
            
            # Extract topics using LLM service
            success, message, topics = await self.llm_service.extract_topics_from_content(
                campaign_context
            )
            
            if not success:
                return False, f"Topic extraction failed: {message}", None
            
            # Update campaign with selected documents and status
            campaign.selected_document_ids = request.document_ids
            campaign.status = CampaignStatus.DOCUMENTS_UPLOADED
            
            if not self._update_campaign(campaign):
                return False, "Failed to update campaign", None
            
            self.logger.info(f"Extracted {len(topics)} topics for campaign {campaign_id}")
            
            return True, f"Extracted {len(topics)} topics from {len(request.document_ids)} documents", {
                "topics": topics,
                "selected_document_ids": request.document_ids,
                "total_topics": len(topics)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting topics for campaign {campaign_id}: {str(e)}")
            return False, f"Error extracting topics: {str(e)}", None
    
    # ========================================
    # SUBREDDIT DISCOVERY
    # ========================================
    
    async def discover_subreddits(
        self, 
        campaign_id: str, 
        request: SubredditDiscoveryByTopicsRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover relevant subreddits based on provided topics."""
        try:
            # Get campaign
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Ensure campaign has documents selected
            if not campaign.selected_document_ids:
                return False, "Campaign must have documents selected before subreddit discovery", None
            
            # Get campaign context for ranking
            campaign_context = await self._get_relevant_campaign_context(
                campaign.organization_id, 
                campaign.selected_document_ids
            )
            
            # Discover subreddits using Reddit service with provided topics
            success, message, discovery_data = await self.reddit_service.discover_subreddits_by_topics(
                topics=request.topics,
                organization_id=campaign.organization_id,
                min_subscribers=10000
            )
            
            if not success:
                return False, message, None
            
            # Rank subreddits using LLM service
            all_subreddits = discovery_data.get("all_subreddits", {})
            if all_subreddits:
                success, message, ranked_subreddits = await self.llm_service.rank_subreddits_by_relevance(
                    campaign_context, 
                    all_subreddits
                )
                
                if success:
                    # Filter ranked subreddits to only include those we found
                    relevant_subreddits = {}
                    for name in ranked_subreddits:
                        if name in all_subreddits:
                            relevant_subreddits[name] = all_subreddits[name]
                    
                    discovery_data["relevant_subreddits"] = relevant_subreddits
                else:
                    # Fallback: use all found subreddits
                    discovery_data["relevant_subreddits"] = all_subreddits
            else:
                discovery_data["relevant_subreddits"] = {}
            
            # Update campaign with results
            campaign.target_subreddits = list(discovery_data["relevant_subreddits"].keys())
            campaign.status = CampaignStatus.SUBREDDITS_DISCOVERED
            
            if not self._update_campaign(campaign):
                return False, "Failed to update campaign", None
            
            self.logger.info(f"Discovered {len(campaign.target_subreddits)} subreddits for campaign {campaign_id}")
            
            return True, f"Discovered {len(campaign.target_subreddits)} relevant subreddits", {
                "subreddits": campaign.target_subreddits,
                "topics": request.topics,
                "total_found": len(discovery_data.get("relevant_subreddits", {}))
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits for campaign {campaign_id}: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", None
    
    # ========================================
    # POST DISCOVERY
    # ========================================
    
    async def discover_posts(
        self, 
        campaign_id: str, 
        request: PostDiscoveryRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover relevant posts and comments in target subreddits."""
        try:
            # Get campaign
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get campaign context
            campaign_context = await self._get_relevant_campaign_context(
                campaign.organization_id, 
                campaign.selected_document_ids
            )
            
            # Extract topics for search using LLM service
            success, message, topics = await self.llm_service.extract_topics_from_content(
                campaign_context
            )
            
            if not success:
                topics = [campaign.name]
                if campaign.description:
                    topics.append(campaign.description)
                topics = [t for t in topics if t] # Ensure no empty strings
                if not topics: # Fallback if name/description are also empty
                    topics = ["general"]
            
            # Discover posts using Reddit service
            success, message, posts = await self.reddit_service.discover_posts(
                subreddits=request.subreddits,
                topics=topics,
                reddit_credentials=request.reddit_credentials,
                max_posts_per_subreddit=request.max_posts_per_subreddit,
                time_filter=request.time_filter
            )
            
            if not success:
                return False, message, None
            
            # Analyze posts for relevance using LLM service
            target_posts = []
            for post in posts:
                try:
                    success, _, analysis = await self.llm_service.analyze_post_relevance(
                        post_title=post.get("title", ""),
                        post_content=post.get("selftext", ""),
                        campaign_context=campaign_context,
                        subreddit=post.get("search_subreddit", "")
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
            campaign.target_posts = {post.id: post for post in target_posts}
            campaign.status = CampaignStatus.POSTS_FOUND
            
            if not self._update_campaign(campaign):
                return False, "Failed to update campaign", None
            
            self.logger.info(f"Found {len(target_posts)} relevant posts for campaign {campaign_id}")
            
            return True, f"Found {len(target_posts)} relevant posts", {
                "posts_found": len(target_posts),
                "subreddits_searched": len(request.subreddits),
                "posts": [post.model_dump() for post in target_posts]
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering posts for campaign {campaign_id}: {str(e)}")
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
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get campaign context
            campaign_context = await self._get_relevant_campaign_context(
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
                
                # Generate response using LLM service
                success, _, response_data = await self.llm_service.generate_reddit_response(
                    post_title=target_post.title,
                    post_content=target_post.content,
                    campaign_context=campaign_context,
                    tone=(request.tone or campaign.response_tone).value,
                    subreddit=target_post.subreddit
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
            campaign.planned_responses = {resp.id: resp for resp in planned_responses}
            campaign.status = CampaignStatus.RESPONSES_PLANNED
            
            if not self._update_campaign(campaign):
                return False, "Failed to update campaign", None
            
            self.logger.info(f"Generated {len(planned_responses)} responses for campaign {campaign_id}")
            
            return True, f"Generated {len(planned_responses)} responses", {
                "responses_generated": len(planned_responses),
                "responses": [resp.model_dump() for resp in planned_responses]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating responses for campaign {campaign_id}: {str(e)}")
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
            campaign = self.campaign_manager.get_campaign(campaign_id)
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
            for resp in posted_responses:
                campaign.posted_responses[resp.id] = resp
            campaign.status = CampaignStatus.RESPONSES_POSTED
            
            if not self._update_campaign(campaign):
                return False, "Failed to update campaign", None
            
            successful_posts = len([r for r in posted_responses if r.posting_successful])
            
            self.logger.info(f"Posted {successful_posts}/{len(posted_responses)} responses for campaign {campaign_id}")
            
            return True, f"Posted {successful_posts}/{len(posted_responses)} responses", {
                "responses_posted": successful_posts,
                "responses_failed": len(posted_responses) - successful_posts,
                "posted_responses": [resp.model_dump() for resp in posted_responses]
            }
            
        except Exception as e:
            self.logger.error(f"Error executing responses for campaign {campaign_id}: {str(e)}")
            return False, f"Error executing responses: {str(e)}", None
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    async def _get_relevant_campaign_context(
        self, 
        organization_id: str, 
        document_ids: List[str]
    ) -> str:
        """Get combined context from campaign documents."""
        try:
            return await self.document_service.get_relevant_campaign_context(organization_id, document_ids)
        except Exception as e:
            self.logger.error(f"Error getting campaign context: {str(e)}")
            return ""
    
    def _find_target_post(self, campaign: Campaign, target_post_id: str) -> Optional[TargetPost]:
        """Find a target post by ID."""
        return campaign.target_posts.get(target_post_id)
    
    def _find_planned_response(self, campaign: Campaign, planned_response_id: str) -> Optional[PlannedResponse]:
        """Find a planned response by ID."""
        return campaign.planned_responses.get(planned_response_id)
    
    def _already_responded_to_author(self, campaign: Campaign, author: str) -> bool:
        """Check if we already responded to this author."""
        for posted_response in campaign.posted_responses.values():
            target_post = self._find_target_post(campaign, posted_response.target_post_id)
            if target_post and target_post.author == author:
                return True
        return False