"""
User analytics service for fetching Reddit user statistics.
"""

import logging
from typing import Dict, Any, Optional

from src.clients.reddit_client import RedditClient
from src.models.common import format_timestamp

logger = logging.getLogger(__name__)


class UserAnalyticsService:
    """Service for fetching Reddit user statistics and analytics."""
    
    def __init__(self, reddit_client: RedditClient):
        """Initialize the user analytics service."""
        self.reddit_client = reddit_client
        self.logger = logger
    
    async def get_user_profile_stats(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive statistics for a Reddit user.
        
        Args:
            username: Reddit username (without u/ prefix)
            
        Returns:
            Dictionary containing user statistics or None if user not found/error
        """
        try:
            async with self.reddit_client:
                # Get the redditor object
                redditor = await self.reddit_client._reddit_instance.redditor(username)
                
                # Fetch user data
                try:
                    # This will trigger an API call to fetch user data
                    await redditor.load()
                except Exception as e:
                    if "404" in str(e) or "not found" in str(e).lower():
                        self.logger.warning(f"User '{username}' not found")
                        return None
                    else:
                        raise e
                
                # Extract user statistics
                user_stats = {
                    "username": redditor.name,
                    "total_karma": getattr(redditor, 'total_karma', 0),
                    "link_karma": getattr(redditor, 'link_karma', 0),
                    "comment_karma": getattr(redditor, 'comment_karma', 0),
                    "awardee_karma": getattr(redditor, 'awardee_karma', 0),
                    "awarder_karma": getattr(redditor, 'awarder_karma', 0),
                    "created_utc": getattr(redditor, 'created_utc', 0),
                    "created_date": format_timestamp(getattr(redditor, 'created_utc', 0)),
                    "is_employee": getattr(redditor, 'is_employee', False),
                    "is_mod": getattr(redditor, 'is_mod', False),
                    "is_gold": getattr(redditor, 'is_gold', False),
                    "has_verified_email": getattr(redditor, 'has_verified_email', False),
                    "icon_img": getattr(redditor, 'icon_img', ''),
                    "profile_url": f"https://reddit.com/u/{username}"
                }
                
                # Get subreddit info if available
                if hasattr(redditor, 'subreddit') and redditor.subreddit:
                    user_stats["subreddit"] = {
                        "name": getattr(redditor.subreddit, 'display_name', ''),
                        "title": getattr(redditor.subreddit, 'title', ''),
                        "public_description": getattr(redditor.subreddit, 'public_description', ''),
                        "subscribers": getattr(redditor.subreddit, 'subscribers', 0)
                    }
                else:
                    user_stats["subreddit"] = None
                
                self.logger.info(f"Successfully fetched stats for user '{username}'")
                return user_stats
                
        except Exception as e:
            self.logger.error(f"Error fetching stats for user '{username}': {str(e)}")
            return None
    
    async def get_user_recent_activity(
        self, 
        username: str, 
        activity_type: str = "all",
        limit: int = 25
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch recent activity for a Reddit user.
        
        Args:
            username: Reddit username
            activity_type: Type of activity ("submissions", "comments", "all")
            limit: Number of items to fetch
            
        Returns:
            Dictionary containing recent activity or None if error
        """
        try:
            async with self.reddit_client:
                redditor = await self.reddit_client._reddit_instance.redditor(username)
                
                activity_data = {
                    "username": username,
                    "activity_type": activity_type,
                    "submissions": [],
                    "comments": []
                }
                
                # Fetch submissions if requested
                if activity_type in ["submissions", "all"]:
                    try:
                        submission_count = 0
                        async for submission in redditor.submissions.new(limit=limit):
                            if submission_count >= limit:
                                break
                            
                            submission_data = {
                                "id": submission.id,
                                "title": submission.title,
                                "subreddit": submission.subreddit.display_name,
                                "score": submission.score,
                                "upvote_ratio": getattr(submission, 'upvote_ratio', 0),
                                "num_comments": submission.num_comments,
                                "created_utc": submission.created_utc,
                                "created_date": format_timestamp(submission.created_utc),
                                "permalink": submission.permalink,
                                "url": submission.url,
                                "selftext": getattr(submission, 'selftext', '')[:200] + "..." if len(getattr(submission, 'selftext', '')) > 200 else getattr(submission, 'selftext', '')
                            }
                            activity_data["submissions"].append(submission_data)
                            submission_count += 1
                    except Exception as e:
                        self.logger.warning(f"Error fetching submissions for '{username}': {str(e)}")
                
                # Fetch comments if requested
                if activity_type in ["comments", "all"]:
                    try:
                        comment_count = 0
                        async for comment in redditor.comments.new(limit=limit):
                            if comment_count >= limit:
                                break
                            
                            comment_data = {
                                "id": comment.id,
                                "body": comment.body[:200] + "..." if len(comment.body) > 200 else comment.body,
                                "subreddit": comment.subreddit.display_name,
                                "score": comment.score,
                                "created_utc": comment.created_utc,
                                "created_date": format_timestamp(comment.created_utc),
                                "permalink": comment.permalink,
                                "parent_id": comment.parent_id,
                                "is_submitter": getattr(comment, 'is_submitter', False)
                            }
                            activity_data["comments"].append(comment_data)
                            comment_count += 1
                    except Exception as e:
                        self.logger.warning(f"Error fetching comments for '{username}': {str(e)}")
                
                # Add summary statistics
                activity_data["summary"] = {
                    "total_submissions": len(activity_data["submissions"]),
                    "total_comments": len(activity_data["comments"]),
                    "avg_submission_score": sum(s["score"] for s in activity_data["submissions"]) / len(activity_data["submissions"]) if activity_data["submissions"] else 0,
                    "avg_comment_score": sum(c["score"] for c in activity_data["comments"]) / len(activity_data["comments"]) if activity_data["comments"] else 0,
                    "most_active_subreddits": self._get_most_active_subreddits(activity_data)
                }
                
                self.logger.info(f"Successfully fetched recent activity for user '{username}'")
                return activity_data
                
        except Exception as e:
            self.logger.error(f"Error fetching recent activity for user '{username}': {str(e)}")
            return None
    
    async def get_user_karma_breakdown(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed karma breakdown for a user.
        
        Args:
            username: Reddit username
            
        Returns:
            Dictionary containing karma breakdown or None if error
        """
        try:
            # Get basic profile stats
            profile_stats = await self.get_user_profile_stats(username)
            if not profile_stats:
                return None
            
            # Get recent activity to calculate karma sources
            recent_activity = await self.get_user_recent_activity(username, "all", 100)
            if not recent_activity:
                return profile_stats  # Return basic stats if activity fetch fails
            
            # Calculate karma breakdown
            karma_breakdown = {
                "username": username,
                "total_karma": profile_stats["total_karma"],
                "link_karma": profile_stats["link_karma"],
                "comment_karma": profile_stats["comment_karma"],
                "awardee_karma": profile_stats["awardee_karma"],
                "awarder_karma": profile_stats["awarder_karma"],
                "recent_submission_karma": sum(s["score"] for s in recent_activity["submissions"]),
                "recent_comment_karma": sum(c["score"] for c in recent_activity["comments"]),
                "karma_by_subreddit": {},
                "karma_distribution": {
                    "link_percentage": round((profile_stats["link_karma"] / max(profile_stats["total_karma"], 1)) * 100, 2),
                    "comment_percentage": round((profile_stats["comment_karma"] / max(profile_stats["total_karma"], 1)) * 100, 2),
                    "awardee_percentage": round((profile_stats["awardee_karma"] / max(profile_stats["total_karma"], 1)) * 100, 2),
                    "awarder_percentage": round((profile_stats["awarder_karma"] / max(profile_stats["total_karma"], 1)) * 100, 2)
                }
            }
            
            # Calculate karma by subreddit from recent activity
            subreddit_karma = {}
            
            for submission in recent_activity["submissions"]:
                subreddit = submission["subreddit"]
                if subreddit not in subreddit_karma:
                    subreddit_karma[subreddit] = {"submission_karma": 0, "comment_karma": 0}
                subreddit_karma[subreddit]["submission_karma"] += submission["score"]
            
            for comment in recent_activity["comments"]:
                subreddit = comment["subreddit"]
                if subreddit not in subreddit_karma:
                    subreddit_karma[subreddit] = {"submission_karma": 0, "comment_karma": 0}
                subreddit_karma[subreddit]["comment_karma"] += comment["score"]
            
            # Sort subreddits by total karma
            for subreddit, karma_data in subreddit_karma.items():
                total_karma = karma_data["submission_karma"] + karma_data["comment_karma"]
                karma_breakdown["karma_by_subreddit"][subreddit] = {
                    **karma_data,
                    "total_karma": total_karma
                }
            
            # Sort by total karma
            karma_breakdown["karma_by_subreddit"] = dict(
                sorted(
                    karma_breakdown["karma_by_subreddit"].items(),
                    key=lambda x: x[1]["total_karma"],
                    reverse=True
                )
            )
            
            self.logger.info(f"Successfully calculated karma breakdown for user '{username}'")
            return karma_breakdown
            
        except Exception as e:
            self.logger.error(f"Error calculating karma breakdown for user '{username}': {str(e)}")
            return None
    
    def _get_most_active_subreddits(self, activity_data: Dict[str, Any]) -> Dict[str, int]:
        """Get most active subreddits from activity data."""
        subreddit_counts = {}
        
        # Count submissions by subreddit
        for submission in activity_data["submissions"]:
            subreddit = submission["subreddit"]
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        # Count comments by subreddit
        for comment in activity_data["comments"]:
            subreddit = comment["subreddit"]
            subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
        
        # Sort by activity count and return top 10
        sorted_subreddits = sorted(
            subreddit_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_subreddits[:10])