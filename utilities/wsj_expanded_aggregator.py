#!/usr/bin/env python3
"""
WSJ Expanded Aggregator - More articles with less restrictive filtering
Processes multiple WSJ RSS feeds with relaxed filtering criteria
"""
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import smtplib
import anthropic
import os
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class WSJExpandedAggregator:
    def __init__(self):
        # Expanded RSS feeds for more content
        self.rss_urls = {
            "Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
            "Technology": "https://feeds.content.dowjones.io/public/rss/RSSWSJD",
            "Markets": "https://feeds.content.dowjones.io/public/rss/WSJcomUSMarkets",
            "Economy": "https://feeds.content.dowjones.io/public/rss/WSJcomUSEconomy",
            "World": "https://feeds.content.dowjones.io/public/rss/WSJcomUSWorldNews",
            "Politics": "https://feeds.content.dowjones.io/public/rss/WSJcomUSPolitics"
        }
        self.output_dir = Path(__file__).parent.parent / 'content' / 'wsj_expanded'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # WSJ credentials
        self.wsj_username = "harris.walker@lazard.com"
        self.wsj_password = "Iluvbanking146"
        
        # Initialize Claude API client
        self.anthropic_client = None
        
        # Relaxed filtering - broader categories and fewer exclusions
        self.relevant_categories = [
            'business', 'finance', 'economics', 'markets', 'technology', 'policy',
            'regulation', 'government', 'corporate', 'industry', 'trade', 'investment',
            'banking', 'insurance', 'healthcare', 'energy', 'infrastructure', 'manufacturing',
            'transportation', 'telecommunications', 'media', 'real estate', 'commodities'
        ]
        
        # Minimal exclusions - only clearly irrelevant content
        self.excluded_topics = [
            'celebrity gossip', 'entertainment news', 'sports scores', 'weather',
            'horoscope', 'recipe', 'fashion week', 'movie review', 'music album'
        ]
        
        # Paragraph-only analysis prompt
        self.analysis_prompt = """You are a business and economic analyst providing concise summaries of Wall Street Journal articles. Your analysis should be written entirely in paragraph format with no bullet points, lists, or structured sections.

Write a comprehensive analysis that flows naturally from one insight to the next. Begin with the most significant development or finding from the article, then explain the broader context and implications. Include relevant financial figures, market impacts, and strategic considerations throughout your narrative.

Focus on delivering actionable insights for business professionals and investors while maintaining journalistic objectivity. Connect the immediate news to larger economic trends, regulatory changes, or market dynamics when relevant. Conclude with the potential longer-term implications or what to watch for next.

Your analysis should be 150-250 words and read as a cohesive, flowing commentary rather than a structured breakdown. Write in clear, professional prose that could appear in a business newsletter or executive briefing."""
        
    def get_anthropic_client(self):
        """Initialize Claude API client"""
        if self.anthropic_client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self.anthropic_client
    
    def is_article_relevant(self, entry):
        """Relaxed filtering - include most business-related content"""
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '').lower()
        content = f"{title} {summary}"
        
        # Only exclude clearly irrelevant content
        for excluded in self.excluded_topics:
            if excluded in content:
                return False, f"Excluded: {excluded}"
        
        # Much broader inclusion criteria
        # Include if it mentions any business/economic terms OR is from business sections
        for category in self.relevant_categories:
            if category in content:
                return True, f"Included: {category}"
        
        # Also include articles with financial figures
        if re.search(r'\$\d+|percent|million|billion|trillion|revenue|profit|loss|earnings', content):
            return True, "Included: financial content"
        
        # Include articles about companies, policies, or markets
        if re.search(r'company|corporation|inc\.|ltd\.|llc|policy|regulation|market|stocks?|bonds?', content):
            return True, "Included: corporate/market content"
        
        # Default to inclusion unless clearly excluded
        return True, "Included: general business relevance"
    
    def fetch_article_content(self, url):
        """Fetch full article content from WSJ"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for WSJ content
            article_selectors = [
                '.wsj-article-wrap .article-content',
                '.article-wrap .article-content', 
                '.ArticleBody-articleBody',
                '[data-module="ArticleBody"]',
                '.snippet-promotion'
            ]
            
            for selector in article_selectors:
                article_div = soup.select_one(selector)
                if article_div:
                    paragraphs = article_div.find_all('p')
                    if paragraphs:
                        content = '\n\n'.join([p.get_text().strip() for p in paragraphs[:8]])  # First 8 paragraphs
                        if len(content) > 200:
                            return content
            
            return None
            
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return None
    
    def analyze_article_with_claude(self, title, content):
        """Analyze article content using Claude"""
        try:
            client = self.get_anthropic_client()
            
            prompt = f"""Article Title: {title}

