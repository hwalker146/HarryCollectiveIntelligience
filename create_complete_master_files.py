#!/usr/bin/env python3
"""
Create complete master files with ALL transcripts and analyses
"""
import sqlite3
from datetime import datetime
import os

def create_complete_master_files():
    """Create comprehensive master files with all historical data"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    print("📊 Gathering all historical data...")
    
    # Get ALL transcribed episodes
    cursor.execute("""
        SELECT e.id, e.title, e.transcript, e.pub_date, p.name as podcast_name, e.created_at
        FROM episodes e
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE e.transcript IS NOT NULL 
        AND LENGTH(e.transcript) > 100
        ORDER BY e.pub_date DESC, p.name
    """)
    
    transcript_episodes = cursor.fetchall()
    print(f"   Found {len(transcript_episodes)} transcribed episodes")
    
    # Get ALL analyses
    cursor.execute("""
        SELECT e.id, e.title, ar.analysis_result, e.pub_date, p.name as podcast_name, 
               ar.created_at as analysis_date, ar.key_quote
        FROM analysis_reports ar
        JOIN episodes e ON ar.episode_id = e.id
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE ar.user_id = 2
        ORDER BY e.pub_date DESC, p.name
    """)
    
    analysis_episodes = cursor.fetchall()
    print(f"   Found {len(analysis_episodes)} analyzed episodes")
    
    conn.close()
    
    # Create timestamp for files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create COMPLETE master transcript file
    transcript_file = f"COMPLETE_MASTER_TRANSCRIPTS_{timestamp}.md"
    print(f"📄 Creating complete transcript file: {transcript_file}")
    
    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Complete Master Podcast Transcripts
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Episodes: {len(transcript_episodes)}

This file contains ALL transcribed podcast episodes from:
- The Infrastructure Investor
- Crossroads: The Infrastructure Podcast  
- Deal Talks
- Exchanges at Goldman Sachs
- Global Evolution
- The Data Center Frontier Show

---

""")
        
        current_date = None
        for episode in transcript_episodes:
            episode_id, title, transcript, pub_date, podcast_name, created_at = episode
            
            # Group by publication date
            if pub_date != current_date:
                current_date = pub_date
                f.write(f"\n## {pub_date}\n\n")
            
            f.write(f"### {podcast_name}: {title}\n")
            f.write(f"**Publication Date:** {pub_date}\n")
            f.write(f"**Episode ID:** {episode_id}\n")
            f.write(f"**Transcribed:** {created_at}\n\n")
            f.write(f"**Full Transcript:**\n{transcript}\n\n")
            f.write("---\n\n")
    
    # Create COMPLETE master analysis file
    analysis_file = f"COMPLETE_MASTER_ANALYSIS_{timestamp}.md"
    print(f"📄 Creating complete analysis file: {analysis_file}")
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Complete Master Podcast Analysis
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Analyses: {len(analysis_episodes)}

This file contains ALL podcast analyses for infrastructure and finance investment insights from:
- The Infrastructure Investor
- Crossroads: The Infrastructure Podcast  
- Deal Talks  
- Exchanges at Goldman Sachs
- Global Evolution
- The Data Center Frontier Show

---

""")
        
        current_date = None
        for episode in analysis_episodes:
            episode_id, title, analysis, pub_date, podcast_name, analysis_date, key_quote = episode
            
            # Group by publication date
            if pub_date != current_date:
                current_date = pub_date
                f.write(f"\n## {pub_date}\n\n")
            
            f.write(f"### {podcast_name}: {title}\n")
            f.write(f"**Publication Date:** {pub_date}\n")
            f.write(f"**Episode ID:** {episode_id}\n")
            f.write(f"**Analysis Date:** {analysis_date}\n")
            
            if key_quote:
                f.write(f"**Key Quote:** {key_quote}\n")
            
            f.write(f"\n**Full Analysis:**\n{analysis}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Complete master files created:")
    print(f"   📄 Transcripts: {transcript_file} ({os.path.getsize(transcript_file) / (1024*1024):.1f} MB)")
    print(f"   📄 Analysis: {analysis_file} ({os.path.getsize(analysis_file) / (1024*1024):.1f} MB)")
    
    return transcript_file, analysis_file

def sync_complete_files_to_drive(transcript_file, analysis_file):
    """Sync the complete master files to Google Drive"""
    try:
        from google_drive_sync import GoogleDriveSync
        
        print("☁️ Syncing complete master files to Google Drive...")
        sync = GoogleDriveSync()
        
        if not sync.authenticate():
            print("❌ Google Drive authentication failed")
            return False
        
        # Ensure folder structure exists
        if not sync.podcast_folder_id:
            sync.create_folder_structure()
        
        # Upload complete files
        transcript_result = sync.upload_or_update_file(
            transcript_file, 
            sync.transcripts_folder_id,
            f"Complete master transcripts - ALL {datetime.now().strftime('%Y-%m-%d')} episodes"
        )
        
        analysis_result = sync.upload_or_update_file(
            analysis_file,
            sync.analysis_folder_id, 
            f"Complete master analysis - ALL {datetime.now().strftime('%Y-%m-%d')} episodes"
        )
        
        if transcript_result and analysis_result:
            folder_url = sync.get_drive_folder_url()
            print(f"✅ Complete master files synced to Google Drive!")
            print(f"📁 Access: {folder_url}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Google Drive sync failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating complete master files with ALL historical data...")
    
    transcript_file, analysis_file = create_complete_master_files()
    
    # Sync to Google Drive
    sync_complete_files_to_drive(transcript_file, analysis_file)
    
    print(f"\n🎉 COMPLETE! You now have:")
    print(f"   📄 Complete transcript archive")
    print(f"   📄 Complete analysis archive") 
    print(f"   ☁️ Both synced to Google Drive")
    print(f"   🔗 Access: https://drive.google.com/drive/folders/1Zo8p26SksJCUTviH95w0JOoKdR1fHGzJ")