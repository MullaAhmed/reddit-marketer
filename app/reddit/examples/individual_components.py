"""
Examples for running each Reddit marketing component individually.
These examples show how to use each silo independently for testing and development.
"""

import asyncio
import json
import os
from typing import Dict, List, Any

# Individual component imports
from reddit.agents.ingestion_agent import IngestionAgent
from reddit.core.subreddit_finder import SubredditFinder
from reddit.core.reddit_post_finder import RedditPostFinder
from reddit.core.reddit_interactor import RedditInteractor
from rag.ingestion import DocumentIngestion
from rag.retrieval import DocumentRetrieval
from rag.models import DocumentQuery
from services.llm.llm_service import ai_client


# ========================================
# 1. DOCUMENT INGESTION EXAMPLE
# ========================================

async def example_document_ingestion():
    """
    Example: Upload and ingest documents into the RAG system.
    This is typically the first step - getting your content into the system.
    """
    print("🔄 Document Ingestion Example")
    print("=" * 40)
    
    # Sample documents to ingest
    documents = [
        {
            "title": "Python Best Practices Guide",
            "content": """
            This comprehensive guide covers Python best practices including:
            - Code organization and structure
            - Error handling and logging
            - Testing strategies with pytest
            - Performance optimization techniques
            - Security considerations
            - Documentation standards
            
            We recommend using virtual environments, following PEP 8 style guidelines,
            and implementing comprehensive test coverage for all production code.
            """,
            "metadata": {
                "category": "programming",
                "language": "python",
                "difficulty": "intermediate"
            }
        },
        {
            "title": "Machine Learning Fundamentals",
            "content": """
            Machine learning is a subset of artificial intelligence that enables
            computers to learn and improve from experience without being explicitly
            programmed. Key concepts include:
            
            - Supervised learning (classification, regression)
            - Unsupervised learning (clustering, dimensionality reduction)
            - Deep learning and neural networks
            - Model evaluation and validation
            - Feature engineering and selection
            
            Popular libraries include scikit-learn, TensorFlow, and PyTorch.
            """,
            "metadata": {
                "category": "machine-learning",
                "difficulty": "beginner"
            }
        }
    ]
    
    # Initialize ingestion service
    ingestion_service = DocumentIngestion(data_dir="data")
    
    # Ingest documents
    org_id = "example-org-1"
    org_name = "Example Tech Company"
    
    success, message, doc_ids = ingestion_service.ingest_documents(
        documents, org_id, org_name
    )
    
    print(f"✅ Ingestion Result: {success}")
    print(f"📝 Message: {message}")
    print(f"📄 Document IDs: {doc_ids}")
    print(f"📊 Documents ingested: {len(doc_ids)}")
    
    return org_id, doc_ids


# ========================================
# 2. DOCUMENT RETRIEVAL EXAMPLE
# ========================================

async def example_document_retrieval(org_id: str):
    """
    Example: Query and retrieve documents from the RAG system.
    """
    print("\n🔍 Document Retrieval Example")
    print("=" * 40)
    
    # Initialize retrieval service
    retrieval_service = DocumentRetrieval(data_dir="data")
    
    # Example queries
    queries = [
        "Python best practices and coding standards",
        "Machine learning algorithms and techniques",
        "Testing strategies for Python applications"
    ]
    
    for query_text in queries:
        print(f"\n🔎 Query: '{query_text}'")
        
        # Create query
        query = DocumentQuery(
            query=query_text,
            organization_id=org_id,
            method="semantic",
            top_k=3
        )
        
        # Execute query
        results = retrieval_service.query_documents(query)
        
        print(f"📊 Found {results.total_results} results in {results.processing_time_ms:.2f}ms")
        
        # Display top results
        for i, doc in enumerate(results.documents[:2], 1):
            print(f"  {i}. {doc.title} (Score: {doc.score:.3f})")
            print(f"     Content: {doc.content[:100]}...")


# ========================================
# 3. SUBREDDIT DISCOVERY EXAMPLE
# ========================================

async def example_subreddit_discovery():
    """
    Example: Find relevant subreddits based on content analysis.
    """
    print("\n🎯 Subreddit Discovery Example")
    print("=" * 40)
    
    # Sample content for analysis
    content = """
    I'm a Python developer with 5 years of experience building web applications
    and data analysis tools. I specialize in Django, Flask, pandas, and scikit-learn.
    I'm passionate about machine learning, data visualization, and helping other
    developers learn best practices. I also enjoy contributing to open source
    projects and writing technical tutorials.
    """
    
    # Initialize subreddit finder
    finder = SubredditFinder(min_subscribers=10000)
    
    # Find relevant subreddits
    results = await finder.find_relevant_subreddits(content)
    
    print(f"📊 Topics found: {len(results['topics'])}")
    print("🏷️  Topics:", ", ".join(results['topics'][:5]))
    
    print(f"\n🎯 Relevant subreddits: {len(results['relevant_subreddits'])}")
    for name, data in list(results['relevant_subreddits'].items())[:5]:
        print(f"  • r/{name} - {data['subscribers']:,} subscribers")
        print(f"    {data['about'][:80]}...")
    
    return results['relevant_subreddits']


