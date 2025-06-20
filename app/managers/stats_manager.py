"""
Statistics and analytics manager for engagement tracking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from app.storage.json_storage import JsonStorage
from app.managers.campaign_manager import CampaignManager
from app.managers.document_manager import DocumentManager

logger = logging.getLogger(__name__)


class StatsManager:
    """
    Manager for collecting and analyzing engagement statistics and analytics.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize stats manager."""
        self.data_dir = data_dir
        self.json_storage = JsonStorage(data_dir)
        self.campaign_manager = CampaignManager(data_dir)
        self.document_manager = DocumentManager(data_dir)
        self.logger = logger
        
        # Initialize JSON files for stats tracking
        self.json_storage.init_file("engagement_stats.json", [])
        self.json_storage.init_file("response_analytics.json", [])
        self.json_storage.init_file("subreddit_performance.json", [])
    
    # ========================================
    # ENGAGEMENT TRACKING
    # ========================================
    
    def track_response_engagement(
        self,
        campaign_id: str,
        response_id: str,
        reddit_comment_id: str,
        initial_score: int = 0
    ) -> bool:
        """Track initial engagement for a posted response."""
        try:
            engagement_record = {
                "id": f"{campaign_id}_{response_id}",
                "campaign_id": campaign_id,
                "response_id": response_id,
                "reddit_comment_id": reddit_comment_id,
                "initial_score": initial_score,
                "current_score": initial_score,
                "score_history": [{"timestamp": datetime.now(timezone.utc).isoformat(), "score": initial_score}],
                "replies_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return self.json_storage.update_item("engagement_stats.json", engagement_record)
            
        except Exception as e:
            self.logger.error(f"Error tracking response engagement: {str(e)}")
            return False
    
    def update_response_engagement(
        self,
        reddit_comment_id: str,
        current_score: int,
        replies_count: int = None
    ) -> bool:
        """Update engagement metrics for a response."""
        try:
            # Find the engagement record
            engagement_records = self.json_storage.load_data("engagement_stats.json")
            
            for record in engagement_records:
                if record.get("reddit_comment_id") == reddit_comment_id:
                    # Update score
                    record["current_score"] = current_score
                    
                    # Add to score history
                    if "score_history" not in record:
                        record["score_history"] = []
                    
                    record["score_history"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "score": current_score
                    })
                    
                    # Update replies count if provided
                    if replies_count is not None:
                        record["replies_count"] = replies_count
                    
                    record["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Save updated data
                    return self.json_storage.save_data("engagement_stats.json", engagement_records)
            
            return False  # Record not found
            
        except Exception as e:
            self.logger.error(f"Error updating response engagement: {str(e)}")
            return False
    
    def get_response_engagement(self, reddit_comment_id: str) -> Optional[Dict[str, Any]]:
        """Get engagement data for a specific response."""
        try:
            engagement_records = self.json_storage.load_data("engagement_stats.json")
            
            for record in engagement_records:
                if record.get("reddit_comment_id") == reddit_comment_id:
                    return record
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting response engagement: {str(e)}")
            return None
    
    # ========================================
    # CAMPAIGN ANALYTICS
    # ========================================
    
    def analyze_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Analyze overall performance of a campaign."""
        try:
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return {"error": "Campaign not found"}
            
            # Get engagement data for all responses in this campaign
            engagement_records = self.json_storage.filter_items(
                "engagement_stats.json",
                {"campaign_id": campaign_id}
            )
            
            # Calculate metrics
            total_responses = len(campaign.posted_responses)
            successful_responses = len([r for r in campaign.posted_responses if r.posting_successful])
            
            if engagement_records:
                total_score = sum(record.get("current_score", 0) for record in engagement_records)
                total_replies = sum(record.get("replies_count", 0) for record in engagement_records)
                avg_score = total_score / len(engagement_records) if engagement_records else 0
                avg_replies = total_replies / len(engagement_records) if engagement_records else 0
            else:
                total_score = 0
                total_replies = 0
                avg_score = 0
                avg_replies = 0
            
            # Subreddit performance breakdown
            subreddit_performance = {}
            for post in campaign.target_posts:
                subreddit = post.subreddit
                if subreddit not in subreddit_performance:
                    subreddit_performance[subreddit] = {
                        "posts_targeted": 0,
                        "responses_posted": 0,
                        "total_score": 0,
                        "total_replies": 0
                    }
                
                subreddit_performance[subreddit]["posts_targeted"] += 1
                
                # Check if we posted a response to this post
                for response in campaign.posted_responses:
                    if response.target_post_id == post.id and response.posting_successful:
                        subreddit_performance[subreddit]["responses_posted"] += 1
                        
                        # Get engagement data
                        engagement = self.get_response_engagement(response.reddit_comment_id)
                        if engagement:
                            subreddit_performance[subreddit]["total_score"] += engagement.get("current_score", 0)
                            subreddit_performance[subreddit]["total_replies"] += engagement.get("replies_count", 0)
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "total_responses_posted": total_responses,
                "successful_responses": successful_responses,
                "success_rate": (successful_responses / total_responses * 100) if total_responses > 0 else 0,
                "engagement_metrics": {
                    "total_score": total_score,
                    "average_score": avg_score,
                    "total_replies": total_replies,
                    "average_replies": avg_replies
                },
                "subreddit_performance": subreddit_performance,
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing campaign performance: {str(e)}")
            return {"error": str(e)}
    
    def get_organization_analytics(self, org_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for an organization."""
        try:
            campaigns = self.campaign_manager.list_campaigns_by_organization(org_id)
            
            if not campaigns:
                return {
                    "organization_id": org_id,
                    "total_campaigns": 0,
                    "message": "No campaigns found"
                }
            
            # Aggregate metrics across all campaigns
            total_responses = 0
            successful_responses = 0
            total_engagement_score = 0
            total_replies = 0
            subreddit_stats = {}
            
            for campaign in campaigns:
                campaign_analysis = self.analyze_campaign_performance(campaign.id)
                
                if "error" not in campaign_analysis:
                    total_responses += campaign_analysis.get("total_responses_posted", 0)
                    successful_responses += campaign_analysis.get("successful_responses", 0)
                    
                    engagement = campaign_analysis.get("engagement_metrics", {})
                    total_engagement_score += engagement.get("total_score", 0)
                    total_replies += engagement.get("total_replies", 0)
                    
                    # Aggregate subreddit performance
                    for subreddit, stats in campaign_analysis.get("subreddit_performance", {}).items():
                        if subreddit not in subreddit_stats:
                            subreddit_stats[subreddit] = {
                                "posts_targeted": 0,
                                "responses_posted": 0,
                                "total_score": 0,
                                "total_replies": 0
                            }
                        
                        subreddit_stats[subreddit]["posts_targeted"] += stats.get("posts_targeted", 0)
                        subreddit_stats[subreddit]["responses_posted"] += stats.get("responses_posted", 0)
                        subreddit_stats[subreddit]["total_score"] += stats.get("total_score", 0)
                        subreddit_stats[subreddit]["total_replies"] += stats.get("total_replies", 0)
            
            return {
                "organization_id": org_id,
                "total_campaigns": len(campaigns),
                "overall_metrics": {
                    "total_responses_posted": total_responses,
                    "successful_responses": successful_responses,
                    "success_rate": (successful_responses / total_responses * 100) if total_responses > 0 else 0,
                    "total_engagement_score": total_engagement_score,
                    "average_score_per_response": (total_engagement_score / successful_responses) if successful_responses > 0 else 0,
                    "total_replies": total_replies,
                    "average_replies_per_response": (total_replies / successful_responses) if successful_responses > 0 else 0
                },
                "subreddit_performance": subreddit_stats,
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting organization analytics: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # SUBREDDIT PERFORMANCE TRACKING
    # ========================================
    
    def track_subreddit_performance(
        self,
        subreddit: str,
        campaign_id: str,
        posts_found: int,
        responses_posted: int,
        avg_engagement: float = 0.0
    ) -> bool:
        """Track performance metrics for a specific subreddit."""
        try:
            performance_record = {
                "id": f"{subreddit}_{campaign_id}",
                "subreddit": subreddit,
                "campaign_id": campaign_id,
                "posts_found": posts_found,
                "responses_posted": responses_posted,
                "avg_engagement": avg_engagement,
                "tracked_at": datetime.now(timezone.utc).isoformat()
            }
            
            return self.json_storage.update_item("subreddit_performance.json", performance_record)
            
        except Exception as e:
            self.logger.error(f"Error tracking subreddit performance: {str(e)}")
            return False
    
    def get_subreddit_analytics(self, subreddit: str) -> Dict[str, Any]:
        """Get analytics for a specific subreddit across all campaigns."""
        try:
            performance_records = self.json_storage.filter_items(
                "subreddit_performance.json",
                {"subreddit": subreddit}
            )
            
            if not performance_records:
                return {
                    "subreddit": subreddit,
                    "message": "No performance data found"
                }
            
            total_posts_found = sum(record.get("posts_found", 0) for record in performance_records)
            total_responses_posted = sum(record.get("responses_posted", 0) for record in performance_records)
            avg_engagement = sum(record.get("avg_engagement", 0) for record in performance_records) / len(performance_records)
            
            return {
                "subreddit": subreddit,
                "campaigns_involved": len(performance_records),
                "total_posts_found": total_posts_found,
                "total_responses_posted": total_responses_posted,
                "response_rate": (total_responses_posted / total_posts_found * 100) if total_posts_found > 0 else 0,
                "average_engagement": avg_engagement,
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting subreddit analytics: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # TRENDING AND INSIGHTS
    # ========================================
    
    def get_trending_subreddits(self, org_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending subreddits based on engagement performance."""
        try:
            # Get all subreddit performance records
            if org_id:
                # Filter by organization campaigns
                org_campaigns = self.campaign_manager.list_campaigns_by_organization(org_id)
                campaign_ids = [c.id for c in org_campaigns]
                
                all_records = self.json_storage.load_data("subreddit_performance.json")
                performance_records = [r for r in all_records if r.get("campaign_id") in campaign_ids]
            else:
                performance_records = self.json_storage.load_data("subreddit_performance.json")
            
            # Aggregate by subreddit
            subreddit_aggregates = {}
            for record in performance_records:
                subreddit = record.get("subreddit")
                if subreddit not in subreddit_aggregates:
                    subreddit_aggregates[subreddit] = {
                        "subreddit": subreddit,
                        "total_posts": 0,
                        "total_responses": 0,
                        "total_engagement": 0,
                        "campaign_count": 0
                    }
                
                subreddit_aggregates[subreddit]["total_posts"] += record.get("posts_found", 0)
                subreddit_aggregates[subreddit]["total_responses"] += record.get("responses_posted", 0)
                subreddit_aggregates[subreddit]["total_engagement"] += record.get("avg_engagement", 0)
                subreddit_aggregates[subreddit]["campaign_count"] += 1
            
            # Calculate performance scores and sort
            trending_subreddits = []
            for subreddit_data in subreddit_aggregates.values():
                response_rate = (subreddit_data["total_responses"] / subreddit_data["total_posts"] * 100) if subreddit_data["total_posts"] > 0 else 0
                avg_engagement = subreddit_data["total_engagement"] / subreddit_data["campaign_count"] if subreddit_data["campaign_count"] > 0 else 0
                
                # Simple performance score (can be made more sophisticated)
                performance_score = (response_rate * 0.6) + (avg_engagement * 0.4)
                
                trending_subreddits.append({
                    **subreddit_data,
                    "response_rate": response_rate,
                    "avg_engagement": avg_engagement,
                    "performance_score": performance_score
                })
            
            # Sort by performance score
            trending_subreddits.sort(key=lambda x: x["performance_score"], reverse=True)
            
            return trending_subreddits[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting trending subreddits: {str(e)}")
            return []
    
    def get_engagement_insights(self, campaign_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get engagement insights and trends."""
        try:
            # Get engagement records for the specified period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            engagement_records = self.json_storage.load_data("engagement_stats.json")
            
            # Filter by campaign if specified
            if campaign_id:
                engagement_records = [r for r in engagement_records if r.get("campaign_id") == campaign_id]
            
            # Filter by date
            recent_records = []
            for record in engagement_records:
                try:
                    created_at = datetime.fromisoformat(record.get("created_at", "").replace("Z", "+00:00"))
                    if created_at >= cutoff_date:
                        recent_records.append(record)
                except ValueError:
                    continue
            
            if not recent_records:
                return {
                    "message": "No engagement data found for the specified period",
                    "period_days": days
                }
            
            # Calculate insights
            total_responses = len(recent_records)
            total_score = sum(record.get("current_score", 0) for record in recent_records)
            total_replies = sum(record.get("replies_count", 0) for record in recent_records)
            
            positive_responses = len([r for r in recent_records if r.get("current_score", 0) > 0])
            negative_responses = len([r for r in recent_records if r.get("current_score", 0) < 0])
            neutral_responses = total_responses - positive_responses - negative_responses
            
            return {
                "period_days": days,
                "total_responses": total_responses,
                "engagement_summary": {
                    "total_score": total_score,
                    "average_score": total_score / total_responses if total_responses > 0 else 0,
                    "total_replies": total_replies,
                    "average_replies": total_replies / total_responses if total_responses > 0 else 0
                },
                "sentiment_breakdown": {
                    "positive_responses": positive_responses,
                    "negative_responses": negative_responses,
                    "neutral_responses": neutral_responses,
                    "positive_rate": (positive_responses / total_responses * 100) if total_responses > 0 else 0
                },
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting engagement insights: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def cleanup_old_stats(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up old statistics data."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            # Clean engagement stats
            engagement_records = self.json_storage.load_data("engagement_stats.json")
            filtered_engagement = []
            
            for record in engagement_records:
                try:
                    created_at = datetime.fromisoformat(record.get("created_at", "").replace("Z", "+00:00"))
                    if created_at >= cutoff_date:
                        filtered_engagement.append(record)
                except ValueError:
                    # Keep records with invalid dates
                    filtered_engagement.append(record)
            
            # Clean subreddit performance
            performance_records = self.json_storage.load_data("subreddit_performance.json")
            filtered_performance = []
            
            for record in performance_records:
                try:
                    tracked_at = datetime.fromisoformat(record.get("tracked_at", "").replace("Z", "+00:00"))
                    if tracked_at >= cutoff_date:
                        filtered_performance.append(record)
                except ValueError:
                    # Keep records with invalid dates
                    filtered_performance.append(record)
            
            # Save cleaned data
            self.json_storage.save_data("engagement_stats.json", filtered_engagement)
            self.json_storage.save_data("subreddit_performance.json", filtered_performance)
            
            return {
                "engagement_records_removed": len(engagement_records) - len(filtered_engagement),
                "performance_records_removed": len(performance_records) - len(filtered_performance),
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old stats: {str(e)}")
            return {"error": str(e)}