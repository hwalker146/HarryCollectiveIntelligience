#!/usr/bin/env python3
"""
Analyze gaps between episodes for each podcast
"""
import sqlite3
import feedparser
from datetime import datetime

def analyze_gaps():
    print("📊 PODCAST EPISODE GAP ANALYSIS")
    print("=" * 60)
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    # Get all active podcasts
    cursor.execute("SELECT id, name, rss_url FROM podcasts WHERE is_active = 1 ORDER BY name")
    podcasts = cursor.fetchall()
    
    for podcast_id, name, rss_url in podcasts:
        print(f"\n🎙️ {name}")
        print("-" * 50)
        
        # Get database episodes
        cursor.execute("""
            SELECT COUNT(*) as total,
                   MIN(publish_date) as oldest,
                   MAX(publish_date) as newest
            FROM episodes 
            WHERE podcast_id = ?
        """, (podcast_id,))
        
        db_stats = cursor.fetchone()
        db_total, oldest, newest = db_stats
        
        print(f"📊 Database: {db_total} episodes")
        if oldest and newest:
            print(f"📅 Date range: {oldest[:10]} → {newest[:10]}")
        else:
            print("📅 No episodes with dates")
            continue
        
        # Parse RSS feed
        try:
            print("📡 Checking RSS feed...")
            feed = feedparser.parse(rss_url)
            rss_total = len(feed.entries)
            print(f"📊 RSS feed: {rss_total} episodes")
            
            # Estimate gaps
            if rss_total > db_total:
                gap_estimate = rss_total - db_total
                print(f"⚠️  Potential gaps: ~{gap_estimate} episodes missing")
            else:
                print("✅ No apparent gaps (DB >= RSS count)")
                
        except Exception as e:
            print(f"❌ RSS check failed: {e}")
    
    conn.close()

if __name__ == "__main__":
    analyze_gaps()