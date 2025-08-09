#!/usr/bin/env python3
"""
Test script for RSS Intelligence System
Updates prompt and runs analysis for yesterday's news
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

async def test_with_custom_prompt():
    """Test system with custom prompt"""
    
    print("🔧 Setting up RSS Intelligence System...")
    
    # Initialize configuration (this creates config files)
    from config_manager import ConfigManager
    config = ConfigManager()
    
    print("✅ Configuration loaded")
    print(f"   RSS Feeds: {len(config.rss_feeds)}")
    print(f"   AI Provider: {config.ai_settings['provider']}")
    
    # Update the analysis prompt
    new_prompt = """Summarize in full sentences the main points about this article. What are the most important highlights? What trend does this follow? Why is this relevant to someone who is very interested in politics, the economy, infrastructure investing and finance?

Article to analyze:
{article_content}"""
    
    config.update_analysis_prompt(new_prompt)
    print("✅ Updated analysis prompt")
    
    # Test with a smaller subset of feeds for faster testing
    test_feeds = {
        "NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "NYT Economy": "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
        "WSJ Markets": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
        "Economist Business": "https://www.economist.com/business/rss.xml"
    }
    
    # Temporarily override feeds for testing
    original_feeds = config.rss_feeds.copy()
    config.rss_feeds = test_feeds
    
    print(f"🧪 Testing with {len(test_feeds)} feeds...")
    
    processor = None
    try:
        # Import main components
        from feed_processor import FeedProcessor
        from report_generator import ReportGenerator
        from email_sender import EmailSender
        
        # Initialize processor
        processor = FeedProcessor(config)
        
        print("📡 Processing RSS feeds...")
        articles = await processor.process_all_feeds()
        print(f"✅ Found {len(articles)} new articles")
        
        if articles:
            print("🧠 Analyzing articles with custom prompt...")
            analyzed_articles = await processor.analyze_articles(articles)
            print(f"✅ Analyzed {len(analyzed_articles)} articles")
            
            if analyzed_articles:
                # Generate report
                print("📄 Generating test report...")
                report_gen = ReportGenerator(config)
                report = await report_gen.generate_report(analyzed_articles)
                
                # Show sample analysis
                print("\n" + "="*60)
                print("🧪 SAMPLE ANALYSIS WITH CUSTOM PROMPT")
                print("="*60)
                
                for i, article in enumerate(analyzed_articles[:2]):  # Show first 2
                    print(f"\n📄 Article {i+1}: {article.title[:60]}...")
                    print(f"🔗 Source: {article.source}")
                    print(f"📊 Analysis: {article.analysis[:300]}...")
                    print("-" * 40)
                
                # Generate and save test report
                email_body = report_gen.generate_email_body(report)
                
                # Save test report locally
                test_report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(test_report_file, 'w') as f:
                    f.write(report_gen.generate_markdown_report(report))
                
                print(f"\n✅ Test report saved: {test_report_file}")
                print(f"📊 Total articles in report: {len(analyzed_articles)}")
                print(f"📧 Email body length: {len(email_body)} characters")
                
                # Optionally send test email
                print("\n📧 Sending test email...")
                email_sender = EmailSender(config)
                await email_sender.send_daily_report(report, analyzed_articles)
                
            else:
                print("⚠️ No articles were successfully analyzed")
        else:
            print("📧 No new articles found for testing")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore original feeds
        config.rss_feeds = original_feeds
        
        # Close any open connections
        if processor and hasattr(processor, 'article_extractor') and processor.article_extractor.session:
            await processor.article_extractor.close()

if __name__ == "__main__":
    asyncio.run(test_with_custom_prompt())