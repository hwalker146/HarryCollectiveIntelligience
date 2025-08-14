#!/usr/bin/env python3
"""
Add new podcasts and process episodes from December 2024 onwards
- Optimistic Outlook
- The Engineers Collective  
- Talking Infrastructure
- Re-enable Crossroads with proper RSS parsing
"""
import os
import sqlite3
import feedparser
import requests
from datetime import datetime, timedelta
from enhanced_automation import EnhancedPodcastSystem

class NewPodcastAdder:
    def __init__(self):
        self.db_path = 'podcast_app_v2.db'
        self.automation_system = EnhancedPodcastSystem()
        
        # New podcasts to add
        self.new_podcasts = [
            {
                'name': 'Optimistic Outlook',
                'rss_url': 'https://feed.podbean.com/theoptimisticoutlook/feed.xml',
                'description': 'Hosted by Barbara Humpton, CEO of Siemens USA, focusing on technological transformation across American industry and infrastructure.'
            },
            {
                'name': 'The Engineers Collective',
                'rss_url': 'https://feed.podbean.com/theengineerscollective/feed.xml',
                'description': 'News and interviews covering all corners of infrastructure, from rail to roads to energy to tunnels, by New Civil Engineer.'
            },
            {
                'name': 'Talking Infrastructure',
                'rss_url': 'https://feeds.megaphone.fm/OMAEO4014431879',
                'description': 'Global infrastructure consultancy AECOM discusses industry hot topics, key projects and innovations.'
            }
        ]
        
        # Date cutoff for processing episodes
        self.cutoff_date = datetime(2024, 12, 1)
    
    def add_new_podcasts(self):
        """Add new podcasts to database"""
        print("📝 Adding new podcasts to database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for podcast in self.new_podcasts:
            # Check if podcast already exists
            cursor.execute("SELECT id FROM podcasts WHERE name = ?", (podcast['name'],))
            if cursor.fetchone():
                print(f"  ⚠️  {podcast['name']} already exists in database")
                continue
            
            # Add new podcast
            cursor.execute('''
                INSERT INTO podcasts (name, rss_url, description, is_active, created_at)
                VALUES (?, ?, ?, 1, ?)
            ''', (
                podcast['name'],
                podcast['rss_url'], 
                podcast['description'],
                datetime.now().isoformat()
            ))
            
            podcast_id = cursor.lastrowid
            print(f"  ✅ Added {podcast['name']} (ID: {podcast_id})")
        
        conn.commit()
        conn.close()
        
        print("✅ New podcasts added to database")
    
    def re_enable_crossroads(self):
        """Re-enable Crossroads in daily automation"""
        print("🔧 Re-enabling Crossroads for daily automation...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update Crossroads to use proper RSS URL
        cursor.execute('''
            UPDATE podcasts 
            SET rss_url = 'https://fast.wistia.com/channels/z8h3prypqf/rss'
            WHERE name LIKE '%Crossroads%'
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Crossroads re-enabled with proper RSS URL")
    
    def process_recent_episodes(self):
        """Process episodes from December 2024 onwards for all new podcasts + Crossroads"""
        print(f"🔧 Processing episodes since {self.cutoff_date.strftime('%Y-%m-%d')}...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all podcasts to process (new ones + Crossroads)
        podcast_names = [p['name'] for p in self.new_podcasts] + ['Crossroads: The Infrastructure Podcast']
        
        for podcast_name in podcast_names:
            print(f"\n🎧 Processing {podcast_name}...")
            
            # Get podcast info
            cursor.execute("SELECT id, rss_url FROM podcasts WHERE name = ?", (podcast_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"  ❌ Podcast not found: {podcast_name}")
                continue
            
            podcast_id, rss_url = result
            
            # Parse RSS feed
            episodes_to_process = self.find_recent_episodes(rss_url, podcast_id, podcast_name)
            
            if episodes_to_process:
                print(f"  📊 Found {len(episodes_to_process)} episodes since Dec 2024")
                
                # Process episodes in batches of 5
                for i in range(0, len(episodes_to_process), 5):
                    batch = episodes_to_process[i:i+5]
                    print(f"  🔧 Processing batch {i//5 + 1}: {len(batch)} episodes")
                    
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
    
    def create_master_files(self):
        """Create master files for new podcasts"""
        print("\n📝 Creating master files for new podcasts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for podcast in self.new_podcasts:
            # Get podcast info
            cursor.execute("SELECT id FROM podcasts WHERE name = ?", (podcast['name'],))
            result = cursor.fetchone()
            
            if result:
                podcast_id = result[0]
                
                # Check if we have any episodes with transcripts
                cursor.execute('''
                    SELECT COUNT(*) FROM episodes 
                    WHERE podcast_id = ? AND transcript IS NOT NULL AND LENGTH(transcript) > 100
                ''', (podcast_id,))
                
                episode_count = cursor.fetchone()[0]
                
                if episode_count > 0:
                    # Create master file
                    safe_name = podcast['name'].replace(':', '').replace(' ', '_').replace("'", "")
                    filename = f"{safe_name}_Master_Transcripts.md"
                    
                    from pathlib import Path
                    filepath = Path('content/master_transcripts') / filename
                    
                    # Get episodes for master file
                    cursor.execute('''
                        SELECT title, publish_date, transcript, id
                        FROM episodes 
                        WHERE podcast_id = ? 
                        AND transcript IS NOT NULL 
                        AND LENGTH(transcript) > 100
                        ORDER BY publish_date DESC
                    ''', (podcast_id,))
                    
                    episodes = cursor.fetchall()
                    
                    # Create content
                    content = f"# {podcast['name']} - Master Transcripts\n\n"
                    content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    content += f"**Total Episodes:** {len(episodes)}\n"
                    if episodes:
                        content += f"**Date Range:** {episodes[-1][1][:10]} to {episodes[0][1][:10]}\n\n"
                    else:
                        content += f"**Date Range:** N/A\n\n"
                    content += "Episodes organized by publication date (newest first).\n\n"
                    content += "---\n\n"
                    
                    for title, publish_date, transcript, episode_id in episodes:
                        date_str = publish_date[:10] if publish_date else "Unknown Date"
                        
                        content += f"## {date_str}\n\n"
                        content += f"### {title}\n"
                        content += f"**Publication Date:** {publish_date}\n"
                        content += f"**Episode ID:** {episode_id}\n\n"
                        content += f"**Full Transcript:**\n"
                        content += f"{transcript}\n\n"
                        content += "---\n\n"
                    
                    # Save file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"  ✅ Created: {filename} ({len(episodes)} episodes)")
                else:
                    print(f"  📭 No episodes with transcripts for {podcast['name']}")
        
        conn.close()
    
    def show_summary(self):
        """Show final summary of what was added"""
        print("\n📊 Final Summary:")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        all_podcasts = [p['name'] for p in self.new_podcasts] + ['Crossroads: The Infrastructure Podcast']
        
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
    
    def run_full_setup(self):
        """Run complete setup process"""
        print("🚀 Starting new podcast setup process...\n")
        
        # Step 1: Add new podcasts
        self.add_new_podcasts()
        
        # Step 2: Re-enable Crossroads
        self.re_enable_crossroads()
        
        # Step 3: Process recent episodes
        self.process_recent_episodes()
        
        # Step 4: Create master files
        self.create_master_files()
        
        # Step 5: Show summary
        self.show_summary()
        
        print("\n🎉 New podcast setup complete!")

if __name__ == "__main__":
    adder = NewPodcastAdder()
    adder.run_full_setup()