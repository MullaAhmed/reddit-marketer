"""
Example: Subreddit Discovery using REST API

This example demonstrates how to:
1. Extract topics from content
2. Discover relevant subreddits
3. Search for specific subreddits
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ORGANIZATION_ID = "example-org"

def extract_topics(content: str) -> Dict[str, Any]:
    """Extract topics from content."""
    url = f"{API_BASE_URL}/subreddits/extract-topics"
    params = {"organization_id": ORGANIZATION_ID}
    
    response = requests.post(url, params=params, json={"content": content})
    response.raise_for_status()
    return response.json()

def discover_subreddits(content: str, min_subscribers: int = 10000) -> Dict[str, Any]:
    """Discover relevant subreddits."""
    url = f"{API_BASE_URL}/subreddits/discover"
    params = {
        "organization_id": ORGANIZATION_ID,
        "min_subscribers": min_subscribers
    }
    
    response = requests.post(url, params=params, json={"content": content})
    response.raise_for_status()
    return response.json()

def search_subreddits(query: str, limit: int = 25) -> Dict[str, Any]:
    """Search for subreddits by name or topic."""
    url = f"{API_BASE_URL}/subreddits/search"
    params = {"query": query, "limit": limit}
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_subreddit_info(subreddit_name: str) -> Dict[str, Any]:
    """Get information about a specific subreddit."""
    url = f"{API_BASE_URL}/subreddits/{subreddit_name}/info"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def main():
    """Run subreddit discovery examples."""
    print("🚀 Subreddit Discovery API Examples")
    print("=" * 50)
    
    # Sample content for analysis
    sample_content = """
    I'm a Python developer with expertise in web development using FastAPI and Django.
    I specialize in building REST APIs, microservices, and data processing pipelines.
    I also work with machine learning using scikit-learn and TensorFlow for predictive analytics.
    My experience includes database design with PostgreSQL, cloud deployment on AWS,
    and containerization with Docker. I enjoy helping others learn programming and
    sharing knowledge about best practices in software development.
    """
    
    try:
        # 1. Extract topics from content
        print("\n1. 🏷️ Extracting topics from content...")
        print(f"📝 Content: {sample_content[:100]}...")
        
        result = extract_topics(sample_content)
        if result['success']:
            topics = result['data']['topics']
            print(f"✅ Extracted {len(topics)} topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
        
        # 2. Discover relevant subreddits
        print("\n2. 🔍 Discovering relevant subreddits...")
        result = discover_subreddits(sample_content, min_subscribers=5000)
        
        if result['success']:
            subreddits = result['data'].get('relevant_subreddits', {})
            print(f"✅ Found {len(subreddits)} relevant subreddits:")
            
            for name, info in list(subreddits.items())[:5]:
                subscribers = info.get('subscribers', 0)
                description = info.get('about', '')[:100]
                print(f"  📍 r/{name}")
                print(f"     👥 {subscribers:,} subscribers")
                print(f"     📄 {description}...")
                print()
        
        # 3. Search for specific subreddits
        print("\n3. 🔎 Searching for Python-related subreddits...")
        search_queries = ["python", "programming", "webdev"]
        
        for query in search_queries:
            print(f"\n🔍 Searching for: '{query}'")
            result = search_subreddits(query, limit=5)
            
            if result['success']:
                print(f"✅ Search completed for '{query}'")
                # Note: This is a placeholder response in the current implementation
                print(f"📊 Results: {result['data']['total']}")
        
        # 4. Get specific subreddit information
        print("\n4. 📊 Getting subreddit information...")
        subreddit_names = ["python", "programming", "webdev"]
        
        for name in subreddit_names:
            print(f"\n📍 Getting info for r/{name}...")
            result = get_subreddit_info(name)
            
            if result['success']:
                data = result['data']
                print(f"✅ r/{name}")
                print(f"   👥 Subscribers: {data['subscribers']:,}")
                print(f"   📄 Description: {data['description'][:100]}...")
        
        print("\n✅ Subreddit discovery examples completed successfully!")
        
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