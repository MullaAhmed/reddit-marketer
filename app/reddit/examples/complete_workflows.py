"""
Complete workflow examples showing end-to-end Reddit marketing campaigns.
Includes both programmatic and API-based approaches.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional

# Service imports
from reddit.services.campaign_service import CampaignService
from reddit.models import (
    CampaignCreateRequest, SubredditDiscoveryRequest, PostDiscoveryRequest,
    ResponseGenerationRequest, ResponseExecutionRequest, ResponseTone
)

# Individual component imports
from rag.ingestion import DocumentIngestion
from rag.retrieval import DocumentRetrieval
from reddit.agents.ingestion_agent import IngestionAgent
from reddit.core.reddit_post_finder import RedditPostFinder
from reddit.core.reddit_interactor import RedditInteractor


# ========================================
# COMPLETE WORKFLOW - PROGRAMMATIC
# ========================================

async def complete_workflow_programmatic():
    """
    Complete end-to-end workflow using direct service calls.
    This approach gives you full control over each step.
    """
    print("🚀 Complete Programmatic Workflow")
    print("=" * 50)
    
    # Configuration
    organization_id = "workflow-org-1"
    organization_name = "Tech Consulting Company"
    
    reddit_credentials = {
        "client_id": "YOUR_REDDIT_CLIENT_ID",
        "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
        "username": "YOUR_REDDIT_USERNAME",
        "password": "YOUR_REDDIT_PASSWORD"
    }
    
    try:
        # ========================================
        # PHASE 1: DOCUMENT PREPARATION
        # ========================================
        
        print("\n📚 Phase 1: Document Preparation")
        print("-" * 30)
        
        # Sample company documents
        company_documents = [
            {
                "title": "Python Development Services",
                "content": """
                Our company specializes in Python web development using Django and Flask.
                We have 8+ years of experience building scalable web applications,
                REST APIs, and microservices. Our expertise includes:
                
                - Full-stack web development with Python/Django/React
                - Database design and optimization (PostgreSQL, MongoDB)
                - Cloud deployment on AWS and Google Cloud
                - DevOps and CI/CD pipeline setup
                - Performance optimization and scaling
                
                We've helped over 50 startups and enterprises build robust
                web applications that handle millions of users.
                """,
                "metadata": {
                    "category": "services",
                    "technology": "python",
                    "experience_years": 8
                }
            },
            {
                "title": "Machine Learning Consulting",
                "content": """
                We provide end-to-end machine learning consulting services:
                
                - Data analysis and preprocessing
                - Model development and training
                - MLOps and model deployment
                - Computer vision and NLP solutions
                - Recommendation systems
                - Predictive analytics
                
                Our team has PhD-level expertise in machine learning and has
                delivered ML solutions for healthcare, finance, and e-commerce
                industries. We work with TensorFlow, PyTorch, and scikit-learn.
                """,
                "metadata": {
                    "category": "consulting",
                    "technology": "machine-learning",
                    "industries": ["healthcare", "finance", "ecommerce"]
                }
            },
            {
                "title": "Open Source Contributions",
                "content": """
                We actively contribute to the Python open source community:
                
                - Maintainers of 3 popular Python packages on PyPI
                - Regular contributors to Django, Flask, and pandas
                - Authors of technical blog posts and tutorials
                - Speakers at PyCon and local Python meetups
                - Mentors for Google Summer of Code
                
                We believe in giving back to the community that has helped
                us grow as developers. Our open source work has been used
                by thousands of developers worldwide.
                """,
                "metadata": {
                    "category": "community",
                    "activity": "open-source"
                }
            }
        ]
        
        # Ingest documents
        print("📄 Ingesting company documents...")
        ingestion_service = DocumentIngestion(data_dir="data")
        
        success, message, doc_ids = ingestion_service.ingest_documents(
            company_documents, organization_id, organization_name
        )
        
        if not success:
            print(f"❌ Document ingestion failed: {message}")
            return
        
        print(f"✅ Ingested {len(doc_ids)} documents")
        
        # ========================================
        # PHASE 2: CAMPAIGN SETUP
        # ========================================
        
        print("\n🎯 Phase 2: Campaign Setup")
        print("-" * 30)
        
        # Initialize campaign service
        campaign_service = CampaignService(data_dir="data")
        
        # Create campaign
        create_request = CampaignCreateRequest(
            name="Python & ML Community Engagement",
            description="Engage with Python and ML communities to share expertise and build relationships",
            response_tone=ResponseTone.HELPFUL,
            max_responses_per_day=8
        )
        
        success, message, campaign = await campaign_service.create_campaign(
            organization_id, create_request
        )
        
        if not success:
            print(f"❌ Campaign creation failed: {message}")
            return
        
        print(f"✅ Created campaign: {campaign.name}")
        print(f"   Campaign ID: {campaign.id}")
        
        # ========================================
        # PHASE 3: SUBREDDIT DISCOVERY
        # ========================================
        
        print("\n🔍 Phase 3: Subreddit Discovery")
        print("-" * 30)
        
        # Select documents for subreddit discovery
        selected_docs = doc_ids[:2]  # Use first 2 documents
        
        subreddit_request = SubredditDiscoveryRequest(
            document_ids=selected_docs
        )
        
        success, message, subreddit_data = await campaign_service.discover_subreddits(
            campaign.id, subreddit_request
        )
        
        if not success:
            print(f"❌ Subreddit discovery failed: {message}")
            return
        
        discovered_subreddits = subreddit_data["subreddits"]
        print(f"✅ Discovered {len(discovered_subreddits)} relevant subreddits:")
        
        for i, subreddit in enumerate(discovered_subreddits[:5], 1):
            print(f"   {i}. r/{subreddit}")
        
        # ========================================
        # PHASE 4: POST DISCOVERY
        # ========================================
        
        print("\n📋 Phase 4: Post Discovery")
        print("-" * 30)
        
        # Discover posts in target subreddits
        post_request = PostDiscoveryRequest(
            subreddits=discovered_subreddits[:4],  # Use top 4 subreddits
            max_posts_per_subreddit=15,
            time_filter="day"
        )
        
        success, message, post_data = await campaign_service.discover_posts(
            campaign.id, post_request, reddit_credentials
        )
        
        if not success:
            print(f"❌ Post discovery failed: {message}")
            return
        
        posts_found = post_data["posts_found"]
        print(f"✅ Found {posts_found} relevant posts across {len(post_request.subreddits)} subreddits")
        
        # ========================================
        # PHASE 5: RESPONSE GENERATION
        # ========================================
        
        print("\n💬 Phase 5: Response Generation")
        print("-" * 30)
        
        # Get updated campaign to access target posts
        success, message, updated_campaign = await campaign_service.get_campaign(campaign.id)
        
        if not success or not updated_campaign.target_posts:
            print("❌ No target posts available for response generation")
            return
        
        # Select high-relevance posts for response generation
        high_relevance_posts = [
            post for post in updated_campaign.target_posts 
            if post.relevance_score > 0.5
        ]
        
        if not high_relevance_posts:
            high_relevance_posts = updated_campaign.target_posts[:5]  # Fallback to top 5
        
        target_post_ids = [post.id for post in high_relevance_posts[:6]]
        
        response_request = ResponseGenerationRequest(
            target_post_ids=target_post_ids,
            tone=ResponseTone.HELPFUL
        )
        
        success, message, response_data = await campaign_service.generate_responses(
            campaign.id, response_request
        )
        
        if not success:
            print(f"❌ Response generation failed: {message}")
            return
        
        responses_generated = response_data["responses_generated"]
        print(f"✅ Generated {responses_generated} responses")
        
        # Display sample responses
        print("\n📝 Sample Generated Responses:")
        for i, response in enumerate(response_data["responses"][:2], 1):
            print(f"\nResponse {i} (Confidence: {response['confidence_score']:.2f}):")
            print(f"Content: {response['response_content'][:120]}...")
        
        # ========================================
        # PHASE 6: RESPONSE REVIEW & EXECUTION
        # ========================================
        
        print("\n🚀 Phase 6: Response Execution")
        print("-" * 30)
        
        print("⚠️  Response execution is disabled for safety in this example.")
        print("   To enable actual posting, uncomment the execution code below.")
        
        # Filter high-confidence responses
        high_confidence_responses = [
            resp for resp in response_data["responses"]
            if resp["confidence_score"] > 0.7
        ]
        
        print(f"📊 High-confidence responses: {len(high_confidence_responses)}")
        
        """
        # UNCOMMENT TO ACTUALLY POST TO REDDIT
        if high_confidence_responses:
            execution_request = ResponseExecutionRequest(
                planned_response_ids=[resp["id"] for resp in high_confidence_responses],
                reddit_credentials=reddit_credentials
            )
            
            success, message, execution_data = await campaign_service.execute_responses(
                campaign.id, execution_request
            )
            
            if success:
                posted = execution_data["responses_posted"]
                failed = execution_data["responses_failed"]
                print(f"✅ Posted {posted} responses successfully")
                if failed > 0:
                    print(f"⚠️  {failed} responses failed to post")
            else:
                print(f"❌ Response execution failed: {message}")
        """
        
        # ========================================
        # PHASE 7: CAMPAIGN SUMMARY
        # ========================================
        
        print("\n📊 Phase 7: Campaign Summary")
        print("-" * 30)
        
        # Get final campaign status
        success, message, final_campaign = await campaign_service.get_campaign(campaign.id)
        
        if success:
            print(f"Campaign: {final_campaign.name}")
            print(f"Status: {final_campaign.status}")
            print(f"Documents Used: {len(final_campaign.selected_document_ids)}")
            print(f"Subreddits Discovered: {len(final_campaign.target_subreddits)}")
            print(f"Posts Analyzed: {len(final_campaign.target_posts)}")
            print(f"Responses Generated: {len(final_campaign.planned_responses)}")
            print(f"Responses Posted: {len(final_campaign.posted_responses)}")
            
            # Calculate success metrics
            if final_campaign.target_posts:
                relevance_scores = [post.relevance_score for post in final_campaign.target_posts]
                avg_relevance = sum(relevance_scores) / len(relevance_scores)
                print(f"Average Post Relevance: {avg_relevance:.2f}")
            
            if final_campaign.planned_responses:
                confidence_scores = [resp.confidence_score for resp in final_campaign.planned_responses]
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                print(f"Average Response Confidence: {avg_confidence:.2f}")
        
        print("\n🎉 Programmatic workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Workflow error: {str(e)}")
        import traceback
        traceback.print_exc()


# ========================================
# COMPLETE WORKFLOW - API BASED
# ========================================

import requests

class WorkflowAPIClient:
    """API client for workflow operations."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API Error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail.get('detail', '')}"
                except:
                    error_msg += f" - {e.response.text}"
            return False, {"error": error_msg}


