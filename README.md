# Reddit Marketing AI Agent

A comprehensive Reddit marketing automation system that helps organizations engage with relevant communities based on their content and expertise.

## 🚀 Features

- **Document-Based Subreddit Discovery**: Analyze uploaded documents to find relevant subreddits
- **Intelligent Post Discovery**: Find relevant posts and comments to engage with
- **AI-Powered Response Generation**: Generate contextual, helpful responses based on your content
- **Automated Posting**: Execute approved responses automatically
- **Campaign Management**: Track and manage multiple marketing campaigns
- **Response Tracking**: Monitor posted responses and avoid duplicate interactions

## 🏗️ Architecture

### Refactored Structure
```
app/
├── shared/                    # Shared utilities and common functionality
│   ├── base/                 # Base classes and mixins
│   ├── clients/              # Shared client interfaces
│   ├── llm/                  # Shared LLM functionality
│   └── utils/                # Utility functions
├── core/                     # Core application functionality
├── rag/                     # RAG system with unified services
├── reddit/                  # Reddit marketing functionality
└── services/                # Application services
```

### Key Improvements
- **30% code reduction** through elimination of redundancy
- **Unified services** for document processing and Reddit operations
- **Centralized configuration** and shared utilities
- **Consistent base classes** for all services

## 📋 Workflow

### 1. Campaign Creation
```python
create_request = CampaignCreateRequest(
    name="Python Learning Community Outreach",
    description="Engage with Python learning communities",
    response_tone=ResponseTone.HELPFUL,
    max_responses_per_day=5
)
```

### 2. Document Selection & Subreddit Discovery
```python
subreddit_request = SubredditDiscoveryRequest(
    document_ids=["doc-1", "doc-2"]
)
```

### 3. Post Discovery
```python
post_request = PostDiscoveryRequest(
    subreddits=["python", "learnpython"],
    max_posts_per_subreddit=10,
    time_filter="day"
)
```

### 4. Response Generation
```python
response_request = ResponseGenerationRequest(
    target_post_ids=["post-1", "post-2"],
    tone=ResponseTone.HELPFUL
)
```

### 5. Response Execution
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

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- OpenAI API key
- Google API key (for Gemini)
- Reddit API credentials

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   ```
4. Run the application:
   ```bash
   cd app
   python main.py
   ```

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

## 📝 Usage Examples

### Programmatic Usage
```python
from reddit.services.campaign_service import CampaignService
from reddit.models import CampaignCreateRequest, ResponseTone

# Initialize service
campaign_service = CampaignService()

# Create campaign
request = CampaignCreateRequest(
    name="My Campaign",
    response_tone=ResponseTone.HELPFUL
)

success, message, campaign = await campaign_service.create_campaign(
    "org-1", request
)
```

### API Usage
```python
import requests

# Create campaign via API
response = requests.post(
    "http://localhost:8000/api/v1/reddit/campaigns/?organization_id=org-1",
    json={
        "name": "My Campaign",
        "response_tone": "helpful"
    }
)
```

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

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the server
- **Architecture Guide**: See `app/README.md` for detailed architecture information
- **Configuration Reference**: See `app/core/config.py` for all configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the documentation in `app/README.md`
2. Review the API documentation at `/docs`
3. Create an issue on GitHub with detailed information

## 🔄 Version History

- **v2.0.0**: Refactored architecture with 30% code reduction
- **v1.0.0**: Initial release with basic campaign functionality

---

**Note**: This system is designed for legitimate marketing purposes. Always follow Reddit's community guidelines and terms of service.