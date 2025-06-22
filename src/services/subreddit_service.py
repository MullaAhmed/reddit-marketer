"""
Subreddit discovery and ranking service with Haystack RAG integration and parallelization.
"""

import asyncio
import logging
from typing import List, Tuple

from src.clients.reddit_client import RedditClient
from src.clients.llm_client import LLMClient
from src.storage.vector_storage import VectorStorage
from src.prompts import TOPIC_EXTRACTION_PROMPT, SUBREDDIT_RANKING_PROMPT
from src.utils.text_utils import format_prompt

logger = logging.getLogger(__name__)


class SubredditService:
    """Service for subreddit discovery and ranking with Haystack RAG integration and parallelization."""
    
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
        """Discover and rank subreddits based on topics and Haystack RAG context with parallelization."""
        try:
            if not topics:
                return False, "No topics provided", []
            
            # If no context provided and RAG is enabled, try to get context from documents
            if not context_content and use_rag_context:
                context_content = await self._get_organization_context(organization_id, topics)
            
            # PARALLELIZATION: Search for subreddits for all topics concurrently
            all_subreddits = {}
            
            async with self.reddit_client:
                # Create tasks for parallel subreddit searching
                search_tasks = []
                for topic in topics:
                    task = asyncio.create_task(
                        self._search_subreddits_for_topic(topic),
                        name=f"search_subreddits_{topic}"
                    )
                    search_tasks.append((topic, task))
                
                # Execute all searches concurrently
                self.logger.info(f"Starting parallel subreddit search for {len(topics)} topics")
                results = await asyncio.gather(
                    *[task for _, task in search_tasks], 
                    return_exceptions=True
                )
                
                # Process results
                for i, (topic, _) in enumerate(search_tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(result)}")
                        continue
                    
                    # Merge subreddit results
                    for name, info in result.items():
                        if name not in all_subreddits:
                            all_subreddits[name] = info
            
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
            
            method = "haystack_rag_ranking_parallel" if context_content else "subscriber_count_fallback"
            self.logger.info(f"Ranked {len(ranked_subreddits)} subreddits using {method}")
            
            return True, f"Found and ranked {len(ranked_subreddits)} subreddits using parallel Haystack RAG", ranked_subreddits
            
        except Exception as e:
            self.logger.error(f"Error discovering subreddits: {str(e)}")
            return False, f"Error discovering subreddits: {str(e)}", []
    
    async def _search_subreddits_for_topic(self, topic: str) -> dict:
        """Search subreddits for a single topic (used for parallelization)."""
        try:
            subreddits = await self.reddit_client.search_subreddits(topic, limit=10)
            result = {}
            for subreddit in subreddits:
                name = subreddit["name"]
                result[name] = {
                    "subscribers": subreddit["subscribers"],
                    "description": subreddit["description"]
                }
            return result
        except Exception as e:
            self.logger.warning(f"Error searching subreddits for topic '{topic}': {str(e)}")
            return {}
    
    async def extract_topics_from_documents(
        self,
        organization_id: str,
        document_ids: List[str] = None,
        query: str = None
    ) -> Tuple[bool, str, List[str]]:
        """Extract topics from organization documents using Haystack RAG with parallelization."""
        try:
            # PARALLELIZATION: Get document context using parallel chunk retrieval
            if document_ids:
                # Create tasks for parallel document chunk retrieval
                chunk_tasks = []
                for doc_id in document_ids:
                    task = asyncio.create_task(
                        self._get_document_chunks_async(organization_id, doc_id, query),
                        name=f"get_chunks_{doc_id}"
                    )
                    chunk_tasks.append(task)
                
                # Execute all chunk retrievals concurrently
                self.logger.info(f"Starting parallel chunk retrieval for {len(document_ids)} documents")
                chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
                
                # Combine all chunks
                context_content = ""
                for i, result in enumerate(chunk_results):
                    if isinstance(result, Exception):
                        self.logger.warning(f"Error getting chunks for document {document_ids[i]}: {str(result)}")
                        continue
                    
                    if result:
                        doc_content = "\n".join([chunk['content'] for chunk in result])
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
                self.logger.info(f"Extracted {len(topics)} topics using parallel Haystack RAG")
                return True, f"Extracted {len(topics)} topics from documents using parallel processing", topics
            
            return False, "Failed to extract topics from LLM response", []
            
        except Exception as e:
            self.logger.error(f"Error extracting topics from documents: {str(e)}")
            return False, f"Error extracting topics: {str(e)}", []
    
    async def _get_document_chunks_async(
        self,
        organization_id: str,
        document_id: str,
        query: str = None
    ) -> List[dict]:
        """Get document chunks asynchronously (wrapper for sync method)."""
        try:
            # Run the synchronous vector storage operation in a thread pool
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                self.vector_storage.get_document_chunks_by_document_id,
                organization_id,
                document_id,
                query
            )
            return chunks
        except Exception as e:
            self.logger.error(f"Error getting chunks for document {document_id}: {str(e)}")
            return []
    
    async def _get_organization_context(
        self,
        organization_id: str,
        topics: List[str],
        top_k: int = 5
    ) -> str:
        """Get relevant context from organization documents using Haystack with async wrapper."""
        try:
            # Create a query from topics
            query = " ".join(topics)
            
            # Use async wrapper for vector storage query
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._query_documents_sync,
                organization_id,
                query,
                top_k
            )
            
            if results:
                context_content = "\n\n".join([result["content"] for result in results])
                self.logger.info(f"Retrieved {len(context_content)} characters of context using async Haystack")
                return context_content
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error getting organization context: {str(e)}")
            return ""
    
    def _query_documents_sync(
        self,
        organization_id: str,
        query: str,
        top_k: int
    ) -> List[dict]:
        """Synchronous wrapper for vector storage query (used with run_in_executor)."""
        return self.vector_storage.query_documents(
            org_id=organization_id,
            query=query,
            method="semantic",
            top_k=top_k
        )
    
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
    
    async def discover_subreddits_batch(
        self,
        topic_batches: List[List[str]],
        organization_id: str,
        use_rag_context: bool = True
    ) -> Tuple[bool, str, dict]:
        """
        Discover subreddits for multiple topic batches in parallel.
        
        This method allows processing multiple sets of topics concurrently,
        useful for large-scale subreddit discovery operations.
        """
        try:
            if not topic_batches:
                return False, "No topic batches provided", {}
            
            # Create tasks for parallel batch processing
            batch_tasks = []
            for i, topics in enumerate(topic_batches):
                task = asyncio.create_task(
                    self.discover_and_rank_subreddits(
                        topics=topics,
                        organization_id=organization_id,
                        use_rag_context=use_rag_context
                    ),
                    name=f"discover_batch_{i}"
                )
                batch_tasks.append((i, topics, task))
            
            # Execute all batch discoveries concurrently
            self.logger.info(f"Starting parallel subreddit discovery for {len(topic_batches)} topic batches")
            results = await asyncio.gather(
                *[task for _, _, task in batch_tasks],
                return_exceptions=True
            )
            
            # Process results
            all_results = {}
            successful_batches = 0
            
            for i, (batch_idx, topics, _) in enumerate(batch_tasks):
                result = results[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Error processing batch {batch_idx}: {str(result)}")
                    all_results[f"batch_{batch_idx}"] = {
                        "topics": topics,
                        "success": False,
                        "error": str(result),
                        "subreddits": []
                    }
                    continue
                
                success, message, subreddits = result
                all_results[f"batch_{batch_idx}"] = {
                    "topics": topics,
                    "success": success,
                    "message": message,
                    "subreddits": subreddits
                }
                
                if success:
                    successful_batches += 1
            
            return True, f"Processed {len(topic_batches)} batches, {successful_batches} successful", all_results
            
        except Exception as e:
            self.logger.error(f"Error in batch subreddit discovery: {str(e)}")
            return False, f"Error in batch discovery: {str(e)}", {}