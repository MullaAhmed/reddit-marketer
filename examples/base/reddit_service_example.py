"""
Example: Reddit Service using Base Classes

This example demonstrates how to use the RedditService directly
without going through the API layer.
"""

import asyncio
import traceback
import os
from dotenv import load_dotenv

from app.services.reddit_service import RedditService

load_dotenv(dotenv_path=".env",override=True)

# Mock Reddit credentials for demonstration
MOCK_REDDIT_CREDENTIALS = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "username": os.getenv("REDDIT_USERNAME"),
    "password": os.getenv("REDDIT_PASSWORD")
}

async def main():
    """Run Reddit service examples."""
    print("🚀 Reddit Service Base Class Examples")
    print("=" * 50)
    
    # Initialize the Reddit service
    reddit_service = RedditService(data_dir="examples_data")
    
    try:
        # 1. Extract topics from content
        print("\n1. 🏷️ Extracting topics from content...")
        
        sample_content = """
        I'm a Python developer specializing in web development with FastAPI and Django.
        I build REST APIs, microservices, and full-stack applications. My expertise includes
        database design with PostgreSQL, cloud deployment on AWS, containerization with Docker,
        and machine learning with scikit-learn and TensorFlow. I enjoy mentoring developers
        and contributing to open-source projects.
        """
        
        org_id = "reddit-example-org"
        
        success, message, topics = await reddit_service.extract_topics_from_content(
            content=sample_content,
            organization_id=org_id
        )
        
        if success:
            print(f"✅ {message}")
            print(f"📊 Extracted topics: {topics}")
        else:
            print(f"❌ Topic extraction failed: {message}")
        
        # 2. Discover subreddits
        print("\n2. 🔍 Discovering relevant subreddits...")
        
        success, message, discovery_data = await reddit_service.discover_subreddits(
            content=sample_content,
            organization_id=org_id,
            min_subscribers=5000
        )
        
        if success:
            print(f"✅ {message}")
            
            relevant_subreddits = discovery_data.get('relevant_subreddits', {})
            print(f"📊 Found {len(relevant_subreddits)} relevant subreddits:")
            
            for name, info in list(relevant_subreddits.items())[:5]:
                subscribers = info.get('subscribers', 0)
                description = info.get('about', '')[:80]
                print(f"   📍 r/{name}")
                print(f"      👥 {subscribers:,} subscribers")
                print(f"      📄 {description}...")
                print()
        else:
            print(f"❌ Subreddit discovery failed: {message}")
        
        # 3. Discover posts (will fail with mock credentials, but shows the structure)
        print("\n3. 📝 Discovering posts in subreddits...")
        print("⚠️  Note: This will fail with mock credentials, but demonstrates the API")
        
        target_subreddits = ["python", "learnpython", "webdev"]
        topics_for_search = topics[:3] if topics else ["python", "web development"]
        
        try:
            success, message, posts = await reddit_service.discover_posts(
                subreddits=target_subreddits,
                topics=topics_for_search,
                reddit_credentials=MOCK_REDDIT_CREDENTIALS,
                max_posts_per_subreddit=5,
                time_filter="day"
            )
            
            if success:
                print(f"✅ {message}")
                print(f"📊 Found {len(posts)} posts")
                
                for i, post in enumerate(posts[:3], 1):
                    print(f"   {i}. {post.get('title', 'No title')}")
                    print(f"      📍 r/{post.get('search_subreddit', 'unknown')}")
                    print(f"      👤 {post.get('author', {}).get('name', 'unknown')}")
                    print()
            else:
                print(f"⚠️  Post discovery failed (expected): {message}")
                
        except Exception as e:
            print(f"⚠️  Post discovery error (expected with mock credentials): {e}")
        
        # 4. Analyze post relevance
        print("\n4. 🎯 Analyzing post relevance...")
        
        # Mock post for demonstration
        mock_post = {
            "id": "mock123",
            "title": "Need help with FastAPI authentication",
            "selftext": "I'm building a REST API with FastAPI and need help implementing JWT authentication. Any recommendations for libraries or best practices?",
            "search_subreddit": "python",
            "author": {"name": "pythonlearner123"},
            "score": 15,
            "num_comments": 8
        }
        
        campaign_context = sample_content  # Using our sample content as campaign context
        
        success, message, analysis = await reddit_service.analyze_post_relevance(
            post=mock_post,
            campaign_context=campaign_context,
            organization_id=org_id
        )
        
        if success:
            print(f"✅ Post relevance analysis completed")
            print(f"📊 Relevance score: {analysis.get('relevance_score', 0):.2f}")
            print(f"📝 Reason: {analysis.get('relevance_reason', 'No reason provided')}")
            print(f"💬 Should respond: {analysis.get('should_respond', False)}")
        else:
            print(f"❌ Post relevance analysis failed: {message}")
        
        # 5. Generate response
        print("\n5. 💬 Generating response for post...")
        
        success, message, response_data = await reddit_service.generate_response(
            post=mock_post,
            campaign_context=campaign_context,
            tone="helpful",
            organization_id=org_id
        )
        
        if success:
            print(f"✅ Response generation completed")
            print(f"⭐ Confidence: {response_data.get('confidence', 0):.2f}")
            print(f"📝 Generated response:")
            print(f"   {response_data.get('content', 'No content generated')}")
        else:
            print(f"❌ Response generation failed: {message}")
        
        # 6. Post response (will fail with mock credentials)
        print("\n6. 🚀 Posting response to Reddit...")
        print("⚠️  Note: This will fail with mock credentials")
        
        if 'content' in response_data:
            try:
                success, message, result = await reddit_service.post_response(
                    post_id=mock_post['id'],
                    response_content=response_data['content'],
                    reddit_credentials=MOCK_REDDIT_CREDENTIALS,
                    response_type="post_comment"
                )
                
                if success:
                    print(f"✅ Response posted successfully")
                    print(f"📝 Comment ID: {result.get('id', 'unknown')}")
                    print(f"🔗 Permalink: {result.get('permalink', 'unknown')}")
                else:
                    print(f"⚠️  Response posting failed (expected): {message}")
                    
            except Exception as e:
                print(f"⚠️  Response posting error (expected with mock credentials): {e}")
        
        print("\n✅ Reddit service examples completed!")
        
        print("\n💡 Tips for real usage:")
        print("   1. Replace mock credentials with real Reddit API credentials")
        print("   2. Ensure you have proper Reddit app registration")
        print("   3. Always review generated responses before posting")
        print("   4. Respect Reddit's rate limits and community guidelines")
        print("   5. Test with read-only operations first")
        
    except Exception as e:
        print(f"❌ Error in Reddit service example: {e}")
        traceback.print_exc()
    
    finally:
        # Clean up resources
        await reddit_service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())