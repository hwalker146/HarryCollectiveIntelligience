#!/usr/bin/env python3
"""
Process a single podcast at a time to avoid timeouts
"""
import os
import sys
import sqlite3
from enhanced_automation import EnhancedPodcastSystem
from datetime import datetime

def process_single_podcast(podcast_name):
    print(f"🎧 Processing {podcast_name}...")
    
    automation = EnhancedPodcastSystem()
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get podcast info
    cursor.execute("SELECT id, rss_url FROM podcasts WHERE name = ?", (podcast_name,))
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ Podcast not found: {podcast_name}")
        return
    
    podcast_id, rss_url = result
    
    # Parse RSS feed
    rss_data = automation.parse_rss_feed(rss_url)
    if not rss_data["success"]:
        print(f"❌ RSS failed: {rss_data['error']}")
        return
    
    cutoff_date = datetime(2024, 12, 1)
    episodes_to_process = []
    
    for episode_data in rss_data["episodes"]:
        if not episode_data.get('publish_date'):
            continue
        
        try:
            episode_dt = datetime.fromisoformat(episode_data['publish_date'].replace('Z', '+00:00'))
            episode_dt = episode_dt.replace(tzinfo=None)
        except:
            continue
        
        if episode_dt >= cutoff_date:
            # Check if already exists
            cursor.execute('''
                SELECT id FROM episodes 
                WHERE podcast_id = ? AND (title = ? OR guid = ? OR audio_url = ?)
            ''', (podcast_id, episode_data['title'], episode_data.get('guid'), episode_data.get('audio_url')))
            
            if not cursor.fetchone():
                episode_data['podcast_id'] = podcast_id
                episode_data['podcast_name'] = podcast_name
                episodes_to_process.append(episode_data)
                print(f"📝 Found: {episode_data['title'][:50]}...")
    
    conn.close()
    
    if episodes_to_process:
        print(f"🔧 Processing {len(episodes_to_process)} episodes...")
        
        # Process just first 3 episodes for now
        batch = episodes_to_process[:3]
        processed = automation.process_new_episodes(batch)
        
        if processed:
            automation.append_to_master_files(processed)
            print(f"✅ Successfully processed {len(processed)} episodes")
        else:
            print("❌ No episodes processed successfully")
    else:
        print("📭 No new episodes to process")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_single_podcast.py 'Podcast Name'")
        sys.exit(1)
    
    process_single_podcast(sys.argv[1])