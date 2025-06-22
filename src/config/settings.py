"""
Environment-driven runtime settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM API Keys
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""
    
    # Reddit API
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USERNAME: Optional[str] = None
    REDDIT_PASSWORD: Optional[str] = None
    
    # Storage
    DATA_DIR: str = "data"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()