#!/usr/bin/env python3
"""
Fix transcript data using files from Data_From_Google_Drive folder
This script will:
1. Parse transcript files already in the Data_From_Google_Drive folder
2. Match transcripts to existing database episodes
3. Update episodes with proper transcripts
4. Remove duplicate episodes
5. Flag episodes without transcripts for removal
"""
import os
import sqlite3
import re
from datetime import datetime
from pathlib import Path

class TranscriptDataFixer:
    def __init__(self, db_path='podcast_app_v2.db'):
        self.db_path = db_path
        self.gdrive_folder = Path('content/Data_From_Google_Drive')
        self.transcript_files = {
            'The Infrastructure Investor TRANSCRIPTS.markdown': 'The Infrastructure Investor',
            'Crossroads The Infrastructure Podcast TRANSCRIPTS.markdown': 'Crossroads: The Infrastructure Podcast',
            'Exchanges at Goldman Sachs TRANSCRIPTS.markdown': 'Exchanges at Goldman Sachs',
            'Global Evolution TRANSCRIPTS.markdown': 'Global Evolution',
            'The Data Center Frontier Show TRANSCRIPTS.markdown': 'The Data Center Frontier Show'
        }
        self.parsed_episodes = []
        
    def parse_transcript_file(self, file_path, podcast_name):
        """Parse a transcript file and extract episode data"""
        print(f"📄 Parsing {file_path.name} for {podcast_name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Failed to read {file_path}: {e}")
            return []
        
        # Handle escaped newlines in the content
        content = content.replace('\\n', '\n')
        
        episodes = []
        
        # Split by episode sections - look for date headers with equals line
        # Pattern: ## date followed by ======
        sections = re.split(r'\n## ([^\n]+)\n=+\n', content)
        
        for i in range(1, len(sections), 2):  # Take pairs: date, content
            if i+1 >= len(sections):
                break
                
            date_line = sections[i].strip()
            section_content = sections[i+1]
            
            # Look for episode title (starts with ###)
            title_match = re.search(r'\n### (.+?)\n', section_content)
            episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', section_content)
            transcript_match = re.search(r'\*\*TRANSCRIPT:\*\*\n(.+?)(?=\n---|\n## |$)', section_content, re.DOTALL)
            
            if title_match and transcript_match:
                title = title_match.group(1).strip()
                episode_id = episode_id_match.group(1) if episode_id_match else None
                transcript = transcript_match.group(1).strip()
                
                if len(transcript) > 100:  # Only include substantial transcripts
                    episode = {
                        'podcast_name': podcast_name,
                        'title': title,
                        'publish_date': self.parse_date(date_line),
                        'episode_id': episode_id,
                        'transcript': transcript
                    }
                    episodes.append(episode)
                    print(f"      ✓ Found: {title[:50]}...")
        
        print(f"   ✅ Extracted {len(episodes)} episodes from {file_path.name}")
        return episodes
    
    def parse_date(self, date_str):
        """Parse date from various formats"""
        # Clean up the date string
        date_str = date_str.split(' ')[0]  # Take only the date part
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            print(f"⚠️ Could not parse date: {date_str}")
            return None
    
    def parse_all_files(self):
        """Parse all transcript files in Data_From_Google_Drive"""
        print("🔍 Parsing transcript files from Data_From_Google_Drive...")
        
        for filename, podcast_name in self.transcript_files.items():
            file_path = self.gdrive_folder / filename
            
            if file_path.exists():
                episodes = self.parse_transcript_file(file_path, podcast_name)
                self.parsed_episodes.extend(episodes)
            else:
                print(f"⚠️ File not found: {file_path}")
        
        print(f"\n📊 Total episodes parsed: {len(self.parsed_episodes)}")
        
        # Show breakdown by podcast
        by_podcast = {}
        for episode in self.parsed_episodes:
            podcast = episode['podcast_name']
            by_podcast[podcast] = by_podcast.get(podcast, 0) + 1
        
        for podcast, count in by_podcast.items():
            print(f"   📄 {podcast}: {count} episodes")
    
    def match_and_update_episodes(self):
        """Match parsed episodes to database and update transcripts"""
        print("\n🔄 Matching episodes to database and updating transcripts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get podcast mappings
        cursor.execute("SELECT id, name FROM podcasts")
        podcasts = {name: id for id, name in cursor.fetchall()}
        
        matched = 0
        updated = 0
        
        for episode_data in self.parsed_episodes:
            podcast_name = episode_data['podcast_name']
            title = episode_data['title']
            transcript = episode_data['transcript']
            
            if podcast_name not in podcasts:
                print(f"⚠️ Podcast not found: {podcast_name}")
                continue
            
            podcast_id = podcasts[podcast_name]
            
            # Find matching episode by exact title match
            cursor.execute("""
                SELECT id, transcript
                FROM episodes 
                WHERE podcast_id = ? AND title = ?
            """, (podcast_id, title))
            
            matches = cursor.fetchall()
            
            if matches:
                matched += 1
                
                # Update all matching episodes
                for episode_id, existing_transcript in matches:
                    if not existing_transcript or len(existing_transcript) < 1000:
                        cursor.execute("""
                            UPDATE episodes 
                            SET transcript = ?, transcribed = 1
                            WHERE id = ?
                        """, (transcript, episode_id))
                        updated += 1
                        print(f"   ✅ Updated episode {episode_id}: {title[:50]}...")
            else:
                print(f"   ❌ No match found for: {title[:50]}...")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Matching complete: {matched} episodes matched, {updated} transcripts updated")
    
    def remove_duplicate_episodes(self):
        """Remove duplicate episodes from database"""
        print("\n🧹 Removing duplicate episodes...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find and remove duplicates
        cursor.execute("""
            SELECT podcast_id, title, MIN(id) as keep_id, COUNT(*) as count
            FROM episodes
            GROUP BY podcast_id, title
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        total_removed = 0
        
        for podcast_id, title, keep_id, count in duplicates:
            # Delete all but the first episode
            cursor.execute("""
                DELETE FROM episodes 
                WHERE podcast_id = ? AND title = ? AND id != ?
            """, (podcast_id, title, keep_id))
            
            removed = cursor.rowcount
            total_removed += removed
            print(f"   🗑️ Removed {removed} duplicates of: {title[:50]}...")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Removed {total_removed} duplicate episodes")
    
    def flag_episodes_without_transcripts(self):
        """Flag episodes that don't have transcripts"""
        print("\n🚩 Checking for episodes without transcripts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find episodes without substantial transcripts
        cursor.execute("""
            SELECT e.id, e.title, p.name
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE e.transcript IS NULL 
            OR LENGTH(e.transcript) < 100
            ORDER BY p.name, e.title
        """)
        
        empty_episodes = cursor.fetchall()
        
        if empty_episodes:
            print(f"\n⚠️ Found {len(empty_episodes)} episodes without transcripts:")
            
            # Group by podcast
            by_podcast = {}
            for episode_id, title, podcast_name in empty_episodes:
                if podcast_name not in by_podcast:
                    by_podcast[podcast_name] = []
                by_podcast[podcast_name].append((episode_id, title))
            
            for podcast_name, episodes in by_podcast.items():
                print(f"   📄 {podcast_name}: {len(episodes)} episodes")
                for episode_id, title in episodes[:3]:  # Show first 3
                    print(f"      - Episode {episode_id}: {title[:50]}...")
                if len(episodes) > 3:
                    print(f"      ... and {len(episodes) - 3} more")
            
            print(f"\n❗ FLAGGED {len(empty_episodes)} episodes without transcripts for review")
            print("   These episodes should be removed from the database.")
            print("   Run the script with --remove-empty flag to delete them automatically.")
        else:
            print("✅ All episodes have transcripts!")
        
        conn.close()
    
    def run_fix(self):
        """Run the complete fix process"""
        print("🚀 Starting transcript data fix...")
        print("=" * 60)
        
        # Step 1: Parse transcript files
        self.parse_all_files()
        
        # Step 2: Remove duplicates first
        self.remove_duplicate_episodes()
        
        # Step 3: Match and update episodes
        self.match_and_update_episodes()
        
        # Step 4: Handle episodes without transcripts
        self.flag_episodes_without_transcripts()
        
        print("\n" + "=" * 60)
        print("🎉 Transcript data fix complete!")

if __name__ == "__main__":
    fixer = TranscriptDataFixer()
    fixer.run_fix()