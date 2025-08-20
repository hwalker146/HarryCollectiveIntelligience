#!/usr/bin/env python3
"""
WSJ Business Daily Aggregator
Command-line version for processing articles by date
Usage: python wsj_business_daily.py [today|yesterday|all|NUMBER]
"""
import sys
from wsj_business_aggregator import WSJAggregator

def main():
    aggregator = WSJAggregator()
    
    # Parse command line argument
    if len(sys.argv) > 1:
        option = sys.argv[1].lower()
    else:
        option = 'today'  # Default to today
    
    print("💼 WSJ Business Daily Aggregator")
    print("=" * 50)
    
    try:
        if option == 'today':
            print(f"\n📅 Processing all articles from today with financial analysis...")
            output_path = aggregator.aggregate_articles(date_filter='today', send_analysis=True)
            
        elif option == 'yesterday':
            print(f"\n📅 Processing all articles from yesterday with financial analysis...")
            output_path = aggregator.aggregate_articles(date_filter='yesterday', send_analysis=True)
            
        elif option == 'all':
            print(f"\n📝 Processing ALL articles with financial analysis (this may take a while)...")
            output_path = aggregator.aggregate_articles(send_analysis=True)
            
        elif option.isdigit():
            limit = int(option)
            print(f"\n📝 Processing first {limit} articles with financial analysis...")
            output_path = aggregator.aggregate_articles(limit=limit, send_analysis=True)
            
        else:
            print(f"\n❌ Invalid option: {option}")
            print("Usage: python wsj_business_daily.py [today|yesterday|all|NUMBER]")
            return
        
        if output_path:
            print(f"\n📖 Output file created:")
            print(f"   File: {output_path.name}")
            print(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
            print(f"   Path: {output_path}")
        else:
            print(f"\n📅 No articles found for the specified criteria")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()