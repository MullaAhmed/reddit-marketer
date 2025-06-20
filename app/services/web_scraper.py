"""
Web scraping service.
"""

import requests
import logging
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from typing import Optional

from app.core.settings_config import settings
from app.utils.text_processing import clean_text

logger = logging.getLogger(__name__)


class WebScraperService:
    """
    Service for web scraping operations.
    """
    
    def __init__(self):
        """Initialize the web scraper service."""
        self.logger = logger
    
    def scrape_with_firecrawl(self, url: str) -> Optional[str]:
        """
        Scrape URL using Firecrawl API.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            if not settings.FIRECRAWL_API_KEY:
                raise ValueError("Firecrawl API key not configured")
            
            app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
            response = app.scrape_url(
                url=url,
                formats=['markdown', 'links'],
                only_main_content=True
            )
            
            text = response.markdown
            cleaned_text = clean_text(text)
            
            self.logger.info(f"Successfully scraped {url} with Firecrawl")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error scraping {url} with Firecrawl: {str(e)}")
            return None
    
    def scrape_with_requests(self, url: str, proxies: Optional[dict] = None) -> Optional[str]:
        """
        Scrape URL using requests and BeautifulSoup.
        
        Args:
            url: URL to scrape
            proxies: Optional proxy configuration
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Send HTTP request
            response = requests.get(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'},
                proxies=proxies,
                timeout=30
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
            cleaned_text = clean_text(text)
            
            self.logger.info(f"Successfully scraped {url} with requests")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Error scraping {url} with requests: {str(e)}")
            return None
    
    def scrape_url(self, url: str, method: str = "auto", proxies: Optional[dict] = None) -> Optional[str]:
        """
        Scrape URL using the specified method.
        
        Args:
            url: URL to scrape
            method: Scraping method ("firecrawl", "requests", or "auto")
            proxies: Optional proxy configuration
            
        Returns:
            Extracted text content or None if failed
        """
        if method == "firecrawl":
            return self.scrape_with_firecrawl(url)
        elif method == "requests":
            return self.scrape_with_requests(url, proxies)
        elif method == "auto":
            # Try Firecrawl first, fallback to requests
            result = self.scrape_with_firecrawl(url)
            if result is None:
                result = self.scrape_with_requests(url, proxies)
            return result
        else:
            raise ValueError(f"Unsupported scraping method: {method}")