#!/usr/bin/env python3
"""
Process remaining three podcasts: Optimistic Outlook, The Engineers Collective, Talking Infrastructure
Only process episodes from December 2024 onwards for these new podcasts
"""
import os
import sqlite3
import feedparser
import requests
from datetime import datetime, timedelta
from enhanced_automation import EnhancedPodcastSystem

class RemainingPodcastProcessor:
    def __init__(self):
        self.db_path = 'podcast_app_v2.db'
        self.automation_system = EnhancedPodcastSystem()
        
        # Remaining podcasts to process
        self.remaining_podcasts = [
            'Optimistic Outlook',
            'The Engineers Collective', 
            'Talking Infrastructure'
        ]
        
        # Date cutoff for processing episodes
        self.cutoff_date = datetime(2024, 12, 1)
    
    def process_remaining_podcasts(self):
        """Process the three remaining podcasts"""
        print(f"🔧 Processing remaining podcasts since {self.cutoff_date.strftime('%Y-%m-%d')}...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for podcast_name in self.remaining_podcasts:
            print(f"\n🎧 Processing {podcast_name}...")
            
            # Get podcast info
            cursor.execute("SELECT id, rss_url FROM podcasts WHERE name = ?", (podcast_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"  ❌ Podcast not found: {podcast_name}")
                continue
            
            podcast_id, rss_url = result
            
            # Parse RSS feed and find recent episodes
            episodes_to_process = self.find_recent_episodes(rss_url, podcast_id, podcast_name)
            
            if episodes_to_process:
                print(f"  📊 Found {len(episodes_to_process)} episodes since Dec 2024")
                
                # Process episodes in smaller batches of 3 to avoid timeout
                for i in range(0, len(episodes_to_process), 3):
                    batch = episodes_to_process[i:i+3]
                    print(f"  🔧 Processing batch {i//3 + 1}: {len(batch)} episodes")
                    
                    processed = self.automation_system.process_new_episodes(batch)
                    
                    if processed:
                        # Add to master files
                        self.automation_system.append_to_master_files(processed)
                        print(f"    ✅ Processed {len(processed)} episodes")
                    else:
                        print(f"    ❌ No episodes successfully processed in this batch")
            else:
                print(f"  📭 No episodes found since Dec 2024")
        
        conn.close()
    
    def find_recent_episodes(self, rss_url, podcast_id, podcast_name):
        """Find episodes since December 2024"""
        try:
            # Parse RSS feed
            rss_data = self.automation_system.parse_rss_feed(rss_url)
            if not rss_data["success"]:
                print(f"    ❌ RSS parsing failed: {rss_data['error']}")
                return []
            
            recent_episodes = []
            
            for episode_data in rss_data["episodes"]:
                if not episode_data.get('publish_date'):
                    continue
                
                # Parse episode date
                try:
                    episode_dt = datetime.fromisoformat(episode_data['publish_date'].replace('Z', '+00:00'))
                    episode_dt = episode_dt.replace(tzinfo=None)  # Remove timezone
                except:
                    continue
                
                # Check if episode is recent enough
                if episode_dt >= self.cutoff_date:
                    # Check if already exists in database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT id FROM episodes 
                        WHERE podcast_id = ? AND (title = ? OR guid = ? OR audio_url = ?)
                    ''', (podcast_id, episode_data['title'], episode_data.get('guid'), episode_data.get('audio_url')))
                    
                    if not cursor.fetchone():
                        # New episode
                        episode_data['podcast_id'] = podcast_id
                        episode_data['podcast_name'] = podcast_name
                        recent_episodes.append(episode_data)
                        print(f"    📝 Found: {episode_data['title'][:50]}... ({episode_dt.strftime('%Y-%m-%d')})")
                    
                    conn.close()
            
            return recent_episodes
            
        except Exception as e:
            print(f"    ❌ Error finding recent episodes: {e}")
            return []
    
    def show_final_status(self):
        """Show final status for all podcasts"""
        print("\n📊 Final Status Summary:")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        all_podcasts = self.remaining_podcasts + ['Crossroads: The Infrastructure Podcast']
        
        for podcast_name in all_podcasts:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN transcript IS NOT NULL AND LENGTH(transcript) > 100 THEN 1 END) as with_transcripts,
                       COUNT(CASE WHEN created_at >= ? THEN 1 END) as recent
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.id
                WHERE p.name = ?
            ''', (self.cutoff_date.isoformat(), podcast_name))
            
            result = cursor.fetchone()
            if result:
                total, with_transcripts, recent = result
                print(f"  📁 {podcast_name}:")
                print(f"     📊 Total episodes: {total}")
                print(f"     ✅ With transcripts: {with_transcripts}")
                print(f"     🆕 Added since Dec 2024: {recent}")
        
        conn.close()

if __name__ == "__main__":
    processor = RemainingPodcastProcessor()
    processor.process_remaining_podcasts()
    processor.show_final_status()