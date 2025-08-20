#!/usr/bin/env python3
"""
Canary Media Analysis - Generate investment analysis without email dependency
"""
from canary_media_aggregator import CanaryMediaAggregator
from datetime import datetime

def main():
    print("🕊️ Canary Media Investment Analysis")
    print("=" * 50)
    
    aggregator = CanaryMediaAggregator()
    
    # Process today's articles and generate analysis
    try:
        print(f"\n📅 Processing today's articles with investment analysis...")
        output_path = aggregator.aggregate_articles(date_filter='today', send_analysis=False)
        
        if output_path:
            # Read the content and generate analysis
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n🧠 Generating investment analysis...")
            analysis = aggregator.analyze_with_claude(content)
            
            if analysis:
                # Save analysis to separate file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                analysis_path = output_path.parent / f"investment_analysis_{timestamp}.txt"
                
                # Create email-ready content
                date_str = datetime.now().strftime('%B %d, %Y')
                email_content = f"""Subject: Canary Media Investment Analysis - {date_str}

Daily Clean Energy Investment Analysis
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

{analysis}

---

Full Article Text Available At:
{output_path}

This analysis was generated automatically using Claude AI based on the latest Canary Media articles.
"""
                
                # Save analysis
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    f.write(email_content)
                
                print(f"\n✅ Analysis Complete!")
                print(f"📁 Articles saved to: {output_path.name}")
                print(f"📧 Email-ready analysis saved to: {analysis_path.name}")
                print(f"📋 Analysis size: {analysis_path.stat().st_size / 1024:.1f} KB")
                
                print(f"\n📧 To email the analysis:")
                print(f"   Recipient: hwalker146@outlook.com")
                print(f"   Copy content from: {analysis_path}")
                
                # Also display the analysis
                print(f"\n🔍 INVESTMENT ANALYSIS:")
                print("=" * 60)
                print(analysis)
                print("=" * 60)
                
            else:
                print(f"\n❌ Analysis generation failed")
        else:
            print(f"\n📅 No articles found for today")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()