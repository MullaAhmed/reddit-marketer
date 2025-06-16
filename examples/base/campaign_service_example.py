"""
Example: Campaign Service using Base Classes

This example demonstrates how to use the CampaignService directly
without going through the API layer.
"""
import asyncio
import traceback
import os
from dotenv import load_dotenv

from app.services.campaign_service import CampaignService
from app.models.campaign import (
    CampaignCreateRequest, SubredditDiscoveryRequest, 
    PostDiscoveryRequest, ResponseGenerationRequest, 
    ResponseExecutionRequest, ResponseTone
)

load_dotenv(dotenv_path=".env",override=True)

# Mock Reddit credentials for demonstration
MOCK_REDDIT_CREDENTIALS = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "username": os.getenv("REDDIT_USERNAME"),
    "password": os.getenv("REDDIT_PASSWORD")
}

async def setup_sample_documents(campaign_service):
    """Set up sample documents for the campaign."""
    print("📄 Setting up sample documents...")
    
    sample_documents = [
        {
            "title": "Python Web Development Expertise",
            "content": """
            We are experts in Python web development with over 5 years of experience building
            scalable web applications using FastAPI, Django, and Flask. Our team specializes
            in REST API development, microservices architecture, and database optimization.
            We have successfully delivered projects for startups and enterprise app.clients.
            """,
            "metadata": {"category": "expertise", "technology": "python"}
        },
        {
            "title": "Machine Learning Consulting Services",
            "content": """
            Our machine learning practice helps businesses implement AI solutions using
            Python libraries like scikit-learn, TensorFlow, and PyTorch. We provide
            end-to-end ML services from data preprocessing to model deployment in production.
            Our expertise includes predictive analytics, recommendation systems, and NLP.
            """,
            "metadata": {"category": "services", "technology": "machine-learning"}
        }
    ]
    
    org_id = "campaign-example-org"
    
    # Use the document service from campaign service
    success, message, document_ids = campaign_service.document_service.ingest_documents(
        documents=sample_documents,
        org_id=org_id,
        org_name="Campaign Example Organization"
    )
    
    if success:
        print(f"✅ Documents ingested: {document_ids}")
        return org_id, document_ids
    else:
        print(f"❌ Document ingestion failed: {message}")
        return org_id, []

