"""
SubredditFinder - A module for finding relevant subreddits based on text content analysis.
"""

from services.llm.llm_service import ai_client
import aiohttp
import asyncio
import json

from typing import Dict, List, Any, Optional

class SubredditFinder:
    """
    A class for finding relevant subreddits based on text content analysis.
    Uses AI to extract topics from text and then finds and filters subreddits
    related to those topics.
    """

    def __init__(self, min_subscribers: int = 10000, user_agent: str = "Mozilla/5.0", proxies: Optional[Dict[str, str]] = None):
        """
        Initialize the SubredditFinder.

        Args:
            min_subscribers: Minimum number of subscribers a subreddit should have
            user_agent: User agent to use for Reddit API requests
            proxies: Optional dictionary of proxies to use for requests (e.g., {"http": "http://proxy.com:8080"})
        """
        self.min_subscribers = min_subscribers
        self.headers = {"User-Agent": user_agent}
        self.proxies = proxies

    async def extract_topics_from_text(self, text: str) -> List[str]:
        """
        Extract relevant topics from the given text using AI analysis.

        Args:
            text: The content to analyze

        Returns:
            A list of relevant topics
        """
        messages = [
            {"role": "system", "content": "You are an expert marketing content analyzer. Your task is to analyze the provided text and provide a list of related topics to search on reddit."},
            {"role": "user", "content": f"Analyse the text provided below and return a list of related topics in a JSON object ({{'topics':[...]}}). Here is the content to analyze: {text}"}
        ]

        response = await ai_client.generate_chat_completion_gemini(
            messages=messages,
            response_format={"type": "json_object"}
        )

        content = response["choices"][0]["message"]["content"]
        
        topics = content["topics"]

        return topics

    async def batch_extract_topics_from_texts(self, texts: List[str]) -> Dict[int, List[str]]:
        """
        Extract relevant topics from multiple text samples in parallel.

        Args:
            texts (List[str]): List of content samples to analyze

        Returns:
            dict: Dictionary mapping text indices to their extracted topics
        """
        results = {}
        tasks = []
        
        # Create a task for each text sample
        for i, text in enumerate(texts):
            task = asyncio.create_task(self.extract_topics_from_text(text))
            tasks.append((i, task))
        
        # Execute all tasks concurrently and gather results
        for i, task in tasks:
            try:
                result = await task
                results[i] = result
            except Exception as e:
                print(f"Error extracting topics from text sample {i}: {str(e)}")
                results[i] = {"error": str(e)}
        
        return results

    async def get_subreddit_details(self, subreddit_name: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        Fetch information about a specific subreddit, including description and size.

        Args:
            subreddit_name: Name of the subreddit to get details for
            session: aiohttp ClientSession to use for requests

        Returns:
            Dictionary containing subreddit information
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Get the description and subscriber count
                    about = data["data"].get("public_description", "") or data["data"].get("description", "")
                    subscribers = data["data"].get("subscribers", 0)
                    
                    return {
                        "about": about,
                        "subscribers": subscribers
                    }
                else:
                    return {"about": "", "subscribers": 0}  # Return empty values if we can't fetch data
        except Exception as e:
            print(f"Error fetching subreddit details for {subreddit_name}: {str(e)}")
            return {"about": "", "subscribers": 0}

    async def search_subreddits_by_topic(self, topic: str, session: aiohttp.ClientSession) -> Dict[str, Dict[str, Any]]:
        """
        Search Reddit for subreddits related to a specific topic.

        Args:
            topic: The topic to search for
            session: aiohttp ClientSession to use for requests

        Returns:
            Dictionary of subreddits with their details
        """
        url = f"https://www.reddit.com/search.json?q={topic}"
        
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data["data"]["children"]

                    # Dictionary to store unique subreddits and their info
                    subreddit_dict = {}
                    
                    # Create tasks for fetching subreddit details in parallel
                    subreddit_names = set()
                    for post in posts:
                        post_data = post["data"]
                        subreddit_name = post_data["subreddit"].strip()
                        subreddit_names.add(subreddit_name)
                    
                    # Fetch all subreddit details in parallel
                    tasks = [self.get_subreddit_details(name, session) for name in subreddit_names]
                    results = await asyncio.gather(*tasks)
                    
                    # Combine results with subreddit names
                    for name, info in zip(subreddit_names, results):
                        subreddit_dict[name] = info
                    
                    return subreddit_dict
                else:
                    return {"error": f"Failed to fetch data, status code {response.status}"}
        except Exception as e:
            return {"error": f"Failed to search subreddits for topic '{topic}': {str(e)}"}

    def filter_subreddits_by_criteria(self, subreddit_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Filter subreddits based on having a non-empty description and minimum subscribers.
        
        Args:
            subreddit_data: Dictionary of subreddits with their info
            
        Returns:
            Filtered dictionary containing only subreddits meeting the criteria
        """
        filtered_subreddits = {}
        
        for subreddit_name, info in subreddit_data.items():
            # Check if the about field is not empty and subscriber count meets minimum
            if info["about"] != "" and info["subscribers"] >= self.min_subscribers:
                filtered_subreddits[subreddit_name] = info
        
        return filtered_subreddits

    async def rank_subreddits_by_relevance(self, text: str, subreddit_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Use AI to rank and filter subreddits by relevance to the original text.

        Args:
            text: The original text content
            subreddit_data: Dictionary of subreddits with their info

        Returns:
            List of most relevant subreddit names
        """
        messages = [
            {"role": "system", "content": "You are an expert reddit marketer. Your task is to analyze the provided text and the list of related subreddits, and filter it down to best suited subreddits."},
            {"role": "user", "content": f"Analyse the text and list of subreddits provided below and return a list of most relevant subreddits in a JSON object ({{'subreddits':[...]}}). Here is the content to analyze: {text} Here is the list of subreddits: {subreddit_data}"}
        ]

        response = await ai_client.generate_chat_completion_gemini(
            messages=messages,
            response_format={"type": "json_object"}
        )

        content = response["choices"][0]["message"]["content"]
        subreddits = content["subreddits"]

        return subreddits

    async def find_relevant_subreddits(self, text: str) -> Dict[str, Any]:
        """
        Main method to find relevant subreddits based on text content.
        Orchestrates the entire process of topic extraction, subreddit search, and filtering.

        Args:
            text: The content to analyze

        Returns:
            Dictionary containing relevant subreddits and their data
        """
        # Step 1: Extract topics from the text
        topics = await self.extract_topics_from_text(text)
        
        # Step 2: Search for subreddits related to each topic in parallel
        all_subreddits = {}
        
        # Create a ClientSession with proxy support if configured
        connector = None
        if self.proxies:
            # Set up proxy configuration for aiohttp
            connector = aiohttp.TCPConnector(ssl=False)
            
        async with aiohttp.ClientSession(connector=connector) as session:
            # If proxies are configured, set the proxy for the session
            if self.proxies:
                session._default_headers.update(self.headers)
                session._proxy = self.proxies.get("http") or self.proxies.get("https")
            
            # Create tasks for searching topics in parallel
            search_tasks = [self.search_subreddits_by_topic(topic, session) for topic in topics]
            topic_results = await asyncio.gather(*search_tasks)
            
            # Merge results from all topics
            for result in topic_results:
                if "error" not in result:
                    all_subreddits.update(result)
    
        # Step 3: Filter subreddits by criteria
        filtered_subreddits = self.filter_subreddits_by_criteria(all_subreddits)
        
        # Step 4: Rank and further filter subreddits by relevance
        relevant_subreddit_names = await self.rank_subreddits_by_relevance(text, filtered_subreddits)
        
        # Step 5: Create final result dictionary
        result_subreddits = {}
        for name in relevant_subreddit_names:
            if name in filtered_subreddits:
                result_subreddits[name] = filtered_subreddits[name]
        
        return {
            "relevant_subreddits": result_subreddits,
            "all_subreddits": filtered_subreddits,
            "topics": topics
        }

    async def batch_find_relevant_subreddits(self, texts: List[str]) -> Dict[int, Dict[str, Any]]:
        """
        Find relevant subreddits for multiple text samples in parallel.
        
        Args:
            texts (List[str]): List of content samples to analyze
            
        Returns:
            dict: Dictionary mapping text indices to their subreddit analysis results
        """
        results = {}
        tasks = []
        
        # Create a task for each text sample
        for i, text in enumerate(texts):
            task = asyncio.create_task(self.find_relevant_subreddits(text))
            tasks.append((i, task))
        
        # Execute all tasks concurrently and gather results
        for i, task in tasks:
            try:
                result = await task
                results[i] = result
            except Exception as e:
                print(f"Error finding subreddits for text sample {i}: {str(e)}")
                results[i] = {"error": str(e)}
        
        return results

if __name__ == "__main__":
    
    """
    Example script demonstrating the SubredditFinder module with hard-coded text.
    """

    import asyncio
    import time
    async def main():
        """
        Main function that demonstrates how to use the SubredditFinder class
        with a hard-coded text example.
        """
        # Sample text for analysis
        sample_text = """
        I've been learning Python for the past 6 months and have built several small
        projects including a web scraper, a data visualization dashboard, and a simple
        machine learning model for text classification. I'm particularly interested in
        AI and natural language processing. I'm looking for communities where I can share
        my projects, get feedback from experienced developers, and continue learning about
        best practices in software development. I also enjoy gaming in my free time,
        particularly RPGs and strategy games.
        """
        
        print("Initializing SubredditFinder...")
        finder = SubredditFinder(min_subscribers=5000)
        
        print("Analyzing text and finding relevant subreddits...")
        start = time.time()
        results = await finder.find_relevant_subreddits(sample_text)
        print(time.time()-start)
        # Display topics
        print(f"\nExtracted Topics ({len(results['topics'])}):")
        for i, topic in enumerate(results['topics'], 1):
            print(f"{i}. {topic}")
        
        # Display relevant subreddits
        print(f"\nRelevant Subreddits ({len(results['relevant_subreddits'])}):")
        for i, (name, data) in enumerate(results['relevant_subreddits'].items(), 1):
            print(f"{i}. r/{name} - {data['subscribers']:,} subscribers")
            print(f"   Description: {data['about'][:100]}..." if len(data['about']) > 100 else f"   Description: {data['about']}")
            print()
        
        # Save results to JSON file
        with open("subreddit_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("Full results saved to subreddit_analysis_results.json")

        # Example of batch processing multiple text samples
        print("\nDemonstrating batch processing with multiple text samples...")
        sample_texts = [
            sample_text,  # Reuse our first sample
            """
            I'm building a mobile app that helps users track their fitness goals and nutrition.
            The app will use machine learning to suggest personalized workout routines and meal plans.
            I'm looking for communities to get feedback on UI design and app features.
            """,
            """
            I'm writing a sci-fi novel set in a future where AI has become sentient and integrated
            with human consciousness. Looking for communities to discuss ethical implications and
            get feedback on my worldbuilding and character development.
            """
        ]
        
        start = time.time()
        batch_results = await finder.batch_find_relevant_subreddits(sample_texts)
        batch_time = time.time() - start
        print(f"Batch processing completed in {batch_time:.2f} seconds")
        
        # Display summary of batch results
        for i, result in batch_results.items():
            if "error" in result:
                print(f"Sample {i}: Error - {result['error']}")
            else:
                print(f"Sample {i}: Found {len(result['relevant_subreddits'])} relevant subreddits from {len(result['topics'])} topics")
        
        # Save batch results to JSON file
        with open("batch_subreddit_analysis_results.json", "w") as f:
            json.dump(batch_results, f, indent=2)
        print("Batch results saved to batch_subreddit_analysis_results.json")

    # Run the async main function
    asyncio.run(main())