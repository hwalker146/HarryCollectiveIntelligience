#!/usr/bin/env python3
"""
Force test of custom prompt - bypasses article tracking
"""
import asyncio
import feedparser
from datetime import datetime

async def force_test():
    """Force test without article tracking"""
    
    print("🧪 Force Test - Custom Prompt Analysis")
    print("=" * 50)
    
    # Test with real article content
    test_article_content = """
Trump Administration Loosens 401(k) Investment Rules to Include Cryptocurrency

The Trump administration has issued new regulations that will allow Americans to invest their 401(k) retirement savings in cryptocurrency, private equity, and real estate investments for the first time. 

The Department of Labor announced the changes Wednesday, which reverse Obama-era restrictions that limited 401(k) investments to traditional stocks, bonds, and mutual funds. The new rules will take effect in 90 days.

"American workers deserve the freedom to invest their hard-earned retirement savings however they see fit," Labor Secretary said in a statement. "These outdated restrictions have prevented millions of Americans from accessing potentially lucrative investment opportunities."

The move fulfills a key campaign promise from Trump, who pledged to "unleash American innovation" in financial markets. Cryptocurrency advocates have long pushed for inclusion in retirement accounts, arguing that digital assets offer superior returns compared to traditional investments.

However, financial advisors warn that the new rules could expose retirees to significant risks. Cryptocurrency markets are notoriously volatile, with Bitcoin losing over 60% of its value in 2022 before recovering.

The changes are expected to benefit major cryptocurrency exchanges like Coinbase and Kraken, which have been preparing new 401(k) products. Several private equity firms have also announced plans to create retail-friendly investment vehicles.

Labor unions and some Democratic lawmakers criticized the move, calling it a "reckless gamble" with workers' retirement security.
"""
    
    # Initialize config with custom prompt
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    from config_manager import ConfigManager
    from ai_analyzer import AIAnalyzer
    
    config = ConfigManager()
    
    # Your custom prompt
    custom_prompt = """Summarize in full sentences the main points about this article. What are the most important highlights? What trend does this follow? Why is this relevant to someone who is very interested in politics, the economy, infrastructure investing and finance?

Article to analyze:
{article_content}"""
    
    config.update_analysis_prompt(custom_prompt)
    print("✅ Updated to your custom prompt")
    print(f"✅ AI Provider: {config.ai_settings['provider']}")
    print(f"✅ Model: {config.ai_settings['model']}")
    
    # Test analysis
    analyzer = AIAnalyzer(config)
    
    print("\n🧠 Testing analysis with sample article...")
    print("📄 Article: Trump 401(k) Cryptocurrency Rules")
    
    result = await analyzer.analyze_article(test_article_content)
    
    print("\n" + "=" * 60)
    print("📊 ANALYSIS WITH YOUR CUSTOM PROMPT:")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(force_test())