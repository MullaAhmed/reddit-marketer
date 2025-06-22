"""
Example usage of the Reddit Marketing AI Agent.
"""

import asyncio
import logging
from src.config.settings import settings
from src.clients.reddit_client import RedditClient
from src.clients.llm_client import LLMClient
from src.clients.embedding_client import EmbeddingClient
from src.storage.json_storage import JsonStorage
from src.storage.vector_storage import VectorStorage
from src.services.ingestion_service import IngestionService
from src.services.subreddit_service import SubredditService
from src.services.posting_service import PostingService
from src.services.analytics_service import AnalyticsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example workflow demonstrating the Reddit Marketing AI Agent."""
    
    # Configuration
    ORGANIZATION_ID = "demo-org-2024"
    
    # Initialize clients
    reddit_client = RedditClient(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        username=settings.REDDIT_USERNAME,
        password=settings.REDDIT_PASSWORD
    )
    
    llm_client = LLMClient()
    embedding_client = EmbeddingClient()
    
    # Initialize storage
    json_storage = JsonStorage()
    vector_storage = VectorStorage()
    
    # Initialize services
    ingestion_service = IngestionService(json_storage, vector_storage, embedding_client)
    subreddit_service = SubredditService(reddit_client, llm_client)
    posting_service = PostingService(reddit_client, llm_client, vector_storage, json_storage)
    analytics_service = AnalyticsService(json_storage, reddit_client)
    
    try:
        # Step 1: Ingest a document
        logger.info("Step 1: Ingesting document...")
        content = """
        Python is a versatile programming language that's great for web development,
        data science, machine learning, and automation. It has frameworks like Django
        and Flask for web development, pandas and numpy for data analysis, and
        scikit-learn for machine learning.
        """
        
        success, message, doc_id = await ingestion_service.ingest_document(
            content=content,
            title="Python Programming Guide",
            organization_id=ORGANIZATION_ID
        )
        
        if success:
            logger.info(f"✅ Document ingested: {message}")
        else:
            logger.error(f"❌ Document ingestion failed: {message}")
            return
        
        # Step 2: Discover subreddits
        logger.info("Step 2: Discovering subreddits...")
        topics = ["python", "programming", "web development"]
        
        success, message, subreddits = await subreddit_service.discover_and_rank_subreddits(
            topics=topics,
            organization_id=ORGANIZATION_ID,
            context_content=content
        )
        
        if success:
            logger.info(f"✅ Found subreddits: {subreddits}")
        else:
            logger.error(f"❌ Subreddit discovery failed: {message}")
            return
        
        # Step 3: Search for posts in a subreddit
        logger.info("Step 3: Searching for posts...")
        if subreddits:
            target_subreddit = subreddits[0]  # Use first subreddit
            
            async with reddit_client:
                posts = await reddit_client.search_subreddit_posts(
                    subreddit=target_subreddit,
                    query="python help",
                    limit=5
                )
            
            if posts:
                logger.info(f"✅ Found {len(posts)} posts in r/{target_subreddit}")
                
                # Step 4: Analyze a post and generate response
                logger.info("Step 4: Analyzing post and generating response...")
                target_post = posts[0]
                
                success, message, response_data = await posting_service.analyze_and_generate_response(
                    post_id=target_post["id"],
                    organization_id=ORGANIZATION_ID,
                    tone="helpful"
                )
                
                if success:
                    logger.info(f"✅ Generated response: {message}")
                    logger.info(f"Response preview: {response_data['response']['content'][:100]}...")
                    
                    # Note: In a real scenario, you would review and approve the response
                    # before posting. For this example, we'll skip the actual posting.
                    logger.info("ℹ️  Response generated but not posted (manual approval required)")
                    
                else:
                    logger.error(f"❌ Response generation failed: {message}")
            else:
                logger.warning("No posts found in target subreddit")
        
        # Step 5: Get analytics report
        logger.info("Step 5: Getting analytics report...")
        report = await analytics_service.get_engagement_report(ORGANIZATION_ID)
        logger.info(f"✅ Analytics report: {report}")
        
        # Step 6: Get posting history
        logger.info("Step 6: Getting posting history...")
        history = analytics_service.get_posting_history(ORGANIZATION_ID)
        logger.info(f"✅ Posting history: {history}")
        
    except Exception as e:
        logger.error(f"❌ Error in workflow: {str(e)}")
    
    finally:
        # Cleanup
        await reddit_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())