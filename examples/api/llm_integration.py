"""
Example: LLM Integration using REST API

This example demonstrates how to:
1. Use LLM services through the API
2. Test different LLM providers
3. Generate structured responses
4. Handle LLM errors and retries
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_health_check() -> Dict[str, Any]:
    """Test API health and LLM service availability."""
    url = f"{API_BASE_URL}/health/detailed"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def query_documents_with_llm(query: str, organization_id: str = "example-org") -> Dict[str, Any]:
    """Query documents using LLM-powered semantic search."""
    url = f"{API_BASE_URL}/documents/query"
    
    payload = {
        "query": query,
        "organization_id": organization_id,
        "method": "semantic",
        "top_k": 5
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def extract_topics_with_llm(content: str, organization_id: str = "example-org") -> Dict[str, Any]:
    """Extract topics using LLM analysis."""
    url = f"{API_BASE_URL}/subreddits/extract-topics"
    params = {"organization_id": organization_id}
    
    response = requests.post(url, params=params, json={"content": content})
    response.raise_for_status()
    return response.json()

def discover_subreddits_with_llm(content: str, organization_id: str = "example-org") -> Dict[str, Any]:
    """Discover subreddits using LLM analysis."""
    url = f"{API_BASE_URL}/subreddits/discover"
    params = {"organization_id": organization_id}
    
    response = requests.post(url, params=params, json={"content": content})
    response.raise_for_status()
    return response.json()

def main():
    """Run LLM integration examples."""
    print("🚀 LLM Integration API Examples")
    print("=" * 50)
    
    try:
        # 1. Check LLM service health
        print("\n1. 🏥 Checking LLM service health...")
        
        health_result = test_health_check()
        print(f"✅ API Status: {health_result['status']}")
        
        # Check LLM service specifically
        llm_check = health_result['checks']['llm_service']
        print(f"🧠 LLM Service: {llm_check['status']}")
        print(f"⏱️  Response time: {llm_check['response_time_ms']}ms")
        
        if llm_check['status'] != 'healthy':
            print(f"⚠️  LLM Service issue: {llm_check.get('error', 'Unknown error')}")
        
        # 2. Test topic extraction with LLM
        print("\n2. 🏷️ Testing topic extraction with LLM...")
        
        sample_content = """
        I'm a senior software engineer specializing in Python web development and machine learning.
        I have extensive experience with FastAPI, Django, and Flask for building REST APIs and web applications.
        My ML expertise includes scikit-learn, TensorFlow, and PyTorch for building predictive models.
        I also work with cloud platforms like AWS and Azure, containerization with Docker and Kubernetes,
        and database technologies including PostgreSQL, MongoDB, and Redis.
        I'm passionate about clean code, test-driven development, and mentoring junior developers.
        """
        
        result = extract_topics_with_llm(sample_content)
        if result['success']:
            topics = result['data']['topics']
            print(f"✅ LLM extracted {len(topics)} topics:")
            for i, topic in enumerate(topics, 1):
                print(f"   {i}. {topic}")
        else:
            print(f"❌ Topic extraction failed: {result['message']}")
        
        # 3. Test subreddit discovery with LLM
        print("\n3. 🔍 Testing subreddit discovery with LLM...")
        
        result = discover_subreddits_with_llm(sample_content)
        if result['success']:
            subreddits = result['data'].get('relevant_subreddits', {})
            print(f"✅ LLM discovered {len(subreddits)} relevant subreddits:")
            
            for name, info in list(subreddits.items())[:5]:
                subscribers = info.get('subscribers', 0)
                description = info.get('about', '')[:80]
                print(f"   📍 r/{name}")
                print(f"      👥 {subscribers:,} subscribers")
                print(f"      📄 {description}...")
                print()
        else:
            print(f"❌ Subreddit discovery failed: {result['message']}")
        
        # 4. Test semantic document search
        print("\n4. 📚 Testing semantic document search...")
        
        # First, let's try to ingest a sample document
        print("   📝 Note: This requires documents to be ingested first")
        print("   Run document_management.py example to ingest sample documents")
        
        search_queries = [
            "Python web development frameworks",
            "machine learning algorithms and libraries",
            "cloud deployment and containerization"
        ]
        
        for query in search_queries:
            print(f"\n   🔎 Searching: '{query}'")
            try:
                result = query_documents_with_llm(query)
                
                if result['total_results'] > 0:
                    print(f"   ✅ Found {result['total_results']} results in {result['processing_time_ms']:.2f}ms")
                    
                    for i, doc in enumerate(result['documents'][:2], 1):
                        print(f"      {i}. {doc['title']} (score: {doc['score']:.3f})")
                        print(f"         {doc['content'][:80]}...")
                else:
                    print(f"   ℹ️  No documents found (ingest documents first)")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  Search failed: {e}")
        
        # 5. Test LLM error handling
        print("\n5. 🛠️ Testing LLM error handling...")
        
        # Test with very long content to potentially trigger limits
        very_long_content = "This is a test. " * 10000  # Very long content
        
        try:
            result = extract_topics_with_llm(very_long_content)
            if result['success']:
                print("✅ LLM handled long content successfully")
            else:
                print(f"⚠️  LLM returned error (expected): {result['message']}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API error with long content (expected): {e}")
        
        # Test with empty content
        try:
            result = extract_topics_with_llm("")
            if result['success']:
                print("✅ LLM handled empty content")
            else:
                print(f"⚠️  LLM returned error for empty content: {result['message']}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API error with empty content: {e}")
        
        print("\n✅ LLM integration examples completed!")
        
        print("\n💡 LLM Integration Tips:")
        print("   1. The system uses multiple LLM providers (OpenAI, Google, Groq)")
        print("   2. Semantic search provides more relevant results than keyword search")
        print("   3. Topic extraction helps find relevant communities automatically")
        print("   4. Always handle LLM errors gracefully in production")
        print("   5. Monitor LLM usage and costs through the health endpoints")
        
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