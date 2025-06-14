# RAG API

A FastAPI application for Retrieval Augmented Generation (RAG) using the Haystack framework.

## Features

- Document indexing and management
- Direct RAG querying
- Conversational RAG with tools
- Document organization and filtering using RAG IDs
- Flexible configuration for different embedding models and document stores

## Tech Stack

- FastAPI: Web framework
- Haystack: RAG pipeline framework
- OpenAI: Embeddings and LLM
- SentenceTransformers: Alternative embeddings
- Chroma: Vector database (optional)

## Project Structure

```
app/
├── api/                # API layer
│   ├── endpoints/      # API routes
│   └── api.py          # API router
├── core/               # Core application code
│   └── config.py       # Application settings
├── models/             # RAG models
│   ├── document_stores.py
│   ├── embedders.py
│   ├── retrievers.py
│   ├── llm.py
│   ├── indexing.py
│   ├── rag_pipeline.py
│   ├── conversation.py
│   └── rag_system.py   # Main RAG system
├── schemas/            # Pydantic models
│   ├── document.py
│   ├── rag.py
│   └── chat.py
├── services/           # Business logic
│   └── rag_service.py  # RAG service layer
└── main.py             # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key

### Installation

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in your OpenAI API key.

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Documents

- `POST /api/v1/documents/` - Index a single document
- `POST /api/v1/documents/batch` - Index multiple documents
- `POST /api/v1/documents/pdf` - Ingest and process a PDF file
- `POST /api/v1/documents/url` - Ingest content from a URL

### RAG

- `POST /api/v1/rag/query` - Query the RAG system directly

### Chat

- `GET /api/v1/chat/?rag_id={rag_id}` - Web interface for chatting with the RAG system (optional rag_id query parameter)
- `GET /api/v1/chat/widget?rag_id={rag_id}` - Embeddable chat widget for integration into other websites (optional rag_id query parameter)
- `POST /api/v1/chat/message` - Send a message to the chat system (API endpoint, requires rag_id)
- `POST /api/v1/chat/reset` - Reset the chat history (API endpoint, requires rag_id)

## Configuration

The application can be configured using environment variables:

- `OPENAI_API_KEY` - Your OpenAI API key
- `DOCUMENT_STORE_TYPE` - Type of document store (in_memory or chroma)
- `EMBEDDING_PROVIDER` - Provider for embeddings (openai or sentence_transformers)
- `RETRIEVER_TYPE` - Type of retriever (semantic or keyword-based)
- `MODEL_NAME` - Name of the LLM model (e.g., gpt-4o-mini)

## License

MIT
