#!/usr/bin/env python3
"""
Debug version to see exactly what the detection logic is seeing
"""
import sqlite3
import feedparser
import requests
from datetime import datetime

def debug_podcast_detection(podcast_name_filter=None):
    """Debug episode detection for specific podcast"""
    print("🔍 DEBUGGING EPISODE DETECTION LOGIC...")
    
    db_path = 'podcast_app_v2.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get podcasts
    if podcast_name_filter:
        cursor.execute('SELECT id, name, rss_url FROM podcasts WHERE name LIKE ? ORDER BY name', (f'%{podcast_name_filter}%',))
    else:
        cursor.execute('SELECT id, name, rss_url FROM podcasts ORDER BY name')
    podcasts = cursor.fetchall()
    
    for podcast_id, podcast_name, rss_url in podcasts:
        print(f"\n🎧 {podcast_name}")
        print(f"   ID: {podcast_id}")
        print(f"   RSS: {rss_url}")
        
        try:
            # EXACT same query as automation
            cursor.execute('''
                SELECT MIN(publish_date), MAX(publish_date), COUNT(*) 
                FROM episodes 
                WHERE podcast_id = ? AND publish_date IS NOT NULL
            ''', (podcast_id,))
            
            date_info = cursor.fetchone()
            oldest_date, newest_date, episode_count = date_info
            
            print(f"   📊 Database Query Results:")
            print(f"       oldest_date: {oldest_date} (type: {type(oldest_date)})")
            print(f"       newest_date: {newest_date} (type: {type(newest_date)})")
            print(f"       episode_count: {episode_count}")
            
            # Parse dates like automation does
            oldest_db_date = None
            newest_db_date = None
            if oldest_date:
                try:
                    oldest_db_date = datetime.fromisoformat(oldest_date.replace('Z', '+00:00'))
                    print(f"       parsed oldest_db_date: {oldest_db_date}")
                except Exception as e:
                    print(f"       ERROR parsing oldest_date: {e}")
                    oldest_db_date = None
            if newest_date:
                try:
                    newest_db_date = datetime.fromisoformat(newest_date.replace('Z', '+00:00'))
                    print(f"       parsed newest_db_date: {newest_db_date}")
                except Exception as e:
                    print(f"       ERROR parsing newest_date: {e}")
                    newest_db_date = None
            
            print(f"   🔍 Logic Check:")
            print(f"       oldest_naive: {oldest_db_date}")
            print(f"       newest_naive: {newest_db_date}")
            print(f"       not oldest_naive and not newest_naive: {not oldest_db_date and not newest_db_date}")
            
            if not oldest_db_date and not newest_db_date:
                print(f"   ❌ BUG: This will treat ALL RSS episodes as 'new' because both dates are None!")
            elif oldest_db_date and newest_db_date:
                print(f"   ✅ Good: Has date range {oldest_db_date} to {newest_db_date}")
            else:
                print(f"   ⚠️  Issue: Only one date parsed successfully")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    # Test specific podcasts that are showing issues
    debug_podcast_detection("Intelligence")
    debug_podcast_detection("a16z")
    debug_podcast_detection("Exchanges")