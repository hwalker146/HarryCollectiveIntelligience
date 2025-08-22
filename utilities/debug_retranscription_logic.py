#!/usr/bin/env python3
"""
Debug Retranscription Logic
Check why existing episodes are being flagged for retranscription
"""
import sqlite3
import feedparser
import requests

def debug_retranscription():
    print("🔍 DEBUGGING RETRANSCRIPTION LOGIC")
    print("=" * 50)
    
    # Check Crossroads (126 episodes - most likely to have issues)
    podcast_name = "Crossroads: The Infrastructure Podcast"
    rss_url = "https://feeds.acast.com/public/shows/crossroads-the-infrastructure-podcast"
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get podcast ID
    cursor.execute("SELECT id FROM podcasts WHERE name = ?", (podcast_name,))
    podcast_id = cursor.fetchone()[0]
    
    print(f"📊 Checking {podcast_name} (ID: {podcast_id})")
    
    # FIRST QUERY: Get existing episodes for matching (same as automation)
    cursor.execute('''
        SELECT guid, audio_url, title FROM episodes 
        WHERE podcast_id = ?
    ''', (podcast_id,))
    
    existing_episodes = set()
    db_episodes = []
    for guid, audio_url, title in cursor.fetchall():
        db_episodes.append((guid, audio_url, title))
        if guid:
            existing_episodes.add(guid)
        if audio_url:
            existing_episodes.add(audio_url)
        if title:
            existing_episodes.add(title)
    
    print(f"📚 Database has {len(db_episodes)} episodes")
    
    # Get RSS feed
    print(f"📡 Fetching RSS feed...")
    headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
    response = requests.get(rss_url, headers=headers, timeout=30)
    feed = feedparser.parse(response.content)
    
    print(f"📻 RSS has {len(feed.entries)} episodes")
    
    # Check first few RSS episodes
    for i, entry in enumerate(feed.entries[:5]):
        print(f"\n--- RSS Episode {i+1} ---")
        
        # Extract data same as automation
        audio_url = None
        for enclosure in getattr(entry, 'enclosures', []):
            if hasattr(enclosure, 'type') and enclosure.type and 'audio' in enclosure.type:
                audio_url = enclosure.href
                break
        
        episode_title = getattr(entry, 'title', 'Unknown Title')
        episode_guid = getattr(entry, 'id', None) or audio_url
        
        print(f"GUID:  {episode_guid}")
        print(f"URL:   {audio_url}")
        print(f"TITLE: {episode_title}")
        
        # STEP 1: Check if episode exists (same logic as automation)
        episode_exists = (
            (episode_guid and episode_guid in existing_episodes) or
            (audio_url and audio_url in existing_episodes) or  
            (episode_title and episode_title in existing_episodes)
        )
        
        print(f"EXISTS: {episode_exists}")
        
        if episode_exists:
            # STEP 2: Run the retranscription query (same as automation)
            cursor.execute('''
                SELECT id, transcribed, transcript FROM episodes 
                WHERE podcast_id = ? AND (guid = ? OR audio_url = ? OR title = ?)
            ''', (podcast_id, episode_guid, audio_url, episode_title))
            
            existing_episode = cursor.fetchone()
            
            if existing_episode:
                episode_id, transcribed, transcript = existing_episode
                transcript_length = len(transcript.strip()) if transcript else 0
                
                print(f"FOUND IN DB:")
                print(f"  ID: {episode_id}")
                print(f"  Transcribed: {transcribed}")
                print(f"  Transcript length: {transcript_length}")
                
                # Check retranscription conditions
                needs_retranscription = (
                    transcribed == 0 or 
                    not transcript or 
                    len(transcript.strip()) < 100
                )
                
                print(f"  NEEDS RETRANSCRIPTION: {needs_retranscription}")
                
                if needs_retranscription:
                    print("  ⚠️  THIS WOULD BE FLAGGED FOR RETRANSCRIPTION!")
                    if transcribed == 0:
                        print("      Reason: transcribed = 0")
                    if not transcript:
                        print("      Reason: transcript is NULL")
                    if transcript and len(transcript.strip()) < 100:
                        print("      Reason: transcript too short")
            else:
                print("❌ WEIRD: Episode exists in first query but not found in retranscription query!")
        else:
            print("NEW: Would be processed as new episode")
    
    conn.close()

if __name__ == "__main__":
    debug_retranscription()