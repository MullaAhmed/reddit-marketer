"""
Example: LLM Service using Base Classes

This example demonstrates how to use the LLMService directly
without going through the API layer.
"""

import asyncio
import traceback
   

from app.services.llm_service import LLMService

async def main():
    """Run LLM service examples."""
    print("🚀 LLM Service Base Class Examples")
    print("=" * 50)
    
    # Initialize the LLM service
    llm_service = LLMService()
    
    try:
        # 1. Basic text completion
        print("\n1. 📝 Basic text completion...")
        
        prompt = """
        Explain the benefits of using FastAPI for building REST APIs in Python.
        Focus on performance, ease of use, and developer experience.
        """
        
        result = await llm_service.generate_completion(
            prompt=prompt,
            response_format="text",
            temperature=0.7
        )
        
        if 'content' in result:
            print("✅ Text completion successful")
            print(f"📝 Response: {result['content'][:300]}...")
        else:
            print(f"❌ Text completion failed: {result.get('error', 'Unknown error')}")
        
        # 2. JSON structured response
        print("\n2. 🔧 JSON structured response...")
        
        json_prompt = """
        Analyze the following Python code and return a JSON object with:
        - complexity_score (1-10)
        - readability_score (1-10)
        - suggestions (array of improvement suggestions)
        - technologies_used (array of technologies/libraries identified)
        
        Code:
        ```python
        def process_data(data):
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
            return result
        ```
        """
        
        result = await llm_service.generate_completion(
            prompt=json_prompt,
            response_format="json",
            temperature=0.3
        )
        
        if 'complexity_score' in result:
            print("✅ JSON response successful")
            print(f"🔍 Complexity score: {result.get('complexity_score', 'N/A')}")
            print(f"📖 Readability score: {result.get('readability_score', 'N/A')}")
            print(f"💡 Suggestions: {result.get('suggestions', [])}")
            print(f"🛠️ Technologies: {result.get('technologies_used', [])}")
        else:
            print(f"❌ JSON response failed: {result.get('error', 'Unknown error')}")
        
        # 3. Chat completion with multiple messages
        print("\n3. 💬 Chat completion with conversation...")
        
        messages = [
            {"role": "system", "content": "You are a helpful Python programming assistant."},
            {"role": "user", "content": "What's the difference between FastAPI and Flask?"},
            {"role": "assistant", "content": "FastAPI is a modern, fast web framework with automatic API documentation and type hints, while Flask is a lightweight, flexible framework that's been around longer."},
            {"role": "user", "content": "Which one should I choose for a new REST API project?"}
        ]
        
        result = await llm_service.generate_chat_completion(
            messages=messages,
            temperature=0.6,
            provider="gemini"
        )
        
        if 'choices' in result:
            print("✅ Chat completion successful")
            response_content = result['choices'][0]['message']['content']
            print(f"🤖 Assistant: {response_content[:300]}...")
            
            # Show usage metadata
            if 'usage_metadata' in result:
                usage = result['usage_metadata']
                print(f"📊 Token usage: {usage.get('input_tokens', 0)} input, {usage.get('output_tokens', 0)} output")
        else:
            print(f"❌ Chat completion failed: {result.get('error', 'Unknown error')}")
        
        # 4. Topic extraction
        print("\n4. 🏷️ Topic extraction...")
        
        content = """
        I'm a senior software engineer with 8 years of experience in Python development.
        I specialize in building scalable web applications using Django and FastAPI.
        My expertise includes database optimization with PostgreSQL, cloud deployment on AWS,
        containerization with Docker, and implementing CI/CD pipelines. I also have experience
        with machine learning using scikit-learn and TensorFlow for predictive analytics.
        I'm passionate about clean code, test-driven development, and mentoring junior developers.
        """
        
        topics = await llm_service.extract_topics(content)
        
        if topics:
            print("✅ Topic extraction successful")
            print(f"📊 Extracted {len(topics)} topics:")
            for i, topic in enumerate(topics, 1):
                print(f"   {i}. {topic}")
        else:
            print("❌ Topic extraction failed")
        
        # 5. Subreddit ranking
        print("\n5. 🎯 Subreddit ranking...")
        
        subreddits = {
            "python": {"about": "News about the dynamic, interpreted, interactive, object-oriented, extensible programming language Python"},
            "learnpython": {"about": "Subreddit for posting questions and asking for general advice about your Python code"},
            "django": {"about": "News and discussion about Django, the Python web framework"},
            "MachineLearning": {"about": "A subreddit dedicated to learning machine learning"},
            "webdev": {"about": "A community dedicated to all things web development"},
            "programming": {"about": "Computer Programming"}
        }
        
        ranked_subreddits = await llm_service.rank_subreddits(content, subreddits)
        
        if ranked_subreddits:
            print("✅ Subreddit ranking successful")
            print(f"📊 Top ranked subreddits:")
            for i, subreddit in enumerate(ranked_subreddits[:5], 1):
                print(f"   {i}. r/{subreddit}")
        else:
            print("❌ Subreddit ranking failed")
        
        # 6. Post relevance analysis
        print("\n6. 🎯 Post relevance analysis...")
        
        post_title = "Need help with FastAPI authentication implementation"
        post_content = """
        I'm building a REST API with FastAPI and struggling with implementing JWT authentication.
        I need to protect certain endpoints and validate tokens. Any recommendations for
        libraries or best practices? I'm also wondering about refresh token implementation.
        """
        
        campaign_context = content  # Using our sample content as campaign context
        
        analysis = await llm_service.analyze_post_relevance(
            post_title=post_title,
            post_content=post_content,
            campaign_context=campaign_context
        )
        
        if 'relevance_score' in analysis:
            print("✅ Post relevance analysis successful")
            print(f"📊 Relevance score: {analysis.get('relevance_score', 0):.2f}")
            print(f"📝 Reason: {analysis.get('relevance_reason', 'No reason provided')}")
            print(f"💬 Should respond: {analysis.get('should_respond', False)}")
        else:
            print(f"❌ Post relevance analysis failed: {analysis.get('error', 'Unknown error')}")
        
        # 7. Reddit response generation
        print("\n7. 💬 Reddit response generation...")
        
        response_result = await llm_service.generate_reddit_response(
            post_title=post_title,
            post_content=post_content,
            campaign_context=campaign_context,
            tone="helpful"
        )
        
        if 'content' in response_result:
            print("✅ Reddit response generation successful")
            print(f"⭐ Confidence: {response_result.get('confidence', 0):.2f}")
            print(f"📝 Generated response:")
            print(f"   {response_result['content'][:400]}...")
        else:
            print(f"❌ Reddit response generation failed: {response_result.get('error', 'Unknown error')}")
        
        # 8. Test different providers
        print("\n8. 🔄 Testing different LLM providers...")
        
        simple_prompt = "Explain Python list comprehensions in one sentence."
        providers = ["gemini", "openai", "groq"]
        
        for provider in providers:
            print(f"\n🧠 Testing {provider.upper()}...")
            
            try:
                messages = [{"role": "user", "content": simple_prompt}]
                
                result = await llm_service.generate_chat_completion(
                    messages=messages,
                    provider=provider,
                    temperature=0.5
                )
                
                if 'choices' in result:
                    response_content = result['choices'][0]['message']['content']
                    print(f"✅ {provider.upper()}: {response_content[:150]}...")
                    
                    if 'usage_metadata' in result:
                        usage = result['usage_metadata']
                        print(f"   📊 Tokens: {usage.get('total_tokens', 0)} total")
                else:
                    print(f"❌ {provider.upper()} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"⚠️  {provider.upper()} error: {e}")
        
        print("\n✅ LLM service examples completed!")
        
        print("\n💡 LLM Service Features:")
        print("   1. ✅ Multiple provider support (OpenAI, Google, Groq)")
        print("   2. ✅ Text and JSON response formats")
        print("   3. ✅ Chat completion with conversation history")
        print("   4. ✅ Specialized functions for Reddit marketing")
        print("   5. ✅ Token usage tracking")
        print("   6. ✅ Error handling and fallbacks")
        
        print("\n🔧 Configuration tips:")
        print("   1. Set appropriate temperature for creativity vs consistency")
        print("   2. Use JSON format for structured data extraction")
        print("   3. Choose providers based on cost, speed, and quality needs")
        print("   4. Monitor token usage to control costs")
        print("   5. Implement proper error handling for production use")
        
    except Exception as e:
        print(f"❌ Error in LLM service example: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())