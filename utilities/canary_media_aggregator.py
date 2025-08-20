#!/usr/bin/env python3
"""
Canary Media RSS Feed Aggregator
Fetches all articles from Canary Media RSS feed and outputs organized text content
"""
import feedparser
import requests
from bs4 import BeautifulSoup
import re
import smtplib
import anthropic
import os
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class CanaryMediaAggregator:
    def __init__(self):
        self.rss_url = "https://www.canarymedia.com/rss.rss"
        self.output_dir = Path(__file__).parent.parent / 'content' / 'canary_media'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude API client
        self.anthropic_client = None
        
        # Investment analysis prompt
        self.analysis_prompt = """You are an expert research analyst specializing in infrastructure investment. You will be given one or more articles from Canary Media. Your task is to produce a clear, concise, and investor-focused summary.

Focus on:
- The core issue or development (policy change, technology advancement, corporate strategy, financing, etc.)
- The implications for infrastructure investment (renewable energy, grid modernization, storage, transmission, EV charging, hydrogen, etc.)
- Any risks, bottlenecks, or enabling factors (policy, permitting, supply chain, regulation, financing environment)
- The scale and timing of potential impact (short-term vs long-term relevance)
- Relevant data points or statistics that strengthen understanding

Output format:
Headline Insight – one sentence capturing the main takeaway for an infrastructure investor.
Summary - paragraph format explaining the above
Investor Lens – one short paragraph explaining how this development could influence opportunities, risks, or capital allocation in the infrastructure sector."""
        
    def fetch_rss_feed(self):
        """Fetch and parse the RSS feed"""
        try:
            print("📡 Fetching Canary Media RSS feed...")
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                print(f"⚠️ Warning: Feed parsing issues detected")
            
            print(f"✅ Found {len(feed.entries)} articles")
            return feed.entries
            
        except Exception as e:
            print(f"❌ Error fetching RSS feed: {e}")
            return []
    
    def extract_article_content(self, article_url):
        """Extract full article content from URL"""
        try:
            headers = {
                'User-Agent': 'Canary Media Content Aggregator v1.0.0 (Educational/Research Purpose)'
            }
            
            response = requests.get(article_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article content - try multiple approaches
            content_selectors = [
                '[data-module="ArticleBody"]',  # Canary Media specific
                '.article-body',
                '.post-body',
                'article .content',
                '.article-content',
                '.post-content', 
                '.entry-content',
                '[class*="article-body"]',
                '[class*="post-body"]',
                'main article',
                'article',
                'main'
            ]
            
            article_text = ""
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Remove script, style, nav, footer elements
                    for unwanted in content_div.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                        unwanted.decompose()
                    
                    # Extract text
                    article_text = content_div.get_text(separator='\n', strip=True)
                    break
            
            if not article_text or len(article_text) < 200:
                # Fallback: try to get all paragraph text from main content areas
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    paragraphs = main_content.find_all('p')
                    paragraph_texts = [p.get_text(strip=True) for p in paragraphs 
                                     if p.get_text(strip=True) and len(p.get_text(strip=True)) > 20]
                    article_text = '\n\n'.join(paragraph_texts)
            
            # Clean up text
            article_text = re.sub(r'\n{3,}', '\n\n', article_text)  # Reduce excessive newlines
            article_text = re.sub(r'[ \t]+', ' ', article_text)      # Normalize whitespace
            
            return article_text.strip()
            
        except Exception as e:
            print(f"   ❌ Error extracting content from {article_url}: {e}")
            return ""
    
    def clean_title(self, title):
        """Clean title for use as section header"""
        # Remove HTML entities and clean up
        title = re.sub(r'&[a-zA-Z0-9#]+;', '', title)  # Remove HTML entities
        title = re.sub(r'[^\w\s\-\.\,\:\!]', '', title)  # Keep basic punctuation
        return title.strip()
    
    def format_date(self, published_parsed):
        """Format published date"""
        try:
            if published_parsed:
                dt = datetime(*published_parsed[:6])
                return dt.strftime('%B %d, %Y')
            return "Date Unknown"
        except:
            return "Date Unknown"
    
    def filter_articles_by_date(self, entries, target_date=None):
        """Filter articles by publication date"""
        if not target_date:
            target_date = datetime.now().date()
        
        filtered_entries = []
        for entry in entries:
            try:
                if entry.get('published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:3]).date()
                    if pub_date == target_date:
                        filtered_entries.append(entry)
            except:
                continue
        
        return filtered_entries
    
    def get_anthropic_client(self):
        """Initialize Anthropic client lazily"""
        if not self.anthropic_client:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self.anthropic_client
    
    def analyze_with_claude(self, content):
        """Send content to Claude for investment analysis"""
        try:
            print("🧠 Analyzing articles with Claude AI...")
            
            response = self.get_anthropic_client().messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user", 
                        "content": f"{self.analysis_prompt}\n\nArticles to analyze:\n\n{content}"
                    }
                ]
            )
            
            analysis = response.content[0].text
            print("✅ Analysis completed")
            return analysis
            
        except Exception as e:
            print(f"❌ Claude analysis failed: {e}")
            return None
    
    def send_email(self, subject, content, recipient="hwalker146@outlook.com"):
        """Send email with analysis"""
        try:
            print("📧 Sending analysis email...")
            
            # Get email credentials first - match unified automation format
            sender_email = os.getenv('EMAIL_FROM', 'aipodcastdigest@gmail.com')
            sender_password = os.getenv('EMAIL_PASSWORD')
            
            # Email configuration - detect provider from email address
            if sender_email and sender_email.endswith('@gmail.com'):
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
            else:
                smtp_server = "smtp-mail.outlook.com"
                smtp_port = 587
            
            if not sender_email or not sender_password:
                print("❌ Email credentials not found in environment variables")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add content
            msg.attach(MIMEText(content, 'plain'))
            
            # Send email - match unified automation method
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
            server.quit()
            
            print(f"✅ Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    
    def aggregate_articles(self, limit=None, date_filter=None, send_analysis=False):
        """Fetch all articles and aggregate content"""
        entries = self.fetch_rss_feed()
        
        if not entries:
            print("❌ No articles found")
            return
        
        # Filter by date if specified
        if date_filter:
            if date_filter == 'today':
                target_date = datetime.now().date()
                entries = self.filter_articles_by_date(entries, target_date)
                print(f"📅 Found {len(entries)} articles from today ({target_date})")
            elif date_filter == 'yesterday':
                from datetime import timedelta
                target_date = datetime.now().date() - timedelta(days=1)
                entries = self.filter_articles_by_date(entries, target_date)
                print(f"📅 Found {len(entries)} articles from yesterday ({target_date})")
        
        # Limit articles if specified
        if limit and not date_filter:
            entries = entries[:limit]
            print(f"📝 Processing first {limit} articles...")
        elif not date_filter:
            print(f"📝 Processing all {len(entries)} articles...")
        
        # Generate output content
        output_content = f"""# Canary Media - Clean Energy News Aggregation
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Source: {self.rss_url}
Total Articles: {len(entries)}

---

"""
        
        processed_count = 0
        for i, entry in enumerate(entries, 1):
            print(f"📄 Processing article {i}/{len(entries)}: {entry.title[:60]}...")
            
            title = self.clean_title(entry.title)
            published_date = self.format_date(entry.get('published_parsed'))
            article_url = entry.link
            
            # Try to get article content
            article_content = self.extract_article_content(article_url)
            
            if article_content:
                output_content += f"""## {title}
**Published:** {published_date}  
**URL:** {article_url}

{article_content}

---

"""
                processed_count += 1
            else:
                # Fallback to RSS summary if content extraction fails
                summary = entry.get('summary', 'No summary available')
                output_content += f"""## {title}
**Published:** {published_date}  
**URL:** {article_url}

*[Content extraction failed, showing RSS summary]*

{summary}

---

"""
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"canary_media_aggregated_{timestamp}.md"
        output_path = self.output_dir / filename
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        print(f"\n✅ Aggregation Complete!")
        print(f"📁 Output saved to: {output_path}")
        print(f"📊 Successfully processed: {processed_count}/{len(entries)} articles")
        
        # Perform Claude analysis and send email if requested
        if send_analysis and processed_count > 0:
            print(f"\n🔍 Performing investment analysis...")
            
            # Analyze content with Claude
            analysis = self.analyze_with_claude(output_content)
            
            if analysis:
                # Generate email subject
                date_str = datetime.now().strftime('%B %d, %Y')
                subject = f"Canary Media Investment Analysis - {date_str} ({processed_count} articles)"
                
                # Create email content
                email_content = f"""Daily Clean Energy Investment Analysis
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Articles Analyzed: {processed_count}

{analysis}

---

Full Article Text Available At:
{output_path}

This analysis was generated automatically using Claude AI based on the latest Canary Media articles.
"""
                
                # Send email
                email_success = self.send_email(subject, email_content)
                
                if email_success:
                    print(f"📧 Investment analysis emailed successfully!")
                else:
                    print(f"❌ Failed to send email, but analysis completed")
                    print(f"📋 Analysis saved to file for manual review")
            else:
                print(f"❌ Analysis failed, skipping email")
        
        return output_path

def main():
    """Main execution function"""
    print("🕊️ Canary Media RSS Aggregator")
    print("=" * 50)
    
    aggregator = CanaryMediaAggregator()
    
    # Process all articles from today with analysis and email
    print(f"\n📅 Processing all articles from today with investment analysis...")
    
    # Run aggregation
    try:
        output_path = aggregator.aggregate_articles(date_filter='today', send_analysis=True)
        
        if output_path:
            print(f"\n📖 Preview of output file:")
            print(f"   File: {output_path.name}")
            print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
        else:
            print(f"\n📅 No articles found for today. Trying yesterday...")
            output_path = aggregator.aggregate_articles(date_filter='yesterday', send_analysis=True)
            if output_path:
                print(f"\n📖 Preview of yesterday's output file:")
                print(f"   File: {output_path.name}")
                print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
            
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during aggregation: {e}")

if __name__ == "__main__":
    main()