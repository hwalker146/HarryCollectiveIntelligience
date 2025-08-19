#!/usr/bin/env python3
"""
List all episodes for each podcast to identify duplicates
"""

import sqlite3

def connect_to_database():
    """Connect to the podcast database."""
    db_path = "/Users/hwalker/Desktop/podcast_processor/podcast_app_v2/podcast_app_v2.db"
    return sqlite3.connect(db_path)

def list_episodes_for_podcast(podcast_name):
    """List all transcribed episodes for a specific podcast."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Get all transcribed episodes for this podcast
    cursor.execute("""
        SELECT e.id, e.title, e.guid, e.publish_date
        FROM episodes e 
        JOIN podcasts p ON e.podcast_id = p.id 
        WHERE p.name = ? AND e.transcribed = TRUE 
        ORDER BY e.title
    """, (podcast_name,))
    
    episodes = cursor.fetchall()
    conn.close()
    
    return episodes

def find_duplicates_in_episodes(episodes):
    """Find duplicate episodes by title."""
    title_counts = {}
    duplicates = []
    
    for episode_id, title, guid, publish_date in episodes:
        if title in title_counts:
            title_counts[title].append((episode_id, guid, publish_date))
        else:
            title_counts[title] = [(episode_id, guid, publish_date)]
    
    # Find titles with multiple episodes
    for title, episode_list in title_counts.items():
        if len(episode_list) > 1:
            duplicates.append((title, episode_list))
    
    return duplicates

def main():
    """List all episodes for each podcast and identify duplicates."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    # Get all podcasts with transcribed episodes
    cursor.execute("""
        SELECT DISTINCT p.name 
        FROM podcasts p 
        JOIN episodes e ON p.id = e.podcast_id 
        WHERE e.transcribed = TRUE 
        ORDER BY p.name
    """)
    
    podcasts = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print("Episode Listing and Duplicate Detection")
    print("=" * 60)
    
    total_duplicates = 0
    
    for podcast_name in podcasts:
        print(f"\n📻 {podcast_name}")
        print("-" * 50)
        
        episodes = list_episodes_for_podcast(podcast_name)
        duplicates = find_duplicates_in_episodes(episodes)
        
        print(f"Total episodes: {len(episodes)}")
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate titles:")
            for title, episode_list in duplicates:
                print(f"\n  🔄 '{title}' ({len(episode_list)} copies)")
                for i, (episode_id, guid, publish_date) in enumerate(episode_list):
                    status = "KEEP" if i == 0 else "REMOVE"
                    print(f"     {status}: ID {episode_id}, GUID {guid[:8]}..., Date {publish_date}")
                total_duplicates += len(episode_list) - 1
        else:
            print("✅ No duplicates found")
        
        # List all unique episode titles
        unique_titles = set(episode[1] for episode in episodes)
        print(f"\nUnique episode titles ({len(unique_titles)}):")
        for i, title in enumerate(sorted(unique_titles), 1):
            print(f"  {i:2d}. {title}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total podcasts checked: {len(podcasts)}")
    print(f"Total duplicate episodes to remove: {total_duplicates}")
    
    if total_duplicates > 0:
        print(f"\n⚠️  Found {total_duplicates} duplicate episodes across all podcasts")
        print("Ready to clean up duplicates!")
    else:
        print("✅ No duplicates found across all podcasts")

if __name__ == "__main__":
    main()