"""
Campaign storage manager.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.repositories.json_repository import JsonRepository
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)


class CampaignManager:
    """
    Manager for campaign storage and retrieval.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize campaign manager."""
        self.data_dir = data_dir
        self.json_repository = JsonRepository(data_dir)
        self.logger = logger
        
        # Initialize JSON files
        self.json_repository.init_file("campaigns.json", [])
    
    # ========================================
    # CAMPAIGN OPERATIONS
    # ========================================
    
    def save_campaign(self, campaign: Campaign) -> bool:
        """Save campaign data."""
        try:
            # Update timestamp
            campaign.updated_at = datetime.now(timezone.utc)
            
            # Convert to dict for storage
            campaign_data = campaign.model_dump()
            
            return self.json_repository.update_item("campaigns.json", campaign_data)
        except Exception as e:
            self.logger.error(f"Error saving campaign: {str(e)}")
            return False
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        try:
            campaign_data = self.json_repository.find_item("campaigns.json", campaign_id)
            if campaign_data:
                return Campaign(**campaign_data)
            return None
        except Exception as e:
            self.logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
            return None
    
    def list_campaigns(self) -> List[Campaign]:
        """List all campaigns."""
        try:
            campaigns_data = self.json_repository.load_data("campaigns.json")
            return [Campaign(**data) for data in campaigns_data]
        except Exception as e:
            self.logger.error(f"Error listing campaigns: {str(e)}")
            return []
    
    def list_campaigns_by_organization(self, org_id: str) -> List[Campaign]:
        """List campaigns for a specific organization."""
        try:
            campaigns_data = self.json_repository.filter_items(
                "campaigns.json", 
                {"organization_id": org_id}
            )
            return [Campaign(**data) for data in campaigns_data]
        except Exception as e:
            self.logger.error(f"Error listing campaigns for org {org_id}: {str(e)}")
            return []
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete campaign."""
        try:
            return self.json_repository.delete_item("campaigns.json", campaign_id)
        except Exception as e:
            self.logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
            return False
    
    # ========================================
    # SEARCH AND FILTERING
    # ========================================
    
    def search_campaigns(
        self, 
        query: str, 
        org_id: str = None,
        status: str = None,
        limit: int = 50
    ) -> List[Campaign]:
        """Search campaigns by name or description."""
        try:
            # Get campaigns for organization if specified
            if org_id:
                campaigns_data = self.json_repository.filter_items(
                    "campaigns.json", 
                    {"organization_id": org_id}
                )
            else:
                campaigns_data = self.json_repository.load_data("campaigns.json")
            
            # Filter by status if specified
            if status:
                campaigns_data = [
                    camp for camp in campaigns_data 
                    if camp.get("status") == status
                ]
            
            # Simple text search in name and description
            query_lower = query.lower()
            matching_campaigns = []
            
            for camp_data in campaigns_data:
                # Search in name
                if query_lower in camp_data.get("name", "").lower():
                    matching_campaigns.append(Campaign(**camp_data))
                    continue
                
                # Search in description
                description = camp_data.get("description", "")
                if description and query_lower in description.lower():
                    matching_campaigns.append(Campaign(**camp_data))
                    continue
            
            return matching_campaigns[:limit]
            
        except Exception as e:
            self.logger.error(f"Error searching campaigns: {str(e)}")
            return []
    
    def get_campaigns_by_status(
        self, 
        status: str, 
        org_id: str = None
    ) -> List[Campaign]:
        """Get campaigns by status."""
        try:
            filters = {"status": status}
            if org_id:
                filters["organization_id"] = org_id
            
            campaigns_data = self.json_repository.filter_items("campaigns.json", filters)
            return [Campaign(**data) for data in campaigns_data]
        except Exception as e:
            self.logger.error(f"Error getting campaigns by status '{status}': {str(e)}")
            return []
    
    def get_active_campaigns(self, org_id: str = None) -> List[Campaign]:
        """Get active campaigns (not completed or failed)."""
        try:
            all_campaigns = self.list_campaigns_by_organization(org_id) if org_id else self.list_campaigns()
            
            active_statuses = [
                "created", "documents_uploaded", "subreddits_discovered", 
                "posts_found", "responses_planned", "responses_posted"
            ]
            
            return [
                campaign for campaign in all_campaigns 
                if campaign.status in active_statuses
            ]
        except Exception as e:
            self.logger.error(f"Error getting active campaigns: {str(e)}")
            return []
    
    # ========================================
    # STATISTICS
    # ========================================
    
    def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get statistics for a specific campaign."""
        try:
            campaign = self.get_campaign(campaign_id)
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
                "successful_posts": len([r for r in campaign.posted_responses if r.posting_successful]),
                "failed_posts": len([r for r in campaign.posted_responses if not r.posting_successful]),
                "created_at": campaign.created_at,
                "updated_at": campaign.updated_at
            }
            
        except Exception as e:
            self.logger.error(f"Error getting campaign stats for {campaign_id}: {str(e)}")
            return {"error": str(e)}
    
    def get_organization_campaign_stats(self, org_id: str) -> Dict[str, Any]:
        """Get campaign statistics for an organization."""
        try:
            campaigns = self.list_campaigns_by_organization(org_id)
            
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
                len([r for r in campaign.posted_responses if r.posting_successful])
                for campaign in campaigns
            )
            
            return {
                "organization_id": org_id,
                "total_campaigns": len(campaigns),
                "active_campaigns": len(self.get_active_campaigns(org_id)),
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
            campaigns = self.list_campaigns()
            
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
                len([r for r in campaign.posted_responses if r.posting_successful])
                for campaign in campaigns
            )
            
            return {
                "total_campaigns": len(campaigns),
                "total_organizations": len(organizations),
                "active_campaigns": len(self.get_active_campaigns()),
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