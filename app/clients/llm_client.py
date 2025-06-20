"""
LLM provider clients.
"""

import json
import logging
from typing import Optional, Dict, Any, List

from google import genai
from groq import AsyncGroq
from openai import AsyncOpenAI
from langsmith import traceable

from app.core.settings import settings, OpenAIConfig, GoogleConfig, GroqConfig

logger = logging.getLogger(__name__)


def conditional_decorator(decorator, condition):
    """Apply decorator conditionally."""
    def wrapper(func):
        return decorator(func) if condition else func
    return wrapper


class LLMClient:
    """
    Unified LLM client that orchestrates calls to different providers.
    """
    
    def __init__(self):
        """Initialize the LLM client."""
        self.logger = logger
        
        # Provider clients (lazy loading)
        self._openai_client = None
        self._groq_client = None
        self._gemini_client = None
    
    @property
    def openai_client(self) -> AsyncOpenAI:
        """Get OpenAI client (lazy loading)."""
        if not self._openai_client:
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client
    
    @property
    def groq_client(self) -> AsyncGroq:
        """Get Groq client (lazy loading)."""
        if not self._groq_client:
            self._groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._groq_client
    
    @property
    def gemini_client(self):
        """Get Gemini client (lazy loading)."""
        if not self._gemini_client:
            self._gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._gemini_client
    
    def _build_chat_response(
        self,
        content: str,
        usage_metadata: Dict[str, int],
        parse_json: bool = False
    ) -> Dict[str, Any]:
        """Build standardized response format."""
        if parse_json:
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse JSON response")
                content = {"error": "Invalid JSON response"}
        
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content
                    }
                }
            ],
            "usage_metadata": usage_metadata,
        }
    
    # ========================================
    # OPENAI PROVIDER
    # ========================================
    
    async def generate_chat_completion_openai(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = OpenAIConfig.GPT_MODEL,
        temperature: float = OpenAIConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI."""
        
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "OpenAI Chat",
            project_name=project_name or settings.LANGCHAIN_PROJECT,
            metadata={"ls_provider": "OpenAI", "ls_model_name": model}
        ), project_name)
        async def inner_openai_call(messages: Optional[List[Dict[str, str]]] = None):
            try:
                if response_format:
                    response = await self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages or [],
                        response_format=response_format,
                        temperature=temperature
                    )
                else:
                    response = await self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages or [],
                        temperature=temperature
                    )
                
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                
                content = response.choices[0].message.content
                parse_json = bool(response_format)
                
                return self._build_chat_response(
                    content=content, 
                    usage_metadata=usage, 
                    parse_json=parse_json
                )
                
            except Exception as e:
                self.logger.error(f"OpenAI API error: {str(e)}")
                raise
        
        return await inner_openai_call(messages)
    
    # ========================================
    # GROQ PROVIDER
    # ========================================
    
    async def generate_chat_completion_groq(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = GroqConfig.GROQ_MODEL,
        temperature: float = GroqConfig.TEMPERATURE,
        response_format: Optional[Dict] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat completion using Groq."""
        
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "Groq Chat",
            project_name=project_name or settings.LANGCHAIN_PROJECT,
            metadata={"ls_provider": "Groq", "ls_model_name": model}
        ), project_name)
        async def inner_groq_call(messages: Optional[List[Dict[str, str]]] = None):
            try:
                if response_format:
                    response = await self.groq_client.chat.completions.create(
                        model=model,
                        messages=messages or [],
                        response_format=response_format,
                        temperature=temperature
                    )
                else:
                    response = await self.groq_client.chat.completions.create(
                        model=model,
                        messages=messages or [],
                        temperature=temperature
                    )
                
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                
                content = response.choices[0].message.content
                parse_json = bool(response_format)
                
                return self._build_chat_response(
                    content=content, 
                    usage_metadata=usage, 
                    parse_json=parse_json
                )
                
            except Exception as e:
                self.logger.error(f"Groq API error: {str(e)}")
                raise
        
        return await inner_groq_call(messages)
    
    # ========================================
    # GEMINI PROVIDER
    # ========================================
    
    async def generate_chat_completion_gemini(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = GoogleConfig.GEMINI_MODEL,
        temperature: float = GoogleConfig.TEMPERATURE,
        top_p: float = GoogleConfig.TOP_P,
        top_k: int = GoogleConfig.TOP_K,
        max_tokens: int = GoogleConfig.MAX_TOKENS,
        response_format: Optional[Dict] = None,
        response_schema: Optional[Any] = None,
        chat_name: Optional[str] = None,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate chat completion using Gemini."""
        
        @conditional_decorator(traceable(
            run_type="llm",
            name=chat_name or "Gemini Chat",
            project_name=project_name or settings.LANGCHAIN_PROJECT,
            metadata={"ls_provider": "Google", "ls_model_name": model}
        ), project_name)
        async def inner_gemini_call(messages: Optional[List[Dict[str, str]]] = None):
            try:
                # Extract system instructions
                system_instructions = "You are a helpful assistant."
                if messages and messages[0]["role"] == "system":
                    system_instructions = messages[0]["content"]
                
                # Build conversation history
                conversation_history = []
                if messages:
                    for msg in messages:
                        if msg["role"] == "system":
                            continue
                        
                        role = "model" if msg["role"] == "assistant" else "user"
                        conversation_history.append({
                            "role": role,
                            "parts": [{"text": msg["content"]}]
                        })
                
                # Build generation config
                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_output_tokens": max_tokens,
                    "system_instruction": system_instructions,
                }
                
                if response_format:
                    generation_config["response_mime_type"] = "application/json"
                    if response_schema:
                        generation_config["response_schema"] = response_schema
                
                # Generate response
                response = self.gemini_client.models.generate_content(
                    model=model,
                    config=generation_config,
                    contents=conversation_history,
                )
                
                usage = {
                    "input_tokens": response.usage_metadata.prompt_token_count,
                    "output_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
                
                content = response.text
                parse_json = bool(response_format)
                
                return self._build_chat_response(
                    content=content,
                    usage_metadata=usage,
                    parse_json=parse_json
                )
                
            except Exception as e:
                self.logger.error(f"Gemini API error: {str(e)}")
                raise
        
        return await inner_gemini_call(messages)
    
    # ========================================
    # UNIFIED INTERFACE
    # ========================================
    
    async def generate_chat_completion(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        provider: str = "gemini",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using specified provider."""
        if provider == "openai":
            return await self.generate_chat_completion_openai(messages=messages, **kwargs)
        elif provider == "groq":
            return await self.generate_chat_completion_groq(messages=messages, **kwargs)
        elif provider == "gemini":
            return await self.generate_chat_completion_gemini(messages=messages, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")