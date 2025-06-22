"""
Example usage of the Reddit Marketing AI Agent without API layer.
This demonstrates how to use the services directly.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all necessary components
from app.services.campaign_service import CampaignService
from app.services.document_service import DocumentService
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService
from app.services.analytics_service import AnalyticsService
from app.managers.analytics_manager import AnalyticsManager
from app.managers.campaign_manager import CampaignManager
from app.managers.document_manager import DocumentManager
from app.managers.embeddings_manager import EmbeddingsManager
from app.storage.vector_storage import VectorStorage
from app.storage.json_storage import JsonStorage
from app.clients.llm_client import LLMClient
from app.clients.reddit_client import RedditClient
from app.clients.storage_client import VectorStorageClient
from app.services.scraper_service import WebScraperService

# Import models
from app.models.campaign import CampaignCreateRequest, ResponseTone, SubredditDiscoveryRequest
from app.models.document import DocumentQuery


def initialize_services():
    """Initialize all services without dependency injection."""
    
    # Storage layer
    json_storage = JsonStorage()
    vector_storage_client = VectorStorageClient()
    vector_storage = VectorStorage(vector_storage_client)
    
    # Managers
    document_manager = DocumentManager(json_storage)
    campaign_manager = CampaignManager(json_storage)
    embeddings_manager = EmbeddingsManager(vector_storage_client)
    analytics_manager = AnalyticsManager(campaign_manager, document_manager)
    
    # Clients
    llm_client = LLMClient()
    reddit_client = RedditClient(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD")
    )
    web_scraper_service = WebScraperService()
    
    # Services
    document_service = DocumentService(
        document_manager,
        vector_storage,
        web_scraper_service
    )
    reddit_service = RedditService(json_storage, reddit_client)
    llm_service = LLMService(llm_client)
    analytics_service = AnalyticsService(analytics_manager)
    campaign_service = CampaignService(
        campaign_manager,
        document_service,
        reddit_service,
        llm_service
    )
    
    return {
        'campaign_service': campaign_service,
        'document_service': document_service,
        'reddit_service': reddit_service,
        'llm_service': llm_service,
        'analytics_service': analytics_service
    }


async def main():
    """Main example workflow."""
    
    print("🚀 Reddit Marketing AI Agent - Example Usage")
    print("=" * 50)
    
    # Initialize services
    print("🔧 Initializing services...")
    services = initialize_services()
    
    campaign_service = services['campaign_service']
    document_service = services['document_service']
    reddit_service = services['reddit_service']
    llm_service = services['llm_service']
    analytics_service = services['analytics_service']
    
    # Configuration
    ORGANIZATION_ID = "demo-org-2024"
    ORGANIZATION_NAME = "Demo Organization"
    
    try:
        # Step 1: Create organization
        print(f"\n📋 Step 1: Creating organization...")
        organization = document_service.get_or_create_organization(ORGANIZATION_ID, ORGANIZATION_NAME)
        print(f"   ✅ Organization: {organization.name} ({organization.id})")
        
        # Step 2: Ingest documents
        print(f"\n📄 Step 2: Ingesting documents...")
        documents = [{
            "title": "Python Best Practices",
            "content": """
            Python Best Practices for Clean Code
            
            1. Follow PEP 8 Style Guide
            - Use 4 spaces for indentation
            - Keep lines under 79 characters
            - Use descriptive variable names
            
            2. Write Docstrings
            - Document all functions and classes
            - Use triple quotes for docstrings
            
            3. Use Type Hints
            - Add type hints to function parameters
            - Use typing module for complex types
            """,
            "metadata": {"category": "programming", "language": "python"}
        }]
        
        success, message, document_ids = document_service.ingest_documents(
            documents=documents,
            org_id=ORGANIZATION_ID
        )
        print(f"   ✅ Ingested: {len(document_ids) if document_ids else 0} documents")
        
        # Step 3: Ingest from URL
        print(f"\n🌐 Step 3: Ingesting from URL...")
        success, message, doc_id = await document_service.ingest_document_from_url(
            url="https://docs.python.org/3/tutorial/introduction.html",
            organization_id=ORGANIZATION_ID,
            title="Python Tutorial Introduction",
            scraping_method="auto"
        )
        if success:
            print(f"   ✅ URL ingestion successful: {doc_id}")
            document_ids.append(doc_id)
        else:
            print(f"   ⚠️ URL ingestion failed: {message}")
        
        # Step 4: Query documents
        print(f"\n🔍 Step 4: Querying documents...")
        query = DocumentQuery(
            query="python best practices",
            organization_id=ORGANIZATION_ID,
            method="semantic",
            top_k=3
        )
        response = document_service.query_documents(query)
        print(f"   ✅ Found {response.total_results} documents in {response.processing_time_ms:.2f}ms")
        
        # Step 5: Create campaign
        print(f"\n🎯 Step 5: Creating campaign...")
        request = CampaignCreateRequest(
            name="Python Community Outreach",
            description="Engage with Python learning communities",
            response_tone=ResponseTone.HELPFUL,
            max_responses_per_day=5
        )
        
        success, message, campaign = await campaign_service.create_campaign(
            organization_id=ORGANIZATION_ID,
            request=request
        )
        if success:
            print(f"   ✅ Campaign created: {campaign.name} ({campaign.id})")
        else:
            print(f"   ❌ Campaign creation failed: {message}")
            return
        
        # Step 6: Discover topics
        print(f"\n🔍 Step 6: Discovering topics...")
        topic_request = SubredditDiscoveryRequest(document_ids=document_ids)
        success, message, data = await campaign_service.discover_topics(
            campaign_id=campaign.id,
            request=topic_request
        )
        if success and data:
            topics = data.get("topics", [])
            print(f"   ✅ Discovered {len(topics)} topics")
            for i, topic in enumerate(topics[:5], 1):
                print(f"      {i}. {topic}")
        else:
            print(f"   ⚠️ Topic discovery failed: {message}")
        
        # Step 7: Generate LLM response
        print(f"\n🤖 Step 7: Testing LLM response generation...")
        response = await llm_service.generate_completion(
            prompt="Explain the benefits of using Python for web development",
            response_format="text",
            temperature=0.7
        )
        print(f"   ✅ LLM response generated ({len(str(response))} characters)")
        print(f"   Preview: {str(response)[:100]}...")
        
        # Step 8: Search subreddits
        print(f"\n🎯 Step 8: Searching subreddits...")
        success, message, results = await reddit_service.search_subreddits("python programming", limit=3)
        if success:
            print(f"   ✅ Found {len(results)} subreddits")
            for result in results:
                print(f"      - r/{result['name']} ({result['subscribers']:,} subscribers)")
        else:
            print(f"   ⚠️ Subreddit search failed: {message}")
        
        # Step 9: Get analytics
        print(f"\n📊 Step 9: Getting analytics...")
        quick_stats = analytics_service.get_quick_stats(ORGANIZATION_ID)
        if "error" not in quick_stats:
            print(f"   ✅ Analytics retrieved")
            print(f"      - Total Campaigns: {quick_stats.get('total_campaigns', 0)}")
            print(f"      - Total Documents: {quick_stats.get('total_documents', 0)}")
            print(f"      - Success Rate: {quick_stats.get('success_rate', 0):.1f}%")
        else:
            print(f"   ⚠️ Analytics failed: {quick_stats.get('error')}")
        
        print(f"\n✅ Example workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in workflow: {str(e)}")
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        await campaign_service.cleanup()
        await reddit_service.cleanup()
        print("   ✅ Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())