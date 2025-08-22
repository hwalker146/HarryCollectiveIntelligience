#!/usr/bin/env python3
"""
Quick script to process today's new episodes
"""
import sys
import os
sys.path.append('automation')

from unified_podcast_automation import EnhancedPodcastSystem

def main():
    print("🚀 Processing today's new episodes...")
    
    try:
        automation = EnhancedPodcastSystem()
        automation.run_daily_automation()
        print("✅ Automation completed successfully!")
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()