async def complete_workflow_api_based():
    """
    Complete end-to-end workflow using API endpoints.
    This approach simulates how a frontend application would interact with the system.
    """
    print("🌐 Complete API-Based Workflow")
    print("=" * 50)
    
    # Configuration
    organization_id = "api-workflow-org-1"
    reddit_credentials = {
        "client_id": "YOUR_REDDIT_CLIENT_ID",
        "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
        "username": "YOUR_REDDIT_USERNAME",
        "password": "YOUR_REDDIT_PASSWORD"
    }
    
    # Initialize API client
    api_client = WorkflowAPIClient()
    
    try:
        # ========================================
        # STEP 1: PREPARE DOCUMENTS (Outside API)
        # ========================================
        
        print("\n📚 Step 1: Document Preparation")
        print("-" * 30)
        
        # Note: Document ingestion is typically done separately
        # Here we simulate having documents already in the system
        document_ids = ["api-doc-1", "api-doc-2", "api-doc-3"]
        print(f"✅ Using existing documents: {document_ids}")
        
        # ========================================
        # STEP 2: CREATE CAMPAIGN
        # ========================================
        
        print("\n🎯 Step 2: Create Campaign via API")
        print("-" * 30)
        
        campaign_data = {
            "name": "API-Driven Marketing Campaign",
            "description": "End-to-end campaign managed via API calls",
            "response_tone": "professional",
            "max_responses_per_day": 6
        }
        
        success, result = api_client.make_request(
            "POST",
            f"/api/v1/reddit/campaigns/?organization_id={organization_id}",
            json=campaign_data
        )
        
        if not success:
            print(f"❌ Campaign creation failed: {result['error']}")
            return
        
        campaign_id = result["campaign"]["id"]
        print(f"✅ Campaign created via API: {campaign_id}")
        
        # ========================================
        # STEP 3: DISCOVER SUBREDDITS
        # ========================================
        
        print("\n🔍 Step 3: Discover Subreddits via API")
        print("-" * 30)
        
        subreddit_data = {
            "document_ids": document_ids[:2]  # Use first 2 documents
        }
        
        success, result = api_client.make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/discover-subreddits",
            json=subreddit_data
        )
        
        if not success:
            print(f"❌ Subreddit discovery failed: {result['error']}")
            return
        
        subreddits = result["data"]["subreddits"]
        print(f"✅ Discovered {len(subreddits)} subreddits via API")
        
        for i, subreddit in enumerate(subreddits[:3], 1):
            print(f"   {i}. r/{subreddit}")
        
        # ========================================
        # STEP 4: DISCOVER POSTS
        # ========================================
        
        print("\n📋 Step 4: Discover Posts via API")
        print("-" * 30)
        
        post_data = {
            "subreddits": subreddits[:3],
            "max_posts_per_subreddit": 12,
            "time_filter": "day"
        }
        
        success, result = api_client.make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/discover-posts",
            json=post_data,
            params={"reddit_credentials": json.dumps(reddit_credentials)}
        )
        
        if not success:
            print(f"❌ Post discovery failed: {result['error']}")
            return
        
        posts_found = result["data"]["posts_found"]
        print(f"✅ Found {posts_found} posts via API")
        
        # ========================================
        # STEP 5: GENERATE RESPONSES
        # ========================================
        
        print("\n💬 Step 5: Generate Responses via API")
        print("-" * 30)
        
        # Get campaign to access target posts
        success, campaign_result = api_client.make_request(
            "GET",
            f"/api/v1/reddit/campaigns/{campaign_id}"
        )
        
        if not success:
            print(f"❌ Failed to get campaign: {campaign_result['error']}")
            return
        
        target_posts = campaign_result["campaign"]["target_posts"]
        
        if not target_posts:
            print("⚠️  No target posts available")
            return
        
        # Select posts for response generation
        target_post_ids = [post["id"] for post in target_posts[:4]]
        
        response_data = {
            "target_post_ids": target_post_ids,
            "tone": "helpful"
        }
        
        success, result = api_client.make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/generate-responses",
            json=response_data
        )
        
        if not success:
            print(f"❌ Response generation failed: {result['error']}")
            return
        
        responses_generated = result["data"]["responses_generated"]
        print(f"✅ Generated {responses_generated} responses via API")
        
        # ========================================
        # STEP 6: CHECK CAMPAIGN STATUS
        # ========================================
        
        print("\n📊 Step 6: Check Campaign Status via API")
        print("-" * 30)
        
        success, status_result = api_client.make_request(
            "GET",
            f"/api/v1/reddit/campaigns/{campaign_id}/status"
        )
        
        if success:
            progress = status_result["data"]
            print(f"✅ Campaign Status: {progress['status']}")
            print(f"   Documents: {progress['documents_selected']}")
            print(f"   Subreddits: {progress['subreddits_found']}")
            print(f"   Posts: {progress['posts_found']}")
            print(f"   Responses Planned: {progress['responses_planned']}")
            print(f"   Responses Posted: {progress['responses_posted']}")
        
        # ========================================
        # STEP 7: EXECUTE RESPONSES (Optional)
        # ========================================
        
        print("\n🚀 Step 7: Execute Responses via API")
        print("-" * 30)
        
        print("⚠️  Response execution is disabled for safety.")
        print("   To enable, uncomment the execution code below.")
        
        """
        # UNCOMMENT TO ACTUALLY POST TO REDDIT
        planned_responses = result["data"]["responses"]
        high_confidence = [
            resp for resp in planned_responses 
            if resp["confidence_score"] > 0.6
        ]
        
        if high_confidence:
            execution_data = {
                "planned_response_ids": [resp["id"] for resp in high_confidence],
                "reddit_credentials": reddit_credentials
            }
            
            success, exec_result = api_client.make_request(
                "POST",
                f"/api/v1/reddit/campaigns/{campaign_id}/execute-responses",
                json=execution_data
            )
            
            if success:
                posted = exec_result["data"]["responses_posted"]
                print(f"✅ Posted {posted} responses via API")
            else:
                print(f"❌ Execution failed: {exec_result['error']}")
        """
        
        print("\n🎉 API-based workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ API workflow error: {str(e)}")


