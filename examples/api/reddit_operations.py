"""
Example: Reddit Operations using REST API

This example demonstrates how to:
1. Discover posts in subreddits
2. Generate responses for posts
3. Execute (post) responses to Reddit
4. Track response status
"""

import requests
import json
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ORGANIZATION_ID = "example-org"

# Mock Reddit credentials for demonstration
MOCK_REDDIT_CREDENTIALS = {
    "client_id": "your_reddit_client_id",
    "client_secret": "your_reddit_client_secret",
    "username": "your_reddit_username",
    "password": "your_reddit_password"
}

def discover_posts_for_campaign(
    campaign_id: str, 
    subreddits: List[str], 
    max_posts_per_subreddit: int = 10,
    time_filter: str = "day"
) -> Dict[str, Any]:
    """Discover posts for a campaign."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/discover-posts"
    
    payload = {
        "subreddits": subreddits,
        "max_posts_per_subreddit": max_posts_per_subreddit,
        "time_filter": time_filter,
        "reddit_credentials": MOCK_REDDIT_CREDENTIALS
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def generate_responses_for_campaign(
    campaign_id: str, 
    target_post_ids: List[str],
    tone: str = None
) -> Dict[str, Any]:
    """Generate responses for target posts."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/generate-responses"
    
    payload = {
        "target_post_ids": target_post_ids,
        "tone": tone
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def execute_responses_for_campaign(
    campaign_id: str, 
    planned_response_ids: List[str]
) -> Dict[str, Any]:
    """Execute planned responses."""
    url = f"{API_BASE_URL}/campaigns/{campaign_id}/execute-responses"
    
    payload = {
        "planned_response_ids": planned_response_ids,
        "reddit_credentials": MOCK_REDDIT_CREDENTIALS
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def create_sample_campaign() -> str:
    """Create a sample campaign for demonstration."""
    url = f"{API_BASE_URL}/campaigns/"
    params = {"organization_id": ORGANIZATION_ID}
    
    payload = {
        "name": "Reddit Operations Demo",
        "description": "Demonstration of Reddit operations",
        "response_tone": "helpful",
        "max_responses_per_day": 5
    }
    
    response = requests.post(url, params=params, json=payload)
    response.raise_for_status()
    result = response.json()
    
    return result['campaign']['id']

def main():
    """Run Reddit operations examples."""
    print("🚀 Reddit Operations API Examples")
    print("=" * 50)
    
    print("⚠️  Note: This example uses mock Reddit credentials")
    print("   Replace MOCK_REDDIT_CREDENTIALS with real credentials for actual usage")
    print()
    
    try:
        # 1. Create a sample campaign
        print("1. 📝 Creating sample campaign...")
        campaign_id = create_sample_campaign()
        print(f"✅ Campaign created: {campaign_id}")
        
        # 2. Discover posts (this will fail with mock credentials, but shows the API structure)
        print("\n2. 🔍 Discovering posts in subreddits...")
        
        target_subreddits = ["python", "learnpython", "programming"]
        
        try:
            result = discover_posts_for_campaign(
                campaign_id=campaign_id,
                subreddits=target_subreddits,
                max_posts_per_subreddit=5,
                time_filter="day"
            )
            
            if result['success']:
                posts_found = result['data']['posts_found']
                print(f"✅ Post discovery completed")
                print(f"📊 Found {posts_found} relevant posts")
                print(f"🎯 Searched {len(target_subreddits)} subreddits")
                
                # Show sample posts
                if 'posts' in result['data']:
                    print("\n📝 Sample posts found:")
                    for i, post in enumerate(result['data']['posts'][:3], 1):
                        print(f"   {i}. {post['title']}")
                        print(f"      📍 r/{post['subreddit']}")
                        print(f"      ⭐ Score: {post['relevance_score']:.2f}")
                        print(f"      💬 {post['num_comments']} comments")
                        print()
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Post discovery failed (expected with mock credentials): {e}")
            print("   This is normal when using mock Reddit credentials")
        
        # 3. Generate responses (mock example)
        print("\n3. 💬 Generating responses for posts...")
        
        # Mock target post IDs for demonstration
        mock_post_ids = ["post-1", "post-2", "post-3"]
        
        try:
            result = generate_responses_for_campaign(
                campaign_id=campaign_id,
                target_post_ids=mock_post_ids,
                tone="helpful"
            )
            
            if result['success']:
                responses_generated = result['data']['responses_generated']
                print(f"✅ Response generation completed")
                print(f"💬 Generated {responses_generated} responses")
                
                # Show sample responses
                if 'responses' in result['data']:
                    print("\n📝 Sample generated responses:")
                    for i, response in enumerate(result['data']['responses'][:2], 1):
                        print(f"   {i}. Response for post {response['target_post_id']}")
                        print(f"      🎯 Tone: {response['tone']}")
                        print(f"      ⭐ Confidence: {response['confidence_score']:.2f}")
                        print(f"      📝 Content: {response['response_content'][:100]}...")
                        print()
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Response generation failed: {e}")
            print("   This may happen if no posts were found in the previous step")
        
        # 4. Execute responses (mock example)
        print("\n4. 🚀 Executing responses...")
        
        # Mock planned response IDs for demonstration
        mock_response_ids = ["response-1", "response-2"]
        
        try:
            result = execute_responses_for_campaign(
                campaign_id=campaign_id,
                planned_response_ids=mock_response_ids
            )
            
            if result['success']:
                responses_posted = result['data']['responses_posted']
                responses_failed = result['data']['responses_failed']
                
                print(f"✅ Response execution completed")
                print(f"🎉 Successfully posted: {responses_posted}")
                print(f"❌ Failed to post: {responses_failed}")
                
                # Show execution results
                if 'posted_responses' in result['data']:
                    print("\n📊 Execution results:")
                    for i, posted in enumerate(result['data']['posted_responses'], 1):
                        status = "✅ Success" if posted['posting_successful'] else "❌ Failed"
                        print(f"   {i}. {status}")
                        if posted['posting_successful']:
                            print(f"      🔗 Reddit ID: {posted['reddit_comment_id']}")
                        else:
                            print(f"      ⚠️  Error: {posted['error_message']}")
                        print()
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Response execution failed: {e}")
            print("   This is expected when using mock Reddit credentials")
        
        # 5. Get final campaign status
        print("\n5. 📊 Getting final campaign status...")
        
        status_url = f"{API_BASE_URL}/campaigns/{campaign_id}/status"
        response = requests.get(status_url)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                status_data = result['data']
                print(f"✅ Final campaign status:")
                print(f"   📊 Status: {status_data['status']}")
                print(f"   📝 Posts found: {status_data['posts_found']}")
                print(f"   💬 Responses planned: {status_data['responses_planned']}")
                print(f"   🎉 Responses posted: {status_data['responses_posted']}")
        
        print("\n✅ Reddit operations examples completed!")
        print("\n💡 Tips for real usage:")
        print("   1. Replace mock credentials with real Reddit API credentials")
        print("   2. Ensure you have documents ingested for better subreddit discovery")
        print("   3. Always review generated responses before posting")
        print("   4. Respect Reddit's rate limits and community guidelines")
        
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