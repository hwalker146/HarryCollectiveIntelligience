#!/usr/bin/env python3
"""
Regenerate ALL master transcript files from database with proper chronological ordering
Ensures all episodes are included and ordered newest first
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def regenerate_all_master_files():
    """Regenerate all master transcript files from database"""
    print("🔄 REGENERATING ALL MASTER TRANSCRIPT FILES...")
    
    db_path = 'podcast_app_v2.db'
    master_dir = Path('content/master_transcripts_organized')
    master_dir.mkdir(parents=True, exist_ok=True)
    
    # Podcast name to file mapping
    podcast_files = {
        'Exchanges at Goldman Sachs': 'Exchanges_at_Goldman_Sachs_Master_Transcripts_Organized.md',
        'The Infrastructure Investor': 'The_Infrastructure_Investor_Master_Transcripts_Organized.md',
        'The Data Center Frontier Show': 'The_Data_Center_Frontier_Show_Master_Transcripts_Organized.md',
        'Crossroads: The Infrastructure Podcast': 'Crossroads_The_Infrastructure_Podcast_Master_Transcripts_Organized.md',
        'Deal Talks': 'Deal_Talks_Master_Transcripts_Organized.md',
        'Global Evolution': 'Global_Evolution_Master_Transcripts_Organized.md',
        'WSJ What\'s News': 'WSJ_Whats_News_Master_Transcripts_Organized.md',
        'The Intelligence': 'The_Intelligence_Master_Transcripts_Organized.md',
        'The Ezra Klein Show': 'The_Ezra_Klein_Show_Master_Transcripts_Organized.md',
        'Optimistic Outlook': 'Optimistic_Outlook_Master_Transcripts_Organized.md',
        'The Engineers Collective': 'The_Engineers_Collective_Master_Transcripts_Organized.md',
        'Talking Infrastructure': 'Talking_Infrastructure_Master_Transcripts_Organized.md',
        'a16z Podcast': 'a16z_Podcast_Master_Transcripts_Organized.md'
    }
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all podcasts with episodes
    cursor.execute('''
        SELECT p.name, COUNT(e.id) as episode_count
        FROM podcasts p
        LEFT JOIN episodes e ON p.id = e.podcast_id
        WHERE e.transcript IS NOT NULL AND LENGTH(e.transcript) > 100
        GROUP BY p.id, p.name
        HAVING episode_count > 0
        ORDER BY p.name
    ''')
    
    podcasts_with_episodes = cursor.fetchall()
    
    for podcast_name, episode_count in podcasts_with_episodes:
        print(f"\n📄 {podcast_name}: {episode_count} episodes")
        
        filename = podcast_files.get(podcast_name)
        if not filename:
            print(f"   ⚠️  No file mapping for: {podcast_name}")
            continue
            
        filepath = master_dir / filename
        
        # Get all episodes for this podcast, ordered newest first
        cursor.execute('''
            SELECT e.id, e.title, e.publish_date, e.guid, e.transcript
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            WHERE p.name = ? AND e.transcript IS NOT NULL AND LENGTH(e.transcript) > 100
            ORDER BY e.publish_date DESC, e.id DESC
        ''', (podcast_name,))
        
        episodes = cursor.fetchall()
        
        if not episodes:
            print(f"   ⚠️  No episodes with transcripts found")
            continue
        
        # Generate master file content
        content = f"""# {podcast_name} - Master Transcripts

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Episodes:** {len(episodes)}

Episodes organized by publication date (newest first).

---
"""
        
        for episode_id, title, publish_date, guid, transcript in episodes:
            # Format publication date
            if publish_date:
                try:
                    if 'T' in publish_date:
                        date_obj = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    else:
                        formatted_date = publish_date[:10]
                except:
                    formatted_date = publish_date[:10] if publish_date else 'Unknown'
            else:
                formatted_date = 'Unknown'
            
            # Add episode section
            content += f"""
## {formatted_date}

### {title}
**Publication Date:** {publish_date or 'Unknown'}
"""
            
            if guid:
                content += f"**GUID:** {guid}\n"
            else:
                content += f"**Episode ID:** {episode_id}\n"
            
            content += f"""
**Full Transcript:**
{transcript}

---
"""
        
        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Generated: {filename}")
    
    conn.close()
    print(f"\n🎉 REGENERATED {len(podcasts_with_episodes)} MASTER FILES")
    print("✅ All episodes included in chronological order (newest first)")

if __name__ == "__main__":
    regenerate_all_master_files()