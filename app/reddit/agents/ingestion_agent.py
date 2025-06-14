"""
IngestionAgent - Phase 1: Subreddit Discovery and Topic Extraction
Takes user input text and finds relevant subreddits, saves configuration data.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from reddit.core.subreddit_finder import SubredditFinder


class IngestionAgent:
    """
    Handles the ingestion phase of the Reddit marketing pipeline.
    Extracts topics from user content and finds relevant subreddits.
    """
    
    def __init__(self, min_subscribers: int = 10000):
        """
        Initialize the IngestionAgent.
        
        Args:
            min_subscribers: Minimum subscriber count for subreddit filtering
        """
        self.min_subscribers = min_subscribers
        
        # Set up logging
        self.logger = logging.getLogger("IngestionAgent")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Initialize SubredditFinder
        self.subreddit_finder = SubredditFinder(min_subscribers=min_subscribers)
        
        # Create data directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path("data/json").mkdir(parents=True, exist_ok=True)
        Path("data/daily").mkdir(parents=True, exist_ok=True)
    
    def _save_json(self, data: Any, file_path: str):
        """Save data to JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved data to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {str(e)}")
            raise
    
    async def process_content(self, content: str, organization_id:str) -> Dict[str, Any]:
        """
        Process user content to extract topics and find relevant subreddits.
        
        Args:
            content: The user's content to analyze
            
        Returns:
            dict: Processing results with topics and subreddits
        """
        self.logger.info("Starting content processing...")
        
        try:
            # Find relevant subreddits (this also extracts topics)
            self.logger.info("Analyzing content and finding relevant subreddits...")
            results = await self.subreddit_finder.find_relevant_subreddits(content)
            # Extract data from results
            topics = results.get("topics", [])
            relevant_subreddits = results.get("relevant_subreddits", {})
            all_subreddits = results.get("all_subreddits", {})
            
            self.logger.info(f"Found {len(topics)} topics and {len(relevant_subreddits)} relevant subreddits")
            
            # Save topics to topics.json
            topics_data = {
                "extracted_topics": topics,
                "content_analyzed": content[:200] + "..." if len(content) > 200 else content,
                "total_topics": len(topics),
                "organization_id":organization_id
            }
            self._save_json(topics_data, "data/json/topics.json")
            
            # Save subreddits to subreddits.json
            subreddits_data = {
                "relevant_subreddits": relevant_subreddits,
                "all_filtered_subreddits": all_subreddits,
                "total_relevant": len(relevant_subreddits),
                "total_filtered": len(all_subreddits),
                "min_subscribers": self.min_subscribers,
                "organization_id": organization_id
            }
            self._save_json(subreddits_data, "data/json/subreddits.json")
            
            # Return summary
            processing_summary = {
                "success": True,
                "topics_found": len(topics),
                "relevant_subreddits_found": len(relevant_subreddits),
                "total_subreddits_analyzed": len(all_subreddits),
                "topics": topics,
                "top_subreddits": list(relevant_subreddits.keys())[:10]
            }
            
            self.logger.info("Content processing completed successfully")
            return processing_summary
            
        except Exception as e:
            self.logger.error(f"Error processing content: {str(e)}")
            raise
    
    async def run_ingestion(self, content: str, organization_id:str):
        """
        Main method to run the ingestion process.
        
        Args:
            content: User content to analyze
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


if __name__ == "__main__":
    # Hard-coded configuration
    SAMPLE_CONTENT = """
    I've been learning Python for the past 6 months and have built several small
    projects including a web scraper, a data visualization dashboard, and a simple
    machine learning model for text classification. I'm particularly interested in
    AI and natural language processing. I'm looking for communities where I can share
    my projects, get feedback from experienced developers, and continue learning about
    best practices in software development. I also enjoy gaming in my free time,
    particularly RPGs and strategy games.
    """
    
    MIN_SUBSCRIBERS = 10000
    ORGANIZATION_ID = "test-1"
    async def main():
        """Run the ingestion agent with sample content."""
        # Initialize the agent
        agent = IngestionAgent(min_subscribers=MIN_SUBSCRIBERS)
        
        # Run ingestion
        await agent.run_ingestion(SAMPLE_CONTENT,ORGANIZATION_ID)
    
    # Run the async main function
    asyncio.run(main())