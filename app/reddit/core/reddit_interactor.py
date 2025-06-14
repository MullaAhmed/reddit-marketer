"""
RedditInteractor - A module for interacting with Reddit posts and comments.
Supports reading comments, posting comments, replying to comments, and more.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Any, Union, Tuple

# Using ASYNC-PRAW for asynchronous Reddit API interactions
import asyncpraw
from asyncpraw.models import Comment, Submission
from asyncpraw.exceptions import RedditAPIException


class RedditInteractor:
    """
    A class for interacting with Reddit posts and comments asynchronously.
    Supports reading comments, posting comments, replying to comments, and more.
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
        log_level: int = logging.INFO
    ):
        """
        Initialize the RedditInteractor with Reddit API credentials.
        
        Args:
            client_id (str): Reddit API client ID
            client_secret (str): Reddit API client secret
            username (str, optional): Reddit username for authenticated actions
            password (str, optional): Reddit password for authenticated actions
            user_agent (str, optional): Custom User-Agent for API requests
            rate_limit_requests (int): Maximum number of requests in rate limit period
            rate_limit_period (int): Rate limit period in seconds
            max_retries (int): Maximum number of retry attempts for failed requests
            retry_base_delay (float): Base delay for retry backoff in seconds
            log_level (int): Logging level for the interactor
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        
        # Generate a default user agent if none provided
        self.user_agent = user_agent or (
            f"python:async-reddit-interactor:v1.0 (by /u/{username or 'anonymous'})"
        )
        
        # Configuration for rate limiting and retries
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        
        # Set up logging
        self.logger = logging.getLogger("RedditInteractor")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Track request timestamps for rate limiting
        self.request_timestamps = []
        
        # Initialize the Reddit instance
        self.reddit = None
        
    async def _initialize_reddit(self):
        """
        Initialize the Reddit API client if not already initialized.
        """
        if self.reddit is None:
            # Setup with or without authentication based on provided credentials
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
        """
        Enforce rate limits by waiting if necessary.
        """
        now = time.time()
        
        # Remove timestamps older than the rate limit period
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < self.rate_limit_period]
        
        # If we've reached the rate limit, wait until we can make another request
        if len(self.request_timestamps) >= self.rate_limit_requests:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = self.rate_limit_period - (now - oldest_timestamp)
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
                await asyncio.sleep(wait_time)
        
        # Add a small random delay to avoid request bursts
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Record the current timestamp for rate limiting
        self.request_timestamps.append(time.time())
    
    async def _execute_with_retry(self, coroutine_func, *args, **kwargs):
        """
        Execute a coroutine function with retry logic.
        
        Args:
            coroutine_func: The async function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the coroutine function
            
        Raises:
            Exception: If all retries fail
        """
        for retry in range(self.max_retries + 1):
            try:
                # Enforce rate limits before making the request
                await self._enforce_rate_limits()
                
                # Execute the coroutine
                return await coroutine_func(*args, **kwargs)
                
            except RedditAPIException as e:
                # Handle specific Reddit API exceptions
                if any(error.error_type == "RATELIMIT" for error in e.items):
                    # Parse the wait time from the error message if possible
                    wait_time = self.retry_base_delay * (2 ** retry)
                    for error in e.items:
                        if error.error_type == "RATELIMIT" and "minute" in error.message:
                            try:
                                # Try to extract minutes from error message
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
        
        # Should never reach here, but just in case
        raise Exception(f"Failed after {self.max_retries} retries")
    
    def _extract_post_id_from_url(self, url: str) -> str:
        """
        Extract a post ID from a Reddit URL.
        
        Args:
            url (str): Reddit post URL
            
        Returns:
            str: Post ID
            
        Raises:
            ValueError: If the URL is not a valid Reddit post URL
        """
        import re
        
        # Pattern to match Reddit post URLs
        # This handles URLs like:
        # - https://www.reddit.com/r/subreddit/comments/POST_ID/...
        # - https://old.reddit.com/r/subreddit/comments/POST_ID/...
        # - https://reddit.com/r/subreddit/comments/POST_ID/...
        # - https://www.reddit.com/comments/POST_ID/...
        pattern = r'reddit\.com(?:/r/[^/]+)?/comments/([a-zA-Z0-9]+)'
        
        # Search for the pattern in the URL
        match = re.search(pattern, url)
        
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid Reddit post URL: {url}")
    
    def _extract_comment_id_from_url(self, url: str) -> str:
        """
        Extract a comment ID from a Reddit URL.
        
        Args:
            url (str): Reddit comment URL
            
        Returns:
            str: Comment ID
            
        Raises:
            ValueError: If the URL is not a valid Reddit comment URL
        """
        import re
        
        # Pattern to match Reddit comment URLs
        # This handles URLs like:
        # - https://www.reddit.com/r/subreddit/comments/POST_ID/.../comment/COMMENT_ID/...
        pattern = r'reddit\.com(?:/r/[^/]+)?/comments/[a-zA-Z0-9]+/[^/]*/comment/([a-zA-Z0-9]+)'
        
        # Search for the pattern in the URL
        match = re.search(pattern, url)
        
        if match:
            return match.group(1)
        else:
            raise ValueError(f"Invalid Reddit comment URL: {url}")
            
    def _get_id_or_extract_from_url(self, id_or_url: str, id_type: str = "post") -> str:
        """
        Get ID directly or extract it from URL.
        
        Args:
            id_or_url (str): A Reddit post/comment ID or URL
            id_type (str): Type of ID to extract ('post' or 'comment')
            
        Returns:
            str: The extracted ID
        """
        # Check if it's already a post/comment ID or a prefixed ID
        if (id_type == "post" and (len(id_or_url) == 6 or id_or_url.startswith('t3_'))) or \
           (id_type == "comment" and (len(id_or_url) == 7 or id_or_url.startswith('t1_'))):
            return id_or_url
        
        # If it looks like a URL, try to extract the ID
        if id_or_url.startswith(('http://', 'https://')):
            try:
                if id_type == "post":
                    return self._extract_post_id_from_url(id_or_url)
                else:  # comment
                    return self._extract_comment_id_from_url(id_or_url)
            except ValueError as e:
                self.logger.error(str(e))
                raise
        
        # If we can't determine what it is, assume it's an ID
        return id_or_url
    
    async def _get_author_info(self, item: Union[Submission, Comment]) -> Dict[str, Any]:
        """
        Extract author information from a Reddit item.
        
        Args:
            item: A Reddit Submission or Comment object
            
        Returns:
            dict: Author information or None if deleted/suspended
        """
        if not item.author:
            return {
                "name": "[deleted]",
                "is_deleted": True
            }
        
        return {
            "name": item.author.name,
            "id": item.author.id if hasattr(item.author, "id") else None,
            "is_gold": item.author.is_gold if hasattr(item.author, "is_gold") else None,
            "is_mod": item.author.is_mod if hasattr(item.author, "is_mod") else None,
            "karma": {
                "comment": item.author.comment_karma if hasattr(item.author, "comment_karma") else None,
                "link": item.author.link_karma if hasattr(item.author, "link_karma") else None
            }
        }
    
    async def get_post_comments(self, post_id_or_url: str, sort: str = "top", limit: int = None) -> Dict[str, Any]:
        """
        Get a Reddit post with its comments.
        
        Args:
            post_id_or_url (str): Reddit post ID or URL
            sort (str): Comment sort order ('top', 'new', 'controversial', 'old', 'qa')
            limit (int): Max number of MoreComments to replace, or None for all
            
        Returns:
            dict: Post data with comments
            
        Raises:
            Exception: If fetching comments fails
        """
        await self._initialize_reddit()
        
        try:
            # Extract the post ID from URL if needed
            post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
            
            # Clean up the post ID
            if post_id.startswith('t3_'):
                post_id = post_id[3:]
                
            # Define a recursive function to process comments and their replies
            async def process_comment(comment):
                # Get basic comment data
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
                
                # Process replies if any
                if hasattr(comment, "replies") and comment.replies:
                    # Replace MoreComments objects with actual comments
                    if hasattr(comment.replies, "replace_more"):
                        await comment.replies.replace_more(limit=None)
                    
                    # Process all reply comments
                    async for reply in comment.replies:
                        reply_data = await process_comment(reply)
                        comment_data["replies"].append(reply_data)
                
                return comment_data
            
            # Get the submission
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=post_id)
            )
            
            # Get basic post data
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
            
            # Sort comments as requested
            if sort == "top":
                submission.comment_sort = "top"
            elif sort == "new":
                submission.comment_sort = "new"
            elif sort == "controversial":
                submission.comment_sort = "controversial"
            elif sort == "old":
                submission.comment_sort = "old"
            elif sort == "qa":
                submission.comment_sort = "qa"
            
            # Replace MoreComments objects with actual comments
            await submission.comments.replace_more(limit=limit)
            
            # Process all top-level comments
            async for comment in submission.comments:
                comment_data = await process_comment(comment)
                post_data["comments"].append(comment_data)
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id_or_url}: {str(e)}")
            raise
    
    
    async def add_comment_to_post(self, post_id_or_url: str, comment_text: str) -> Dict[str, Any]:
        """
        Add a new comment to a Reddit post.
        
        Args:
            post_id_or_url (str): Reddit post ID or URL
            comment_text (str): Text content of the comment
            
        Returns:
            dict: Information about the posted comment
            
        Raises:
            Exception: If user is not authenticated or if comment posting fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to post comments")
        
        try:
            # Extract the post ID from URL if needed
            post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
            
            # Clean up the post ID
            if post_id.startswith('t3_'):
                post_id = post_id[3:]
                
            # Get the submission
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=post_id)
            )
            
            # Add the comment
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
    
    async def reply_to_comment(self, comment_id_or_url: str, reply_text: str) -> Dict[str, Any]:
        """
        Reply to an existing Reddit comment.
        
        Args:
            comment_id_or_url (str): Comment ID or URL
            reply_text (str): Text content of the reply
            
        Returns:
            dict: Information about the posted reply
            
        Raises:
            Exception: If user is not authenticated or if reply posting fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to post replies")
        
        try:
            # Extract the comment ID from URL if needed
            comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
            
            # Clean up the comment ID
            if comment_id.startswith('t1_'):
                comment_id = comment_id[3:]
                
            # Get the comment
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            # Add the reply
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
    
    async def edit_comment(self, comment_id_or_url: str, new_text: str) -> Dict[str, Any]:
        """
        Edit an existing comment made by the authenticated user.
        
        Args:
            comment_id_or_url (str): Comment ID or URL
            new_text (str): New text content for the comment
            
        Returns:
            dict: Information about the edited comment
            
        Raises:
            Exception: If user is not authenticated or if editing fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to edit comments")
        
        try:
            # Extract the comment ID from URL if needed
            comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
            
            # Clean up the comment ID
            if comment_id.startswith('t1_'):
                comment_id = comment_id[3:]
                
            # Get the comment
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            # Verify the comment belongs to the user
            if comment.author and comment.author.name != self.username:
                raise Exception("Cannot edit a comment that doesn't belong to you")
            
            # Edit the comment
            edited_comment = await self._execute_with_retry(
                lambda: comment.edit(new_text)
            )
            
            return {
                "id": edited_comment.id,
                "author": self.username,
                "body": new_text,
                "edited": True,
                "created_utc": edited_comment.created_utc,
                "permalink": edited_comment.permalink
            }
            
        except Exception as e:
            self.logger.error(f"Error editing comment {comment_id_or_url}: {str(e)}")
            raise
    
    async def delete_comment(self, comment_id_or_url: str) -> bool:
        """
        Delete a comment made by the authenticated user.
        
        Args:
            comment_id_or_url (str): Comment ID or URL
            
        Returns:
            bool: True if the comment was successfully deleted
            
        Raises:
            Exception: If user is not authenticated or if deletion fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to delete comments")
        
        try:
            # Extract the comment ID from URL if needed
            comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
            
            # Clean up the comment ID
            if comment_id.startswith('t1_'):
                comment_id = comment_id[3:]
                
            # Get the comment
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            # Verify the comment belongs to the user
            if comment.author and comment.author.name != self.username:
                raise Exception("Cannot delete a comment that doesn't belong to you")
            
            # Delete the comment
            await self._execute_with_retry(
                lambda: comment.delete()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting comment {comment_id_or_url}: {str(e)}")
            raise
    
    async def vote_on_comment(self, comment_id_or_url: str, direction: int) -> bool:
        """
        Vote on a comment (upvote, downvote, or clear vote).
        
        Args:
            comment_id_or_url (str): Comment ID or URL
            direction (int): 1 for upvote, -1 for downvote, 0 to clear vote
            
        Returns:
            bool: True if the vote was successful
            
        Raises:
            Exception: If user is not authenticated or if voting fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to vote")
        
        try:
            # Extract the comment ID from URL if needed
            comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
            
            # Clean up the comment ID
            if comment_id.startswith('t1_'):
                comment_id = comment_id[3:]
                
            # Get the comment
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            # Apply the vote
            if direction == 1:
                await self._execute_with_retry(
                    lambda: comment.upvote()
                )
            elif direction == -1:
                await self._execute_with_retry(
                    lambda: comment.downvote()
                )
            else:
                await self._execute_with_retry(
                    lambda: comment.clear_vote()
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error voting on comment {comment_id_or_url}: {str(e)}")
            raise
    
    async def vote_on_post(self, post_id_or_url: str, direction: int) -> bool:
        """
        Vote on a post (upvote, downvote, or clear vote).
        
        Args:
            post_id_or_url (str): Post ID or URL
            direction (int): 1 for upvote, -1 for downvote, 0 to clear vote
            
        Returns:
            bool: True if the vote was successful
            
        Raises:
            Exception: If user is not authenticated or if voting fails
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to vote")
        
        try:
            # Extract the post ID from URL if needed
            post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
            
            # Clean up the post ID
            if post_id.startswith('t3_'):
                post_id = post_id[3:]
                
            # Get the submission
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=post_id)
            )
            
            # Apply the vote
            if direction == 1:
                await self._execute_with_retry(
                    lambda: submission.upvote()
                )
            elif direction == -1:
                await self._execute_with_retry(
                    lambda: submission.downvote()
                )
            else:
                await self._execute_with_retry(
                    lambda: submission.clear_vote()
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error voting on post {post_id_or_url}: {str(e)}")
            raise
    
    async def batch_get_post_comments(self, post_ids_or_urls: List[str], sort: str = "top", limit: int = None) -> Dict[str, Any]:
        """
        Get multiple Reddit posts with their comments in parallel.
        
        Args:
            post_ids_or_urls (List[str]): List of Reddit post IDs or URLs
            sort (str): Comment sort order ('top', 'new', 'controversial', 'old', 'qa')
            limit (int): Max number of MoreComments to replace, or None for all
            
        Returns:
            dict: Dictionary mapping post IDs to their post data with comments
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each post ID/URL
        for post_id_or_url in post_ids_or_urls:
            task = asyncio.create_task(self.get_post_comments(post_id_or_url, sort, limit))
            tasks.append((post_id_or_url, task))
        
        # Execute all tasks concurrently and gather results
        for post_id_or_url, task in tasks:
            try:
                result = await task
                # Use the clean post ID as the key
                post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
                if post_id.startswith('t3_'):
                    post_id = post_id[3:]
                results[post_id] = result
            except Exception as e:
                self.logger.error(f"Error processing {post_id_or_url}: {str(e)}")
                results[post_id_or_url] = {"error": str(e)}
        
        return results

    async def batch_add_comments_to_posts(self, post_data_pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Add comments to multiple Reddit posts in parallel.
        
        Args:
            post_data_pairs (List[Tuple[str, str]]): List of (post_id_or_url, comment_text) tuples
            
        Returns:
            dict: Dictionary mapping post IDs to information about the posted comments
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to post comments")
        
        results = {}
        tasks = []
        
        # Create a task for each post/comment pair
        for post_id_or_url, comment_text in post_data_pairs:
            task = asyncio.create_task(self.add_comment_to_post(post_id_or_url, comment_text))
            tasks.append((post_id_or_url, task))
        
        # Execute all tasks concurrently and gather results
        for post_id_or_url, task in tasks:
            try:
                result = await task
                # Use the clean post ID as the key
                post_id = self._get_id_or_extract_from_url(post_id_or_url, "post")
                if post_id.startswith('t3_'):
                    post_id = post_id[3:]
                results[post_id] = result
            except Exception as e:
                self.logger.error(f"Error adding comment to {post_id_or_url}: {str(e)}")
                results[post_id_or_url] = {"error": str(e)}
        
        return results

    async def batch_reply_to_comments(self, comment_data_pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Reply to multiple Reddit comments in parallel.
        
        Args:
            comment_data_pairs (List[Tuple[str, str]]): List of (comment_id_or_url, reply_text) tuples
            
        Returns:
            dict: Dictionary mapping comment IDs to information about the posted replies
        """
        await self._initialize_reddit()
        
        # Check if authenticated
        if not self.username or not self.password:
            raise Exception("Authentication required to post replies")
        
        results = {}
        tasks = []
        
        # Create a task for each comment/reply pair
        for comment_id_or_url, reply_text in comment_data_pairs:
            task = asyncio.create_task(self.reply_to_comment(comment_id_or_url, reply_text))
            tasks.append((comment_id_or_url, task))
        
        # Execute all tasks concurrently and gather results
        for comment_id_or_url, task in tasks:
            try:
                result = await task
                # Use the clean comment ID as the key
                comment_id = self._get_id_or_extract_from_url(comment_id_or_url, "comment")
                if comment_id.startswith('t1_'):
                    comment_id = comment_id[3:]
                results[comment_id] = result
            except Exception as e:
                self.logger.error(f"Error replying to {comment_id_or_url}: {str(e)}")
                results[comment_id_or_url] = {"error": str(e)}
        
        return results
    
    async def close(self):
        """
        Close the Reddit instance and any open connections.
        """
        if self.reddit:
            await self.reddit.close()
            self.reddit = None
            self.logger.info("Closed Reddit API client")



if __name__ == "__main__":
    # Example usage:
    async def main():
        # Initialize the interactor with your Reddit API credentials
        reddit_interactor = RedditInteractor(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            username="YOUR_USERNAME",  # Optional, but required for posting
            password="YOUR_PASSWORD",   # Optional, but required for posting
            user_agent="script:async-reddit-interactor:v1.0 (by /u/YOUR_USERNAME)"
        )
        
        try:
            # Example 1: Get comments from a post using URL
            post_url = "https://www.reddit.com/r/python/comments/abc123/sample_post_title/"
            post_data = await reddit_interactor.get_post_comments(post_url)
            print(f"Found {len(post_data['comments'])} comments for post: {post_data['title']}")
            
            # Example 2: Add a comment to a post (requires authentication)
            if reddit_interactor.username:
                comment_result = await reddit_interactor.add_comment_to_post(
                    post_url, 
                    "This is a test comment from the RedditInteractor!"
                )
                print(f"Added comment with ID: {comment_result['id']}")
                
                # Example 3: Reply to a comment using the comment ID
                comment_id = comment_result['id']
                reply_result = await reddit_interactor.reply_to_comment(
                    comment_id,
                    "This is a test reply from the RedditInteractor!"
                )
                print(f"Added reply with ID: {reply_result['id']}")
                
                # Example 4: Reply to a comment using comment URL
                comment_url = f"https://www.reddit.com{comment_result['permalink']}"
                reply_result = await reddit_interactor.reply_to_comment(
                    comment_url,
                    "This is another test reply using the comment URL!"
                )
                print(f"Added reply with ID: {reply_result['id']}")
            
            # Example 5: Batch get comments from multiple posts
            post_urls = [
                "https://www.reddit.com/r/python/comments/abc123/sample_post_title/",
                "https://www.reddit.com/r/python/comments/def456/another_sample_post/"
            ]
            batch_post_data = await reddit_interactor.batch_get_post_comments(post_urls)
            for post_id, data in batch_post_data.items():
                if "error" in data:
                    print(f"Error fetching post {post_id}: {data['error']}")
                else:
                    print(f"Post {post_id}: {data['title']} - {len(data['comments'])} comments")
            
            # Example 6: Batch add comments to posts (requires authentication)
            if reddit_interactor.username:
                comment_pairs = [
                    (post_urls[0], "This is a batch comment 1!"),
                    (post_urls[1], "This is a batch comment 2!")
                ]
                batch_comment_results = await reddit_interactor.batch_add_comments_to_posts(comment_pairs)
                for post_id, result in batch_comment_results.items():
                    if "error" in result:
                        print(f"Error commenting on post {post_id}: {result['error']}")
                    else:
                        print(f"Added comment to post {post_id}: {result['id']}")
        
            
        finally:
            # Always close the connection when done
            await reddit_interactor.close()


    asyncio.run(main())