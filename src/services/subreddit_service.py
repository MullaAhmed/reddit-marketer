"""
Subreddit discovery and ranking service.
"""

import logging
from typing import List, Tuple

from src.clients.reddit_client import RedditClient
from src.clients.llm_client import LLMClient
from src.prompts import TOPIC_EXTRACTION_PROMPT, SUBREDDIT_RANKING_PROMPT
from src.utils.text_utils import format_prompt

logger = logging.getLogger(__name__)


class SubredditService:
    """Service for subreddit discovery and ranking."""
    
    def __init__(self, reddit_client: RedditClient, llm_client: LLMClient):
        """Initialize the subreddit service."""
        self.reddit_client = reddit_client
        self.llm_client = llm_client
        self.logger = logger
    
    async def discover_and_rank_subreddits(
        self,
        topics: List[str],
        organization_id: str,
        context_content: str
    ) -> Tuple[bool, str, List[str]]:
        """Discover and rank subreddits based on topics and context."""
        try:
            if not topics:
                return False, "No topics provided", []
            
            # Search for subreddits for each topic
            all_subreddits = {}
            
            async with self.reddit_client:
                for topic in topics:
                    try:
                        subreddits = await self.reddit_client.search_subreddits(topic, limit=10)
                        for subreddit in subreddits:
                            name = subreddit["name"]
                            if name not in all_subreddits:
                                all_subreddits[name] = {
                                    "subscribers": subreddit["subscribers"],
                                    "description": subreddit["description"]
                                }
                    except Exception as e:
                        self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(e)}")
                        continue
            
            if not all_subreddits:
                return False, "No subreddits found", []
            
            # Filter by minimum subscribers (10,000)
            filtered_subreddits = {
                name: info for name, info in all_subreddits.items()
                if info["subscribers"] >= 10000
            }
            
            if not filtered_subreddits:
                return False, "No subreddits meet minimum subscriber criteria", []
            
            # Use LLM to rank subreddits by relevance
            subreddit_list = []
            for name, info in filtered_subreddits.items():
                subreddit_list.append(f"{name}: {info['description']}")
            
            prompt = format_prompt(
                SUBREDDIT_RANKING_PROMPT,
                content=context_content,
                subreddit_list="\n".join(subreddit_list)
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.generate_chat_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if "error" in response:
                # Fallback: return subreddits sorted by subscriber count
                ranked_subreddits = sorted(
                    filtered_subreddits.keys(),
                    key=lambda x: filtered_subreddits[x]["subscribers"],
                    reverse=True
                )[:10]
                return True, f"Found {len(ranked_subreddits)} subreddits (fallback ranking)", ranked_subreddits
            
            # Extract ranked subreddits from LLM response
            content = response.get("content", {})
            if isinstance(content, dict) and "subreddits" in content:
                ranked_subreddits = content["subreddits"][:10]  # Top 10
                return True, f"Found and ranked {len(ranked_subreddits)} subreddits", ranked_subreddits
            
            # Fallback if LLM response is malformed
            ranked_subreddits = list(filtered_subreddits.keys())[:10]
            return True, f"Found {len(ranked_subreddits)} subreddits", ranked_subreddits
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", []