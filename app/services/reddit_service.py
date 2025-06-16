"""
Reddit operations service.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Tuple, Optional

from app.clients.reddit_client import RedditClient
from app.services.llm_service import LLMService
from app.utils.text_processing import clean_text
from app.storage.json_storage import JsonStorage

logger = logging.getLogger(__name__)


class RedditService:
    """
    Service for all Reddit-related operations including
    subreddit discovery, post analysis, and response generation.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the Reddit service."""
        self.data_dir = data_dir
        self.llm_service = LLMService()
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
            # Clean content
            clean_content = clean_text(content)
            
            # Build prompt for topic extraction
            prompt = f"""
            Analyze the following text and extract 5-10 relevant topics that could be used 
            to find related subreddits on Reddit. Return the topics as a JSON array.
            
            Text: {clean_content}
            
            Return format: {{"topics": ["topic1", "topic2", ...]}}
            """
            
            # Get AI response
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                response_format="json"
            )
            
            topics = response.get("topics", [])
            
            # Save topics
            topics_data = {
                "extracted_topics": topics,
                "content_analyzed": clean_content[:200] + "..." if len(clean_content) > 200 else clean_content,
                "total_topics": len(topics),
                "organization_id": organization_id
            }
            self.json_storage.save_data("topics.json", topics_data)
            
            self.logger.info(f"Extracted {len(topics)} topics for org {organization_id}")
            
            return True, f"Extracted {len(topics)} topics", topics
            
        except Exception as e:
            self.logger.error(f"Error extracting topics for org {organization_id}: {str(e)}")
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
       
            headers = {"User-Agent": "Mozilla/5.0 Reddit Marketing Agent"}
            
            async with aiohttp.ClientSession() as session:
                # Create coroutine list directly, no create_task
                coroutines = [
                    self._search_subreddits_by_topic(topic, session, headers)
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
            self.json_storage.save_data("subreddits.json", subreddits_data)
            
            discovery_data = {
                "topics": topics,
                "relevant_subreddits": result_subreddits,
                "all_subreddits": filtered_subreddits
            }
            
            self.logger.info(f"Discovered {len(result_subreddits)} relevant subreddits for org {organization_id}")
            
            return True, f"Discovered {len(result_subreddits)} relevant subreddits", discovery_data
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits for org {organization_id}: {str(e)}")
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
            # Build prompt for subreddit ranking
            subreddit_list = []
            for name, info in subreddit_data.items():
                subreddit_list.append(f"{name}: {info['about'][:100]}")
            
            prompt = f"""
            Based on the following content, rank the subreddits by relevance and return the top 10 most relevant ones.
            
            Content: {content}
            
            Subreddits:
            {chr(10).join(subreddit_list)}
            
            Return format: {{"subreddits": ["subreddit1", "subreddit2", ...]}}
            """
            
            # Get AI response
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                response_format="json"
            )
            
            subreddits = response.get("subreddits", [])
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
            
            self.logger.info(f"Discovered {len(all_posts)} posts across {len(subreddits)} subreddits")
            
            return True, f"Discovered {len(all_posts)} posts", all_posts
            
        except Exception as e:
            self.logger.error(f"Error discovering posts: {str(e)}")
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
            # Build prompt for post relevance analysis
            prompt = f"""
            Analyze if this Reddit post is relevant for our marketing campaign and if we should respond.
            
            Campaign Context: {campaign_context[:1000]}
            
            Post Title: {post.get('title', '')}
            Post Content: {post.get('selftext', '')[:500]}
            Subreddit: r/{post.get('search_subreddit', '')}
            
            Analyze this post and return a JSON object with:
            - relevance_score (0.0 to 1.0)
            - relevance_reason (brief explanation)
            - should_respond (boolean)
            
            Return format: {{"relevance_score": 0.8, "relevance_reason": "...", "should_respond": true}}
            """
            
            # Get AI response
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                response_format="json"
            )
            
            self.logger.debug(f"Analyzed post relevance: {response.get('relevance_score', 0):.2f}")
            
            return True, "Post relevance analyzed", response
            
        except Exception as e:
            self.logger.error(f"Error analyzing post relevance: {str(e)}")
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
            # Build prompt for response generation
            prompt = f"""
            Generate a helpful Reddit response based on the following context and post.
            
            Context about my expertise: {campaign_context[:1000]}
            
            Post Title: {post.get('title', '')}
            Post Content: {post.get('selftext', '')}
            Subreddit: r/{post.get('search_subreddit', '')}
            
            Generate a response that:
            1. Adds value to the conversation
            2. Is natural and not overly promotional
            3. Uses a {tone} tone
            4. Is 1-3 paragraphs long
            
            Return a JSON object with:
            - content (the response text)
            - confidence (0.0 to 1.0 how confident you are this is a good response)
            
            Return format: {{"content": "...", "confidence": 0.8}}
            """
            
            # Get AI response
            response = await self.llm_service.generate_completion(
                prompt=prompt,
                response_format="json"
            )
            
            self.logger.info(f"Generated response with confidence: {response.get('confidence', 0):.2f}")
            
            return True, "Response generated successfully", response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
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
            
            self.logger.info(f"Posted response to {post_id}")
            
            return True, "Response posted successfully", result
            
        except Exception as e:
            self.logger.error(f"Error posting response to {post_id}: {str(e)}")
            return False, f"Error posting response: {str(e)}", {}