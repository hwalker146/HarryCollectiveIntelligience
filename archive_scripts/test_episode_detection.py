#!/usr/bin/env python3
"""
Test script to detect new episodes without processing them
"""
import sqlite3
import feedparser
import requests
from datetime import datetime, date
from pathlib import Path

def test_episode_detection():
    """Test episode detection for all podcasts"""
    print("🔍 TESTING EPISODE DETECTION...")
    
    db_path = 'podcast_app_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all podcasts
    cursor.execute('SELECT id, name, rss_url FROM podcasts ORDER BY name')
    podcasts = cursor.fetchall()
    
    total_new_episodes = 0
    
    for podcast_id, podcast_name, rss_url in podcasts:
        print(f"\n📡 {podcast_name}")
        print(f"   RSS: {rss_url}")
        
        try:
            # Get existing episodes from database
            cursor.execute('''
                SELECT COUNT(*) as episode_count,
                       MIN(publish_date) as oldest_date,
                       MAX(publish_date) as newest_date
                FROM episodes 
                WHERE podcast_id = ?
            ''', (podcast_id,))
            
            episode_count, oldest_date, newest_date = cursor.fetchone()
            
            cursor.execute('''
                SELECT guid, audio_url, title FROM episodes 
                WHERE podcast_id = ?
            ''', (podcast_id,))
            
            existing_episodes = set()
            for guid, audio_url, title in cursor.fetchall():
                # Add all possible identifiers for this episode
                if guid:
                    existing_episodes.add(guid)
                if audio_url:
                    existing_episodes.add(audio_url)
                if title:
                    existing_episodes.add(title)
            
            print(f"   📊 Database: {episode_count} episodes, oldest: {oldest_date}, newest: {newest_date}")
            
            # Fetch RSS feed
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"   ❌ Feed parse error: {feed.bozo_exception}")
                continue
            
            print(f"   📋 RSS Feed: {len(feed.entries)} episodes available")
            
            new_episodes = []
            
            for entry in feed.entries:
                # Extract episode info
                episode_title = entry.title if hasattr(entry, 'title') else None
                
                # Get audio URL
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if not audio_url:
                    continue
                
                # Parse publication date
                publish_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    publish_date = datetime(*entry.published_parsed[:6]).isoformat()
                elif hasattr(entry, 'published'):
                    publish_date = entry.published
                
                episode_guid = getattr(entry, 'id', None) or audio_url
                
                # Check if this episode exists in our database using any identifier
                episode_exists = (
                    (episode_guid and episode_guid in existing_episodes) or
                    (audio_url and audio_url in existing_episodes) or  
                    (episode_title and episode_title in existing_episodes)
                )
                
                # If episode doesn't exist, it's new
                if not episode_exists:
                    new_episodes.append({
                        'title': episode_title,
                        'audio_url': audio_url,
                        'publish_date': publish_date,
                        'guid': episode_guid
                    })
            
            print(f"   🆕 NEW EPISODES DETECTED: {len(new_episodes)}")
            total_new_episodes += len(new_episodes)
            
            for i, episode in enumerate(new_episodes, 1):
                publish_date_short = episode['publish_date'][:10] if episode['publish_date'] else 'Unknown'
                print(f"      {i}. [{publish_date_short}] {episode['title']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    conn.close()
    
    print(f"\n🎯 DETECTION COMPLETE")
    print(f"📈 Total new episodes across all podcasts: {total_new_episodes}")

if __name__ == "__main__":
    test_episode_detection()