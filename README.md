# Reddit Marketing AI Agent

A comprehensive Reddit marketing automation system that helps organizations engage with relevant communities based on their content and expertise.

## 🚀 Features

- **Multiple Document Ingestion Methods**: 
  - Direct content input
  - File upload processing
  - **URL scraping** with Firecrawl and BeautifulSoup
- **Document-Based Subreddit Discovery**: Analyze uploaded documents to find relevant subreddits
- **Intelligent Post Discovery**: Find relevant posts and comments to engage with
- **AI-Powered Response Generation**: Generate contextual, helpful responses based on your content
- **Automated Posting**: Execute approved responses automatically
- **Campaign Management**: Track and manage multiple marketing campaigns
- **Analytics & Reporting**: Comprehensive analytics for campaign performance
- **Response Tracking**: Monitor posted responses and avoid duplicate interactions
- **Complete Example Workflow**: Jupyter notebook demonstrating all features

## 🏗️ Architecture

### Clean, Modular Structure
```
app/
├── main.py                           # Single application entry point
├── core/                            # Core application functionality
│   ├── settings.py                  # Centralized configuration
│   ├── dependencies.py              # FastAPI dependencies
│   └── middleware.py                # Application middleware
├── api/                             # Unified API layer
│   ├── router.py                    # Main API router
│   └── endpoints/                   # All API endpoints
│       ├── campaigns.py             # Campaign management endpoints
│       ├── documents.py             # Document management endpoints
│       ├── subreddits.py           # Subreddit discovery endpoints
│       ├── analytics.py            # Analytics endpoints
│       └── health.py               # Health check endpoints
├── services/                        # Business logic layer
│   ├── campaign_service.py          # Campaign orchestration
│   ├── document_service.py          # Document processing (RAG)
│   ├── reddit_service.py            # Reddit operations
│   ├── llm_service.py              # LLM interactions
│   ├── analytics_service.py        # Analytics and reporting
│   └── web_scraper.py              # Web scraping service
├── models/                          # Data models
│   ├── campaign.py                  # Campaign-related models
│   ├── document.py                  # Document-related models
│   ├── reddit.py                    # Reddit-related models
│   └── common.py                    # Shared models (health status)
├── clients/                         # External service clients
│   ├── reddit_client.py             # Reddit API client
│   ├── llm_client.py               # LLM provider clients
│   └── storage_client.py           # Storage clients (ChromaDB, etc.)
├── managers/                        # Data management layer
│   ├── campaign_manager.py          # Campaign storage management
│   ├── document_manager.py          # Document metadata management
│   ├── embeddings_manager.py        # Embeddings management
│   └── analytics_manager.py         # Analytics data management
├── storage/                         # Storage layer
│   ├── vector_storage.py            # Vector database operations
│   └── json_storage.py             # JSON file storage
├── utils/                           # Utility functions
│   ├── text_utils.py               # Text processing utilities
│   ├── file_utils.py               # File management utilities
│   ├── validator_utils.py          # Data validation utilities
│   └── web_scraper.py              # Web scraping utilities
└── run_example_workflow.ipynb       # Complete example workflow
```

### Key Design Principles
- **Separation of Concerns**: Clear boundaries between API, business logic, and data layers
- **Unified Services**: Centralized document processing and Reddit operations
- **Modular Architecture**: Easy to extend and maintain
- **Clean Dependencies**: Minimal coupling between components
- **Consistent Naming**: Clear and descriptive naming conventions

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

### 2. Document Ingestion (Multiple Methods)
```python
# Method 1: Direct content
doc_request = DocumentCreateRequest(
    title="Python Best Practices",
    content="Your content here...",
    metadata={"category": "programming"}
)

# Method 2: URL scraping
url_request = DocumentIngestURLRequest(
    url="https://example.com/article",
    title="Article Title",
    organization_id="org-1",
    scraping_method="auto"  # firecrawl, requests, or auto
)

# Method 3: File upload (via API)
# Upload files through the /documents/upload endpoint
```

### 3. Subreddit Discovery
```python
subreddit_request = SubredditDiscoveryRequest(
    document_ids=["doc-1", "doc-2"]
)
```

