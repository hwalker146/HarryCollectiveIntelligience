#!/usr/bin/env python3
"""
Use the existing working pipeline to process new episodes
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Add paths
sys.path.append('.')
sys.path.append('core')

def run_existing_pipeline():
    """Use existing enhanced parallel processor"""
    
    print("🚀 Using existing EnhancedParallelProcessor...")
    
    try:
        from core.enhanced_parallel_processor import EnhancedParallelProcessor
        
        # Get new episodes that need transcription
        conn = sqlite3.connect('podcast_app_v2.db')
        cursor = conn.cursor()
        
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute("""
            SELECT e.id, e.title, e.audio_url, p.name
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id  
            WHERE e.created_at >= ?
            AND (LENGTH(e.transcript) < 1000 OR e.transcript IS NULL)
            AND e.audio_url IS NOT NULL
            AND p.id IN (3, 6, 7, 8, 10)
            ORDER BY e.created_at DESC
            LIMIT 5
        """, (yesterday,))
        
        episodes_to_process = cursor.fetchall()
        conn.close()
        
        print(f"📊 Found {len(episodes_to_process)} episodes to transcribe")
        
        if not episodes_to_process:
            print("📭 No episodes need transcription")
            return
        
        # Process with existing parallel processor
        processor = EnhancedParallelProcessor(max_workers=4)
        
        episode_ids = [ep[0] for ep in episodes_to_process]
        
        print(f"🎤 Starting transcription of {len(episode_ids)} episodes...")
        transcription_results = processor.parallel_transcribe_episodes(episode_ids)
        
        print(f"✅ Transcription complete: {len(transcription_results)} episodes")
        
        # Now run analysis on transcribed episodes
        print(f"🧠 Running analysis...")
        from core.working_analysis_processor import analyze_with_openai
        successful, failed = analyze_with_openai()
        
        print(f"✅ Analysis complete: {successful} successful, {failed} failed")
        
        if successful > 0:
            print(f"🎉 SUCCESS! Processed {successful} episodes with real transcripts and analysis")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_existing_pipeline()