# Examples

This folder contains practical examples demonstrating how to use the Reddit Marketing AI Agent system.

## 📁 Structure

- **`api/`** - Examples using the REST API endpoints
- **`base/`** - Examples using the base classes directly

## 🚀 Getting Started

1. Ensure the main application is running:
   ```bash
   cd app
   python main.py
   ```

2. Set up your environment variables in `.env`:
   ```env
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   ```

3. Install required dependencies:
   ```bash
   pip install requests python-dotenv
   ```

## 📋 Examples Overview

### Individual Subsystem Examples
- **Document Management**: Ingest and query documents
- **Subreddit Discovery**: Find relevant subreddits
- **Campaign Management**: Create and manage campaigns
- **Reddit Operations**: Discover posts and generate responses
- **LLM Integration**: Direct LLM interactions

### Complete Workflow Examples
- **End-to-End Campaign**: Full campaign workflow from document ingestion to response posting
- **Automated Marketing**: Complete automation example with error handling

## 🔧 Configuration

Each example includes configuration options and can be customized for your specific use case.

## ⚠️ Important Notes

- Examples use test data and mock Reddit credentials
- Always review generated responses before posting to Reddit
- Respect Reddit's API terms and community guidelines
- Use appropriate rate limiting in production