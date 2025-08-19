#!/usr/bin/env python3
"""
Debug RSS feed to see what episodes are being detected as new
"""
import sqlite3
import feedparser
import requests
from datetime import datetime

def debug_rss_episodes(podcast_name_filter):
    """Debug specific RSS feed to see detected episodes"""
    print(f"🔍 DEBUGGING RSS FEED FOR: {podcast_name_filter}")
    
    db_path = 'podcast_app_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get podcast
    cursor.execute('SELECT id, name, rss_url FROM podcasts WHERE name LIKE ?', (f'%{podcast_name_filter}%',))
    podcast_data = cursor.fetchone()
    
    if not podcast_data:
        print(f"❌ Podcast not found: {podcast_name_filter}")
        return
    
    podcast_id, podcast_name, rss_url = podcast_data
    print(f"🎧 {podcast_name}")
    print(f"   RSS: {rss_url}")
    
    # Get database info
    cursor.execute('''
        SELECT MIN(publish_date), MAX(publish_date), COUNT(*) 
        FROM episodes 
        WHERE podcast_id = ? AND publish_date IS NOT NULL
    ''', (podcast_id,))
    
    oldest_date, newest_date, episode_count = cursor.fetchone()
    print(f"   📊 Database: {episode_count} episodes, {oldest_date} to {newest_date}")
    
    # Parse dates
    oldest_db_date = datetime.fromisoformat(oldest_date.replace('Z', '+00:00')) if oldest_date else None
    newest_db_date = datetime.fromisoformat(newest_date.replace('Z', '+00:00')) if newest_date else None
    
    # Get existing episodes
    cursor.execute('SELECT guid, audio_url, title FROM episodes WHERE podcast_id = ?', (podcast_id,))
    existing_episodes = set()
    for guid, audio_url, title in cursor.fetchall():
        if guid: existing_episodes.add(guid)
        if audio_url: existing_episodes.add(audio_url)
        if title: existing_episodes.add(title)
    
    print(f"   📝 {len(existing_episodes)} existing episode identifiers in database")
    
    # Fetch RSS feed
    try:
        headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
        response = requests.get(rss_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        print(f"   📡 RSS Feed: {len(feed.entries)} episodes available")
        
        episodes_checked = 0
        new_episodes = []
        
        for entry in feed.entries:
            episodes_checked += 1
            if episodes_checked > 20:  # Limit for debugging
                print(f"   ... (stopped after checking first 20 episodes)")
                break
            
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
            episode_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                episode_date = datetime(*entry.published_parsed[:6])
                publish_date = episode_date.isoformat()
            elif hasattr(entry, 'published'):
                publish_date = entry.published
                try:
                    episode_date = datetime.fromisoformat(publish_date)
                except:
                    episode_date = None
            
            episode_guid = getattr(entry, 'id', None) or audio_url
            
            # Check if episode exists
            episode_exists = (
                (episode_guid and episode_guid in existing_episodes) or
                (audio_url and audio_url in existing_episodes) or  
                (episode_title and episode_title in existing_episodes)
            )
            
            print(f"   {episodes_checked:2d}. [{publish_date[:10] if publish_date else 'No Date'}] {episode_title}")
            print(f"       GUID: {episode_guid}")
            print(f"       Exists: {episode_exists}")
            
            if not episode_exists:
                # Replicate automation logic
                is_gap = False
                is_new = False
                
                if episode_date:
                    # Convert to naive datetime for comparison
                    episode_naive = episode_date.replace(tzinfo=None) if episode_date.tzinfo else episode_date
                    oldest_naive = oldest_db_date.replace(tzinfo=None) if oldest_db_date and oldest_db_date.tzinfo else oldest_db_date
                    newest_naive = newest_db_date.replace(tzinfo=None) if newest_db_date and newest_db_date.tzinfo else newest_db_date
                    
                    print(f"       Episode date: {episode_naive}")
                    print(f"       DB range: {oldest_naive} to {newest_naive}")
                    
                    # Check if episode falls within existing date range (gap) or is newer (new episode)
                    if oldest_naive and newest_naive:
                        if oldest_naive <= episode_naive <= newest_naive:
                            is_gap = True
                            print(f"       -> GAP (between existing episodes)")
                        elif episode_naive > newest_naive:
                            is_new = True
                            print(f"       -> NEW (newer than newest)")
                        else:
                            print(f"       -> OLDER than oldest episode (should skip)")
                    elif not oldest_naive and not newest_naive:
                        is_new = True
                        print(f"       -> NEW (no episodes in DB)")
                    elif episode_naive and newest_naive and episode_naive > newest_naive:
                        is_new = True
                        print(f"       -> NEW (newer than newest)")
                else:
                    is_new = episode_count == 0
                    print(f"       -> NEW (no date, treat as new: {is_new})")
                
                if is_gap or is_new:
                    new_episodes.append(episode_title)
                    print(f"       ✅ WOULD BE PROCESSED")
                else:
                    print(f"       ❌ WOULD BE SKIPPED")
            
            print()
        
        print(f"🎯 SUMMARY:")
        print(f"   RSS episodes checked: {episodes_checked}")
        print(f"   New episodes detected: {len(new_episodes)}")
        if new_episodes:
            print(f"   Episodes that would be processed:")
            for i, title in enumerate(new_episodes, 1):
                print(f"      {i}. {title}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    debug_rss_episodes("a16z")