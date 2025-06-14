"""
RedditPostFinder - A module for finding with Reddit posts based on topic.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Any, Union

# Using ASYNC-PRAW for asynchronous Reddit API interactions
import asyncpraw
from asyncpraw.models import Comment, Submission
from asyncpraw.exceptions import RedditAPIException


class RedditPostFinder:
    """
    A class for finding Reddit posts asynchronously.
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
        Initialize the RedditPostFinder with Reddit API credentials.
        
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
        self.logger = logging.getLogger("RedditPostFinder")
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
    
    
    async def search_subreddit_posts(self, subreddit: str, query: str, sort: str = "relevance", 
                                    time_filter: str = "all", limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for posts in a subreddit.
        
        Args:
            subreddit (str): Subreddit name (without 'r/')
            query (str): Search query
            sort (str): Sort order ('relevance', 'hot', 'new', 'top', 'comments')
            time_filter (str): Time filter ('all', 'day', 'hour', 'month', 'week', 'year')
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of post data dictionaries
            
        Raises:
            Exception: If search fails
        """
        await self._initialize_reddit()
        
        try:
            results = []
            
            # Get the subreddit
            subreddit_obj = await self._execute_with_retry(
                lambda: self.reddit.subreddit(subreddit)
            )
            
            # Perform the search
            search_results = subreddit_obj.search(
                query, 
                sort=sort, 
                time_filter=time_filter
            )
            
            # Process results
            counter = 0
            async for post in search_results:
                # Get post data
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "author": await self._get_author_info(post),
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "permalink": post.permalink,
                    "url": post.url,
                    "selftext": post.selftext if hasattr(post, "selftext") else "",
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
    
    async def batch_search_subreddits(self, search_params: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search multiple subreddits with different parameters in parallel.
        
        Args:
            search_params (List[Dict[str, Any]]): List of dictionaries containing search parameters.
                Each dictionary should have the following keys:
                - 'subreddit' (str): Subreddit name to search in
                - 'query' (str): Search query
                - 'sort' (str, optional): Sort order ('relevance', 'hot', 'new', 'top', 'comments')
                - 'time_filter' (str, optional): Time filter ('all', 'day', 'hour', 'month', 'week', 'year')
                - 'limit' (int, optional): Maximum number of results to return
            
        Returns:
            dict: Dictionary mapping search identifiers to their search results
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each search
        for i, params in enumerate(search_params):
            subreddit = params.get('subreddit')
            query = params.get('query')
            sort = params.get('sort', 'relevance')
            time_filter = params.get('time_filter', 'all')
            limit = params.get('limit', 25)
            
            if not subreddit or not query:
                results[f"search_{i}"] = {"error": "Missing required parameters (subreddit and query)"}
                continue
            
            # Create a unique identifier for this search
            search_id = f"{subreddit}_{query}_{sort}_{time_filter}"
            
            task = asyncio.create_task(
                self.search_subreddit_posts(subreddit, query, sort, time_filter, limit)
            )
            tasks.append((search_id, task))
        
        # Execute all tasks concurrently and gather results
        for search_id, task in tasks:
            try:
                result = await task
                results[search_id] = result
            except Exception as e:
                self.logger.error(f"Error processing search {search_id}: {str(e)}")
                results[search_id] = {"error": str(e)}
        
        return results

    async def search_multiple_subreddits(self, subreddits: List[str], query: str, 
                                       sort: str = "relevance", time_filter: str = "all", 
                                       limit: int = 25) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for the same query across multiple subreddits in parallel.
        
        Args:
            subreddits (List[str]): List of subreddit names to search in
            query (str): Search query to use for all subreddits
            sort (str): Sort order ('relevance', 'hot', 'new', 'top', 'comments')
            time_filter (str): Time filter ('all', 'day', 'hour', 'month', 'week', 'year')
            limit (int): Maximum number of results to return per subreddit
            
        Returns:
            dict: Dictionary mapping subreddit names to their search results
        """
        # Create search parameters for each subreddit
        search_params = [
            {
                'subreddit': subreddit,
                'query': query,
                'sort': sort,
                'time_filter': time_filter,
                'limit': limit
            }
            for subreddit in subreddits
        ]
        
        # Use the batch search method
        results_with_ids = await self.batch_search_subreddits(search_params)
        
        # Reorganize results by subreddit name for cleaner output
        results_by_subreddit = {}
        for search_id, results in results_with_ids.items():
            # Extract subreddit name from the search_id
            subreddit = search_id.split('_')[0]
            results_by_subreddit[subreddit] = results
        
        return results_by_subreddit
    
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
        reddit_interactor = RedditPostFinder(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            username="YOUR_USERNAME",  # Optional, but required for posting
            password="YOUR_PASSWORD",   # Optional, but required for posting
            user_agent="script:async-reddit-interactor:v1.0 (by /u/YOUR_USERNAME)"
        )
        
        try:
            # Example 1: Search for posts in a subreddit
            search_results = await reddit_interactor.search_subreddit_posts(
                "python", 
                "async programming"
            )
            print(f"Found {len(search_results)} matching posts")
            
            # Example 2: Search across multiple subreddits
            multi_search_results = await reddit_interactor.search_multiple_subreddits(
                ["python", "programming", "learnprogramming"],
                "async programming",
                limit=10
            )
            for subreddit, results in multi_search_results.items():
                print(f"Found {len(results)} posts in r/{subreddit}")
            
            # Example 3: Batch search with different parameters
            batch_params = [
                {"subreddit": "python", "query": "async", "sort": "relevance"},
                {"subreddit": "python", "query": "threading", "sort": "new"},
                {"subreddit": "programming", "query": "concurrency", "limit": 5}
            ]
            batch_results = await reddit_interactor.batch_search_subreddits(batch_params)
            for search_id, results in batch_results.items():
                print(f"Search {search_id}: Found {len(results)} posts")
            
        finally:
            # Always close the connection when done
            await reddit_interactor.close()

    asyncio.run(main())