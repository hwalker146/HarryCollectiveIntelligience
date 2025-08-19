#!/usr/bin/env python3
"""
Verify and fix database episode assignments
"""

import sqlite3
import re

def connect_to_database():
    """Connect to the podcast database."""
    db_path = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/podcast_app_v2.db"
    return sqlite3.connect(db_path)

def get_correct_podcast_id(cursor, title):
    """Determine correct podcast ID based on episode title."""
    title_lower = title.lower()
    
    # More precise patterns
    if 'crossroads' in title_lower or 'infrastructure podcast' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'Crossroads: The Infrastructure Podcast'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'data center frontier' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'The Data Center Frontier Show'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'global evolution' in title_lower or 'energy transition podcast' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'Global Evolution'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'exchanges at goldman' in title_lower or 'goldman sachs' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'Exchanges at Goldman Sachs'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'infrastructure investor' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'The Infrastructure Investor'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'deal talks' in title_lower and 'crossroads' not in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'Deal Talks'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'a16z' in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'a16z Podcast'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'wsj' in title_lower or "what's news" in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = ?", ("WSJ What's News",))
        result = cursor.fetchone()
        return result[0] if result else None
    
    if 'intelligence' in title_lower and 'artificial' not in title_lower:
        cursor.execute("SELECT id FROM podcasts WHERE name = 'The Intelligence'")
        result = cursor.fetchone()
        return result[0] if result else None
    
    return None

def verify_database():
    """Verify database integrity and show misassigned episodes."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    print("Database Verification Report")
    print("=" * 50)
    
    # Get all transcribed episodes
    cursor.execute("""
        SELECT e.id, e.title, p.name as current_podcast, e.podcast_id
        FROM episodes e 
        JOIN podcasts p ON e.podcast_id = p.id 
        WHERE e.transcribed = TRUE 
        ORDER BY e.id
    """)
    
    episodes = cursor.fetchall()
    misassigned = []
    
    for episode_id, title, current_podcast, current_podcast_id in episodes:
        correct_podcast_id = get_correct_podcast_id(cursor, title)
        
        if correct_podcast_id and correct_podcast_id != current_podcast_id:
            # Get correct podcast name
            cursor.execute("SELECT name FROM podcasts WHERE id = ?", (correct_podcast_id,))
            correct_podcast = cursor.fetchone()[0]
            
            misassigned.append({
                'id': episode_id,
                'title': title,
                'current_podcast': current_podcast,
                'correct_podcast': correct_podcast,
                'current_id': current_podcast_id,
                'correct_id': correct_podcast_id
            })
    
    if misassigned:
        print(f"Found {len(misassigned)} misassigned episodes:")
        print()
        for episode in misassigned:
            print(f"Episode ID: {episode['id']}")
            print(f"Title: {episode['title'][:80]}...")
            print(f"Currently assigned to: {episode['current_podcast']}")
            print(f"Should be assigned to: {episode['correct_podcast']}")
            print("-" * 50)
    else:
        print("✅ All episodes are correctly assigned!")
    
    conn.close()
    return misassigned

def fix_database(misassigned_episodes, dry_run=True):
    """Fix misassigned episodes."""
    if not misassigned_episodes:
        print("No episodes to fix!")
        return
    
    conn = connect_to_database()
    cursor = conn.cursor()
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Fixing {len(misassigned_episodes)} misassigned episodes...")
    
    try:
        for episode in misassigned_episodes:
            if not dry_run:
                cursor.execute("""
                    UPDATE episodes 
                    SET podcast_id = ? 
                    WHERE id = ?
                """, (episode['correct_id'], episode['id']))
            
            print(f"{'Would move' if dry_run else 'Moved'} Episode {episode['id']} from {episode['current_podcast']} to {episode['correct_podcast']}")
        
        if not dry_run:
            conn.commit()
            print("\n✅ Database corrections applied!")
        else:
            print(f"\n🔍 DRY RUN: Found {len(misassigned_episodes)} episodes that need correction")
            print("Run with dry_run=False to apply fixes")
    
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def show_podcast_stats():
    """Show corrected podcast statistics."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.name, COUNT(*) as total_episodes, 
               SUM(CASE WHEN e.transcribed = TRUE THEN 1 ELSE 0 END) as with_transcripts
        FROM episodes e 
        JOIN podcasts p ON e.podcast_id = p.id 
        GROUP BY p.name 
        ORDER BY with_transcripts DESC
    """)
    
    results = cursor.fetchall()
    
    print("\nCorrected Podcast Statistics:")
    print("-" * 60)
    print(f"{'Podcast':<35} {'Total':<8} {'Transcripts':<12}")
    print("-" * 60)
    
    for podcast, total, transcripts in results:
        print(f"{podcast:<35} {total:<8} {transcripts:<12}")
    
    conn.close()

def main():
    """Main verification and fixing function."""
    # First, verify the database
    misassigned = verify_database()
    
    if misassigned:
        print("\n" + "="*50)
        print("Auto-fixing database assignments...")
        
        # First show what would be fixed
        fix_database(misassigned, dry_run=True)
        print("\n" + "="*50)
        
        # Apply the fixes
        fix_database(misassigned, dry_run=False)
        
        # Show updated stats
        show_podcast_stats()
    else:
        print("✅ No misassigned episodes found!")
    
    show_podcast_stats()

if __name__ == "__main__":
    main()