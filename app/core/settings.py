"""
Centralized configuration management.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(dotenv_path=".env", override=True)


class OpenAIConfig:
    """OpenAI configuration."""
    GPT_MODEL = "gpt-4o"
    TEMPERATURE = 0.7


class GoogleConfig:
    """Google/Gemini configuration."""
    GEMINI_MODEL = "gemini-2.0-flash"
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 40
    MAX_TOKENS = 8192


class GroqConfig:
    """Groq configuration."""
    GROQ_MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.7


class RedditConfig:
    """Reddit API configuration."""
    DEFAULT_RATE_LIMIT_REQUESTS = 30
    DEFAULT_RATE_LIMIT_PERIOD = 60
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_BASE_DELAY = 2.0
    DEFAULT_USER_AGENT = "python:reddit-marketing-agent:v2.0"


class RAGConfig:
    """RAG system configuration."""
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_TOP_K = 5
    DEFAULT_DOCUMENT_STORE_TYPE = "chroma"
    DEFAULT_EMBEDDING_PROVIDER = "openai"
    DEFAULT_RETRIEVER_TYPE = "semantic"


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict()

    # Application
    PROJECT_NAME: str = "Reddit Marketing AI Agent"
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEEP_SEEK_API_KEY: str = os.getenv("DEEP_SEEK_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    
    # Optional
    LANGCHAIN_PROJECT: Optional[str] = os.getenv("LANGCHAIN_PROJECT")
    
    # RAG settings with defaults
    DOCUMENT_STORE_TYPE: str = os.getenv("DOCUMENT_STORE_TYPE", RAGConfig.DEFAULT_DOCUMENT_STORE_TYPE)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", RAGConfig.DEFAULT_EMBEDDING_PROVIDER)
    RETRIEVER_TYPE: str = os.getenv("RETRIEVER_TYPE", RAGConfig.DEFAULT_RETRIEVER_TYPE)
    MODEL_NAME: str = os.getenv("MODEL_NAME", OpenAIConfig.GPT_MODEL)
    
    # Data directories
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    
    def validate_required_keys(self) -> None:
        """Validate that required API keys are present."""
        required_keys = {
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "GOOGLE_API_KEY": self.GOOGLE_API_KEY
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")


# Global settings instance
settings = Settings()