### 4. Post Discovery
```python
post_request = PostDiscoveryRequest(
    subreddits=["python", "learnpython"],
    max_posts_per_subreddit=10,
    time_filter="day"
)
```

### 5. Response Generation
```python
response_request = ResponseGenerationRequest(
    target_post_ids=["post-1", "post-2"],
    tone=ResponseTone.HELPFUL
)
```

### 6. Response Execution
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
- `POST /api/v1/documents/ingest` - Ingest documents (direct content)
- `POST /api/v1/documents/ingest-url` - **Ingest from URL** (web scraping)
- `POST /api/v1/documents/upload` - Upload file
- `POST /api/v1/documents/query` - Query documents
- `GET /api/v1/documents/organizations/{id}` - Get organization documents

### Analytics & Reporting
- `GET /api/v1/analytics/campaigns/{id}/engagement` - Campaign engagement report
- `GET /api/v1/analytics/organizations/{id}/performance` - Organization performance
- `GET /api/v1/analytics/organizations/{id}/quick-stats` - Quick stats overview
- `GET /api/v1/analytics/platform/overview` - Platform-wide metrics

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
- Firecrawl API key (optional, for enhanced web scraping)

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

## 📓 Example Workflow

### Complete Jupyter Notebook
The repository includes `run_example_workflow.ipynb` - a comprehensive Jupyter notebook that demonstrates the entire workflow:

```bash
# Install Jupyter if needed
pip install jupyter

# Run the example workflow
jupyter notebook run_example_workflow.ipynb
```

### What the Notebook Demonstrates
1. **Setup & Configuration** - Environment validation and service initialization
2. **Organization Setup** - Create and configure an organization
3. **Document Ingestion** - All three methods:
   - Direct content input
   - Simulated file upload
   - URL scraping with web scraper
4. **Campaign Creation** - Create and configure a marketing campaign
5. **Subreddit Discovery** - AI-powered topic extraction and subreddit finding
6. **Post Discovery** - Find relevant posts in target subreddits
7. **Response Generation** - AI-generated contextual responses
8. **Response Execution** - Post responses to Reddit (with safety controls)
9. **Analytics & Reporting** - Comprehensive performance analysis

### Safety Features in Notebook
- **Reddit Posting Control**: `ACTUALLY_POST_TO_REDDIT = False` prevents accidental posting
- **Credential Validation**: Checks for required API keys
- **Error Handling**: Graceful handling of API failures
- **Independent Cells**: Each step can be run independently

## 🌐 Web Scraping Capabilities

### Supported Methods
- **Firecrawl API**: Premium web scraping with clean markdown output
- **BeautifulSoup + Requests**: Fallback method for basic scraping
- **Auto Mode**: Tries Firecrawl first, falls back to BeautifulSoup

### URL Ingestion Example
```python
# Via API
response = requests.post(
    "http://localhost:8000/api/v1/documents/ingest-url",
    json={
        "url": "https://example.com/article",
        "title": "Article Title",
        "organization_id": "org-1",
        "scraping_method": "auto"
    }
)

# Via Service
success, message, doc_id = await document_service.ingest_document_from_url(
    url="https://example.com/article",
    organization_id="org-1",
    title="Article Title",
    scraping_method="auto"
)
```

## 🔒 Safety Features

- **Duplicate Prevention**: Avoids responding to the same author multiple times
- **Relevance Scoring**: AI-powered relevance analysis before responding
- **Manual Approval**: Responses require explicit approval before posting
- **Rate Limiting**: Configurable daily response limits
- **Error Handling**: Comprehensive error tracking and recovery
- **URL Validation**: Validates URLs before scraping
- **Content Filtering**: Ensures scraped content is meaningful

## 📊 Campaign Status Tracking

Campaigns progress through these states:
1. `CREATED` - Campaign initialized
2. `DOCUMENTS_UPLOADED` - Documents selected
3. `SUBREDDITS_DISCOVERED` - Relevant subreddits found
4. `POSTS_FOUND` - Target posts identified
5. `RESPONSES_PLANNED` - Responses generated
6. `RESPONSES_POSTED` - Responses posted to Reddit
7. `COMPLETED` - Campaign finished

