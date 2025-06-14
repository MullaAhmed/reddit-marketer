"""
Example workflow demonstrating the complete Reddit marketing campaign process.
"""

import asyncio
import json
from reddit.services.campaign_service import CampaignService
from reddit.models import (
    CampaignCreateRequest, SubredditDiscoveryRequest, PostDiscoveryRequest,
    ResponseGenerationRequest, ResponseExecutionRequest, ResponseTone
)

async def run_complete_campaign_workflow():
    """
    Demonstrates the complete workflow from campaign creation to response posting.
    """
    
    # Initialize service
    campaign_service = CampaignService()
    
    # Configuration
    organization_id = "test-org-1"
    reddit_credentials = {
        "client_id": "YOUR_REDDIT_CLIENT_ID",
        "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
        "username": "YOUR_REDDIT_USERNAME",
        "password": "YOUR_REDDIT_PASSWORD"
    }
    
    print("🚀 Starting Reddit Marketing Campaign Workflow")
    print("=" * 50)
    
    # Step 1: Create Campaign
    print("\n📝 Step 1: Creating Campaign")
    create_request = CampaignCreateRequest(
        name="Python Learning Community Outreach",
        description="Engage with Python learning communities to share expertise",
        response_tone=ResponseTone.HELPFUL,
        max_responses_per_day=5
    )
    
    success, message, campaign = await campaign_service.create_campaign(
        organization_id, create_request
    )
    
    if not success:
        print(f"❌ Failed to create campaign: {message}")
        return
    
    print(f"✅ Campaign created: {campaign.name} (ID: {campaign.id})")
    
    # Step 2: Discover Subreddits
    print("\n🔍 Step 2: Discovering Subreddits")
    
    # Assuming you have documents already uploaded with these IDs
    # In practice, you'd get these from your document ingestion system
    document_ids = ["doc-1", "doc-2"]  # Replace with actual document IDs
    
    subreddit_request = SubredditDiscoveryRequest(
        document_ids=document_ids
    )
    
    success, message, subreddit_data = await campaign_service.discover_subreddits(
        campaign.id, subreddit_request
    )
    
    if not success:
        print(f"❌ Failed to discover subreddits: {message}")
        return
    
    print(f"✅ Found {len(subreddit_data['subreddits'])} relevant subreddits:")
    for subreddit in subreddit_data['subreddits'][:5]:
        print(f"   - r/{subreddit}")
    
    # Step 3: Discover Posts
    print("\n📋 Step 3: Discovering Posts")
    
    post_request = PostDiscoveryRequest(
        subreddits=subreddit_data['subreddits'][:3],  # Use top 3 subreddits
        max_posts_per_subreddit=10,
        time_filter="day"
    )
    
    success, message, post_data = await campaign_service.discover_posts(
        campaign.id, post_request, reddit_credentials
    )
    
    if not success:
        print(f"❌ Failed to discover posts: {message}")
        return
    
    print(f"✅ Found {post_data['posts_found']} relevant posts")
    
    # Step 4: Generate Responses
    print("\n💬 Step 4: Generating Responses")
    
    # Get updated campaign to access target posts
    success, message, updated_campaign = await campaign_service.get_campaign(campaign.id)
    
    if not success or not updated_campaign.target_posts:
        print("❌ No target posts found for response generation")
        return
    
    # Select top 3 posts for response generation
    target_post_ids = [post.id for post in updated_campaign.target_posts[:3]]
    
    response_request = ResponseGenerationRequest(
        target_post_ids=target_post_ids,
        tone=ResponseTone.HELPFUL
    )
    
    success, message, response_data = await campaign_service.generate_responses(
        campaign.id, response_request
    )
    
    if not success:
        print(f"❌ Failed to generate responses: {message}")
        return
    
    print(f"✅ Generated {response_data['responses_generated']} responses")
    
    # Step 5: Review Generated Responses (Optional)
    print("\n👀 Step 5: Reviewing Generated Responses")
    
    for i, response in enumerate(response_data['responses'][:2], 1):
        print(f"\nResponse {i}:")
        print(f"Confidence: {response['confidence_score']:.2f}")
        print(f"Content: {response['response_content'][:100]}...")
    
    # Step 6: Execute Responses (Commented out for safety)
    print("\n🚀 Step 6: Execute Responses")
    print("⚠️  Response execution is commented out for safety.")
    print("   Uncomment the code below to actually post to Reddit.")
    
    """
    # UNCOMMENT TO ACTUALLY POST TO REDDIT
    execution_request = ResponseExecutionRequest(
        planned_response_ids=[resp['id'] for resp in response_data['responses']],
        reddit_credentials=reddit_credentials
    )
    
    success, message, execution_data = await campaign_service.execute_responses(
        campaign.id, execution_request
    )
    
    if not success:
        print(f"❌ Failed to execute responses: {message}")
        return
    
    print(f"✅ Posted {execution_data['responses_posted']} responses successfully")
    """
    
    # Step 7: Check Campaign Status
    print("\n📊 Step 7: Campaign Status")
    
    success, message, final_campaign = await campaign_service.get_campaign(campaign.id)
    
    if success:
        print(f"Campaign Status: {final_campaign.status}")
        print(f"Documents Selected: {len(final_campaign.selected_document_ids)}")
        print(f"Subreddits Found: {len(final_campaign.target_subreddits)}")
        print(f"Posts Found: {len(final_campaign.target_posts)}")
        print(f"Responses Planned: {len(final_campaign.planned_responses)}")
        print(f"Responses Posted: {len(final_campaign.posted_responses)}")
    
    print("\n🎉 Campaign workflow completed!")
    print("=" * 50)


async def run_step_by_step_example():
    """
    Example showing how to run each step individually with proper error handling.
    """
    
    campaign_service = CampaignService()
    organization_id = "test-org-2"
    
    try:
        # Create campaign
        create_request = CampaignCreateRequest(
            name="AI/ML Community Engagement",
            description="Share AI/ML expertise with relevant communities"
        )
        
        success, message, campaign = await campaign_service.create_campaign(
            organization_id, create_request
        )
        
        if not success:
            raise Exception(f"Campaign creation failed: {message}")
        
        print(f"✅ Created campaign: {campaign.id}")
        
        # List campaigns for organization
        success, message, campaigns = await campaign_service.list_campaigns(organization_id)
        print(f"📋 Organization has {len(campaigns)} campaigns")
        
        # Get campaign details
        success, message, retrieved_campaign = await campaign_service.get_campaign(campaign.id)
        print(f"📄 Retrieved campaign: {retrieved_campaign.name}")
        
    except Exception as e:
        print(f"❌ Error in workflow: {str(e)}")


if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Complete Campaign Workflow")
    print("2. Step-by-Step Example")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(run_complete_campaign_workflow())
    elif choice == "2":
        asyncio.run(run_step_by_step_example())
    else:
        print("Invalid choice. Please run the script again.")