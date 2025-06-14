# Reddit Marketing Examples

This directory contains comprehensive examples showing how to use the Reddit Marketing AI Agent system. The examples are organized into three main categories:

## 📁 Example Files

### 1. `individual_components.py`
**Purpose**: Test and understand each component independently

**What it includes**:
- Document ingestion examples
- Document retrieval from RAG system
- Subreddit discovery using AI analysis
- Reddit post finding and searching
- AI-powered response generation
- Reddit API interactions (reading/posting)
- Ingestion agent workflow

**When to use**: 
- Learning how each component works
- Debugging specific functionality
- Testing individual features
- Development and troubleshooting

### 2. `api_workflow_examples.py`
**Purpose**: Interact with the system via HTTP API endpoints

**What it includes**:
- Complete API workflow using requests
- Individual API endpoint examples
- Error handling and validation
- Async API client examples
- Direct requests library usage

**When to use**:
- Building frontend applications
- Integrating with external systems
- API testing and validation
- Production deployment scenarios

### 3. `complete_workflows.py`
**Purpose**: End-to-end campaign management examples

**What it includes**:
- Complete programmatic workflow
- Complete API-based workflow
- Batch processing for multiple campaigns
- Real-world scenario simulations

**When to use**:
- Understanding the full campaign lifecycle
- Production workflow implementation
- Scaling to multiple campaigns
- Complete system testing

### 4. `campaign_workflow.py`
**Purpose**: Original campaign workflow example (from integration)

**What it includes**:
- Step-by-step campaign creation
- Basic workflow demonstration
- Simple error handling

## 🚀 Getting Started

### Prerequisites

1. **Environment Setup**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   export OPENAI_API_KEY="your_openai_key"
   export GOOGLE_API_KEY="your_google_key"
   export REDDIT_CLIENT_ID="your_reddit_client_id"
   export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
   ```

2. **Reddit API Credentials**:
   - Create a Reddit app at https://www.reddit.com/prefs/apps
   - Get your client_id and client_secret
   - For posting, you'll need username and password

3. **Document Preparation**:
   - Have some documents ready to ingest
   - Or use the sample documents provided in examples

### Running Examples

#### Option 1: Individual Components
```bash
cd app/reddit/examples
python individual_components.py
```

Choose from:
- All examples (comprehensive test)
- Document ingestion
- Document retrieval
- Subreddit discovery
- Post discovery
- Response generation
- Reddit interaction
- Ingestion agent

#### Option 2: API Workflows
```bash
# Start the API server first
cd app
python main.py

# In another terminal, run API examples
cd app/reddit/examples
python api_workflow_examples.py
```

Choose from:
- Complete API workflow
- Individual API calls
- Error handling examples
- Direct requests usage
- Async API client

#### Option 3: Complete Workflows
```bash
cd app/reddit/examples
python complete_workflows.py
```

Choose from:
- Complete programmatic workflow
- Complete API-based workflow
- Batch processing workflow
- Run all workflows

## 📋 Example Scenarios

### Scenario 1: Testing Individual Components
**Use Case**: You want to test the subreddit discovery feature

```bash
python individual_components.py
# Choose option 4 (Subreddit discovery)
```

This will:
- Analyze sample content
- Find relevant subreddits
- Display results with subscriber counts

### Scenario 2: API Integration Testing
**Use Case**: You're building a frontend and need to test API endpoints

```bash
# Terminal 1: Start API server
python main.py

# Terminal 2: Test API
python api_workflow_examples.py
# Choose option 2 (Individual API calls)
```

This will:
- Create campaigns via API
- Test error handling
- Show request/response formats

### Scenario 3: Full Campaign Simulation
**Use Case**: You want to see the complete workflow in action

```bash
python complete_workflows.py
# Choose option 1 (Complete programmatic workflow)
```

This will:
- Ingest company documents
- Create a marketing campaign
- Discover relevant subreddits
- Find target posts
- Generate responses
- Show campaign analytics

## ⚠️ Safety Notes

### Reddit API Usage
- **Rate Limiting**: All examples respect Reddit's rate limits
- **Read-Only by Default**: Posting operations are commented out for safety
- **Test Credentials**: Replace sample credentials with your own
- **Community Guidelines**: Always follow subreddit rules

### Response Posting
- **Manual Review**: Always review generated responses before posting
- **Confidence Thresholds**: Examples use confidence scores to filter responses
- **Duplicate Prevention**: System prevents responding to same authors
- **Error Handling**: Comprehensive error tracking and recovery

### Data Privacy
- **Local Storage**: All data is stored locally in JSON files
- **No External Sharing**: Documents and responses stay on your system
- **Credential Security**: Never commit API credentials to version control

## 🔧 Customization

### Modifying Examples

1. **Change Reddit Credentials**:
   ```python
   reddit_credentials = {
       "client_id": "YOUR_ACTUAL_CLIENT_ID",
       "client_secret": "YOUR_ACTUAL_CLIENT_SECRET",
       "username": "YOUR_REDDIT_USERNAME",
       "password": "YOUR_REDDIT_PASSWORD"
   }
   ```

2. **Adjust Response Tones**:
   ```python
   # Available tones
   ResponseTone.HELPFUL      # Helpful and supportive
   ResponseTone.PROMOTIONAL  # Promotional but tasteful
   ResponseTone.EDUCATIONAL  # Educational and informative
   ResponseTone.CASUAL       # Casual and friendly
   ResponseTone.PROFESSIONAL # Professional and formal
   ```

3. **Modify Document Content**:
   ```python
   # Add your own company documents
   documents = [
       {
           "title": "Your Service Description",
           "content": "Your actual company content...",
           "metadata": {"category": "services"}
       }
   ]
   ```

4. **Configure Campaign Settings**:
   ```python
   create_request = CampaignCreateRequest(
       name="Your Campaign Name",
       description="Your campaign description",
       response_tone=ResponseTone.HELPFUL,
       max_responses_per_day=10  # Adjust as needed
   )
   ```

## 📊 Understanding Output

### Campaign Status Progression
1. `CREATED` - Campaign initialized
2. `SUBREDDITS_DISCOVERED` - Relevant subreddits found
3. `POSTS_FOUND` - Target posts identified
4. `RESPONSES_PLANNED` - Responses generated
5. `RESPONSES_POSTED` - Responses posted to Reddit

### Metrics to Monitor
- **Relevance Scores**: How relevant posts are to your content (0.0-1.0)
- **Confidence Scores**: AI confidence in generated responses (0.0-1.0)
- **Success Rates**: Percentage of successful operations
- **Response Quality**: Manual review of generated content

## 🐛 Troubleshooting

### Common Issues

1. **Reddit API Errors**:
   - Check credentials are correct
   - Verify rate limits aren't exceeded
   - Ensure Reddit app permissions

2. **Document Ingestion Failures**:
   - Check document format and content
   - Verify organization IDs are consistent
   - Ensure data directory permissions

3. **API Connection Issues**:
   - Verify API server is running
   - Check port availability (default: 8000)
   - Confirm network connectivity

4. **Response Generation Problems**:
   - Check AI service credentials
   - Verify document content quality
   - Review relevance thresholds

### Debug Mode
Enable detailed logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Next Steps

After running the examples:

1. **Customize for Your Use Case**: Modify documents and campaign settings
2. **Integrate with Your System**: Use API endpoints in your application
3. **Scale Up**: Implement batch processing for multiple campaigns
4. **Monitor Performance**: Track metrics and optimize settings
5. **Deploy to Production**: Set up proper credentials and monitoring

For production deployment, see the main README.md for deployment guidelines and best practices.