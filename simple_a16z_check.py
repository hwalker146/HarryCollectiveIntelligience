#!/usr/bin/env python3
"""
Simple script to check a16z RSS feed for recent episodes
"""
import feedparser
import sqlite3
from datetime import datetime, timedelta

def check_a16z_episodes():
    print("🔍 Checking a16z RSS feed for recent episodes...")
    
    # Get RSS URL from database
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT rss_url FROM podcasts WHERE name = 'a16z Podcast'")
    result = cursor.fetchone()
    
    if not result:
        print("❌ a16z Podcast not found in database")
        return
    
    rss_url = result[0]
    print(f"📡 RSS URL: {rss_url}")
    
    # Parse RSS feed
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ No episodes found in RSS feed")
        return
    
    print(f"📝 Found {len(feed.entries)} total episodes in RSS feed")
    print("\n🎙️ Recent episodes:")
    
    cutoff_date = datetime.now() - timedelta(days=3)  # Check last 3 days
    
    for i, entry in enumerate(feed.entries[:10]):  # Check first 10 episodes
        title = entry.title if hasattr(entry, 'title') else 'No title'
        
        # Get publish date
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
            date_str = pub_date.strftime('%Y-%m-%d %H:%M')
            is_recent = pub_date >= cutoff_date
        else:
            date_str = "Unknown date"
            is_recent = False
        
        # Get audio URL
        audio_url = None
        if hasattr(entry, 'enclosures') and entry.enclosures:
            audio_url = entry.enclosures[0].href
        elif hasattr(entry, 'links'):
            for link in entry.links:
                if 'audio' in link.get('type', ''):
                    audio_url = link.href
                    break
        
        # Check if exists in database
        if audio_url:
            cursor.execute('SELECT id, transcribed, processed FROM episodes WHERE audio_url = ?', (audio_url,))
            existing = cursor.fetchone()
            
            if existing:
                status = f"In DB (transcribed={existing[1]}, processed={existing[2]})"
            else:
                status = "NEW - not in database"
        else:
            status = "No audio URL found"
        
        recent_marker = "🆕 " if is_recent else "   "
        print(f"{recent_marker}{i+1:2d}. {title}")
        print(f"     📅 {date_str}")
        print(f"     📊 {status}")
        
        if audio_url and len(audio_url) > 60:
            print(f"     🔗 {audio_url[:60]}...")
        elif audio_url:
            print(f"     🔗 {audio_url}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_a16z_episodes()