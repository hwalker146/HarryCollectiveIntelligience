#!/usr/bin/env python3
"""
Test automation logic locally to see what episodes it would process
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.unified_podcast_automation import EnhancedPodcastSystem

def test_locally():
    print("🔍 TESTING AUTOMATION LOCALLY")
    print("=" * 50)
    
    # Initialize system
    system = EnhancedPodcastSystem()
    
    # Check for new episodes without processing them
    episodes = system.check_rss_for_new_episodes()
    
    print(f"\n📊 RESULTS:")
    print(f"Episodes that would be processed: {len(episodes)}")
    
    if episodes:
        print(f"\n📝 Episodes to process:")
        for episode in episodes:
            status = "NEW" if not episode.get('existing_episode_id') else "RETRANSCRIBE"
            print(f"  {status}: {episode['podcast_name']} - {episode['title'][:60]}...")
    else:
        print("✅ No episodes to process - automation would be fast!")

if __name__ == "__main__":
    test_locally()