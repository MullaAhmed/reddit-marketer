"""
LLM client for chat completions.
"""

import json
import logging
from typing import List, Dict, Any

from openai import AsyncOpenAI
from groq import AsyncGroq
from google import genai

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client for different providers."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.logger = logger
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
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "gemini",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using specified provider."""
        try:
            if provider == "openai":
                return await self._generate_chat_completion_openai(messages, **kwargs)
            elif provider == "groq":
                return await self._generate_chat_completion_groq(messages, **kwargs)
            elif provider == "gemini":
                return await self._generate_chat_completion_gemini(messages, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            self.logger.error(f"Error generating chat completion with {provider}: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_chat_completion_openai(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using OpenAI."""
        try:
            response_format = kwargs.get("response_format")
            temperature = kwargs.get("temperature", 0.7)
            model = kwargs.get("model", "gpt-4o")
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if response_format:
                completion_kwargs["response_format"] = response_format
            
            response = await self.openai_client.chat.completions.create(**completion_kwargs)
            
            content = response.choices[0].message.content
            
            # Parse JSON if requested
            if response_format and response_format.get("type") == "json_object":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON response from OpenAI")
                    return {"error": "Invalid JSON response"}
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_chat_completion_groq(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Groq."""
        try:
            response_format = kwargs.get("response_format")
            temperature = kwargs.get("temperature", 0.7)
            model = kwargs.get("model", "llama-3.3-70b-versatile")
            
            completion_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if response_format:
                completion_kwargs["response_format"] = response_format
            
            response = await self.groq_client.chat.completions.create(**completion_kwargs)
            
            content = response.choices[0].message.content
            
            # Parse JSON if requested
            if response_format and response_format.get("type") == "json_object":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON response from Groq")
                    return {"error": "Invalid JSON response"}
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            self.logger.error(f"Groq API error: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_chat_completion_gemini(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Gemini."""
        try:
            response_format = kwargs.get("response_format")
            temperature = kwargs.get("temperature", 0.7)
            model = kwargs.get("model", "gemini-2.0-flash")
            
            # Extract system instructions
            system_instructions = "You are a helpful assistant."
            if messages and messages[0]["role"] == "system":
                system_instructions = messages[0]["content"]
            
            # Build conversation history
            conversation_history = []
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
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "system_instruction": system_instructions,
            }
            
            if response_format and response_format.get("type") == "json_object":
                generation_config["response_mime_type"] = "application/json"
            
            # Generate response
            response = self.gemini_client.models.generate_content(
                model=model,
                config=generation_config,
                contents=conversation_history,
            )
            
            content = response.text
            
            # Parse JSON if requested
            if response_format and response_format.get("type") == "json_object":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    self.logger.error("Failed to parse JSON response from Gemini")
                    return {"error": "Invalid JSON response"}
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            return {"error": str(e)}