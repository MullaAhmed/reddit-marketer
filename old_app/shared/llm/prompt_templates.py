"""
Centralized prompt templates for consistent AI interactions.
"""

from typing import Dict, Any, List
from enum import Enum


class PromptType(str, Enum):
    """Types of prompts available."""
    TOPIC_EXTRACTION = "topic_extraction"
    SUBREDDIT_RANKING = "subreddit_ranking"
    POST_RELEVANCE = "post_relevance"
    RESPONSE_GENERATION = "response_generation"


class PromptTemplates:
    """
    Centralized prompt templates for all AI interactions.
    """
    
    @staticmethod
    def get_system_prompt(prompt_type: PromptType) -> str:
        """Get system prompt for a specific type."""
        system_prompts = {
            PromptType.TOPIC_EXTRACTION: (
                "You are an expert marketing content analyzer. Your task is to analyze "
                "the provided text and provide a list of related topics to search on reddit."
            ),
            PromptType.SUBREDDIT_RANKING: (
                "You are an expert reddit marketer. Your task is to analyze the provided "
                "text and the list of related subreddits, and filter it down to best suited subreddits."
            ),
            PromptType.POST_RELEVANCE: (
                "You are an expert at analyzing Reddit posts for marketing relevance. "
                "Analyze if the post is relevant for the given campaign context and provide a relevance score."
            ),
            PromptType.RESPONSE_GENERATION: (
                "You are a helpful Reddit user responding to posts. Generate a natural, "
                "helpful response that adds value to the conversation. Do not be overly promotional. "
                "Base your response on the provided context."
            )
        }
        
        return system_prompts.get(prompt_type, "You are a helpful assistant.")
    
    @staticmethod
    def build_topic_extraction_prompt(content: str) -> List[Dict[str, str]]:
        """Build prompt for topic extraction."""
        return [
            {
                "role": "system",
                "content": PromptTemplates.get_system_prompt(PromptType.TOPIC_EXTRACTION)
            },
            {
                "role": "user",
                "content": (
                    f"Analyse the text provided below and return a list of related topics "
                    f"in a JSON object ({{'topics':[...]}}). Here is the content to analyze: {content}"
                )
            }
        ]
    
    @staticmethod
    def build_subreddit_ranking_prompt(
        content: str, 
        subreddit_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Build prompt for subreddit ranking."""
        return [
            {
                "role": "system",
                "content": PromptTemplates.get_system_prompt(PromptType.SUBREDDIT_RANKING)
            },
            {
                "role": "user",
                "content": (
                    f"Analyse the text and list of subreddits provided below and return a list "
                    f"of most relevant subreddits in a JSON object ({{'subreddits':[...]}}). "
                    f"Here is the content to analyze: {content} "
                    f"Here is the list of subreddits: {subreddit_data}"
                )
            }
        ]
    
    @staticmethod
    def build_post_relevance_prompt(
        campaign_context: str,
        post_title: str,
        post_content: str,
        subreddit: str
    ) -> List[Dict[str, str]]:
        """Build prompt for post relevance analysis."""
        return [
            {
                "role": "system",
                "content": PromptTemplates.get_system_prompt(PromptType.POST_RELEVANCE)
            },
            {
                "role": "user",
                "content": (
                    f"Campaign Context: {campaign_context[:1000]}\n\n"
                    f"Post Title: {post_title}\n"
                    f"Post Content: {post_content[:500]}\n"
                    f"Subreddit: r/{subreddit}\n\n"
                    f"Analyze this post and return a JSON object with:\n"
                    f"- relevance_score (0.0 to 1.0)\n"
                    f"- relevance_reason (brief explanation)\n"
                    f"- should_respond (boolean)"
                )
            }
        ]
    
    @staticmethod
    def build_response_generation_prompt(
        campaign_context: str,
        post_title: str,
        post_content: str,
        subreddit: str,
        tone: str
    ) -> List[Dict[str, str]]:
        """Build prompt for response generation."""
        system_prompt = PromptTemplates.get_system_prompt(PromptType.RESPONSE_GENERATION)
        system_prompt += f" Your tone should be {tone}."
        
        return [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": (
                    f"Context about my expertise: {campaign_context[:1000]}\n\n"
                    f"Post Title: {post_title}\n"
                    f"Post Content: {post_content}\n"
                    f"Subreddit: r/{subreddit}\n\n"
                    f"Generate a helpful response that:\n"
                    f"1. Adds value to the conversation\n"
                    f"2. Is natural and not overly promotional\n"
                    f"3. Uses the {tone} tone\n"
                    f"4. Is 1-3 paragraphs long\n\n"
                    f"Return a JSON object with:\n"
                    f"- content (the response text)\n"
                    f"- confidence (0.0 to 1.0 how confident you are this is a good response)"
                )
            }
        ]
    
    @staticmethod
    def build_custom_prompt(
        system_message: str,
        user_message: str,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Build a custom prompt with variable substitution."""
        # Format messages with kwargs
        formatted_system = system_message.format(**kwargs)
        formatted_user = user_message.format(**kwargs)
        
        return [
            {"role": "system", "content": formatted_system},
            {"role": "user", "content": formatted_user}
        ]