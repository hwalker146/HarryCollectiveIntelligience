#!/usr/bin/env python3
"""
Fixed Database Reconciliation Script
Parses ALL master transcript files and reconciles them with the database,
handling multiple date formats and ensuring no duplicate episodes.
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

def get_podcast_id_by_name(cursor, podcast_name, filename):
    """Get podcast ID from the database by name."""
    # Enhanced mapping based on all the files we've seen
    name_mapping = {
        'WSJ_Whats_News_Master_Transcripts.md': ["WSJ What's News", "WSJ Whats News"],
        'WSJ_Whats_News_Transcripts.md': ["WSJ What's News", "WSJ Whats News"],
        'The_Intelligence_Master_Transcripts.md': ["The Intelligence"],
        'The_Intelligence_Transcripts.md': ["The Intelligence"],
        'The_Infrastructure_Investor_Master_Transcripts.md': ["The Infrastructure Investor"],
        'The_Infrastructure_Investor_Transcripts.md': ["The Infrastructure Investor"],
        'Exchanges_at_Goldman_Sachs_Master_Transcripts.md': ["Exchanges at Goldman Sachs"],
        'Exchanges_at_Goldman_Sachs_Transcripts.md': ["Exchanges at Goldman Sachs"],
        'Crossroads_The_Infrastructure_Podcast_Master_Transcripts.md': ["Crossroads: The Infrastructure Podcast", "Crossroads"],
        'Crossroads_The_Infrastructure_Podcast_Transcripts.md': ["Crossroads: The Infrastructure Podcast", "Crossroads"],
        'Crossroads_Transcripts.md': ["Crossroads: The Infrastructure Podcast", "Crossroads"],
        'Deal_Talks_Master_Transcripts.md': ["Deal Talks"],
        'Global_Evolution_Master_Transcripts.md': ["Global Evolution"],
        'Global_Evolution_Transcripts.md': ["Global Evolution"],
        'Global_Energy_Transition_Transcripts.md': ["Global Evolution"],
        'The_Data_Center_Frontier_Show_Master_Transcripts.md': ["The Data Center Frontier Show"],
        'The_Data_Center_Frontier_Show_Transcripts.md': ["The Data Center Frontier Show"],
        'The_Ezra_Klein_Show_Master_Transcripts.md': ["The Ezra Klein Show"],
        'a16z_Podcast_Master_Transcripts.md': ["a16z Podcast"],
        'Business_Strategy_Podcast_Transcripts.md': ["Business Strategy Podcast"],
        'Tech_Innovation_Weekly_Transcripts.md': ["Tech Innovation Weekly"],
        'Master_All_Transcripts.md': None  # Special case - contains multiple podcasts
    }
    
    possible_names = name_mapping.get(filename, [podcast_name])
    
    if possible_names is None:
        # For Master_All_Transcripts.md, we'll need to determine podcast from episode title
        return None
        
    for name in possible_names:
        cursor.execute("SELECT id FROM podcasts WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
    
    print(f"Warning: No podcast found for {filename}")
    return None

def determine_podcast_from_title(cursor, title):
    """Determine podcast from episode title for Master_All_Transcripts.md file."""
    title_lower = title.lower()
    
    # Define patterns for each podcast
    patterns = {
        "The Data Center Frontier Show": ["data center frontier", "dcf"],
        "Global Evolution": ["global evolution", "energy transition"],
        "Deal Talks": ["deal talks"],
        "Exchanges at Goldman Sachs": ["exchanges at goldman", "goldman sachs"],
        "The Infrastructure Investor": ["infrastructure investor"],
        "Crossroads: The Infrastructure Podcast": ["crossroads", "infrastructure podcast"],
        "a16z Podcast": ["a16z"],
        "WSJ What's News": ["wsj", "what's news"],
        "The Intelligence": ["intelligence"]
    }
    
    for podcast_name, keywords in patterns.items():
        if any(keyword in title_lower for keyword in keywords):
            cursor.execute("SELECT id FROM podcasts WHERE name = ?", (podcast_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
    
    # If no pattern matches, return None and we'll skip this episode
    return None

def parse_episode_from_content(content, date_str, episode_id, title=""):
    """Parse episode details from content block."""
    lines = content.strip().split('\n')
    
    if not title:
        # Find the title (line starting with ###)
        for line in lines:
            if line.startswith('### '):
                title = line[4:].strip()
                break
    
    pub_date = ""
    transcript = ""
    
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
            # Handle multiple date formats
            pub_date_str = episode_data['publication_date']
            # Remove timezone info if present
            if '+' in pub_date_str:
                pub_date_str = pub_date_str.split('+')[0]
            if 'T' in pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str)
            else:
                pub_date = datetime.fromisoformat(pub_date_str)
        except Exception as e:
            print(f"Warning: Could not parse date {episode_data['publication_date']}: {e}")
    
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
    filename = os.path.basename(file_path)
    
    # Handle different date formats
    # Format 1: ## 2025-08-15
    # Format 2: ## 2025-08-07T17:44:44+00:00
    date_patterns = [
        r'\n## (\d{4}-\d{2}-\d{2})\n',  # Simple date format
        r'\n## (\d{4}-\d{2}-\d{2}T[\d:+.-]+)\n'  # ISO datetime format
    ]
    
    for date_pattern in date_patterns:
        date_sections = re.split(date_pattern, content)
        
        if len(date_sections) >= 3:  # Found date sections
            # Process each date section
            for i in range(1, len(date_sections), 2):
                if i + 1 < len(date_sections):
                    date_str = date_sections[i]
                    # Extract just the date part if it's a full timestamp
                    if 'T' in date_str:
                        date_str = date_str.split('T')[0]
                    
                    section_content = date_sections[i + 1]
                    
                    # Find episodes in this date section
                    episode_parts = re.split(r'\n### ([^\n]+)\n', section_content)
                    
                    for j in range(1, len(episode_parts), 2):
                        if j + 1 < len(episode_parts):
                            title = episode_parts[j]
                            episode_content = episode_parts[j + 1]
                            
                            # Extract episode ID
                            episode_id_match = re.search(r'\*\*Episode ID:\*\* (\d+)', episode_content)
                            if episode_id_match:
                                episode_id = episode_id_match.group(1)
                                
                                full_content = f"### {title}\n{episode_content}"
                                episode_data = parse_episode_from_content(full_content, date_str, episode_id, title)
                                
                                if episode_data['title'] and episode_data['transcript']:
                                    episodes.append(episode_data)
            break  # Stop after finding the right format
    
    return episodes

def reconcile_file(file_path, stats):
    """Reconcile a single master transcript file with the database."""
    filename = os.path.basename(file_path)
    print(f"\nProcessing: {filename}")
    
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
        # Process each episode
        new_episodes = 0
        updated_episodes = 0
        duplicates = 0
        skipped = 0
        
        for episode_data in episodes:
            # Determine podcast ID
            if filename == 'Master_All_Transcripts.md':
                podcast_id = determine_podcast_from_title(cursor, episode_data['title'])
            else:
                podcast_id = get_podcast_id_by_name(cursor, "", filename)
            
            if not podcast_id:
                print(f"  Skipped: {episode_data['title']} (no matching podcast)")
                skipped += 1
                continue
            
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
        stats['skipped'] += skipped
        stats['files_processed'] += 1
        
        print(f"  Results: {new_episodes} new, {updated_episodes} updated, {duplicates} duplicates, {skipped} skipped")
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main reconciliation function."""
    print("Starting COMPLETE Database Reconciliation...")
    print("=" * 60)
    
    # Initialize statistics
    stats = {
        'files_processed': 0,
        'new_episodes': 0,
        'updated_episodes': 0,
        'duplicates': 0,
        'skipped': 0
    }
    
    # Path to master transcripts directory
    transcripts_dir = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/content/master_transcripts"
    
    # Process ALL transcript files (not just _Master_Transcripts.md)
    for filename in sorted(os.listdir(transcripts_dir)):
        if filename.endswith('.md') and 'Transcript' in filename:
            file_path = os.path.join(transcripts_dir, filename)
            reconcile_file(file_path, stats)
    
    # Print final summary
    print("\n" + "=" * 60)
    print("COMPLETE RECONCILIATION FINISHED")
    print("=" * 60)
    print(f"Files processed: {stats['files_processed']}")
    print(f"New episodes added: {stats['new_episodes']}")
    print(f"Episodes updated with transcripts: {stats['updated_episodes']}")
    print(f"Duplicates skipped: {stats['duplicates']}")
    print(f"Episodes skipped (no podcast match): {stats['skipped']}")
    print(f"Total episodes processed: {stats['new_episodes'] + stats['updated_episodes'] + stats['duplicates']}")

if __name__ == "__main__":
    main()