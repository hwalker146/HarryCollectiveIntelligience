#!/usr/bin/env python3
"""
WSJ Filtered Aggregator - Investment-focused filtering
Filters WSJ Business & Technology articles based on specific investment criteria
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

class WSJFilteredAggregator:
    def __init__(self):
        self.rss_urls = {
            "Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
            "Technology": "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
        }
        self.output_dir = Path(__file__).parent.parent / 'content' / 'wsj_filtered'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # WSJ credentials
        self.wsj_username = "harris.walker@lazard.com"
        self.wsj_password = "Iluvbanking146"
        
        # Initialize Claude API client
        self.anthropic_client = None
        
        # Investment filtering criteria
        self.relevant_industries = [
            'infrastructure', 'energy', 'healthcare', 'financial services', 
            'technology', 'industrials', 'utilities', 'renewable energy',
            'data center', 'payment', 'fintech', 'biotech', 'power',
            'transportation', 'telecom', 'banking', 'insurance'
        ]
        
        self.relevant_events = [
            'merger', 'acquisition', 'M&A', 'IPO', 'deal', 'transaction',
            'regulatory', 'regulation', 'policy', 'market trend', 'funding',
            'investment', 'capital', 'private equity', 'venture capital',
            'valuation', 'earnings', 'revenue', 'billion', 'million'
        ]
        
        self.excluded_topics = [
            'celebrity', 'entertainment', 'sports', 'retail', 'fashion',
            'restaurant', 'movie', 'music', 'gaming', 'social media',
            'consumer goods', 'apparel', 'luxury'
        ]
        
        self.financial_keywords = [
            '$100m', '$100 million', '$200m', '$300m', '$500m', '$1b', '$1 billion',
            'billion', 'market cap', 'valuation', 'acquisition', 'merger'
        ]
        
        # Financial analysis prompt
        self.analysis_prompt = """You are a financial analyst specializing in corporate strategy and investment. You will be given filtered Wall Street Journal Business and Technology articles that have been pre-screened for investment relevance. Your task is to produce a clear, concise, and investor-oriented summary.

Focus on:
- The main development or event (earnings, M&A, regulation, management, industry shifts)
- The business implications (competitive dynamics, risks, opportunities, financial impacts, market positioning)
- Any quantitative details (financial metrics, growth rates, valuations, deal sizes) that add clarity
- The short- and long-term relevance for investors and decision-makers

