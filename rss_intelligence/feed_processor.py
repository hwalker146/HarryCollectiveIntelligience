"""
Feed Processor for RSS Intelligence System
Handles RSS feed parsing, article extraction, and AI analysis
"""
import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import hashlib
import json
from pathlib import Path
import re

from article_extractor import ArticleExtractor
from ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)

class Article:
    """Represents a single article"""
    def __init__(self, title: str, url: str, content: str, published: datetime, 
                 source: str, summary: str = "", analysis: str = ""):
        self.title = title
        self.url = url
        self.content = content
        self.published = published
        self.source = source
        self.summary = summary
        self.analysis = analysis
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID for article"""
        return hashlib.md5(f"{self.url}{self.title}".encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'content': self.content[:1000],  # Truncated for storage
            'published': self.published.isoformat(),
            'source': self.source,
            'summary': self.summary,
            'analysis': self.analysis
        }

class FeedProcessor:
    """Processes RSS feeds and extracts articles"""
    
    def __init__(self, config):
        self.config = config
        self.article_extractor = ArticleExtractor()
        self.ai_analyzer = AIAnalyzer(config)
        self.processed_articles_file = Path("processed_articles.json")
        self.processed_articles = self._load_processed_articles()
        
    def _load_processed_articles(self) -> set:
        """Load list of previously processed article IDs"""
        if self.processed_articles_file.exists():
            with open(self.processed_articles_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_articles(self):
        """Save list of processed article IDs"""
        with open(self.processed_articles_file, 'w') as f:
            json.dump(list(self.processed_articles), f)
    
    async def process_all_feeds(self) -> List[Article]:
        """Process all RSS feeds and extract new articles"""
        all_articles = []
        
        # Process feeds in parallel
        tasks = []
        for feed_name, feed_url in self.config.rss_feeds.items():
            task = self._process_single_feed(feed_name, feed_url)
            tasks.append(task)
        
        # Wait for all feeds to be processed
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Feed processing failed: {result}")
            else:
                all_articles.extend(result)
        
        # Filter out already processed articles
        new_articles = []
        for article in all_articles:
            if article.id not in self.processed_articles:
                new_articles.append(article)
                self.processed_articles.add(article.id)
        
        # Save updated processed articles list
        self._save_processed_articles()
        
        logger.info(f"Found {len(new_articles)} new articles out of {len(all_articles)} total")
        return new_articles
    
    async def _process_single_feed(self, feed_name: str, feed_url: str) -> List[Article]:
        """Process a single RSS feed"""
        logger.info(f"📡 Processing feed: {feed_name}")
        
        try:
            # Parse RSS feed
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=30) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {feed_name}: HTTP {response.status}")
                        return []
                    
                    feed_content = await response.text()
            
            feed = feedparser.parse(feed_content)
            
            if not feed.entries:
                logger.warning(f"No entries found in {feed_name}")
                return []
            
            logger.info(f"   📄 Found {len(feed.entries)} entries")
            
            # Process recent entries (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_articles = []
            
            for entry in feed.entries[:20]:  # Process up to 20 most recent
                try:
                    article = await self._process_feed_entry(entry, feed_name)
                    if article and article.published > cutoff_date:
                        recent_articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to process entry from {feed_name}: {e}")
                    continue
            
            logger.info(f"   ✅ Processed {len(recent_articles)} recent articles from {feed_name}")
            return recent_articles
            
        except Exception as e:
            logger.error(f"Failed to process feed {feed_name}: {e}")
            return []
    
    async def _process_feed_entry(self, entry, feed_name: str) -> Optional[Article]:
        """Process a single feed entry into an Article"""
        try:
            # Extract basic info
            title = entry.get('title', 'Untitled').strip()
            url = entry.get('link', '').strip()
            
            if not url:
                return None
            
            # Parse published date
            published_parsed = entry.get('published_parsed')
            if published_parsed:
                published = datetime(*published_parsed[:6])
            else:
                published = datetime.now()
            
            # Extract full article content
            content = await self.article_extractor.extract_content(url)
            
            if not content or len(content.strip()) < 100:
                logger.debug(f"Skipping article with insufficient content: {title}")
                return None
            
            return Article(
                title=title,
                url=url,
                content=content,
                published=published,
                source=feed_name
            )
            
        except Exception as e:
            logger.warning(f"Failed to process feed entry: {e}")
            return None
    
    async def analyze_articles(self, articles: List[Article]) -> List[Article]:
        """Analyze articles with AI"""
        if not articles:
            return []
        
        logger.info(f"🧠 Analyzing {len(articles)} articles with AI")
        
        # Analyze articles in parallel (with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent analyses
        tasks = []
        
        for article in articles:
            task = self._analyze_single_article(article, semaphore)
            tasks.append(task)
        
        # Wait for all analyses to complete
        analyzed_articles = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful analyses
        successful_analyses = []
        for result in analyzed_articles:
            if isinstance(result, Exception):
                logger.error(f"Article analysis failed: {result}")
            elif result:
                successful_analyses.append(result)
        
        logger.info(f"✅ Successfully analyzed {len(successful_analyses)} articles")
        return successful_analyses
    
    async def _analyze_single_article(self, article: Article, semaphore) -> Optional[Article]:
        """Analyze a single article with AI"""
        async with semaphore:
            try:
                analysis = await self.ai_analyzer.analyze_article(article.content)
                article.analysis = analysis
                return article
            except Exception as e:
                logger.error(f"Failed to analyze article '{article.title}': {e}")
                return None