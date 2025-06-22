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
├── core/                            # Core application functionality
│   ├── settings.py                  # Centralized configuration
│   └── dependencies.py              # Service container for dependency injection
├── services/                        # Business logic layer
│   ├── campaign_service.py          # Campaign orchestration
│   ├── document_service.py          # Document processing (RAG)
│   ├── reddit_service.py            # Reddit operations
│   ├── llm_service.py              # LLM interactions
│   ├── analytics_service.py        # Analytics and reporting
│   └── scraper_service.py          # Web scraping service
├── models/                          # Data models
│   ├── campaign.py                  # Campaign-related models
│   ├── document.py                  # Document-related models
│   ├── reddit.py                    # Reddit-related models
│   └── common.py                    # Shared models
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
│   └── validator_utils.py          # Data validation utilities
└── run_example_workflow.ipynb       # Complete example workflow
```

### Key Design Principles
- **Separation of Concerns**: Clear boundaries between business logic and data layers
- **Unified Services**: Centralized document processing and Reddit operations
- **Modular Architecture**: Easy to extend and maintain
- **Clean Dependencies**: Service container for dependency injection
- **Consistent Naming**: Clear and descriptive naming conventions

## 📋 Workflow

### 1. Initialize Services
```python
from app.core.dependencies import service_container

# Get services
campaign_service = service_container.get_campaign_service()
document_service = service_container.get_document_service()
analytics_service = service_container.get_analytics_service()
```

### 2. Campaign Creation
```python
from app.models.campaign import CampaignCreateRequest, ResponseTone

create_request = CampaignCreateRequest(
    name="Python Learning Community Outreach",
    description="Engage with Python learning communities",
    response_tone=ResponseTone.HELPFUL,
    max_responses_per_day=5
)

success, message, campaign = await campaign_service.create_campaign(
    organization_id="org-1",
    request=create_request
)
```

### 3. Document Ingestion (Multiple Methods)
```python
from app.models.document import DocumentCreateRequest, DocumentIngestURLRequest

# Method 1: Direct content
documents = [{
    "title": "Python Best Practices",
    "content": "Your content here...",
    "metadata": {"category": "programming"}
}]

success, message, document_ids = document_service.ingest_documents(
    documents=documents,
    org_id="org-1"
)

# Method 2: URL scraping
success, message, doc_id = await document_service.ingest_document_from_url(
    url="https://example.com/article",
    organization_id="org-1",
    title="Article Title",
    scraping_method="auto"
)
```

### 4. Subreddit Discovery
```python
from app.models.campaign import SubredditDiscoveryRequest

subreddit_request = SubredditDiscoveryRequest(
    document_ids=["doc-1", "doc-2"]
)

success, message, data = await campaign_service.discover_topics(
    campaign_id=campaign.id,
    request=subreddit_request
)
```

### 5. Post Discovery
```python
from app.models.campaign import PostDiscoveryRequest

post_request = PostDiscoveryRequest(
    subreddits=["python", "learnpython"],
    max_posts_per_subreddit=10,
    time_filter="day",
    reddit_credentials=reddit_creds
)

success, message, data = await campaign_service.discover_posts(
    campaign_id=campaign.id,
    request=post_request
)
```

### 6. Response Generation
```python
from app.models.campaign import ResponseGenerationRequest

response_request = ResponseGenerationRequest(
    target_post_ids=["post-1", "post-2"],
    tone=ResponseTone.HELPFUL
)

success, message, data = await campaign_service.generate_responses(
    campaign_id=campaign.id,
    request=response_request
)
```

### 7. Response Execution
```python
from app.models.campaign import ResponseExecutionRequest

execution_request = ResponseExecutionRequest(
    planned_response_ids=["response-1", "response-2"],
    reddit_credentials=reddit_creds
)

success, message, data = await campaign_service.execute_responses(
    campaign_id=campaign.id,
    request=execution_request
)
```

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
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   ```

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
from app.core.dependencies import service_container

document_service = service_container.get_document_service()

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

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

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

### Service Container Usage
```python
from app.core.dependencies import service_container

# Get all services
campaign_service = service_container.get_campaign_service()
document_service = service_container.get_document_service()
reddit_service = service_container.get_reddit_service()
llm_service = service_container.get_llm_service()
analytics_service = service_container.get_analytics_service()
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

success, message, document_ids = document_service.ingest_documents(
    documents=documents,
    org_id="org-1"
)

# URL ingestion
success, message, doc_id = await document_service.ingest_document_from_url(
    url="https://example.com/article",
    organization_id="org-1",
    title="Article Title",
    scraping_method="auto"
)
```

### Campaign Management
```python
from app.models.campaign import CampaignCreateRequest, ResponseTone

# Create campaign
request = CampaignCreateRequest(
    name="My Campaign",
    response_tone=ResponseTone.HELPFUL
)

success, message, campaign = await campaign_service.create_campaign(
    organization_id="org-1",
    request=request
)

# Get campaign status
success, message, campaign = await campaign_service.get_campaign(campaign.id)
```

### Analytics Usage
```python
# Get campaign engagement report
engagement_report = analytics_service.get_campaign_engagement_report(campaign_id)

# Get organization performance
performance_report = analytics_service.get_organization_performance_report(org_id)

# Get quick stats
quick_stats = analytics_service.get_quick_stats(org_id)
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

## 🧪 Testing

### Service Testing
```python
from app.core.dependencies import service_container

# Test document ingestion
document_service = service_container.get_document_service()
success, message, doc_ids = document_service.ingest_documents(
    documents=[{"title": "Test", "content": "Test content"}],
    org_id="test-org"
)

# Test campaign creation
campaign_service = service_container.get_campaign_service()
from app.models.campaign import CampaignCreateRequest, ResponseTone

request = CampaignCreateRequest(
    name="Test Campaign",
    response_tone=ResponseTone.HELPFUL
)

success, message, campaign = await campaign_service.create_campaign(
    organization_id="test-org",
    request=request
)
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

# Run example workflow
jupyter notebook run_example_workflow.ipynb
```

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Review the example workflow notebook
2. Check application logs for detailed error information
3. Create an issue on GitHub with detailed information

## 🔄 Version History

- **v3.0.0**: Removed API layer, pure service-based architecture
- **v2.2.0**: Added URL ingestion capabilities and complete example workflow
- **v2.1.0**: Added comprehensive analytics and reporting system
- **v2.0.0**: Clean architecture with modular design
- **v1.0.0**: Initial release with basic campaign functionality

---

**Note**: This system is designed for legitimate marketing purposes. Always follow Reddit's community guidelines and terms of service. The example workflow notebook provides a safe way to test all features before using them in production.