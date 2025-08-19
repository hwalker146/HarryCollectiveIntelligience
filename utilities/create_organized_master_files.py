#!/usr/bin/env python3
"""
Create organized master transcript files for each podcast
Episodes organized by date (newest first)
"""

import os
import sqlite3
from datetime import datetime

def connect_to_database():
    """Connect to the podcast database."""
    db_path = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/podcast_app_v2.db"
    return sqlite3.connect(db_path)

def safe_filename(name):
    """Create a safe filename from podcast name."""
    return name.replace(":", "").replace(" ", "_").replace("'", "")

def create_master_file_for_podcast(podcast_name, podcast_id, output_dir):
    """Create a master transcript file for a specific podcast."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Get all episodes with transcripts for this podcast, ordered by date (newest first)
        cursor.execute("""
            SELECT title, publish_date, transcript, guid
            FROM episodes 
            WHERE podcast_id = ? AND transcribed = TRUE AND transcript IS NOT NULL AND LENGTH(transcript) > 100
            ORDER BY publish_date DESC
        """, (podcast_id,))
        
        episodes = cursor.fetchall()
        
        if not episodes:
            print(f"No transcribed episodes found for {podcast_name}")
            return
        
        # Create filename
        safe_name = safe_filename(podcast_name)
        filename = f"{safe_name}_Master_Transcripts_Organized.md"
        filepath = os.path.join(output_dir, filename)
        
        # Generate content
        content = f"# {podcast_name} - Master Transcripts\n\n"
        content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**Total Episodes:** {len(episodes)}\n\n"
        content += "Episodes organized by publication date (newest first).\n\n"
        content += "---\n\n"
        
        current_date = None
        
        for title, publish_date, transcript, guid in episodes:
            # Parse date
            if publish_date:
                try:
                    if 'T' in publish_date:
                        dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(publish_date)
                    episode_date = dt.strftime('%Y-%m-%d')
                    display_date = dt.strftime('%Y-%m-%dT%H:%M:%S')
                except:
                    episode_date = "Unknown"
                    display_date = publish_date or "Unknown"
            else:
                episode_date = "Unknown"
                display_date = "Unknown"
            
            # Add date header if changed
            if episode_date != current_date:
                current_date = episode_date
                content += f"## {episode_date}\n\n"
            
            # Add episode
            content += f"### {title}\n"
            content += f"**Publication Date:** {display_date}\n"
            content += f"**GUID:** {guid}\n\n"
            content += f"**Full Transcript:**\n"
            content += f"{transcript}\n\n"
            content += "---\n\n"
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filename} ({len(episodes)} episodes)")
        
    except Exception as e:
        print(f"Error creating file for {podcast_name}: {str(e)}")
    finally:
        conn.close()

def main():
    """Create organized master transcript files for all podcasts."""
    print("Creating Organized Master Transcript Files...")
    print("=" * 50)
    
    # Output directory - overwrite the existing organized files
    output_dir = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/content/master_transcripts_organized"
    
    # Remove existing files first
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith('.md'):
                os.remove(os.path.join(output_dir, filename))
                print(f"Removed old file: {filename}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all podcasts that have transcribed episodes
    conn = connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT p.id, p.name 
        FROM podcasts p 
        JOIN episodes e ON p.id = e.podcast_id 
        WHERE e.transcribed = TRUE AND e.transcript IS NOT NULL AND LENGTH(e.transcript) > 100
        ORDER BY p.name
    """)
    
    podcasts = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(podcasts)} podcasts with transcripts")
    print()
    
    # Create master file for each podcast
    for podcast_id, podcast_name in podcasts:
        create_master_file_for_podcast(podcast_name, podcast_id, output_dir)
    
    print()
    print("=" * 50)
    print(f"Organized master files created in: {output_dir}")
    print("=" * 50)

if __name__ == "__main__":
    main()