"""
Enhanced posting service with Haystack RAG integration.
"""

import logging
from typing import Tuple, Optional, Dict, Any, List

from src.clients.reddit_client import RedditClient
from src.clients.llm_client import LLMClient
from src.storage.vector_storage import VectorStorage
from src.storage.json_storage import JsonStorage
from src.models.reddit import PostInfo, CommentInfo, ResponseTarget, GeneratedResponse
from src.models.common import generate_id, get_current_timestamp
from src.prompts import POST_COMMENT_SELECTION_PROMPT, REDDIT_RESPONSE_GENERATION_PROMPT
from src.utils.text_utils import format_prompt

logger = logging.getLogger(__name__)


class PostingService:
    """Enhanced service for analyzing posts/comments and generating responses with Haystack RAG."""
    
    def __init__(
        self,
        reddit_client: RedditClient,
        llm_client: LLMClient,
        vector_storage: VectorStorage,
        json_storage: JsonStorage
    ):
        """Initialize the posting service."""
        self.reddit_client = reddit_client
        self.llm_client = llm_client
        self.vector_storage = vector_storage
        self.json_storage = json_storage
        self.logger = logger
        
        # Initialize storage files
        self.json_storage.init_file("posted_responses.json", [])
    
    async def analyze_and_generate_response(
        self,
        post_id: str,
        organization_id: str,
        tone: str = "helpful"
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Analyze post and comments, decide where to respond, and generate response using Haystack RAG.
        
        This method uses Haystack for intelligent context retrieval and response generation.
        """
        try:
            async with self.reddit_client:
                # Step 1: Fetch post information
                post_info = await self.reddit_client.get_post_info(post_id)
                
                # Step 2: Fetch all comments for the post
                comments = await self.reddit_client.get_post_comments(post_id, limit=50)
                
                # Step 3: Create structured data for analysis
                post_data = PostInfo(
                    id=post_info["id"],
                    title=post_info["title"],
                    content=post_info["content"],
                    author=post_info["author"],
                    subreddit=post_info["subreddit"],
                    score=post_info["score"],
                    num_comments=post_info["num_comments"],
                    created_utc=post_info["created_utc"],
                    permalink=post_info["permalink"],
                    comments=[CommentInfo(**comment) for comment in comments]
                )
                
                # Step 4: Get relevant context using Haystack semantic search
                search_text = f"{post_data.title} {post_data.content}"
                context_chunks = await self._get_relevant_context_haystack(organization_id, search_text)
                context_content = "\n\n".join([chunk["content"] for chunk in context_chunks])
                
                if not context_content.strip():
                    return False, "No relevant context found for this post", None
                
                # Step 5: Use LLM to decide where to respond
                target = await self._select_response_target(post_data, context_content)
                if not target:
                    return False, "No suitable response target identified", None
                
                # Step 6: Generate the actual response
                response = await self._generate_response(
                    target=target,
                    context_content=context_content,
                    subreddit=post_data.subreddit,
                    tone=tone
                )
                
                if not response:
                    return False, "Failed to generate response", None
                
                # Step 7: Return the complete response data
                result = {
                    "post_id": post_id,
                    "target": target.model_dump(),
                    "response": response.model_dump(),
                    "context_chunks_used": len(context_chunks),
                    "subreddit": post_data.subreddit,
                    "rag_method": "haystack_semantic_search"
                }
                
                self.logger.info(f"Generated response for {target.response_type} on post {post_id} using Haystack RAG")
                return True, f"Generated {target.response_type} response using Haystack RAG", result
                
        except Exception as e:
            self.logger.error(f"Error analyzing and generating response for post {post_id}: {str(e)}")
            return False, f"Error analyzing post: {str(e)}", None
    
    async def post_approved_response(
        self,
        response_type: str,
        response_content: str,
        target_id: Optional[str] = None,
        target_url: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Post an approved response to Reddit.
        
        Args:
            target_id: ID of the post or comment to respond to
            response_type: "post_comment" or "comment_reply"
            response_content: The response text to post
        """
        try:

            async with self.reddit_client:
                if response_type == "post_comment":
                    result = await self.reddit_client.add_comment_to_post(response_content, target_id, target_url)
                elif response_type == "comment_reply":
                    result = await self.reddit_client.reply_to_comment(response_content, target_id, target_url)
                else:
                    return False, f"Invalid response type: {response_type}", None
                
                # Log the posted response
                log_entry = {
                    "id": generate_id(),
                    "target_id": target_id,
                    "response_type": response_type,
                    "response_content": response_content,
                    "posted_at": get_current_timestamp(),
                    "reddit_response": result,
                    "success": True,
                    "rag_enabled": True
                }
                
                self.json_storage.update_item("posted_responses.json", log_entry)
                
                self.logger.info(f"Successfully posted {response_type} to {target_id}")
                return True, f"Successfully posted {response_type}", result
                
        except Exception as e:
            # Log the failed attempt
            log_entry = {
                "id": generate_id(),
                "target_id": target_id,
                "response_type": response_type,
                "response_content": response_content,
                "posted_at": get_current_timestamp(),
                "error": str(e),
                "success": False,
                "rag_enabled": True
            }
            
            self.json_storage.update_item("posted_responses.json", log_entry)
            
            self.logger.error(f"Error posting {response_type} to {target_id}: {str(e)}")
            return False, f"Error posting response: {str(e)}", None
    
    async def _get_relevant_context_haystack(
        self,
        organization_id: str,
        search_text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant context chunks using Haystack semantic search."""
        try:
            # Use Haystack vector storage for semantic search
            results = self.vector_storage.query_documents(
                org_id=organization_id,
                query=search_text,
                method="semantic",
                top_k=top_k
            )
            
            self.logger.info(f"Retrieved {len(results)} relevant chunks using Haystack semantic search")
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting relevant context with Haystack: {str(e)}")
            return []
    
    async def _select_response_target(
        self,
        post_data: PostInfo,
        context_content: str
    ) -> Optional[ResponseTarget]:
        """Use LLM to select the best response target (post or specific comment)."""
        try:
            # Format comments for LLM analysis
            comments_text = ""
            if post_data.comments:
                comments_text = "\n\n".join([
                    f"Comment by {comment.author}: {comment.body}"
                    for comment in post_data.comments[:10]  # Limit to top 10 comments
                ])
            else:
                comments_text = "No comments yet."
            
            # Create prompt for target selection
            prompt = format_prompt(
                POST_COMMENT_SELECTION_PROMPT,
                campaign_context=context_content,
                post_title=post_data.title,
                post_content=post_data.content,
                comments_text=comments_text
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.generate_chat_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if "error" in response:
                self.logger.error(f"LLM error in target selection: {response['error']}")
                return None
            
            content = response.get("content", {})
            if not isinstance(content, dict):
                return None
            
            # Create ResponseTarget object
            target = ResponseTarget(
                target_id= post_data.id,
                response_type=content.get("response_type", "post_comment"),
                target_content=content.get("target_content", post_data.content),
                reasoning=content.get("reasoning", "Default selection")
            )
            
            return target
            
        except Exception as e:
            self.logger.error(f"Error selecting response target: {str(e)}")
            return None
    
    async def _generate_response(
        self,
        target: ResponseTarget,
        context_content: str,
        subreddit: str,
        tone: str
    ) -> Optional[GeneratedResponse]:
        """Generate the actual response content using LLM with Haystack context."""
        try:
            prompt = format_prompt(
                REDDIT_RESPONSE_GENERATION_PROMPT,
                campaign_context=context_content,
                target_content=target.target_content,
                response_type=target.response_type,
                subreddit=subreddit,
                tone=tone
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.generate_chat_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            if "error" in response:
                self.logger.error(f"LLM error in response generation: {response['error']}")
                return None
            
            content = response.get("content", {})
            if not isinstance(content, dict):
                return None
            
            # Create GeneratedResponse object
            generated_response = GeneratedResponse(
                content=content.get("content", ""),
                target=target,
                confidence=content.get("confidence", 0.0),
                context_used=[context_content[:100] + "..."]  # Truncated for logging
            )
            
            return generated_response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return None