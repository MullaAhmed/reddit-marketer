"""
Reddit operations service - Focused on Reddit API interactions only.
"""

import asyncio
import logging
from typing import Dict, List, Any, Tuple, Optional

from app.clients.reddit_client import RedditClient
from app.storage.json_storage import JsonStorage

logger = logging.getLogger(__name__)


class RedditService:
    """
    Service for Reddit-related operations focused on Reddit API interactions.
    AI operations have been moved to LLMService for better separation of concerns.
    """
    
    def __init__(
        self,
        json_storage: JsonStorage,
        reddit_client: RedditClient
    ):
        """Initialize the Reddit service."""
        self.json_storage = json_storage
        self._reddit_client = reddit_client
        self.logger = logger
    
    async def cleanup(self):
        """Clean up resources."""
        if self._reddit_client:
            await self._reddit_client.cleanup()
            self._reddit_client = None
    
    # ========================================
    # SUBREDDIT DISCOVERY (Reddit API focused)
    # ========================================
    
    async def discover_subreddits_by_topics(
        self, 
        topics: List[str], 
        organization_id: str,
        min_subscribers: int = 10000
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Discover subreddits based on provided topics.
        
        Args:
            topics: List of topics to search for
            organization_id: Organization ID
            min_subscribers: Minimum subscriber count
            
        Returns:
            Tuple of (success, message, discovery_data)
        """
        try:
            if not topics:
                return False, "No topics provided", {}
            
            # Search for subreddits related to each topic
            all_subreddits = {}
       
            async with self._reddit_client: # Use the service's client as context manager
                coroutines = [
                    self._search_subreddits_by_topic(topic, self._reddit_client)
                    for topic in topics
                ]
                results = await asyncio.gather(*coroutines, return_exceptions=True)

                for topic, result in zip(topics, results):
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(result)}")
                    else:
                        all_subreddits.update(result)
            
            # Filter subreddits by criteria
            filtered_subreddits = self._filter_subreddits_by_criteria(all_subreddits, min_subscribers)
            
            # Save results
            subreddits_data = {
                "all_subreddits": filtered_subreddits,
                "total_found": len(filtered_subreddits),
                "min_subscribers": min_subscribers,
                "organization_id": organization_id,
                "topics_used": topics
            }
            self.json_storage.save_data("subreddits.json", subreddits_data)
            
            discovery_data = {
                "topics": topics,
                "all_subreddits": filtered_subreddits
            }
            
            self.logger.info(f"Discovered {len(filtered_subreddits)} subreddits for {len(topics)} topics")
            
            return True, f"Discovered {len(filtered_subreddits)} subreddits", discovery_data
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits for org {organization_id}: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", {}
    
    async def _search_subreddits_by_topic(
        self, 
        topic: str, 
        reddit_client: RedditClient
    ) -> Dict[str, Dict[str, Any]]:
        """Search Reddit for subreddits related to a topic."""
        try:
            # Assuming RedditClient has a search_subreddits method
            search_results = await reddit_client.search_subreddits(topic)
            subreddit_dict = {}
            for subreddit_name, details in search_results.items():
                try:
                    # Use RedditClient's get_subreddit_info
                    info = await reddit_client.get_subreddit_info(subreddit_name)
                    subreddit_dict[subreddit_name] = {
                        "about": info.get("description", ""),
                        "subscribers": info.get("subscribers", 0)
                    }
                except Exception as e:
                    self.logger.warning(f"Error getting details for r/{subreddit_name}: {str(e)}")
            return subreddit_dict
        except Exception as e:
            self.logger.error(f"Error searching subreddits for topic '{topic}': {str(e)}")
            return {}
    
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
            reddit_client = self._reddit_client
            
            all_posts = []
            
            async with reddit_client:
                # Search each subreddit for each topic
                for subreddit in subreddits:
                    for topic in topics:  # Removed slicing
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
            
            self.logger.info(f"Discovered {len(all_posts)} posts across {len(subreddits)} subreddits")
            
            return True, f"Discovered {len(all_posts)} posts", all_posts
            
        except Exception as e:
            self.logger.error(f"Error discovering posts: {str(e)}")
            return False, f"Error discovering posts: {str(e)}", []
    
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
            reddit_client = self._reddit_client
            
            async with reddit_client:
                if response_type == "post_comment":
                    result = await reddit_client.add_comment_to_post(post_id, response_content)
                else:
                    result = await reddit_client.reply_to_comment(post_id, response_content)
            
            self.logger.info(f"Posted response to {post_id}")
            
            return True, "Response posted successfully", result
            
        except Exception as e:
            self.logger.error(f"Error posting response to {post_id}: {str(e)}")
            return False, f"Error posting response: {str(e)}", {}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    async def get_subreddit_info(self, subreddit_name: str) -> Dict[str, Any]:
        """Get information about a specific subreddit."""
        try:
            info = await self._reddit_client.get_subreddit_info(subreddit_name)
            return {
                "name": subreddit_name,
                "subscribers": info.get("subscribers", 0),
                "description": info.get("description", ""),
                "success": True
            }
        except Exception as e:
            self.logger.error(f"Error getting subreddit info for r/{subreddit_name}: {str(e)}")
            return {
                "name": subreddit_name,
                "error": str(e),
                "success": False
            }
    
    async def search_subreddits(self, query: str, limit: int = 25) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Search for subreddits by name or topic using the Reddit client."""
        try:
            results = await self._reddit_client.search_subreddits(query, limit)
            formatted_results = []
            for name, info in results.items():
                formatted_results.append({
                    "name": name,
                    "subscribers": info.get("subscribers", 0),
                    "description": info.get("about", "")
                })
            return True, f"Found {len(formatted_results)} subreddits for '{query}'", formatted_results
        except Exception as e:
            self.logger.error(f"Error searching subreddits: {str(e)}")
            return False, f"Error searching subreddits: {str(e)}", []