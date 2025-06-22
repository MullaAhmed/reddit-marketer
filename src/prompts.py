"""
Central store for all prompt templates.
"""

TOPIC_EXTRACTION_PROMPT = """
Analyze the following content and extract relevant topics that could be used 
to find related subreddits on Reddit. Return the topics as a JSON array.

Content: {content}

Return format: {{"topics": ["topic1", "topic2", ...]}}
"""

SUBREDDIT_RANKING_PROMPT = """
Based on the following content, rank the subreddits by relevance and return the top 10 most relevant ones.

Content: {content}

Subreddits:
{subreddit_list}

Return format: {{"subreddits": ["subreddit1", "subreddit2", ...]}}
"""

POST_RELEVANCE_ANALYSIS_PROMPT = """
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

POST_COMMENT_SELECTION_PROMPT = """
Analyze this Reddit post and its comments to decide the best place to engage.

Campaign Context: {campaign_context}

Post Title: {post_title}
Post Content: {post_content}

Comments:
{comments_text}

Decide whether to:
1. Comment on the main post
2. Reply to a specific comment

Return a JSON object with:
- target_id (post ID or comment ID)
- response_type ("post_comment" or "comment_reply")
- target_content (the content we're responding to)
- reasoning (why this is the best engagement point)

Return format: {{"target_id": "abc123", "response_type": "post_comment", "target_content": "...", "reasoning": "..."}}
"""

REDDIT_RESPONSE_GENERATION_PROMPT = """
Generate a helpful Reddit response based on the following context and target content.

Context about my expertise: {campaign_context}

Target Content: {target_content}
Response Type: {response_type}
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