Article Content:
{content}

{self.analysis_prompt}"""
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error analyzing article with Claude: {e}")
            return f"Analysis unavailable. Summary: {content[:300]}..."
    
    def process_feeds(self, hours_back=24):
        """Process all WSJ RSS feeds"""
        print("🔍 Processing WSJ RSS feeds for expanded coverage...")
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_articles = []
        
        for feed_name, rss_url in self.rss_urls.items():
            print(f"\n📡 Processing {feed_name} feed...")
            
            try:
                feed = feedparser.parse(rss_url)
                print(f"   Found {len(feed.entries)} total articles")
                
                recent_articles = 0
                relevant_articles = 0
                
                for entry in feed.entries:
                    # Check if article is recent
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date < cutoff_time:
                            continue
                    
                    recent_articles += 1
                    
                    # Apply relaxed filtering
                    is_relevant, reason = self.is_article_relevant(entry)
                    if not is_relevant:
                        continue
                    
                    relevant_articles += 1
                    
                    # Fetch article content
                    article_url = entry.get('link', '')
                    article_content = self.fetch_article_content(article_url)
                    
                    if not article_content:
                        article_content = entry.get('summary', 'Content unavailable')
                    
                    # Analyze with Claude
                    analysis = self.analyze_article_with_claude(entry.title, article_content)
                    
                    article_data = {
                        'title': entry.title,
                        'url': article_url,
                        'published': entry.get('published', 'Unknown'),
                        'summary': entry.get('summary', ''),
                        'content': article_content,
                        'analysis': analysis,
                        'feed': feed_name,
                        'reason': reason
                    }
                    
                    all_articles.append(article_data)
                
                print(f"   📊 Recent: {recent_articles}, Relevant: {relevant_articles}")
                
            except Exception as e:
                print(f"   ❌ Error processing {feed_name}: {e}")
        
        return all_articles
    
    def generate_report(self, articles):
        """Generate comprehensive report from articles"""
        if not articles:
            return "No relevant articles found in the specified time period."
        
        # Group by feed
        feeds = {}
        for article in articles:
            feed_name = article['feed']
            if feed_name not in feeds:
                feeds[feed_name] = []
            feeds[feed_name].append(article)
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_content = f"""# WSJ Expanded Daily Report
**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Articles Analyzed:** {len(articles)}
**Sources:** {', '.join(feeds.keys())}

"""
        
        for feed_name, feed_articles in feeds.items():
            report_content += f"\n## {feed_name} ({len(feed_articles)} articles)\n\n"
            
            for article in feed_articles:
                report_content += f"### {article['title']}\n"
                report_content += f"**Published:** {article['published']}  \n"
                report_content += f"**Source:** [{feed_name}]({article['url']})  \n\n"
                report_content += f"{article['analysis']}\n\n"
                report_content += "---\n\n"
        
        # Don't save report to file - just return for email
        print(f"📄 Report generated (email only - not saved to file)")
        return report_content, None
    
    def send_email_report(self, report_content, num_articles):
        """Send email report"""
        try:
            email_user = os.getenv('EMAIL_USER', 'hwalker146@outlook.com')
            email_password = os.getenv('EMAIL_PASSWORD')
            
            if not email_password:
                print("📧 Email password not configured, skipping email")
                return
            
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = "hwalker146@outlook.com"
            msg['Subject'] = f"WSJ Expanded Daily Report - {num_articles} Articles"
            
            msg.attach(MIMEText(report_content, 'plain'))
            
            with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
            
            print("📧 Email report sent successfully")
            
        except Exception as e:
            print(f"📧 Error sending email: {e}")
    
    def run(self, hours_back=24, send_email=True):
        """Main execution function"""
        print("🚀 Starting WSJ Expanded Aggregation")
        print("=" * 50)
        
        # Process feeds
        articles = self.process_feeds(hours_back)
        
        if not articles:
            print("📭 No relevant articles found")
            return
        
        print(f"\n✅ Processed {len(articles)} relevant articles")
        
        # Generate report
        report_content, report_path = self.generate_report(articles)
        
        # Send email if requested
        if send_email:
            self.send_email_report(report_content, len(articles))
        
        print(f"\n🎉 WSJ Expanded aggregation completed!")
        print(f"📊 Total articles: {len(articles)}")
        print(f"📧 Report emailed (not saved locally)")

if __name__ == "__main__":
    aggregator = WSJExpandedAggregator()
    aggregator.run()