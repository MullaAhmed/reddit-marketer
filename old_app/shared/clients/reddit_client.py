"""
Unified Reddit API client combining functionality from multiple Reddit modules.
"""

import asyncio
import logging
import random
import time
import re
from typing import Dict, List, Any, Union, Tuple, Optional

import asyncpraw
from asyncpraw.models import Comment, Submission
from asyncpraw.exceptions import RedditAPIException

from shared.base.service_base import AsyncBaseService


class RedditClient(AsyncBaseService):
    """
    Unified Reddit API client for all Reddit operations.
    Combines functionality from reddit_interactor and reddit_post_finder.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str = None,
        password: str = None,
        user_agent: str = None,
        rate_limit_requests: int = 30,
        rate_limit_period: int = 60,
        max_retries: int = 3,
        retry_base_delay: float = 2.0,
        data_dir: str = "data"
    ):
        """Initialize the unified Reddit client."""
        super().__init__("RedditClient", data_dir)
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        self.user_agent = user_agent or (
            f"python:unified-reddit-client:v1.0 (by /u/{username or 'anonymous'})"
        )
        
        # Rate limiting configuration
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        
        # Track request timestamps for rate limiting
        self.request_timestamps = []
        
        # Reddit instance
        self.reddit = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_reddit()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def cleanup(self):
        """Clean up Reddit connection."""
        if self.reddit:
            await self.reddit.close()
            self.reddit = None
            self.logger.info("Closed Reddit API client")
    
    async def _initialize_reddit(self):
        """Initialize the Reddit API client."""
        if self.reddit is None:
            if self.username and self.password:
                self.reddit = asyncpraw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    username=self.username,
                    password=self.password,
                    user_agent=self.user_agent
                )
                self.logger.info(f"Initialized Reddit API client with user: {self.username}")
            else:
                self.reddit = asyncpraw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.logger.info("Initialized Reddit API client in read-only mode")
    
    async def _enforce_rate_limits(self):
        """Enforce rate limits by waiting if necessary."""
        now = time.time()
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < self.rate_limit_period
        ]
        
        # Wait if rate limit reached
        if len(self.request_timestamps) >= self.rate_limit_requests:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = self.rate_limit_period - (now - oldest_timestamp)
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
                await asyncio.sleep(wait_time)
        
        # Add random delay to avoid bursts
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Record timestamp
        self.request_timestamps.append(time.time())
    
    async def _execute_with_retry(self, coroutine_func, *args, **kwargs):
        """Execute coroutine with retry logic."""
        for retry in range(self.max_retries + 1):
            try:
                await self._enforce_rate_limits()
                return await coroutine_func(*args, **kwargs)
                
            except RedditAPIException as e:
                if any(error.error_type == "RATELIMIT" for error in e.items):
                    wait_time = self.retry_base_delay * (2 ** retry)
                    for error in e.items:
                        if error.error_type == "RATELIMIT" and "minute" in error.message:
                            try:
                                minutes = int(''.join(filter(str.isdigit, error.message)))
                                wait_time = minutes * 60
                            except ValueError:
                                pass
                    
                    self.logger.warning(f"Rate limited by Reddit. Waiting {wait_time:.2f} seconds.")
                    await asyncio.sleep(wait_time)
                    continue
                
                elif retry < self.max_retries:
                    wait_time = self.retry_base_delay * (2 ** retry)
                    self.logger.warning(f"Reddit API error: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Max retries reached: {str(e)}")
                    raise
                    
            except Exception as e:
                if retry < self.max_retries:
                    wait_time = self.retry_base_delay * (2 ** retry)
                    self.logger.warning(f"Error: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Max retries reached: {str(e)}")
                    raise
        
        raise Exception(f"Failed after {self.max_retries} retries")
    
    def _extract_id_from_url(self, url: str, id_type: str = "post") -> str:
        """Extract Reddit ID from URL."""
        if id_type == "post":
            pattern = r'reddit\.com(?:/r/[^/]+)?/comments/([a-zA-Z0-9]+)'
        else:  # comment
            pattern = r'reddit\.com(?:/r/[^/]+)?/comments/[a-zA-Z0-9]+/[^/]*/comment/([a-zA-Z0-9]+)'
        
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid Reddit {id_type} URL: {url}")
    
    def _get_id_or_extract_from_url(self, id_or_url: str, id_type: str = "post") -> str:
        """Get ID directly or extract from URL."""
        # Check if it's already an ID
        if (id_type == "post" and (len(id_or_url) == 6 or id_or_url.startswith('t3_'))) or \
           (id_type == "comment" and (len(id_or_url) == 7 or id_or_url.startswith('t1_'))):
            return id_or_url
        
        # Try to extract from URL
        if id_or_url.startswith(('http://', 'https://')):
            return self._extract_id_from_url(id_or_url, id_type)
        
        # Assume it's an ID
        return id_or_url
    
    async def _get_author_info(self, item: Union[Submission, Comment]) -> Dict[str, Any]:
        """Extract author information."""
        if not item.author:
            return {"name": "[deleted]", "is_deleted": True}
        
        return {
            "name": item.author.name,
            "id": getattr(item.author, "id", None),
            "is_gold": getattr(item.author, "is_gold", None),
            "is_mod": getattr(item.author, "is_mod", None),
            "karma": {
                "comment": getattr(item.author, "comment_karma", None),
                "link": getattr(item.author, "link_karma", None)
            }
        }
    
    # ========================================
    # POST AND COMMENT READING
    # ========================================
    
    async def get_post_comments(
        self, 
        post_id_or_url: str, 
        sort: str = "top", 
        limit: int = None
    ) -> Dict[str, Any]:
        """Get a Reddit post with its comments."""
        await self._initialize_reddit()
        
        try:
            post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
            if post_id.startswith('t3_'):
                post_id = post_id[3:]
            
            async def process_comment(comment):
                comment_data = {
                    "id": comment.id,
                    "author": await self._get_author_info(comment),
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "permalink": comment.permalink,
                    "is_submitter": comment.is_submitter,
                    "replies": []
                }
                
                if hasattr(comment, "replies") and comment.replies:
                    if hasattr(comment.replies, "replace_more"):
                        await comment.replies.replace_more(limit=None)
                    
                    async for reply in comment.replies:
                        reply_data = await process_comment(reply)
                        comment_data["replies"].append(reply_data)
                
                return comment_data
            
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=post_id)
            )
            
            post_data = {
                "id": submission.id,
                "title": submission.title,
                "author": await self._get_author_info(submission),
                "created_utc": submission.created_utc,
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "permalink": submission.permalink,
                "url": submission.url,
                "selftext": submission.selftext,
                "num_comments": submission.num_comments,
                "comments": []
            }
            
            # Set sort order
            submission.comment_sort = sort
            
            # Replace MoreComments
            await submission.comments.replace_more(limit=limit)
            
            # Process comments
            async for comment in submission.comments:
                comment_data = await process_comment(comment)
                post_data["comments"].append(comment_data)
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id_or_url}: {str(e)}")
            raise
    
    # ========================================
    # POST SEARCHING
    # ========================================
    
    async def search_subreddit_posts(
        self, 
        subreddit: str, 
        query: str, 
        sort: str = "relevance",
        time_filter: str = "all", 
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for posts in a subreddit."""
        await self._initialize_reddit()
        
        try:
            results = []
            
            subreddit_obj = await self._execute_with_retry(
                lambda: self.reddit.subreddit(subreddit)
            )
            
            search_results = subreddit_obj.search(
                query, 
                sort=sort, 
                time_filter=time_filter
            )
            
            counter = 0
            async for post in search_results:
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "author": await self._get_author_info(post),
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "permalink": post.permalink,
                    "url": post.url,
                    "selftext": getattr(post, "selftext", ""),
                    "num_comments": post.num_comments
                }
                
                results.append(post_data)
                
                counter += 1
                if counter >= limit:
                    break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching for '{query}' in r/{subreddit}: {str(e)}")
            raise
    
    async def search_multiple_subreddits(
        self, 
        subreddits: List[str], 
        query: str,
        sort: str = "relevance", 
        time_filter: str = "all", 
        limit: int = 25
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search for the same query across multiple subreddits."""
        results = {}
        tasks = []
        
        for subreddit in subreddits:
            task = asyncio.create_task(
                self.search_subreddit_posts(subreddit, query, sort, time_filter, limit)
            )
            tasks.append((subreddit, task))
        
        for subreddit, task in tasks:
            try:
                result = await task
                results[subreddit] = result
            except Exception as e:
                self.logger.error(f"Error processing search in r/{subreddit}: {str(e)}")
                results[subreddit] = {"error": str(e)}
        
        return results
    
    # ========================================
    # POSTING AND INTERACTION
    # ========================================
    
    async def add_comment_to_post(
        self, 
        post_id_or_url: str, 
        comment_text: str
    ) -> Dict[str, Any]:
        """Add a comment to a Reddit post."""
        await self._initialize_reddit()
        
        if not self.username or not self.password:
            raise Exception("Authentication required to post comments")
        
        try:
            post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
            if post_id.startswith('t3_'):
                post_id = post_id[3:]
            
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=post_id)
            )
            
            comment = await self._execute_with_retry(
                lambda: submission.reply(comment_text)
            )
            
            return {
                "id": comment.id,
                "author": self.username,
                "body": comment_text,
                "created_utc": comment.created_utc,
                "permalink": comment.permalink
            }
            
        except Exception as e:
            self.logger.error(f"Error adding comment to post {post_id_or_url}: {str(e)}")
            raise
    
    async def reply_to_comment(
        self, 
        comment_id_or_url: str, 
        reply_text: str
    ) -> Dict[str, Any]:
        """Reply to an existing Reddit comment."""
        await self._initialize_reddit()
        
        if not self.username or not self.password:
            raise Exception("Authentication required to post replies")
        
        try:
            comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
            if comment_id.startswith('t1_'):
                comment_id = comment_id[3:]
            
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            reply = await self._execute_with_retry(
                lambda: comment.reply(reply_text)
            )
            
            return {
                "id": reply.id,
                "author": self.username,
                "body": reply_text,
                "created_utc": reply.created_utc,
                "permalink": reply.permalink
            }
            
        except Exception as e:
            self.logger.error(f"Error replying to comment {comment_id_or_url}: {str(e)}")
            raise
    
    # ========================================
    # BATCH OPERATIONS
    # ========================================
    
    async def batch_get_post_comments(
        self, 
        post_ids_or_urls: List[str], 
        sort: str = "top", 
        limit: int = None
    ) -> Dict[str, Any]:
        """Get multiple Reddit posts with their comments in parallel."""
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        for post_id_or_url in post_ids_or_urls:
            task = asyncio.create_task(
                self.get_post_comments(post_id_or_url, sort, limit)
            )
            tasks.append((post_id_or_url, task))
        
        for post_id_or_url, task in tasks:
            try:
                result = await task
                post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
                if post_id.startswith('t3_'):
                    post_id = post_id[3:]
                results[post_id] = result
            except Exception as e:
                self.logger.error(f"Error processing {post_id_or_url}: {str(e)}")
                results[post_id_or_url] = {"error": str(e)}
        
        return results
    
    async def batch_add_comments_to_posts(
        self, 
        post_data_pairs: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Add comments to multiple Reddit posts in parallel."""
        await self._initialize_reddit()
        
        if not self.username or not self.password:
            raise Exception("Authentication required to post comments")
        
        results = {}
        tasks = []
        
        for post_id_or_url, comment_text in post_data_pairs:
            task = asyncio.create_task(
                self.add_comment_to_post(post_id_or_url, comment_text)
            )
            tasks.append((post_id_or_url, task))
        
        for post_id_or_url, task in tasks:
            try:
                result = await task
                post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
                if post_id.startswith('t3_'):
                    post_id = post_id[3:]
                results[post_id] = result
            except Exception as e:
                self.logger.error(f"Error adding comment to {post_id_or_url}: {str(e)}")
                results[post_id_or_url] = {"error": str(e)}
        
        return results