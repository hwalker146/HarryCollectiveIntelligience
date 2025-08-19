#!/usr/bin/env python3
"""
Remove duplicate episodes from database
"""

import sqlite3

def connect_to_database():
    """Connect to the podcast database."""
    db_path = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/podcast_app_v2.db"
    return sqlite3.connect(db_path)

def find_duplicates():
    """Find duplicate episodes based on title and podcast_id."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Find episodes with the same title and podcast_id
    cursor.execute("""
        SELECT title, podcast_id, COUNT(*) as count
        FROM episodes 
        WHERE transcribed = TRUE
        GROUP BY title, podcast_id 
        HAVING COUNT(*) > 1
        ORDER BY count DESC, title
    """)
    
    duplicates = cursor.fetchall()
    conn.close()
    
    return duplicates

def remove_all_duplicates():
    """Remove duplicate episodes from all podcasts, keeping the first occurrence."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Get all podcasts with transcribed episodes that have duplicates
    cursor.execute("""
        SELECT p.name, p.id
        FROM podcasts p 
        JOIN episodes e ON p.id = e.podcast_id 
        WHERE e.transcribed = TRUE 
        GROUP BY p.name, p.id
        ORDER BY p.name
    """)
    
    podcasts = cursor.fetchall()
    conn.close()
    
    total_removed = 0
    
    for podcast_name, podcast_id in podcasts:
        conn = connect_to_database()
        cursor = conn.cursor()
        
        # Find duplicates for this podcast
        cursor.execute("""
            SELECT title, GROUP_CONCAT(id) as ids
            FROM episodes 
            WHERE podcast_id = ? AND transcribed = TRUE
            GROUP BY title 
            HAVING COUNT(*) > 1
            ORDER BY title
        """, (podcast_id,))
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print(f"✅ {podcast_name}: No duplicates found")
            conn.close()
            continue
        
        print(f"🔧 {podcast_name}: Found {len(duplicates)} duplicate episode titles")
        
        removed_count = 0
        
        for title, ids_str in duplicates:
            ids = [int(id) for id in ids_str.split(',')]
            # Keep the first (lowest ID), remove the rest
            ids_to_remove = ids[1:]
            
            print(f"  📝 '{title[:60]}{'...' if len(title) > 60 else ''}'")
            print(f"     KEEP: ID {ids[0]}")
            print(f"     REMOVE: IDs {ids_to_remove}")
            
            # Remove duplicate episodes
            for episode_id in ids_to_remove:
                cursor.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
                removed_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Removed {removed_count} duplicate episodes from {podcast_name}\n")
        total_removed += removed_count
    
    return total_removed

def main():
    """Main function to find and remove duplicates."""
    print("COMPREHENSIVE DUPLICATE REMOVAL")
    print("=" * 60)
    
    # First, show all duplicates
    duplicates = find_duplicates()
    
    if not duplicates:
        print("No duplicate episodes found!")
        return
    
    print(f"Found duplicates in {len(duplicates)} episode titles across all podcasts:")
    for title, podcast_id, count in duplicates:
        # Get podcast name
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM podcasts WHERE id = ?", (podcast_id,))
        podcast_name = cursor.fetchone()[0]
        conn.close()
        
        print(f"  '{title[:50]}{'...' if len(title) > 50 else ''}' in {podcast_name} ({count} copies)")
    
    print("\n" + "=" * 60)
    print("REMOVING ALL DUPLICATES...")
    print("=" * 60)
    
    # Remove duplicates from ALL podcasts
    total_removed = remove_all_duplicates()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Total duplicate episodes removed: {total_removed}")
    
    if total_removed > 0:
        print("\nRecreating all organized master files with clean data...")
        
        # Recreate all organized files
        import subprocess
        result = subprocess.run(["python", "create_organized_master_files.py"], 
                              cwd="/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/utilities",
                              capture_output=True, text=True)
        print(result.stdout)

if __name__ == "__main__":
    main()