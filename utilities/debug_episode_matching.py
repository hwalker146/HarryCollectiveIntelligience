#!/usr/bin/env python3
"""
Debug Episode Matching
Check why episodes aren't being recognized as existing
"""
import sqlite3
import feedparser
import requests

def debug_episode_matching():
    # Check multiple podcasts
    podcasts = [
        ("The Infrastructure Investor", "https://feed.podbean.com/infrastructureinvestorpodcast/feed.xml"),
        ("Crossroads: The Infrastructure Podcast", "https://feeds.acast.com/public/shows/crossroads-the-infrastructure-podcast"),
        ("The Intelligence", "https://economist-espresso-app.s3.amazonaws.com/rss-20230607.xml")
    ]
    
    for podcast_name, rss_url in podcasts[:1]:  # Just check first one for now
    
    print("🔍 DEBUGGING EPISODE MATCHING")
    print("=" * 50)
    
    # Get existing episodes from database
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT guid, audio_url, title FROM episodes 
        WHERE podcast_id = (SELECT id FROM podcasts WHERE name = 'The Infrastructure Investor')
        ORDER BY created_at DESC
        LIMIT 5
    ''')
    
    db_episodes = cursor.fetchall()
    print(f"📊 Database episodes (latest 5):")
    for guid, audio_url, title in db_episodes:
        print(f"  GUID: {guid}")
        print(f"  URL:  {audio_url}")  
        print(f"  TITLE: {title}")
        print(f"  ---")
    
    # Get RSS episodes
    print(f"\n📡 RSS Feed episodes (latest 5):")
    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
    response = requests.get(rss_url, headers=headers, timeout=30)
    feed = feedparser.parse(response.content)
    
    for i, entry in enumerate(feed.entries[:5]):
        # Extract audio URL
        audio_url = None
        for enclosure in getattr(entry, 'enclosures', []):
            if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                audio_url = enclosure.href
                break
        
        episode_title = getattr(entry, 'title', 'Unknown Title')
        episode_guid = getattr(entry, 'id', None) or audio_url
        
        print(f"  GUID: {episode_guid}")
        print(f"  URL:  {audio_url}")
        print(f"  TITLE: {episode_title}")
        
        # Check if this matches any database episode
        matches = []
        for db_guid, db_url, db_title in db_episodes:
            if episode_guid == db_guid:
                matches.append("GUID")
            if audio_url == db_url:
                matches.append("URL")
            if episode_title == db_title:
                matches.append("TITLE")
        
        if matches:
            print(f"  ✅ MATCHES: {', '.join(matches)}")
        else:
            print(f"  ❌ NO MATCH FOUND!")
            
        print(f"  ---")
    
    conn.close()

if __name__ == "__main__":
    debug_episode_matching()