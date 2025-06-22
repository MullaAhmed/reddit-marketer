# Reddit Marketing AI Agent - Clean Implementation

A simplified, clean implementation of the Reddit Marketing AI Agent that focuses on core functionality with enhanced post and comment analysis.

## 🚀 Features

- **Document Ingestion**: Support for direct content and URL scraping
- **Subreddit Discovery**: AI-powered subreddit finding and ranking
- **Enhanced Post Analysis**: Fetches posts AND comments, then intelligently decides where to respond
- **Smart Response Generation**: AI-generated contextual responses
- **Real-time Analytics**: Fetches latest karma and engagement metrics from Reddit
- **Clean Architecture**: Simple, modular design that's easy to understand and extend

## 🏗️ Architecture

```
src/
├── config/
│   └── settings.py           # Environment-driven configuration
├── models/
│   ├── common.py             # Shared utilities (ID generation, timestamps)
│   ├── document.py           # Document data models
│   └── reddit.py             # Reddit data models (posts, comments, responses)
├── prompts.py                # Centralized prompt templates
├── clients/
│   ├── reddit_client.py      # Reddit API operations
│   ├── llm_client.py         # Multi-provider LLM client
│   └── embedding_client.py   # Text embedding generation
├── storage/
│   ├── vector_storage.py     # ChromaDB vector storage
│   └── json_storage.py       # Simple JSON file storage
├── services/
│   ├── ingestion_service.py  # Document processing and storage
│   ├── subreddit_service.py  # Subreddit discovery and ranking
│   ├── posting_service.py    # Enhanced post/comment analysis and response generation
│   └── analytics_service.py  # Real-time engagement analytics
└── utils/
    ├── text_utils.py         # Text processing utilities
    └── file_utils.py         # File handling utilities
```

## 🔧 Key Enhancements

### Enhanced Post Analysis
The `posting_service.py` now includes sophisticated post and comment analysis:

1. **Fetches Complete Context**: Gets both the main post and all comments
2. **Intelligent Target Selection**: Uses AI to decide whether to:
   - Comment on the main post
   - Reply to a specific comment
3. **Context-Aware Responses**: Generates responses based on the chosen target and relevant document context

### Real-time Analytics
The `analytics_service.py` fetches live metrics from Reddit:
- Current karma scores for posts and comments
- Latest comment counts
- Engagement trends over time

## 📋 Workflow

### 1. Document Ingestion
```python
success, message, doc_id = await ingestion_service.ingest_document(
    content="Your content here...",
    title="Document Title",
    organization_id="your-org-id"
)
```

### 2. Subreddit Discovery
```python
success, message, subreddits = await subreddit_service.discover_and_rank_subreddits(
    topics=["python", "programming"],
    organization_id="your-org-id",
    context_content="Your expertise context..."
)
```

### 3. Enhanced Post Analysis and Response Generation
```python
success, message, response_data = await posting_service.analyze_and_generate_response(
    post_id="reddit_post_id",
    organization_id="your-org-id",
    tone="helpful"
)
```

This method:
- Fetches the post and all its comments
- Analyzes the entire conversation context
- Decides the best engagement point (post or specific comment)
- Generates a contextual response

### 4. Response Posting
```python
success, message, result = await posting_service.post_approved_response(
    target_id=response_data["target"]["target_id"],
    response_type=response_data["target"]["response_type"],
    response_content=response_data["response"]["content"]
)
```

### 5. Real-time Analytics
```python
report = await analytics_service.get_engagement_report("your-org-id")
```

## 🛠️ Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
GROQ_API_KEY=your_groq_key
FIRECRAWL_API_KEY=your_firecrawl_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
DATA_DIR=data
```

3. Run the example:
```bash
python example_usage.py
```

## 🔍 Key Components

### PostingService.analyze_and_generate_response()
This is the core method that orchestrates the enhanced workflow:

1. **Fetch Post Data**: Gets post title, content, author, etc.
2. **Fetch Comments**: Retrieves all comments on the post
3. **Get Context**: Finds relevant document chunks based on post content
4. **Select Target**: Uses AI to decide where to respond (post vs. specific comment)
5. **Generate Response**: Creates contextual response for the selected target

### Analytics with Real-time Fetching
The analytics service now fetches live data from Reddit:
- Current karma scores
- Latest comment counts
- Engagement metrics over time

### Simplified Storage
- **Vector Storage**: ChromaDB for document embeddings and semantic search
- **JSON Storage**: Simple file-based storage for logs and metadata

## 🎯 Response Target Selection

The AI analyzes the post and comments to decide the best engagement strategy:

```json
{
  "target_id": "comment_abc123",
  "response_type": "comment_reply",
  "target_content": "The specific comment content we're responding to",
  "reasoning": "This comment asks a specific question about Python that matches our expertise"
}
```

## 📊 Analytics Features

- **Engagement Tracking**: Real-time karma and comment metrics
- **Response Analysis**: Success rates and performance tracking
- **Historical Data**: Posting history with detailed logs
- **Live Updates**: Fetches current scores from Reddit API

## 🔒 Safety Features

- **Manual Approval**: All responses require explicit approval before posting
- **Error Logging**: Comprehensive error tracking and recovery
- **Rate Limiting**: Respects Reddit API rate limits
- **Context Validation**: Ensures responses are relevant and helpful

## 📝 Example Usage

See `example_usage.py` for a complete workflow demonstration that shows:
- Document ingestion
- Subreddit discovery
- Post analysis with comment fetching
- Response generation with target selection
- Real-time analytics

## 🤝 Contributing

This clean implementation focuses on:
- **Simplicity**: Easy to understand and modify
- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy to add new features
- **Maintainability**: Clean code with good documentation

The architecture is designed to be straightforward while providing powerful functionality for Reddit marketing automation.