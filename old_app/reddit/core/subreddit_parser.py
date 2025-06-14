"""
RedditParser - A module for asynchronously fetching and parsing Reddit RSS feeds.
"""

import xml.etree.ElementTree as ET
import json
import re
from html import unescape
import asyncio
import aiohttp
import time
import logging
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

class RedditParser:
    """
    A class to asynchronously fetch and parse Reddit RSS feeds into structured JSON format.
    Includes rate limiting, retry mechanisms, and parallel processing capabilities.
    """
    
    def __init__(
        self, 
        user_agent: str = None, 
        max_concurrent_requests: int = 5,
        request_timeout: int = 30,
        rate_limit_requests: int = 10,
        rate_limit_period: int = 60,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        proxies: Optional[Dict[str, str]] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the RedditParser with configurable parameters.
        
        Args:
            user_agent (str, optional): Custom User-Agent header for requests.
                                        If None, a default one will be used.
            max_concurrent_requests (int): Maximum number of concurrent requests.
            request_timeout (int): Timeout for HTTP requests in seconds.
            rate_limit_requests (int): Maximum number of requests in rate limit period.
            rate_limit_period (int): Rate limit period in seconds.
            max_retries (int): Maximum number of retry attempts for failed requests.
            retry_base_delay (float): Base delay for retry backoff in seconds.
            proxies (dict, optional): Optional proxies configuration.
            log_level (int): Logging level for the parser.
        """
        self.user_agent = user_agent or (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Define namespaces used in Reddit's Atom feeds
        self.namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'media': 'http://search.yahoo.com/mrss/'
        }
        
        # Configuration for parallel processing and rate limiting
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period = rate_limit_period
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.proxies = proxies
        
        # Set up logging
        self.logger = logging.getLogger("RedditParser")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Track request timestamps for rate limiting
        self.request_timestamps = []
        
        # Semaphore for controlling concurrent requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def fetch_and_parse(self, url: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Asynchronously fetch a Reddit RSS feed from a URL and convert it to a list of JSON objects.
        
        Args:
            url (str): The URL of the Reddit RSS feed (e.g., 'https://www.reddit.com/r/machinelearningnews.rss')
            sort_by_date (bool, optional): If True, sort posts by publication date (newest first).
                                         Defaults to True.
            
        Returns:
            list: A list of dictionaries containing the feed items.
            
        Raises:
            ValueError: If the URL is not a valid Reddit URL.
            Exception: If there's an error fetching or parsing the feed.
        """
        # Validate and format the URL
        url = self._validate_and_format_url(url)
        
        try:
            # Fetch the content from the URL
            xml_content = await self._fetch_feed(url)
            
            # Parse the fetched XML content
            return self._parse_feed(xml_content, sort_by_date)
            
        except aiohttp.ClientError as e:
            self.logger.error(f"Error fetching RSS feed: {str(e)}")
            raise Exception(f"Error fetching RSS feed: {str(e)}")
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML content: {str(e)}")
            raise Exception(f"Error parsing XML content: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error processing feed: {str(e)}")
            raise Exception(f"Error processing feed: {str(e)}")
    
    async def parse_from_string(self, xml_content: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Parse a Reddit Atom feed (RSS) from a string and convert it to a list of JSON objects.
        
        Args:
            xml_content (str): The XML content of the Reddit Atom feed.
            sort_by_date (bool, optional): If True, sort posts by publication date (newest first).
                                         Defaults to True.
            
        Returns:
            list: A list of dictionaries containing the feed items.
        """
        return self._parse_feed(xml_content, sort_by_date)
    
    async def parse_from_file(self, file_path: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Parse a Reddit Atom feed (RSS) from a file and convert it to a list of JSON objects.
        
        Args:
            file_path (str): Path to the XML file containing the Reddit feed.
            sort_by_date (bool, optional): If True, sort posts by publication date (newest first).
                                         Defaults to True.
            
        Returns:
            list: A list of dictionaries containing the feed items.
        """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                xml_content = await f.read()
            return self._parse_feed(xml_content, sort_by_date)
        except Exception as e:
            self.logger.error(f"Error reading or parsing file: {str(e)}")
            raise Exception(f"Error reading or parsing file: {str(e)}")
    
    async def save_to_json(self, posts: List[Dict[str, Any]], file_path: str, pretty: bool = True) -> None:
        """
        Save the parsed posts to a JSON file.
        
        Args:
            posts (list): List of post dictionaries to save.
            file_path (str): Path where the JSON file will be saved.
            pretty (bool, optional): If True, format the JSON with indentation for readability.
        """
        try:
            import aiofiles
            indent = 2 if pretty else None
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                json_data = json.dumps(posts, indent=indent, ensure_ascii=False)
                await f.write(json_data)
        except Exception as e:
            self.logger.error(f"Error saving to JSON file: {str(e)}")
            raise Exception(f"Error saving to JSON file: {str(e)}")
    
    async def get_feed_metadata(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract metadata about the Reddit feed itself (not the posts).
        
        Args:
            xml_content (str): The XML content of the Reddit Atom feed.
            
        Returns:
            dict: Feed metadata including title, subtitle, icon, etc.
        """
        try:
            # Make sure we have valid XML content
            if not xml_content or not xml_content.strip().startswith('<?xml'):
                raise ValueError("Invalid XML content provided")
            
            root = ET.fromstring(xml_content)
            
            metadata = {
                'title': self._get_text(root, './/atom:title', self.namespaces),
                'subtitle': self._get_text(root, './/atom:subtitle', self.namespaces),
                'updated': self._get_text(root, './/atom:updated', self.namespaces),
                'icon': self._get_text(root, './/atom:icon', self.namespaces),
                'id': self._get_text(root, './/atom:id', self.namespaces),
                'links': []
            }
            
            # Extract links from feed
            for link in root.findall('.//atom:link', self.namespaces):
                link_data = {
                    'rel': link.get('rel'),
                    'href': link.get('href'),
                    'type': link.get('type')
                }
                metadata['links'].append(link_data)
            
            return metadata
        except Exception as e:
            self.logger.error(f"Error extracting feed metadata: {str(e)}")
            raise Exception(f"Error extracting feed metadata: {str(e)}")
            
    async def get_subreddit_metadata(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract metadata about a subreddit.
        
        Args:
            url (str): The URL of the subreddit (with or without .rss).
            
        Returns:
            dict: Feed metadata including title, subtitle, icon, etc.
        """
        # Validate and format the URL
        formatted_url = self._validate_and_format_url(url)
        
        try:
            # Fetch the content from the URL
            xml_content = await self._fetch_feed(formatted_url)
            
            # Extract metadata
            return await self.get_feed_metadata(xml_content)
        except Exception as e:
            self.logger.error(f"Error fetching subreddit metadata: {str(e)}")
            raise Exception(f"Error fetching subreddit metadata: {str(e)}")
    
    def _construct_subreddit_url(self, subreddit: str) -> str:
        """
        Construct a properly formatted Reddit RSS URL from a subreddit name.
        
        Args:
            subreddit (str): Subreddit name (with or without 'r/' prefix)
            
        Returns:
            str: Properly formatted Reddit RSS URL
        """
        # Remove 'r/' prefix if present
        if subreddit.startswith('r/'):
            subreddit = subreddit[2:]
            
        # Remove any leading/trailing slashes
        subreddit = subreddit.strip('/')
        
        # Construct and return the full URL
        return f"https://www.reddit.com/r/{subreddit}.rss"
    
    async def fetch_subreddit(self, subreddit: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch and parse posts from a subreddit by name.
        
        Args:
            subreddit (str): Name of the subreddit (with or without 'r/' prefix)
            sort_by_date (bool): Whether to sort posts by date
            
        Returns:
            list: A list of post dictionaries
        """
        url = self._construct_subreddit_url(subreddit)
        return await self.fetch_and_parse(url, sort_by_date)
    
    async def get_subreddit_info(self, subreddit: str) -> Dict[str, Any]:
        """
        Get metadata information about a subreddit by name.
        
        Args:
            subreddit (str): Name of the subreddit (with or without 'r/' prefix)
            
        Returns:
            dict: Subreddit metadata
        """
        url = self._construct_subreddit_url(subreddit)
        return await self.get_subreddit_metadata(url)
        
    async def batch_fetch_subreddits(self, subreddits: List[str], sort_by_date: bool = True) -> Dict[str, Any]:
        """
        Batch fetch and parse multiple subreddits by name.
        
        Args:
            subreddits (list): List of subreddit names
            sort_by_date (bool): Whether to sort posts by date
            
        Returns:
            dict: Dictionary mapping subreddit names to their parsed feeds
        """
        # Convert subreddit names to URLs
        urls = [self._construct_subreddit_url(subreddit) for subreddit in subreddits]
        
        # Fetch all feeds
        results = await self.batch_fetch_and_parse(urls, sort_by_date)
        
        # Remap results from URLs back to subreddit names
        output = {}
        for subreddit, url in zip(subreddits, urls):
            output[subreddit] = results.get(url, {"error": "Failed to process"})
            
        return output
    
    async def _fetch_and_parse_with_session(self, url: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Helper method to fetch and parse a feed using the shared session.
        
        Args:
            url (str): The URL to fetch.
            sort_by_date (bool): Whether to sort posts by date.
            
        Returns:
            list: Parsed feed items.
        """
        try:
            xml_content = await self._fetch_feed_with_session(url)
            return self._parse_feed(xml_content, sort_by_date)
        except Exception as e:
            self.logger.error(f"Error in _fetch_and_parse_with_session for {url}: {str(e)}")
            raise

    async def batch_fetch_and_parse(self, urls: List[str], sort_by_date: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch fetch and parse multiple Reddit RSS feeds in parallel.
        
        Args:
            urls (list): List of Reddit RSS feed URLs
            sort_by_date (bool): Whether to sort posts by date
            
        Returns:
            dict: Dictionary mapping URLs to their parsed feeds
        """
        # Create ClientSession with appropriate configurations
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = None
        
        if self.proxies:
            connector = aiohttp.TCPConnector(ssl=False)
        
        # Store results indexed by URL
        results = {}
        tasks = []
        
        # Create a shared session for all requests
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # Create a task for each URL
            for url in urls:
                try:
                    # Validate URL format
                    formatted_url = self._validate_and_format_url(url)
                    task = asyncio.create_task(self._fetch_and_parse_with_session(formatted_url, sort_by_date))
                    tasks.append((formatted_url, task))
                except ValueError as e:
                    results[url] = {"error": str(e)}
            
            # Execute all tasks concurrently and gather results
            for url, task in tasks:
                try:
                    result = await task
                    results[url] = result
                except Exception as e:
                    self.logger.error(f"Error processing {url}: {str(e)}")
                    results[url] = {"error": str(e)}
        
        return results

    async def batch_get_subreddit_metadata(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch and extract metadata about multiple subreddits in parallel.
        
        Args:
            urls (List[str]): List of subreddit URLs (with or without .rss)
            
        Returns:
            dict: Dictionary mapping subreddit URLs to their metadata
        """
        results = {}
        tasks = []
        
        # Create a ClientSession with appropriate configurations
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = None
        
        if self.proxies:
            connector = aiohttp.TCPConnector(ssl=False)
        
        # Create a shared session for all requests
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session
            
            # Create a task for each URL
            for url in urls:
                try:
                    # Validate and format the URL
                    formatted_url = self._validate_and_format_url(url)
                    
                    # Create task to fetch and extract metadata
                    async def fetch_metadata(url):
                        xml_content = await self._fetch_feed_with_session(url)
                        return await self.get_feed_metadata(xml_content)
                    
                    task = asyncio.create_task(fetch_metadata(formatted_url))
                    tasks.append((url, task))
                except ValueError as e:
                    results[url] = {"error": str(e)}
            
            # Execute all tasks concurrently and gather results
            for url, task in tasks:
                try:
                    result = await task
                    results[url] = result
                except Exception as e:
                    self.logger.error(f"Error fetching metadata for {url}: {str(e)}")
                    results[url] = {"error": str(e)}
        
        return results

    async def batch_get_subreddit_info(self, subreddits: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata information about multiple subreddits by name in parallel.
        
        Args:
            subreddits (List[str]): List of subreddit names (with or without 'r/' prefix)
            
        Returns:
            dict: Dictionary mapping subreddit names to their metadata
        """
        # Convert subreddit names to URLs
        urls = [self._construct_subreddit_url(subreddit) for subreddit in subreddits]
        
        # Fetch all metadata
        results = await self.batch_get_subreddit_metadata(urls)
        
        # Remap results from URLs back to subreddit names
        output = {}
        for subreddit, url in zip(subreddits, urls):
            output[subreddit] = results.get(url, {"error": "Failed to process"})
            
        return output
    
    # Private methods
    
    def _validate_and_format_url(self, url: str) -> str:
        """
        Validate that the URL is a Reddit URL and ensure it ends with .rss
        
        Args:
            url (str): URL to validate and format
            
        Returns:
            str: Properly formatted URL
            
        Raises:
            ValueError: If the URL is not a valid Reddit URL
        """
        parsed_url = urlparse(url)
        if not parsed_url.netloc or 'reddit.com' not in parsed_url.netloc:
            raise ValueError("Invalid Reddit URL. Expected a URL from reddit.com domain.")
            
        # Ensure URL ends with .rss
        if not url.endswith('.rss'):
            if url.endswith('/'):
                url = url[:-1] + '.rss'
            else:
                url = url + '.rss'
        
        return url
    
    async def _enforce_rate_limits(self):
        """
        Enforce rate limits by waiting if necessary.
        """
        now = time.time()
        
        # Remove timestamps older than the rate limit period
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < self.rate_limit_period]
        
        # If we've reached the rate limit, wait until we can make another request
        if len(self.request_timestamps) >= self.rate_limit_requests:
            oldest_timestamp = min(self.request_timestamps)
            wait_time = self.rate_limit_period - (now - oldest_timestamp)
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds.")
                await asyncio.sleep(wait_time)
        
        # Add a small random delay to avoid request bursts
        await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def _fetch_feed(self, url: str) -> str:
        """
        Asynchronously fetch the RSS feed content from the given URL.
        Includes retry logic with exponential backoff.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: XML content of the feed
        """
        # Create a new session for this request
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        connector = None
        
        if self.proxies:
            connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            return await self._fetch_feed_with_session(url, session)
    
    async def _fetch_feed_with_session(self, url: str, session=None) -> str:
        """
        Fetch a feed using an existing session or the class's session.
        Includes retry logic and rate limiting.
        
        Args:
            url (str): URL to fetch
            session: An existing aiohttp session (optional)
            
        Returns:
            str: XML content of the feed
        """
        use_session = session or self.session
        headers = {'User-Agent': self.user_agent}
        
        # Apply rate limiting
        await self._enforce_rate_limits()
        
        # Use semaphore to limit concurrent requests
        async with self.semaphore:
            for retry in range(self.max_retries + 1):
                try:
                    # Record the request timestamp for rate limiting
                    self.request_timestamps.append(time.time())
                    
                    # Make the request
                    proxy = None
                    if self.proxies:
                        proxy = self.proxies.get("http") or self.proxies.get("https")
                    
                    async with use_session.get(url, headers=headers, proxy=proxy) as response:
                        # Handle rate limiting response
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', self.retry_base_delay * (2 ** retry)))
                            self.logger.warning(f"Rate limited by Reddit. Waiting {retry_after} seconds.")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        # Handle other error status codes
                        if response.status >= 400:
                            if retry < self.max_retries:
                                wait_time = self.retry_base_delay * (2 ** retry)
                                self.logger.warning(f"Request failed with status {response.status}. Retrying in {wait_time:.2f} seconds...")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                response.raise_for_status()
                        
                        # Successful response
                        return await response.text()
                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if retry < self.max_retries:
                        wait_time = self.retry_base_delay * (2 ** retry)
                        self.logger.warning(f"Request error: {str(e)}. Retrying in {wait_time:.2f} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.error(f"Max retries reached for {url}: {str(e)}")
                        raise
        
        # Should never reach here, but just in case
        raise Exception(f"Failed to fetch {url} after {self.max_retries} retries")
    
    def _parse_feed(self, xml_content: str, sort_by_date: bool = True) -> List[Dict[str, Any]]:
        """
        Parse the XML content of a Reddit Atom feed.
        
        Args:
            xml_content (str): XML content to parse
            sort_by_date (bool, optional): If True, sort posts by publication date (newest first).
                                         Defaults to True.
            
        Returns:
            list: List of post dictionaries
        """
        root = ET.fromstring(xml_content)
        results = []
        
        # Process each entry in the feed
        for entry in root.findall('.//atom:entry', self.namespaces):
            entry_data = {}
            
            # Extract basic entry data
            entry_data['id'] = self._get_text(entry, './/atom:id', self.namespaces)
            entry_data['title'] = self._get_text(entry, './/atom:title', self.namespaces)
            entry_data['updated'] = self._get_text(entry, './/atom:updated', self.namespaces)
            entry_data['published'] = self._get_text(entry, './/atom:published', self.namespaces)
            
            # Extract the link to the post
            link_elem = entry.find('.//atom:link', self.namespaces)
            if link_elem is not None:
                entry_data['permalink'] = link_elem.get('href')
            
            # Extract author information
            author = entry.find('.//atom:author', self.namespaces)
            if author is not None:
                entry_data['author'] = {
                    'name': self._get_text(author, './/atom:name', self.namespaces),
                    'uri': self._get_text(author, './/atom:uri', self.namespaces)
                }
            
            # Extract content
            content = self._get_text(entry, './/atom:content', self.namespaces)
            if content:
                # Parse the content to extract links and text
                entry_data['content'] = self._parse_content(content)
            
            # Extract media thumbnail if present
            thumbnail = entry.find('.//media:thumbnail', self.namespaces)
            if thumbnail is not None:
                entry_data['thumbnail_url'] = thumbnail.get('url')
            
            # Extract category if present
            category = entry.find('.//atom:category', self.namespaces)
            if category is not None:
                entry_data['category'] = {
                    'term': category.get('term'),
                    'label': category.get('label')
                }
            
            results.append(entry_data)
        
        # Sort posts by publication date (newest first) if requested
        if sort_by_date and results:
            results.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        return results
    
    def _get_text(self, element, xpath, namespaces=None):
        """
        Helper function to get text from an XML element
        
        Args:
            element: The XML element to search in
            xpath: XPath expression to find the target element
            namespaces: Namespace mappings for the XPath
            
        Returns:
            str or None: Text content of the element if found, None otherwise
        """
        elem = element.find(xpath, namespaces)
        return elem.text if elem is not None else None
    
    def _parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse the HTML content of a Reddit post to extract links and text.
        
        Args:
            content (str): The HTML content of the Reddit post.
            
        Returns:
            dict: A dictionary containing parsed content elements.
        """
        result = {
            'text': '',
            'links': [],
            'has_image': False
        }
        
        # Extract links
        link_pattern = r'<a href="([^"]+)">([^<]+)</a>'
        links = re.findall(link_pattern, content)
        for url, text in links:
            result['links'].append({
                'url': url,
                'text': text
            })
        
        # Check for images
        if '<img src=' in content:
            result['has_image'] = True
        
        # Clean text (remove HTML tags)
        text = re.sub(r'<[^>]+>', ' ', content)
        result['text'] = unescape(text).strip()
        
        return result


if __name__ == "__main__":
    # Example usage:
    async def main():
        parser = RedditParser()
        
        # Example 1: Fetch from single subreddit by name
        subreddit_name = "machinelearningnews"
        posts = await parser.fetch_subreddit(subreddit_name)
        print(f"Found {len(posts)} posts from r/{subreddit_name}")
        
        # Example 2: Batch fetch multiple subreddits by name
        subreddits = [
            "machinelearningnews",
            "python",
            "artificial"
        ]
        results = await parser.batch_fetch_subreddits(subreddits)
        for subreddit, data in results.items():
            if isinstance(data, list):
                print(f"Found {len(data)} posts from r/{subreddit}")
            else:
                print(f"Error fetching r/{subreddit}: {data.get('error')}")
        
        # Example 3: Batch get metadata for multiple subreddits
        metadata_results = await parser.batch_get_subreddit_info(subreddits)
        for subreddit, metadata in metadata_results.items():
            if 'error' not in metadata:
                print(f"r/{subreddit} title: {metadata.get('title')}")
            else:
                print(f"Error fetching metadata for r/{subreddit}: {metadata.get('error')}")


    asyncio.run(main())