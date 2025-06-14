import os
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class OpenAIConfig:
    GPT_MODEL = "gpt-4o"
    TEMPERATURE = 0.7

class GoogleConfig:
    GEMINI_MODEL = "gemini-2.0-flash"#"gemini-1.5-flash-8b"
    TEMPERATURE = 0.7
    TOP_P = 0.95
    TOP_K = 40
    MAX_TOKENS = 8192

class GroqConfig:
    GROQ_MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.7


class Settings(BaseSettings):
    model_config = SettingsConfigDict()

    PROJECT_NAME: str = "Reddit Marketer"
    API_BASE_URL: str = "/v1"
   
    # ENVIRONMENT: Literal["dev", "prod"] = os.getenv("ENVIRONMENT", "dev")
 
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    DEEP_SEEK_API_KEY: str = os.getenv("DEEP_SEEK_API_KEY")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY")
    LANGCHAIN_PROJECT: Optional[str] = None
 
    # RAG settings
    DOCUMENT_STORE_TYPE: str = os.environ.get("DOCUMENT_STORE_TYPE", "in_memory")
    EMBEDDING_PROVIDER: str = os.environ.get("EMBEDDING_PROVIDER", "openai")
    RETRIEVER_TYPE: str = os.environ.get("RETRIEVER_TYPE", "semantic")
    MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")
    

settings = Settings()