"""
Analytics service for high-level analytics and reporting.
"""

import logging
from typing import Dict, Any, Optional

from app.managers.analytics_manager import AnalyticsManager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for analytics operations that provides a high-level interface
    for accessing various analytics and reports.
    """
    
    def __init__(self, analytics_manager: AnalyticsManager):
        """Initialize the analytics service."""
        self.analytics_manager = analytics_manager
        self.logger = logger
    
    # ========================================
    # CAMPAIGN ANALYTICS
    # ========================================
    
    def get_campaign_engagement_report(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed engagement report for a specific campaign."""
        try:
            campaign_stats = self.analytics_manager.get_campaign_stats(campaign_id)
            engagement_metrics = self.analytics_manager.get_engagement_metrics(campaign_id=campaign_id)
            
            if "error" in campaign_stats:
                return campaign_stats
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign_stats.get("campaign_name"),
                "status": campaign_stats.get("status"),
                "basic_stats": campaign_stats,
                "engagement_metrics": engagement_metrics,
                "report_type": "campaign_engagement"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating campaign engagement report for {campaign_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_organization_performance_report(self, org_id: str) -> Dict[str, Any]:
        """Get comprehensive performance report for an organization."""
        try:
            comprehensive_report = self.analytics_manager.get_comprehensive_report(org_id)
            
            if "error" in comprehensive_report:
                return comprehensive_report
            
            # Add performance insights
            campaign_stats = comprehensive_report.get("campaign_stats", {})
            engagement_metrics = comprehensive_report.get("engagement_metrics", {})
            
            insights = []
            
            # Generate insights based on data
            if campaign_stats.get("success_rate", 0) > 80:
                insights.append("High success rate indicates effective response generation")
            elif campaign_stats.get("success_rate", 0) < 50:
                insights.append("Low success rate suggests need for response quality improvement")
            
            if engagement_metrics.get("engagement_rate", 0) > 50:
                insights.append("Good engagement rate shows effective post targeting")
            elif engagement_metrics.get("engagement_rate", 0) < 20:
                insights.append("Low engagement rate indicates need for better post selection")
            
            comprehensive_report["performance_insights"] = insights
            comprehensive_report["report_type"] = "organization_performance"
            
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"Error generating organization performance report for {org_id}: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # PLATFORM ANALYTICS
    # ========================================
    
    def get_overall_platform_metrics(self) -> Dict[str, Any]:
        """Get overall platform metrics and insights."""
        try:
            platform_overview = self.analytics_manager.get_platform_overview()
            
            if "error" in platform_overview:
                return platform_overview
            
            # Add platform-level insights
            campaign_stats = platform_overview.get("campaign_stats", {})
            document_stats = platform_overview.get("document_stats", {})
            engagement_metrics = platform_overview.get("engagement_metrics", {})
            
            platform_insights = []
            
            # Platform health indicators
            total_campaigns = campaign_stats.get("total_campaigns", 0)
            active_campaigns = campaign_stats.get("active_campaigns", 0)
            total_orgs = campaign_stats.get("total_organizations", 0)
            
            if total_campaigns > 0:
                activity_rate = (active_campaigns / total_campaigns) * 100
                if activity_rate > 30:
                    platform_insights.append("High platform activity with many active campaigns")
                elif activity_rate < 10:
                    platform_insights.append("Low platform activity - consider user engagement strategies")
            
            if total_orgs > 0:
                avg_campaigns_per_org = campaign_stats.get("average_campaigns_per_org", 0)
                if avg_campaigns_per_org > 3:
                    platform_insights.append("Organizations are actively using the platform")
                elif avg_campaigns_per_org < 1:
                    platform_insights.append("Low adoption - organizations need more guidance")
            
            platform_overview["platform_insights"] = platform_insights
            platform_overview["report_type"] = "platform_overview"
            
            return platform_overview
            
        except Exception as e:
            self.logger.error(f"Error generating platform metrics: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # SUBREDDIT ANALYTICS
    # ========================================
    
    def get_subreddit_effectiveness_report(self, org_id: str = None) -> Dict[str, Any]:
        """Get report on subreddit effectiveness."""
        try:
            subreddit_performance = self.analytics_manager.get_subreddit_performance(org_id)
            
            if "error" in subreddit_performance:
                return subreddit_performance
            
            subreddit_data = subreddit_performance.get("subreddit_performance", {})
            
            # Rank subreddits by effectiveness
            ranked_subreddits = []
            for subreddit, stats in subreddit_data.items():
                effectiveness_score = (
                    stats.get("engagement_rate", 0) * 0.6 + 
                    stats.get("success_rate", 0) * 0.4
                )
                
                ranked_subreddits.append({
                    "subreddit": subreddit,
                    "effectiveness_score": effectiveness_score,
                    "stats": stats
                })
            
            # Sort by effectiveness score
            ranked_subreddits.sort(key=lambda x: x["effectiveness_score"], reverse=True)
            
            # Generate recommendations
            recommendations = []
            if ranked_subreddits:
                top_performer = ranked_subreddits[0]
                if top_performer["effectiveness_score"] > 70:
                    recommendations.append(f"r/{top_performer['subreddit']} is highly effective - consider similar communities")
                
                if len(ranked_subreddits) > 1:
                    bottom_performer = ranked_subreddits[-1]
                    if bottom_performer["effectiveness_score"] < 20:
                        recommendations.append(f"r/{bottom_performer['subreddit']} shows low effectiveness - review targeting strategy")
            
            return {
                "organization_id": org_id,
                "ranked_subreddits": ranked_subreddits,
                "total_subreddits_analyzed": len(ranked_subreddits),
                "recommendations": recommendations,
                "report_type": "subreddit_effectiveness"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating subreddit effectiveness report: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # TREND ANALYSIS
    # ========================================
    
    def get_campaign_trends(self, org_id: str = None) -> Dict[str, Any]:
        """Get campaign trend analysis."""
        try:
            if org_id:
                campaigns = self.analytics_manager.campaign_manager.list_campaigns_by_organization(org_id)
            else:
                campaigns = self.analytics_manager.campaign_manager.list_campaigns()
            
            if not campaigns:
                return {
                    "organization_id": org_id,
                    "trends": [],
                    "message": "No campaigns found for trend analysis"
                }
            
            # Sort campaigns by creation date
            campaigns.sort(key=lambda c: c.created_at)
            
            # Analyze trends over time
            trends = []
            
            # Success rate trend
            if len(campaigns) >= 3:
                recent_campaigns = campaigns[-3:]
                older_campaigns = campaigns[:-3] if len(campaigns) > 3 else []
                
                if older_campaigns:
                    recent_success_rate = sum(
                        len([r for r in c.posted_responses.values() if r.posting_successful]) / max(len(c.posted_responses), 1)
                        for c in recent_campaigns
                    ) / len(recent_campaigns) * 100
                    
                    older_success_rate = sum(
                        len([r for r in c.posted_responses.values() if r.posting_successful]) / max(len(c.posted_responses), 1)
                        for c in older_campaigns
                    ) / len(older_campaigns) * 100
                    
                    if recent_success_rate > older_success_rate + 10:
                        trends.append("Success rate is improving over time")
                    elif recent_success_rate < older_success_rate - 10:
                        trends.append("Success rate is declining - review strategy")
            
            # Campaign completion trend
            completed_campaigns = [c for c in campaigns if c.status == "completed"]
            if len(completed_campaigns) / len(campaigns) > 0.7:
                trends.append("High campaign completion rate indicates good execution")
            elif len(completed_campaigns) / len(campaigns) < 0.3:
                trends.append("Low completion rate - campaigns may need better planning")
            
            return {
                "organization_id": org_id,
                "campaigns_analyzed": len(campaigns),
                "trends": trends,
                "report_type": "campaign_trends"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating campaign trends: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_quick_stats(self, org_id: str) -> Dict[str, Any]:
        """Get quick overview stats for an organization."""
        try:
            campaign_stats = self.analytics_manager.get_organization_campaign_stats(org_id)
            document_stats = self.analytics_manager.get_organization_document_stats(org_id)
            
            return {
                "organization_id": org_id,
                "total_campaigns": campaign_stats.get("total_campaigns", 0),
                "active_campaigns": campaign_stats.get("active_campaigns", 0),
                "total_documents": document_stats.get("total_documents", 0),
                "success_rate": campaign_stats.get("success_rate", 0),
                "report_type": "quick_stats"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating quick stats for {org_id}: {str(e)}")
            return {"error": str(e)}