Output format:
Headline Insight – one sentence capturing the most important takeaway.
Summary - paragraph concise breakdown of key facts and implications.
Investor Lens – one short paragraph on how this development could affect corporate strategy, markets, or capital allocation."""
        
    def is_article_relevant(self, entry):
        """Filter articles based on investment criteria"""
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '').lower()
        content = f"{title} {summary}"
        
        # Exclude unwanted topics first
        for excluded in self.excluded_topics:
            if excluded in content:
                return False, f"Excluded: {excluded}"
        
        # Check for relevant industries
        industry_match = False
        matched_industry = ""
        for industry in self.relevant_industries:
            if industry in content:
                industry_match = True
                matched_industry = industry
                break
        
        # Check for relevant events
        event_match = False
        matched_event = ""
        for event in self.relevant_events:
            if event in content:
                event_match = True
                matched_event = event
                break
        
        # Check for financial significance
        financial_match = False
        matched_financial = ""
        for keyword in self.financial_keywords:
            if keyword in content:
                financial_match = True
                matched_financial = keyword
                break
        
        # Article is relevant if it matches industry AND (event OR financial significance)
        if industry_match and (event_match or financial_match):
            reason = f"Industry: {matched_industry}"
            if event_match:
                reason += f", Event: {matched_event}"
            if financial_match:
                reason += f", Financial: {matched_financial}"
            return True, reason
        
        # Also include if it has strong financial significance even without specific industry match
        if financial_match and event_match:
            return True, f"Financial: {matched_financial}, Event: {matched_event}"
        
        return False, "No relevant matches"
    
    def fetch_rss_feeds(self):
        """Fetch and parse multiple RSS feeds with filtering and deduplication"""
        all_entries = []
        filtered_count = 0
        seen_urls = set()  # Track URLs to avoid duplicates
        
        for feed_name, feed_url in self.rss_urls.items():
            try:
                print(f"📡 Fetching WSJ {feed_name} RSS feed...")
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    print(f"⚠️ Warning: Feed parsing issues detected for {feed_name}")
                
                feed_filtered = 0
                for entry in feed.entries:
                    entry['feed_category'] = feed_name
                    
                    # Check for duplicates first
                    article_url = entry.link
                    if article_url in seen_urls:
                        print(f"   🔄 {entry.title[:50]}... (Duplicate - skipped)")
                        continue
                    
                    # Apply filtering
                    is_relevant, reason = self.is_article_relevant(entry)
                    if is_relevant:
                        seen_urls.add(article_url)
                        all_entries.append(entry)
                        feed_filtered += 1
                        print(f"   ✅ {entry.title[:50]}... ({reason})")
                    else:
                        print(f"   🚫 {entry.title[:50]}... ({reason})")
                
                filtered_count += feed_filtered
                print(f"✅ {feed_name}: {feed_filtered}/{len(feed.entries)} articles passed filter")
                
            except Exception as e:
                print(f"❌ Error fetching {feed_name} RSS feed: {e}")
        
        print(f"📊 Total filtered articles: {filtered_count} (from {sum(len(feedparser.parse(url).entries) for url in self.rss_urls.values())} total)")
        return all_entries
    
    def extract_article_content(self, article_url):
        """Extract full article content from URL with WSJ authentication"""
        try:
            # Create session for WSJ login
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # First, try to get the article directly
            response = session.get(article_url, timeout=30)
            
            # If we get redirected to login or get 401/403, try to authenticate
            if response.status_code in [401, 403] or 'sign-in' in response.url.lower():
                print(f"   🔐 Authenticating with WSJ...")
                
                # Get login page
                login_url = "https://accounts.wsj.com/login"
                login_response = session.get(login_url)
                
                # Basic login attempt
                login_data = {
                    'username': self.wsj_username,
                    'password': self.wsj_password
                }
                
                auth_response = session.post(login_url, data=login_data, timeout=30)
                
                # Now try to get the article again
                response = session.get(article_url, timeout=30)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article content - WSJ specific selectors
            content_selectors = [
                '[data-module="ArticleBody"]',
                '.wsj-snippet-body',
                '.article-content',
                '.articleLead-container',
                'article .content',
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
            article_text = re.sub(r'\n{3,}', '\n\n', article_text)
            article_text = re.sub(r'[ \t]+', ' ', article_text)
            
            return article_text.strip()
            
        except Exception as e:
            print(f"   ❌ Error extracting content from {article_url}: {e}")
            return ""
    
    def clean_title(self, title):
        """Clean title for use as section header"""
        title = re.sub(r'&[a-zA-Z0-9#]+;', '', title)
        title = re.sub(r'[^\w\s\-\.\,\:\!\$\%]', '', title)
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
        """Send content to Claude for financial analysis"""
        try:
            print("🧠 Analyzing filtered articles with Claude AI...")
            
            response = self.get_anthropic_client().messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user", 
                        "content": f"{self.analysis_prompt}\n\nFiltered articles to analyze:\n\n{content}"
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
            print("📧 Sending filtered analysis email...")
            
            sender_email = os.getenv('EMAIL_FROM', 'aipodcastdigest@gmail.com')
            sender_password = os.getenv('EMAIL_PASSWORD')
            
            if not sender_email or not sender_password:
                print("❌ Email credentials not found in environment variables")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
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
        """Fetch and filter articles, then aggregate content"""
        entries = self.fetch_rss_feeds()
        
        if not entries:
            print("❌ No relevant articles found after filtering")
            return
        
        # Filter by date if specified
        if date_filter:
            if date_filter == 'today':
                target_date = datetime.now().date()
                entries = self.filter_articles_by_date(entries, target_date)
                print(f"📅 Found {len(entries)} relevant articles from today ({target_date})")
            elif date_filter == 'yesterday':
                target_date = datetime.now().date() - timedelta(days=1)
                entries = self.filter_articles_by_date(entries, target_date)
                print(f"📅 Found {len(entries)} relevant articles from yesterday ({target_date})")
        
        # Limit articles if specified
        if limit and len(entries) > limit:
            entries = entries[:limit]
            print(f"📝 Limited to first {limit} relevant articles...")
        
        # Generate output content
        output_content = f"""# WSJ Filtered Investment Analysis
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Sources: WSJ Business & Technology RSS Feeds (Filtered for Investment Relevance)
Articles Processed: {len(entries)}
Filter Criteria: Infrastructure, Energy, Healthcare, Financial Services, Technology, Industrials, Utilities
Focus: M&A, IPOs, Regulatory Changes, Market Trends ($300M+ market cap, $100M+ transactions)