# ========================================
# BATCH PROCESSING WORKFLOW
# ========================================

async def batch_processing_workflow():
    """
    Workflow for processing multiple campaigns in batch.
    Useful for managing multiple clients or campaign variations.
    """
    print("📦 Batch Processing Workflow")
    print("=" * 40)
    
    campaign_service = CampaignService(data_dir="data")
    
    # Multiple campaign configurations
    campaign_configs = [
        {
            "org_id": "batch-org-1",
            "name": "Python Community Engagement",
            "tone": ResponseTone.HELPFUL,
            "focus": "python programming"
        },
        {
            "org_id": "batch-org-2", 
            "name": "ML Research Outreach",
            "tone": ResponseTone.EDUCATIONAL,
            "focus": "machine learning research"
        },
        {
            "org_id": "batch-org-3",
            "name": "Startup Tech Consulting",
            "tone": ResponseTone.PROFESSIONAL,
            "focus": "startup technology consulting"
        }
    ]
    
    created_campaigns = []
    
    # Create multiple campaigns
    print("\n🎯 Creating Multiple Campaigns")
    for config in campaign_configs:
        create_request = CampaignCreateRequest(
            name=config["name"],
            description=f"Batch campaign focused on {config['focus']}",
            response_tone=config["tone"],
            max_responses_per_day=5
        )
        
        success, message, campaign = await campaign_service.create_campaign(
            config["org_id"], create_request
        )
        
        if success:
            created_campaigns.append((campaign, config))
            print(f"✅ Created: {campaign.name}")
        else:
            print(f"❌ Failed: {config['name']} - {message}")
    
    # Process each campaign
    print(f"\n🔄 Processing {len(created_campaigns)} Campaigns")
    
    for campaign, config in created_campaigns:
        print(f"\n📋 Processing: {campaign.name}")
        
        # Simulate document selection (in practice, you'd have real document IDs)
        document_ids = [f"{config['org_id']}-doc-1", f"{config['org_id']}-doc-2"]
        
        # Discover subreddits
        subreddit_request = SubredditDiscoveryRequest(document_ids=document_ids)
        
        success, message, subreddit_data = await campaign_service.discover_subreddits(
            campaign.id, subreddit_request
        )
        
        if success:
            subreddit_count = len(subreddit_data["subreddits"])
            print(f"   ✅ Found {subreddit_count} subreddits")
        else:
            print(f"   ❌ Subreddit discovery failed: {message}")
            continue
        
        # Note: In a real batch process, you'd continue with post discovery,
        # response generation, etc. for each campaign
    
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Campaigns Created: {len(created_campaigns)}")
    print(f"   Success Rate: {len(created_campaigns)/len(campaign_configs)*100:.1f}%")


# ========================================
# MAIN EXECUTION
# ========================================

async def main():
    """
    Main function to run workflow examples.
    """
    print("Reddit Marketing Complete Workflow Examples")
    print("=" * 60)
    print("Choose a workflow to run:")
    print("1. Complete Programmatic Workflow")
    print("2. Complete API-Based Workflow") 
    print("3. Batch Processing Workflow")
    print("4. Run All Workflows")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await complete_workflow_programmatic()
    elif choice == "2":
        await complete_workflow_api_based()
    elif choice == "3":
        await batch_processing_workflow()
    elif choice == "4":
        print("🚀 Running All Workflows")
        print("=" * 30)
        
        await complete_workflow_programmatic()
        print("\n" + "="*60 + "\n")
        
        await complete_workflow_api_based()
        print("\n" + "="*60 + "\n")
        
        await batch_processing_workflow()
        
        print("\n🎉 All workflows completed!")
    else:
        print("Invalid choice. Please run the script again.")


if __name__ == "__main__":
    asyncio.run(main())