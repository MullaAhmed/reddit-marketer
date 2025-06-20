"""
LLM service for AI interactions.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.core.config import settings, OpenAIConfig, GoogleConfig, GroqConfig
from app.clients.llm_client import LLMClient

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for LLM interactions that orchestrates calls to different providers.
    """
    
    def __init__(self):
        """Initialize the LLM service."""
        self.llm_client = LLMClient()
        self.logger = logger
    
    async def generate_completion(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            response_format: "text" or "json"
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            model: Model to use (defaults to configured model)
            
        Returns:
            Dict containing the response
        """
        try:
            # Convert prompt to messages format
            messages = [{"role": "user", "content": prompt}]
            
            # Set response format
            format_dict = None
            if response_format == "json":
                format_dict = {"type": "json_object"}
            
            # Generate completion
            response = await self.llm_client.generate_chat_completion_gemini(
                messages=messages,
                temperature=temperature or GoogleConfig.TEMPERATURE,
                max_tokens=max_tokens or GoogleConfig.MAX_TOKENS,
                response_format=format_dict
            )
            
            content = response["choices"][0]["message"]["content"]
                  
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating completion: {str(e)}")
            return {"error": str(e)}
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        response_format: Optional[Dict] = None,
        model: Optional[str] = None,
        provider: str = "gemini"
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using the specified provider.
        
        Args:
            messages: List of message dicts with role and content
            temperature: Temperature for generation
            response_format: Response format specification
            model: Model to use
            provider: LLM provider ("openai", "gemini", "groq")
            
        Returns:
            Dict containing the response
        """
        try:
            if provider == "openai":
                return await self.llm_client.generate_chat_completion_openai(
                    messages=messages,
                    model=model or OpenAIConfig.GPT_MODEL,
                    temperature=temperature or OpenAIConfig.TEMPERATURE,
                    response_format=response_format
                )
            elif provider == "gemini":
                return await self.llm_client.generate_chat_completion_gemini(
                    messages=messages,
                    model=model or GoogleConfig.GEMINI_MODEL,
                    temperature=temperature or GoogleConfig.TEMPERATURE,
                    response_format=response_format
                )
            elif provider == "groq":
                return await self.llm_client.generate_chat_completion_groq(
                    messages=messages,
                    model=model or GroqConfig.GROQ_MODEL,
                    temperature=temperature or GroqConfig.TEMPERATURE,
                    response_format=response_format
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            self.logger.error(f"Error generating chat completion with {provider}: {str(e)}")
            return {"error": str(e)}
    
    async def extract_topics(self, content: str) -> List[str]:
        """Extract topics from content."""
        prompt = f"""
        Analyze the following text and extract 5-10 relevant topics that could be used 
        to find related subreddits on Reddit. Return the topics as a JSON array.
        
        Text: {content}
        
        Return format: {{"topics": ["topic1", "topic2", ...]}}
        """
        
        response = await self.generate_completion(prompt, response_format="json")
        return response.get("topics", [])
    
    async def rank_subreddits(self, content: str, subreddits: Dict[str, Any]) -> List[str]:
        """Rank subreddits by relevance to content."""
        subreddit_list = []
        for name, info in subreddits.items():
            subreddit_list.append(f"r/{name}: {info.get('about', '')[:100]}")
        
        prompt = f"""
        Based on the following content, rank the subreddits by relevance and return the top 10 most relevant ones.
        
        Content: {content}
        
        Subreddits:
        {chr(10).join(subreddit_list)}
        
        Return format: {{"subreddits": ["subreddit1", "subreddit2", ...]}}
        """
        
        response = await self.generate_completion(prompt, response_format="json")
        return response.get("subreddits", [])
    
    async def analyze_post_relevance(
        self, 
        post_title: str, 
        post_content: str, 
        campaign_context: str
    ) -> Dict[str, Any]:
        """Analyze post relevance for campaign."""
        prompt = f"""
        Analyze if this Reddit post is relevant for our marketing campaign and if we should respond.
        
        Campaign Context: {campaign_context}
        
        Post Title: {post_title}
        Post Content: {post_content}
        
        Analyze this post and return a JSON object with:
        - relevance_score (0.0 to 1.0)
        - relevance_reason (brief explanation)
        - should_respond (boolean)
        
        Return format: {{"relevance_score": 0.8, "relevance_reason": "...", "should_respond": true}}
        """
        
        return await self.generate_completion(prompt, response_format="json")
    
    async def generate_reddit_response(
        self, 
        post_title: str, 
        post_content: str, 
        campaign_context: str, 
        tone: str = "helpful"
    ) -> Dict[str, Any]:
        """Generate a Reddit response."""
        prompt = f"""
        Generate a helpful Reddit response based on the following context and post.
        
        Context about the product: {campaign_context}
        
        Post Title: {post_title}
        Post Content: {post_content}
        
        Generate a response that:
        1. Adds value to the conversation
        2. Is natural and not overly promotional
        3. Uses a {tone} tone
        4. Is 1-3 paragraphs long
        
        Return a JSON object with:
        - content (the response text)
        - confidence (0.0 to 1.0 how confident you are this is a good response)
        
        Return format: {{"content": "...", "confidence": 0.8}}
        """
        
        return await self.generate_completion(prompt, response_format="json")