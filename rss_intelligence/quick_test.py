#!/usr/bin/env python3
"""
Quick test of custom prompt with just 2 articles
"""
import asyncio
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def quick_test():
    """Test custom prompt with just a few articles"""
    
    print("🧪 Quick RSS Intelligence Test")
    print("=" * 40)
    
    # Initialize config and set custom prompt
    from config_manager import ConfigManager
    config = ConfigManager()
    
    # Your custom prompt
    custom_prompt = """Summarize in full sentences the main points about this article. What are the most important highlights? What trend does this follow? Why is this relevant to someone who is very interested in politics, the economy, infrastructure investing and finance?

Article to analyze:
{article_content}"""
    
    config.update_analysis_prompt(custom_prompt)
    print("✅ Updated to custom prompt")
    
    # Test with just NYT Business feed
    from feed_processor import FeedProcessor
    processor = FeedProcessor(config)
    
    # Override to just one feed for faster testing
    config.rss_feeds = {"NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"}
    
    print("📡 Fetching articles from NYT Business...")
    articles = await processor.process_all_feeds()
    
    if articles:
        print(f"✅ Found {len(articles)} articles")
        
        # Take just the first 2 for testing
        test_articles = articles[:2]
        print(f"🧠 Testing analysis on {len(test_articles)} articles...")
        
        analyzed = await processor.analyze_articles(test_articles)
        
        if analyzed:
            print(f"✅ Successfully analyzed {len(analyzed)} articles")
            print("\n" + "=" * 60)
            print("📊 SAMPLE ANALYSIS WITH YOUR CUSTOM PROMPT:")
            print("=" * 60)
            
            for i, article in enumerate(analyzed):
                print(f"\n📄 Article {i+1}: {article.title}")
                print(f"🔗 URL: {article.url}")
                print(f"📊 ANALYSIS:\n{article.analysis}")
                print("-" * 40)
        else:
            print("❌ Analysis failed")
    else:
        print("📧 No articles found")
    
    # Close connections
    if hasattr(processor, 'article_extractor') and processor.article_extractor.session:
        await processor.article_extractor.close()

if __name__ == "__main__":
    asyncio.run(quick_test())