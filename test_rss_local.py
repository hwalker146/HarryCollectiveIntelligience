#!/usr/bin/env python3
"""
Test RSS checking locally to debug the issue
"""
import os
import sqlite3
import sys
sys.path.append('scripts')
from automated_podcast_system import AutomatedPodcastSystem

def test_rss_checking():
    """Test the RSS checking locally"""
    print("🧪 Testing RSS checking locally...")
    
    system = AutomatedPodcastSystem()
    
    # Test database connection
    print(f"📄 Database path: {system.db_path}")
    print(f"📄 Database exists: {os.path.exists(system.db_path)}")
    
    if os.path.exists(system.db_path):
        conn = sqlite3.connect(system.db_path)
        cursor = conn.cursor()
        
        # Check podcasts
        cursor.execute("SELECT COUNT(*) FROM podcasts WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        print(f"📡 Active podcasts: {active_count}")
        
        # Check podcasts with RSS URLs
        cursor.execute("SELECT COUNT(*) FROM podcasts WHERE is_active = 1 AND rss_url IS NOT NULL AND rss_url != ''")
        rss_count = cursor.fetchone()[0]
        print(f"📡 Podcasts with RSS URLs: {rss_count}")
        
        # List them
        cursor.execute("SELECT id, name, rss_url FROM podcasts WHERE is_active = 1 AND rss_url IS NOT NULL AND rss_url != '' LIMIT 5")
        podcasts = cursor.fetchall()
        print(f"📡 Sample podcasts:")
        for podcast_id, name, rss_url in podcasts:
            print(f"  - {podcast_id}: {name} -> {rss_url}")
        
        conn.close()
    
    # Test the method
    print("\n🔍 Testing process_new_episodes()...")
    try:
        result = system.process_new_episodes()
        print(f"✅ Result: {result}")
        print(f"📊 Found {len(result)} new episodes")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rss_checking()