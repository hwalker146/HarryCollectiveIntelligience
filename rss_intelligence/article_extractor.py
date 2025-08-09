"""
Article Content Extractor
Extracts and cleans full text content from article URLs
"""
import aiohttp
import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import hashlib

# Try to import readability and BeautifulSoup
try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False
    logging.warning("readability-lxml not installed. Article extraction will be basic.")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup4 not installed. HTML parsing will be limited.")

logger = logging.getLogger(__name__)

class ArticleExtractor:
    """Extracts clean article content from URLs"""
    
    def __init__(self):
        self.session = None
        self.cache = {}  # Simple in-memory cache
        
    async def extract_content(self, url: str) -> Optional[str]:
        """Extract clean article content from URL"""
        # Check cache first
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.cache:
            logger.debug(f"Cache hit for {url}")
            return self.cache[url_hash]
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        'User-Agent': 'RSS Intelligence Bot 1.0 (Professional News Aggregator)'
                    }
                )
            
            logger.debug(f"Extracting content from: {url}")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html_content = await response.text()
                
                # Extract clean content
                if READABILITY_AVAILABLE:
                    content = self._extract_with_readability(html_content, url)
                elif BS4_AVAILABLE:
                    content = self._extract_with_bs4(html_content)
                else:
                    content = self._extract_basic(html_content)
                
                # Clean and validate content
                cleaned_content = self._clean_content(content)
                
                # Cache the result
                self.cache[url_hash] = cleaned_content
                
                return cleaned_content
                
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return None
    
    def _extract_with_readability(self, html_content: str, url: str) -> str:
        """Extract content using readability library (best option)"""
        try:
            doc = Document(html_content)
            title = doc.title()
            content = doc.summary()
            
            if BS4_AVAILABLE:
                # Use BeautifulSoup to extract text from HTML
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text()
            else:
                # Basic HTML tag removal
                text_content = re.sub(r'<[^>]+>', '', content)
            
            return f"{title}\n\n{text_content}"
            
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")
            return self._extract_with_bs4(html_content) if BS4_AVAILABLE else ""
    
    def _extract_with_bs4(self, html_content: str) -> str:
        """Extract content using BeautifulSoup (fallback)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'advertisement', 'ads', 'sidebar']):
                element.decompose()
            
            # Try to find main content areas
            content_selectors = [
                'article',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '.content',
                'main',
                '.main-content'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text()
                    break
            
            # Fallback to body if no specific content area found
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text()
            
            # Get title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            return f"{title}\n\n{content}" if content else ""
            
        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed: {e}")
            return self._extract_basic(html_content)
    
    def _extract_basic(self, html_content: str) -> str:
        """Basic HTML tag removal (last resort)"""
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception as e:
            logger.error(f"Basic extraction failed: {e}")
            return ""
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Subscribe to.*newsletter',
            r'Click here to.*',
            r'Advertisement\s*',
            r'Continue reading.*',
            r'Read more.*',
            r'Share this.*',
            r'Follow us on.*',
            r'Copyright.*\d{4}',
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Truncate if too long (to manage token limits)
        if len(content) > 8000:
            content = content[:8000] + "...[Content truncated]"
        
        return content.strip()
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.session and not self.session.closed:
            # Note: This should ideally be handled properly with async context managers
            pass