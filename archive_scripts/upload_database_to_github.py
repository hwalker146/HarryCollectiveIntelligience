#!/usr/bin/env python3
"""
Upload the real database to GitHub so the workflow can use it
"""
import os
import sqlite3
import shutil
from datetime import datetime

def prepare_database_for_github():
    """Prepare and upload the real database"""
    
    # First, let's see what databases we have
    print("🔍 Checking available databases...")
    
    databases = []
    for file in os.listdir('.'):
        if file.endswith('.db'):
            databases.append(file)
    
    print(f"Found databases: {databases}")
    
    # Check if we can find a database with actual content
    best_db = None
    best_count = 0
    
    for db_file in databases:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Count episodes with transcripts
            cursor.execute("""
                SELECT COUNT(*) FROM episodes 
                WHERE transcript IS NOT NULL AND transcript != ''
            """)
            
            count = cursor.fetchone()[0]
            print(f"{db_file}: {count} transcribed episodes")
            
            if count > best_count:
                best_count = count
                best_db = db_file
            
            conn.close()
            
        except Exception as e:
            print(f"Error checking {db_file}: {e}")
    
    if best_db and best_count > 0:
        print(f"✅ Best database: {best_db} with {best_count} episodes")
        
        # Copy it as the main database
        if best_db != 'podcast_app_v2.db':
            shutil.copy2(best_db, 'podcast_app_v2.db')
            print(f"📁 Copied {best_db} to podcast_app_v2.db")
        
        return True
    else:
        print("❌ No database with content found")
        return False

def create_organized_files_from_real_data():
    """Create organized files using the real database"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get actual podcast data
    cursor.execute("""
        SELECT DISTINCT p.id, p.name, 
               COUNT(CASE WHEN e.transcript IS NOT NULL AND e.transcript != '' THEN 1 END) as transcripts,
               COUNT(ar.id) as analyses
        FROM podcasts p
        LEFT JOIN episodes e ON p.id = e.podcast_id
        LEFT JOIN analysis_reports ar ON e.id = ar.episode_id
        GROUP BY p.id, p.name
        HAVING transcripts > 0 OR analyses > 0
        ORDER BY transcripts DESC
    """)
    
    podcast_data = cursor.fetchall()
    
    print(f"📊 Found {len(podcast_data)} podcasts with content:")
    for pid, name, transcripts, analyses in podcast_data:
        print(f"  {name}: {transcripts} transcripts, {analyses} analyses")
        
        # Create individual files for each podcast
        create_podcast_files(pid, name)
    
    # Create master file
    create_master_file()
    
    conn.close()

def create_podcast_files(podcast_id, podcast_name):
    """Create transcript and analysis files for one podcast"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    clean_name = podcast_name.replace(':', '').replace('/', '').replace(' ', '_').replace(',', '')
    transcript_file = f"{clean_name}_Transcripts.md"
    analysis_file = f"{clean_name}_Analysis.md"
    
    # Create transcript file
    cursor.execute('''
        SELECT e.title, e.transcript, e.pub_date, e.id
        FROM episodes e
        WHERE e.podcast_id = ? 
        AND e.transcript IS NOT NULL 
        AND e.transcript != ''
        ORDER BY e.pub_date DESC
    ''', (podcast_id,))
    
    episodes = cursor.fetchall()
    
    if episodes:
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(f"# {podcast_name} - All Transcripts\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Episodes: {len(episodes)}\n\n")
            
            current_date = None
            for title, transcript, pub_date, episode_id in episodes:
                episode_date = pub_date[:10] if pub_date else "Unknown"
                
                if episode_date != current_date:
                    current_date = episode_date
                    f.write(f"\n## {episode_date}\n\n")
                
                f.write(f"### {title}\n")
                f.write(f"**Episode ID:** {episode_id}\n")
                f.write(f"**Date:** {pub_date}\n\n")
                f.write(f"{transcript}\n\n")
                f.write("---\n\n")
        
        print(f"   ✅ {transcript_file}")
    
    # Create analysis file
    cursor.execute('''
        SELECT ar.analysis_result, ar.key_quote, ar.created_at, e.title, e.pub_date, e.id
        FROM analysis_reports ar
        JOIN episodes e ON ar.episode_id = e.id
        WHERE e.podcast_id = ?
        ORDER BY e.pub_date DESC
    ''', (podcast_id,))
    
    analyses = cursor.fetchall()
    
    if analyses:
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(f"# {podcast_name} - All Analysis\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Episodes Analyzed: {len(analyses)}\n\n")
            
            current_date = None
            for analysis_result, key_quote, created_at, title, pub_date, episode_id in analyses:
                episode_date = pub_date[:10] if pub_date else "Unknown"
                
                if episode_date != current_date:
                    current_date = episode_date
                    f.write(f"\n## {episode_date}\n\n")
                
                f.write(f"### {title}\n")
                f.write(f"**Episode ID:** {episode_id}\n")
                f.write(f"**Publication Date:** {pub_date}\n")
                f.write(f"**Analysis Date:** {created_at}\n\n")
                
                if key_quote and key_quote.strip():
                    f.write(f"**Key Quote:** {key_quote}\n\n")
                
                f.write(f"{analysis_result}\n\n")
                f.write("---\n\n")
        
        print(f"   ✅ {analysis_file}")
    
    conn.close()

def create_master_file():
    """Create master transcript file"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.title, e.transcript, e.pub_date, p.name as podcast_name, e.id
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.transcript IS NOT NULL 
        AND e.transcript != ''
        ORDER BY e.pub_date DESC
    ''')
    
    episodes = cursor.fetchall()
    
    with open("Master_All_Transcripts.md", 'w', encoding='utf-8') as f:
        f.write(f"# Master Transcript Database - All Podcasts\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Episodes: {len(episodes)}\n\n")
        
        current_date = None
        for title, transcript, pub_date, podcast_name, episode_id in episodes:
            episode_date = pub_date[:10] if pub_date else "Unknown"
            
            if episode_date != current_date:
                current_date = episode_date
                f.write(f"\n## {episode_date}\n\n")
            
            f.write(f"### {podcast_name}: {title}\n")
            f.write(f"**Episode ID:** {episode_id}\n")
            f.write(f"**Date:** {pub_date}\n\n")
            f.write(f"{transcript}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Master_All_Transcripts.md ({len(episodes)} episodes)")
    conn.close()

if __name__ == "__main__":
    print("🚀 Preparing database and files for GitHub Actions...")
    
    if prepare_database_for_github():
        create_organized_files_from_real_data()
        print("\n✅ Ready for GitHub Actions!")
        print("💡 Commit and push these files to trigger the workflow with real data.")
    else:
        print("❌ Could not find database with content")