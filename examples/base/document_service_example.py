"""
Example: Document Service using Base Classes

This example demonstrates how to use the DocumentService directly
without going through the API layer.
"""

import asyncio
import traceback
  

from app.services.document_service import DocumentService
from app.models.document import DocumentQuery

async def main():
    """Run document service examples."""
    print("🚀 Document Service Base Class Examples")
    print("=" * 50)
    
    # Initialize the document service
    document_service = DocumentService(data_dir="examples_data")
    
    try:
        # 1. Create organization and ingest documents
        print("\n1. 📄 Ingesting documents...")
        
        sample_documents = [
            {
                "title": "Python FastAPI Tutorial",
                "content": """
                FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+
                based on standard Python type hints. It's designed to be easy to use and learn, fast to code,
                and production-ready. Key features include automatic API documentation, data validation,
                serialization, and async support. FastAPI is built on top of Starlette and Pydantic.
                """,
                "metadata": {
                    "category": "tutorial",
                    "framework": "fastapi",
                    "language": "python"
                }
            },
            {
                "title": "Machine Learning with scikit-learn",
                "content": """
                Scikit-learn is a powerful machine learning library for Python that provides simple and efficient
                tools for data mining and data analysis. It features various classification, regression and
                clustering algorithms including support vector machines, random forests, gradient boosting,
                k-means and DBSCAN. The library is built on NumPy, SciPy, and matplotlib.
                """,
                "metadata": {
                    "category": "tutorial",
                    "topic": "machine-learning",
                    "library": "scikit-learn"
                }
            },
            {
                "title": "Docker Containerization Guide",
                "content": """
                Docker is a platform that uses containerization to package applications and their dependencies
                into lightweight, portable containers. Containers ensure that applications run consistently
                across different environments. Key concepts include images, containers, Dockerfiles, and
                Docker Compose for multi-container applications. Docker is essential for modern DevOps practices.
                """,
                "metadata": {
                    "category": "devops",
                    "technology": "docker",
                    "topic": "containerization"
                }
            }
        ]
        
        org_id = "base-example-org"
        success, message, document_ids = document_service.ingest_documents(
            documents=sample_documents,
            org_id=org_id,
            org_name="Base Example Organization"
        )
        
        if success:
            print(f"✅ {message}")
            print(f"📊 Document IDs: {document_ids}")
        else:
            print(f"❌ Ingestion failed: {message}")
            return
        
        # 2. Query documents using semantic search
        print("\n2. 🔍 Querying documents with semantic search...")
        
        queries = [
            "web development frameworks",
            "machine learning algorithms",
            "containerization and deployment"
        ]
        
        for query_text in queries:
            print(f"\n🔎 Query: '{query_text}'")
            
            query = DocumentQuery(
                query=query_text,
                organization_id=org_id,
                method="semantic",
                top_k=3
            )
            
            result = document_service.query_documents(query)
            
            print(f"📈 Found {result.total_results} results in {result.processing_time_ms:.2f}ms")
            
            for i, doc in enumerate(result.documents, 1):
                print(f"   {i}. {doc.title} (score: {doc.score:.3f})")
                print(f"      Content: {doc.content[:100]}...")
                print(f"      Metadata: {doc.metadata}")
                print()
        
        # 3. Query documents using keyword search
        print("\n3. 🔎 Querying documents with keyword search...")
        
        keyword_query = DocumentQuery(
            query="Python FastAPI",
            organization_id=org_id,
            method="keyword",
            top_k=5
        )
        
        result = document_service.query_documents(keyword_query)
        
        print(f"📈 Keyword search found {result.total_results} results")
        for doc in result.documents:
            print(f"   • {doc.title} (score: {doc.score:.3f})")
        
        # 4. Get organization information
        print("\n4. 📋 Getting organization information...")
        
        organization = document_service.get_or_create_organization(org_id)
        
        print(f"✅ Organization: {organization.name}")
        print(f"📊 Total documents: {organization.documents_count}")
        print(f"📅 Created: {organization.created_at}")
        
        print("\n📚 Documents in organization:")
        for doc in organization.documents:
            print(f"   • {doc.title} ({doc.chunk_count} chunks)")
        
        # 5. Get campaign context
        print("\n5. 🎯 Getting campaign context...")
        
        campaign_context = await document_service.get_campaign_context(
            organization_id=org_id,
            document_ids=document_ids[:2]  # Use first 2 documents
        )
        
        print(f"✅ Campaign context generated ({len(campaign_context)} characters)")
        print(f"📝 Preview: {campaign_context[:200]}...")
        
        # 6. Get organization statistics
        print("\n6. 📊 Getting organization statistics...")
        
        stats = document_service.get_organization_stats(org_id)
        
        if 'error' not in stats:
            print(f"✅ Organization statistics:")
            print(f"   📄 Total documents: {stats['total_documents']}")
            print(f"   🧩 Total chunks: {stats['total_chunks']}")
            print(f"   📏 Total content length: {stats['total_content_length']:,} characters")
            print(f"   📊 Average chunks per document: {stats['average_chunks_per_document']:.1f}")
        else:
            print(f"❌ Error getting stats: {stats['error']}")
        
        print("\n✅ Document service examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in document service example: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())