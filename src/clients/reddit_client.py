"""
Reddit API client for all Reddit operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional

import asyncpraw
from asyncpraw.models import Comment, Submission

logger = logging.getLogger(__name__)


class RedditClient:
    """Reddit API client for all Reddit operations."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """Initialize the Reddit client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        self.user_agent = f"python:reddit-marketing-agent:v1.0 (by /u/{username or 'anonymous'})"
        self._reddit_instance = None
        self.logger = logger
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_reddit()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def _initialize_reddit(self):
        """Initialize the Reddit API client."""
        if self._reddit_instance is None:
            if self.username and self.password:
                self._reddit_instance = asyncpraw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    username=self.username,
                    password=self.password,
                    user_agent=self.user_agent
                )
                self.logger.info(f"Initialized Reddit API client with user: {self.username}")
            else:
                self._reddit_instance = asyncpraw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                self.logger.info("Initialized Reddit API client in read-only mode")
    
    async def cleanup(self):
        """Clean up Reddit connection."""
        if self._reddit_instance:
            await self._reddit_instance.close()
            self._reddit_instance = None
            self.logger.info("Closed Reddit API client")
    
    async def search_subreddits(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Search for subreddits by name or topic."""
        await self._initialize_reddit()
        results = []
        
        try:
            search_generator = self._reddit_instance.subreddits.search(query, limit=limit)
            async for subreddit in search_generator:
                results.append({
                    "name": subreddit.display_name,
                    "subscribers": subreddit.subscribers,
                    "description": subreddit.public_description or subreddit.description
                })
            return results
        except Exception as e:
            self.logger.error(f"Error searching subreddits for '{query}': {str(e)}")
            return []
    
    async def get_subreddit_info(self, subreddit_name: str) -> Dict[str, Any]:
        """Get information about a specific subreddit."""
        await self._initialize_reddit()
        
        try:
            subreddit = await self._reddit_instance.subreddit(subreddit_name, fetch=True)
            return {
                "name": subreddit.display_name,
                "subscribers": subreddit.subscribers,
                "description": subreddit.public_description or subreddit.description,
                "created_utc": subreddit.created_utc,
                "over18": subreddit.over18,
                "url": subreddit.url
            }
        except Exception as e:
            self.logger.error(f"Error getting info for r/{subreddit_name}: {str(e)}")
            raise
    
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
            subreddit_obj = await self._reddit_instance.subreddit(subreddit)
            
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
                    "author": post.author.name if post.author else "[deleted]",
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "permalink": post.permalink,
                    "url": post.url,
                    "selftext": getattr(post, "selftext", ""),
                    "num_comments": post.num_comments,
                    "subreddit": subreddit
                }
                results.append(post_data)
                
                counter += 1
                if counter >= limit:
                    break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching for '{query}' in r/{subreddit}: {str(e)}")
            return []
    
    async def get_post_info(self, post_id: str) -> Dict[str, Any]:
        """Get information about a specific post."""
        await self._initialize_reddit()
        
        try:
            submission = await self._reddit_instance.submission(id=post_id)
            return {
                "id": submission.id,
                "title": submission.title,
                "content": getattr(submission, "selftext", ""),
                "author": submission.author.name if submission.author else "[deleted]",
                "subreddit": submission.subreddit.display_name,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "permalink": submission.permalink
            }
        except Exception as e:
            self.logger.error(f"Error getting post info for {post_id}: {str(e)}")
            raise
    
    async def get_post_comments(self, post_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all comments for a post."""
        await self._initialize_reddit()
        
        try:
            submission = await self._reddit_instance.submission(id=post_id)
            await submission.comments.replace_more(limit=0)  # Load all comments
            
            comments = []
            comment_queue = list(submission.comments)
            
            while comment_queue and (limit is None or len(comments) < limit):
                comment = comment_queue.pop(0)
                
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    comment_data = {
                        "id": comment.id,
                        "author": comment.author.name if comment.author else "[deleted]",
                        "body": comment.body,
                        "created_utc": comment.created_utc,
                        "permalink": comment.permalink,
                        "score": comment.score
                    }
                    comments.append(comment_data)
                
                # Add replies to queue
                if hasattr(comment, 'replies'):
                    comment_queue.extend(comment.replies)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error getting comments for post {post_id}: {str(e)}")
            return []
    
    async def get_comment_info(self, comment_id: str) -> Dict[str, Any]:
        """Get information about a specific comment."""
        await self._initialize_reddit()
        
        try:
            comment = await self._reddit_instance.comment(id=comment_id)
            return {
                "id": comment.id,
                "author": comment.author.name if comment.author else "[deleted]",
                "body": comment.body,
                "created_utc": comment.created_utc,
                "permalink": comment.permalink,
                "score": comment.score
            }
        except Exception as e:
            self.logger.error(f"Error getting comment info for {comment_id}: {str(e)}")
            raise
    
    async def add_comment_to_post(self, comment_text: str, post_id: Optional[str] = None, post_url:Optional[str] = None) -> Dict[str, Any]:
        """Add a comment to a Reddit post."""
        await self._initialize_reddit()
        
        if not self.username or not self.password:
            raise Exception("Authentication required to post comments")
        
        try:

            if post_id:
                submission = await self._reddit_instance.submission(id=post_id)
            elif post_url:
                submission = await self._reddit_instance.submission(url=post_url)
                
            comment = await submission.reply(comment_text)
            
            return {
                "id": comment.id,
                "author": self.username,
                "body": comment_text,
                "created_utc": comment.created_utc,
                "permalink": comment.permalink
            }
            
        except Exception as e:
            self.logger.error(f"Error adding comment to post {post_id}: {str(e)}")
            raise
    
    async def reply_to_comment(self, reply_text: str, comment_id: Optional[str] = None, comment_url: Optional[str] = None) -> Dict[str, Any]:
        """Reply to an existing Reddit comment."""
        await self._initialize_reddit()
        
        if not self.username or not self.password:
            raise Exception("Authentication required to post replies")
        
        try:
            if comment_id:
                comment = await self._reddit_instance.comment(id=comment_id)
            elif comment_url:
                comment = await self._reddit_instance.comment(url=comment_url)
            reply = await comment.reply(reply_text)
            
            return {
                "id": reply.id,
                "author": self.username,
                "body": reply_text,
                "created_utc": reply.created_utc,
                "permalink": reply.permalink
            }
            
        except Exception as e:
            self.logger.error(f"Error replying to comment {comment_id}: {str(e)}")
            raise
    
    async def get_comment_score(self, comment_id: str) -> int:
        """Get the current score of a comment."""
        await self._initialize_reddit()
        
        try:
            comment = await self._reddit_instance.comment(id=comment_id)
            return comment.score
        except Exception as e:
            self.logger.error(f"Error getting comment score for {comment_id}: {str(e)}")
            return 0
    
    async def get_post_score(self, post_id: str) -> int:
        """Get the current score of a post."""
        await self._initialize_reddit()
        
        try:
            submission = await self._reddit_instance.submission(id=post_id)
            return submission.score
        except Exception as e:
            self.logger.error(f"Error getting post score for {post_id}: {str(e)}")
            return 0