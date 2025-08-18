#!/usr/bin/env python3
"""
Create the missing Ezra Klein "Trump vs. the U.S. Economy" episode in database
This episode was analyzed and emailed but not saved due to missing Ezra Klein episodes in DB
"""
import sqlite3
import requests
import feedparser
from datetime import datetime

def create_missing_ezra_episode():
    """Create the missing Ezra Klein episode"""
    print("🔍 Creating missing Ezra Klein episode...")
    
    # Get the RSS feed
    rss_url = "https://feeds.simplecast.com/kEKXbjuJ"
    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
    
    try:
        response = requests.get(rss_url, headers=headers, timeout=30)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        # Find the Trump vs. the U.S. Economy episode
        target_episode = None
        for entry in feed.entries:
            if "Trump vs. the U.S. Economy" in entry.title:
                target_episode = entry
                break
        
        if not target_episode:
            print("❌ Could not find 'Trump vs. the U.S. Economy' episode")
            return
            
        print(f"✅ Found episode: {target_episode.title}")
        
        # Extract episode data
        audio_url = None
        for enclosure in getattr(target_episode, 'enclosures', []):
            if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                audio_url = enclosure.href
                break
        
        if not audio_url:
            print("❌ No audio URL found for episode")
            return
            
        # Parse publication date
        publish_date = None
        if hasattr(target_episode, 'published_parsed') and target_episode.published_parsed:
            publish_date = datetime(*target_episode.published_parsed[:6]).isoformat()
        
        episode_data = {
            'title': target_episode.title,
            'description': getattr(target_episode, 'summary', ''),
            'audio_url': audio_url,
            'episode_url': getattr(target_episode, 'link', ''),
            'guid': getattr(target_episode, 'id', None) or audio_url,
            'publish_date': publish_date
        }
        
        print(f"📅 Publish date: {publish_date}")
        print(f"🎵 Audio URL: {audio_url[:50]}...")
        
        # Save to database
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        # Insert the episode
        cursor.execute('''
            INSERT INTO episodes (
                podcast_id, title, description, audio_url, episode_url,
                guid, publish_date, transcript, transcribed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            5,  # Ezra Klein Show podcast_id
            episode_data['title'],
            episode_data['description'],
            episode_data['audio_url'],
            episode_data['episode_url'],
            episode_data['guid'],
            episode_data['publish_date'],
            "",  # Empty transcript initially
            0,   # Not transcribed yet
            datetime.now().isoformat()
        ))
        
        episode_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Created episode {episode_id}: {episode_data['title']}")
        print("\n📧 The automation system should now be able to:")
        print("   1. Detect this episode exists in the database")
        print("   2. Transcribe it if needed")
        print("   3. Save the transcript and analysis properly")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_missing_ezra_episode()