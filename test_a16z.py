#!/usr/bin/env python3
"""
Test script to check for new a16z episodes and process them
"""
import sys
import os
sys.path.append('automation')

from unified_podcast_automation import EnhancedPodcastSystem

def test_a16z():
    automation = EnhancedPodcastSystem()
    
    # Get a16z podcast info
    conn = automation.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, rss_url FROM podcasts WHERE name = 'a16z Podcast'")
    podcast = cursor.fetchone()
    
    if not podcast:
        print("❌ a16z Podcast not found in database")
        return
    
    podcast_id, name, rss_url = podcast
    print(f"🎙️ Found {name}")
    print(f"📡 RSS: {rss_url}")
    
    # Check for new episodes in the last 2 days
    episodes = automation.fetch_podcast_episodes(rss_url, name, limit_episodes=5)
    
    if not episodes:
        print("📭 No episodes found in RSS feed")
        return
    
    print(f"📝 Found {len(episodes)} recent episodes in RSS:")
    for episode in episodes:
        print(f"  • {episode['title']}")
        print(f"    Published: {episode['publish_date']}")
        print(f"    Audio URL: {episode['audio_url'][:80]}...")
        
        # Check if already in database
        cursor.execute('SELECT id, transcribed, processed FROM episodes WHERE audio_url = ?', (episode['audio_url'],))
        existing = cursor.fetchone()
        
        if existing:
            print(f"    Status: Already in DB (transcribed={existing[1]}, processed={existing[2]})")
        else:
            print(f"    Status: NEW - not in database")
            
            # Process this new episode
            print(f"🔄 Processing new episode: {episode['title']}")
            try:
                automation.process_episode(episode, podcast_id, name)
                print(f"✅ Successfully processed episode")
            except Exception as e:
                print(f"❌ Failed to process episode: {e}")
        
        print()
    
    conn.close()

if __name__ == "__main__":
    test_a16z()