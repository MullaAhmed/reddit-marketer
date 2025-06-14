"""
Example: Campaign Management using REST API

This example demonstrates how to:
1. Create a new campaign
2. Get campaign details
3. List campaigns for an organization
4. Get campaign status and progress
"""

import requests
import json
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ORGANIZATION_ID = "example-org"

def create_campaign(name: str, description: str = None, response_tone: str = "helpful") -> Dict[str, Any]:
    """Create a new campaign."""
    url = f"{API_BASE_URL}/campaigns/"
    params = {"organization_id": ORGANIZATION_ID}
    
    payload = {
        "name": name,
        "description": description,
        "response_tone": response_tone,
        "max_responses_per_day": 10
    }
    
    response = requests.post(url, params=params, json=payload)
    response.raise_for_status()
    return response.json()

def get_campaign(campaign_id: str) -> Dict[str, Any]:
    """Get campaign details."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def list_campaigns() -> Dict[str, Any]:
    """List all campaigns for organization."""
    url = f"{API_BASE_URL}/campaigns/"
    params = {"organization_id": ORGANIZATION_ID}
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_campaign_status(campaign_id: str) -> Dict[str, Any]:
    """Get detailed campaign status."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/status"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def discover_subreddits_for_campaign(campaign_id: str, document_ids: List[str]) -> Dict[str, Any]:
    """Discover subreddits for campaign."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/discover-subreddits"
    
    payload = {"document_ids": document_ids}
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def main():
    """Run campaign management examples."""
    print("🚀 Campaign Management API Examples")
    print("=" * 50)
    
    campaign_id = None
    
    try:
        # 1. Create a new campaign
        print("\n1. 📝 Creating a new campaign...")
        
        campaign_data = create_campaign(
            name="Python Community Outreach",
            description="Engage with Python learning communities to share expertise",
            response_tone="helpful"
        )
        
        if campaign_data['success']:
            campaign = campaign_data['campaign']
            campaign_id = campaign['id']
            
            print(f"✅ Campaign created successfully!")
            print(f"📋 ID: {campaign_id}")
            print(f"📝 Name: {campaign['name']}")
            print(f"📊 Status: {campaign['status']}")
            print(f"🎯 Tone: {campaign['response_tone']}")
            print(f"📅 Created: {campaign['created_at']}")
        
        # 2. Get campaign details
        if campaign_id:
            print(f"\n2. 📖 Getting campaign details...")
            
            result = get_campaign(campaign_id)
            if result['success']:
                campaign = result['campaign']
                print(f"✅ Campaign details retrieved:")
                print(f"   📋 Name: {campaign['name']}")
                print(f"   📊 Status: {campaign['status']}")
                print(f"   📄 Description: {campaign['description']}")
                print(f"   🎯 Max responses/day: {campaign['max_responses_per_day']}")
        
        # 3. List all campaigns
        print(f"\n3. 📋 Listing all campaigns for organization...")
        
        result = list_campaigns()
        if result['success']:
            campaigns = result['data']['campaigns']
            print(f"✅ Found {len(campaigns)} campaigns:")
            
            for i, campaign in enumerate(campaigns, 1):
                print(f"   {i}. {campaign['name']}")
                print(f"      📊 Status: {campaign['status']}")
                print(f"      📅 Created: {campaign['created_at']}")
                print()
        
        # 4. Get campaign status
        if campaign_id:
            print(f"\n4. 📊 Getting campaign status...")
            
            result = get_campaign_status(campaign_id)
            if result['success']:
                status_data = result['data']
                print(f"✅ Campaign status:")
                print(f"   📊 Status: {status_data['status']}")
                print(f"   📄 Documents selected: {status_data['documents_selected']}")
                print(f"   🎯 Subreddits found: {status_data['subreddits_found']}")
                print(f"   📝 Posts found: {status_data['posts_found']}")
                print(f"   💬 Responses planned: {status_data['responses_planned']}")
                print(f"   ✅ Responses posted: {status_data['responses_posted']}")
                print(f"   🎉 Successful posts: {status_data['successful_posts']}")
                print(f"   ❌ Failed posts: {status_data['failed_posts']}")
        
        # 5. Example of subreddit discovery (requires documents)
        print(f"\n5. 🔍 Example: Subreddit discovery...")
        print("ℹ️  Note: This requires documents to be ingested first")
        print("   Run the document_management.py example first to ingest documents")
        
        # Uncomment the following lines if you have documents ingested:
        # if campaign_id:
        #     try:
        #         result = discover_subreddits_for_campaign(campaign_id, ["doc-id-1", "doc-id-2"])
        #         if result['success']:
        #             print(f"✅ Subreddit discovery completed")
        #             print(f"📊 Found {len(result['data']['subreddits'])} subreddits")
        #     except Exception as e:
        #         print(f"⚠️  Subreddit discovery failed: {e}")
        
        print("\n✅ Campaign management examples completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"📝 Error details: {error_detail}")
            except:
                print(f"📝 Response text: {e.response.text}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()