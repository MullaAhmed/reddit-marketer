"""
Statistics and analytics service for engagement tracking and insights.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.managers.stats_manager import StatsManager
from app.clients.reddit_client import RedditClient

logger = logging.getLogger(__name__)


class StatsService:
    """
    Service for statistics collection, analysis, and engagement tracking.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize stats service."""
        self.data_dir = data_dir
        self.stats_manager = StatsManager(data_dir)
        self.logger = logger
    
    # ========================================
    # ENGAGEMENT COLLECTION
    # ========================================
    
    async def collect_response_engagement(
        self,
        reddit_comment_ids: List[str],
        reddit_credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Collect current engagement metrics for posted responses.
        
        Args:
            reddit_comment_ids: List of Reddit comment IDs to check
            reddit_credentials: Reddit API credentials
            
        Returns:
            Dict with collection results and updated metrics
        """
        try:
            reddit_client = RedditClient(
                client_id=reddit_credentials["client_id"],
                client_secret=reddit_credentials["client_secret"],
                username=reddit_credentials.get("username"),
                password=reddit_credentials.get("password"),
                data_dir=self.data_dir
            )
            
            updated_count = 0
            failed_count = 0
            engagement_updates = []
            
            async with reddit_client:
                for comment_id in reddit_comment_ids:
                    try:
                        # Get comment details from Reddit
                        comment = await reddit_client.reddit.comment(id=comment_id)
                        await comment.load()
                        
                        # Count replies
                        replies_count = len(comment.replies) if hasattr(comment, 'replies') else 0
                        
                        # Update engagement in stats manager
                        success = self.stats_manager.update_response_engagement(
                            reddit_comment_id=comment_id,
                            current_score=comment.score,
                            replies_count=replies_count
                        )
                        
                        if success:
                            updated_count += 1
                            engagement_updates.append({
                                "comment_id": comment_id,
                                "score": comment.score,
                                "replies": replies_count,
                                "updated": True
                            })
                        else:
                            failed_count += 1
                            engagement_updates.append({
                                "comment_id": comment_id,
                                "updated": False,
                                "error": "Failed to update in database"
                            })
                            
                    except Exception as e:
                        failed_count += 1
                        engagement_updates.append({
                            "comment_id": comment_id,
                            "updated": False,
                            "error": str(e)
                        })
                        self.logger.warning(f"Failed to collect engagement for comment {comment_id}: {str(e)}")
            
            self.logger.info(f"Collected engagement for {updated_count}/{len(reddit_comment_ids)} comments")
            
            return {
                "total_comments": len(reddit_comment_ids),
                "updated_successfully": updated_count,
                "failed_updates": failed_count,
                "engagement_updates": engagement_updates,
                "collection_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting response engagement: {str(e)}")
            return {
                "error": str(e),
                "total_comments": len(reddit_comment_ids),
                "updated_successfully": 0,
                "failed_updates": len(reddit_comment_ids)
            }
    
    async def collect_campaign_engagement(
        self,
        campaign_id: str,
        reddit_credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Collect engagement metrics for all responses in a campaign.
        
        Args:
            campaign_id: Campaign ID to collect engagement for
            reddit_credentials: Reddit API credentials
            
        Returns:
            Dict with collection results
        """
        try:
            # Get campaign analysis to find all comment IDs
            campaign_analysis = self.stats_manager.analyze_campaign_performance(campaign_id)
            
            if "error" in campaign_analysis:
                return {"error": f"Campaign analysis failed: {campaign_analysis['error']}"}
            
            # Extract comment IDs from engagement records
            engagement_records = self.stats_manager.json_repository.filter_items(
                "engagement_stats.json",
                {"campaign_id": campaign_id}
            )
            
            comment_ids = [record.get("reddit_comment_id") for record in engagement_records if record.get("reddit_comment_id")]
            
            if not comment_ids:
                return {
                    "campaign_id": campaign_id,
                    "message": "No comment IDs found for engagement collection",
                    "total_comments": 0
                }
            
            # Collect engagement for all comments
            result = await self.collect_response_engagement(comment_ids, reddit_credentials)
            result["campaign_id"] = campaign_id
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error collecting campaign engagement: {str(e)}")
            return {"error": str(e), "campaign_id": campaign_id}
    
    # ========================================
    # ANALYTICS AND INSIGHTS
    # ========================================
    
    def get_campaign_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a campaign."""
        try:
            return self.stats_manager.analyze_campaign_performance(campaign_id)
        except Exception as e:
            self.logger.error(f"Error getting campaign analytics: {str(e)}")
            return {"error": str(e)}
    
    def get_organization_analytics(self, org_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for an organization."""
        try:
            return self.stats_manager.get_organization_analytics(org_id)
        except Exception as e:
            self.logger.error(f"Error getting organization analytics: {str(e)}")
            return {"error": str(e)}
    
    def get_subreddit_performance(self, subreddit: str) -> Dict[str, Any]:
        """Get performance analytics for a specific subreddit."""
        try:
            return self.stats_manager.get_subreddit_analytics(subreddit)
        except Exception as e:
            self.logger.error(f"Error getting subreddit performance: {str(e)}")
            return {"error": str(e)}
    
    def get_trending_subreddits(
        self,
        org_id: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending subreddits based on performance."""
        try:
            return self.stats_manager.get_trending_subreddits(org_id, limit)
        except Exception as e:
            self.logger.error(f"Error getting trending subreddits: {str(e)}")
            return []
    
    def get_engagement_insights(
        self,
        campaign_id: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get engagement insights and trends."""
        try:
            return self.stats_manager.get_engagement_insights(campaign_id, days)
        except Exception as e:
            self.logger.error(f"Error getting engagement insights: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # PERFORMANCE TRACKING
    # ========================================
    
    def track_campaign_performance(
        self,
        campaign_id: str,
        subreddit_metrics: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Track performance metrics for a campaign across subreddits.
        
        Args:
            campaign_id: Campaign ID
            subreddit_metrics: Dict mapping subreddit names to metrics
            
        Returns:
            Success status
        """
        try:
            success_count = 0
            
            for subreddit, metrics in subreddit_metrics.items():
                success = self.stats_manager.track_subreddit_performance(
                    subreddit=subreddit,
                    campaign_id=campaign_id,
                    posts_found=metrics.get("posts_found", 0),
                    responses_posted=metrics.get("responses_posted", 0),
                    avg_engagement=metrics.get("avg_engagement", 0.0)
                )
                
                if success:
                    success_count += 1
            
            self.logger.info(f"Tracked performance for {success_count}/{len(subreddit_metrics)} subreddits")
            return success_count == len(subreddit_metrics)
            
        except Exception as e:
            self.logger.error(f"Error tracking campaign performance: {str(e)}")
            return False
    
    def initialize_response_tracking(
        self,
        campaign_id: str,
        response_id: str,
        reddit_comment_id: str,
        initial_score: int = 0
    ) -> bool:
        """Initialize tracking for a newly posted response."""
        try:
            return self.stats_manager.track_response_engagement(
                campaign_id=campaign_id,
                response_id=response_id,
                reddit_comment_id=reddit_comment_id,
                initial_score=initial_score
            )
        except Exception as e:
            self.logger.error(f"Error initializing response tracking: {str(e)}")
            return False
    
    # ========================================
    # REPORTING AND EXPORTS
    # ========================================
    
    def generate_campaign_report(self, campaign_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for a campaign."""
        try:
            # Get campaign analytics
            analytics = self.get_campaign_analytics(campaign_id)
            
            if "error" in analytics:
                return analytics
            
            # Get engagement insights for this campaign
            insights = self.get_engagement_insights(campaign_id=campaign_id)
            
            # Combine into comprehensive report
            report = {
                "campaign_id": campaign_id,
                "campaign_name": analytics.get("campaign_name", "Unknown"),
                "report_generated": datetime.now(timezone.utc).isoformat(),
                "performance_summary": {
                    "total_responses": analytics.get("total_responses_posted", 0),
                    "successful_responses": analytics.get("successful_responses", 0),
                    "success_rate": analytics.get("success_rate", 0),
                    "engagement_score": analytics.get("engagement_metrics", {}).get("total_score", 0),
                    "total_replies": analytics.get("engagement_metrics", {}).get("total_replies", 0)
                },
                "subreddit_breakdown": analytics.get("subreddit_performance", {}),
                "engagement_insights": insights,
                "recommendations": self._generate_recommendations(analytics)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating campaign report: {str(e)}")
            return {"error": str(e)}
    
    def generate_organization_report(self, org_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for an organization."""
        try:
            # Get organization analytics
            analytics = self.get_organization_analytics(org_id)
            
            if "error" in analytics:
                return analytics
            
            # Get trending subreddits for this org
            trending = self.get_trending_subreddits(org_id=org_id, limit=5)
            
            # Get overall engagement insights
            insights = self.get_engagement_insights(days=30)
            
            report = {
                "organization_id": org_id,
                "report_generated": datetime.now(timezone.utc).isoformat(),
                "overview": {
                    "total_campaigns": analytics.get("total_campaigns", 0),
                    "overall_metrics": analytics.get("overall_metrics", {}),
                    "top_performing_subreddits": trending[:3]
                },
                "detailed_analytics": analytics,
                "engagement_insights": insights,
                "trending_subreddits": trending,
                "recommendations": self._generate_org_recommendations(analytics, trending)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating organization report: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on campaign analytics."""
        recommendations = []
        
        try:
            success_rate = analytics.get("success_rate", 0)
            avg_score = analytics.get("engagement_metrics", {}).get("average_score", 0)
            
            if success_rate < 50:
                recommendations.append("Consider improving response relevance - success rate is below 50%")
            
            if avg_score < 1:
                recommendations.append("Focus on providing more value - average engagement score is low")
            
            subreddit_performance = analytics.get("subreddit_performance", {})
            if subreddit_performance:
                best_subreddit = max(subreddit_performance.items(), key=lambda x: x[1].get("total_score", 0))
                recommendations.append(f"Consider focusing more on r/{best_subreddit[0]} - it shows the best engagement")
            
            if len(recommendations) == 0:
                recommendations.append("Campaign is performing well - continue current strategy")
            
        except Exception as e:
            self.logger.warning(f"Error generating recommendations: {str(e)}")
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations
    
    def _generate_org_recommendations(
        self,
        analytics: Dict[str, Any],
        trending: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations for organization based on analytics."""
        recommendations = []
        
        try:
            overall_metrics = analytics.get("overall_metrics", {})
            success_rate = overall_metrics.get("success_rate", 0)
            
            if success_rate < 60:
                recommendations.append("Overall success rate could be improved - consider refining targeting criteria")
            
            if trending:
                top_subreddit = trending[0]
                recommendations.append(f"r/{top_subreddit['subreddit']} is your top performer - consider expanding presence there")
            
            total_campaigns = analytics.get("total_campaigns", 0)
            if total_campaigns < 5:
                recommendations.append("Consider running more campaigns to gather better performance data")
            
            if len(recommendations) == 0:
                recommendations.append("Organization is performing well across campaigns")
            
        except Exception as e:
            self.logger.warning(f"Error generating org recommendations: {str(e)}")
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up old statistics data."""
        try:
            return self.stats_manager.cleanup_old_stats(days_to_keep)
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            return {"error": str(e)}