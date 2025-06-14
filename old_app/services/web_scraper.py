import requests
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from core.config import settings

class WebScraper:

    @staticmethod
    def get_text_from_firecrawl(url):
        app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        response = scrape_url(
            url=url,		
            formats= [ 'markdown', 'links' ],
            only_main_content= True
        )
        
        text = response.markdown
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text


   
    @staticmethod
    def get_text_from_requests(url, proxies=None):
        """
        Fetches and extracts text content from a given URL.
        
        Args:
            url (str): The URL to fetch content from.
            proxies (dict, optional): A dictionary of proxy protocols and URLs.
                Example: {'http': 'http://10.10.1.10:3128', 'https': 'http://10.10.1.10:1080'}
            
        Returns:
            str: The extracted text content.
            
        Raises:
            Exception: If there's an error fetching or parsing the content.
        """
        try:
            # Send HTTP request to the URL with proxies if provided
            response = requests.get(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'},
                proxies=proxies
            )
            
            # Raise an exception for bad status codes
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(['script', 'style']):
                script_or_style.extract()
                
            # Get text content
            text = soup.get_text()
            
            # Clean up text (remove extra whitespace)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            raise Exception(f"Error fetching content from {url}: {str(e)}")