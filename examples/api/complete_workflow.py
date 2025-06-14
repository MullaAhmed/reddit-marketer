"""
Example: Complete Workflow using REST API

This example demonstrates a complete end-to-end workflow:
1. Ingest documents
2. Create campaign
3. Discover subreddits
4. Find relevant posts
5. Generate responses
6. Execute responses (mock)
7. Monitor progress
"""

import requests
import json
import time
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
ORGANIZATION_ID = "complete-workflow-org"

# Mock Reddit credentials for demonstration
MOCK_REDDIT_CREDENTIALS = {
    "client_id": "demo_client_id",
    "client_secret": "demo_client_secret",
    "username": "demo_username",
    "password": "demo_password"
}

class RedditMarketingWorkflow:
    """Complete Reddit marketing workflow using API."""
    
    def __init__(self):
        self.organization_id = ORGANIZATION_ID
        self.campaign_id = None
        self.document_ids = []
        self.target_subreddits = []
        self.target_posts = []
        self.planned_responses = []
    
    def step_1_ingest_documents(self) -> bool:
        """Step 1: Ingest documents for the organization."""
        print("\n" + "="*60)
        print("📄 STEP 1: DOCUMENT INGESTION")
        print("="*60)
        
        # Sample documents for a Python consulting business
        documents = [
            {
                "title": "Python Web Development Services",
                "content": """
                We specialize in Python web development using modern frameworks like FastAPI, Django, and Flask.
                Our team builds scalable REST APIs, microservices, and full-stack web applications.
                We have expertise in database design with PostgreSQL and MongoDB, cloud deployment on AWS and Azure,
                and containerization with Docker and Kubernetes. We follow best practices including test-driven
                development, clean architecture, and comprehensive documentation.
                """,
                "metadata": {
                    "category": "services",
                    "type": "web-development",
                    "technologies": ["Python", "FastAPI", "Django", "Flask"]
                }
            },
            {
                "title": "Machine Learning Consulting",
                "content": """
                Our machine learning practice helps businesses leverage AI for predictive analytics,
                recommendation systems, and automated decision making. We work with scikit-learn,
                TensorFlow, and PyTorch to build custom ML models. Our services include data preprocessing,
                feature engineering, model training and validation, and deployment to production environments.
                We specialize in supervised learning, unsupervised learning, and deep learning applications.
                """,
                "metadata": {
                    "category": "services",
                    "type": "machine-learning",
                    "technologies": ["scikit-learn", "TensorFlow", "PyTorch"]
                }
            },
            {
                "title": "Python Training and Mentorship",
                "content": """
                We offer comprehensive Python training programs for individuals and teams.
                Our curriculum covers Python fundamentals, object-oriented programming, web development,
                data analysis, and machine learning. We provide hands-on workshops, code reviews,
                and one-on-one mentorship. Our instructors are experienced Python developers who
                understand real-world challenges and best practices in software development.
                """,
                "metadata": {
                    "category": "services",
                    "type": "training",
                    "topics": ["Python", "programming", "mentorship"]
                }
            }
        ]
        
        try:
            url = f"{API_BASE_URL}/documents/ingest"
            params = {"organization_id": self.organization_id}
            
            response = requests.post(url, params=params, json=documents)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                self.document_ids = result['data']['document_ids']
                print(f"✅ Successfully ingested {len(documents)} documents")
                print(f"📊 Document IDs: {self.document_ids}")
                return True
            else:
                print(f"❌ Document ingestion failed: {result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Error in document ingestion: {e}")
            return False
    
    def step_2_create_campaign(self) -> bool:
        """Step 2: Create a marketing campaign."""
        print("\n" + "="*60)
        print("🎯 STEP 2: CAMPAIGN CREATION")
        print("="*60)
        
        try:
            url = f"{API_BASE_URL}/campaigns/"
            params = {"organization_id": self.organization_id}
            
            payload = {
                "name": "Python Consulting Outreach 2024",
                "description": "Engage with Python communities to share expertise and build relationships",
                "response_tone": "helpful",
                "max_responses_per_day": 5
            }
            
            response = requests.post(url, params=params, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                campaign = result['campaign']
                self.campaign_id = campaign['id']
                print(f"✅ Campaign created successfully")
                print(f"📋 Campaign ID: {self.campaign_id}")
                print(f"📝 Name: {campaign['name']}")
                print(f"🎯 Tone: {campaign['response_tone']}")
                print(f"📊 Status: {campaign['status']}")
                return True
            else:
                print(f"❌ Campaign creation failed: {result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Error in campaign creation: {e}")
            return False
    
    def step_3_discover_subreddits(self) -> bool:
        """Step 3: Discover relevant subreddits."""
        print("\n" + "="*60)
        print("🔍 STEP 3: SUBREDDIT DISCOVERY")
        print("="*60)
        
        try:
            url = f"{API_BASE_URL}/campaigns/{self.campaign_id}/discover-subreddits"
            
            payload = {"document_ids": self.document_ids}
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                self.target_subreddits = result['data']['subreddits']
                print(f"✅ Subreddit discovery completed")
                print(f"📊 Found {len(self.target_subreddits)} relevant subreddits:")
                
                for i, subreddit in enumerate(self.target_subreddits[:5], 1):
                    print(f"   {i}. r/{subreddit}")
                
                if len(self.target_subreddits) > 5:
                    print(f"   ... and {len(self.target_subreddits) - 5} more")
                
                return True
            else:
                print(f"❌ Subreddit discovery failed: {result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Error in subreddit discovery: {e}")
            return False
    
    def step_4_discover_posts(self) -> bool:
        """Step 4: Discover relevant posts in target subreddits."""
        print("\n" + "="*60)
        print("📝 STEP 4: POST DISCOVERY")
        print("="*60)
        
        try:
            # Use a subset of subreddits for demonstration
            demo_subreddits = self.target_subreddits[:3] if self.target_subreddits else ["python", "learnpython"]
            
            url = f"{API_BASE_URL}/campaigns/{self.campaign_id}/discover-posts"
            
            payload = {
                "subreddits": demo_subreddits,
                "max_posts_per_subreddit": 5,
                "time_filter": "day",
                "reddit_credentials": MOCK_REDDIT_CREDENTIALS
            }
            
            response = requests.post(url, json=payload)
            
            # Note: This will likely fail with mock credentials, but shows the workflow
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    posts_found = result['data']['posts_found']
                    print(f"✅ Post discovery completed")
                    print(f"📊 Found {posts_found} relevant posts")
                    
                    if 'posts' in result['data']:
                        self.target_posts = result['data']['posts']
                        print("📝 Sample posts:")
                        for i, post in enumerate(self.target_posts[:3], 1):
                            print(f"   {i}. {post['title']}")
                            print(f"      📍 r/{post['subreddit']}")
                            print(f"      ⭐ Relevance: {post['relevance_score']:.2f}")
                    
                    return True
                else:
                    print(f"⚠️  Post discovery returned error: {result['message']}")
            else:
                print(f"⚠️  Post discovery failed (expected with mock credentials)")
                print("   Creating mock posts for demonstration...")
                
                # Create mock posts for demonstration
                self.target_posts = [
                    {"id": "mock-post-1", "title": "Need help with FastAPI", "subreddit": "python"},
                    {"id": "mock-post-2", "title": "Machine learning project advice", "subreddit": "MachineLearning"},
                    {"id": "mock-post-3", "title": "Python web development best practices", "subreddit": "webdev"}
                ]
                print(f"✅ Created {len(self.target_posts)} mock posts for demonstration")
                return True
                
        except Exception as e:
            print(f"⚠️  Error in post discovery (creating mock data): {e}")
            # Create mock data for demonstration
            self.target_posts = [
                {"id": "mock-post-1", "title": "Need help with FastAPI", "subreddit": "python"},
                {"id": "mock-post-2", "title": "Machine learning project advice", "subreddit": "MachineLearning"}
            ]
            return True
    
    def step_5_generate_responses(self) -> bool:
        """Step 5: Generate responses for target posts."""
        print("\n" + "="*60)
        print("💬 STEP 5: RESPONSE GENERATION")
        print("="*60)
        
        try:
            target_post_ids = [post['id'] for post in self.target_posts[:3]]
            
            url = f"{API_BASE_URL}/campaigns/{self.campaign_id}/generate-responses"
            
            payload = {
                "target_post_ids": target_post_ids,
                "tone": "helpful"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    responses_generated = result['data']['responses_generated']
                    print(f"✅ Response generation completed")
                    print(f"💬 Generated {responses_generated} responses")
                    
                    if 'responses' in result['data']:
                        self.planned_responses = result['data']['responses']
                        print("📝 Sample responses:")
                        for i, resp in enumerate(self.planned_responses[:2], 1):
                            print(f"   {i}. Response for {resp['target_post_id']}")
                            print(f"      🎯 Tone: {resp['tone']}")
                            print(f"      ⭐ Confidence: {resp['confidence_score']:.2f}")
                            print(f"      📝 Preview: {resp['response_content'][:100]}...")
                            print()
                    
                    return True
                else:
                    print(f"⚠️  Response generation failed: {result['message']}")
            else:
                print(f"⚠️  Response generation failed with status {response.status_code}")
                
            # Create mock responses for demonstration
            print("   Creating mock responses for demonstration...")
            self.planned_responses = [
                {
                    "id": f"mock-response-{i}",
                    "target_post_id": post['id'],
                    "response_content": f"Mock helpful response for {post['title']}",
                    "confidence_score": 0.85,
                    "tone": "helpful"
                }
                for i, post in enumerate(self.target_posts, 1)
            ]
            print(f"✅ Created {len(self.planned_responses)} mock responses")
            return True
                
        except Exception as e:
            print(f"⚠️  Error in response generation: {e}")
            return True  # Continue with mock data
    
    def step_6_execute_responses(self) -> bool:
        """Step 6: Execute (post) responses to Reddit."""
        print("\n" + "="*60)
        print("🚀 STEP 6: RESPONSE EXECUTION")
        print("="*60)
        
        try:
            planned_response_ids = [resp['id'] for resp in self.planned_responses[:2]]
            
            url = f"{API_BASE_URL}/campaigns/{self.campaign_id}/execute-responses"
            
            payload = {
                "planned_response_ids": planned_response_ids,
                "reddit_credentials": MOCK_REDDIT_CREDENTIALS
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    responses_posted = result['data']['responses_posted']
                    responses_failed = result['data']['responses_failed']
                    
                    print(f"✅ Response execution completed")
                    print(f"🎉 Successfully posted: {responses_posted}")
                    print(f"❌ Failed to post: {responses_failed}")
                    return True
                else:
                    print(f"⚠️  Response execution failed: {result['message']}")
            else:
                print(f"⚠️  Response execution failed (expected with mock credentials)")
                print("   In real usage, responses would be posted to Reddit here")
                return True
                
        except Exception as e:
            print(f"⚠️  Error in response execution: {e}")
            print("   This is expected when using mock Reddit credentials")
            return True
    
    def step_7_monitor_progress(self) -> bool:
        """Step 7: Monitor campaign progress."""
        print("\n" + "="*60)
        print("📊 STEP 7: PROGRESS MONITORING")
        print("="*60)
        
        try:
            url = f"{API_BASE_URL}/campaigns/{self.campaign_id}/status"
            
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            
            if result['success']:
                campaign = result['campaign']
                status_data = result['data']
                
                print(f"✅ Campaign monitoring completed")
                print(f"📋 Campaign: {campaign['name']}")
                print(f"📊 Status: {campaign['status']}")
                print()
                print("📈 Progress Summary:")
                print(f"   📄 Documents selected: {status_data['documents_selected']}")
                print(f"   🎯 Subreddits found: {status_data['subreddits_found']}")
                print(f"   📝 Posts found: {status_data['posts_found']}")
                print(f"   💬 Responses planned: {status_data['responses_planned']}")
                print(f"   🎉 Responses posted: {status_data['responses_posted']}")
                print(f"   ✅ Successful posts: {status_data['successful_posts']}")
                print(f"   ❌ Failed posts: {status_data['failed_posts']}")
                
                return True
            else:
                print(f"❌ Progress monitoring failed: {result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Error in progress monitoring: {e}")
            return False
    
    def run_complete_workflow(self):
        """Run the complete workflow."""
        print("🚀 REDDIT MARKETING AI AGENT - COMPLETE WORKFLOW")
        print("=" * 80)
        print("This example demonstrates a complete end-to-end marketing campaign")
        print("using the Reddit Marketing AI Agent API.")
        print()
        print("⚠️  Note: This example uses mock Reddit credentials for demonstration.")
        print("   Replace with real credentials for actual Reddit posting.")
        
        # Track workflow progress
        steps = [
            ("Document Ingestion", self.step_1_ingest_documents),
            ("Campaign Creation", self.step_2_create_campaign),
            ("Subreddit Discovery", self.step_3_discover_subreddits),
            ("Post Discovery", self.step_4_discover_posts),
            ("Response Generation", self.step_5_generate_responses),
            ("Response Execution", self.step_6_execute_responses),
            ("Progress Monitoring", self.step_7_monitor_progress)
        ]
        
        completed_steps = 0
        
        for step_name, step_function in steps:
            try:
                if step_function():
                    completed_steps += 1
                    print(f"\n✅ {step_name} completed successfully")
                else:
                    print(f"\n❌ {step_name} failed")
                    break
                    
                # Small delay between steps
                time.sleep(1)
                
            except Exception as e:
                print(f"\n❌ {step_name} failed with error: {e}")
                break
        
        # Final summary
        print("\n" + "="*80)
        print("📊 WORKFLOW SUMMARY")
        print("="*80)
        print(f"✅ Completed steps: {completed_steps}/{len(steps)}")
        
        if completed_steps == len(steps):
            print("🎉 Complete workflow executed successfully!")
            print("\n💡 Next steps for real usage:")
            print("   1. Replace mock Reddit credentials with real ones")
            print("   2. Review generated responses before posting")
            print("   3. Monitor campaign performance and adjust strategy")
            print("   4. Respect Reddit community guidelines and rate limits")
        else:
            print("⚠️  Workflow completed partially")
            print("   Check the error messages above for troubleshooting")
        
        print("\n📚 For more examples, check the other files in the examples/ folder")

def main():
    """Run the complete workflow example."""
    workflow = RedditMarketingWorkflow()
    workflow.run_complete_workflow()

if __name__ == "__main__":
    main()