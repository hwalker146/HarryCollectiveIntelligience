#!/usr/bin/env python3
"""
Test RSS feeds can actually pull audio URLs
"""
import sqlite3
import requests
import feedparser

def test_rss_feeds():
    """Test each RSS feed can pull audio URLs"""
    
    conn = sqlite3.connect('podcast_app_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, rss_url 
        FROM podcasts 
        WHERE is_active = 1 AND rss_url IS NOT NULL 
        ORDER BY name
    """)
    
    podcasts = cursor.fetchall()
    conn.close()
    
    print(f"🧪 Testing {len(podcasts)} RSS feeds...")
    
    for podcast_id, name, rss_url in podcasts:
        print(f"\n📡 Testing: {name}")
        print(f"   RSS: {rss_url}")
        
        try:
            # Test RSS fetch
            headers = {'User-Agent': 'Podcast Analysis Application v2/2.0.0'}
            response = requests.get(rss_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse RSS
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"   ❌ Invalid RSS format")
                continue
            
            # Check for episodes with audio
            audio_episodes = 0
            for entry in feed.entries[:3]:  # Check first 3 episodes
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if audio_url:
                    audio_episodes += 1
                    print(f"   ✅ Audio found: {getattr(entry, 'title', 'Unknown')[:50]}...")
                    
                    # Test audio URL
                    try:
                        audio_response = requests.head(audio_url, headers=headers, timeout=10)
                        if audio_response.status_code == 200:
                            size_mb = int(audio_response.headers.get('content-length', 0)) / (1024*1024)
                            print(f"      📁 Audio accessible: {size_mb:.1f}MB")
                        else:
                            print(f"      ⚠️ Audio HTTP {audio_response.status_code}")
                    except Exception as e:
                        print(f"      ❌ Audio not accessible: {e}")
            
            if audio_episodes == 0:
                print(f"   ❌ No audio episodes found")
            else:
                print(f"   ✅ Found {audio_episodes} episodes with audio")
                
        except Exception as e:
            print(f"   ❌ RSS fetch failed: {e}")

if __name__ == "__main__":
    test_rss_feeds()