#!/usr/bin/env python3
"""
Create organized files from the original database structure
"""
import sqlite3
from datetime import datetime

def create_organized_files():
    """Create organized files from original database"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get podcasts with transcribed content
    cursor.execute("""
        SELECT p.id, p.name, COUNT(e.id) as transcript_count
        FROM podcasts p
        JOIN episodes e ON p.id = e.podcast_id
        WHERE e.transcript IS NOT NULL AND e.transcript != ''
        GROUP BY p.id, p.name
        ORDER BY transcript_count DESC
    """)
    
    podcasts_with_content = cursor.fetchall()
    
    print(f"Creating files for {len(podcasts_with_content)} podcasts with content:")
    
    all_episodes = []  # For master file
    
    for podcast_id, podcast_name, transcript_count in podcasts_with_content:
        print(f"\n📝 {podcast_name}: {transcript_count} episodes")
        
        # Get episodes for this podcast
        cursor.execute("""
            SELECT title, transcript, publish_date, id
            FROM episodes
            WHERE podcast_id = ? 
            AND transcript IS NOT NULL 
            AND transcript != ''
            ORDER BY publish_date DESC
        """, (podcast_id,))
        
        episodes = cursor.fetchall()
        
        # Create individual transcript file
        clean_name = podcast_name.replace(':', '').replace('/', '').replace(' ', '_').replace(',', '').replace("'", "")
        transcript_file = f"{clean_name}_Transcripts.md"
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"# {podcast_name} - All Transcripts\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Episodes: {len(episodes)}\n\n")
            
            current_date = None
            for title, transcript, publish_date, episode_id in episodes:
                # Handle date formatting
                if publish_date:
                    episode_date = publish_date[:10]  # Get YYYY-MM-DD part
                else:
                    episode_date = "Unknown"
                
                if episode_date != current_date:
                    current_date = episode_date
                    f.write(f"\n## {episode_date}\n\n")
                
                f.write(f"### {title}\n")
                f.write(f"**Episode ID:** {episode_id}\n")
                f.write(f"**Date:** {publish_date}\n\n")
                f.write(f"{transcript}\n\n")
                f.write("---\n\n")
        
        print(f"   ✅ {transcript_file}")
        
        # Add to master list
        for episode in episodes:
            all_episodes.append(episode + (podcast_name,))  # Add podcast name
    
    # Create master transcript file
    print(f"\n📄 Creating master file with {len(all_episodes)} total episodes...")
    
    with open("Master_All_Transcripts.md", 'w', encoding='utf-8') as f:
        f.write(f"# Master Transcript Database - All Podcasts\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Episodes: {len(all_episodes)}\n\n")
        
        # Sort all episodes by date
        all_episodes.sort(key=lambda x: x[2] or "1900-01-01", reverse=True)
        
        current_date = None
        for title, transcript, publish_date, episode_id, podcast_name in all_episodes:
            episode_date = publish_date[:10] if publish_date else "Unknown"
            
            if episode_date != current_date:
                current_date = episode_date
                f.write(f"\n## {episode_date}\n\n")
            
            f.write(f"### {podcast_name}: {title}\n")
            f.write(f"**Episode ID:** {episode_id}\n")
            f.write(f"**Date:** {publish_date}\n\n")
            f.write(f"{transcript}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Master_All_Transcripts.md")
    
    # Since there are no analyses yet, we'll create empty analysis files
    print(f"\n📊 Creating empty analysis files (will be populated by automation)...")
    
    for podcast_id, podcast_name, transcript_count in podcasts_with_content:
        clean_name = podcast_name.replace(':', '').replace('/', '').replace(' ', '_').replace(',', '').replace("'", "")
        analysis_file = f"{clean_name}_Analysis.md"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(f"# {podcast_name} - All Analysis\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Episodes Analyzed: 0\n\n")
            f.write("*Analysis will be added automatically as episodes are processed by the daily automation.*\n\n")
        
        print(f"   📄 {analysis_file}")
    
    conn.close()
    print(f"\n🎉 All files created! Your automation workflow will now:")
    print(f"   1. Process new episodes daily")
    print(f"   2. Append transcripts to the appropriate files")
    print(f"   3. Append analyses to the appropriate files")
    print(f"   4. Update the master file")
    print(f"   5. Send daily email reports")

if __name__ == "__main__":
    create_organized_files()