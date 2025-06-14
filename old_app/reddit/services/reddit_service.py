"""
Unified Reddit service combining all Reddit-related functionality.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Tuple, Optional

from shared.base.service_base import AsyncBaseService
from shared.base.json_storage_mixin import JsonStorageMixin
from shared.clients.reddit_client import RedditClient
from shared.llm.prompt_templates import PromptTemplates, PromptType
from services.llm.llm_service import ai_client
from rag.services.document_service import DocumentService
from rag.models import DocumentQuery


class RedditService(AsyncBaseService, JsonStorageMixin):
    """
    Unified service for all Reddit-related operations.
    Combines functionality from multiple Reddit modules.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the Reddit service."""
        super().__init__("RedditService", data_dir)
        
        # Initialize JSON files
        self._init_json_file("topics.json", [])
        self._init_json_file("subreddits.json", [])
        
        # Initialize document service
        self.document_service = DocumentService(data_dir)
        
        # Reddit client will be initialized per operation
        self._reddit_client = None
    
    async def cleanup(self):
        """Clean up resources."""
        if self._reddit_client:
            await self._reddit_client.cleanup()
            self._reddit_client = None
    
    def _get_reddit_client(self, credentials: Dict[str, str]) -> RedditClient:
        """Get or create Reddit client with credentials."""
        return RedditClient(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            username=credentials.get("username"),
            password=credentials.get("password"),
            data_dir=self.data_dir
        )
    
    # ========================================
    # TOPIC EXTRACTION AND SUBREDDIT DISCOVERY
    # ========================================
    
    async def extract_topics_from_content(
        self, 
        content: str, 
        organization_id: str
    ) -> Tuple[bool, str, List[str]]:
        """
        Extract topics from content using AI analysis.
        
        Args:
            content: Content to analyze
            organization_id: Organization ID for tracking
            
        Returns:
            Tuple of (success, message, topics)
        """
        try:
            # Build prompt using template
            messages = PromptTemplates.build_topic_extraction_prompt(content)
            
            # Get AI response
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            content_response = response["choices"][0]["message"]["content"]
            topics = content_response["topics"]
            
            # Save topics
            topics_data = {
                "extracted_topics": topics,
                "content_analyzed": content[:200] + "..." if len(content) > 200 else content,
                "total_topics": len(topics),
                "organization_id": organization_id
            }
            self._save_json("topics.json", topics_data)
            
            self.log_operation(
                "TOPIC_EXTRACTION",
                True,
                f"Extracted {len(topics)} topics",
                org_id=organization_id,
                topic_count=len(topics)
            )
            
            return True, f"Extracted {len(topics)} topics", topics
            
        except Exception as e:
            self.log_operation("TOPIC_EXTRACTION", False, str(e), org_id=organization_id)
            return False, f"Error extracting topics: {str(e)}", []
    
    async def discover_subreddits(
        self, 
        content: str, 
        organization_id: str,
        min_subscribers: int = 10000
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Discover relevant subreddits based on content analysis.
        
        Args:
            content: Content to analyze
            organization_id: Organization ID
            min_subscribers: Minimum subscriber count
            
        Returns:
            Tuple of (success, message, discovery_data)
        """
        try:
            # Extract topics first
            success, message, topics = await self.extract_topics_from_content(content, organization_id)
            if not success:
                return False, f"Topic extraction failed: {message}", {}
            
            # Search for subreddits related to each topic
            all_subreddits = {}
            
            import aiohttp
            headers = {"User-Agent": "Mozilla/5.0 Reddit Marketing Agent"}
            
            async with aiohttp.ClientSession() as session:
                # Search for subreddits for each topic
                for topic in topics:
                    try:
                        subreddit_data = await self._search_subreddits_by_topic(topic, session, headers)
                        all_subreddits.update(subreddit_data)
                    except Exception as e:
                        self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(e)}")
            
            # Filter subreddits by criteria
            filtered_subreddits = self._filter_subreddits_by_criteria(all_subreddits, min_subscribers)
            
            # Rank subreddits by relevance using AI
            relevant_subreddit_names = await self._rank_subreddits_by_relevance(content, filtered_subreddits)
            
            # Create final result
            result_subreddits = {}
            for name in relevant_subreddit_names:
                if name in filtered_subreddits:
                    result_subreddits[name] = filtered_subreddits[name]
            
            # Save results
            subreddits_data = {
                "relevant_subreddits": result_subreddits,
                "all_filtered_subreddits": filtered_subreddits,
                "total_relevant": len(result_subreddits),
                "total_filtered": len(filtered_subreddits),
                "min_subscribers": min_subscribers,
                "organization_id": organization_id
            }
            self._save_json("subreddits.json", subreddits_data)
            
            discovery_data = {
                "topics": topics,
                "relevant_subreddits": result_subreddits,
                "all_subreddits": filtered_subreddits
            }
            
            self.log_operation(
                "SUBREDDIT_DISCOVERY",
                True,
                f"Discovered {len(result_subreddits)} relevant subreddits",
                org_id=organization_id,
                relevant_count=len(result_subreddits),
                total_count=len(filtered_subreddits)
            )
            
            return True, f"Discovered {len(result_subreddits)} relevant subreddits", discovery_data
            
        except Exception as e:
            self.log_operation("SUBREDDIT_DISCOVERY", False, str(e), org_id=organization_id)
            return False, f"Error discovering subreddits: {str(e)}", {}
    
    async def _search_subreddits_by_topic(
        self, 
        topic: str, 
        session, 
        headers: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Search Reddit for subreddits related to a topic."""
        url = f"https://www.reddit.com/search.json?q={topic}"
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data["data"]["children"]
                    
                    subreddit_dict = {}
                    subreddit_names = set()
                    
                    # Collect unique subreddit names
                    for post in posts:
                        post_data = post["data"]
                        subreddit_name = post_data["subreddit"].strip()
                        subreddit_names.add(subreddit_name)
                    
                    # Get details for each subreddit
                    for name in subreddit_names:
                        try:
                            details = await self._get_subreddit_details(name, session, headers)
                            subreddit_dict[name] = details
                        except Exception as e:
                            self.logger.warning(f"Error getting details for r/{name}: {str(e)}")
                    
                    return subreddit_dict
                else:
                    return {}
        except Exception as e:
            self.logger.error(f"Error searching subreddits for topic '{topic}': {str(e)}")
            return {}
    
    async def _get_subreddit_details(
        self, 
        subreddit_name: str, 
        session, 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get details about a specific subreddit."""
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    about = data["data"].get("public_description", "") or data["data"].get("description", "")
                    subscribers = data["data"].get("subscribers", 0)
                    
                    return {
                        "about": about,
                        "subscribers": subscribers
                    }
                else:
                    return {"about": "", "subscribers": 0}
        except Exception:
            return {"about": "", "subscribers": 0}
    
    def _filter_subreddits_by_criteria(
        self, 
        subreddit_data: Dict[str, Dict[str, Any]], 
        min_subscribers: int
    ) -> Dict[str, Dict[str, Any]]:
        """Filter subreddits by criteria."""
        filtered_subreddits = {}
        
        for subreddit_name, info in subreddit_data.items():
            if info["about"] != "" and info["subscribers"] >= min_subscribers:
                filtered_subreddits[subreddit_name] = info
        
        return filtered_subreddits
    
    async def _rank_subreddits_by_relevance(
        self, 
        content: str, 
        subreddit_data: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Use AI to rank subreddits by relevance."""
        try:
            # Build prompt using template
            messages = PromptTemplates.build_subreddit_ranking_prompt(content, subreddit_data)
            
            # Get AI response
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            content_response = response["choices"][0]["message"]["content"]
            subreddits = content_response["subreddits"]
            
            return subreddits
            
        except Exception as e:
            self.logger.error(f"Error ranking subreddits: {str(e)}")
            # Fallback: return all subreddit names
            return list(subreddit_data.keys())
    
    # ========================================
    # POST DISCOVERY AND ANALYSIS
    # ========================================
    
    async def discover_posts(
        self, 
        subreddits: List[str],
        topics: List[str],
        reddit_credentials: Dict[str, str],
        max_posts_per_subreddit: int = 25,
        time_filter: str = "day"
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Discover relevant posts in target subreddits.
        
        Args:
            subreddits: List of subreddit names
            topics: List of topics to search for
            reddit_credentials: Reddit API credentials
            max_posts_per_subreddit: Maximum posts per subreddit
            time_filter: Time filter for posts
            
        Returns:
            Tuple of (success, message, posts)
        """
        try:
            reddit_client = self._get_reddit_client(reddit_credentials)
            
            all_posts = []
            
            async with reddit_client:
                # Search each subreddit for each topic
                for subreddit in subreddits:
                    for topic in topics[:3]:  # Limit to top 3 topics
                        try:
                            posts = await reddit_client.search_subreddit_posts(
                                subreddit=subreddit,
                                query=topic,
                                sort="new",
                                time_filter=time_filter,
                                limit=max_posts_per_subreddit
                            )
                            
                            # Add subreddit and topic context to posts
                            for post in posts:
                                post['search_subreddit'] = subreddit
                                post['search_topic'] = topic
                            
                            all_posts.extend(posts)
                            
                        except Exception as e:
                            self.logger.warning(f"Error searching r/{subreddit} for '{topic}': {str(e)}")
            
            self.log_operation(
                "POST_DISCOVERY",
                True,
                f"Discovered {len(all_posts)} posts",
                subreddit_count=len(subreddits),
                topic_count=len(topics),
                post_count=len(all_posts)
            )
            
            return True, f"Discovered {len(all_posts)} posts", all_posts
            
        except Exception as e:
            self.log_operation("POST_DISCOVERY", False, str(e))
            return False, f"Error discovering posts: {str(e)}", []
    
    async def analyze_post_relevance(
        self, 
        post: Dict[str, Any],
        campaign_context: str,
        organization_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Analyze if a post is relevant for the campaign.
        
        Args:
            post: Post data
            campaign_context: Campaign context from documents
            organization_id: Organization ID
            
        Returns:
            Tuple of (success, message, analysis)
        """
        try:
            # Build prompt using template
            messages = PromptTemplates.build_post_relevance_prompt(
                campaign_context=campaign_context,
                post_title=post.get('title', ''),
                post_content=post.get('selftext', ''),
                subreddit=post.get('search_subreddit', '')
            )
            
            # Get AI response
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            analysis = response["choices"][0]["message"]["content"]
            
            self.log_operation(
                "POST_RELEVANCE_ANALYSIS",
                True,
                f"Analyzed post relevance: {analysis['relevance_score']:.2f}",
                org_id=organization_id,
                post_id=post.get('id'),
                relevance_score=analysis['relevance_score']
            )
            
            return True, "Post relevance analyzed", analysis
            
        except Exception as e:
            self.log_operation("POST_RELEVANCE_ANALYSIS", False, str(e), org_id=organization_id)
            return False, f"Error analyzing post relevance: {str(e)}", {}
    
    # ========================================
    # RESPONSE GENERATION
    # ========================================
    
    async def generate_response(
        self, 
        post: Dict[str, Any],
        campaign_context: str,
        tone: str,
        organization_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate a response for a target post.
        
        Args:
            post: Post data
            campaign_context: Campaign context
            tone: Response tone
            organization_id: Organization ID
            
        Returns:
            Tuple of (success, message, response_data)
        """
        try:
            # Build prompt using template
            messages = PromptTemplates.build_response_generation_prompt(
                campaign_context=campaign_context,
                post_title=post.get('title', ''),
                post_content=post.get('selftext', ''),
                subreddit=post.get('search_subreddit', ''),
                tone=tone
            )
            
            # Get AI response
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            response_data = response["choices"][0]["message"]["content"]
            
            self.log_operation(
                "RESPONSE_GENERATION",
                True,
                f"Generated response with confidence: {response_data['confidence']:.2f}",
                org_id=organization_id,
                post_id=post.get('id'),
                confidence=response_data['confidence']
            )
            
            return True, "Response generated successfully", response_data
            
        except Exception as e:
            self.log_operation("RESPONSE_GENERATION", False, str(e), org_id=organization_id)
            return False, f"Error generating response: {str(e)}", {}
    
    # ========================================
    # RESPONSE POSTING
    # ========================================
    
    async def post_response(
        self, 
        post_id: str,
        response_content: str,
        reddit_credentials: Dict[str, str],
        response_type: str = "post_comment"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Post a response to Reddit.
        
        Args:
            post_id: Reddit post ID
            response_content: Response content
            reddit_credentials: Reddit credentials
            response_type: Type of response (post_comment or comment_reply)
            
        Returns:
            Tuple of (success, message, posted_response_data)
        """
        try:
            reddit_client = self._get_reddit_client(reddit_credentials)
            
            async with reddit_client:
                if response_type == "post_comment":
                    result = await reddit_client.add_comment_to_post(post_id, response_content)
                else:
                    result = await reddit_client.reply_to_comment(post_id, response_content)
            
            self.log_operation(
                "RESPONSE_POSTING",
                True,
                f"Posted response to {post_id}",
                post_id=post_id,
                response_id=result.get('id')
            )
            
            return True, "Response posted successfully", result
            
        except Exception as e:
            self.log_operation("RESPONSE_POSTING", False, str(e), post_id=post_id)
            return False, f"Error posting response: {str(e)}", {}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    async def get_campaign_context(
        self, 
        organization_id: str, 
        document_ids: List[str]
    ) -> str:
        """Get combined context from campaign documents."""
        try:
            contents = []
            
            for doc_id in document_ids:
                query = DocumentQuery(
                    query="",  # Empty query to get all content
                    organization_id=organization_id,
                    filters={"document_id": doc_id},
                    top_k=100  # Get all chunks
                )
                
                results = self.document_service.query_documents(query)
                
                # Combine all chunks for this document
                doc_content = "\n".join([doc.content for doc in results.documents])
                if doc_content.strip():
                    contents.append(doc_content)
            
            return "\n\n".join(contents)
            
        except Exception as e:
            self.logger.error(f"Error getting campaign context: {str(e)}")
            return ""