# ========================================
# 4. POST DISCOVERY EXAMPLE
# ========================================

async def example_post_discovery(subreddits: Dict[str, Any]):
    """
    Example: Find relevant posts in target subreddits.
    """
    print("\n📋 Post Discovery Example")
    print("=" * 40)
    
    # Reddit credentials (replace with your actual credentials)
    reddit_credentials = {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "username": "YOUR_USERNAME",  # Optional for read-only
        "password": "YOUR_PASSWORD"   # Optional for read-only
    }
    
    # Initialize post finder
    post_finder = RedditPostFinder(
        client_id=reddit_credentials["client_id"],
        client_secret=reddit_credentials["client_secret"]
    )
    
    try:
        # Search topics
        search_topics = ["python programming", "machine learning", "data science"]
        target_subreddits = list(subreddits.keys())[:3]  # Use top 3 subreddits
        
        all_posts = []
        
        for subreddit in target_subreddits:
            print(f"\n🔍 Searching r/{subreddit}")
            
            for topic in search_topics[:2]:  # Limit to 2 topics per subreddit
                try:
                    posts = await post_finder.search_subreddit_posts(
                        subreddit=subreddit,
                        query=topic,
                        sort="new",
                        time_filter="day",
                        limit=5
                    )
                    
                    print(f"  📄 Found {len(posts)} posts for '{topic}'")
                    all_posts.extend(posts)
                    
                    # Display sample posts
                    for post in posts[:2]:
                        print(f"    • {post['title'][:60]}...")
                        print(f"      Score: {post['score']}, Comments: {post['num_comments']}")
                
                except Exception as e:
                    print(f"    ❌ Error searching '{topic}': {str(e)}")
        
        print(f"\n📊 Total posts found: {len(all_posts)}")
        return all_posts
        
    finally:
        await post_finder.close()


# ========================================
# 5. RESPONSE GENERATION EXAMPLE
# ========================================

