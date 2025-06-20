"""
Analytics manager for statistics calculation and aggregation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.managers.campaign_manager import CampaignManager
from app.managers.document_manager import DocumentManager

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """
    Manager for analytics data calculation and aggregation.
    Centralizes all statistics calculation logic.
    """
    
    def __init__(
        self,
        campaign_manager: CampaignManager,
        document_manager: DocumentManager
    ):
        """Initialize analytics manager."""
        self.campaign_manager = campaign_manager
        self.document_manager = document_manager
        self.logger = logger
    
    # ========================================
    # CAMPAIGN ANALYTICS
    # ========================================
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get statistics for a specific campaign."""
        try:
            campaign = self.campaign_manager.get_campaign(campaign_id)
            if not campaign:
                return {"error": "Campaign not found"}
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "organization_id": campaign.organization_id,
                "documents_selected": len(campaign.selected_document_ids),
                "subreddits_found": len(campaign.target_subreddits),
                "posts_found": len(campaign.target_posts),
                "responses_planned": len(campaign.planned_responses),
                "responses_posted": len(campaign.posted_responses),
                "successful_posts": len([r for r in campaign.posted_responses.values() if r.posting_successful]),
                "failed_posts": len([r for r in campaign.posted_responses.values() if not r.posting_successful]),
                "created_at": campaign.created_at,
                "updated_at": campaign.updated_at
            }
            
        except Exception as e:
            self.logger.error(f"Error getting campaign stats for {campaign_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_organization_campaign_stats(self, org_id: str) -> Dict[str, Any]:
        """Get campaign statistics for an organization."""
        try:
            campaigns = self.campaign_manager.list_campaigns_by_organization(org_id)
            
            if not campaigns:
                return {
                    "organization_id": org_id,
                    "total_campaigns": 0,
                    "active_campaigns": 0,
                    "completed_campaigns": 0,
                    "failed_campaigns": 0
                }
            
            status_counts = {}
            for campaign in campaigns:
                status = campaign.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total_responses_posted = sum(
                len(campaign.posted_responses) for campaign in campaigns
            )
            
            total_successful_posts = sum(
                len([r for r in campaign.posted_responses.values() if r.posting_successful])
                for campaign in campaigns
            )
            
            active_campaigns = self.campaign_manager.get_active_campaigns(org_id)
            
            return {
                "organization_id": org_id,
                "total_campaigns": len(campaigns),
                "active_campaigns": len(active_campaigns),
                "completed_campaigns": status_counts.get("completed", 0),
                "failed_campaigns": status_counts.get("failed", 0),
                "status_breakdown": status_counts,
                "total_responses_posted": total_responses_posted,
                "total_successful_posts": total_successful_posts,
                "success_rate": (total_successful_posts / total_responses_posted * 100) if total_responses_posted > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting organization campaign stats for {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_global_campaign_stats(self) -> Dict[str, Any]:
        """Get global campaign statistics."""
        try:
            campaigns = self.campaign_manager.list_campaigns()
            
            if not campaigns:
                return {
                    "total_campaigns": 0,
                    "active_campaigns": 0,
                    "completed_campaigns": 0,
                    "failed_campaigns": 0
                }
            
            status_counts = {}
            for campaign in campaigns:
                status = campaign.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            organizations = set(campaign.organization_id for campaign in campaigns)
            
            total_responses_posted = sum(
                len(campaign.posted_responses) for campaign in campaigns
            )
            
            total_successful_posts = sum(
                len([r for r in campaign.posted_responses.values() if r.posting_successful])
                for campaign in campaigns
            )
            
            active_campaigns = self.campaign_manager.get_active_campaigns()
            
            return {
                "total_campaigns": len(campaigns),
                "total_organizations": len(organizations),
                "active_campaigns": len(active_campaigns),
                "completed_campaigns": status_counts.get("completed", 0),
                "failed_campaigns": status_counts.get("failed", 0),
                "status_breakdown": status_counts,
                "total_responses_posted": total_responses_posted,
                "total_successful_posts": total_successful_posts,
                "success_rate": (total_successful_posts / total_responses_posted * 100) if total_responses_posted > 0 else 0,
                "average_campaigns_per_org": len(campaigns) / len(organizations) if organizations else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting global campaign stats: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # DOCUMENT ANALYTICS
    # ========================================
    
    def get_organization_document_stats(self, org_id: str) -> Dict[str, Any]:
        """Get document statistics for an organization."""
        try:
            org_data = self.document_manager.get_organization(org_id)
            if not org_data:
                return {"error": "Organization not found"}
            
            documents = self.document_manager.get_documents_by_organization(org_id)
            
            total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
            total_content_length = sum(doc.get("content_length", 0) for doc in documents)
            
            return {
                "organization_id": org_id,
                "organization_name": org_data.get("name", ""),
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "total_content_length": total_content_length,
                "average_chunks_per_document": total_chunks / len(documents) if documents else 0,
                "average_content_length": total_content_length / len(documents) if documents else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting organization document stats for {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_global_document_stats(self) -> Dict[str, Any]:
        """Get global document statistics."""
        try:
            organizations = self.document_manager.list_organizations()
            documents = self.document_manager.list_documents()
            
            total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
            total_content_length = sum(doc.get("content_length", 0) for doc in documents)
            
            return {
                "total_organizations": len(organizations),
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "total_content_length": total_content_length,
                "average_documents_per_org": len(documents) / len(organizations) if organizations else 0,
                "average_chunks_per_document": total_chunks / len(documents) if documents else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting global document stats: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # ENGAGEMENT ANALYTICS
    # ========================================
    
    def get_engagement_metrics(self, campaign_id: str = None, org_id: str = None) -> Dict[str, Any]:
        """Get engagement metrics for campaigns."""
        try:
            if campaign_id:
                campaigns = [self.campaign_manager.get_campaign(campaign_id)]
                campaigns = [c for c in campaigns if c is not None]
            elif org_id:
                campaigns = self.campaign_manager.list_campaigns_by_organization(org_id)
            else:
                campaigns = self.campaign_manager.list_campaigns()
            
            if not campaigns:
                return {
                    "total_posts_targeted": 0,
                    "total_responses_generated": 0,
                    "total_responses_posted": 0,
                    "engagement_rate": 0.0,
                    "success_rate": 0.0
                }
            
            total_posts_targeted = sum(len(c.target_posts) for c in campaigns)
            total_responses_generated = sum(len(c.planned_responses) for c in campaigns)
            total_responses_posted = sum(len(c.posted_responses) for c in campaigns)
            total_successful_posts = sum(
                len([r for r in c.posted_responses.values() if r.posting_successful])
                for c in campaigns
            )
            
            engagement_rate = (total_responses_generated / total_posts_targeted * 100) if total_posts_targeted > 0 else 0
            success_rate = (total_successful_posts / total_responses_posted * 100) if total_responses_posted > 0 else 0
            
            return {
                "total_posts_targeted": total_posts_targeted,
                "total_responses_generated": total_responses_generated,
                "total_responses_posted": total_responses_posted,
                "total_successful_posts": total_successful_posts,
                "engagement_rate": engagement_rate,
                "success_rate": success_rate,
                "campaigns_analyzed": len(campaigns)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting engagement metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_subreddit_performance(self, org_id: str = None) -> Dict[str, Any]:
        """Get performance metrics by subreddit."""
        try:
            if org_id:
                campaigns = self.campaign_manager.list_campaigns_by_organization(org_id)
            else:
                campaigns = self.campaign_manager.list_campaigns()
            
            subreddit_stats = {}
            
            for campaign in campaigns:
                for post in campaign.target_posts.values():
                    subreddit = post.subreddit
                    if subreddit not in subreddit_stats:
                        subreddit_stats[subreddit] = {
                            "posts_targeted": 0,
                            "responses_planned": 0,
                            "responses_posted": 0,
                            "successful_posts": 0
                        }
                    
                    subreddit_stats[subreddit]["posts_targeted"] += 1
                    
                    # Count planned responses for this post
                    planned_for_post = [r for r in campaign.planned_responses.values() if r.target_post_id == post.id]
                    subreddit_stats[subreddit]["responses_planned"] += len(planned_for_post)
                    
                    # Count posted responses for this post
                    posted_for_post = [r for r in campaign.posted_responses.values() if r.target_post_id == post.id]
                    subreddit_stats[subreddit]["responses_posted"] += len(posted_for_post)
                    
                    # Count successful posts
                    successful_for_post = [r for r in posted_for_post if r.posting_successful]
                    subreddit_stats[subreddit]["successful_posts"] += len(successful_for_post)
            
            # Calculate rates for each subreddit
            for subreddit, stats in subreddit_stats.items():
                stats["engagement_rate"] = (stats["responses_planned"] / stats["posts_targeted"] * 100) if stats["posts_targeted"] > 0 else 0
                stats["success_rate"] = (stats["successful_posts"] / stats["responses_posted"] * 100) if stats["responses_posted"] > 0 else 0
            
            return {
                "subreddit_performance": subreddit_stats,
                "total_subreddits": len(subreddit_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting subreddit performance: {str(e)}")
            return {"error": str(e)}
    
    # ========================================
    # COMPREHENSIVE REPORTS
    # ========================================
    
    def get_comprehensive_report(self, org_id: str) -> Dict[str, Any]:
        """Get a comprehensive analytics report for an organization."""
        try:
            return {
                "organization_id": org_id,
                "campaign_stats": self.get_organization_campaign_stats(org_id),
                "document_stats": self.get_organization_document_stats(org_id),
                "engagement_metrics": self.get_engagement_metrics(org_id=org_id),
                "subreddit_performance": self.get_subreddit_performance(org_id),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report for {org_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_platform_overview(self) -> Dict[str, Any]:
        """Get platform-wide analytics overview."""
        try:
            return {
                "campaign_stats": self.get_global_campaign_stats(),
                "document_stats": self.get_global_document_stats(),
                "engagement_metrics": self.get_engagement_metrics(),
                "subreddit_performance": self.get_subreddit_performance(),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating platform overview: {str(e)}")
            return {"error": str(e)}