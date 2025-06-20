"""
Campaign storage manager.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.storage.json_storage import JsonStorage
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)


class CampaignManager:
    """
    Manager for campaign storage and retrieval.
    """
    
    def __init__(self, json_storage: JsonStorage):
        """Initialize campaign manager."""
        self.json_storage = json_storage
        self.logger = logger
        
        # Initialize JSON files
        self.json_storage.init_file("campaigns.json", [])
    
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
            
            return self.json_storage.update_item("campaigns.json", campaign_data)
        except Exception as e:
            self.logger.error(f"Error saving campaign: {str(e)}")
            return False
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        try:
            campaign_data = self.json_storage.find_item("campaigns.json", campaign_id)
            if campaign_data:
                return Campaign(**campaign_data)
            return None
        except Exception as e:
            self.logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
            return None
    
    def list_campaigns(self) -> List[Campaign]:
        """List all campaigns."""
        try:
            campaigns_data = self.json_storage.load_data("campaigns.json")
            return [Campaign(**data) for data in campaigns_data]
        except Exception as e:
            self.logger.error(f"Error listing campaigns: {str(e)}")
            return []
    
    def list_campaigns_by_organization(self, org_id: str) -> List[Campaign]:
        """List campaigns for a specific organization."""
        try:
            campaigns_data = self.json_storage.filter_items(
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
            return self.json_storage.delete_item("campaigns.json", campaign_id)
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
                campaigns_data = self.json_storage.filter_items(
                    "campaigns.json", 
                    {"organization_id": org_id}
                )
            else:
                campaigns_data = self.json_storage.load_data("campaigns.json")
            
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
            
            return matching_campaigns
            
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
            
            campaigns_data = self.json_storage.filter_items("campaigns.json", filters)
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