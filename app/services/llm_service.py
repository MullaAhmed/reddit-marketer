"""
LLM service for AI interactions - Centralized AI operations.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Tuple

from app.core.settings import settings, OpenAIConfig, GoogleConfig, GroqConfig
from app.clients.llm_client import LLMClient

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Centralized prompt templates for consistent AI interactions."""
    
    TOPIC_EXTRACTION = """
    Analyze the following text and extract relevant topics that could be used 
    to find related subreddits on Reddit. Return the topics as a JSON array.
    
    Text: {content}
    
    Return format: {{"topics": ["topic1", "topic2", ...]}}
    """
    
    SUBREDDIT_RANKING = """
    Based on the following content, rank the subreddits by relevance and return the top 10 most relevant ones.
    
    Content: {content}
    
    Subreddits:
    {subreddit_list}
    
    Return format: {{"subreddits": ["subreddit1", "subreddit2", ...]}}
    """
    
    POST_RELEVANCE_ANALYSIS = """
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
    
    REDDIT_RESPONSE_GENERATION = """
    Generate a helpful Reddit response based on the following context and post.
    
    Context about my expertise: {campaign_context}
    
    Post Title: {post_title}
    Post Content: {post_content}
    Subreddit: r/{subreddit}
    
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


class LLMService:
    """
    Service for LLM interactions that orchestrates calls to different providers.
    Centralized location for all AI operations.
    """
    
    def __init__(self, llm_client: LLMClient):
        """Initialize the LLM service."""
        self.llm_client = llm_client
        self.logger = logger
        self.prompts = PromptTemplates()
    
    async def _generate_completion_with_error_handling(
        self,
        prompt: str,
        response_format: str = "json",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate completion with standardized error handling.
        
        Returns:
            Tuple of (success: bool, message: str, result: Dict[str, Any])
        """
        try:
            result = await self.generate_completion(
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model
            )
            
            if "error" in result:
                return False, f"LLM error: {result['error']}", {}
            
            return True, "Success", result
            
        except Exception as e:
            self.logger.error(f"Error in LLM completion: {str(e)}")
            return False, f"LLM service error: {str(e)}", {}
    
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
    
    # ========================================
    # DOMAIN-SPECIFIC AI OPERATIONS
    # ========================================
    
    async def extract_topics_from_content(
        self, 
        content: str
    ) -> Tuple[bool, str, List[str]]:
        """
        Extract topics from content using AI analysis.
        
        Args:
            content: Content to analyze
            
        Returns:
            Tuple of (success, message, topics)
        """
        try:
            prompt = self.prompts.TOPIC_EXTRACTION.format(content=content)
            
            success, message, response = await self._generate_completion_with_error_handling(
                prompt=prompt,
                response_format="json"
            )
            
            if not success:
                return False, message, []
            
            topics = response.get("topics", [])
            
            self.logger.info(f"Extracted {len(topics)} topics from content")
            return True, f"Extracted {len(topics)} topics", topics
            
        except Exception as e:
            self.logger.error(f"Error extracting topics: {str(e)}")
            return False, f"Error extracting topics: {str(e)}", []
    
    async def rank_subreddits_by_relevance(
        self, 
        content: str, 
        subreddit_data: Dict[str, Dict[str, Any]]
    ) -> Tuple[bool, str, List[str]]:
        """
        Use AI to rank subreddits by relevance to content.
        
        Args:
            content: Content to analyze
            subreddit_data: Dictionary of subreddit info
            
        Returns:
            Tuple of (success, message, ranked_subreddits)
        """
        try:
            # Build subreddit list for prompt
            subreddit_list = []
            for name, info in subreddit_data.items():
                subreddit_list.append(f"{name}: {info.get('about', '')}")
            
            prompt = self.prompts.SUBREDDIT_RANKING.format(
                content=content,
                subreddit_list=chr(10).join(subreddit_list)
            )
            
            success, message, response = await self._generate_completion_with_error_handling(
                prompt=prompt,
                response_format="json"
            )
            
            if not success:
                return False, message, list(subreddit_data.keys())
            
            subreddits = response.get("subreddits", [])
            
            self.logger.info(f"Ranked {len(subreddits)} subreddits by relevance")
            return True, f"Ranked {len(subreddits)} subreddits", subreddits
            
        except Exception as e:
            self.logger.error(f"Error ranking subreddits: {str(e)}")
            # Fallback: return all subreddit names
            return False, f"Error ranking subreddits: {str(e)}", list(subreddit_data.keys())
    
    async def analyze_post_relevance(
        self, 
        post_title: str, 
        post_content: str, 
        campaign_context: str,
        subreddit: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Analyze if a post is relevant for the campaign.
        
        Args:
            post_title: Post title
            post_content: Post content
            campaign_context: Campaign context from documents
            subreddit: Subreddit name (optional)
            
        Returns:
            Tuple of (success, message, analysis)
        """
        try:
            prompt = self.prompts.POST_RELEVANCE_ANALYSIS.format(
                campaign_context=campaign_context,
                post_title=post_title,
                post_content=post_content
            )
            
            success, message, response = await self._generate_completion_with_error_handling(
                prompt=prompt,
                response_format="json"
            )
            
            if not success:
                return False, message, {}
            
            # Ensure required fields exist
            analysis = {
                "relevance_score": response.get("relevance_score", 0.0),
                "relevance_reason": response.get("relevance_reason", ""),
                "should_respond": response.get("should_respond", False)
            }
            
            self.logger.debug(f"Analyzed post relevance: {analysis['relevance_score']:.2f}")
            return True, "Post relevance analyzed", analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing post relevance: {str(e)}")
            return False, f"Error analyzing post relevance: {str(e)}", {}
    
    async def generate_reddit_response(
        self, 
        post_title: str, 
        post_content: str, 
        campaign_context: str, 
        tone: str = "helpful",
        subreddit: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generate a response for a Reddit post.
        
        Args:
            post_title: Post title
            post_content: Post content
            campaign_context: Campaign context
            tone: Response tone
            subreddit: Subreddit name
            
        Returns:
            Tuple of (success, message, response_data)
        """
        try:
            prompt = self.prompts.REDDIT_RESPONSE_GENERATION.format(
                campaign_context=campaign_context,
                post_title=post_title,
                post_content=post_content,
                subreddit=subreddit,
                tone=tone
            )
            
            success, message, response = await self._generate_completion_with_error_handling(
                prompt=prompt,
                response_format="json"
            )
            
            if not success:
                return False, message, {}
            
            # Ensure required fields exist
            response_data = {
                "content": response.get("content", ""),
                "confidence": response.get("confidence", 0.0)
            }
            
            self.logger.info(f"Generated response with confidence: {response_data['confidence']:.2f}")
            return True, "Response generated successfully", response_data
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return False, f"Error generating response: {str(e)}", {}