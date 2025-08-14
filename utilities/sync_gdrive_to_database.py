#!/usr/bin/env python3
"""
Sync Google Drive transcript content to database
Matches episodes using AND logic: title, date, and audio_url must all match
"""
import sys
import sqlite3
import re
from datetime import datetime
from google_drive_sync import GoogleDriveSync

class GoogleDriveToDatabase:
    def __init__(self):
        self.sync = GoogleDriveSync()
        self.db_path = 'podcast_app_v2.db'
        
        # Active podcasts to sync
        self.active_podcasts = [
            'Crossroads: The Infrastructure Podcast',
            'Deal Talks', 
            'Exchanges at Goldman Sachs',
            'Global Evolution',
            'The Data Center Frontier Show',
            'The Infrastructure Investor'
        ]
        
    def extract_episodes_from_transcript(self, content, podcast_name):
        """Extract individual episodes from a transcript file"""
        episodes = []
        
        # Split by date headers (## YYYY-MM-DD)
        date_sections = re.split(r'\n## (\d{4}-\d{2}-\d{2})\n', content)
        
        for i in range(1, len(date_sections), 2):
            if i + 1 < len(date_sections):
                date = date_sections[i]
                section_content = date_sections[i + 1]
                
                # Extract episode title (### Title)
                title_match = re.search(r'^### (.+)$', section_content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                    
                    # Extract episode ID if present
                    episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', section_content)
                    episode_id = int(episode_id_match.group(1)) if episode_id_match else None
                    
                    # Extract date from section
                    date_match = re.search(r'\*\*Date:\*\* (.+)', section_content)
                    publish_date = date_match.group(1).strip() if date_match else f"{date}T00:00:00"
                    
                    # Extract transcript content (everything after metadata)
                    transcript_start = section_content.find('\n\n')
                    if transcript_start != -1:
                        transcript = section_content[transcript_start:].strip()
                        # Remove the trailing --- separator
                        transcript = re.sub(r'\n---\n*$', '', transcript)
                        
                        # Only include if there's actual transcript content (not just metadata)
                        if len(transcript) > 100 and transcript not in ['', '---']:
                            episodes.append({
                                'title': title,
                                'publish_date': publish_date,
                                'transcript': transcript,
                                'episode_id': episode_id,
                                'podcast_name': podcast_name
                            })
        
        return episodes
    
    def get_podcast_id_from_name(self, podcast_name):
        """Get podcast ID from database by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM podcasts WHERE name = ? AND is_active = 1", (podcast_name,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def find_matching_episode_in_db(self, episode, podcast_id):
        """Find matching episode in database using AND logic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try exact match first (title, date, audio_url all match)
        cursor.execute("""
            SELECT id, transcript FROM episodes 
            WHERE podcast_id = ? AND title = ? AND publish_date = ?
        """, (podcast_id, episode['title'], episode['publish_date']))
        
        result = cursor.fetchone()
        conn.close()
        
        return result if result else None
    
    def sync_podcast_transcripts(self, podcast_name):
        """Sync transcripts for a specific podcast"""
        print(f"\n📁 Syncing {podcast_name}...")
        
        # Get podcast ID
        podcast_id = self.get_podcast_id_from_name(podcast_name)
        if not podcast_id:
            print(f"   ❌ Podcast not found in database: {podcast_name}")
            return
        
        # Find transcript file in Google Drive (in Master Transcripts folder)
        service = self.sync.service
        main_folder_id = '1Zo8p26SksJCUTviH95w0JOoKdR1fHGzJ'
        
        # First find the Master Transcripts folder
        master_transcripts_results = service.files().list(
            q=f"parents in '{main_folder_id}' and name = 'Master Transcripts' and mimeType='application/vnd.google-apps.folder'",
            fields='files(id, name)'
        ).execute()
        
        if not master_transcripts_results['files']:
            print(f"   ❌ Master Transcripts folder not found")
            return
            
        transcripts_folder_id = master_transcripts_results['files'][0]['id']
        
        # Look for transcript file with various naming patterns
        filename_patterns = [
            f"{podcast_name.replace(':', '').replace(' ', '_')}_Transcripts.md",
            f"{podcast_name.replace(':', '_').replace(' ', '_')}_Transcripts.md", 
            f"{podcast_name.replace(' ', '_')}_Transcripts.md",
            f"{podcast_name.replace(': ', '_').replace(' ', '_')}_Transcripts.md"
        ]
        
        transcript_file = None
        for pattern in filename_patterns:
            search_results = service.files().list(
                q=f"parents in '{transcripts_folder_id}' and name = '{pattern}'",
                fields='files(id, name)'
            ).execute()
            
            if search_results['files']:
                transcript_file = search_results['files'][0]
                print(f"   📄 Found transcript file: {pattern}")
                break
        
        if not transcript_file:
            print(f"   ❌ No transcript file found for {podcast_name}")
            return
        
        # Download and parse transcript file
        try:
            request = service.files().get_media(fileId=transcript_file['id'])
            content = request.execute().decode('utf-8', errors='ignore')
            
            episodes = self.extract_episodes_from_transcript(content, podcast_name)
            print(f"   📊 Found {len(episodes)} episodes in Google Drive")
            
            # Sync each episode
            matched_count = 0
            new_count = 0
            conflict_count = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for episode in episodes:
                # Check if episode exists in database
                existing = self.find_matching_episode_in_db(episode, podcast_id)
                
                if existing:
                    episode_id, existing_transcript = existing
                    
                    # Check for transcript conflicts
                    if existing_transcript and len(existing_transcript) > 100:
                        if existing_transcript.strip() != episode['transcript'].strip():
                            print(f"   ⚠️  CONFLICT: {episode['title'][:50]}... has different transcript content")
                            conflict_count += 1
                        else:
                            matched_count += 1
                    else:
                        # Update with transcript from Google Drive
                        cursor.execute("""
                            UPDATE episodes SET transcript = ?, transcribed = 1 
                            WHERE id = ?
                        """, (episode['transcript'], episode_id))
                        matched_count += 1
                        print(f"   ✅ Updated: {episode['title'][:50]}...")
                else:
                    # Create new episode (audio_url can be NULL)
                    cursor.execute("""
                        INSERT INTO episodes (
                            podcast_id, title, publish_date, transcript, 
                            transcribed, created_at
                        ) VALUES (?, ?, ?, ?, 1, ?)
                    """, (
                        podcast_id, episode['title'], episode['publish_date'], 
                        episode['transcript'], datetime.now().isoformat()
                    ))
                    new_count += 1
                    print(f"   ➕ Created: {episode['title'][:50]}...")
            
            conn.commit()
            conn.close()
            
            print(f"   📊 Summary: {matched_count} matched, {new_count} new, {conflict_count} conflicts")
            
        except Exception as e:
            print(f"   ❌ Error processing {podcast_name}: {e}")
    
    def sync_from_master_file(self):
        """Sync from the COMPLETE_MASTER_TRANSCRIPTS file that has all real content"""
        print("📄 Syncing from COMPLETE_MASTER_TRANSCRIPTS file...")
        
        service = self.sync.service
        transcripts_folder_id = '10sCLnljEf-Nxu5HmgBZqHcmbfygzu63u'
        
        # Get the complete master transcripts file
        search_results = service.files().list(
            q=f"parents in '{transcripts_folder_id}' and name = 'COMPLETE_MASTER_TRANSCRIPTS_20250809_153636.md'",
            fields='files(id, name)'
        ).execute()
        
        if not search_results['files']:
            print("❌ COMPLETE_MASTER_TRANSCRIPTS file not found")
            return
        
        file_id = search_results['files'][0]['id']
        request = service.files().get_media(fileId=file_id)
        content = request.execute().decode('utf-8', errors='ignore')
        
        print(f"📊 Master file loaded: {len(content)} characters")
        
        # Parse master file format: ## DATE followed by ### PODCAST: TITLE
        episodes = []
        date_sections = re.split(r'\n## ([0-9T:\+\-]+)\n', content)
        
        for i in range(1, len(date_sections), 2):
            if i + 1 < len(date_sections):
                date = date_sections[i]
                section_content = date_sections[i + 1]
                
                # Extract title with podcast name (### Podcast: Title)
                title_match = re.search(r'^### (.+)$', section_content, re.MULTILINE)
                if title_match:
                    full_title = title_match.group(1).strip()
                    
                    # Parse podcast name and episode title
                    if ':' in full_title:
                        podcast_part, episode_title = full_title.split(':', 1)
                        podcast_name = podcast_part.strip()
                        episode_title = episode_title.strip()
                    else:
                        podcast_name = "Unknown"
                        episode_title = full_title
                    
                    # Only process active podcasts
                    if podcast_name not in self.active_podcasts:
                        continue
                    
                    # Extract metadata
                    pub_date_match = re.search(r'\*\*Publication Date:\*\* (.+)', section_content)
                    episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', section_content)
                    
                    publish_date = pub_date_match.group(1).strip() if pub_date_match else date
                    episode_id = int(episode_id_match.group(1)) if episode_id_match else None
                    
                    # Extract transcript (after **Full Transcript:**)
                    transcript_start = section_content.find('**Full Transcript:**')
                    if transcript_start != -1:
                        transcript = section_content[transcript_start + len('**Full Transcript:**'):].strip()
                        
                        if len(transcript) > 200:  # Substantial transcript content
                            episodes.append({
                                'title': episode_title,
                                'publish_date': publish_date,
                                'transcript': transcript,
                                'episode_id': episode_id,
                                'podcast_name': podcast_name
                            })
        
        print(f"📊 Extracted {len(episodes)} episodes with real transcripts")
        
        # Group by podcast and sync
        by_podcast = {}
        for episode in episodes:
            podcast = episode['podcast_name']
            if podcast not in by_podcast:
                by_podcast[podcast] = []
            by_podcast[podcast].append(episode)
        
        total_matched = 0
        total_new = 0
        total_conflicts = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for podcast_name, podcast_episodes in by_podcast.items():
            print(f"\n📁 Processing {podcast_name}: {len(podcast_episodes)} episodes")
            
            podcast_id = self.get_podcast_id_from_name(podcast_name)
            if not podcast_id:
                print(f"   ❌ Podcast not found in database: {podcast_name}")
                continue
            
            matched = 0
            new = 0
            conflicts = 0
            
            for episode in podcast_episodes:
                existing = self.find_matching_episode_in_db(episode, podcast_id)
                
                if existing:
                    episode_id, existing_transcript = existing
                    
                    if existing_transcript and len(existing_transcript) > 100:
                        if existing_transcript.strip() != episode['transcript'].strip():
                            print(f"   ⚠️  CONFLICT: {episode['title'][:50]}...")
                            conflicts += 1
                        else:
                            matched += 1
                    else:
                        # Update with transcript
                        cursor.execute("""
                            UPDATE episodes SET transcript = ?, transcribed = 1 
                            WHERE id = ?
                        """, (episode['transcript'], episode_id))
                        matched += 1
                        print(f"   ✅ Updated: {episode['title'][:50]}...")
                else:
                    # Create new episode with required fields
                    guid = f"gdrive_sync_{podcast_id}_{episode.get('episode_id', 'unknown')}_{len(episode['title'])}"
                    audio_url = f"placeholder://gdrive_sync/{podcast_id}/{episode.get('episode_id', 'unknown')}"
                    
                    cursor.execute("""
                        INSERT INTO episodes (
                            podcast_id, title, publish_date, transcript, 
                            transcribed, created_at, audio_url, guid
                        ) VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                    """, (
                        podcast_id, episode['title'], episode['publish_date'], 
                        episode['transcript'], datetime.now().isoformat(),
                        audio_url, guid
                    ))
                    new += 1
                    print(f"   ➕ Created: {episode['title'][:50]}...")
            
            print(f"   📊 {podcast_name}: {matched} matched, {new} new, {conflicts} conflicts")
            total_matched += matched
            total_new += new
            total_conflicts += conflicts
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Master file sync complete!")
        print(f"   📊 TOTAL: {total_matched} matched, {total_new} new, {total_conflicts} conflicts")
    
    def run_sync(self):
        """Run complete sync for all active podcasts"""
        print("🔄 Starting Google Drive → Database sync...")
        
        if not self.sync.authenticate():
            print("❌ Failed to authenticate with Google Drive")
            return
        
        print("✅ Authenticated with Google Drive")
        
        # Use the master file approach instead of individual files
        self.sync_from_master_file()
        
        print(f"\n🎉 Sync complete!")
        
        # Show final database state
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 Final database state:")
        cursor.execute("""
            SELECT p.name, COUNT(*) as total_episodes, 
                   COUNT(CASE WHEN e.transcript IS NOT NULL AND LENGTH(e.transcript) > 1000 THEN 1 END) as with_transcripts
            FROM episodes e 
            JOIN podcasts p ON e.podcast_id = p.id 
            WHERE p.is_active = 1 
            GROUP BY p.name 
            ORDER BY p.name
        """)
        
        for row in cursor.fetchall():
            podcast_name, total, with_transcripts = row
            print(f"  📁 {podcast_name}: {with_transcripts}/{total} episodes with transcripts")
        
        conn.close()

if __name__ == "__main__":
    syncer = GoogleDriveToDatabase()
    syncer.run_sync()