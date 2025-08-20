#!/usr/bin/env python3
"""
Test Claude analysis functionality without email
"""
import os
from canary_media_aggregator import CanaryMediaAggregator

def main():
    print("🧪 Testing Claude Analysis Functionality")
    print("=" * 50)
    
    # Check if ANTHROPIC_API_KEY is set
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        print("Please set it first: export ANTHROPIC_API_KEY=your_key_here")
        return
    
    aggregator = CanaryMediaAggregator()
    
    # Test with just 1 article to verify analysis works
    try:
        print("\n🔍 Testing with 1 article (no email)...")
        output_path = aggregator.aggregate_articles(limit=1, send_analysis=False)
        
        if output_path:
            # Read the content and test Claude analysis
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📊 Testing Claude analysis on content...")
            analysis = aggregator.analyze_with_claude(content)
            
            if analysis:
                print(f"\n✅ Claude Analysis Results:")
                print("=" * 40)
                print(analysis)
                print("=" * 40)
                print(f"\n🎯 Analysis successful! Ready for email integration.")
            else:
                print(f"\n❌ Analysis failed")
        else:
            print(f"\n❌ No articles found to analyze")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()