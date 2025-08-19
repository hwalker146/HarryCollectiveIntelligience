#!/usr/bin/env python3
"""
Create missing episodes in database for all transcripts found in Google Drive data
"""
import sqlite3
import re
from datetime import datetime
from pathlib import Path

class MissingEpisodeCreator:
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
        self.created_episodes = 0
        
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
    
    def create_missing_episodes(self):
        """Create missing episodes in database"""
        print("\n🏗️ Creating missing episodes in database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get podcast mappings
        cursor.execute("SELECT id, name FROM podcasts")
        podcasts = {name: id for id, name in cursor.fetchall()}
        
        created_by_podcast = {}
        
        for episode_data in self.parsed_episodes:
            podcast_name = episode_data['podcast_name']
            title = episode_data['title']
            transcript = episode_data['transcript']
            publish_date = episode_data['publish_date']
            
            if podcast_name not in podcasts:
                print(f"⚠️ Podcast not found: {podcast_name}")
                continue
            
            podcast_id = podcasts[podcast_name]
            
            # Check if episode already exists
            cursor.execute("""
                SELECT id FROM episodes 
                WHERE podcast_id = ? AND title = ?
            """, (podcast_id, title))
            
            existing = cursor.fetchone()
            
            if not existing:
                # Episode doesn't exist - create it
                try:
                    cursor.execute("""
                        INSERT INTO episodes (
                            podcast_id, title, audio_url, publish_date, 
                            transcript, transcribed, guid, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        podcast_id,
                        title,
                        "",  # No audio URL for these episodes
                        publish_date.isoformat() if publish_date else None,
                        transcript,
                        1,  # Mark as transcribed
                        f"gdrive-{podcast_id}-{hash(title)}",  # Generate unique GUID
                        datetime.now().isoformat()
                    ))
                    
                    episode_id = cursor.lastrowid
                    self.created_episodes += 1
                    
                    # Track by podcast
                    if podcast_name not in created_by_podcast:
                        created_by_podcast[podcast_name] = 0
                    created_by_podcast[podcast_name] += 1
                    
                    print(f"   ➕ Created episode {episode_id}: {title[:50]}...")
                    
                except Exception as e:
                    print(f"   ❌ Failed to create episode '{title[:50]}...': {e}")
            else:
                # Episode exists - update transcript if it's empty
                cursor.execute("""
                    SELECT LENGTH(COALESCE(transcript, '')) FROM episodes WHERE id = ?
                """, (existing[0],))
                
                transcript_length = cursor.fetchone()[0]
                
                if transcript_length < 100:
                    cursor.execute("""
                        UPDATE episodes 
                        SET transcript = ?, transcribed = 1
                        WHERE id = ?
                    """, (transcript, existing[0]))
                    print(f"   ✅ Updated transcript for episode {existing[0]}: {title[:50]}...")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Created {self.created_episodes} missing episodes")
        
        if created_by_podcast:
            print("📊 Episodes created by podcast:")
            for podcast, count in created_by_podcast.items():
                print(f"   📄 {podcast}: {count} new episodes")
    
    def verify_final_counts(self):
        """Verify final episode counts match Google Drive data"""
        print("\n🔍 Verifying final episode counts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.name, COUNT(*) as total_episodes, 
                   COUNT(CASE WHEN e.transcript IS NOT NULL AND LENGTH(e.transcript) >= 100 THEN 1 END) as with_transcripts
            FROM episodes e 
            JOIN podcasts p ON e.podcast_id = p.id 
            GROUP BY p.name 
            ORDER BY p.name
        """)
        
        db_counts = cursor.fetchall()
        conn.close()
        
        # Compare with parsed counts
        parsed_counts = {}
        for episode in self.parsed_episodes:
            podcast = episode['podcast_name']
            parsed_counts[podcast] = parsed_counts.get(podcast, 0) + 1
        
        print("📊 Database vs Google Drive counts:")
        for podcast_name, total_episodes, with_transcripts in db_counts:
            if podcast_name in parsed_counts:
                parsed_count = parsed_counts[podcast_name]
                status = "✅" if with_transcripts >= parsed_count else "⚠️"
                print(f"   {status} {podcast_name}: DB={with_transcripts}, GDrive={parsed_count}")
            else:
                print(f"   📄 {podcast_name}: DB={with_transcripts}, GDrive=0")
    
    def run_creation(self):
        """Run the complete episode creation process"""
        print("🚀 Starting missing episode creation...")
        print("=" * 60)
        
        # Step 1: Parse all files
        self.parse_all_files()
        
        # Step 2: Create missing episodes
        self.create_missing_episodes()
        
        # Step 3: Verify final counts
        self.verify_final_counts()
        
        print("\n" + "=" * 60)
        print("🎉 Missing episode creation complete!")

if __name__ == "__main__":
    creator = MissingEpisodeCreator()
    creator.run_creation()