# Reddit Marketing AI Agent

A comprehensive Reddit marketing automation system that helps organizations engage with relevant communities based on their content and expertise.

## 🚀 Features

- **Document-Based Subreddit Discovery**: Analyze uploaded documents to find relevant subreddits
- **Intelligent Post Discovery**: Find relevant posts and comments to engage with
- **AI-Powered Response Generation**: Generate contextual, helpful responses based on your content
- **Automated Posting**: Execute approved responses automatically
- **Campaign Management**: Track and manage multiple marketing campaigns
- **Response Tracking**: Monitor posted responses and avoid duplicate interactions

## 📋 Workflow

### 1. Campaign Creation
Create a new marketing campaign with specific tone and daily limits:

```python
create_request = CampaignCreateRequest(
    name="Python Learning Community Outreach",
    description="Engage with Python learning communities",
    response_tone=ResponseTone.HELPFUL,
    max_responses_per_day=5
)
```

### 2. Document Selection & Subreddit Discovery
Select documents and discover relevant subreddits:

```python
subreddit_request = SubredditDiscoveryRequest(
    document_ids=["doc-1", "doc-2"]
)
```

### 3. Post Discovery
Find relevant posts in discovered subreddits:

```python
post_request = PostDiscoveryRequest(
    subreddits=["python", "learnpython"],
    max_posts_per_subreddit=10,
    time_filter="day"
)
```

### 4. Response Generation
Generate contextual responses for target posts:

```python
response_request = ResponseGenerationRequest(
    target_post_ids=["post-1", "post-2"],
    tone=ResponseTone.HELPFUL
)
```

### 5. Response Execution
Post approved responses to Reddit:

```python
execution_request = ResponseExecutionRequest(
    planned_response_ids=["response-1", "response-2"],
    reddit_credentials=reddit_creds
)
```

## 🔧 API Endpoints

### Campaign Management
- `POST /api/v1/reddit/campaigns/` - Create campaign
- `GET /api/v1/reddit/campaigns/{id}` - Get campaign
- `GET /api/v1/reddit/campaigns/` - List campaigns

### Workflow Steps
- `POST /api/v1/reddit/campaigns/{id}/discover-subreddits` - Find subreddits
- `POST /api/v1/reddit/campaigns/{id}/discover-posts` - Find posts
- `POST /api/v1/reddit/campaigns/{id}/generate-responses` - Generate responses
- `POST /api/v1/reddit/campaigns/{id}/execute-responses` - Post responses

### Monitoring
- `GET /api/v1/reddit/campaigns/{id}/status` - Get campaign status

## 🏗️ Architecture

### Core Components

1. **CampaignService**: Orchestrates the entire workflow
2. **IngestionAgent**: Analyzes documents and finds subreddits
3. **RedditPostFinder**: Searches for relevant posts
4. **RedditInteractor**: Handles Reddit API interactions
5. **DocumentRetrieval**: Retrieves relevant content from RAG system

### Data Models

- **Campaign**: Main campaign entity with status tracking
- **TargetPost**: Posts/comments identified for engagement
- **PlannedResponse**: Generated responses awaiting approval
- **PostedResponse**: Successfully posted responses with tracking

## 🔒 Safety Features

- **Duplicate Prevention**: Avoids responding to the same author multiple times
- **Relevance Scoring**: AI-powered relevance analysis before responding
- **Manual Approval**: Responses require explicit approval before posting
- **Rate Limiting**: Configurable daily response limits
- **Error Handling**: Comprehensive error tracking and recovery

## 📊 Campaign Status Tracking

Campaigns progress through these states:
1. `CREATED` - Campaign initialized
2. `DOCUMENTS_UPLOADED` - Documents selected
3. `SUBREDDITS_DISCOVERED` - Relevant subreddits found
4. `POSTS_FOUND` - Target posts identified
5. `RESPONSES_PLANNED` - Responses generated
6. `RESPONSES_POSTED` - Responses posted to Reddit
7. `COMPLETED` - Campaign finished

## 🛠️ Configuration

### Reddit API Credentials
```python
reddit_credentials = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret", 
    "username": "your_username",
    "password": "your_password"
}
```

### Response Tones
- `HELPFUL` - Helpful and supportive
- `PROMOTIONAL` - Promotional but tasteful
- `EDUCATIONAL` - Educational and informative
- `CASUAL` - Casual and friendly
- `PROFESSIONAL` - Professional and formal

## 📝 Example Usage

See `reddit/examples/campaign_workflow.py` for a complete example workflow.

## ⚠️ Important Notes

1. **Reddit API Compliance**: Ensure compliance with Reddit's API terms
2. **Rate Limiting**: Respect Reddit's rate limits and community guidelines
3. **Content Quality**: Focus on providing genuine value to communities
4. **Manual Review**: Always review generated responses before posting
5. **Community Rules**: Respect individual subreddit rules and guidelines

## 🔍 Monitoring & Analytics

The system tracks:
- Response success/failure rates
- Community engagement metrics
- Campaign progression
- Error logs and debugging info

For engagement analytics and performance metrics, integrate with external analytics tools.