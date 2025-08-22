#!/usr/bin/env python3
"""
Compare filtering approaches - old vs new
"""
import feedparser
from datetime import datetime, timedelta

def old_filtering(entry):
    """Original tight filtering"""
    relevant_industries = [
        'infrastructure', 'energy', 'healthcare', 'financial services', 
        'technology', 'industrials', 'utilities', 'renewable energy',
        'data center', 'payment', 'fintech', 'biotech', 'power',
        'transportation', 'telecom', 'banking', 'insurance'
    ]
    
    relevant_events = [
        'merger', 'acquisition', 'M&A', 'IPO', 'deal', 'transaction',
        'regulatory', 'regulation', 'policy', 'market trend', 'funding',
        'investment', 'capital', 'private equity', 'venture capital',
        'valuation', 'earnings', 'revenue', 'billion', 'million'
    ]
    
    excluded_topics = [
        'celebrity', 'entertainment', 'sports', 'retail', 'fashion',
        'restaurant', 'movie', 'music', 'gaming', 'social media',
        'consumer goods', 'apparel', 'luxury'
    ]
    
    title = entry.get('title', '').lower()
    summary = entry.get('summary', '').lower()
    content = f"{title} {summary}"
    
    # Exclude unwanted topics first
    for excluded in excluded_topics:
        if excluded in content:
            return False, f"Excluded: {excluded}"
    
    # Must match industry AND event
    industry_match = any(industry in content for industry in relevant_industries)
    event_match = any(event in content for event in relevant_events)
    
    if industry_match and event_match:
        return True, "Included: industry + event match"
    
    return False, "No industry + event match"

def new_filtering(entry):
    """New relaxed filtering"""
    relevant_categories = [
        'business', 'finance', 'economics', 'markets', 'technology', 'policy',
        'regulation', 'government', 'corporate', 'industry', 'trade', 'investment',
        'banking', 'insurance', 'healthcare', 'energy', 'infrastructure', 'manufacturing',
        'transportation', 'telecommunications', 'media', 'real estate', 'commodities'
    ]
    
    excluded_topics = [
        'celebrity gossip', 'entertainment news', 'sports scores', 'weather',
        'horoscope', 'recipe', 'fashion week', 'movie review', 'music album'
    ]
    
    title = entry.get('title', '').lower()
    summary = entry.get('summary', '').lower()
    content = f"{title} {summary}"
    
    # Only exclude clearly irrelevant content
    for excluded in excluded_topics:
        if excluded in content:
            return False, f"Excluded: {excluded}"
    
    # Much broader inclusion criteria
    for category in relevant_categories:
        if category in content:
            return True, f"Included: {category}"
    
    # Default to inclusion
    return True, "Included: general business relevance"

def compare_filtering():
    print("🔍 Comparing Old vs New WSJ Filtering Approaches")
    print("=" * 60)
    
    rss_urls = {
        "Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
        "Technology": "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
    }
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    total_articles = 0
    old_included = 0
    new_included = 0
    
    for feed_name, rss_url in rss_urls.items():
        print(f"\n📡 Processing {feed_name} feed...")
        
        try:
            feed = feedparser.parse(rss_url)
            recent_articles = []
            
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date >= cutoff_time:
                        recent_articles.append(entry)
            
            print(f"   Recent articles (24h): {len(recent_articles)}")
            total_articles += len(recent_articles)
            
            # Test both filtering approaches
            old_count = 0
            new_count = 0
            
            for entry in recent_articles:
                old_relevant, old_reason = old_filtering(entry)
                new_relevant, new_reason = new_filtering(entry)
                
                if old_relevant:
                    old_count += 1
                if new_relevant:
                    new_count += 1
            
            print(f"   Old filtering: {old_count} articles")
            print(f"   New filtering: {new_count} articles")
            print(f"   Improvement: +{new_count - old_count} articles ({((new_count/old_count - 1) * 100):.1f}% increase)" if old_count > 0 else f"   Improvement: +{new_count} articles")
            
            old_included += old_count
            new_included += new_count
            
        except Exception as e:
            print(f"   Error: {e}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total recent articles: {total_articles}")
    print(f"Old filtering included: {old_included} ({(old_included/total_articles*100):.1f}%)")
    print(f"New filtering included: {new_included} ({(new_included/total_articles*100):.1f}%)")
    print(f"Net improvement: +{new_included - old_included} articles ({((new_included/old_included - 1) * 100):.1f}% increase)" if old_included > 0 else f"Net improvement: +{new_included} articles")

if __name__ == "__main__":
    compare_filtering()