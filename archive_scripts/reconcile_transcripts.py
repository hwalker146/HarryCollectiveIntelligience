#!/usr/bin/env python3
"""
Database Reconciliation Script
Parses master transcript files and reconciles them with the database,
ensuring no duplicate episodes are created.
"""

import os
import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

def connect_to_database():
    """Connect to the podcast database."""
    db_path = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/podcast_app_v2.db"
    return sqlite3.connect(db_path)

def get_podcast_id_by_name(cursor, podcast_name):
    """Get podcast ID from the database by name."""
    # Map master transcript file names to podcast names in database
    name_mapping = {
        'WSJ_Whats_News_Master_Transcripts.md': ["WSJ What's News", "WSJ Whats News"],
        'The_Intelligence_Master_Transcripts.md': ["The Intelligence"],
        'The_Infrastructure_Investor_Master_Transcripts.md': ["The Infrastructure Investor"],
        'Exchanges_at_Goldman_Sachs_Master_Transcripts.md': ["Exchanges at Goldman Sachs"],
        'Crossroads_The_Infrastructure_Podcast_Master_Transcripts.md': ["Crossroads: The Infrastructure Podcast", "Crossroads"],
        'Deal_Talks_Master_Transcripts.md': ["Deal Talks"],
        'Global_Evolution_Master_Transcripts.md': ["Global Evolution"],
        'The_Data_Center_Frontier_Show_Master_Transcripts.md': ["The Data Center Frontier Show"],
        'The_Ezra_Klein_Show_Master_Transcripts.md': ["The Ezra Klein Show"],
        'a16z_Podcast_Master_Transcripts.md': ["a16z Podcast"]
    }
    
    possible_names = name_mapping.get(podcast_name, [podcast_name])
    
    for name in possible_names:
        cursor.execute("SELECT id FROM podcasts WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
    
    print(f"Warning: No podcast found for {podcast_name}")
    return None

def parse_episode_from_content(content, date_str, episode_id):
    """Parse episode details from content block."""
    lines = content.strip().split('\n')
    title = ""
    pub_date = ""
    transcript = ""
    
    # Find the title (line starting with ###)
    for line in lines:
        if line.startswith('### '):
            title = line[4:].strip()
            break
    
    # Extract publication date and transcript
    in_transcript = False
    for line in lines:
        if line.startswith('**Publication Date:**'):
            pub_date = line.replace('**Publication Date:**', '').strip()
        elif line.startswith('**Full Transcript:**'):
            in_transcript = True
        elif in_transcript and line.strip():
            transcript += line + '\n'
    
    return {
        'title': title,
        'publication_date': pub_date,
        'episode_id': episode_id,
        'transcript': transcript.strip(),
        'date': date_str
    }

def create_episode_guid(title, date, episode_id):
    """Create a unique GUID for the episode."""
    content = f"{title}_{date}_{episode_id}"
    return hashlib.md5(content.encode()).hexdigest()

def episode_exists(cursor, guid):
    """Check if episode already exists in database."""
    cursor.execute("SELECT id FROM episodes WHERE guid = ?", (guid,))
    return cursor.fetchone() is not None

def insert_episode(cursor, podcast_id, episode_data):
    """Insert new episode into database."""
    guid = create_episode_guid(episode_data['title'], episode_data['date'], episode_data['episode_id'])
    
    # Convert publication date to timestamp
    pub_date = None
    if episode_data['publication_date']:
        try:
            pub_date = datetime.fromisoformat(episode_data['publication_date'].replace('Z', '+00:00'))
        except:
            print(f"Warning: Could not parse date {episode_data['publication_date']}")
    
    cursor.execute("""
        INSERT INTO episodes (
            podcast_id, title, description, audio_url, episode_url, 
            guid, transcript, publish_date, transcribed, processed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        podcast_id,
        episode_data['title'],
        f"Episode {episode_data['episode_id']}",  # Default description
        f"episode_{episode_data['episode_id']}/audio.mp3",  # Audio URL pattern
        "",  # Episode URL
        guid,
        episode_data['transcript'],
        pub_date,
        True,  # Already transcribed
        False  # Not processed for analysis yet
    ))
    
    return cursor.lastrowid

def update_episode_transcript(cursor, guid, transcript):
    """Update existing episode with transcript."""
    cursor.execute("""
        UPDATE episodes 
        SET transcript = ?, transcribed = TRUE 
        WHERE guid = ?
    """, (transcript, guid))

def parse_master_transcript_file(file_path):
    """Parse a master transcript file and extract episodes."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    episodes = []
    
    # Split by date headers (## YYYY-MM-DD)
    date_sections = re.split(r'\n## (\d{4}-\d{2}-\d{2})\n', content)
    
    # Skip the first section (before first date)
    for i in range(1, len(date_sections), 2):
        if i + 1 < len(date_sections):
            date_str = date_sections[i]
            section_content = date_sections[i + 1]
            
            # Split by episode headers (### Title)
            episode_parts = re.split(r'\n### ([^\n]+)\n', section_content)
            
            # Process each episode
            for j in range(1, len(episode_parts), 2):
                if j + 1 < len(episode_parts):
                    title = episode_parts[j]
                    episode_content = episode_parts[j + 1]
                    
                    # Extract episode ID
                    episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', episode_content)
                    if episode_id_match:
                        episode_id = episode_id_match.group(1)
                        
                        full_content = f"### {title}\n{episode_content}"
                        episode_data = parse_episode_from_content(full_content, date_str, episode_id)
                        
                        if episode_data['title'] and episode_data['transcript']:
                            episodes.append(episode_data)
    
    return episodes

def reconcile_file(file_path, stats):
    """Reconcile a single master transcript file with the database."""
    print(f"\nProcessing: {os.path.basename(file_path)}")
    
    # Parse episodes from file
    episodes = parse_master_transcript_file(file_path)
    print(f"Found {len(episodes)} episodes in file")
    
    if not episodes:
        print("No episodes found in file")
        return
    
    # Connect to database
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Get podcast ID
        filename = os.path.basename(file_path)
        podcast_id = get_podcast_id_by_name(cursor, filename)
        
        if not podcast_id:
            print(f"Skipping file - no matching podcast found")
            return
        
        # Process each episode
        new_episodes = 0
        updated_episodes = 0
        duplicates = 0
        
        for episode_data in episodes:
            guid = create_episode_guid(episode_data['title'], episode_data['date'], episode_data['episode_id'])
            
            if episode_exists(cursor, guid):
                # Check if episode has transcript
                cursor.execute("SELECT transcript FROM episodes WHERE guid = ?", (guid,))
                result = cursor.fetchone()
                
                if not result[0] or result[0].strip() == "":
                    # Update with transcript
                    update_episode_transcript(cursor, guid, episode_data['transcript'])
                    updated_episodes += 1
                    print(f"  Updated transcript for: {episode_data['title']}")
                else:
                    duplicates += 1
            else:
                # Insert new episode
                episode_id = insert_episode(cursor, podcast_id, episode_data)
                new_episodes += 1
                print(f"  Added new episode: {episode_data['title']} (ID: {episode_id})")
        
        # Commit changes
        conn.commit()
        
        # Update stats
        stats['new_episodes'] += new_episodes
        stats['updated_episodes'] += updated_episodes
        stats['duplicates'] += duplicates
        stats['files_processed'] += 1
        
        print(f"  Results: {new_episodes} new, {updated_episodes} updated, {duplicates} duplicates")
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main reconciliation function."""
    print("Starting Database Reconciliation...")
    print("=" * 50)
    
    # Initialize statistics
    stats = {
        'files_processed': 0,
        'new_episodes': 0,
        'updated_episodes': 0,
        'duplicates': 0
    }
    
    # Path to master transcripts directory
    transcripts_dir = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/content/master_transcripts"
    
    # Process each master transcript file
    for filename in os.listdir(transcripts_dir):
        if filename.endswith('_Master_Transcripts.md'):
            file_path = os.path.join(transcripts_dir, filename)
            reconcile_file(file_path, stats)
    
    # Print final summary
    print("\n" + "=" * 50)
    print("RECONCILIATION COMPLETE")
    print("=" * 50)
    print(f"Files processed: {stats['files_processed']}")
    print(f"New episodes added: {stats['new_episodes']}")
    print(f"Episodes updated with transcripts: {stats['updated_episodes']}")
    print(f"Duplicates skipped: {stats['duplicates']}")
    print(f"Total episodes processed: {stats['new_episodes'] + stats['updated_episodes'] + stats['duplicates']}")

if __name__ == "__main__":
    main()