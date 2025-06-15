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

### Clean, Modular Structure
```
app/
├── main.py                           # Single application entry point
├── core/                            # Core application functionality
│   ├── config.py                    # Centralized configuration
│   ├── dependencies.py              # FastAPI dependencies
│   └── middleware.py                # Application middleware
├── api/                             # Unified API layer
│   ├── router.py                    # Main API router
│   └── endpoints/                   # All API endpoints
│       ├── campaigns.py             # Campaign management endpoints
│       ├── documents.py             # Document management endpoints
│       ├── subreddits.py           # Subreddit discovery endpoints
│       └── health.py               # Health check endpoints
├── services/                        # Business logic layer
│   ├── campaign_service.py          # Campaign orchestration
│   ├── document_service.py          # Document processing (RAG)
│   ├── reddit_service.py            # Reddit operations
│   ├── llm_service.py              # LLM interactions
│   └── web_scraper.py              # Web scraping
├── models/                          # Data models
│   ├── campaign.py                  # Campaign-related models
│   ├── document.py                  # Document-related models
│   ├── reddit.py                    # Reddit-related models
│   └── common.py                    # Shared models
├── clients/                         # External service clients
│   ├── reddit_client.py             # Reddit API client
│   ├── llm_client.py               # LLM provider clients
│   └── storage_client.py           # Storage clients (ChromaDB, etc.)
├── utils/                           # Utility functions
│   ├── text_processing.py          # Text utilities
│   ├── file_utils.py               # File operations
│   └── validation.py               # Data validation
├── storage/                         # Data persistence layer
│   ├── json_storage.py              # JSON file operations
│   └── vector_storage.py            # Vector database operations
└── managers/                        # Storage managers
    ├── document_manager.py          # Document storage
    ├── campaign_manager.py          # Campaign storage
    └── embeddings_manager.py        # Embeddings management
```

### Key Design Principles
- **Separation of Concerns**: Clear boundaries between API, business logic, and data layers
- **Unified Services**: Centralized document processing and Reddit operations
- **Modular Architecture**: Easy to extend and maintain
- **Clean Dependencies**: Minimal coupling between components

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
- `POST /api/v1/campaigns/` - Create campaign
- `GET /api/v1/campaigns/{id}` - Get campaign
- `GET /api/v1/campaigns/` - List campaigns

### Workflow Steps
- `POST /api/v1/campaigns/{id}/discover-subreddits` - Find subreddits
- `POST /api/v1/campaigns/{id}/discover-posts` - Find posts
- `POST /api/v1/campaigns/{id}/generate-responses` - Generate responses
- `POST /api/v1/campaigns/{id}/execute-responses` - Post responses

### Document Management
- `POST /api/v1/documents/ingest` - Ingest documents
- `POST /api/v1/documents/query` - Query documents
- `GET /api/v1/documents/organizations/{id}` - Get organization documents

### Subreddit Discovery
- `POST /api/v1/subreddits/discover` - Discover subreddits
- `POST /api/v1/subreddits/extract-topics` - Extract topics

### Health & Monitoring
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

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
   GROQ_API_KEY=your_groq_key
   FIRECRAWL_API_KEY=your_firecrawl_key
   LANGCHAIN_PROJECT=your_langchain_project
   ```
4. Run the application:
   ```bash
   cd app
   python main.py
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

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

### Environment Variables
```env
# Required API Keys
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# Optional API Keys
GROQ_API_KEY=your_groq_key
FIRECRAWL_API_KEY=your_firecrawl_key
LANGCHAIN_PROJECT=your_langchain_project

# Application Settings
DATA_DIR=data
MODEL_NAME=gpt-4o
EMBEDDING_PROVIDER=openai
DOCUMENT_STORE_TYPE=chroma
```

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
from services.campaign_service import CampaignService
from models.campaign import CampaignCreateRequest, ResponseTone

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
    "http://localhost:8000/api/v1/campaigns/?organization_id=org-1",
    json={
        "name": "My Campaign",
        "response_tone": "helpful"
    }
)

# Get campaign status
status_response = requests.get(
    f"http://localhost:8000/api/v1/campaigns/{campaign_id}/status"
)
```

### Document Ingestion
```python
# Ingest documents
documents = [
    {
        "title": "Python Tutorial",
        "content": "Learn Python programming...",
        "metadata": {"category": "tutorial"}
    }
]

response = requests.post(
    "http://localhost:8000/api/v1/documents/ingest?organization_id=org-1",
    json=documents
)
```

## 🧠 AI & LLM Integration

### Supported Providers
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Google**: Gemini 2.0 Flash
- **Groq**: Llama 3.3 70B Versatile

### LLM Service Features
- **Multi-provider support**: Switch between different LLM providers
- **Structured outputs**: JSON response formatting
- **Temperature control**: Adjustable creativity levels
- **Token management**: Usage tracking and optimization

### Vector Storage
- **ChromaDB**: Default vector database for document embeddings
- **OpenAI Embeddings**: High-quality text embeddings
- **Semantic Search**: Find relevant content based on meaning
- **Chunk Management**: Intelligent text chunking and overlap

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
- LLM usage and costs
- Vector storage statistics

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the server
- **OpenAPI Spec**: Available at `/openapi.json`
- **Health Checks**: Multiple endpoints for monitoring system health

## 🧪 Testing

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/api/v1/health/

# Detailed health check
curl http://localhost:8000/api/v1/health/detailed

# Readiness check
curl http://localhost:8000/api/v1/health/ready
```

### API Testing
```bash
# Test document ingestion
curl -X POST "http://localhost:8000/api/v1/documents/ingest?organization_id=test-org" \
  -H "Content-Type: application/json" \
  -d '[{"title": "Test Doc", "content": "Test content"}]'

# Test campaign creation
curl -X POST "http://localhost:8000/api/v1/campaigns/?organization_id=test-org" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Campaign", "response_tone": "helpful"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run the application in development mode
cd app
python main.py

# Access API documentation
open http://localhost:8000/docs
```

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the health check endpoints
3. Check application logs for detailed error information
4. Create an issue on GitHub with detailed information

## 🔄 Version History

- **v2.0.0**: Clean architecture with modular design
- **v1.0.0**: Initial release with basic campaign functionality

---

**Note**: This system is designed for legitimate marketing purposes. Always follow Reddit's community guidelines and terms of service.