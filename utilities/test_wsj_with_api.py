#!/usr/bin/env python3
"""
Test the new WSJ aggregator with API key to show analysis format
"""
import os
import sys
sys.path.append('.')

# Set the API key temporarily from the main automation
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', '')

from utilities.wsj_expanded_aggregator import WSJExpandedAggregator

def test_single_article():
    aggregator = WSJExpandedAggregator()
    
    # Test with a sample article
    sample_title = "Walmart Wins Over More Shoppers as Tariffs Push Prices Higher"
    sample_content = """The retail giant missed its earnings target but reported that U.S. comparable sales rose 4.6% in the latest quarter. Walmart Inc. reported stronger-than-expected sales growth in the second quarter as the retailer benefited from higher prices due to tariffs and continued to attract customers seeking value. The company's U.S. comparable sales rose 4.6% in the quarter ended July 31, above analysts' expectations of 3.8% growth. Total revenue increased 4.8% to $169.3 billion, also beating estimates. However, Walmart's earnings per share of $0.67 fell short of the $0.68 consensus estimate, primarily due to higher operating expenses and investments in technology and store improvements."""
    
    print("🧪 Testing Paragraph-Only Analysis Format")
    print("=" * 50)
    print(f"Article: {sample_title}")
    print(f"Content: {sample_content[:200]}...")
    print("\n📝 Analysis:")
    
    try:
        analysis = aggregator.analyze_article_with_claude(sample_title, sample_content)
        print(analysis)
    except Exception as e:
        print(f"Error: {e}")
        print("\nFallback analysis (to show format):")
        print("Walmart's second-quarter performance demonstrates the complex dynamics facing retailers in the current economic environment. While the company exceeded sales growth expectations with a robust 4.6% increase in comparable sales, it fell short on earnings due to elevated operating costs and strategic investments in technology infrastructure. The revenue growth to $169.3 billion reflects both organic expansion and the price inflation effects from ongoing tariff policies, which have become a significant factor in retail pricing strategies. Walmart's ability to maintain customer loyalty during this period of rising prices underscores its competitive positioning as a value-oriented retailer, even as profit margins face pressure from increased operational spending and modernization efforts that prioritize long-term market share over immediate profitability.")

if __name__ == "__main__":
    test_single_article()