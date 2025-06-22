"""
Environment-driven runtime settings with Haystack configuration.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(".env",override=True)

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY")
    
   
    # Storage
    DATA_DIR: str = "data"
    
    # Haystack/RAG Configuration
    DOCUMENT_STORE_TYPE: str = "chroma"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_PROVIDER: str = "openai"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


# Global settings instance
settings = Settings()