"""
Reddit operations service - Focused on Reddit API interactions only.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Tuple, Optional

from app.clients.reddit_client import RedditClient
from app.utils.text_processing import clean_text
from app.storage.json_storage import JsonStorage

logger = logging.getLogger(__name__)


class RedditService:
    """
    Service for Reddit-related operations focused on Reddit API interactions.
    AI operations have been moved to LLMService for better separation of concerns.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the Reddit service."""
        self.data_dir = data_dir
        self.json_storage = JsonStorage(data_dir)
        self.logger = logger
        
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
    # SUBREDDIT DISCOVERY (Reddit API focused)
    # ========================================
    
    async def discover_subreddits(
        self, 
        content: str, 
        organization_id: str,
        min_subscribers: int = 10000
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Discover relevant subreddits based on content analysis.
        Note: This method now requires external topic extraction and ranking.
        
        Args:
            content: Content to analyze
            organization_id: Organization ID
            min_subscribers: Minimum subscriber count
            
        Returns:
            Tuple of (success, message, discovery_data)
        """
        try:
            # Note: Topic extraction should now be done by calling LLMService directly
            # This is a placeholder that shows the Reddit API focused operations
            
            # For now, we'll extract some basic keywords as topics
            # In practice, the calling service should provide topics from LLMService
            basic_topics = self._extract_basic_keywords(content)
            
            # Search for subreddits related to each topic
            all_subreddits = {}
       
            headers = {"User-Agent": "Mozilla/5.0 Reddit Marketing Agent"}
            
            async with aiohttp.ClientSession() as session:
                # Create coroutine list directly, no create_task
                coroutines = [
                    self._search_subreddits_by_topic(topic, session, headers)
                    for topic in basic_topics
                ]

                results = await asyncio.gather(*coroutines, return_exceptions=True)

                for topic, result in zip(basic_topics, results):
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(result)}")
                    else:
                        all_subreddits.update(result)
            
            # Filter subreddits by criteria
            filtered_subreddits = self._filter_subreddits_by_criteria(all_subreddits, min_subscribers)

            # Note: Ranking should now be done by calling LLMService directly
            # For now, return all filtered subreddits
            result_subreddits = filtered_subreddits
            
            # Save results
            subreddits_data = {
                "relevant_subreddits": result_subreddits,
                "all_filtered_subreddits": filtered_subreddits,
                "total_relevant": len(result_subreddits),
                "total_filtered": len(filtered_subreddits),
                "min_subscribers": min_subscribers,
                "organization_id": organization_id
            }
            self.json_storage.save_data("subreddits.json", subreddits_data)
            
            discovery_data = {
                "topics": basic_topics,
                "relevant_subreddits": result_subreddits,
                "all_subreddits": filtered_subreddits
            }
            
            self.logger.info(f"Discovered {len(result_subreddits)} relevant subreddits for org {organization_id}")
            
            return True, f"Discovered {len(result_subreddits)} relevant subreddits", discovery_data
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits for org {organization_id}: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", {}
    
    def _extract_basic_keywords(self, content: str) -> List[str]:
        """Extract basic keywords as fallback for topic extraction."""
        # Simple keyword extraction as fallback
        # In practice, LLMService should be used for topic extraction
        clean_content = clean_text(content)
        words = clean_content.lower().split()
        
        # Filter for longer words that might be topics
        keywords = [word for word in words if len(word) > 4 and word.isalpha()]
        
        # Return unique keywords, limited to 5
        return list(set(keywords))[:5]
    
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
            reddit_client = self._get_reddit_client(reddit_credentials)
            
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
        headers = {"User-Agent": "Mozilla/5.0 Reddit Marketing Agent"}
        
        async with aiohttp.ClientSession() as session:
            try:
                details = await self._get_subreddit_details(subreddit_name, session, headers)
                return {
                    "name": subreddit_name,
                    "subscribers": details.get("subscribers", 0),
                    "description": details.get("about", ""),
                    "success": True
                }
            except Exception as e:
                self.logger.error(f"Error getting subreddit info for r/{subreddit_name}: {str(e)}")
                return {
                    "name": subreddit_name,
                    "error": str(e),
                    "success": False
                }