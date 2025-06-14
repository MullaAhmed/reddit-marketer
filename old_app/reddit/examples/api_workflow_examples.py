"""
Examples for using the Reddit Marketing API endpoints.
Shows how to interact with the system via HTTP requests.
"""

import asyncio
import json
import requests
from typing import Dict, Any, Optional


class RedditMarketingAPIClient:
    """
    Client for interacting with the Reddit Marketing API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
    
    # Campaign Management
    def create_campaign(self, organization_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign."""
        return self._make_request(
            "POST", 
            f"/api/v1/reddit/campaigns/?organization_id={organization_id}",
            json=campaign_data
        )
    
    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign by ID."""
        return self._make_request("GET", f"/api/v1/reddit/campaigns/{campaign_id}")
    
    def list_campaigns(self, organization_id: str) -> Dict[str, Any]:
        """List campaigns for organization."""
        return self._make_request(
            "GET", 
            f"/api/v1/reddit/campaigns/?organization_id={organization_id}"
        )
    
    def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign status."""
        return self._make_request("GET", f"/api/v1/reddit/campaigns/{campaign_id}/status")
    
    # Workflow Steps
    def discover_subreddits(self, campaign_id: str, document_ids: list) -> Dict[str, Any]:
        """Discover subreddits for campaign."""
        return self._make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/discover-subreddits",
            json={"document_ids": document_ids}
        )
    
    def discover_posts(self, campaign_id: str, subreddits: list, reddit_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Discover posts in subreddits."""
        return self._make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/discover-posts",
            json={
                "subreddits": subreddits,
                "max_posts_per_subreddit": 10,
                "time_filter": "day"
            },
            params={"reddit_credentials": reddit_credentials}
        )
    
    def generate_responses(self, campaign_id: str, target_post_ids: list, tone: str = None) -> Dict[str, Any]:
        """Generate responses for target posts."""
        data = {"target_post_ids": target_post_ids}
        if tone:
            data["tone"] = tone
        
        return self._make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/generate-responses",
            json=data
        )
    
    def execute_responses(self, campaign_id: str, planned_response_ids: list, reddit_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Execute planned responses."""
        return self._make_request(
            "POST",
            f"/api/v1/reddit/campaigns/{campaign_id}/execute-responses",
            json={
                "planned_response_ids": planned_response_ids,
                "reddit_credentials": reddit_credentials
            }
        )


# ========================================
# API WORKFLOW EXAMPLES
# ========================================

def example_complete_api_workflow():
    """
    Complete workflow using API endpoints.
    """
    print("🚀 Complete API Workflow Example")
    print("=" * 50)
    
    # Initialize API client
    client = RedditMarketingAPIClient()
    
    # Configuration
    organization_id = "api-test-org-1"
    reddit_credentials = {
        "client_id": "YOUR_REDDIT_CLIENT_ID",
        "client_secret": "YOUR_REDDIT_CLIENT_SECRET",
        "username": "YOUR_REDDIT_USERNAME",
        "password": "YOUR_REDDIT_PASSWORD"
    }
    
    try:
        # Step 1: Create Campaign
        print("\n📝 Step 1: Creating Campaign")
        campaign_data = {
            "name": "API Test Campaign",
            "description": "Testing the Reddit marketing API workflow",
            "response_tone": "helpful",
            "max_responses_per_day": 5
        }
        
        result = client.create_campaign(organization_id, campaign_data)
        
        if "error" in result:
            print(f"❌ Failed to create campaign: {result['error']}")
            return
        
        campaign_id = result["campaign"]["id"]
        print(f"✅ Campaign created: {campaign_id}")
        
        # Step 2: List Campaigns
        print("\n📋 Step 2: Listing Campaigns")
        campaigns = client.list_campaigns(organization_id)
        
        if "error" not in campaigns:
            campaign_count = len(campaigns["data"]["campaigns"])
            print(f"✅ Found {campaign_count} campaigns for organization")
        
        # Step 3: Discover Subreddits
        print("\n🔍 Step 3: Discovering Subreddits")
        
        # Note: You need actual document IDs from your RAG system
        document_ids = ["doc-1", "doc-2"]  # Replace with real document IDs
        
        subreddit_result = client.discover_subreddits(campaign_id, document_ids)
        
        if "error" in subreddit_result:
            print(f"❌ Failed to discover subreddits: {subreddit_result['error']}")
            return
        
        subreddits = subreddit_result["data"]["subreddits"]
        print(f"✅ Found {len(subreddits)} relevant subreddits")
        
        # Step 4: Discover Posts
        print("\n📋 Step 4: Discovering Posts")
        
        post_result = client.discover_posts(
            campaign_id, 
            subreddits[:3],  # Use top 3 subreddits
            reddit_credentials
        )
        
        if "error" in post_result:
            print(f"❌ Failed to discover posts: {post_result['error']}")
            return
        
        posts_found = post_result["data"]["posts_found"]
        print(f"✅ Found {posts_found} relevant posts")
        
        # Step 5: Generate Responses
        print("\n💬 Step 5: Generating Responses")
        
        # Get updated campaign to access target posts
        campaign = client.get_campaign(campaign_id)
        
        if "error" in campaign:
            print(f"❌ Failed to get campaign: {campaign['error']}")
            return
        
        target_posts = campaign["campaign"]["target_posts"]
        
        if not target_posts:
            print("⚠️  No target posts found for response generation")
            return
        
        target_post_ids = [post["id"] for post in target_posts[:3]]
        
        response_result = client.generate_responses(
            campaign_id, 
            target_post_ids,
            tone="helpful"
        )
        
        if "error" in response_result:
            print(f"❌ Failed to generate responses: {response_result['error']}")
            return
        
        responses_generated = response_result["data"]["responses_generated"]
        print(f"✅ Generated {responses_generated} responses")
        
        # Step 6: Get Campaign Status
        print("\n📊 Step 6: Campaign Status")
        
        status = client.get_campaign_status(campaign_id)
        
        if "error" not in status:
            progress = status["data"]
            print(f"Status: {progress['status']}")
            print(f"Documents: {progress['documents_selected']}")
            print(f"Subreddits: {progress['subreddits_found']}")
            print(f"Posts: {progress['posts_found']}")
            print(f"Responses: {progress['responses_planned']}")
        
        # Step 7: Execute Responses (Commented for safety)
        print("\n🚀 Step 7: Execute Responses")
        print("⚠️  Response execution is commented out for safety")
        print("   Uncomment to actually post to Reddit")
        
        """
        # UNCOMMENT TO ACTUALLY POST TO REDDIT
        planned_responses = response_result["data"]["responses"]
        planned_response_ids = [resp["id"] for resp in planned_responses]
        
        execution_result = client.execute_responses(
            campaign_id,
            planned_response_ids,
            reddit_credentials
        )
        
        if "error" not in execution_result:
            posted = execution_result["data"]["responses_posted"]
            print(f"✅ Posted {posted} responses successfully")
        """
        
        print("\n🎉 API workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in API workflow: {str(e)}")


def example_individual_api_calls():
    """
    Examples of individual API calls.
    """
    print("🔧 Individual API Call Examples")
    print("=" * 40)
    
    client = RedditMarketingAPIClient()
    organization_id = "api-test-org-2"
    
    # Example 1: Create Campaign
    print("\n📝 Creating Campaign")
    campaign_data = {
        "name": "Individual API Test",
        "description": "Testing individual API endpoints",
        "response_tone": "professional"
    }
    
    result = client.create_campaign(organization_id, campaign_data)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    campaign_id = result["campaign"]["id"]
    print(f"✅ Created campaign: {campaign_id}")
    
    # Example 2: Get Campaign
    print("\n📄 Getting Campaign")
    campaign = client.get_campaign(campaign_id)
    
    if "error" not in campaign:
        print(f"✅ Retrieved: {campaign['campaign']['name']}")
        print(f"   Status: {campaign['campaign']['status']}")
    
    # Example 3: List Campaigns
    print("\n📋 Listing Campaigns")
    campaigns = client.list_campaigns(organization_id)
    
    if "error" not in campaigns:
        count = len(campaigns["data"]["campaigns"])
        print(f"✅ Found {count} campaigns")
        
        for camp in campaigns["data"]["campaigns"]:
            print(f"   • {camp['name']} ({camp['status']})")
    
    # Example 4: Get Status
    print("\n📊 Getting Campaign Status")
    status = client.get_campaign_status(campaign_id)
    
    if "error" not in status:
        progress = status["data"]
        print(f"✅ Status: {progress['status']}")
        print(f"   Progress: {progress['documents_selected']} docs, "
              f"{progress['subreddits_found']} subreddits, "
              f"{progress['posts_found']} posts")


def example_error_handling():
    """
    Example showing error handling with API calls.
    """
    print("⚠️  Error Handling Examples")
    print("=" * 30)
    
    client = RedditMarketingAPIClient()
    
    # Example 1: Invalid campaign ID
    print("\n🔍 Testing invalid campaign ID")
    result = client.get_campaign("invalid-campaign-id")
    
    if "error" in result:
        print(f"✅ Handled error: {result['error']}")
        print(f"   Status code: {result.get('status_code')}")
    
    # Example 2: Missing required fields
    print("\n📝 Testing missing required fields")
    result = client.create_campaign("test-org", {})  # Missing required fields
    
    if "error" in result:
        print(f"✅ Handled validation error: {result['error']}")
    
    # Example 3: Invalid subreddit discovery
    print("\n🔍 Testing invalid document IDs")
    result = client.discover_subreddits("invalid-campaign", ["invalid-doc"])
    
    if "error" in result:
        print(f"✅ Handled discovery error: {result['error']}")


def example_api_with_requests_library():
    """
    Example using requests library directly (without the client wrapper).
    """
    print("🌐 Direct Requests Library Example")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    organization_id = "direct-requests-org"
    
    # Example 1: Create Campaign with requests
    print("\n📝 Creating Campaign with requests")
    
    campaign_data = {
        "name": "Direct Requests Campaign",
        "description": "Using requests library directly",
        "response_tone": "casual"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/reddit/campaigns/?organization_id={organization_id}",
            json=campaign_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            campaign_id = result["campaign"]["id"]
            print(f"✅ Campaign created: {campaign_id}")
            
            # Example 2: Get Campaign with requests
            print("\n📄 Getting Campaign with requests")
            
            get_response = requests.get(
                f"{base_url}/api/v1/reddit/campaigns/{campaign_id}"
            )
            
            if get_response.status_code == 200:
                campaign = get_response.json()
                print(f"✅ Retrieved: {campaign['campaign']['name']}")
            else:
                print(f"❌ Error: {get_response.status_code}")
        
        else:
            print(f"❌ Error creating campaign: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")


# ========================================
# ASYNC API CLIENT EXAMPLE
# ========================================

import aiohttp

class AsyncRedditMarketingAPIClient:
    """
    Async client for the Reddit Marketing API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request."""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "status_code": response.status,
                            "message": await response.text()
                        }
            except aiohttp.ClientError as e:
                return {"error": str(e)}
    
    async def create_campaign(self, organization_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create campaign async."""
        return await self._make_request(
            "POST",
            f"/api/v1/reddit/campaigns/?organization_id={organization_id}",
            json=campaign_data,
            headers={"Content-Type": "application/json"}
        )
    
    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign async."""
        return await self._make_request("GET", f"/api/v1/reddit/campaigns/{campaign_id}")


async def example_async_api_client():
    """
    Example using async API client.
    """
    print("⚡ Async API Client Example")
    print("=" * 30)
    
    client = AsyncRedditMarketingAPIClient()
    organization_id = "async-test-org"
    
    # Create campaign
    campaign_data = {
        "name": "Async Test Campaign",
        "description": "Testing async API client"
    }
    
    result = await client.create_campaign(organization_id, campaign_data)
    
    if "error" not in result:
        campaign_id = result["campaign"]["id"]
        print(f"✅ Async campaign created: {campaign_id}")
        
        # Get campaign
        campaign = await client.get_campaign(campaign_id)
        
        if "error" not in campaign:
            print(f"✅ Async retrieval: {campaign['campaign']['name']}")
    else:
        print(f"❌ Async error: {result['error']}")


# ========================================
# MAIN EXECUTION
# ========================================

def main():
    """
    Main function to run API examples.
    """
    print("Reddit Marketing API Examples")
    print("=" * 40)
    print("Choose an example to run:")
    print("1. Complete API workflow")
    print("2. Individual API calls")
    print("3. Error handling")
    print("4. Direct requests library")
    print("5. Async API client")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        example_complete_api_workflow()
    elif choice == "2":
        example_individual_api_calls()
    elif choice == "3":
        example_error_handling()
    elif choice == "4":
        example_api_with_requests_library()
    elif choice == "5":
        asyncio.run(example_async_api_client())
    else:
        print("Invalid choice. Please run the script again.")


if __name__ == "__main__":
    main()