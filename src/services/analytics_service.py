"""
Analytics service with real-time Reddit metrics fetching.
"""

import logging
from typing import Dict, Any, Optional, List

from src.storage.json_storage import JsonStorage
from src.clients.reddit_client import RedditClient
from src.models.common import format_timestamp

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics with real-time Reddit metrics."""
    
    def __init__(self, json_storage: JsonStorage, reddit_client: RedditClient):
        """Initialize the analytics service."""
        self.json_storage = json_storage
        self.reddit_client = reddit_client
        self.logger = logger
    
    async def get_engagement_report(
        self,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get engagement report with latest karma and comment counts.
        
        This method fetches the latest metrics from Reddit for each posted response.
        """
        try:
            # Load posted responses log
            all_responses = self.json_storage.load_data("posted_responses.json")
            
            # Filter by organization if specified
            if organization_id:
                # We'd need to track organization_id in the posted responses
                # For now, we'll analyze all responses
                pass
            
            # Filter only successful posts
            successful_responses = [r for r in all_responses if r.get("success", False)]
            
            if not successful_responses:
                return {
                    "total_responses": 0,
                    "successful_responses": 0,
                    "failed_responses": len([r for r in all_responses if not r.get("success", False)]),
                    "engagement_metrics": {},
                    "message": "No successful responses found"
                }
            
            # Fetch latest metrics from Reddit
            engagement_metrics = await self._fetch_latest_metrics(successful_responses)
            
            # Calculate summary statistics
            total_karma = sum(metrics.get("current_score", 0) for metrics in engagement_metrics.values())
            avg_karma = total_karma / len(engagement_metrics) if engagement_metrics else 0
            
            # Response type breakdown
            response_types = {}
            for response in successful_responses:
                resp_type = response.get("response_type", "unknown")
                response_types[resp_type] = response_types.get(resp_type, 0) + 1
            
            return {
                "total_responses": len(all_responses),
                "successful_responses": len(successful_responses),
                "failed_responses": len(all_responses) - len(successful_responses),
                "total_karma_earned": total_karma,
                "average_karma_per_response": round(avg_karma, 2),
                "response_type_breakdown": response_types,
                "engagement_metrics": engagement_metrics,
                "last_updated": format_timestamp(self._get_current_timestamp())
            }
            
        except Exception as e:
            self.logger.error(f"Error generating engagement report: {str(e)}")
            return {
                "error": str(e),
                "total_responses": 0,
                "successful_responses": 0,
                "failed_responses": 0
            }
    
    async def _fetch_latest_metrics(
        self,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch latest karma and engagement metrics from Reddit."""
        metrics = {}
        
        try:
            async with self.reddit_client:
                for response in responses:
                    response_id = response.get("id")
                    target_id = response.get("target_id")
                    response_type = response.get("response_type")
                    posted_at = response.get("posted_at")
                    
                    if not target_id or not response_type:
                        continue
                    
                    try:
                        if response_type == "post_comment":
                            # For post comments, get the post score and comment count
                            current_score = await self.reddit_client.get_post_score(target_id)
                            post_info = await self.reddit_client.get_post_info(target_id)
                            comment_count = post_info.get("num_comments", 0)
                            
                            metrics[response_id] = {
                                "target_id": target_id,
                                "response_type": response_type,
                                "current_score": current_score,
                                "comment_count": comment_count,
                                "posted_at": format_timestamp(posted_at),
                                "target_type": "post"
                            }
                            
                        elif response_type == "comment_reply":
                            # For comment replies, get the comment score
                            current_score = await self.reddit_client.get_comment_score(target_id)
                            
                            metrics[response_id] = {
                                "target_id": target_id,
                                "response_type": response_type,
                                "current_score": current_score,
                                "posted_at": format_timestamp(posted_at),
                                "target_type": "comment"
                            }
                        
                        # Add a small delay to respect rate limits
                        import asyncio
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        self.logger.warning(f"Error fetching metrics for {target_id}: {str(e)}")
                        # Add entry with error info
                        metrics[response_id] = {
                            "target_id": target_id,
                            "response_type": response_type,
                            "error": str(e),
                            "posted_at": format_timestamp(posted_at)
                        }
                        continue
            
        except Exception as e:
            self.logger.error(f"Error in batch metrics fetching: {str(e)}")
        
        return metrics
    
    def get_posting_history(
        self,
        organization_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get posting history with basic statistics."""
        try:
            all_responses = self.json_storage.load_data("posted_responses.json")
            
            # Sort by posted_at (most recent first)
            all_responses.sort(key=lambda x: x.get("posted_at", 0), reverse=True)
            
            # Limit results
            recent_responses = all_responses[:limit]
            
            # Calculate basic stats
            successful_count = len([r for r in all_responses if r.get("success", False)])
            failed_count = len(all_responses) - successful_count
            
            # Format responses for display
            formatted_responses = []
            for response in recent_responses:
                formatted_responses.append({
                    "id": response.get("id"),
                    "target_id": response.get("target_id"),
                    "response_type": response.get("response_type"),
                    "posted_at": format_timestamp(response.get("posted_at", 0)),
                    "success": response.get("success", False),
                    "error": response.get("error"),
                    "content_preview": response.get("response_content", "")[:100] + "..."
                })
            
            return {
                "total_responses": len(all_responses),
                "successful_responses": successful_count,
                "failed_responses": failed_count,
                "success_rate": round((successful_count / len(all_responses) * 100), 2) if all_responses else 0,
                "recent_responses": formatted_responses
            }
            
        except Exception as e:
            self.logger.error(f"Error getting posting history: {str(e)}")
            return {
                "error": str(e),
                "total_responses": 0,
                "recent_responses": []
            }
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        from src.models.common import get_current_timestamp
        return get_current_timestamp()