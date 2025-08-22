#!/usr/bin/env python3
"""
New York Times Aggregator - Top Stories Analysis
Processes NYT Homepage RSS feed with article summaries
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

class NYTimesAggregator:
    def __init__(self):
        # NYT RSS feed
        self.rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        self.output_dir = Path(__file__).parent.parent / 'content' / 'nytimes'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude API client
        self.anthropic_client = None
        
        # Simple analysis prompt as requested
        self.analysis_prompt = """Please summarize this article in 300 words or less. What is the key message or thesis?

Focus on the main point the article is making and provide a clear, concise summary that captures the essential information and conclusions."""
        
    def get_anthropic_client(self):
        """Initialize Claude API client"""
        if self.anthropic_client is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self.anthropic_client
    
    def is_todays_article(self, entry):
        """Check if article is from today"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                today = datetime.now().date()
                return pub_date.date() == today
            return False
        except Exception:
            return False
    
    def fetch_article_content(self, url):
        """Fetch full article content from NYT"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for NYT content
            article_selectors = [
                '.StoryBodyCompanionColumn div[data-module="ArticleBody"] p',
                '.ArticleBody-articleBody p',
                '[data-module="ArticleBody"] p',
                '.css-1r7ky0e p',
                '.css-at9mc1 p',
                '.StoryBodyCompanionColumn p'
            ]
            
            for selector in article_selectors:
                paragraphs = soup.select(selector)
                if paragraphs and len(paragraphs) > 2:
                    content = '\n\n'.join([p.get_text().strip() for p in paragraphs[:10]])  # First 10 paragraphs
                    if len(content) > 300:
                        return content
            
            # Fallback to any paragraph content
            all_paragraphs = soup.find_all('p')
            if all_paragraphs:
                content = '\n\n'.join([p.get_text().strip() for p in all_paragraphs[:8] if len(p.get_text().strip()) > 50])
                if len(content) > 300:
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
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error analyzing article with Claude: {e}")
            return f"Analysis unavailable. Summary: {content[:300]}..."
    
    def process_feed(self):
        """Process NYT RSS feed for today's articles"""
        print("🔍 Processing New York Times top stories...")
        
        try:
            feed = feedparser.parse(self.rss_url)
            print(f"   Found {len(feed.entries)} total articles")
            
            todays_articles = []
            
            for entry in feed.entries:
                # Only process today's articles
                if not self.is_todays_article(entry):
                    continue
                
                print(f"   📰 Processing: {entry.title[:60]}...")
                
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
                    'analysis': analysis
                }
                
                todays_articles.append(article_data)
            
            print(f"   📊 Today's articles processed: {len(todays_articles)}")
            return todays_articles
            
        except Exception as e:
            print(f"   ❌ Error processing NYT feed: {e}")
            return []
    
    def generate_report(self, articles):
        """Generate comprehensive report from articles"""
        if not articles:
            return "No articles found for today."
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        today_str = datetime.now().strftime('%B %d, %Y')
        
        report_content = f"""# New York Times Top Stories
**Date:** {today_str}
**Articles Analyzed:** {len(articles)}
**Generated:** {datetime.now().strftime('%I:%M %p')}

"""
        
        for i, article in enumerate(articles, 1):
            report_content += f"## {i}. {article['title']}\n"
            report_content += f"**Published:** {article['published']}  \n"
            report_content += f"**Link:** [{article['title']}]({article['url']})  \n\n"
            report_content += f"{article['analysis']}\n\n"
            report_content += "---\n\n"
        
        # Don't save report to file - just return for email
        print(f"📄 Report generated for {len(articles)} articles (email only)")
        return report_content
    
    def send_email_report(self, report_content, num_articles):
        """Send email report"""
        try:
            email_user = os.getenv('EMAIL_USER', 'hwalker146@outlook.com')
            email_password = os.getenv('EMAIL_PASSWORD')
            
            if not email_password:
                print("📧 Email password not configured, skipping email")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = "hwalker146@outlook.com"
            msg['Subject'] = f"NYT Top Stories - {num_articles} Articles ({datetime.now().strftime('%B %d, %Y')})"
            
            msg.attach(MIMEText(report_content, 'plain'))
            
            with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
            
            print("📧 Email report sent successfully to hwalker146@outlook.com")
            return True
            
        except Exception as e:
            print(f"📧 Error sending email: {e}")
            return False
    
    def run(self, send_email=True):
        """Main execution function"""
        print("🚀 Starting New York Times Aggregation")
        print("=" * 50)
        
        # Process feed
        articles = self.process_feed()
        
        if not articles:
            print("📭 No articles found for today")
            return
        
        print(f"\n✅ Processed {len(articles)} articles from today")
        
        # Generate report
        report_content = self.generate_report(articles)
        
        # Send email if requested
        if send_email:
            success = self.send_email_report(report_content, len(articles))
            if success:
                print(f"✅ Email sent with {len(articles)} NYT articles")
            else:
                print("❌ Email sending failed")
        
        print(f"\n🎉 New York Times aggregation completed!")
        print(f"📊 Total articles: {len(articles)}")

if __name__ == "__main__":
    aggregator = NYTimesAggregator()
    aggregator.run()