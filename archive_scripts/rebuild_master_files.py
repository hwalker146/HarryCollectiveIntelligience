#!/usr/bin/env python3
"""
Rebuild all master transcript files from database
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

def rebuild_master_files():
    """Rebuild all master transcript files from existing database data"""
    
    print("🔧 REBUILDING ALL MASTER TRANSCRIPT FILES")
    print("=" * 60)
    
    # Create master directory
    master_dir = Path('content/master_transcripts')
    master_dir.mkdir(parents=True, exist_ok=True)
    
    # Podcast name to file mapping
    podcast_files = {
        'Exchanges at Goldman Sachs': 'Exchanges_at_Goldman_Sachs_Master_Transcripts.md',
        'The Infrastructure Investor': 'The_Infrastructure_Investor_Master_Transcripts.md',
        'The Data Center Frontier Show': 'The_Data_Center_Frontier_Show_Master_Transcripts.md',
        'Crossroads: The Infrastructure Podcast': 'Crossroads_The_Infrastructure_Podcast_Master_Transcripts.md',
        'Deal Talks': 'Deal_Talks_Master_Transcripts.md',
        'Global Evolution': 'Global_Evolution_Master_Transcripts.md',
        'WSJ What\'s News': 'WSJ_Whats_News_Master_Transcripts.md',
        'The Intelligence': 'The_Intelligence_Master_Transcripts.md',
        'The Ezra Klein Show': 'The_Ezra_Klein_Show_Master_Transcripts.md',
        'a16z Podcast': 'a16z_Podcast_Master_Transcripts.md'
    }
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get all podcasts with transcripts
    cursor.execute("""
        SELECT p.name, COUNT(e.id) as total_episodes, 
               COUNT(CASE WHEN e.transcript IS NOT NULL AND e.transcript != '' THEN 1 END) as with_transcripts
        FROM podcasts p 
        LEFT JOIN episodes e ON p.id = e.podcast_id 
        WHERE p.name IN ({})
        GROUP BY p.name
        ORDER BY p.name
    """.format(','.join(['?' for _ in podcast_files.keys()])), list(podcast_files.keys()))
    
    podcast_stats = cursor.fetchall()
    
    for podcast_name, total_episodes, with_transcripts in podcast_stats:
        print(f"\n📝 {podcast_name}")
        print(f"   Episodes: {total_episodes}, With transcripts: {with_transcripts}")
        
        if with_transcripts == 0:
            print("   ⏭️  No transcripts, skipping")
            continue
        
        filename = podcast_files.get(podcast_name)
        if not filename:
            print("   ❌ No filename configured")
            continue
        
        filepath = master_dir / filename
        
        # Get all episodes with transcripts for this podcast, ordered by date
        cursor.execute("""
            SELECT e.id, e.title, e.publish_date, e.transcript
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE p.name = ? 
            AND e.transcript IS NOT NULL 
            AND e.transcript != ''
            ORDER BY e.publish_date DESC
        """, (podcast_name,))
        
        episodes = cursor.fetchall()
        
        if not episodes:
            print("   ⏭️  No transcribed episodes found")
            continue
        
        # Build master file content
        content = f"""# {podcast_name} - Master Transcripts

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Episodes:** {len(episodes)}

Episodes organized by publication date (newest first).

---

"""
        
        for episode_id, title, publish_date, transcript in episodes:
            # Parse date
            if publish_date:
                date_str = publish_date.split('T')[0] if 'T' in publish_date else publish_date.split(' ')[0]
            else:
                date_str = 'Unknown'
            
            episode_content = f"""## {date_str}

### {title}
**Publication Date:** {publish_date or 'Unknown'}
**Episode ID:** {episode_id}

**Full Transcript:**
{transcript}

---

"""
            content += episode_content
        
        # Write master file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Created {filename} with {len(episodes)} episodes")
    
    conn.close()
    
    print(f"\n🎯 MASTER FILES REBUILD COMPLETE")
    print(f"📁 Files saved to: {master_dir}")
    
    # List all created files
    print(f"\n📄 FILES CREATED:")
    for file in sorted(master_dir.glob("*.md")):
        size_kb = file.stat().st_size / 1024
        print(f"   {file.name} ({size_kb:.1f}KB)")

if __name__ == "__main__":
    rebuild_master_files()