#!/usr/bin/env python3
"""
Quick summary of new episodes detected per podcast
"""
import sqlite3
import feedparser
import requests
from datetime import datetime

def quick_detection_summary():
    """Quick summary of truly new episodes (after newest DB episode) by podcast"""
    print("🔍 EPISODE DETECTION SUMMARY (TRULY NEW ONLY)...")
    
    db_path = 'podcast_app_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all podcasts
    cursor.execute('SELECT id, name, rss_url FROM podcasts ORDER BY name')
    podcasts = cursor.fetchall()
    
    summary = []
    total_new = 0
    
    for podcast_id, podcast_name, rss_url in podcasts:
        try:
            # Get newest episode date
            cursor.execute('''
                SELECT MAX(publish_date) 
                FROM episodes 
                WHERE podcast_id = ? AND publish_date IS NOT NULL
            ''', (podcast_id,))
            
            newest_date = cursor.fetchone()[0]
            if not newest_date:
                summary.append(f"⚪ {podcast_name}: No episodes in DB")
                continue
                
            newest_db_date = datetime.fromisoformat(newest_date.replace('Z', '+00:00'))
            
            # Get existing episodes for matching
            cursor.execute('SELECT guid, audio_url, title FROM episodes WHERE podcast_id = ?', (podcast_id,))
            existing_episodes = set()
            for guid, audio_url, title in cursor.fetchall():
                if guid: existing_episodes.add(guid)
                if audio_url: existing_episodes.add(audio_url)
                if title: existing_episodes.add(title)
            
            # Fetch RSS feed
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            if feed.bozo:
                summary.append(f"❌ {podcast_name}: Feed error")
                continue
            
            new_count = 0
            
            for entry in feed.entries:
                episode_title = entry.title if hasattr(entry, 'title') else None
                
                # Get audio URL
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if not audio_url:
                    continue
                
                episode_guid = getattr(entry, 'id', None) or audio_url
                
                # Check if episode exists
                episode_exists = (
                    (episode_guid and episode_guid in existing_episodes) or
                    (audio_url and audio_url in existing_episodes) or  
                    (episode_title and episode_title in existing_episodes)
                )
                
                if not episode_exists:
                    # Parse date
                    episode_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        episode_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'published'):
                        try:
                            episode_date = datetime.fromisoformat(entry.published)
                        except:
                            episode_date = None
                    
                    # Check if truly new (after newest DB episode)
                    if episode_date:
                        episode_naive = episode_date.replace(tzinfo=None) if episode_date.tzinfo else episode_date
                        newest_naive = newest_db_date.replace(tzinfo=None) if newest_db_date.tzinfo else newest_db_date
                        
                        if episode_naive > newest_naive:
                            new_count += 1
            
            summary.append(f"{'✅' if new_count == 0 else '🆕'} {podcast_name}: {new_count} truly new episodes")
            total_new += new_count
            
        except Exception as e:
            summary.append(f"❌ {podcast_name}: Error - {str(e)[:50]}")
    
    conn.close()
    
    # Print summary
    for line in summary:
        print(line)
    
    print(f"\n🎯 TOTAL TRULY NEW EPISODES: {total_new}")

if __name__ == "__main__":
    quick_detection_summary()