## 📈 Analytics & Reporting

### Campaign Analytics
- **Engagement Reports**: Detailed engagement metrics per campaign
- **Performance Tracking**: Success rates, response effectiveness
- **Subreddit Analysis**: Performance breakdown by subreddit
- **Trend Analysis**: Campaign performance over time

### Organization Analytics
- **Comprehensive Reports**: Full organization performance overview
- **Document Statistics**: Document usage and effectiveness
- **Quick Stats**: At-a-glance performance indicators
- **Platform Insights**: AI-generated insights and recommendations

### Platform Analytics
- **Global Metrics**: Platform-wide performance indicators
- **Cross-Organization Trends**: Comparative analysis
- **Usage Statistics**: Platform adoption and activity metrics

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

### URL Ingestion
```python
# Ingest document from URL
url_request = DocumentIngestURLRequest(
    url="https://realpython.com/python-basics/",
    title="Python Basics Tutorial",
    organization_id="org-1",
    scraping_method="auto"
)

response = requests.post(
    "http://localhost:8000/api/v1/documents/ingest-url",
    json=url_request.model_dump()
)
```

### Programmatic Usage
```python
from app.services.campaign_service import CampaignService
from app.models.campaign import CampaignCreateRequest, ResponseTone

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
# Direct content ingestion
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

# URL ingestion
url_response = requests.post(
    "http://localhost:8000/api/v1/documents/ingest-url",
    json={
        "url": "https://example.com/article",
        "title": "Article Title",
        "organization_id": "org-1",
        "scraping_method": "auto"
    }
)
```

### Analytics Usage
```python
# Get campaign engagement report
engagement_report = requests.get(
    f"http://localhost:8000/api/v1/analytics/campaigns/{campaign_id}/engagement"
)

# Get organization performance
performance_report = requests.get(
    f"http://localhost:8000/api/v1/analytics/organizations/{org_id}/performance"
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
6. **Web Scraping Ethics**: Respect robots.txt and website terms of service

## 🔍 Monitoring & Analytics

The system tracks:
- Response success/failure rates
- Community engagement metrics
- Campaign progression
- Error logs and debugging info
- LLM usage and costs
- Vector storage statistics
- Subreddit effectiveness
- Performance trends over time
- Document ingestion statistics
- Web scraping success rates

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the server
- **OpenAPI Spec**: Available at `/openapi.json`
- **Health Checks**: Multiple endpoints for monitoring system health
- **Example Workflow**: Complete Jupyter notebook with step-by-step guide

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

# Test URL ingestion
curl -X POST "http://localhost:8000/api/v1/documents/ingest-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "organization_id": "test-org"}'

# Test campaign creation
curl -X POST "http://localhost:8000/api/v1/campaigns/?organization_id=test-org" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Campaign", "response_tone": "helpful"}'

# Test analytics
curl "http://localhost:8000/api/v1/analytics/platform/overview"
```

### Example Workflow Testing
```bash
# Run the complete example workflow
jupyter notebook run_example_workflow.ipynb

# Or run specific cells interactively
jupyter notebook run_example_workflow.ipynb
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

# Install Jupyter for running examples
pip install jupyter

# Run the application in development mode
cd app
python main.py

# Access API documentation
open http://localhost:8000/docs

# Run example workflow
jupyter notebook run_example_workflow.ipynb
```

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the health check endpoints
3. Run the example workflow notebook
4. Check application logs for detailed error information
5. Create an issue on GitHub with detailed information

## 🔄 Version History

- **v2.2.0**: Added URL ingestion capabilities and complete example workflow
- **v2.1.0**: Added comprehensive analytics and reporting system
- **v2.0.0**: Clean architecture with modular design
- **v1.0.0**: Initial release with basic campaign functionality

---

**Note**: This system is designed for legitimate marketing purposes. Always follow Reddit's community guidelines and terms of service. The example workflow notebook provides a safe way to test all features before using them in production.