#!/usr/bin/env python3
"""
Sync New Episodes to Master Transcript Files
Add today's processed episodes to their respective master transcript files
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def sync_new_episodes():
    print("🔄 SYNCING NEW EPISODES TO MASTER TRANSCRIPT FILES")
    print("=" * 60)
    
    # Get episodes processed today
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.name, e.title, e.transcript, e.processed_summary, e.publish_date, e.created_at
        FROM episodes e 
        JOIN podcasts p ON e.podcast_id = p.id 
        WHERE DATE(e.created_at) = '2025-08-20'
        ORDER BY e.created_at DESC
    ''')
    
    new_episodes = cursor.fetchall()
    conn.close()
    
    if not new_episodes:
        print("📭 No new episodes found for today")
        return
    
    print(f"📝 Found {len(new_episodes)} episodes to add:")
    for podcast_name, title, _, _, _, _ in new_episodes:
        print(f"  • {podcast_name}: {title}")
    
    # Master transcript files mapping
    master_files = {
        'WSJ What\'s News': 'WSJ_Whats_News_Master_Transcripts_Organized.md',
        'The Infrastructure Investor': 'The_Infrastructure_Investor_Master_Transcripts_Organized.md',
        'The Intelligence': 'The_Intelligence_Master_Transcripts_Organized.md',
        'a16z Podcast': 'a16z_Podcast_Master_Transcripts_Organized.md'
    }
    
    base_dir = Path('content/master_transcripts_organized')
    
    for podcast_name, episode_title, transcript, analysis, publish_date, created_at in new_episodes:
        if podcast_name not in master_files:
            print(f"⚠️  No master file found for {podcast_name}")
            continue
            
        master_file = base_dir / master_files[podcast_name]
        
        print(f"\n📄 Adding to {master_file.name}...")
        
        if not master_file.exists():
            print(f"❌ Master file doesn't exist: {master_file}")
            continue
        
        # Parse publish date
        if publish_date:
            try:
                pub_date = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                date_str = pub_date.strftime('%Y-%m-%d')
            except:
                date_str = "2025-08-20"
        else:
            date_str = "2025-08-20"
        
        # Create episode entry
        episode_entry = f"""
## {date_str}

### {episode_title}

**Published:** {date_str}

#### Transcript

{transcript}

"""
        
        # If there's analysis, add it
        if analysis and analysis.strip():
            episode_entry += f"""#### Analysis

{analysis}

"""
        
        episode_entry += "---\n"
        
        # Read current content
        with open(master_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find insertion point (after header, before first episode)
        header_end = content.find('---\n') + 4
        if header_end == 3:  # Not found
            print(f"❌ Could not find header in {master_file}")
            continue
        
        # Insert new episode at the beginning
        new_content = content[:header_end] + episode_entry + content[header_end:]
        
        # Update episode count in header
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('**Total Episodes:**'):
                # Extract current count and increment
                try:
                    current_count = int(line.split(':')[1].strip())
                    lines[i] = f"**Total Episodes:** {current_count + 1}"
                    break
                except:
                    pass
        
        new_content = '\n'.join(lines)
        
        # Write updated content
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Added {episode_title[:50]}... to {master_file.name}")
    
    print(f"\n🎉 Successfully synced {len(new_episodes)} episodes to master transcript files!")

if __name__ == "__main__":
    sync_new_episodes()