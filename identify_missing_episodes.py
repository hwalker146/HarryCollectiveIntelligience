#!/usr/bin/env python3
"""
Identify missing episodes by comparing RSS feeds against database
Show most recent transcribed episode and list all missing episodes for approval
"""
import sys
import sqlite3
import requests
import feedparser
from datetime import datetime
import re

class MissingEpisodeIdentifier:
    def __init__(self):
        self.db_path = 'podcast_app_v2.db'
        
        # Active podcasts with working RSS feeds
        self.active_podcasts = {
            'Crossroads: The Infrastructure Podcast': 'https://fast.wistia.com/channels/z8h3prypqf/rss',
            'Deal Talks': 'https://feeds.buzzsprout.com/2303626.rss', 
            'Exchanges at Goldman Sachs': 'https://feeds.megaphone.fm/GLD9218176758',
            'Global Evolution': 'https://global-energy-transition.podigee.io/feed/mp3',
            'The Data Center Frontier Show': 'https://feed.podbean.com/thedatacenterfrontiershow/feed.xml',
            'The Infrastructure Investor': 'https://feed.podbean.com/infrastructureinvestorpodcast/feed.xml'
        }
        
    def get_podcast_id(self, podcast_name):
        """Get podcast ID from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM podcasts WHERE name = ? AND is_active = 1", (podcast_name,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_latest_transcribed_episode(self, podcast_id):
        """Get the most recent episode with a real transcript"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, publish_date, LENGTH(transcript) as transcript_length
            FROM episodes 
            WHERE podcast_id = ? 
            AND transcript IS NOT NULL 
            AND LENGTH(transcript) > 1000
            ORDER BY publish_date DESC 
            LIMIT 1
        """, (podcast_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result if result else None
    
    def fetch_rss_episodes(self, rss_url, limit=50):
        """Fetch episodes from RSS feed"""
        try:
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                return {"success": False, "error": "Invalid RSS feed format"}
            
            episodes = []
            for entry in feed.entries[:limit]:
                # Extract audio URL
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if not audio_url:
                    continue
                
                # Parse publication date
                publish_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    publish_date = datetime(*entry.published_parsed[:6]).isoformat()
                
                # Get GUID safely
                guid = getattr(entry, 'id', None) or getattr(entry, 'link', None) or audio_url
                
                episode_data = {
                    "title": getattr(entry, 'title', 'Unknown Title'),
                    "description": getattr(entry, 'summary', ''),
                    "audio_url": audio_url,
                    "episode_url": getattr(entry, 'link', ''),
                    "guid": guid,
                    "publish_date": publish_date
                }
                
                episodes.append(episode_data)
            
            return {
                "success": True,
                "episodes": episodes
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch RSS feed: {str(e)}"}
    
    def episode_exists_in_db(self, podcast_id, episode):
        """Check if episode exists in database (using AND logic)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check by title and publish_date (main matching criteria)
        cursor.execute("""
            SELECT id, transcript FROM episodes 
            WHERE podcast_id = ? AND title = ? AND publish_date = ?
        """, (podcast_id, episode['title'], episode['publish_date']))
        
        result = cursor.fetchone()
        conn.close()
        
        return result if result else None
    
    def identify_missing_for_podcast(self, podcast_name, rss_url):
        """Identify missing episodes for a specific podcast"""
        print(f"\\n📁 Analyzing {podcast_name}...")
        
        podcast_id = self.get_podcast_id(podcast_name)
        if not podcast_id:
            print(f"   ❌ Podcast not found in database")
            return []
        
        # Get latest transcribed episode
        latest = self.get_latest_transcribed_episode(podcast_id)
        if latest:
            title, date, transcript_len = latest
            print(f"   📄 Latest transcribed: '{title[:50]}...' ({date})")
            print(f"   📊 Transcript length: {transcript_len:,} characters")
        else:
            print(f"   📄 Latest transcribed: No episodes with transcripts found")
            date = "1900-01-01"  # Very old date to catch everything
        
        # Fetch RSS episodes
        print(f"   🌐 Fetching RSS episodes...")
        rss_data = self.fetch_rss_episodes(rss_url)
        
        if not rss_data["success"]:
            print(f"   ❌ Failed to fetch RSS: {rss_data['error']}")
            return []
        
        print(f"   📡 Found {len(rss_data['episodes'])} episodes in RSS feed")
        
        # Find missing episodes
        missing_episodes = []
        
        for episode in rss_data["episodes"]:
            # Skip if older than our latest transcript (if we have one)
            if latest and episode.get('publish_date') and episode['publish_date'] <= latest[1]:
                continue
            
            # Check if exists in database
            existing = self.episode_exists_in_db(podcast_id, episode)
            
            if not existing:
                missing_episodes.append(episode)
                print(f"   ➕ Missing: '{episode['title'][:50]}...' ({episode.get('publish_date', 'No date')})")
            else:
                episode_id, transcript = existing
                if not transcript or len(transcript) < 1000:
                    missing_episodes.append(episode)
                    print(f"   📝 Needs transcript: '{episode['title'][:50]}...' ({episode.get('publish_date', 'No date')})")
        
        print(f"   📊 Total missing/needing transcription: {len(missing_episodes)}")
        
        return missing_episodes
    
    def run_analysis(self):
        """Run complete missing episode analysis"""
        print("🔍 IDENTIFYING MISSING EPISODES...")
        print("=" * 60)
        
        all_missing = {}
        total_missing = 0
        
        for podcast_name, rss_url in self.active_podcasts.items():
            missing = self.identify_missing_for_podcast(podcast_name, rss_url)
            if missing:
                all_missing[podcast_name] = missing
                total_missing += len(missing)
        
        print(f"\\n🎉 ANALYSIS COMPLETE!")
        print(f"📊 Total episodes needing transcription: {total_missing}")
        
        if total_missing > 0:
            print(f"\\n📋 EPISODES PLANNED FOR TRANSCRIPTION:")
            print("=" * 60)
            
            for podcast_name, episodes in all_missing.items():
                print(f"\\n📁 {podcast_name} ({len(episodes)} episodes):")
                for i, episode in enumerate(episodes[:10], 1):  # Show first 10
                    print(f"   {i:2d}. {episode['title']}")
                    print(f"       📅 {episode.get('publish_date', 'No date')}")
                    print(f"       🎧 {episode['audio_url'][:60]}...")
                
                if len(episodes) > 10:
                    print(f"       ... and {len(episodes) - 10} more episodes")
        
        return all_missing

if __name__ == "__main__":
    identifier = MissingEpisodeIdentifier()
    identifier.run_analysis()