async def example_response_generation(posts: List[Dict], context: str):
    """
    Example: Generate responses for target posts using AI.
    """
    print("\n💬 Response Generation Example")
    print("=" * 40)
    
    # Select a few posts for response generation
    target_posts = posts[:3] if posts else []
    
    for i, post in enumerate(target_posts, 1):
        print(f"\n📝 Generating response {i}/3")
        print(f"Post: {post['title'][:50]}...")
        
        # Generate response using AI
        messages = [
            {
                "role": "system",
                "content": """You are a helpful Reddit user with expertise in Python and machine learning. 
                Generate a natural, helpful response that adds value to the conversation. 
                Be helpful but not overly promotional."""
            },
            {
                "role": "user",
                "content": f"""
                My expertise: {context[:500]}
                
                Post Title: {post['title']}
                Post Content: {post.get('selftext', 'No content')}
                
                Generate a helpful response that:
                1. Adds value to the conversation
                2. Is natural and conversational
                3. Shows expertise without being promotional
                4. Is 1-2 paragraphs long
                
                Return JSON with:
                - content: the response text
                - confidence: 0.0-1.0 confidence score
                """
            }
        ]
        
        try:
            response = await ai_client.generate_chat_completion_gemini(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            result = response["choices"][0]["message"]["content"]
            
            print(f"✅ Generated response (Confidence: {result['confidence']:.2f})")
            print(f"📄 Content: {result['content'][:150]}...")
            
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")


# ========================================
# 6. REDDIT INTERACTION EXAMPLE
# ========================================

async def example_reddit_interaction():
    """
    Example: Interact with Reddit (read-only operations for safety).
    """
    print("\n🤖 Reddit Interaction Example")
    print("=" * 40)
    
    # Reddit credentials
    reddit_credentials = {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD"
    }
    
    # Initialize Reddit interactor
    interactor = RedditInteractor(
        client_id=reddit_credentials["client_id"],
        client_secret=reddit_credentials["client_secret"],
        username=reddit_credentials.get("username"),
        password=reddit_credentials.get("password")
    )
    
    try:
        # Example: Get comments from a popular post (read-only)
        # Replace with an actual Reddit post URL
        sample_post_url = "https://www.reddit.com/r/python/comments/sample_post/"
        
        print("📖 Reading post comments (read-only operation)")
        print("⚠️  Using sample URL - replace with actual post for testing")
        
        # Note: This would fail with the sample URL, but shows the structure
        try:
            post_data = await interactor.get_post_comments(
                sample_post_url,
                sort="top",
                limit=5
            )
            
            print(f"✅ Post: {post_data['title']}")
            print(f"📊 Comments: {len(post_data['comments'])}")
            
        except Exception as e:
            print(f"ℹ️  Expected error with sample URL: {str(e)}")
        
        # Example: Demonstrate posting (commented out for safety)
        print("\n⚠️  Posting operations are commented out for safety")
        print("   Uncomment and provide valid credentials to test posting")
        
        """
        # UNCOMMENT TO TEST ACTUAL POSTING (BE CAREFUL!)
        
        # Add comment to post
        comment_result = await interactor.add_comment_to_post(
            post_url,
            "This is a helpful comment generated by the Reddit marketing agent!"
        )
        print(f"✅ Posted comment: {comment_result['id']}")
        
        # Reply to a comment
        reply_result = await interactor.reply_to_comment(
            comment_id,
            "Thank you for the feedback! Here's additional information..."
        )
        print(f"✅ Posted reply: {reply_result['id']}")
        """
        
    finally:
        await interactor.close()


# ========================================
# 7. INGESTION AGENT EXAMPLE
# ========================================

async def example_ingestion_agent():
    """
    Example: Use the ingestion agent to analyze content and find subreddits.
    """
    print("\n🔄 Ingestion Agent Example")
    print("=" * 40)
    
    # Sample content
    content = """
    Our company specializes in developing AI-powered web applications using Python,
    Django, and React. We have expertise in natural language processing, computer vision,
    and recommendation systems. We're particularly experienced with TensorFlow, PyTorch,
    and scikit-learn. We also provide consulting services for startups looking to
    integrate machine learning into their products.
    """
    
    # Initialize ingestion agent
    agent = IngestionAgent(min_subscribers=5000)
    
    # Process content
    org_id = "example-org-2"
    results = await agent.process_content(content, org_id)
    
    print(f"✅ Processing successful: {results['success']}")
    print(f"📊 Topics found: {results['topics_found']}")
    print(f"🎯 Relevant subreddits: {results['relevant_subreddits_found']}")
    
    print(f"\n🏷️  Top topics:")
    for topic in results['topics'][:5]:
        print(f"  • {topic}")
    
    print(f"\n🎯 Top subreddits:")
    for subreddit in results['top_subreddits'][:5]:
        print(f"  • r/{subreddit}")
    
    return results


# ========================================
# MAIN EXECUTION
# ========================================

async def run_all_individual_examples():
    """
    Run all individual component examples in sequence.
    """
    print("🚀 Running All Individual Component Examples")
    print("=" * 60)
    
    try:
        # 1. Document Ingestion
        org_id, doc_ids = await example_document_ingestion()
        
        # 2. Document Retrieval
        await example_document_retrieval(org_id)
        
        # 3. Subreddit Discovery
        subreddits = await example_subreddit_discovery()
        
        # 4. Post Discovery
        posts = await example_post_discovery(subreddits)
        
        # 5. Response Generation
        context = "Expert Python developer with ML experience"
        await example_response_generation(posts, context)
        
        # 6. Reddit Interaction
        await example_reddit_interaction()
        
        # 7. Ingestion Agent
        await example_ingestion_agent()
        
        print("\n🎉 All individual examples completed!")
        
    except Exception as e:
        print(f"\n❌ Error in examples: {str(e)}")


async def run_single_example(example_name: str):
    """
    Run a single example by name.
    """
    examples = {
        "ingestion": example_document_ingestion,
        "retrieval": lambda: example_document_retrieval("example-org-1"),
        "subreddits": example_subreddit_discovery,
        "posts": lambda: example_post_discovery({"python": {"subscribers": 50000}}),
        "responses": lambda: example_response_generation([], "Python expert"),
        "reddit": example_reddit_interaction,
        "agent": example_ingestion_agent
    }
    
    if example_name in examples:
        print(f"🚀 Running {example_name} example")
        await examples[example_name]()
    else:
        print(f"❌ Unknown example: {example_name}")
        print(f"Available examples: {', '.join(examples.keys())}")


if __name__ == "__main__":
    print("Reddit Marketing Individual Component Examples")
    print("=" * 50)
    print("Choose an example to run:")
    print("1. All examples")
    print("2. Document ingestion")
    print("3. Document retrieval") 
    print("4. Subreddit discovery")
    print("5. Post discovery")
    print("6. Response generation")
    print("7. Reddit interaction")
    print("8. Ingestion agent")
    
    choice = input("\nEnter choice (1-8): ").strip()
    
    example_map = {
        "1": "all",
        "2": "ingestion",
        "3": "retrieval",
        "4": "subreddits", 
        "5": "posts",
        "6": "responses",
        "7": "reddit",
        "8": "agent"
    }
    
    if choice in example_map:
        if choice == "1":
            asyncio.run(run_all_individual_examples())
        else:
            asyncio.run(run_single_example(example_map[choice]))
    else:
        print("Invalid choice. Please run the script again.")