---

"""
        
        processed_count = 0
        for i, entry in enumerate(entries, 1):
            print(f"📄 Processing article {i}/{len(entries)}: {entry.title[:60]}...")
            
            title = self.clean_title(entry.title)
            published_date = self.format_date(entry.get('published_parsed'))
            article_url = entry.link
            feed_category = entry.get('feed_category', 'Unknown')
            
            # Try to get article content
            article_content = self.extract_article_content(article_url)
            summary = entry.get('summary', 'No summary available')
            
            if article_content and len(article_content) > 200:
                # Use full content if successfully extracted
                output_content += f"""## [{feed_category}] {title}
**Published:** {published_date}  
**URL:** {article_url}

{article_content}

---

"""
                processed_count += 1
            elif summary and len(summary) > 20:
                # Use RSS summary (be less restrictive since auth isn't working)
                output_content += f"""## [{feed_category}] {title}
**Published:** {published_date}  
**URL:** {article_url}

{summary}

---

"""
                processed_count += 1
            else:
                # Use title only if no summary available
                output_content += f"""## [{feed_category}] {title}
**Published:** {published_date}  
**URL:** {article_url}

*[RSS summary not available - title only]*

---

"""
                processed_count += 1
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wsj_filtered_aggregated_{timestamp}.md"
        output_path = self.output_dir / filename
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        print(f"\n✅ Filtered Aggregation Complete!")
        print(f"📁 Output saved to: {output_path}")
        print(f"📊 Successfully processed: {processed_count}/{len(entries)} relevant articles")
        
        # Perform Claude analysis and send email if requested
        if send_analysis and processed_count > 0:
            print(f"\n🔍 Performing investment analysis on filtered content...")
            
            analysis = self.analyze_with_claude(output_content)
            
            if analysis:
                date_str = datetime.now().strftime('%B %d, %Y')
                subject = f"WSJ Filtered Investment Analysis - {date_str} ({processed_count} articles)"
                
                email_content = f"""Daily Filtered Investment Analysis
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Relevant Articles Analyzed: {processed_count}

Filter Applied: Infrastructure, Energy, Healthcare, Financial Services, Technology, Industrials, Utilities
Focus: M&A, IPOs, Regulatory Changes, Market Trends ($300M+ market cap, $100M+ transactions)

{analysis}

---

Full Article Text Available At:
{output_path}

This analysis was generated automatically using Claude AI based on filtered WSJ Business & Technology articles.
"""
                
                email_success = self.send_email(subject, email_content)
                
                if email_success:
                    print(f"📧 Filtered investment analysis emailed successfully!")
                else:
                    print(f"❌ Failed to send email, but analysis completed")
            else:
                print(f"❌ Analysis failed, skipping email")
        
        return output_path

def main():
    """Main execution function"""
    print("🎯 WSJ Filtered Investment Aggregator")
    print("=" * 50)
    
    aggregator = WSJFilteredAggregator()
    
    print(f"\n📅 Processing today's investment-relevant articles...")
    
    try:
        output_path = aggregator.aggregate_articles(date_filter='today', send_analysis=True)
        
        if output_path:
            print(f"\n📖 Preview of output file:")
            print(f"   File: {output_path.name}")
            print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
        else:
            print(f"\n📅 No relevant articles found for today. Trying yesterday...")
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