"""
Example: Complete Workflow using Base Classes

This example demonstrates a complete end-to-end workflow using
the base service classes directly without the API layer.
"""


import asyncio
import time
import random
import os
from dotenv import load_dotenv

from app.services.campaign_service import CampaignService
from app.services.document_service import DocumentService
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService

from app.models.campaign import (
    CampaignCreateRequest, SubredditDiscoveryRequest, 
    PostDiscoveryRequest, ResponseGenerationRequest, 
    ResponseExecutionRequest, ResponseTone
)


load_dotenv(dotenv_path=".env",override=True)

# Mock Reddit credentials for demonstration
MOCK_REDDIT_CREDENTIALS = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "username": os.getenv("REDDIT_USERNAME"),
    "password": os.getenv("REDDIT_PASSWORD")
}

class CompleteWorkflowExample:
    """Complete workflow example using base service classes."""
    
    def __init__(self):
        self.data_dir = "examples_data"
        self.organization_id = "complete-workflow-base"
        
        # Initialize services
        self.document_service = DocumentService(self.data_dir)
        self.reddit_service = RedditService(self.data_dir)
        self.llm_service = LLMService()
        self.campaign_service = CampaignService(self.data_dir)
        
        # Workflow state
        self.document_ids = []
        self.campaign = None
        self.target_subreddits = []
        self.target_posts = []
        self.planned_responses = []
    
    async def step_1_setup_documents(self):
        """Step 1: Set up documents for the organization."""
        print("\n" + "="*70)
        print("📄 STEP 1: DOCUMENT SETUP")
        print("="*70)
        
        # Sample documents for a Python consulting business
        documents = [
            {
                "title": "Python Web Development Expertise",
                "content": """
                We are a team of senior Python developers with over 10 years of combined experience
                in building scalable web applications. Our expertise includes:
                
                - FastAPI and Django for REST API development
                - Database design and optimization with PostgreSQL and MongoDB
                - Cloud deployment on AWS, Azure, and Google Cloud Platform
                - Containerization with Docker and Kubernetes
                - Microservices architecture and API gateway implementation
                - Test-driven development and CI/CD pipeline setup
                
                We have successfully delivered projects for fintech, e-commerce, and SaaS companies.
                Our approach focuses on clean code, scalability, and maintainability.
                """,
                "metadata": {
                    "category": "expertise",
                    "technologies": ["Python", "FastAPI", "Django", "PostgreSQL", "AWS"],
                    "experience_years": 10
                }
            },
            {
                "title": "Machine Learning and AI Services",
                "content": """
                Our machine learning practice specializes in building production-ready AI solutions:
                
                - Predictive analytics using scikit-learn and XGBoost
                - Deep learning with TensorFlow and PyTorch
                - Natural language processing and sentiment analysis
                - Computer vision and image recognition systems
                - Recommendation engines and personalization algorithms
                - MLOps and model deployment pipelines
                
                We help businesses leverage their data to make better decisions and automate processes.
                Our solutions are designed for scalability and real-world performance.
                """,
                "metadata": {
                    "category": "ai-services",
                    "technologies": ["scikit-learn", "TensorFlow", "PyTorch", "MLOps"],
                    "specialties": ["NLP", "computer-vision", "recommendations"]
                }
            },
            {
                "title": "Python Training and Mentorship",
                "content": """
                We offer comprehensive Python training programs for developers and teams:
                
                - Python fundamentals and advanced concepts
                - Web development with modern frameworks
                - Data science and machine learning workflows
                - Best practices in software engineering
                - Code review and architecture guidance
                - One-on-one mentorship and career development
                
                Our training approach is hands-on and project-based. We believe in learning by doing
                and provide real-world examples and exercises. Our instructors are active practitioners
                who understand current industry challenges and trends.
                """,
                "metadata": {
                    "category": "training",
                    "topics": ["Python", "web-development", "data-science", "mentorship"],
                    "format": "hands-on"
                }
            }
        ]
        
        try:
            success, message, document_ids = self.document_service.ingest_documents(
                documents=documents,
                org_id=self.organization_id,
                org_name="Complete Workflow Base Example"
            )
            
            if success:
                self.document_ids = document_ids
                print(f"✅ Successfully ingested {len(documents)} documents")
                print(f"📊 Document IDs: {self.document_ids}")
                
                # Test document querying
                print("\n🔍 Testing document query...")
                from app.models.document import DocumentQuery
                
                query = DocumentQuery(
                    query="Python web development expertise",
                    organization_id=self.organization_id,
                    method="semantic",
                    top_k=3
                )
                
                result = self.document_service.query_documents(query)
                print(f"📈 Query test: Found {result.total_results} results in {result.processing_time_ms:.2f}ms")
                
                return True
            else:
                print(f"❌ Document ingestion failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error in document setup: {e}")
            return False
    
    async def step_2_create_campaign(self):
        """Step 2: Create a marketing campaign."""
        print("\n" + "="*70)
        print("🎯 STEP 2: CAMPAIGN CREATION")
        print("="*70)
        
        try:
            create_request = CampaignCreateRequest(
                name="Python Expertise Outreach 2024",
                description="Share Python expertise with developer communities and build relationships",
                response_tone=ResponseTone.HELPFUL,
                max_responses_per_day=8
            )
            
            success, message, campaign = await self.campaign_service.create_campaign(
                organization_id=self.organization_id,
                request=create_request
            )
            
            if success:
                self.campaign = campaign
                print(f"✅ Campaign created successfully")
                print(f"📋 Campaign ID: {campaign.id}")
                print(f"📝 Name: {campaign.name}")
                print(f"🎯 Tone: {campaign.response_tone}")
                print(f"📊 Status: {campaign.status}")
                print(f"📅 Created: {campaign.created_at}")
                return True
            else:
                print(f"❌ Campaign creation failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error in campaign creation: {e}")
            return False
    
    async def step_3_discover_subreddits(self):
        """Step 3: Discover relevant subreddits using AI."""
        print("\n" + "="*70)
        print("🔍 STEP 3: SUBREDDIT DISCOVERY")
        print("="*70)
        
        try:
            subreddit_request = SubredditDiscoveryRequest(
                document_ids=self.document_ids
            )
            
            success, message, discovery_data = await self.campaign_service.discover_subreddits(
                campaign_id=self.campaign.id,
                request=subreddit_request
            )
            
            if success:
                self.target_subreddits = discovery_data.get('subreddits', [])
                print(f"✅ Subreddit discovery completed")
                print(f"📊 Found {len(self.target_subreddits)} relevant subreddits:")
                
                for i, subreddit in enumerate(self.target_subreddits[:8], 1):
                    print(f"   {i}. r/{subreddit}")
                
                if len(self.target_subreddits) > 8:
                    print(f"   ... and {len(self.target_subreddits) - 8} more")
                
                # Get updated campaign
                _, _, updated_campaign = await self.campaign_service.get_campaign(self.campaign.id)
                self.campaign = updated_campaign
                print(f"📈 Campaign status updated to: {self.campaign.status}")
                
                return True
            else:
                print(f"❌ Subreddit discovery failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error in subreddit discovery: {e}")
            return False
    
    async def step_4_discover_posts(self):
        """Step 4: Discover relevant posts in target subreddits."""
        print("\n" + "="*70)
        print("📝 STEP 4: POST DISCOVERY")
        print("="*70)
        
        try:
            # Use a subset of discovered subreddits for demonstration
            demo_subreddits = self.target_subreddits[:4] if self.target_subreddits else ["python", "learnpython", "webdev"]
            
            print(f"🎯 Searching in subreddits: {demo_subreddits}")
            
            post_request = PostDiscoveryRequest(
                subreddits=demo_subreddits,
                max_posts_per_subreddit=6,
                time_filter="day",
                reddit_credentials=MOCK_REDDIT_CREDENTIALS
            )
            
            # This will likely fail with mock credentials, so we'll handle it gracefully
            try:
                success, message, posts_data = await self.campaign_service.discover_posts(
                    campaign_id=self.campaign.id,
                    request=post_request
                )
                
                if success:
                    posts_found = posts_data.get('posts_found', 0)
                    print(f"✅ Post discovery completed")
                    print(f"📊 Found {posts_found} relevant posts")
                    
                    if 'posts' in posts_data:
                        self.target_posts = posts_data['posts']
                        print("📝 Sample discovered posts:")
                        for i, post in enumerate(self.target_posts[:3], 1):
                            print(f"   {i}. {post['title']}")
                            print(f"      📍 r/{post['subreddit']}")
                            print(f"      ⭐ Relevance: {post['relevance_score']:.2f}")
                            print()
                else:
                    print(f"⚠️  Post discovery failed: {message}")
                    raise Exception("Mock credentials")
                    
            except Exception:
                print("⚠️  Creating mock posts for demonstration...")
                
                # Create realistic mock posts
                mock_posts = [
                    {
                        "id": "mock-post-1",
                        "title": "Best practices for FastAPI project structure?",
                        "content": "I'm starting a new FastAPI project and wondering about the best way to organize my code. Any recommendations?",
                        "subreddit": "python",
                        "relevance_score": 0.85,
                        "author": "pythondev123"
                    },
                    {
                        "id": "mock-post-2", 
                        "title": "Machine learning model deployment strategies",
                        "content": "What are the best practices for deploying ML models to production? Looking for scalable solutions.",
                        "subreddit": "MachineLearning",
                        "relevance_score": 0.78,
                        "author": "mlenginer"
                    },
                    {
                        "id": "mock-post-3",
                        "title": "Python mentorship - where to find experienced developers?",
                        "content": "I'm looking for a Python mentor to help me improve my skills. Any suggestions on where to find one?",
                        "subreddit": "learnpython",
                        "relevance_score": 0.92,
                        "author": "aspiring_dev"
                    },
                    {
                        "id": "mock-post-4",
                        "title": "Database optimization tips for Django applications",
                        "content": "My Django app is getting slow with large datasets. Any tips for database optimization?",
                        "subreddit": "django",
                        "relevance_score": 0.73,
                        "author": "webdev_pro"
                    }
                ]
                
                # Simulate the campaign service updating with mock posts
                self.target_posts = mock_posts
                print(f"✅ Created {len(mock_posts)} mock posts for demonstration")
                
                print("📝 Mock posts created:")
                for i, post in enumerate(mock_posts, 1):
                    print(f"   {i}. {post['title']}")
                    print(f"      📍 r/{post['subreddit']}")
                    print(f"      ⭐ Relevance: {post['relevance_score']:.2f}")
                    print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in post discovery: {e}")
            return False
    
    async def step_5_generate_responses(self):
        """Step 5: Generate AI responses for target posts."""
        print("\n" + "="*70)
        print("💬 STEP 5: RESPONSE GENERATION")
        print("="*70)
        
        try:
            if not self.target_posts:
                print("⚠️  No target posts available for response generation")
                return False
            
            # Get campaign context from documents
            campaign_context = await self.document_service.get_campaign_context(
                organization_id=self.organization_id,
                document_ids=self.document_ids
            )
            
            print(f"📄 Campaign context prepared ({len(campaign_context)} characters)")
            
            # Generate responses for each target post
            generated_responses = []
            
            for i, post in enumerate(self.target_posts[:3], 1):
                print(f"\n💭 Generating response {i}/{min(3, len(self.target_posts))}...")
                print(f"   📝 Post: {post['title']}")
                
                # Use the Reddit service to generate response
                success, message, response_data = await self.reddit_service.generate_response(
                    post=post,
                    campaign_context=campaign_context,
                    tone="helpful",
                    organization_id=self.organization_id
                )
                
                if success and response_data:
                    generated_responses.append({
                        "id": f"response-{i}",
                        "target_post_id": post['id'],
                        "response_content": response_data['content'],
                        "confidence_score": response_data['confidence'],
                        "tone": "helpful"
                    })
                    
                    print(f"   ✅ Response generated (confidence: {response_data['confidence']:.2f})")
                    print(f"   📝 Preview: {response_data['content'][:120]}...")
                else:
                    print(f"   ❌ Response generation failed: {message}")
            
            self.planned_responses = generated_responses
            
            if generated_responses:
                print(f"\n✅ Response generation completed")
                print(f"💬 Generated {len(generated_responses)} responses")
                
                # Show summary
                avg_confidence = sum(r['confidence_score'] for r in generated_responses) / len(generated_responses)
                print(f"📊 Average confidence: {avg_confidence:.2f}")
                
                return True
            else:
                print("❌ No responses were generated successfully")
                return False
                
        except Exception as e:
            print(f"❌ Error in response generation: {e}")
            return False
    
    async def step_6_execute_responses(self):
        """Step 6: Execute responses (mock execution)."""
        print("\n" + "="*70)
        print("🚀 STEP 6: RESPONSE EXECUTION")
        print("="*70)
        
        try:
            if not self.planned_responses:
                print("⚠️  No planned responses available for execution")
                return False
            
            # Simulate response execution
            execution_results = []
            
            for i, response in enumerate(self.planned_responses, 1):
                print(f"\n🚀 Executing response {i}/{len(self.planned_responses)}...")
                print(f"   🎯 Target post: {response['target_post_id']}")
                
                # Simulate posting with some success/failure
                posting_successful = random.random() > 0.2  # 80% success rate
                
                if posting_successful:
                    execution_results.append({
                        "id": f"posted-{i}",
                        "planned_response_id": response['id'],
                        "target_post_id": response['target_post_id'],
                        "reddit_comment_id": f"mock_comment_{i}",
                        "reddit_permalink": f"/r/python/comments/mock_{i}/",
                        "posting_successful": True,
                        "posted_content": response['response_content']
                    })
                    print(f"   ✅ Response posted successfully")
                    print(f"   🔗 Mock comment ID: mock_comment_{i}")
                else:
                    execution_results.append({
                        "id": f"failed-{i}",
                        "planned_response_id": response['id'],
                        "target_post_id": response['target_post_id'],
                        "posting_successful": False,
                        "error_message": "Mock Reddit API error"
                    })
                    print(f"   ❌ Response posting failed (simulated)")
                
                # Small delay to simulate real posting
                await asyncio.sleep(0.5)
            
            # Calculate results
            successful_posts = len([r for r in execution_results if r['posting_successful']])
            failed_posts = len([r for r in execution_results if not r['posting_successful']])
            
            print(f"\n✅ Response execution completed")
            print(f"🎉 Successfully posted: {successful_posts}")
            print(f"❌ Failed to post: {failed_posts}")
            print(f"📊 Success rate: {(successful_posts / len(execution_results) * 100):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in response execution: {e}")
            return False
    
    async def step_7_monitor_and_analyze(self):
        """Step 7: Monitor campaign progress and analyze results."""
        print("\n" + "="*70)
        print("📊 STEP 7: MONITORING & ANALYSIS")
        print("="*70)
        
        try:
            # Get final campaign status
            success, message, final_campaign = await self.campaign_service.get_campaign(self.campaign.id)
            
            if success:
                print("✅ Campaign monitoring completed")
                print(f"📋 Campaign: {final_campaign.name}")
                print(f"📊 Final status: {final_campaign.status}")
                
                print("\n📈 Campaign Progress Summary:")
                print(f"   📄 Documents ingested: {len(self.document_ids)}")
                print(f"   🎯 Subreddits discovered: {len(self.target_subreddits)}")
                print(f"   📝 Posts analyzed: {len(self.target_posts)}")
                print(f"   💬 Responses generated: {len(self.planned_responses)}")
                print(f"   🚀 Responses executed: {len(self.planned_responses)}")
                
                # Analyze response quality
                if self.planned_responses:
                    avg_confidence = sum(r['confidence_score'] for r in self.planned_responses) / len(self.planned_responses)
                    high_confidence_responses = len([r for r in self.planned_responses if r['confidence_score'] > 0.8])
                    
                    print(f"\n🎯 Response Quality Analysis:")
                    print(f"   ⭐ Average confidence: {avg_confidence:.2f}")
                    print(f"   🏆 High confidence responses: {high_confidence_responses}/{len(self.planned_responses)}")
                
                # Show top subreddits
                if self.target_subreddits:
                    print(f"\n🔍 Top Target Subreddits:")
                    for i, subreddit in enumerate(self.target_subreddits[:5], 1):
                        print(f"   {i}. r/{subreddit}")
                
                # Organization statistics
                org_stats = self.document_service.get_organization_stats(self.organization_id)
                if 'error' not in org_stats:
                    print(f"\n📚 Knowledge Base Statistics:")
                    print(f"   📄 Total documents: {org_stats['total_documents']}")
                    print(f"   🧩 Total chunks: {org_stats['total_chunks']}")
                    print(f"   📏 Content length: {org_stats['total_content_length']:,} characters")
                
                return True
            else:
                print(f"❌ Campaign monitoring failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error in monitoring and analysis: {e}")
            return False
    
    async def run_complete_workflow(self):
        """Run the complete workflow."""
        print("🚀 REDDIT MARKETING AI AGENT - COMPLETE BASE WORKFLOW")
        print("=" * 80)
        print("This example demonstrates a complete end-to-end marketing campaign")
        print("using the base service classes directly (no API layer).")
        print()
        print("⚠️  Note: This example uses mock Reddit credentials for demonstration.")
        print("   Replace with real credentials for actual Reddit operations.")
        
        start_time = time.time()
        
        # Define workflow steps
        steps = [
            ("Document Setup", self.step_1_setup_documents),
            ("Campaign Creation", self.step_2_create_campaign),
            ("Subreddit Discovery", self.step_3_discover_subreddits),
            ("Post Discovery", self.step_4_discover_posts),
            ("Response Generation", self.step_5_generate_responses),
            ("Response Execution", self.step_6_execute_responses),
            ("Monitoring & Analysis", self.step_7_monitor_and_analyze)
        ]
        
        completed_steps = 0
        
        for step_name, step_function in steps:
            try:
                step_start = time.time()
                
                if await step_function():
                    completed_steps += 1
                    step_time = time.time() - step_start
                    print(f"\n✅ {step_name} completed successfully ({step_time:.1f}s)")
                else:
                    print(f"\n❌ {step_name} failed")
                    break
                    
                # Small delay between steps
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"\n❌ {step_name} failed with error: {e}")
                break
        
        total_time = time.time() - start_time
        
        # Final summary
        print("\n" + "="*80)
        print("📊 WORKFLOW SUMMARY")
        print("="*80)
        print(f"✅ Completed steps: {completed_steps}/{len(steps)}")
        print(f"⏱️  Total execution time: {total_time:.1f} seconds")
        
        if completed_steps == len(steps):
            print("🎉 Complete workflow executed successfully!")
            
            print("\n📈 Key Achievements:")
            print(f"   📄 Documents processed: {len(self.document_ids)}")
            print(f"   🎯 Subreddits identified: {len(self.target_subreddits)}")
            print(f"   📝 Posts analyzed: {len(self.target_posts)}")
            print(f"   💬 Responses generated: {len(self.planned_responses)}")
            
            print("\n💡 Next steps for production use:")
            print("   1. Replace mock Reddit credentials with real API credentials")
            print("   2. Implement proper error handling and retry logic")
            print("   3. Add response review and approval workflow")
            print("   4. Set up monitoring and alerting for campaign performance")
            print("   5. Implement rate limiting and respect Reddit guidelines")
            print("   6. Add database persistence for campaign state")
        else:
            print("⚠️  Workflow completed partially")
            print("   Check the error messages above for troubleshooting")
        
        print("\n🔧 Base Classes vs API:")
        print("   ✅ Direct access to service methods")
        print("   ✅ Better error handling and debugging")
        print("   ✅ More flexible workflow customization")
        print("   ✅ No HTTP overhead")
        print("   ⚠️  Requires understanding of internal architecture")
        
        print("\n📚 For more examples, check the other files in examples/base/")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.reddit_service.cleanup()
            await self.campaign_service.cleanup()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

async def main():
    """Run the complete workflow example."""
    workflow = CompleteWorkflowExample()
    
    try:
        await workflow.run_complete_workflow()
    finally:
        await workflow.cleanup()

if __name__ == "__main__":
    asyncio.run(main())