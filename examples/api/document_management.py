"""
Example: Document Management using REST API

This example demonstrates how to:
1. Ingest documents into the system
2. Query documents using semantic search
3. Get organization document statistics
"""

import requests
import json
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ORGANIZATION_ID = "example-org"

def ingest_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ingest documents via API."""
    url = f"{API_BASE_URL}/documents/ingest"
    params = {"organization_id": ORGANIZATION_ID}
    
    response = requests.post(url, params=params, json=documents)
    response.raise_for_status()
    return response.json()

def query_documents(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Query documents via API."""
    url = f"{API_BASE_URL}/documents/query"
    
    payload = {
        "query": query,
        "organization_id": ORGANIZATION_ID,
        "method": "semantic",
        "top_k": top_k
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def get_organization_documents() -> Dict[str, Any]:
    """Get all documents for organization."""
    url = f"{API_BASE_URL}/documents/organizations/{ORGANIZATION_ID}"
    
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def upload_document_file(file_path: str, title: str = None) -> Dict[str, Any]:
    """Upload a document file."""
    url = f"{API_BASE_URL}/documents/upload"
    params = {"organization_id": ORGANIZATION_ID}
    
    if title:
        params["title"] = title
    
    with open(file_path, 'rb') as f:
        files = {"file": f}
        response = requests.post(url, params=params, files=files)
    
    response.raise_for_status()
    return response.json()

def main():
    """Run document management examples."""
    print("🚀 Document Management API Examples")
    print("=" * 50)
    
    # Example documents
    sample_documents = [
        {
            "title": "Python Programming Guide",
            "content": """
            Python is a high-level programming language known for its simplicity and readability.
            It's widely used in web development, data science, artificial intelligence, and automation.
            Key features include dynamic typing, automatic memory management, and extensive libraries.
            Popular frameworks include Django for web development and pandas for data analysis.
            """,
            "metadata": {
                "category": "programming",
                "language": "python",
                "difficulty": "beginner"
            }
        },
        {
            "title": "Machine Learning Basics",
            "content": """
            Machine learning is a subset of artificial intelligence that enables computers to learn
            and make decisions from data without explicit programming. Common algorithms include
            linear regression, decision trees, and neural networks. Popular libraries include
            scikit-learn, TensorFlow, and PyTorch for implementing ML models.
            """,
            "metadata": {
                "category": "ai",
                "topic": "machine-learning",
                "difficulty": "intermediate"
            }
        },
        {
            "title": "Web Development with FastAPI",
            "content": """
            FastAPI is a modern, fast web framework for building APIs with Python. It provides
            automatic API documentation, data validation, and async support. Key features include
            type hints, dependency injection, and OpenAPI integration. It's ideal for building
            high-performance REST APIs and microservices.
            """,
            "metadata": {
                "category": "web-development",
                "framework": "fastapi",
                "difficulty": "intermediate"
            }
        }
    ]
    
    try:
        # 1. Ingest documents
        print("\n1. 📄 Ingesting sample documents...")
        result = ingest_documents(sample_documents)
        print(f"✅ Success: {result['message']}")
        print(f"📊 Documents ingested: {result['data']['documents_ingested']}")
        
        # 2. Query documents
        print("\n2. 🔍 Querying documents...")
        queries = [
            "Python programming tutorials",
            "machine learning algorithms",
            "web API development"
        ]
        
        for query in queries:
            print(f"\n🔎 Query: '{query}'")
            result = query_documents(query, top_k=3)
            
            print(f"📈 Found {result['total_results']} results in {result['processing_time_ms']:.2f}ms")
            
            for i, doc in enumerate(result['documents'][:2], 1):
                print(f"  {i}. {doc['title']} (score: {doc['score']:.3f})")
                print(f"     Content: {doc['content'][:100]}...")
        
        # 3. Get organization documents
        print("\n3. 📋 Getting organization documents...")
        result = get_organization_documents()
        
        if result['success']:
            org_data = result['data']['organization']
            print(f"✅ Organization: {org_data['name']}")
            print(f"📊 Total documents: {org_data['documents_count']}")
            
            print("\n📚 Documents:")
            for doc in result['data']['documents'][:3]:
                print(f"  • {doc['title']} ({doc['chunk_count']} chunks)")
        
        print("\n✅ Document management examples completed successfully!")
        
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