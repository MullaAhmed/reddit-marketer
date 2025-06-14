"""
RedditUserAnalyzer - A module for analyzing Reddit user profiles, collecting metrics,
and tracking activity across posts and comments.
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any

# Using ASYNC-PRAW for asynchronous Reddit API interactions
import asyncpraw
from asyncpraw.exceptions import RedditAPIException


class RedditUserAnalyzer:
    """
    A class for analyzing Reddit user profiles, collecting comprehensive metrics,
    and tracking activity patterns.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = None,
        rate_limit_requests: int = 30,
        rate_limit_period: int = 60,
        max_retries: int = 3,
        retry_base_delay: float = 2.0,
        log_level: int = logging.INFO
    ):
        """
        Initialize the RedditUserAnalyzer with Reddit API credentials.
        
        Args:
            client_id (str): Reddit API client ID
            client_secret (str): Reddit API client secret
            user_agent (str, optional): Custom User-Agent for API requests
            rate_limit_requests (int): Maximum number of requests in rate limit period
            rate_limit_period (int): Rate limit period in seconds
            max_retries (int): Maximum number of retry attempts for failed requests
            retry_base_delay (float): Base delay for retry backoff in seconds
            log_level (int): Logging level for the analyzer
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Generate a default user agent if none provided
        self.user_agent = user_agent or (
            f"python:async-reddit-user-analyzer:v1.0 (by /u/anonymous)"
        )
        
        # Configuration for rate limiting and retries
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        
        # Set up logging
        self.logger = logging.getLogger("RedditUserAnalyzer")
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
            # Setup in read-only mode
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
    
    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """
        Get detailed information about a Reddit user's profile.
        
        Args:
            username (str): Reddit username
            
        Returns:
            dict: Dictionary containing user profile information
            
        Raises:
            Exception: If the user doesn't exist or is suspended
        """
        await self._initialize_reddit()
        
        try:
            # Get the user
            redditor = await self._execute_with_retry(
                lambda: self.reddit.redditor(username)
            )
            
            # Get basic user information
            user_data = {
                "username": username,
                "id": None,  # Will be filled if accessible
                "created_utc": None,
                "comment_karma": None,
                "post_karma": None,
                "total_karma": None,
                "is_gold": None,
                "is_mod": None,
                "is_employee": None,
                "verified": None,
                "has_verified_email": None,
                "accept_followers": None,
                "subreddit": None,  # User's profile subreddit details
            }
            
            # Try to access user attributes (some may be unavailable for suspended/deleted users)
            try:
                user_data["id"] = await self._execute_with_retry(lambda: redditor.id)
                user_data["created_utc"] = await self._execute_with_retry(lambda: redditor.created_utc)
                user_data["comment_karma"] = await self._execute_with_retry(lambda: redditor.comment_karma)
                user_data["post_karma"] = await self._execute_with_retry(lambda: redditor.link_karma)
                user_data["total_karma"] = user_data["comment_karma"] + user_data["post_karma"]
                user_data["is_gold"] = await self._execute_with_retry(lambda: redditor.is_gold)
                user_data["is_mod"] = await self._execute_with_retry(lambda: redditor.is_mod)
                user_data["is_employee"] = await self._execute_with_retry(lambda: getattr(redditor, "is_employee", False))
                user_data["verified"] = await self._execute_with_retry(lambda: getattr(redditor, "verified", False))
                user_data["has_verified_email"] = await self._execute_with_retry(lambda: getattr(redditor, "has_verified_email", False))
                user_data["accept_followers"] = await self._execute_with_retry(lambda: getattr(redditor, "accept_followers", True))
                
                # Try to get the user's profile subreddit info
                try:
                    subreddit = await self._execute_with_retry(lambda: redditor.subreddit)
                    if subreddit:
                        user_data["subreddit"] = {
                            "display_name": subreddit.display_name,
                            "title": subreddit.title,
                            "description": subreddit.description,
                            "subscribers": subreddit.subscribers,
                            "created_utc": subreddit.created_utc,
                        }
                except Exception as e:
                    self.logger.debug(f"Couldn't fetch user subreddit: {str(e)}")
                
            except Exception as e:
                self.logger.warning(f"Some user attributes for {username} couldn't be accessed: {str(e)}")
            
            # Calculate account age
            if user_data["created_utc"]:
                created_date = datetime.fromtimestamp(user_data["created_utc"])
                user_data["account_age_days"] = (datetime.now() - created_date).days
            
            return user_data
            
        except Exception as e:
            self.logger.error(f"Error fetching user profile for {username}: {str(e)}")
            raise
    
    async def get_user_submissions(self, username: str, limit: int = None, timeframe: str = "all") -> List[Dict[str, Any]]:
        """
        Get all submissions (posts) made by a user with detailed metrics.
        
        Args:
            username (str): Reddit username
            limit (int, optional): Maximum number of submissions to fetch
            timeframe (str, optional): Time frame to fetch submissions from
                                     ('all', 'day', 'week', 'month', 'year')
            
        Returns:
            list: List of submission dictionaries with detailed metrics
        """
        await self._initialize_reddit()
        
        try:
            # Get the user
            redditor = await self._execute_with_retry(
                lambda: self.reddit.redditor(username)
            )
            
            submissions = []
            
            # Function to process a submission
            async def process_submission(submission):
                # Calculate engagement metrics
                upvote_ratio = getattr(submission, "upvote_ratio", 0)
                estimated_upvotes = int(submission.score * upvote_ratio)
                estimated_downvotes = submission.score - estimated_upvotes
                
                # Get detailed submission data
                submission_data = {
                    "id": submission.id,
                    "title": submission.title,
                    "created_utc": submission.created_utc,
                    "permalink": submission.permalink,
                    "url": submission.url,
                    "subreddit": submission.subreddit.display_name,
                    "score": submission.score,
                    "upvote_ratio": upvote_ratio,
                    "num_comments": submission.num_comments,
                    "is_original_content": getattr(submission, "is_original_content", False),
                    "is_self": submission.is_self,
                    "is_video": getattr(submission, "is_video", False),
                    "over_18": submission.over_18,
                    "spoiler": getattr(submission, "spoiler", False),
                    "stickied": submission.stickied,
                    "locked": submission.locked,
                    "removed": hasattr(submission, "removed") and submission.removed,
                    
                    # Engagement metrics
                    "estimated_upvotes": estimated_upvotes,
                    "estimated_downvotes": estimated_downvotes,
                    "engagement_rate": (submission.num_comments / submission.score) if submission.score > 0 else 0,
                    
                    # Content details (if available)
                    "selftext": submission.selftext if hasattr(submission, "selftext") else "",
                    "selftext_length": len(submission.selftext) if hasattr(submission, "selftext") else 0,
                }
                
                # Calculate post age in days
                created_date = datetime.fromtimestamp(submission.created_utc)
                submission_data["age_days"] = (datetime.now() - created_date).days
                
                # Calculate daily engagement metrics
                if submission_data["age_days"] > 0:
                    submission_data["avg_score_per_day"] = submission.score / submission_data["age_days"]
                    submission_data["avg_comments_per_day"] = submission.num_comments / submission_data["age_days"]
                else:
                    submission_data["avg_score_per_day"] = submission.score
                    submission_data["avg_comments_per_day"] = submission.num_comments
                
                return submission_data
            
            # Get submissions based on time frame
            submission_iterator = None
            
            if timeframe == "day":
                submission_iterator = redditor.submissions.top("day", limit=limit)
            elif timeframe == "week":
                submission_iterator = redditor.submissions.top("week", limit=limit)
            elif timeframe == "month":
                submission_iterator = redditor.submissions.top("month", limit=limit)
            elif timeframe == "year":
                submission_iterator = redditor.submissions.top("year", limit=limit)
            else:  # Default to "all"
                submission_iterator = redditor.submissions.new(limit=limit)
            
            # Process all submissions
            async for submission in submission_iterator:
                submission_data = await process_submission(submission)
                submissions.append(submission_data)
            
            return submissions
            
        except Exception as e:
            self.logger.error(f"Error fetching submissions for {username}: {str(e)}")
            raise
    
    async def get_user_comments(self, username: str, limit: int = None, timeframe: str = "all") -> List[Dict[str, Any]]:
        """
        Get all comments made by a user with detailed metrics.
        
        Args:
            username (str): Reddit username
            limit (int, optional): Maximum number of comments to fetch
            timeframe (str, optional): Time frame to fetch comments from
                                     ('all', 'day', 'week', 'month', 'year')
            
        Returns:
            list: List of comment dictionaries with detailed metrics
        """
        await self._initialize_reddit()
        
        try:
            # Get the user
            redditor = await self._execute_with_retry(
                lambda: self.reddit.redditor(username)
            )
            
            comments = []
            
            # Function to process a comment
            async def process_comment(comment):
                # Calculate basic metrics
                created_date = datetime.fromtimestamp(comment.created_utc)
                age_days = (datetime.now() - created_date).days
                
                # Get detailed comment data
                comment_data = {
                    "id": comment.id,
                    "body": comment.body,
                    "created_utc": comment.created_utc,
                    "permalink": comment.permalink,
                    "subreddit": comment.subreddit.display_name,
                    "score": comment.score,
                    "is_submitter": comment.is_submitter,
                    "stickied": comment.stickied,
                    "edited": bool(comment.edited),
                    "parent_id": comment.parent_id,
                    "post_id": comment.submission.id,
                    "post_title": comment.submission.title,
                    
                    # Additional metrics
                    "body_length": len(comment.body),
                    "age_days": age_days,
                    "avg_score_per_day": comment.score / age_days if age_days > 0 else comment.score,
                    "body_word_count": len(comment.body.split()),
                }
                
                # Check if it's a top-level comment or a reply
                comment_data["is_top_level"] = comment.parent_id.startswith("t3_")
                
                return comment_data
            
            # Get comments based on time frame
            comment_iterator = None
            
            if timeframe == "day":
                comment_iterator = redditor.comments.top("day", limit=limit)
            elif timeframe == "week":
                comment_iterator = redditor.comments.top("week", limit=limit)
            elif timeframe == "month":
                comment_iterator = redditor.comments.top("month", limit=limit)
            elif timeframe == "year":
                comment_iterator = redditor.comments.top("year", limit=limit)
            else:  # Default to "all"
                comment_iterator = redditor.comments.new(limit=limit)
            
            # Process all comments
            async for comment in comment_iterator:
                comment_data = await process_comment(comment)
                comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for {username}: {str(e)}")
            raise
    
    async def generate_user_activity_summary(self, username: str, submission_limit: int = 100, comment_limit: int = 500) -> Dict[str, Any]:
        """
        Generate a comprehensive activity summary for a user with advanced metrics.
        
        Args:
            username (str): Reddit username
            submission_limit (int, optional): Maximum number of submissions to analyze
            comment_limit (int, optional): Maximum number of comments to analyze
            
        Returns:
            dict: Comprehensive user activity summary with detailed metrics
        """
        await self._initialize_reddit()
        
        try:
            # Get user profile
            profile = await self.get_user_profile(username)
            
            # Get user submissions and comments
            submissions = await self.get_user_submissions(username, limit=submission_limit)
            comments = await self.get_user_comments(username, limit=comment_limit)
            
            # Initialize activity summary
            activity_summary = {
                "username": username,
                "profile": profile,
                "post_count": len(submissions),
                "comment_count": len(comments),
                "total_karma": profile.get("total_karma", 0),
                "karma_breakdown": {
                    "post_karma": profile.get("post_karma", 0),
                    "comment_karma": profile.get("comment_karma", 0)
                },
                "account_age_days": profile.get("account_age_days", 0),
                
                # Activity metrics
                "karma_per_day": profile.get("total_karma", 0) / profile.get("account_age_days", 1) if profile.get("account_age_days", 0) > 0 else 0,
                "posts_per_day": len(submissions) / profile.get("account_age_days", 1) if profile.get("account_age_days", 0) > 0 else 0,
                "comments_per_day": len(comments) / profile.get("account_age_days", 1) if profile.get("account_age_days", 0) > 0 else 0,
                
                # Content analysis
                "avg_post_score": sum(s["score"] for s in submissions) / len(submissions) if submissions else 0,
                "avg_comment_score": sum(c["score"] for c in comments) / len(comments) if comments else 0,
                "avg_post_comments": sum(s["num_comments"] for s in submissions) / len(submissions) if submissions else 0,
                "avg_comment_length": sum(c["body_length"] for c in comments) / len(comments) if comments else 0,
                "avg_post_length": sum(s["selftext_length"] for s in submissions) / len(submissions) if submissions else 0,
                
                # Top content
                "top_posts": sorted(submissions, key=lambda x: x["score"], reverse=True)[:5] if submissions else [],
                "top_comments": sorted(comments, key=lambda x: x["score"], reverse=True)[:5] if comments else [],
                
                # Activity patterns
                "subreddit_activity": {},
                "posting_hours": {},
                "posting_days": {},
                "comment_reply_ratio": 0,
                
                # Historical analysis
                "post_frequency_trend": {},
                "comment_frequency_trend": {},
                "karma_trend": {},
                
                # Content types
                "content_type_breakdown": {
                    "text_posts": len([s for s in submissions if s["is_self"]]),
                    "link_posts": len([s for s in submissions if not s["is_self"]]),
                    "top_level_comments": len([c for c in comments if c["is_top_level"]]),
                    "reply_comments": len([c for c in comments if not c["is_top_level"]]),
                    "nsfw_posts": len([s for s in submissions if s["over_18"]]),
                    "original_content": len([s for s in submissions if s.get("is_original_content")])
                }
            }
            
            # Calculate comment reply ratio
            if comments:
                activity_summary["comment_reply_ratio"] = len([c for c in comments if not c["is_top_level"]]) / len(comments)
            
            # Calculate subreddit activity
            subreddit_post_counts = Counter(s["subreddit"] for s in submissions)
            subreddit_comment_counts = Counter(c["subreddit"] for c in comments)
            
            # Merge post and comment data for subreddits
            all_subreddits = set(subreddit_post_counts.keys()) | set(subreddit_comment_counts.keys())
            for subreddit in all_subreddits:
                activity_summary["subreddit_activity"][subreddit] = {
                    "posts": subreddit_post_counts.get(subreddit, 0),
                    "comments": subreddit_comment_counts.get(subreddit, 0),
                    "total": subreddit_post_counts.get(subreddit, 0) + subreddit_comment_counts.get(subreddit, 0)
                }
            
            # Sort subreddits by total activity
            activity_summary["top_subreddits"] = [
                {"name": subreddit, "count": data["total"]}
                for subreddit, data in sorted(
                    activity_summary["subreddit_activity"].items(),
                    key=lambda x: x[1]["total"],
                    reverse=True
                )[:10]
            ]
            
            # Calculate posting hours
            hour_post_counts = Counter()
            hour_comment_counts = Counter()
            for submission in submissions:
                hour = datetime.fromtimestamp(submission["created_utc"]).hour
                hour_post_counts[hour] += 1
            
            for comment in comments:
                hour = datetime.fromtimestamp(comment["created_utc"]).hour
                hour_comment_counts[hour] += 1
            
            for hour in range(24):
                activity_summary["posting_hours"][hour] = {
                    "posts": hour_post_counts.get(hour, 0),
                    "comments": hour_comment_counts.get(hour, 0),
                    "total": hour_post_counts.get(hour, 0) + hour_comment_counts.get(hour, 0)
                }
            
            # Calculate posting days
            day_post_counts = Counter()
            day_comment_counts = Counter()
            for submission in submissions:
                day = datetime.fromtimestamp(submission["created_utc"]).weekday()
                day_post_counts[day] += 1
            
            for comment in comments:
                day = datetime.fromtimestamp(comment["created_utc"]).weekday()
                day_comment_counts[day] += 1
            
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day_num, day_name in enumerate(days):
                activity_summary["posting_days"][day_name] = {
                    "posts": day_post_counts.get(day_num, 0),
                    "comments": day_comment_counts.get(day_num, 0),
                    "total": day_post_counts.get(day_num, 0) + day_comment_counts.get(day_num, 0)
                }
            
            # Calculate monthly trends (last 12 months)
            now = datetime.now()
            for i in range(12):
                month_start = now - timedelta(days=30 * (i + 1))
                month_end = now - timedelta(days=30 * i)
                month_key = month_start.strftime("%Y-%m")
                
                month_posts = [s for s in submissions if month_start.timestamp() <= s["created_utc"] < month_end.timestamp()]
                month_comments = [c for c in comments if month_start.timestamp() <= c["created_utc"] < month_end.timestamp()]
                
                month_karma = sum(s["score"] for s in month_posts) + sum(c["score"] for c in month_comments)
                
                activity_summary["post_frequency_trend"][month_key] = len(month_posts)
                activity_summary["comment_frequency_trend"][month_key] = len(month_comments)
                activity_summary["karma_trend"][month_key] = month_karma
            
            return activity_summary
            
        except Exception as e:
            self.logger.error(f"Error generating activity summary for {username}: {str(e)}")
            raise
    
    async def analyze_user_submission(self, submission_id: str, include_comments: bool = True) -> Dict[str, Any]:
        """
        Perform detailed analysis on a specific user submission.
        
        Args:
            submission_id (str): ID of the submission to analyze
            include_comments (bool, optional): Whether to include comment analysis
            
        Returns:
            dict: Detailed analysis of the submission
        """
        await self._initialize_reddit()
        
        try:
            # Get the submission
            submission = await self._execute_with_retry(
                lambda: self.reddit.submission(id=submission_id)
            )
            
            # Calculate engagement metrics
            upvote_ratio = getattr(submission, "upvote_ratio", 0)
            estimated_upvotes = int(submission.score * upvote_ratio)
            estimated_downvotes = submission.score - estimated_upvotes
            
            # Initialize submission analysis
            submission_analysis = {
                "id": submission.id,
                "author": submission.author.name if submission.author else "[deleted]",
                "title": submission.title,
                "created_utc": submission.created_utc,
                "permalink": submission.permalink,
                "url": submission.url,
                "subreddit": submission.subreddit.display_name,
                "score": submission.score,
                "upvote_ratio": upvote_ratio,
                "num_comments": submission.num_comments,
                "is_original_content": getattr(submission, "is_original_content", False),
                "is_self": submission.is_self,
                "is_video": getattr(submission, "is_video", False),
                "over_18": submission.over_18,
                "spoiler": getattr(submission, "spoiler", False),
                "stickied": submission.stickied,
                "locked": submission.locked,
                "removed": hasattr(submission, "removed") and submission.removed,
                
                # Engagement metrics
                "estimated_upvotes": estimated_upvotes,
                "estimated_downvotes": estimated_downvotes,
                "engagement_rate": (submission.num_comments / submission.score) if submission.score > 0 else 0,
                
                # Content details (if available)
                "selftext": submission.selftext if hasattr(submission, "selftext") else "",
                "selftext_length": len(submission.selftext) if hasattr(submission, "selftext") else 0,
                
                # Advanced analysis
                "flair": {
                    "text": submission.link_flair_text if hasattr(submission, "link_flair_text") else None,
                    "type": submission.link_flair_type if hasattr(submission, "link_flair_type") else None,
                    "css_class": submission.link_flair_css_class if hasattr(submission, "link_flair_css_class") else None
                },
                "domain": submission.domain if hasattr(submission, "domain") else None,
                "gildings": {
                    "silver": getattr(submission, "gildings", {}).get("gid_1", 0) if hasattr(submission, "gildings") else 0,
                    "gold": getattr(submission, "gildings", {}).get("gid_2", 0) if hasattr(submission, "gildings") else 0,
                    "platinum": getattr(submission, "gildings", {}).get("gid_3", 0) if hasattr(submission, "gildings") else 0
                },
                "comments_data": [],
                "comment_stats": {}
            }
            
            # Calculate post age in days
            created_date = datetime.fromtimestamp(submission.created_utc)
            submission_analysis["age_days"] = (datetime.now() - created_date).days
            
            # Calculate daily engagement metrics
            if submission_analysis["age_days"] > 0:
                submission_analysis["avg_score_per_day"] = submission.score / submission_analysis["age_days"]
                submission_analysis["avg_comments_per_day"] = submission.num_comments / submission_analysis["age_days"]
            else:
                submission_analysis["avg_score_per_day"] = submission.score
                submission_analysis["avg_comments_per_day"] = submission.num_comments
            
            # Include comment analysis if requested
            if include_comments:
                # Replace MoreComments objects with actual comments
                await submission.comments.replace_more(limit=None)
                
                # Process top-level comments
                comment_scores = []
                comment_lengths = []
                comment_hours = Counter()
                
                async for comment in submission.comments:
                    # Get basic comment data
                    comment_data = {
                        "id": comment.id,
                        "author": comment.author.name if comment.author else "[deleted]",
                        "body": comment.body,
                        "score": comment.score,
                        "created_utc": comment.created_utc,
                        "is_submitter": comment.is_submitter,
                        "body_length": len(comment.body)
                    }
                    
                    # Collect statistics
                    comment_scores.append(comment.score)
                    comment_lengths.append(len(comment.body))
                    comment_hour = datetime.fromtimestamp(comment.created_utc).hour
                    comment_hours[comment_hour] += 1
                    
                    submission_analysis["comments_data"].append(comment_data)
                
                # Calculate comment statistics
                submission_analysis["comment_stats"] = {
                    "avg_score": sum(comment_scores) / len(comment_scores) if comment_scores else 0,
                    "median_score": sorted(comment_scores)[len(comment_scores) // 2] if comment_scores else 0,
                    "max_score": max(comment_scores) if comment_scores else 0,
                    "min_score": min(comment_scores) if comment_scores else 0,
                    "avg_length": sum(comment_lengths) / len(comment_lengths) if comment_lengths else 0,
                    "top_comment_hours": dict(comment_hours.most_common(3))
                }
            
            return submission_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing submission {submission_id}: {str(e)}")
            raise
    
    async def analyze_user_comment(self, comment_id: str) -> Dict[str, Any]:
        """
        Perform detailed analysis on a specific user comment.
        
        Args:
            comment_id (str): ID of the comment to analyze
            
        Returns:
            dict: Detailed analysis of the comment
        """
        await self._initialize_reddit()
        
        try:
            # Get the comment
            comment = await self._execute_with_retry(
                lambda: self.reddit.comment(id=comment_id)
            )
            
            # Initialize comment analysis
            comment_analysis = {
                "id": comment.id,
                "author": comment.author.name if comment.author else "[deleted]",
                "body": comment.body,
                "created_utc": comment.created_utc,
                "permalink": comment.permalink,
                "subreddit": comment.subreddit.display_name,
                "score": comment.score,
                "is_submitter": comment.is_submitter,
                "stickied": comment.stickied,
                "edited": bool(comment.edited),
                "parent_id": comment.parent_id,
                "post_id": comment.submission.id,
                "post_title": comment.submission.title,
                
                # Additional metrics
                "body_length": len(comment.body),
                "body_word_count": len(comment.body.split()),
                
                # Advanced analysis
                "gildings": {
                    "silver": getattr(comment, "gildings", {}).get("gid_1", 0) if hasattr(comment, "gildings") else 0,
                    "gold": getattr(comment, "gildings", {}).get("gid_2", 0) if hasattr(comment, "gildings") else 0,
                    "platinum": getattr(comment, "gildings", {}).get("gid_3", 0) if hasattr(comment, "gildings") else 0
                },
                "controversiality": getattr(comment, "controversiality", 0),
                "replies": [],
                "context": {}
            }
            
            # Check if it's a top-level comment or a reply
            comment_analysis["is_top_level"] = comment.parent_id.startswith("t3_")
            
            # Calculate comment age in days
            created_date = datetime.fromtimestamp(comment.created_utc)
            comment_analysis["age_days"] = (datetime.now() - created_date).days
            
            # Calculate daily score
            if comment_analysis["age_days"] > 0:
                comment_analysis["avg_score_per_day"] = comment.score / comment_analysis["age_days"]
            else:
                comment_analysis["avg_score_per_day"] = comment.score
            
            # Get comment context (parent comment or post)
            if comment_analysis["is_top_level"]:
                # Parent is the post
                submission = comment.submission
                comment_analysis["context"]["parent_type"] = "post"
                comment_analysis["context"]["parent_title"] = submission.title
                comment_analysis["context"]["parent_score"] = submission.score
                comment_analysis["context"]["parent_created_utc"] = submission.created_utc
            else:
                # Parent is another comment
                try:
                    parent_id = comment.parent_id[3:]  # Remove 't1_' prefix
                    parent_comment = await self._execute_with_retry(
                        lambda: self.reddit.comment(id=parent_id)
                    )
                    
                    comment_analysis["context"]["parent_type"] = "comment"
                    comment_analysis["context"]["parent_author"] = parent_comment.author.name if parent_comment.author else "[deleted]"
                    comment_analysis["context"]["parent_body"] = parent_comment.body
                    comment_analysis["context"]["parent_score"] = parent_comment.score
                    comment_analysis["context"]["parent_created_utc"] = parent_comment.created_utc
                except Exception as e:
                    self.logger.debug(f"Couldn't fetch parent comment: {str(e)}")
                    comment_analysis["context"]["parent_type"] = "comment"
                    comment_analysis["context"]["parent_error"] = "Couldn't fetch parent comment"
            
            # Try to get top replies to this comment
            try:
                # Refresh the comment to get replies
                await comment.refresh()
                
                # Process replies if any
                if hasattr(comment, "replies") and comment.replies:
                    # Replace MoreComments objects with actual comments
                    if hasattr(comment.replies, "replace_more"):
                        await comment.replies.replace_more(limit=5)  # Limit to top 5 for performance
                    
                    # Process top-level replies
                    async for reply in comment.replies:
                        reply_data = {
                            "id": reply.id,
                            "author": reply.author.name if reply.author else "[deleted]",
                            "body": reply.body,
                            "score": reply.score,
                            "created_utc": reply.created_utc
                        }
                        comment_analysis["replies"].append(reply_data)
            except Exception as e:
                self.logger.debug(f"Couldn't fetch replies: {str(e)}")
            
            return comment_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing comment {comment_id}: {str(e)}")
            raise
    
    async def get_user_karma_breakdown(self, username: str, limit: int = 500) -> Dict[str, Dict[str, int]]:
        """
        Get a breakdown of user's karma by subreddit.
        
        Args:
            username (str): Reddit username
            limit (int, optional): Maximum number of posts/comments to analyze
            
        Returns:
            dict: Karma breakdown by subreddit
        """
        await self._initialize_reddit()
        
        try:
            # Get user submissions and comments
            submissions = await self.get_user_submissions(username, limit=limit)
            comments = await self.get_user_comments(username, limit=limit)
            
            # Initialize karma breakdown
            karma_breakdown = {}
            
            # Process submissions
            for submission in submissions:
                subreddit = submission["subreddit"]
                if subreddit not in karma_breakdown:
                    karma_breakdown[subreddit] = {
                        "post_karma": 0,
                        "comment_karma": 0,
                        "total_karma": 0
                    }
                
                karma_breakdown[subreddit]["post_karma"] += submission["score"]
                karma_breakdown[subreddit]["total_karma"] += submission["score"]
            
            # Process comments
            for comment in comments:
                subreddit = comment["subreddit"]
                if subreddit not in karma_breakdown:
                    karma_breakdown[subreddit] = {
                        "post_karma": 0,
                        "comment_karma": 0,
                        "total_karma": 0
                    }
                
                karma_breakdown[subreddit]["comment_karma"] += comment["score"]
                karma_breakdown[subreddit]["total_karma"] += comment["score"]
            
            return karma_breakdown
            
        except Exception as e:
            self.logger.error(f"Error getting karma breakdown for {username}: {str(e)}")
            raise
    
    # NEW BATCH PROCESSING METHODS
    
    async def batch_get_user_profiles(self, usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about multiple Reddit user profiles in parallel.
        
        Args:
            usernames (List[str]): List of Reddit usernames
            
        Returns:
            dict: Dictionary mapping usernames to their profile information
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each username
        for username in usernames:
            task = asyncio.create_task(self.get_user_profile(username))
            tasks.append((username, task))
        
        # Execute all tasks concurrently and gather results
        for username, task in tasks:
            try:
                result = await task
                results[username] = result
            except Exception as e:
                self.logger.error(f"Error fetching profile for {username}: {str(e)}")
                results[username] = {"error": str(e)}
        
        return results

    async def batch_get_user_submissions(self, username_param_pairs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get submissions for multiple users or with different parameters in parallel.
        
        Args:
            username_param_pairs (List[Dict[str, Any]]): List of dictionaries with parameters.
                Each dictionary should have these keys:
                - 'username' (str): Reddit username
                - 'limit' (int, optional): Maximum number of submissions
                - 'timeframe' (str, optional): Timeframe to fetch from
            
        Returns:
            dict: Dictionary mapping usernames to their submissions
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each username with parameters
        for params in username_param_pairs:
            username = params.get('username')
            if not username:
                continue
                
            limit = params.get('limit')
            timeframe = params.get('timeframe', 'all')
            
            task = asyncio.create_task(self.get_user_submissions(username, limit, timeframe))
            task_id = f"{username}_{timeframe}_{limit}"
            tasks.append((task_id, username, task))
        
        # Execute all tasks concurrently and gather results
        for task_id, username, task in tasks:
            try:
                result = await task
                if username not in results:
                    results[username] = []
                results[username].extend(result)
            except Exception as e:
                self.logger.error(f"Error fetching submissions for {username}: {str(e)}")
                results[username] = [{"error": str(e)}]
        
        return results

    async def batch_get_user_comments(self, username_param_pairs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get comments for multiple users or with different parameters in parallel.
        
        Args:
            username_param_pairs (List[Dict[str, Any]]): List of dictionaries with parameters.
                Each dictionary should have these keys:
                - 'username' (str): Reddit username
                - 'limit' (int, optional): Maximum number of comments
                - 'timeframe' (str, optional): Timeframe to fetch from
            
        Returns:
            dict: Dictionary mapping usernames to their comments
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each username with parameters
        for params in username_param_pairs:
            username = params.get('username')
            if not username:
                continue
                
            limit = params.get('limit')
            timeframe = params.get('timeframe', 'all')
            
            task = asyncio.create_task(self.get_user_comments(username, limit, timeframe))
            task_id = f"{username}_{timeframe}_{limit}"
            tasks.append((task_id, username, task))
        
        # Execute all tasks concurrently and gather results
        for task_id, username, task in tasks:
            try:
                result = await task
                if username not in results:
                    results[username] = []
                results[username].extend(result)
            except Exception as e:
                self.logger.error(f"Error fetching comments for {username}: {str(e)}")
                results[username] = [{"error": str(e)}]
        
        return results

    async def batch_get_user_activity_summaries(self, usernames: List[str], 
                                          submission_limit: int = 100, 
                                          comment_limit: int = 500) -> Dict[str, Dict[str, Any]]:
        """
        Generate comprehensive activity summaries for multiple users in parallel.
        
        Args:
            usernames (List[str]): List of Reddit usernames
            submission_limit (int, optional): Maximum number of submissions to analyze per user
            comment_limit (int, optional): Maximum number of comments to analyze per user
            
        Returns:
            dict: Dictionary mapping usernames to their activity summaries
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each username
        for username in usernames:
            task = asyncio.create_task(
                self.generate_user_activity_summary(username, submission_limit, comment_limit)
            )
            tasks.append((username, task))
        
        # Execute all tasks concurrently and gather results
        for username, task in tasks:
            try:
                result = await task
                results[username] = result
            except Exception as e:
                self.logger.error(f"Error generating activity summary for {username}: {str(e)}")
                results[username] = {"error": str(e)}
        
        return results

    async def batch_analyze_user_submissions(self, submission_ids: List[str], include_comments: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple submissions in parallel.
        
        Args:
            submission_ids (List[str]): List of submission IDs to analyze
            include_comments (bool): Whether to include comment analysis
            
        Returns:
            dict: Dictionary mapping submission IDs to their analyses
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each submission ID
        for submission_id in submission_ids:
            task = asyncio.create_task(self.analyze_user_submission(submission_id, include_comments))
            tasks.append((submission_id, task))
        
        # Execute all tasks concurrently and gather results
        for submission_id, task in tasks:
            try:
                result = await task
                results[submission_id] = result
            except Exception as e:
                self.logger.error(f"Error analyzing submission {submission_id}: {str(e)}")
                results[submission_id] = {"error": str(e)}
        
        return results

    async def batch_analyze_user_comments(self, comment_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple comments in parallel.
        
        Args:
            comment_ids (List[str]): List of comment IDs to analyze
            
        Returns:
            dict: Dictionary mapping comment IDs to their analyses
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each comment ID
        for comment_id in comment_ids:
            task = asyncio.create_task(self.analyze_user_comment(comment_id))
            tasks.append((comment_id, task))
        
        # Execute all tasks concurrently and gather results
        for comment_id, task in tasks:
            try:
                result = await task
                results[comment_id] = result
            except Exception as e:
                self.logger.error(f"Error analyzing comment {comment_id}: {str(e)}")
                results[comment_id] = {"error": str(e)}
        
        return results

    async def batch_get_karma_breakdowns(self, usernames: List[str], limit: int = 500) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Get karma breakdowns for multiple users in parallel.
        
        Args:
            usernames (List[str]): List of Reddit usernames
            limit (int, optional): Maximum number of posts/comments to analyze per user
            
        Returns:
            dict: Dictionary mapping usernames to their karma breakdowns
        """
        await self._initialize_reddit()
        
        results = {}
        tasks = []
        
        # Create a task for each username
        for username in usernames:
            task = asyncio.create_task(self.get_user_karma_breakdown(username, limit))
            tasks.append((username, task))
        
        # Execute all tasks concurrently and gather results
        for username, task in tasks:
            try:
                result = await task
                results[username] = result
            except Exception as e:
                self.logger.error(f"Error getting karma breakdown for {username}: {str(e)}")
                results[username] = {"error": str(e)}
        
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
        # Initialize the analyzer with your Reddit API credentials
        user_analyzer = RedditUserAnalyzer(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            user_agent="script:async-reddit-user-analyzer:v1.0 (by /u/YOUR_USERNAME)"
        )
        
        try:
            # Example 1: Get user profile
            username = "spez"  # Reddit CEO's username as an example
            profile = await user_analyzer.get_user_profile(username)
            print(f"User: {profile['username']}")
            print(f"Karma: {profile.get('total_karma', 'Unknown')}")
            print(f"Account Age: {profile.get('account_age_days', 'Unknown')} days")
            
            # Example 2: Get user submissions
            submissions = await user_analyzer.get_user_submissions(username, limit=10)
            print(f"\nFound {len(submissions)} submissions")
            if submissions:
                print(f"Latest post: {submissions[0]['title']}")
            
            # Example 3: Get user comments
            comments = await user_analyzer.get_user_comments(username, limit=10)
            print(f"\nFound {len(comments)} comments")
            
            # Example 4: Generate comprehensive activity summary
            print("\nGenerating activity summary...")
            summary = await user_analyzer.generate_user_activity_summary(username, submission_limit=50, comment_limit=100)
            print(f"Top subreddits: {', '.join(s['name'] for s in summary['top_subreddits'][:3])}")
            print(f"Most active hour: {max(summary['posting_hours'].items(), key=lambda x: x[1]['total'])[0]}")
            print(f"Most active day: {max(summary['posting_days'].items(), key=lambda x: x[1]['total'])[0]}")
            
            # Example 5: Get karma breakdown
            karma_breakdown = await user_analyzer.get_user_karma_breakdown(username, limit=100)
            top_karma_subreddits = sorted(karma_breakdown.items(), key=lambda x: x[1]['total_karma'], reverse=True)[:3]
            print("\nTop karma subreddits:")
            for subreddit, karma in top_karma_subreddits:
                print(f"r/{subreddit}: {karma['total_karma']} karma")
            
            # Example 6: Batch process multiple user profiles
            usernames = ["spez", "kn0thing", "reddit"]
            print("\nBatch processing user profiles...")
            profiles = await user_analyzer.batch_get_user_profiles(usernames)
            for username, profile in profiles.items():
                if "error" in profile:
                    print(f"Error for {username}: {profile['error']}")
                else:
                    print(f"User: {username}, Karma: {profile.get('total_karma', 'Unknown')}")
            
            # Example 7: Batch process karma breakdowns
            print("\nBatch processing karma breakdowns...")
            breakdowns = await user_analyzer.batch_get_karma_breakdowns(usernames)
            for username, breakdown in breakdowns.items():
                if isinstance(breakdown, dict) and "error" not in breakdown:
                    top_subreddit = max(breakdown.items(), key=lambda x: x[1]['total_karma'], default=(None, None))
                    if top_subreddit[0]:
                        print(f"{username}'s top subreddit: r/{top_subreddit[0]} with {top_subreddit[1]['total_karma']} karma")
            
        finally:
            # Always close the connection when done
            await user_analyzer.close()


    asyncio.run(main())