#!/usr/bin/env python3
"""
Test RSS system with free sources and brief summaries
"""
import asyncio
import os
import json

os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def test_free_sources():
    """Test with free sources only"""
    
    print("🧪 Testing Free Sources + Brief Summaries")
    print("=" * 50)
    
    from config_manager import ConfigManager
    config = ConfigManager()
    
    # Load free sources
    with open('config/rss_feeds_free.json', 'r') as f:
        free_feeds = json.load(f)
    
    # Use only first 3 for faster testing
    test_feeds = dict(list(free_feeds.items())[:3])
    config.rss_feeds = test_feeds
    
    print(f"✅ Testing {len(test_feeds)} free sources:")
    for name, url in test_feeds.items():
        print(f"   📡 {name}")
    
    # Clear cache to get fresh articles
    if os.path.exists('processed_articles.json'):
        os.remove('processed_articles.json')
    
    from feed_processor import FeedProcessor
    processor = FeedProcessor(config)
    
    print("\n📡 Processing feeds...")
    articles = await processor.process_all_feeds()
    
    if articles:
        print(f"✅ Found {len(articles)} articles")
        
        # Test first few
        test_articles = articles[:3]
        print(f"\n🧠 Testing brief analysis on {len(test_articles)} articles...")
        
        analyzed = await processor.analyze_articles(test_articles)
        
        if analyzed:
            print(f"✅ Successfully analyzed {len(analyzed)} articles")
            print("\n" + "=" * 60)
            print("📊 BRIEF SUMMARIES:")
            print("=" * 60)
            
            for i, article in enumerate(analyzed):
                print(f"\n📄 Article {i+1}: {article.title}")
                print(f"🔗 Source: {article.source}")
                print(f"📊 Brief Summary: {article.analysis}")
                print("-" * 40)
        else:
            print("❌ Analysis failed")
    else:
        print("📧 No articles found")
    
    # Close connections
    if hasattr(processor, 'article_extractor') and processor.article_extractor.session:
        await processor.article_extractor.close()

if __name__ == "__main__":
    asyncio.run(test_free_sources())