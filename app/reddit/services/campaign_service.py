"""
CampaignService - Orchestrates the entire Reddit marketing campaign workflow
"""

import json
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from reddit.models import (
    Campaign, CampaignStatus, TargetPost, PlannedResponse, PostedResponse,
    ResponseType, ResponseTone, CampaignCreateRequest, SubredditDiscoveryRequest,
    PostDiscoveryRequest, ResponseGenerationRequest, ResponseExecutionRequest
)
from reddit.agents.ingestion_agent import IngestionAgent
from reddit.core.reddit_post_finder import RedditPostFinder
from reddit.core.reddit_interactor import RedditInteractor
from rag.retrieval import DocumentRetrieval
from rag.models import DocumentQuery
from services.llm.llm_service import ai_client


class CampaignService:
    """
    Service for managing Reddit marketing campaigns.
    Orchestrates the entire workflow from document ingestion to response posting.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the campaign service."""
        self.data_dir = data_dir
        self.json_dir = os.path.join(data_dir, "json")
        self.campaigns_file = os.path.join(self.json_dir, "campaigns.json")
        
        # Ensure directories exist
        Path(self.json_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize JSON file if it doesn't exist
        self._init_campaigns_file()
        
        # Set up logging
        self.logger = logging.getLogger("CampaignService")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Initialize services
        self.ingestion_agent = IngestionAgent()
        self.document_retrieval = DocumentRetrieval(data_dir=data_dir)
    
    def _init_campaigns_file(self):
        """Create empty campaigns file if it doesn't exist."""
        if not Path(self.campaigns_file).exists():
            with open(self.campaigns_file, 'w') as f:
                json.dump([], f)
    
    def _load_campaigns(self) -> List[Dict]:
        """Load campaigns from JSON file."""
        try:
            with open(self.campaigns_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_campaigns(self, campaigns: List[Dict]):
        """Save campaigns to JSON file."""
        with open(self.campaigns_file, 'w') as f:
            json.dump(campaigns, f, indent=2, default=str)
    
    def _update_campaign(self, campaign: Campaign):
        """Update a campaign in the JSON file."""
        campaigns = self._load_campaigns()
        
        # Update timestamp
        campaign.updated_at = datetime.now(timezone.utc)
        
        # Find and update existing campaign
        updated = False
        for i, camp_data in enumerate(campaigns):
            if camp_data['id'] == campaign.id:
                campaigns[i] = campaign.model_dump()
                updated = True
                break
        
        if not updated:
            campaigns.append(campaign.model_dump())
        
        self._save_campaigns(campaigns)
    
    def _get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        campaigns = self._load_campaigns()
        
        for camp_data in campaigns:
            if camp_data['id'] == campaign_id:
                return Campaign(**camp_data)
        return None
    
    # ========================================
    # CAMPAIGN MANAGEMENT
    # ========================================
    
    async def create_campaign(
        self, 
        organization_id: str, 
        request: CampaignCreateRequest
    ) -> Tuple[bool, str, Optional[Campaign]]:
        """
        Create a new Reddit marketing campaign.
        
        Args:
            organization_id: Organization ID
            request: Campaign creation request
            
        Returns:
            Tuple of (success, message, campaign)
        """
        try:
            campaign = Campaign(
                organization_id=organization_id,
                name=request.name,
                description=request.description,
                response_tone=request.response_tone,
                max_responses_per_day=request.max_responses_per_day
            )
            
            self._update_campaign(campaign)
            
            self.logger.info(f"Created campaign {campaign.id} for organization {organization_id}")
            return True, f"Campaign '{campaign.name}' created successfully", campaign
            
        except Exception as e:
            self.logger.error(f"Error creating campaign: {str(e)}")
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
            self.logger.error(f"Error getting campaign: {str(e)}")
            return False, f"Error getting campaign: {str(e)}", None
    
    async def list_campaigns(self, organization_id: str) -> Tuple[bool, str, List[Campaign]]:
        """List all campaigns for an organization."""
        try:
            campaigns = self._load_campaigns()
            org_campaigns = [
                Campaign(**camp_data) 
                for camp_data in campaigns 
                if camp_data.get('organization_id') == organization_id
            ]
            
            return True, f"Found {len(org_campaigns)} campaigns", org_campaigns
            
        except Exception as e:
            self.logger.error(f"Error listing campaigns: {str(e)}")
            return False, f"Error listing campaigns: {str(e)}", []
    
    # ========================================
    # SUBREDDIT DISCOVERY
    # ========================================
    
    async def discover_subreddits(
        self, 
        campaign_id: str, 
        request: SubredditDiscoveryRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Discover relevant subreddits based on selected documents.
        
        Args:
            campaign_id: Campaign ID
            request: Subreddit discovery request
            
        Returns:
            Tuple of (success, message, discovery_data)
        """
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get selected documents content
            documents_content = await self._get_documents_content(
                campaign.organization_id, 
                request.document_ids
            )
            
            if not documents_content:
                return False, "No valid documents found", None
            
            # Combine document content
            combined_content = "\n\n".join(documents_content)
            
            # Use ingestion agent to find subreddits
            discovery_results = await self.ingestion_agent.process_content(
                combined_content, 
                campaign.organization_id
            )
            
            # Update campaign with results
            campaign.selected_document_ids = request.document_ids
            campaign.target_subreddits = discovery_results.get("top_subreddits", [])
            campaign.status = CampaignStatus.SUBREDDITS_DISCOVERED
            
            self._update_campaign(campaign)
            
            self.logger.info(f"Discovered {len(campaign.target_subreddits)} subreddits for campaign {campaign_id}")
            
            return True, f"Discovered {len(campaign.target_subreddits)} relevant subreddits", {
                "subreddits": campaign.target_subreddits,
                "topics": discovery_results.get("topics", []),
                "total_found": discovery_results.get("topics_found", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits: {str(e)}")
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
        """
        Discover relevant posts and comments in target subreddits.
        
        Args:
            campaign_id: Campaign ID
            request: Post discovery request
            reddit_credentials: Reddit API credentials
            
        Returns:
            Tuple of (success, message, discovery_data)
        """
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Initialize Reddit post finder
            post_finder = RedditPostFinder(
                client_id=reddit_credentials["client_id"],
                client_secret=reddit_credentials["client_secret"],
                username=reddit_credentials.get("username"),
                password=reddit_credentials.get("password")
            )
            
            # Get campaign context for relevance analysis
            campaign_context = await self._get_campaign_context(campaign)
            
            all_target_posts = []
            
            try:
                # Search each subreddit
                for subreddit in request.subreddits:
                    self.logger.info(f"Searching posts in r/{subreddit}")
                    
                    # Search for posts using campaign topics as queries
                    topics = await self._get_campaign_topics(campaign)
                    
                    for topic in topics[:3]:  # Limit to top 3 topics
                        posts = await post_finder.search_subreddit_posts(
                            subreddit=subreddit,
                            query=topic,
                            sort="new",  # Get recent posts
                            time_filter=request.time_filter,
                            limit=request.max_posts_per_subreddit
                        )
                        
                        # Analyze posts for relevance
                        for post in posts:
                            target_post = await self._analyze_post_relevance(
                                post, subreddit, campaign_context
                            )
                            if target_post and target_post.relevance_score > 0.3:  # Threshold
                                all_target_posts.append(target_post)
                
                # Update campaign
                campaign.target_posts = all_target_posts
                campaign.status = CampaignStatus.POSTS_FOUND
                self._update_campaign(campaign)
                
                self.logger.info(f"Found {len(all_target_posts)} relevant posts for campaign {campaign_id}")
                
                return True, f"Found {len(all_target_posts)} relevant posts", {
                    "posts_found": len(all_target_posts),
                    "subreddits_searched": len(request.subreddits),
                    "posts": [post.model_dump() for post in all_target_posts[:10]]  # Return first 10
                }
                
            finally:
                await post_finder.close()
                
        except Exception as e:
            self.logger.error(f"Error discovering posts: {str(e)}")
            return False, f"Error discovering posts: {str(e)}", None
    
    # ========================================
    # RESPONSE GENERATION
    # ========================================
    
    async def generate_responses(
        self, 
        campaign_id: str, 
        request: ResponseGenerationRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate responses for target posts.
        
        Args:
            campaign_id: Campaign ID
            request: Response generation request
            
        Returns:
            Tuple of (success, message, generation_data)
        """
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Get campaign context
            campaign_context = await self._get_campaign_context(campaign)
            
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
                
                # Generate response
                response_content = await self._generate_response_content(
                    target_post, 
                    campaign_context, 
                    request.tone or campaign.response_tone
                )
                
                if response_content:
                    planned_response = PlannedResponse(
                        target_post_id=target_post_id,
                        response_content=response_content["content"],
                        response_type=target_post.response_type,
                        relevant_documents=campaign.selected_document_ids,
                        tone=request.tone or campaign.response_tone,
                        confidence_score=response_content["confidence"]
                    )
                    planned_responses.append(planned_response)
            
            # Update campaign
            campaign.planned_responses = planned_responses
            campaign.status = CampaignStatus.RESPONSES_PLANNED
            self._update_campaign(campaign)
            
            self.logger.info(f"Generated {len(planned_responses)} responses for campaign {campaign_id}")
            
            return True, f"Generated {len(planned_responses)} responses", {
                "responses_generated": len(planned_responses),
                "responses": [resp.model_dump() for resp in planned_responses]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating responses: {str(e)}")
            return False, f"Error generating responses: {str(e)}", None
    
    # ========================================
    # RESPONSE EXECUTION
    # ========================================
    
    async def execute_responses(
        self, 
        campaign_id: str, 
        request: ResponseExecutionRequest
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Execute planned responses by posting to Reddit.
        
        Args:
            campaign_id: Campaign ID
            request: Response execution request
            
        Returns:
            Tuple of (success, message, execution_data)
        """
        try:
            # Get campaign
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False, "Campaign not found", None
            
            # Initialize Reddit interactor
            reddit_interactor = RedditInteractor(
                client_id=request.reddit_credentials["client_id"],
                client_secret=request.reddit_credentials["client_secret"],
                username=request.reddit_credentials["username"],
                password=request.reddit_credentials["password"]
            )
            
            posted_responses = []
            
            try:
                # Execute each planned response
                for planned_response_id in request.planned_response_ids:
                    planned_response = self._find_planned_response(campaign, planned_response_id)
                    if not planned_response:
                        continue
                    
                    target_post = self._find_target_post(campaign, planned_response.target_post_id)
                    if not target_post:
                        continue
                    
                    # Post the response
                    posted_response = await self._post_response(
                        reddit_interactor, 
                        planned_response, 
                        target_post
                    )
                    
                    if posted_response:
                        posted_responses.append(posted_response)
                
                # Update campaign
                campaign.posted_responses.extend(posted_responses)
                campaign.status = CampaignStatus.RESPONSES_POSTED
                self._update_campaign(campaign)
                
                successful_posts = len([r for r in posted_responses if r.posting_successful])
                
                self.logger.info(f"Posted {successful_posts}/{len(posted_responses)} responses for campaign {campaign_id}")
                
                return True, f"Posted {successful_posts}/{len(posted_responses)} responses", {
                    "responses_posted": successful_posts,
                    "responses_failed": len(posted_responses) - successful_posts,
                    "posted_responses": [resp.model_dump() for resp in posted_responses]
                }
                
            finally:
                await reddit_interactor.close()
                
        except Exception as e:
            self.logger.error(f"Error executing responses: {str(e)}")
            return False, f"Error executing responses: {str(e)}", None
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    async def _get_documents_content(self, organization_id: str, document_ids: List[str]) -> List[str]:
        """Get content from selected documents."""
        try:
            # Query documents using RAG system
            contents = []
            
            for doc_id in document_ids:
                query = DocumentQuery(
                    query="",  # Empty query to get all content
                    organization_id=organization_id,
                    filters={"document_id": doc_id},
                    top_k=100  # Get all chunks
                )
                
                results = self.document_retrieval.query_documents(query)
                
                # Combine all chunks for this document
                doc_content = "\n".join([doc.content for doc in results.documents])
                if doc_content.strip():
                    contents.append(doc_content)
            
            return contents
            
        except Exception as e:
            self.logger.error(f"Error getting documents content: {str(e)}")
            return []
    
    async def _get_campaign_context(self, campaign: Campaign) -> str:
        """Get combined context from campaign documents."""
        documents_content = await self._get_documents_content(
            campaign.organization_id, 
            campaign.selected_document_ids
        )
        return "\n\n".join(documents_content)
    
    async def _get_campaign_topics(self, campaign: Campaign) -> List[str]:
        """Get topics from campaign's subreddit discovery."""
        try:
            # Load topics from the ingestion agent's output
            topics_file = os.path.join(self.json_dir, "topics.json")
            if os.path.exists(topics_file):
                with open(topics_file, 'r') as f:
                    topics_data = json.load(f)
                    if topics_data.get("organization_id") == campaign.organization_id:
                        return topics_data.get("extracted_topics", [])
            
            # Fallback: extract topics from subreddit names
            return campaign.target_subreddits[:5]  # Use subreddit names as topics
            
        except Exception as e:
            self.logger.error(f"Error getting campaign topics: {str(e)}")
            return campaign.target_subreddits[:5]
    
    async def _analyze_post_relevance(
        self, 
        post: Dict[str, Any], 
        subreddit: str, 
        campaign_context: str
    ) -> Optional[TargetPost]:
        """Analyze if a post is relevant for the campaign."""
        try:
            # Use AI to analyze relevance
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing Reddit posts for marketing relevance. Analyze if the post is relevant for the given campaign context and provide a relevance score."
                },
                {
                    "role": "user",
                    "content": f"""
                    Campaign Context: {campaign_context[:1000]}
                    
                    Post Title: {post.get('title', '')}
                    Post Content: {post.get('selftext', '')[:500]}
                    Subreddit: r/{subreddit}
                    
                    Analyze this post and return a JSON object with:
                    - relevance_score (0.0 to 1.0)
                    - relevance_reason (brief explanation)
                    - should_respond (boolean)
                    """
                }
            ]
            
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            analysis = response["choices"][0]["message"]["content"]
            
            if analysis["should_respond"] and analysis["relevance_score"] > 0.3:
                return TargetPost(
                    reddit_post_id=post["id"],
                    subreddit=subreddit,
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
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing post relevance: {str(e)}")
            return None
    
    async def _generate_response_content(
        self, 
        target_post: TargetPost, 
        campaign_context: str, 
        tone: ResponseTone
    ) -> Optional[Dict[str, Any]]:
        """Generate response content for a target post."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""You are a helpful Reddit user responding to posts. Your tone should be {tone.value}. 
                    Generate a natural, helpful response that adds value to the conversation. 
                    Do not be overly promotional. Base your response on the provided context."""
                },
                {
                    "role": "user",
                    "content": f"""
                    Context about my expertise: {campaign_context[:1000]}
                    
                    Post Title: {target_post.title}
                    Post Content: {target_post.content}
                    Subreddit: r/{target_post.subreddit}
                    
                    Generate a helpful response that:
                    1. Adds value to the conversation
                    2. Is natural and not overly promotional
                    3. Uses the {tone.value} tone
                    4. Is 1-3 paragraphs long
                    
                    Return a JSON object with:
                    - content (the response text)
                    - confidence (0.0 to 1.0 how confident you are this is a good response)
                    """
                }
            ]
            
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            return response["choices"][0]["message"]["content"]
            
        except Exception as e:
            self.logger.error(f"Error generating response content: {str(e)}")
            return None
    
    async def _post_response(
        self, 
        reddit_interactor: RedditInteractor, 
        planned_response: PlannedResponse, 
        target_post: TargetPost
    ) -> Optional[PostedResponse]:
        """Post a response to Reddit."""
        try:
            if planned_response.response_type == ResponseType.POST_COMMENT:
                # Comment on the post
                result = await reddit_interactor.add_comment_to_post(
                    target_post.reddit_post_id,
                    planned_response.response_content
                )
            else:
                # Reply to a comment
                result = await reddit_interactor.reply_to_comment(
                    target_post.reddit_comment_id,
                    planned_response.response_content
                )
            
            return PostedResponse(
                planned_response_id=planned_response.id,
                target_post_id=planned_response.target_post_id,
                reddit_comment_id=result["id"],
                reddit_permalink=result["permalink"],
                posted_content=planned_response.response_content,
                posting_successful=True
            )
            
        except Exception as e:
            self.logger.error(f"Error posting response: {str(e)}")
            return PostedResponse(
                planned_response_id=planned_response.id,
                target_post_id=planned_response.target_post_id,
                reddit_comment_id="",
                reddit_permalink="",
                posted_content=planned_response.response_content,
                posting_successful=False,
                error_message=str(e)
            )
    
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