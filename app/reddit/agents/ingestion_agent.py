"""
Refactored ingestion agent using the new unified services.
"""

from typing import Dict, Any

from shared.base.service_base import AsyncBaseService
from reddit.services.reddit_service import RedditService


class IngestionAgent(AsyncBaseService):
    """
    Refactored ingestion agent using unified Reddit service.
    """
    
    def __init__(self, min_subscribers: int = 10000, data_dir: str = "data"):
        """Initialize the ingestion agent."""
        super().__init__("IngestionAgent", data_dir)
        
        self.min_subscribers = min_subscribers
        
        # Initialize Reddit service
        self.reddit_service = RedditService(data_dir)
    
    async def cleanup(self):
        """Clean up resources."""
        await self.reddit_service.cleanup()
    
    async def process_content(self, content: str, organization_id: str) -> Dict[str, Any]:
        """
        Process user content to extract topics and find relevant subreddits.
        
        Args:
            content: The user's content to analyze
            organization_id: Organization ID for tracking
            
        Returns:
            dict: Processing results with topics and subreddits
        """
        self.log_operation("CONTENT_PROCESSING", True, "Starting content processing", org_id=organization_id)
        
        try:
            # Use Reddit service to discover subreddits
            success, message, results = await self.reddit_service.discover_subreddits(
                content, organization_id, self.min_subscribers
            )
            
            if not success:
                self.log_operation("CONTENT_PROCESSING", False, message, org_id=organization_id)
                raise Exception(message)
            
            # Extract data from results
            topics = results.get("topics", [])
            relevant_subreddits = results.get("relevant_subreddits", {})
            all_subreddits = results.get("all_subreddits", {})
            
            # Return summary
            processing_summary = {
                "success": True,
                "topics_found": len(topics),
                "relevant_subreddits_found": len(relevant_subreddits),
                "total_subreddits_analyzed": len(all_subreddits),
                "topics": topics,
                "top_subreddits": list(relevant_subreddits.keys())[:10]
            }
            
            self.log_operation(
                "CONTENT_PROCESSING", 
                True, 
                "Content processing completed successfully",
                org_id=organization_id,
                topics_found=len(topics),
                subreddits_found=len(relevant_subreddits)
            )
            
            return processing_summary
            
        except Exception as e:
            self.log_operation("CONTENT_PROCESSING", False, str(e), org_id=organization_id)
            raise
    
    async def run_ingestion(self, content: str, organization_id: str):
        """
        Main method to run the ingestion process.
        
        Args:
            content: User content to analyze
            organization_id: Organization ID
        """
        self.logger.info("=== Starting Ingestion Agent ===")
        
        try:
            results = await self.process_content(content, organization_id)
            
            # Log results
            self.logger.info("=== Ingestion Results ===")
            self.logger.info(f"Topics extracted: {results['topics_found']}")
            self.logger.info(f"Relevant subreddits found: {results['relevant_subreddits_found']}")
            self.logger.info(f"Top topics: {', '.join(results['topics'][:5])}")
            self.logger.info(f"Top subreddits: {', '.join(results['top_subreddits'][:5])}")
            
            self.logger.info("=== Files Created ===")
            self.logger.info("- data/json/topics.json")
            self.logger.info("- data/json/subreddits.json")
            
            self.logger.info("=== Ingestion Phase Complete ===")
            
        except Exception as e:
            self.logger.error(f"Ingestion failed: {str(e)}")
            raise