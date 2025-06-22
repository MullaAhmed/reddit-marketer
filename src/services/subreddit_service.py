"""
Subreddit discovery and ranking service with Haystack RAG integration.
"""

import logging
from typing import List, Tuple

from src.clients.reddit_client import RedditClient
from src.clients.llm_client import LLMClient
from src.storage.vector_storage import VectorStorage
from src.prompts import TOPIC_EXTRACTION_PROMPT, SUBREDDIT_RANKING_PROMPT
from src.utils.text_utils import format_prompt

logger = logging.getLogger(__name__)


class SubredditService:
    """Service for subreddit discovery and ranking with Haystack RAG integration."""
    
    def __init__(
        self, 
        reddit_client: RedditClient, 
        llm_client: LLMClient,
        vector_storage: VectorStorage
    ):
        """Initialize the subreddit service."""
        self.reddit_client = reddit_client
        self.llm_client = llm_client
        self.vector_storage = vector_storage
        self.logger = logger
    
    async def discover_and_rank_subreddits(
        self,
        topics: List[str],
        organization_id: str,
        context_content: str = None,
        use_rag_context: bool = True
    ) -> Tuple[bool, str, List[str]]:
        """Discover and rank subreddits based on topics and Haystack RAG context."""
        try:
            if not topics:
                return False, "No topics provided", []
            
            # If no context provided and RAG is enabled, try to get context from documents
            if not context_content and use_rag_context:
                context_content = await self._get_organization_context(organization_id, topics)
            
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
            
            # Use LLM to rank subreddits by relevance with Haystack context
            if context_content:
                ranked_subreddits = await self._rank_subreddits_with_context(
                    filtered_subreddits, context_content
                )
            else:
                # Fallback: sort by subscriber count
                ranked_subreddits = sorted(
                    filtered_subreddits.keys(),
                    key=lambda x: filtered_subreddits[x]["subscribers"],
                    reverse=True
                )[:10]
            
            method = "haystack_rag_ranking" if context_content else "subscriber_count_fallback"
            self.logger.info(f"Ranked {len(ranked_subreddits)} subreddits using {method}")
            
            return True, f"Found and ranked {len(ranked_subreddits)} subreddits using Haystack RAG", ranked_subreddits
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", []
    
    async def extract_topics_from_documents(
        self,
        organization_id: str,
        document_ids: List[str] = None,
        query: str = None
    ) -> Tuple[bool, str, List[str]]:
        """Extract topics from organization documents using Haystack RAG."""
        try:
            # Get document context using Haystack
            if document_ids:
                # Get specific documents
                context_content = ""
                for doc_id in document_ids:
                    chunks = self.vector_storage.get_document_chunks_by_document_id(
                        org_id=organization_id,
                        document_id=doc_id,
                        query=query
                    )
                    if chunks:
                        doc_content = "\n".join([chunk['content'] for chunk in chunks])
                        context_content += f"\n\n{doc_content}"
            else:
                # Query all documents
                if query:
                    results = self.vector_storage.query_documents(
                        org_id=organization_id,
                        query=query,
                        method="semantic",
                        top_k=10
                    )
                    context_content = "\n\n".join([result["content"] for result in results])
                else:
                    return False, "No document IDs or query provided", []
            
            if not context_content.strip():
                return False, "No content found in documents", []
            
            # Use LLM to extract topics
            prompt = format_prompt(
                TOPIC_EXTRACTION_PROMPT,
                content=context_content
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.generate_chat_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if "error" in response:
                return False, f"LLM error: {response['error']}", []
            
            content = response.get("content", {})
            if isinstance(content, dict) and "topics" in content:
                topics = content["topics"]
                self.logger.info(f"Extracted {len(topics)} topics using Haystack RAG")
                return True, f"Extracted {len(topics)} topics from documents", topics
            
            return False, "Failed to extract topics from LLM response", []
            
        except Exception as e:
            self.logger.error(f"Error extracting topics from documents: {str(e)}")
            return False, f"Error extracting topics: {str(e)}", []
    
    async def _get_organization_context(
        self,
        organization_id: str,
        topics: List[str],
        top_k: int = 5
    ) -> str:
        """Get relevant context from organization documents using Haystack."""
        try:
            # Create a query from topics
            query = " ".join(topics)
            
            # Use Haystack semantic search to get relevant context
            results = self.vector_storage.query_documents(
                org_id=organization_id,
                query=query,
                method="semantic",
                top_k=top_k
            )
            
            if results:
                context_content = "\n\n".join([result["content"] for result in results])
                self.logger.info(f"Retrieved {len(context_content)} characters of context using Haystack")
                return context_content
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error getting organization context: {str(e)}")
            return ""
    
    async def _rank_subreddits_with_context(
        self,
        subreddits: dict,
        context_content: str
    ) -> List[str]:
        """Rank subreddits using LLM with Haystack context."""
        try:
            # Build subreddit list for prompt
            subreddit_list = []
            for name, info in subreddits.items():
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
                return sorted(
                    subreddits.keys(),
                    key=lambda x: subreddits[x]["subscribers"],
                    reverse=True
                )[:10]
            
            # Extract ranked subreddits from LLM response
            content = response.get("content", {})
            if isinstance(content, dict) and "subreddits" in content:
                ranked_subreddits = content["subreddits"][:10]  # Top 10
                return ranked_subreddits
            
            # Fallback if LLM response is malformed
            return list(subreddits.keys())[:10]
            
        except Exception as e:
            self.logger.error(f"Error ranking subreddits with context: {str(e)}")
            # Fallback: return subreddits sorted by subscriber count
            return sorted(
                subreddits.keys(),
                key=lambda x: subreddits[x]["subscribers"],
                reverse=True
            )[:10]