async def main():
    """Run campaign service examples."""
    print("🚀 Campaign Service Base Class Examples")
    print("=" * 50)
    
    # Initialize the campaign service
    campaign_service = CampaignService(data_dir="examples_data")
    
    try:
        # Setup sample documents
        org_id, document_ids = await setup_sample_documents(campaign_service)
        
        # 1. Create a campaign
        print("\n1. 📝 Creating a campaign...")
        
        create_request = CampaignCreateRequest(
            name="Python Community Engagement",
            description="Engage with Python communities to share expertise and help developers",
            response_tone=ResponseTone.HELPFUL,
            max_responses_per_day=5
        )
        
        success, message, campaign = await campaign_service.create_campaign(
            organization_id=org_id,
            request=create_request
        )
        
        if success:
            print(f"✅ {message}")
            print(f"📋 Campaign ID: {campaign.id}")
            print(f"📝 Name: {campaign.name}")
            print(f"📊 Status: {campaign.status}")
            print(f"🎯 Tone: {campaign.response_tone}")
        else:
            print(f"❌ Campaign creation failed: {message}")
            return
        
        campaign_id = campaign.id
        
        # 2. Discover subreddits
        print("\n2. 🔍 Discovering subreddits...")
        
        if document_ids:
            subreddit_request = SubredditDiscoveryRequest(
                document_ids=document_ids
            )
            
            success, message, discovery_data = await campaign_service.discover_subreddits(
                campaign_id=campaign_id,
                request=subreddit_request
            )
            
            if success:
                print(f"✅ {message}")
                subreddits = discovery_data.get('subreddits', [])
                print(f"📊 Found subreddits: {subreddits}")
                
                # Get updated campaign
                _, _, updated_campaign = await campaign_service.get_campaign(campaign_id)
                print(f"📈 Campaign status: {updated_campaign.status}")
            else:
                print(f"❌ Subreddit discovery failed: {message}")
        else:
            print("⚠️  Skipping subreddit discovery (no documents available)")
        
        # 3. Discover posts
        print("\n3. 📝 Discovering posts...")
        print("⚠️  Note: This will fail with mock credentials, but demonstrates the workflow")
        
        # Get the campaign to see discovered subreddits
        _, _, current_campaign = await campaign_service.get_campaign(campaign_id)
        target_subreddits = current_campaign.target_subreddits[:3] if current_campaign.target_subreddits else ["python", "learnpython"]
        
        post_request = PostDiscoveryRequest(
            subreddits=target_subreddits,
            max_posts_per_subreddit=50,
            time_filter="week",
            reddit_credentials=MOCK_REDDIT_CREDENTIALS
        )
        
        try:
            success, message, posts_data = await campaign_service.discover_posts(
                campaign_id=campaign_id,
                request=post_request
            )
            
            if success:
                print(f"✅ {message}")
                posts_found = posts_data.get('posts_found', 0)
                print(f"📊 Posts found: {posts_found}")
                
                # Get updated campaign
                _, _, updated_campaign = await campaign_service.get_campaign(campaign_id)
                print(f"📈 Campaign status: {updated_campaign.status}")
                print(f"📝 Target posts: {len(updated_campaign.target_posts)}")
            else:
                print(f"⚠️  Post discovery failed (expected): {message}")
                
        except Exception as e:
            print(f"⚠️  Post discovery error (expected with mock credentials): {e}")
        
        # 4. Generate responses
        print("\n4. 💬 Generating responses...")
        
        # Get current campaign state
        _, _, current_campaign = await campaign_service.get_campaign(campaign_id)
        
        if current_campaign.target_posts:
            target_post_ids = [post.id for post in current_campaign.target_posts]
            
            response_request = ResponseGenerationRequest(
                target_post_ids=target_post_ids,
                tone=ResponseTone.HELPFUL
            )
            
            success, message, response_data = await campaign_service.generate_responses(
                campaign_id=campaign_id,
                request=response_request
            )
            
            if success:
                print(f"✅ {message}")
                responses_generated = response_data.get('responses_generated', 0)
                print(f"💬 Responses generated: {responses_generated}")
                
                # Show sample responses
                if 'responses' in response_data:
                    print("\n📝 Sample responses:")
                    for i, resp in enumerate(response_data['responses'][:2], 1):
                        print(f"   {i}. Target: {resp['target_post_id']}")
                        print(f"      🎯 Tone: {resp['tone']}")
                        print(f"      ⭐ Confidence: {resp['confidence_score']:.2f}")
                        print(f"      📝 Content: {resp['response_content'][:100]}...")
                        print()
                
                # Get updated campaign
                _, _, updated_campaign = await campaign_service.get_campaign(campaign_id)
                print(f"📈 Campaign status: {updated_campaign.status}")
            else:
                print(f"❌ Response generation failed: {message}")
        else:
            print("⚠️  No target posts available for response generation")
        
        # 5. Execute responses
        print("\n5. 🚀 Executing responses...")
        print("⚠️  Note: This will fail with mock credentials")
        
        # Get current campaign state
        _, _, current_campaign = await campaign_service.get_campaign(campaign_id)
        
        if current_campaign.planned_responses:
            planned_response_ids = [resp.id for resp in current_campaign.planned_responses[:2]]
            
            execution_request = ResponseExecutionRequest(
                planned_response_ids=planned_response_ids,
                reddit_credentials=MOCK_REDDIT_CREDENTIALS
            )
            
            try:
                success, message, execution_data = await campaign_service.execute_responses(
                    campaign_id=campaign_id,
                    request=execution_request
                )
                
                if success:
                    print(f"✅ {message}")
                    responses_posted = execution_data.get('responses_posted', 0)
                    responses_failed = execution_data.get('responses_failed', 0)
                    print(f"🎉 Posted: {responses_posted}, Failed: {responses_failed}")
                    
                    # Get final campaign state
                    _, _, final_campaign = await campaign_service.get_campaign(campaign_id)
                    print(f"📈 Final campaign status: {final_campaign.status}")
                else:
                    print(f"⚠️  Response execution failed (expected): {message}")
                    
            except Exception as e:
                print(f"⚠️  Response execution error (expected): {e}")
        else:
            print("⚠️  No planned responses available for execution")
        
        # 6. Get campaign details and status
        print("\n6. 📊 Getting campaign status...")
        
        success, message, final_campaign = await campaign_service.get_campaign(campaign_id)
        
        if success:
            print(f"✅ Campaign details retrieved")
            print(f"📋 Name: {final_campaign.name}")
            print(f"📊 Status: {final_campaign.status}")
            print(f"📄 Documents selected: {len(final_campaign.selected_document_ids)}")
            print(f"🎯 Target subreddits: {len(final_campaign.target_subreddits)}")
            print(f"📝 Target posts: {len(final_campaign.target_posts)}")
            print(f"💬 Planned responses: {len(final_campaign.planned_responses)}")
            print(f"🎉 Posted responses: {len(final_campaign.posted_responses)}")
            
            # Calculate success metrics
            successful_posts = len([r for r in final_campaign.posted_responses if r.posting_successful])
            failed_posts = len([r for r in final_campaign.posted_responses if not r.posting_successful])
            
            print(f"✅ Successful posts: {successful_posts}")
            print(f"❌ Failed posts: {failed_posts}")
            
            print(f"\n📅 Created: {final_campaign.created_at}")
            print(f"📅 Updated: {final_campaign.updated_at}")
        else:
            print(f"❌ Failed to get campaign details: {message}")
        
        # 7. List campaigns for organization
        print("\n7. 📋 Listing campaigns for organization...")
        
        success, message, campaigns = await campaign_service.list_campaigns(org_id)
        
        if success:
            print(f"✅ {message}")
            print("📊 Campaigns:")
            for i, camp in enumerate(campaigns, 1):
                print(f"   {i}. {camp.name}")
                print(f"      📊 Status: {camp.status}")
                print(f"      📅 Created: {camp.created_at}")
                print()
        else:
            print(f"❌ Failed to list campaigns: {message}")
        
        print("\n✅ Campaign service examples completed!")
        
        print("\n💡 Summary of workflow:")
        print("   1. ✅ Campaign created")
        print("   2. ✅ Subreddits discovered (if documents available)")
        print("   3. ⚠️  Posts discovered (requires real Reddit credentials)")
        print("   4. ✅ Responses generated (if posts available)")
        print("   5. ⚠️  Responses executed (requires real Reddit credentials)")
        print("   6. ✅ Campaign status monitored")
        
        print("\n🔧 For real usage:")
        print("   1. Replace mock Reddit credentials with real ones")
        print("   2. Ensure documents are properly ingested")
        print("   3. Review all generated responses before posting")
        print("   4. Monitor campaign progress and adjust strategy")
        
    except Exception as e:
        print(f"❌ Error in campaign service example: {e}")
        traceback.print_exc()
    
    finally:
        # Clean up resources
        await campaign_service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())