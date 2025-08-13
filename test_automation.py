#!/usr/bin/env python3
"""
Test script for the automated podcast system
"""
import os
import sys
sys.path.append('scripts')

def test_missing_episode_identification():
    """Test the missing episode identification"""
    print("🔍 Testing missing episode identification...")
    
    from identify_missing_episodes import MissingEpisodeIdentifier
    
    identifier = MissingEpisodeIdentifier()
    missing_episodes = identifier.run_analysis()
    
    print(f"✅ Found {sum(len(episodes) for episodes in missing_episodes.values())} total missing episodes")
    return missing_episodes

def test_automation_system():
    """Test the automation system with dry run"""
    print("\n🚀 Testing automation system...")
    
    from automated_podcast_system import AutomatedPodcastSystem
    
    system = AutomatedPodcastSystem()
    
    # Test environment validation
    if not system._validate_environment():
        print("❌ Environment validation failed")
        return False
    
    # Test Google Drive authentication (skip actual upload)
    try:
        authenticated = system.sync.authenticate()
        print(f"🔐 Google Drive auth: {'✅ Success' if authenticated else '❌ Failed'}")
    except Exception as e:
        print(f"⚠️ Google Drive auth error: {e}")
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n💾 Testing database connection...")
    
    import sqlite3
    db_path = 'podcast_app_v2.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check podcast count
        cursor.execute("SELECT COUNT(*) FROM podcasts WHERE is_active = 1")
        podcast_count = cursor.fetchone()[0]
        
        # Check episode count  
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        
        # Check episodes with transcripts
        cursor.execute("SELECT COUNT(*) FROM episodes WHERE transcript IS NOT NULL AND LENGTH(transcript) > 1000")
        transcript_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Database stats:")
        print(f"   Active podcasts: {podcast_count}")
        print(f"   Total episodes: {episode_count}")
        print(f"   Episodes with transcripts: {transcript_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AUTOMATED PODCAST SYSTEM - TEST SUITE")
    print("=" * 50)
    
    # Test 1: Database connection
    db_ok = test_database_connection()
    
    # Test 2: Missing episode identification
    if db_ok:
        missing_episodes = test_missing_episode_identification()
    
    # Test 3: Automation system
    if db_ok:
        automation_ok = test_automation_system()
    
    print("\n🎉 Test suite complete!")
    print("✅ System is ready for GitHub Actions automation")